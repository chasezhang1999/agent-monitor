#!/usr/bin/env python3
"""
CLI 命令行工具 - 快速查看统计
"""

import sys
import argparse
from pathlib import Path
from monitor import AgentMonitor

def format_number(n):
    """格式化数字"""
    if n >= 1_000_000:
        return f"{n/1_000_000:.2f}M"
    elif n >= 1_000:
        return f"{n/1_000:.1f}K"
    else:
        return str(n)

def print_report(report, show_details=False):
    """打印报告"""
    stats = report['statistics']
    total = stats['total']
    
    print("\n" + "="*70)
    print(f"📊 Agent Monitor Report - {report.get('period_days', 'All')} days")
    print("="*70)
    
    # 总览
    print("\n【总览】")
    print(f"  会话数:        {total['sessions']:>8}")
    print(f"  API 调用:      {total['api_calls']:>8,}")
    print(f"  总 Token:      {format_number(total['total_tokens']):>8}")
    print(f"  ├─ 输入:       {format_number(total['input_tokens']):>8}")
    print(f"  ├─ 输出:       {format_number(total['output_tokens']):>8}")
    print(f"  ├─ 推理:       {format_number(total['reasoning_tokens']):>8}")
    print(f"  ├─ 缓存读:     {format_number(total['cache_read_tokens']):>8}")
    print(f"  └─ 缓存写:     {format_number(total['cache_write_tokens']):>8}")
    print(f"  缓存命中率:    {total['cache_hit_rate']*100:>7.1f}%")
    print(f"  标准费用:      ${total['standard_cost_usd']:>7.4f} USD")
    print(f"  实际费用:      ¥{total['actual_cost_cny']:>7.4f} CNY")
    
    # 按 Agent
    print("\n【按 Agent】")
    print(f"  {'Agent':<12} {'会话':<8} {'Token':<12} {'标准费用':<12} {'实际费用':<12}")
    print("  " + "-"*60)
    for agent, agent_stats in stats['by_agent'].items():
        print(f"  {agent:<12} {agent_stats['sessions']:<8} "
              f"{format_number(agent_stats['total_tokens']):<12} "
              f"${agent_stats['standard_cost_usd']:<11.4f} "
              f"¥{agent_stats['actual_cost_cny']:<11.4f}")
    
    # 按模型 Top 10
    print("\n【按模型 Top 10】")
    print(f"  {'模型':<25} {'会话':<6} {'Token':<12} {'命中率':<8} {'实际费用':<12}")
    print("  " + "-"*70)
    sorted_models = sorted(stats['by_model'].items(), 
                          key=lambda x: x[1]['total_tokens'], 
                          reverse=True)
    for model, model_stats in sorted_models[:10]:
        print(f"  {model:<25} {model_stats['sessions']:<6} "
              f"{format_number(model_stats['total_tokens']):<12} "
              f"{model_stats['cache_hit_rate']*100:>6.1f}% "
              f"¥{model_stats['actual_cost_cny']:<11.4f}")
    
    # 详细信息
    if show_details:
        print("\n【按 Provider】")
        print(f"  {'Provider':<30} {'会话':<6} {'Token':<12} {'费用 (CNY)':<12}")
        print("  " + "-"*65)
        sorted_providers = sorted(stats['by_provider'].items(),
                                 key=lambda x: x[1]['total_tokens'],
                                 reverse=True)
        for provider, provider_stats in sorted_providers:
            print(f"  {provider:<30} {provider_stats['sessions']:<6} "
                  f"{format_number(provider_stats['total_tokens']):<12} "
                  f"¥{provider_stats['actual_cost_cny']:<11.4f}")
    
    print("\n" + "="*70 + "\n")

def main():
    parser = argparse.ArgumentParser(
        description='Agent Monitor - 监控 Hermes 和 OpenCode 的使用情况',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s                    # 全部历史
  %(prog)s -d 1               # 最近 24 小时
  %(prog)s -d 7               # 最近 7 天
  %(prog)s -d 30 --details    # 最近 30 天（详细模式）
  %(prog)s --json             # 输出 JSON 格式
        """
    )
    
    parser.add_argument('-d', '--days', type=int, default=None,
                       help='统计天数（默认全部）')
    parser.add_argument('--details', action='store_true',
                       help='显示详细信息')
    parser.add_argument('--json', action='store_true',
                       help='输出 JSON 格式')
    parser.add_argument('-c', '--config', default='config.yaml',
                       help='配置文件路径')
    
    args = parser.parse_args()
    
    # 初始化
    try:
        monitor = AgentMonitor(args.config)
    except Exception as e:
        print(f"错误: 无法加载配置文件 - {e}", file=sys.stderr)
        return 1
    
    # 生成报告
    try:
        report = monitor.get_report(args.days)
    except Exception as e:
        print(f"错误: 生成报告失败 - {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1
    
    # 输出
    if args.json:
        import json
        print(json.dumps(report, indent=2, ensure_ascii=False, default=str))
    else:
        print_report(report, args.details)
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
