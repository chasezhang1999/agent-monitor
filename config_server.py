#!/usr/bin/env python3
"""
价格配置管理 API
"""

from flask import Flask, render_template, jsonify, request
from monitor import AgentMonitor
import yaml
import json
from pathlib import Path

app = Flask(__name__)
monitor = AgentMonitor()

@app.route('/config')
def config_page():
    """价格配置页面"""
    return render_template('config.html')

@app.route('/api/config/pricing')
def get_pricing_config():
    """获取完整价格配置"""
    with open('config.yaml', 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    return jsonify(config.get('pricing', {}))

@app.route('/api/config/pricing', methods=['POST'])
def update_pricing_config():
    """更新价格配置"""
    try:
        new_pricing = request.json
        
        # 读取当前配置
        with open('config.yaml', 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        # 更新 pricing 部分
        config['pricing'] = new_pricing
        
        # 备份原配置
        backup_path = Path('config.yaml.backup')
        Path('config.yaml').rename(backup_path)
        
        # 写入新配置
        with open('config.yaml', 'w', encoding='utf-8') as f:
            yaml.dump(config, f, allow_unicode=True, default_flow_style=False)
        
        # 清除缓存
        clear_cache()
        
        # 重新加载配置
        global monitor
        monitor = AgentMonitor()
        
        return jsonify({'success': True, 'message': '配置已更新'})
    
    except Exception as e:
        # 恢复备份
        if backup_path.exists():
            backup_path.rename('config.yaml')
        return jsonify({'success': False, 'error': str(e)}), 500

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

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8900, debug=True)
