#!/usr/bin/env python3
"""
快速测试脚本 - 验证多机同步和新 UI
"""

import sys
from pathlib import Path

print("=" * 70)
print("Agent Monitor - 功能测试")
print("=" * 70)
print()

# 测试导入
print("1. 测试模块导入...")
try:
    from monitor import AgentMonitor
    from multi_machine import MachineIdentifier, DataSnapshot, GitSync, MultiMachineAggregator
    from dashboard import create_app
    print("   ✅ 所有模块导入成功")
except Exception as e:
    print(f"   ❌ 导入失败: {e}")
    sys.exit(1)

# 测试配置加载
print("\n2. 测试配置加载...")
try:
    monitor = AgentMonitor()
    print(f"   ✅ 配置加载成功")
    print(f"      Hermes: {'启用' if monitor.config['sources']['hermes']['enabled'] else '禁用'}")
    print(f"      OpenCode: {'启用' if monitor.config['sources']['opencode']['enabled'] else '禁用'}")
    
    multi_config = monitor.config.get('multi_machine', {})
    if multi_config.get('enabled'):
        print(f"      多机同步: 启用")
        print(f"      同步目录: {multi_config.get('sync_dir')}")
    else:
        print(f"      多机同步: 禁用")
except Exception as e:
    print(f"   ❌ 配置加载失败: {e}")
    sys.exit(1)

# 测试机器标识
print("\n3. 测试机器标识...")
try:
    machine_id = MachineIdentifier.get_machine_id()
    hostname = MachineIdentifier.get_hostname()
    print(f"   ✅ 机器识别成功")
    print(f"      Machine ID: {machine_id}")
    print(f"      Hostname: {hostname}")
except Exception as e:
    print(f"   ❌ 机器识别失败: {e}")

# 测试数据采集
print("\n4. 测试数据采集...")
try:
    report = monitor.get_report(days=30)
    print(f"   ✅ 数据采集成功")
    print(f"      消费金额: ¥{report['total_cost_cny']:.2f}")
    print(f"      Tokens: {report['total_tokens']:,}")
    print(f"      请求数: {report['total_requests']:,}")
    print(f"      模型数: {len(report.get('by_model', {}))}")
except Exception as e:
    print(f"   ❌ 数据采集失败: {e}")

# 测试 Flask 应用创建
print("\n5. 测试 Flask 应用...")
try:
    app = create_app(monitor)
    print(f"   ✅ Flask 应用创建成功")
    print(f"      路由数: {len(app.url_map._rules)}")
except Exception as e:
    print(f"   ❌ Flask 应用创建失败: {e}")

# 测试多机同步（如果启用）
if multi_config.get('enabled'):
    print("\n6. 测试多机同步模块...")
    try:
        sync_dir = Path(multi_config['sync_dir']).expanduser()
        
        # 测试数据快照导出
        snapshot_exporter = DataSnapshot(monitor)
        test_snapshot_path = sync_dir / 'machines' / f'test-{machine_id}.json'
        test_snapshot_path.parent.mkdir(parents=True, exist_ok=True)
        
        snapshot = snapshot_exporter.export_snapshot(test_snapshot_path)
        print(f"   ✅ 快照导出成功")
        print(f"      快照文件: {test_snapshot_path}")
        print(f"      包含报告: {list(snapshot['reports'].keys())}")
        
        # 清理测试文件
        if test_snapshot_path.exists():
            test_snapshot_path.unlink()
        
        # 测试聚合器
        aggregator = MultiMachineAggregator(sync_dir)
        snapshots = aggregator.load_all_snapshots()
        print(f"   ✅ 聚合器测试成功")
        print(f"      发现机器数: {len(snapshots)}")
        
        if snapshots:
            for mid, snap in list(snapshots.items())[:3]:
                print(f"        - {mid} ({snap.get('hostname')})")
        
    except Exception as e:
        print(f"   ⚠️  多机同步测试失败: {e}")

print("\n" + "=" * 70)
print("测试完成！")
print("=" * 70)
print()
print("📚 下一步:")
print("  1. 启动 Dashboard: ./start.sh")
print("  2. 访问: http://127.0.0.1:8899")
print("  3. 设置多机同步: python3 setup_sync.py")
print()
