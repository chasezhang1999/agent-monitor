#!/usr/bin/env python3
"""
多机数据同步模块
通过 Git 私有仓库同步多台机器的监控数据
"""

import json
import socket
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
import logging


class MachineIdentifier:
    """机器标识"""
    
    @staticmethod
    def get_hostname() -> str:
        """获取当前机器的主机名"""
        return socket.gethostname()
    
    @staticmethod
    def get_machine_id() -> str:
        """生成机器唯一标识（hostname-简化）"""
        hostname = MachineIdentifier.get_hostname()
        # 移除域名后缀，保留主机名主体
        return hostname.split('.')[0].lower().replace(' ', '-')


class DataSnapshot:
    """数据快照 - 导出当前机器的监控数据"""
    
    def __init__(self, monitor):
        self.monitor = monitor
        self.logger = logging.getLogger(__name__)
    
    def export_snapshot(self, output_path: Path) -> Dict:
        """
        导出当前机器的数据快照
        
        Returns:
            快照数据字典
        """
        machine_id = MachineIdentifier.get_machine_id()
        hostname = MachineIdentifier.get_hostname()
        
        # 获取多个时间窗口的统计数据
        windows = [1, 7, 30, 90]  # 天
        reports = {}
        
        for days in windows:
            try:
                report = self.monitor.get_report(days=days)
                reports[f"{days}d"] = report
            except Exception as e:
                self.logger.error(f"Failed to generate {days}d report: {e}")
                reports[f"{days}d"] = None
        
        # 构建快照数据
        snapshot = {
            "machine_id": machine_id,
            "hostname": hostname,
            "timestamp": datetime.now().isoformat(),
            "reports": reports,
            "metadata": {
                "monitor_version": "1.0",
                "hermes_enabled": self.monitor.config['sources']['hermes']['enabled'],
                "opencode_enabled": self.monitor.config['sources']['opencode']['enabled'],
            }
        }
        
        # 写入文件
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(snapshot, f, indent=2, ensure_ascii=False, default=str)
        
        self.logger.info(f"Exported snapshot for {machine_id} to {output_path}")
        return snapshot


class GitSync:
    """Git 同步管理器"""
    
    def __init__(self, sync_dir: Path, remote_url: Optional[str] = None):
        self.sync_dir = Path(sync_dir)
        self.remote_url = remote_url
        self.logger = logging.getLogger(__name__)
    
    def init_repo(self) -> bool:
        """初始化 Git 仓库"""
        if (self.sync_dir / '.git').exists():
            self.logger.info(f"Git repo already exists at {self.sync_dir}")
            return True
        
        try:
            self.sync_dir.mkdir(parents=True, exist_ok=True)
            
            # 初始化仓库
            subprocess.run(['git', 'init'], cwd=self.sync_dir, check=True, 
                          capture_output=True, text=True)
            
            # 创建目录结构
            (self.sync_dir / 'machines').mkdir(exist_ok=True)
            
            # 创建 README
            readme_path = self.sync_dir / 'README.md'
            if not readme_path.exists():
                readme_content = """# Agent Monitor - Multi-Machine Sync

This repository stores monitoring data from multiple machines.

## Structure

- `machines/{machine-id}.json` - Snapshot data from each machine
- `metadata.yaml` - Machine registry and sync metadata

## Usage

Each machine periodically exports its monitoring snapshot here.
The dashboard aggregates data from all machines.
"""
                readme_path.write_text(readme_content, encoding='utf-8')
            
            # 创建 .gitignore
            gitignore_path = self.sync_dir / '.gitignore'
            if not gitignore_path.exists():
                gitignore_content = """*.pyc
__pycache__/
.DS_Store
*.log
"""
                gitignore_path.write_text(gitignore_content, encoding='utf-8')
            
            # 如果有远程 URL，添加 remote
            if self.remote_url:
                subprocess.run(['git', 'remote', 'add', 'origin', self.remote_url],
                             cwd=self.sync_dir, check=True, capture_output=True, text=True)
            
            self.logger.info(f"Initialized Git repo at {self.sync_dir}")
            return True
            
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Failed to init Git repo: {e.stderr}")
            return False
        except Exception as e:
            self.logger.error(f"Failed to init Git repo: {e}")
            return False
    
    def commit_and_push(self, message: Optional[str] = None) -> bool:
        """提交并推送更改"""
        if not (self.sync_dir / '.git').exists():
            self.logger.error("Git repo not initialized")
            return False
        
        try:
            # 检查是否有更改
            result = subprocess.run(['git', 'status', '--porcelain'],
                                  cwd=self.sync_dir, check=True,
                                  capture_output=True, text=True)
            
            if not result.stdout.strip():
                self.logger.info("No changes to commit")
                return True
            
            # 添加所有更改
            subprocess.run(['git', 'add', '-A'], cwd=self.sync_dir, check=True,
                         capture_output=True, text=True)
            
            # 提交
            if not message:
                machine_id = MachineIdentifier.get_machine_id()
                message = f"Update snapshot from {machine_id} at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            
            subprocess.run(['git', 'commit', '-m', message],
                         cwd=self.sync_dir, check=True,
                         capture_output=True, text=True)
            
            # 推送（如果有 remote）
            if self.remote_url:
                subprocess.run(['git', 'push', 'origin', 'main'],
                             cwd=self.sync_dir, check=True,
                             capture_output=True, text=True)
                self.logger.info("Committed and pushed changes")
            else:
                self.logger.info("Committed changes (no remote configured)")
            
            return True
            
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Git operation failed: {e.stderr}")
            return False
        except Exception as e:
            self.logger.error(f"Git operation failed: {e}")
            return False
    
    def pull(self) -> bool:
        """从远程拉取最新数据"""
        if not (self.sync_dir / '.git').exists():
            self.logger.error("Git repo not initialized")
            return False
        
        if not self.remote_url:
            self.logger.warning("No remote configured, skipping pull")
            return True
        
        try:
            subprocess.run(['git', 'pull', 'origin', 'main'],
                         cwd=self.sync_dir, check=True,
                         capture_output=True, text=True)
            self.logger.info("Pulled latest changes from remote")
            return True
            
        except subprocess.CalledProcessError as e:
            # 首次 pull 可能失败（分支不存在）
            if "couldn't find remote ref" in e.stderr.lower():
                self.logger.info("Remote branch not found (first push), continuing")
                return True
            self.logger.error(f"Git pull failed: {e.stderr}")
            return False
        except Exception as e:
            self.logger.error(f"Git pull failed: {e}")
            return False


class MultiMachineAggregator:
    """多机数据聚合器"""
    
    def __init__(self, sync_dir: Path):
        self.sync_dir = Path(sync_dir)
        self.machines_dir = self.sync_dir / 'machines'
        self.logger = logging.getLogger(__name__)
    
    def load_all_snapshots(self) -> Dict[str, Dict]:
        """
        加载所有机器的快照数据
        
        Returns:
            {machine_id: snapshot_data}
        """
        if not self.machines_dir.exists():
            self.logger.warning(f"Machines directory not found: {self.machines_dir}")
            return {}
        
        snapshots = {}
        
        for snapshot_file in self.machines_dir.glob('*.json'):
            try:
                with open(snapshot_file, 'r', encoding='utf-8') as f:
                    snapshot = json.load(f)
                
                machine_id = snapshot.get('machine_id')
                if machine_id:
                    snapshots[machine_id] = snapshot
                    self.logger.debug(f"Loaded snapshot from {machine_id}")
                else:
                    self.logger.warning(f"Invalid snapshot (no machine_id): {snapshot_file}")
                    
            except Exception as e:
                self.logger.error(f"Failed to load snapshot {snapshot_file}: {e}")
        
        self.logger.info(f"Loaded {len(snapshots)} machine snapshots")
        return snapshots
    
    def aggregate_report(self, days: Optional[int] = None) -> Dict:
        """
        聚合所有机器的数据生成统一报告
        
        Args:
            days: 时间窗口（天），None 表示全部
        
        Returns:
            聚合后的报告
        """
        snapshots = self.load_all_snapshots()
        
        if not snapshots:
            return {
                "total_cost_cny": 0,
                "total_tokens": 0,
                "by_model": {},
                "by_provider": {},
                "by_machine": {},
                "machine_count": 0,
                "timestamp": datetime.now().isoformat(),
            }
        
        # 确定时间窗口 key
        window_key = f"{days}d" if days else "all"
        if window_key not in ["1d", "7d", "30d", "90d"]:
            window_key = "30d"  # 默认
        
        # 初始化聚合数据
        total_cost = 0
        total_tokens = 0
        by_model = {}
        by_provider = {}
        by_machine = {}
        
        # 聚合每台机器的数据
        for machine_id, snapshot in snapshots.items():
            reports = snapshot.get('reports', {})
            report = reports.get(window_key)
            
            if not report:
                self.logger.warning(f"No {window_key} report for {machine_id}")
                continue
            
            # 机器级统计
            machine_cost = report.get('total_cost_cny', 0)
            machine_tokens = report.get('total_tokens', 0)
            
            by_machine[machine_id] = {
                "hostname": snapshot.get('hostname'),
                "cost_cny": machine_cost,
                "tokens": machine_tokens,
                "timestamp": snapshot.get('timestamp'),
            }
            
            total_cost += machine_cost
            total_tokens += machine_tokens
            
            # 按模型聚合
            for model, stats in report.get('by_model', {}).items():
                if model not in by_model:
                    by_model[model] = {
                        "request_count": 0,
                        "input_tokens": 0,
                        "output_tokens": 0,
                        "reasoning_tokens": 0,
                        "cache_read_tokens": 0,
                        "cache_write_tokens": 0,
                        "actual_cost_cny": 0,
                    }
                
                by_model[model]["request_count"] += stats.get("request_count", 0)
                by_model[model]["input_tokens"] += stats.get("input_tokens", 0)
                by_model[model]["output_tokens"] += stats.get("output_tokens", 0)
                by_model[model]["reasoning_tokens"] += stats.get("reasoning_tokens", 0)
                by_model[model]["cache_read_tokens"] += stats.get("cache_read_tokens", 0)
                by_model[model]["cache_write_tokens"] += stats.get("cache_write_tokens", 0)
                by_model[model]["actual_cost_cny"] += stats.get("actual_cost_cny", 0)
            
            # 按 provider 聚合
            for provider, stats in report.get('by_provider', {}).items():
                if provider not in by_provider:
                    by_provider[provider] = {
                        "request_count": 0,
                        "tokens": 0,
                        "cost_cny": 0,
                    }
                
                by_provider[provider]["request_count"] += stats.get("request_count", 0)
                by_provider[provider]["tokens"] += stats.get("tokens", 0)
                by_provider[provider]["cost_cny"] += stats.get("cost_cny", 0)
        
        return {
            "total_cost_cny": total_cost,
            "total_tokens": total_tokens,
            "by_model": by_model,
            "by_provider": by_provider,
            "by_machine": by_machine,
            "machine_count": len(snapshots),
            "timestamp": datetime.now().isoformat(),
            "window": window_key,
        }


def sync_data(monitor, sync_dir: Path, remote_url: Optional[str] = None):
    """
    同步数据的主函数
    
    Args:
        monitor: AgentMonitor 实例
        sync_dir: 同步目录
        remote_url: Git 远程仓库 URL（可选）
    """
    logger = logging.getLogger(__name__)
    
    # 初始化 Git 同步
    git_sync = GitSync(sync_dir, remote_url)
    if not git_sync.init_repo():
        logger.error("Failed to initialize Git repo")
        return False
    
    # 拉取最新数据
    if not git_sync.pull():
        logger.warning("Failed to pull latest data, continuing with local data")
    
    # 导出当前机器的快照
    machine_id = MachineIdentifier.get_machine_id()
    snapshot_path = sync_dir / 'machines' / f'{machine_id}.json'
    
    snapshot_exporter = DataSnapshot(monitor)
    snapshot_exporter.export_snapshot(snapshot_path)
    
    # 提交并推送
    if not git_sync.commit_and_push():
        logger.error("Failed to commit and push changes")
        return False
    
    logger.info("Data sync completed successfully")
    return True
