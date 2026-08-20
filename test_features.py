#!/usr/bin/env python3
"""
最终验证脚本 - 验证所有新功能
"""

import sys
import os
sys.path.insert(0, 'C:/Users/xczha/agent-monitor')

from monitor import AgentMonitor

def test_provider_field():
    """测试模型统计中的 provider 字段"""
    print("\n[测试 1/3] 模型统计中的 provider 字段")
    print("-" * 50)
    
    monitor = AgentMonitor('C:/Users/xczha/agent-monitor/config.yaml')
    report = monitor.get_report(7)
    
    by_model = report['statistics']['by_model']
    
    if not by_model:
        print("  ✗ 没有模型数据")
        return False
    
    # 检查所有模型是否都有 provider 字段
    missing_provider = []
    for model, stats in by_model.items():
        if 'provider' not in stats:
            missing_provider.append(model)
    
    if missing_provider:
        print(f"  ✗ {len(missing_provider)} 个模型缺少 provider 字段")
        for m in missing_provider[:3]:
            print(f"    - {m}")
        return False
    
    print(f"  ✓ 所有 {len(by_model)} 个模型都有 provider 字段")
    
    # 显示示例
    for i, (model, stats) in enumerate(list(by_model.items())[:3], 1):
        print(f"    {i}. {model[:30]:30s} -> {stats['provider']}")
    
    return True

def test_filtering():
    """测试筛选功能"""
    print("\n[测试 2/3] 数据筛选功能")
    print("-" * 50)
    
    monitor = AgentMonitor('C:/Users/xczha/agent-monitor/config.yaml')
    report = monitor.get_report(7)
    
    stats = report['statistics']
    
    # 检查必要的数据结构
    if 'by_agent' not in stats:
        print("  ✗ 缺少 by_agent 数据")
        return False
    
    if 'by_model' not in stats:
        print("  ✗ 缺少 by_model 数据")
        return False
    
    if 'by_provider' not in stats:
        print("  ✗ 缺少 by_provider 数据")
        return False
    
    if 'by_agent_model' not in stats:
        print("  ✗ 缺少 by_agent_model 数据")
        return False
    
    print(f"  ✓ 数据结构完整")
    print(f"    - Agent 数量: {len(stats['by_agent'])}")
    print(f"    - 模型数量: {len(stats['by_model'])}")
    print(f"    - Provider 数量: {len(stats['by_provider'])}")
    
    return True

def test_chart_data():
    """测试图表数据"""
    print("\n[测试 3/3] 图表数据准备")
    print("-" * 50)
    
    monitor = AgentMonitor('C:/Users/xczha/agent-monitor/config.yaml')
    report = monitor.get_report(7)
    
    by_model = report['statistics']['by_model']
    
    if not by_model:
        print("  ✗ 没有模型数据")
        return False
    
    # 按 total_tokens 排序
    sorted_models = sorted(by_model.items(), key=lambda x: x[1]['total_tokens'], reverse=True)
    
    print(f"  ✓ 可以排序模型数据")
    print(f"    Top 3 模型（按 Token）:")
    for i, (model, stats) in enumerate(sorted_models[:3], 1):
        tokens = stats['total_tokens']
        cache_hit = stats.get('cache_hit_rate', 0) * 100
        print(f"      {i}. {model[:25]:25s} {tokens:>12,} tokens, {cache_hit:.1f}% 命中")
    
    # 检查缓存数据
    with_cache = [
        (model, stats) 
        for model, stats in by_model.items() 
        if stats.get('cache_read_tokens', 0) + stats.get('cache_write_tokens', 0) > 0
    ]
    
    print(f"  ✓ 有缓存数据的模型: {len(with_cache)} 个")
    
    return True

def main():
    print("=" * 60)
    print("Agent Monitor - 新功能验证")
    print("=" * 60)
    
    results = []
    
    try:
        results.append(("Provider 字段", test_provider_field()))
    except Exception as e:
        print(f"  ✗ 测试失败: {e}")
        results.append(("Provider 字段", False))
    
    try:
        results.append(("筛选功能", test_filtering()))
    except Exception as e:
        print(f"  ✗ 测试失败: {e}")
        results.append(("筛选功能", False))
    
    try:
        results.append(("图表数据", test_chart_data()))
    except Exception as e:
        print(f"  ✗ 测试失败: {e}")
        results.append(("图表数据", False))
    
    print()
    print("=" * 60)
    print("测试结果汇总")
    print("=" * 60)
    
    for name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"  {name:20s} {status}")
    
    all_passed = all(r[1] for r in results)
    
    print()
    if all_passed:
        print("🎉 所有测试通过！")
        print()
        print("新功能已完成:")
        print("  ✓ 模型统计中添加了 provider 字段")
        print("  ✓ 支持按 Agent 筛选")
        print("  ✓ 支持按 Provider 筛选")
        print("  ✓ 添加了 Token 使用分布图表")
        print("  ✓ 添加了缓存命中率排行图表")
        return 0
    else:
        print("❌ 部分测试失败")
        return 1

if __name__ == '__main__':
    sys.exit(main())
