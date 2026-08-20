#!/usr/bin/env python3
"""
Agent Monitor - 监控 Hermes 和 OpenCode 的 token 使用和费用
不修改任何原有 agent 文件，只读取数据库和配置
"""

import sqlite3
import json
import yaml
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
import logging
import hashlib

@dataclass
class UsageRecord:
    """使用记录"""
    agent: str  # hermes 或 opencode
    session_id: str
    model: str
    provider: str
    provider_display: str
    
    # Token 统计
    api_calls: int
    input_tokens: int
    output_tokens: int
    cache_read_tokens: int
    cache_write_tokens: int
    reasoning_tokens: int
    
    # 费用统计（CNY per million tokens）
    standard_cost_usd: float
    actual_cost_cny: float
    
    # 元数据
    first_seen: Optional[datetime]
    last_seen: Optional[datetime]
    
    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens + self.reasoning_tokens
    
    @property
    def cache_hit_rate(self) -> float:
        """缓存命中率"""
        denominator = self.input_tokens + self.cache_read_tokens + self.cache_write_tokens
        if denominator == 0:
            return 0.0
        return self.cache_read_tokens / denominator


class AgentMonitor:
    """Agent 监控器"""
    
    def __init__(self, config_path: str = "config.yaml"):
        self.config_path = Path(config_path)
        self.config = self._load_config()
        self._setup_logging()
        
        # 初始化缓存
        cache_dir = Path('cache')
        cache_dir.mkdir(exist_ok=True)
        self.cache_db_path = cache_dir / 'reports.db'
        self._init_cache_db()
    
    def _load_config(self) -> dict:
        """加载配置文件"""
        with open(self.config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    
    def _setup_logging(self):
        """配置日志"""
        log_config = self.config.get('monitor', {}).get('logging', {})
        log_level = getattr(logging, log_config.get('level', 'INFO'))
        
        log_dir = Path('logs')
        log_dir.mkdir(exist_ok=True)
        
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s [%(levelname)s] %(message)s',
            handlers=[
                logging.FileHandler(log_dir / 'monitor.log', encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def _init_cache_db(self):
        """初始化缓存数据库"""
        conn = sqlite3.connect(self.cache_db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS report_cache (
                cache_key TEXT PRIMARY KEY,
                days INTEGER,
                report_data TEXT,
                created_at REAL,
                expires_at REAL
            )
        ''')
        
        # 清理过期缓存
        cursor.execute('DELETE FROM report_cache WHERE expires_at < ?', (datetime.now().timestamp(),))
        
        conn.commit()
        conn.close()
    
    def _get_cache_key(self, days: Optional[int]) -> str:
        """生成缓存键"""
        # 基于 days 参数生成键
        key_data = f"report_{days}_{datetime.now().strftime('%Y%m%d%H')}"  # 按小时缓存
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def _get_cached_report(self, days: Optional[int]) -> Optional[Dict]:
        """获取缓存的报告"""
        cache_key = self._get_cache_key(days)
        
        conn = sqlite3.connect(self.cache_db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            'SELECT report_data, expires_at FROM report_cache WHERE cache_key = ?',
            (cache_key,)
        )
        row = cursor.fetchone()
        conn.close()
        
        if row:
            report_json, expires_at = row
            if expires_at > datetime.now().timestamp():
                self.logger.info(f"Using cached report for days={days}")
                return json.loads(report_json)
            else:
                self.logger.info(f"Cache expired for days={days}")
        
        return None
    
    def _cache_report(self, days: Optional[int], report: Dict, ttl_minutes: int = 60):
        """缓存报告"""
        cache_key = self._get_cache_key(days)
        now = datetime.now().timestamp()
        expires_at = now + (ttl_minutes * 60)
        
        conn = sqlite3.connect(self.cache_db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO report_cache (cache_key, days, report_data, created_at, expires_at)
            VALUES (?, ?, ?, ?, ?)
        ''', (cache_key, days or -1, json.dumps(report, default=str), now, expires_at))
        
        conn.commit()
        conn.close()
        
        self.logger.info(f"Cached report for days={days}, TTL={ttl_minutes}min")
    
    def _calculate_price(self, model: str, provider: str, 
                        input_tokens: int, output_tokens: int,
                        cache_read: int, cache_write: int,
                        reasoning: int) -> Tuple[float, float]:
        """
        计算价格
        返回: (标准价格 USD, 实际价格 CNY)
        """
        pricing = self.config['pricing']
        
        # 1. 检查价格覆盖
        override_key = f"{model}@{provider}"
        price_overrides = pricing.get('price_overrides') or {}
        if override_key in price_overrides:
            override = price_overrides[override_key]
            actual_cny = (
                input_tokens * override['input'] / 1_000_000 +
                output_tokens * override['output'] / 1_000_000 +
                cache_write * override.get('cache_write', 0) / 1_000_000 +
                cache_read * override.get('cache_read', 0) / 1_000_000 +
                reasoning * override.get('output', override['output']) / 1_000_000  # reasoning 按 output 计费
            )
            
            # 反推标准价格
            multiplier = pricing['provider_multipliers'].get(provider, 1.0)
            cny_to_usd = pricing['cny_to_usd_rate']
            standard_usd = actual_cny * cny_to_usd / multiplier
            
            return standard_usd, actual_cny
        
        # 2. 使用标准价格
        if model in pricing['standard_prices']:
            std_price = pricing['standard_prices'][model]
            standard_usd = (
                input_tokens * std_price['input'] / 1_000_000 +
                output_tokens * std_price['output'] / 1_000_000 +
                cache_write * std_price.get('cache_write', 0) / 1_000_000 +
                cache_read * std_price.get('cache_read', 0) / 1_000_000 +
                reasoning * std_price['output'] / 1_000_000  # reasoning 按 output 计费
            )
            
            # 计算实际价格
            multiplier = pricing['provider_multipliers'].get(provider, 1.0)
            cny_to_usd = pricing['cny_to_usd_rate']
            actual_cny = standard_usd * multiplier / cny_to_usd
            
            return standard_usd, actual_cny
        
        # 3. 未知模型，返回 0
        self.logger.warning(f"Unknown model pricing: {model}")
        return 0.0, 0.0
    
    def collect_hermes_usage(self, days: Optional[int] = None) -> List[UsageRecord]:
        """采集 Hermes 使用数据"""
        source_config = self.config['sources']['hermes']
        if not source_config['enabled']:
            return []
        
        db_path = source_config['db_path']
        if not Path(db_path).exists():
            self.logger.error(f"Hermes DB not found: {db_path}")
            return []
        
        records = []
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 构建时间过滤条件
        where_clause = ""
        if days:
            cutoff_time = datetime.now().timestamp() - (days * 86400)
            where_clause = f"WHERE last_seen >= {cutoff_time}"
        
        query = f"""
            SELECT 
                session_id,
                model,
                billing_provider,
                task,
                api_call_count,
                input_tokens,
                output_tokens,
                cache_read_tokens,
                cache_write_tokens,
                reasoning_tokens,
                first_seen,
                last_seen
            FROM session_model_usage
            {where_clause}
            ORDER BY last_seen DESC
        """
        
        cursor.execute(query)
        rows = cursor.fetchall()
        
        for row in rows:
            session_id, model, provider, task, calls, input_tok, output_tok, \
                cache_read, cache_write, reasoning, first_seen, last_seen = row
            
            # 处理 None 值
            provider = provider or 'unknown'
            input_tok = input_tok or 0
            output_tok = output_tok or 0
            cache_read = cache_read or 0
            cache_write = cache_write or 0
            reasoning = reasoning or 0
            
            # 计算价格
            std_usd, actual_cny = self._calculate_price(
                model, provider, 
                input_tok, output_tok,
                cache_read, cache_write,
                reasoning
            )
            
            # 获取 provider 显示名称
            provider_display = self._get_provider_display_name(provider, 'hermes')
            
            records.append(UsageRecord(
                agent='hermes',
                session_id=session_id,
                model=model,
                provider=provider,
                provider_display=provider_display,
                api_calls=calls or 0,
                input_tokens=input_tok,
                output_tokens=output_tok,
                cache_read_tokens=cache_read,
                cache_write_tokens=cache_write,
                reasoning_tokens=reasoning,
                standard_cost_usd=std_usd,
                actual_cost_cny=actual_cny,
                first_seen=datetime.fromtimestamp(first_seen) if first_seen else None,
                last_seen=datetime.fromtimestamp(last_seen) if last_seen else None
            ))
        
        conn.close()
        self.logger.info(f"Collected {len(records)} Hermes usage records")
        return records
    
    def collect_opencode_usage(self, days: Optional[int] = None) -> List[UsageRecord]:
        """采集 OpenCode 使用数据"""
        source_config = self.config['sources']['opencode']
        if not source_config['enabled']:
            return []
        
        db_path = source_config['db_path']
        if not Path(db_path).exists():
            self.logger.error(f"OpenCode DB not found: {db_path}")
            return []
        
        records = []
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 构建时间过滤条件
        where_clause = ""
        if days:
            cutoff_time = int((datetime.now() - timedelta(days=days)).timestamp() * 1000)
            where_clause = f"WHERE time_updated >= {cutoff_time}"
        
        query = f"""
            SELECT 
                id,
                model,
                cost,
                tokens_input,
                tokens_output,
                tokens_reasoning,
                tokens_cache_read,
                tokens_cache_write,
                time_created,
                time_updated
            FROM session
            {where_clause}
            ORDER BY time_updated DESC
        """
        
        cursor.execute(query)
        rows = cursor.fetchall()
        
        for row in rows:
            session_id, model_json, cost, input_tok, output_tok, reasoning, \
                cache_read, cache_write, time_created, time_updated = row
            
            # 解析 model JSON
            try:
                model_data = json.loads(model_json) if model_json else {}
                model = model_data.get('id', 'unknown')
                provider = model_data.get('providerID', 'unknown')
            except:
                model = 'unknown'
                provider = 'unknown'
            
            # 处理 None 值
            input_tok = input_tok or 0
            output_tok = output_tok or 0
            reasoning = reasoning or 0
            cache_read = cache_read or 0
            cache_write = cache_write or 0
            
            # 计算价格（OpenCode 已经记录了 cost，但我们重新计算以保持一致）
            std_usd, actual_cny = self._calculate_price(
                model, provider,
                input_tok, output_tok,
                cache_read, cache_write,
                reasoning
            )
            
            # 获取 provider 显示名称
            provider_display = self._get_provider_display_name(provider, 'opencode')
            
            records.append(UsageRecord(
                agent='opencode',
                session_id=session_id,
                model=model,
                provider=provider,
                provider_display=provider_display,
                api_calls=1,  # OpenCode 不记录单独的 API 调用次数
                input_tokens=input_tok,
                output_tokens=output_tok,
                cache_read_tokens=cache_read,
                cache_write_tokens=cache_write,
                reasoning_tokens=reasoning,
                standard_cost_usd=std_usd,
                actual_cost_cny=actual_cny,
                first_seen=datetime.fromtimestamp(time_created / 1000) if time_created else None,
                last_seen=datetime.fromtimestamp(time_updated / 1000) if time_updated else None
            ))
        
        conn.close()
        self.logger.info(f"Collected {len(records)} OpenCode usage records")
        return records
    
    def _get_provider_display_name(self, provider: str, agent: str) -> str:
        """获取 provider 显示名称"""
        # 尝试从配置中读取
        if agent == 'hermes':
            config_path = self.config['sources']['hermes']['config_path']
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f)
                    providers = config.get('providers', {})
                    if provider in providers:
                        return providers[provider].get('name', provider)
            except Exception as e:
                self.logger.warning(f"Failed to read Hermes config: {e}")
        
        elif agent == 'opencode':
            config_path = self.config['sources']['opencode']['config_path']
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    # OpenCode 使用 jsonc 格式，需要移除注释和尾部逗号
                    content = f.read()
                    # 移除 // 注释
                    lines = []
                    for line in content.split('\n'):
                        if '//' in line:
                            line = line[:line.index('//')]
                        lines.append(line)
                    content = '\n'.join(lines)
                    # 移除尾部逗号（JSON 不允许）
                    import re
                    content = re.sub(r',(\s*[}\]])', r'\1', content)
                    config = json.loads(content)
                    providers = config.get('provider', {})
                    if provider in providers:
                        return providers[provider].get('name', provider)
            except Exception as e:
                # 配置文件读取失败不影响核心功能，只记录一次
                if not hasattr(self, '_opencode_config_warned'):
                    self.logger.warning(f"Failed to read OpenCode config: {e}")
                    self._opencode_config_warned = True
        
        return provider
    
    def aggregate_usage(self, records: List[UsageRecord]) -> Dict:
        """聚合使用统计"""
        if not records:
            return {
                'total': self._empty_stats(),
                'by_agent': {},
                'by_model': {},
                'by_provider': {},
                'by_agent_model': {}
            }
        
        # 总计
        total = self._aggregate_records(records)
        
        # 按 agent 聚合
        by_agent = {}
        for agent in set(r.agent for r in records):
            agent_records = [r for r in records if r.agent == agent]
            by_agent[agent] = self._aggregate_records(agent_records)
        
        # 按 model 聚合
        by_model = {}
        for model in set(r.model for r in records):
            model_records = [r for r in records if r.model == model]
            stats = self._aggregate_records(model_records)
            # 添加 provider 信息（取最常用的 provider）
            provider_counts = {}
            for r in model_records:
                provider_counts[r.provider_display] = provider_counts.get(r.provider_display, 0) + r.api_calls
            most_common_provider = max(provider_counts.items(), key=lambda x: x[1])[0] if provider_counts else 'unknown'
            stats['provider'] = most_common_provider
            by_model[model] = stats
        
        # 按 provider 聚合
        by_provider = {}
        for provider in set(r.provider_display for r in records):
            provider_records = [r for r in records if r.provider_display == provider]
            by_provider[provider] = self._aggregate_records(provider_records)
        
        # 按 agent + model 聚合
        by_agent_model = {}
        for agent in set(r.agent for r in records):
            by_agent_model[agent] = {}
            agent_records = [r for r in records if r.agent == agent]
            for model in set(r.model for r in agent_records):
                model_records = [r for r in agent_records if r.model == model]
                by_agent_model[agent][model] = self._aggregate_records(model_records)
        
        return {
            'total': total,
            'by_agent': by_agent,
            'by_model': by_model,
            'by_provider': by_provider,
            'by_agent_model': by_agent_model
        }
    
    def _aggregate_records(self, records: List[UsageRecord]) -> Dict:
        """聚合记录列表"""
        if not records:
            return self._empty_stats()
        
        total_calls = sum(r.api_calls for r in records)
        total_input = sum(r.input_tokens for r in records)
        total_output = sum(r.output_tokens for r in records)
        total_cache_read = sum(r.cache_read_tokens for r in records)
        total_cache_write = sum(r.cache_write_tokens for r in records)
        total_reasoning = sum(r.reasoning_tokens for r in records)
        total_std_cost = sum(r.standard_cost_usd for r in records)
        total_actual_cost = sum(r.actual_cost_cny for r in records)
        
        # 计算缓存命中率
        cache_denominator = total_input + total_cache_read + total_cache_write
        cache_hit_rate = total_cache_read / cache_denominator if cache_denominator > 0 else 0
        
        return {
            'sessions': len(set(r.session_id for r in records)),
            'api_calls': total_calls,
            'input_tokens': total_input,
            'output_tokens': total_output,
            'cache_read_tokens': total_cache_read,
            'cache_write_tokens': total_cache_write,
            'reasoning_tokens': total_reasoning,
            'total_tokens': total_input + total_output + total_reasoning,
            'cache_hit_rate': cache_hit_rate,
            'standard_cost_usd': total_std_cost,
            'actual_cost_cny': total_actual_cost,
            'first_seen': min((r.first_seen for r in records if r.first_seen), default=None),
            'last_seen': max((r.last_seen for r in records if r.last_seen), default=None)
        }
    
    def _empty_stats(self) -> Dict:
        """空统计"""
        return {
            'sessions': 0,
            'api_calls': 0,
            'input_tokens': 0,
            'output_tokens': 0,
            'cache_read_tokens': 0,
            'cache_write_tokens': 0,
            'reasoning_tokens': 0,
            'total_tokens': 0,
            'cache_hit_rate': 0,
            'standard_cost_usd': 0,
            'actual_cost_cny': 0,
            'first_seen': None,
            'last_seen': None
        }
    
    def get_report(self, days: Optional[int] = None, use_cache: bool = True) -> Dict:
        """生成报告"""
        # 尝试从缓存获取
        if use_cache:
            cached = self._get_cached_report(days)
            if cached:
                return cached
        
        self.logger.info(f"Generating report for last {days or 'all'} days")
        
        # 采集数据
        hermes_records = self.collect_hermes_usage(days)
        opencode_records = self.collect_opencode_usage(days)
        all_records = hermes_records + opencode_records
        
        # 聚合统计
        stats = self.aggregate_usage(all_records)
        
        report = {
            'generated_at': datetime.now().isoformat(),
            'period_days': days,
            'record_count': len(all_records),
            'statistics': stats
        }
        
        # 缓存结果
        if use_cache:
            self._cache_report(days, report)
        
        return report


if __name__ == '__main__':
    import sys
    
    monitor = AgentMonitor()
    
    # 命令行参数：天数
    days = int(sys.argv[1]) if len(sys.argv) > 1 else None
    
    # 生成报告
    report = monitor.get_report(days)
    
    # 输出 JSON
    print(json.dumps(report, indent=2, ensure_ascii=False, default=str))
