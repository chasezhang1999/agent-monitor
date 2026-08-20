#!/usr/bin/env python3
"""
Agent Monitor Dashboard - Web 界面
"""

from flask import Flask, render_template, jsonify, request
from monitor import AgentMonitor
from multi_machine import MultiMachineAggregator, sync_data
from pathlib import Path
import json
import yaml
from datetime import datetime


def create_app(monitor_instance=None):
    """创建 Flask 应用"""
    app = Flask(__name__)
    
    if monitor_instance:
        monitor = monitor_instance
    else:
        monitor = AgentMonitor()
    
    # 检查是否启用多机模式
    multi_config = monitor.config.get('multi_machine', {})
    multi_enabled = multi_config.get('enabled', False)
    
    if multi_enabled:
        sync_dir = Path(multi_config.get('sync_dir', '~/.agent-monitor-sync')).expanduser()
        aggregator = MultiMachineAggregator(sync_dir)
    else:
        aggregator = None
    
    @app.route('/')
    def index():
        """首页"""
        return render_template('index.html', 
                             multi_enabled=multi_enabled,
                             show_machine_filter=multi_config.get('show_machine_filter', True))
    
    @app.route('/debug')
    def debug_page():
        """调试页面"""
        return render_template('debug.html')
    
    @app.route('/test')
    def test_page():
        """测试页面"""
        return app.send_static_file('../test_frontend.html')
    
    @app.route('/config')
    def config_page():
        """价格配置页面"""
        return render_template('config.html')
    
    @app.route('/api/report')
    def api_report():
        """获取报告 API"""
        days = request.args.get('days', type=int, default=None)
        machine_id = request.args.get('machine', default='local')
        
        # 如果启用多机模式且请求聚合数据
        if multi_enabled and aggregator and machine_id == 'all':
            report = aggregator.aggregate_report(days)
            report['is_aggregated'] = True
            report['source'] = 'multi_machine'
        else:
            # 单机模式或请求特定机器
            raw_report = monitor.get_report(days)
            
            # 转换数据格式以匹配前端期望
            stats = raw_report.get('statistics', {})
            total = stats.get('total', {})
            
            report = {
                'total_cost_cny': total.get('actual_cost_cny', 0),
                'total_tokens': total.get('total_tokens', 0),
                'total_requests': total.get('api_calls', 0),
                'by_model': {},
                'by_provider': {},
                'is_aggregated': False,
                'source': 'local',
                'generated_at': raw_report.get('generated_at'),
                'period_days': raw_report.get('period_days')
            }
            
            # 转换 by_model
            for model, model_stats in stats.get('by_model', {}).items():
                report['by_model'][model] = {
                    'request_count': model_stats.get('api_calls', 0),
                    'input_tokens': model_stats.get('input_tokens', 0),
                    'output_tokens': model_stats.get('output_tokens', 0),
                    'reasoning_tokens': model_stats.get('reasoning_tokens', 0),
                    'cache_read_tokens': model_stats.get('cache_read_tokens', 0),
                    'cache_write_tokens': model_stats.get('cache_write_tokens', 0),
                    'actual_cost_cny': model_stats.get('actual_cost_cny', 0),
                    'provider': model_stats.get('provider', 'unknown')  # 添加 provider
                }
            
            # 新增：按模型-供应商组合
            report['by_model_provider'] = {}
            
            # 获取所有记录
            hermes_records = monitor.collect_hermes_usage(days)
            opencode_records = monitor.collect_opencode_usage(days)
            all_records = hermes_records + opencode_records
            
            for record in all_records:
                key = f"{record.model}@{record.provider_display}"
                if key not in report['by_model_provider']:
                    report['by_model_provider'][key] = {
                        'model': record.model,
                        'provider': record.provider_display,
                        'request_count': 0,
                        'input_tokens': 0,
                        'output_tokens': 0,
                        'reasoning_tokens': 0,
                        'cache_read_tokens': 0,
                        'cache_write_tokens': 0,
                        'actual_cost_cny': 0
                    }
                
                mp = report['by_model_provider'][key]
                mp['request_count'] += record.api_calls
                mp['input_tokens'] += record.input_tokens
                mp['output_tokens'] += record.output_tokens
                mp['reasoning_tokens'] += record.reasoning_tokens
                mp['cache_read_tokens'] += record.cache_read_tokens
                mp['cache_write_tokens'] += record.cache_write_tokens
                mp['actual_cost_cny'] += record.actual_cost_cny
            
            # 转换 by_provider
            for provider, prov_stats in stats.get('by_provider', {}).items():
                report['by_provider'][provider] = {
                    'request_count': prov_stats.get('api_calls', 0),
                    'tokens': prov_stats.get('total_tokens', 0),
                    'cost_cny': prov_stats.get('actual_cost_cny', 0)
                }
            
            # 添加本机标识
            from multi_machine import MachineIdentifier
            report['machine_id'] = MachineIdentifier.get_machine_id()
            report['hostname'] = MachineIdentifier.get_hostname()
        
        return jsonify(report)
    
    @app.route('/api/machines')
    def api_machines():
        """获取所有机器列表 API"""
        if not multi_enabled or not aggregator:
            return jsonify({'enabled': False, 'machines': []})
        
        snapshots = aggregator.load_all_snapshots()
        
        machines = []
        for machine_id, snapshot in snapshots.items():
            machines.append({
                'id': machine_id,
                'hostname': snapshot.get('hostname'),
                'timestamp': snapshot.get('timestamp'),
                'last_update': snapshot.get('timestamp'),
            })
        
        return jsonify({
            'enabled': True,
            'machines': machines,
            'count': len(machines)
        })
    
    @app.route('/api/sync', methods=['POST'])
    def api_sync():
        """手动同步 API"""
        if not multi_enabled:
            return jsonify({'success': False, 'error': 'Multi-machine sync not enabled'}), 400
        
        try:
            sync_dir = Path(multi_config['sync_dir']).expanduser()
            remote_url = multi_config.get('remote_url') or None
            
            success = sync_data(monitor, sync_dir, remote_url)
            
            if success:
                return jsonify({'success': True, 'message': 'Sync completed'})
            else:
                return jsonify({'success': False, 'error': 'Sync failed'}), 500
                
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/api/pricing/<model>')
    def api_pricing(model):
        """获取模型价格信息 API"""
        pricing_config = monitor.config.get('pricing', {})
        
        # 获取标准价格
        standard_prices = pricing_config.get('standard_prices', {})
        model_price = standard_prices.get(model)
        
        if not model_price:
            return jsonify({'error': 'Model not found'}), 404
        
        # 获取所有 provider 倍率
        multipliers = pricing_config.get('provider_multipliers', {})
        
        return jsonify({
            'model': model,
            'standard_prices': model_price,
            'provider_multipliers': multipliers,
            'cny_to_usd_rate': pricing_config.get('cny_to_usd_rate', 12)
        })
    
    @app.route('/api/config/pricing')
    def get_pricing_config():
        """获取完整价格配置"""
        return jsonify(monitor.config.get('pricing', {}))
    
    @app.route('/api/config/pricing/model', methods=['POST'])
    def add_or_update_model_price():
        """添加或更新模型价格"""
        try:
            data = request.json
            model_name = data['model']
            prices = data['prices']
            
            with open('config.yaml', 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            if 'pricing' not in config:
                config['pricing'] = {}
            if 'standard_prices' not in config['pricing']:
                config['pricing']['standard_prices'] = {}
            
            config['pricing']['standard_prices'][model_name] = prices
            
            with open('config.yaml', 'w', encoding='utf-8') as f:
                yaml.dump(config, f, allow_unicode=True, default_flow_style=False)
            
            clear_cache()
            
            # 重新加载配置
            nonlocal monitor
            monitor = AgentMonitor()
            
            return jsonify({'success': True, 'message': f'模型 {model_name} 价格已更新'})
        
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/api/config/pricing/provider', methods=['POST'])
    def add_or_update_provider_multiplier():
        """添加或更新 Provider 倍率"""
        try:
            data = request.json
            provider_name = data['provider']
            multiplier = data['multiplier']
            
            with open('config.yaml', 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            if 'pricing' not in config:
                config['pricing'] = {}
            if 'provider_multipliers' not in config['pricing']:
                config['pricing']['provider_multipliers'] = {}
            
            config['pricing']['provider_multipliers'][provider_name] = float(multiplier)
            
            with open('config.yaml', 'w', encoding='utf-8') as f:
                yaml.dump(config, f, allow_unicode=True, default_flow_style=False)
            
            clear_cache()
            
            # 重新加载配置
            nonlocal monitor
            monitor = AgentMonitor()
            
            return jsonify({'success': True, 'message': f'Provider {provider_name} 倍率已更新'})
        
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/api/cache/clear', methods=['POST'])
    def clear_cache_api():
        """清除缓存 API"""
        try:
            clear_cache()
            return jsonify({'success': True, 'message': '缓存已清除'})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500
    
    def clear_cache():
        """清除所有缓存"""
        import sqlite3
        cache_db = Path('cache/reports.db')
        if cache_db.exists():
            conn = sqlite3.connect(cache_db)
            cursor = conn.cursor()
            cursor.execute('DELETE FROM report_cache')
            conn.commit()
            conn.close()
    
    @app.route('/api/records')
    def api_records():
        """获取原始记录 API"""
        days = request.args.get('days', type=int, default=None)
        agent = request.args.get('agent', default=None)
        
        # 采集数据
        hermes_records = monitor.collect_hermes_usage(days)
        opencode_records = monitor.collect_opencode_usage(days)
        
        if agent == 'hermes':
            records = hermes_records
        elif agent == 'opencode':
            records = opencode_records
        else:
            records = hermes_records + opencode_records
        
        # 转换为 dict
        records_dict = []
        for r in records:
            rd = {
                'agent': r.agent,
                'session_id': r.session_id,
                'model': r.model,
                'provider': r.provider,
                'provider_display': r.provider_display,
                'api_calls': r.api_calls,
                'input_tokens': r.input_tokens,
                'output_tokens': r.output_tokens,
                'cache_read_tokens': r.cache_read_tokens,
                'cache_write_tokens': r.cache_write_tokens,
                'reasoning_tokens': r.reasoning_tokens,
                'total_tokens': r.total_tokens,
                'cache_hit_rate': round(r.cache_hit_rate * 100, 2),
                'standard_cost_usd': round(r.standard_cost_usd, 4),
                'actual_cost_cny': round(r.actual_cost_cny, 4),
                'first_seen': r.first_seen.isoformat() if r.first_seen else None,
                'last_seen': r.last_seen.isoformat() if r.last_seen else None
            }
            records_dict.append(rd)
        
        return jsonify({
            'count': len(records_dict),
            'records': records_dict
        })
    
    @app.route('/api/config')
    def api_config():
        """获取配置"""
        return jsonify(monitor.config)
    
    def format_number(n):
        """格式化数字"""
        if n >= 1_000_000:
            return f"{n/1_000_000:.2f}M"
        elif n >= 1_000:
            return f"{n/1_000:.2f}K"
        else:
            return str(n)
    
    def format_currency(n):
        """格式化货币"""
        return f"{n:.4f}"
    
    # 注册模板过滤器
    app.jinja_env.filters['format_number'] = format_number
    app.jinja_env.filters['format_currency'] = format_currency
    
    return app


if __name__ == '__main__':
    monitor = AgentMonitor()
    app = create_app(monitor)
    
    config = monitor.config.get('monitor', {}).get('dashboard', {})
    host = config.get('host', '127.0.0.1')
    port = config.get('port', 8899)
    
    print(f"Starting Agent Monitor Dashboard at http://{host}:{port}")
    app.run(host=host, port=port, debug=True)
