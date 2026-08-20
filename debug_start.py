#!/usr/bin/env python3
"""
调试启动脚本 - 检查前端为什么看不到数据
"""

from dashboard import create_app
from monitor import AgentMonitor
import webbrowser
import time

print("=" * 70)
print("Agent Monitor - 调试启动")
print("=" * 70)

# 创建应用
monitor = AgentMonitor()
app = create_app(monitor)

print("\n✅ 应用创建成功")
print(f"   多机模式: {monitor.config.get('multi_machine', {}).get('enabled', False)}")

# 测试 API
print("\n测试 API 端点...")
with app.test_client() as client:
    response = client.get('/api/report?days=30')
    data = response.get_json()
    
    print(f"✅ /api/report 状态: {response.status_code}")
    if data:
        print(f"   total_cost_cny: ¥{data.get('total_cost_cny', 0):.2f}")
        print(f"   total_tokens: {data.get('total_tokens', 0):,}")
        print(f"   模型数: {len(data.get('by_model', {}))}")
    else:
        print("   ⚠️ 没有数据返回")

print("\n" + "=" * 70)
print("启动 Web 服务器")
print("=" * 70)
print("\n访问地址:")
print("  🌐 主页面: http://127.0.0.1:8899/")
print("  🔧 API 测试: http://127.0.0.1:8899/test")
print("\n💡 调试提示:")
print("  1. 打开浏览器开发者工具 (F12 或 Cmd+Option+I)")
print("  2. 切换到 Console 标签")
print("  3. 查看是否有错误信息")
print("  4. 切换到 Network 标签")
print("  5. 刷新页面，查看 /api/report 请求是否成功")
print("\n按 Ctrl+C 停止服务器\n")

# 等待一秒后打开浏览器
time.sleep(1)
try:
    webbrowser.open('http://127.0.0.1:8899/')
except:
    pass

# 启动服务器
app.run(host='127.0.0.1', port=8899, debug=False)
