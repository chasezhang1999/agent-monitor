#!/usr/bin/env python3
"""
快速测试脚本 - 验证监控系统是否正常工作
"""

import sys
from pathlib import Path

# 添加当前目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent))

from monitor import AgentMonitor

def test_monitor():
    """测试监控器"""
    print("=" * 60)
    print("Agent Monitor - 快速测试")
    print("=" * 60)
    print()
    
    # 初始化
    print("📦 初始化监控器...")
    try:
        monitor = AgentMonitor()
        print("✓ 配置文件加载成功")
    except Exception as e:
        print(f"✗ 配置文件加载失败: {e}")
        return False
    
    print()
    
    # 测试 Hermes
    print("🔍 测试 Hermes 数据采集...")
    try:
        hermes_records = monitor.collect_hermes_usage(7)
        print(f"✓ 采集到 {len(hermes_records)} 条 Hermes 记录")
        if hermes_records:
            sample = hermes_records[0]
            print(f"  示例: {sample.model} | {sample.input_tokens:,} in / {sample.output_tokens:,} out")
    except Exception as e:
        print(f"✗ Hermes 采集失败: {e}")
        return False
    
    print()
    
    # 测试 OpenCode
    print("🔍 测试 OpenCode 数据采集...")
    try:
        opencode_records = monitor.collect_opencode_usage(7)
        print(f"✓ 采集到 {len(opencode_records)} 条 OpenCode 记录")
        if opencode_records:
            sample = opencode_records[0]
            print(f"  示例: {sample.model} | {sample.input_tokens:,} in / {sample.output_tokens:,} out")
    except Exception as e:
        print(f"✗ OpenCode 采集失败: {e}")
        return False
    
    print()
    
    # 生成报告
    print("📊 生成统计报告...")
    try:
        report = monitor.get_report(7)
        stats = report['statistics']['total']
        
        print(f"✓ 报告生成成功 (最近 7 天)")
        print()
        print("  总览:")
        print(f"    会话数:      {stats['sessions']}")
        print(f"    API 调用:    {stats['api_calls']:,}")
        print(f"    总 Token:    {stats['total_tokens']:,}")
        print(f"    输入 Token:  {stats['input_tokens']:,}")
        print(f"    输出 Token:  {stats['output_tokens']:,}")
        print(f"    缓存命中率:  {stats['cache_hit_rate']*100:.1f}%")
        print(f"    标准费用:    ${stats['standard_cost_usd']:.4f} USD")
        print(f"    实际费用:    ¥{stats['actual_cost_cny']:.4f} CNY")
        
        print()
        print("  按 Agent 分布:")
        for agent, agent_stats in report['statistics']['by_agent'].items():
            print(f"    {agent:10s}: {agent_stats['sessions']} 会话, {agent_stats['total_tokens']:,} tokens")
        
        print()
        print("  按模型排行 (Top 5):")
        by_model = report['statistics']['by_model']
        sorted_models = sorted(by_model.items(), key=lambda x: x[1]['total_tokens'], reverse=True)
        for i, (model, model_stats) in enumerate(sorted_models[:5], 1):
            print(f"    {i}. {model:20s}: {model_stats['total_tokens']:,} tokens")
        
    except Exception as e:
        print(f"✗ 报告生成失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print()
    print("=" * 60)
    print("✅ 所有测试通过！系统运行正常")
    print("=" * 60)
    print()
    print("下一步:")
    print("  1. 启动 Dashboard: python dashboard.py")
    print("  2. 访问: http://127.0.0.1:8899")
    print()
    
    return True

if __name__ == '__main__':
    success = test_monitor()
    sys.exit(0 if success else 1)
