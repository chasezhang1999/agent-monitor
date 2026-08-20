#!/usr/bin/env python3
"""
Agent Monitor Dashboard - Web 界面
"""

from flask import Flask, render_template, jsonify, request
from monitor import AgentMonitor
import json
from datetime import datetime

app = Flask(__name__)
monitor = AgentMonitor()

@app.route('/')
def index():
    """首页"""
    return render_template('index.html')

@app.route('/config')
def config_page():
    """价格配置页面"""
    return render_template('config.html')

@app.route('/api/report')
def api_report():
    """获取报告 API"""
    days = request.args.get('days', type=int, default=None)
    report = monitor.get_report(days)
    return jsonify(report)

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
        global monitor
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
        global monitor
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
    from pathlib import Path
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

if __name__ == '__main__':
    config = monitor.config.get('monitor', {}).get('dashboard', {})
    host = config.get('host', '127.0.0.1')
    port = config.get('port', 8899)
    
    print(f"Starting Agent Monitor Dashboard at http://{host}:{port}")
    app.run(host=host, port=port, debug=True)
