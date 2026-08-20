#!/usr/bin/env python3
"""
Ad-hoc 验证：图表优化
"""
import tempfile
import os
import sys

verify_script = """
# 验证图表优化
print("=" * 70)
print("Ad-hoc Verification: Chart.js 图表优化")
print("=" * 70)
print()

# 1. 验证 Chart.js 引入
print("[1/3] 验证 Chart.js CDN 引入...")
with open('C:/Users/xczha/agent-monitor/templates/index.html', 'r', encoding='utf-8') as f:
    html = f.read()
    if 'chart.js@4.4.1' in html:
        print("✓ Chart.js CDN 已引入")
    else:
        print("✗ Chart.js CDN 未找到")
        sys.exit(1)

# 2. 验证图表函数
print()
print("[2/3] 验证图表渲染函数...")
functions = [
    'renderTokenChart',
    'renderCostChart', 
    'renderCacheChart',
    'renderProviderChart'
]
for func in functions:
    if func in html:
        print(f"✓ {func} 函数已定义")
    else:
        print(f"✗ {func} 函数缺失")
        sys.exit(1)

# 3. 验证 Canvas 元素
print()
print("[3/3] 验证 Canvas 元素...")
canvases = [
    'id="tokenChart"',
    'id="costChart"',
    'id="cacheChart"',
    'id="providerChart"'
]
for canvas in canvases:
    if canvas in html:
        print(f"✓ {canvas} 元素已创建")
    else:
        print(f"✗ {canvas} 元素缺失")
        sys.exit(1)

print()
print("=" * 70)
print("✅ 所有验证通过")
print("=" * 70)
print()
print("实现的图表:")
print("  1. Token 使用排行 - 堆叠柱状图")
print("  2. 费用分布 - 环形图")
print("  3. 缓存命中率 - 横向柱状图")
print("  4. Provider 分布 - 饼图")
print()
print("UI 验证:")
print("  启动 Dashboard: python dashboard.py")
print("  访问: http://127.0.0.1:8899")
"""

# 创建临时文件
with tempfile.NamedTemporaryFile(mode='w', suffix='.py', prefix='hermes-verify-charts-',
                                  dir=os.environ.get('TEMP'), delete=False) as f:
    f.write(verify_script)
    temp_path = f.name

print(f"Created: {temp_path}")

# 运行验证
import subprocess
result = subprocess.run(['python', temp_path], capture_output=True, text=True)
print(result.stdout)
if result.stderr:
    print("STDERR:", result.stderr)

# 清理
try:
    os.unlink(temp_path)
except:
    pass

sys.exit(result.returncode)
