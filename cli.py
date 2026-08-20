#!/usr/bin/env python3
"""
CLI 命令行工具
"""

import argparse
import sys
from pathlib import Path
import logging

from monitor import AgentMonitor
from multi_machine import sync_data, MultiMachineAggregator


def setup_logging(level='INFO'):
    """配置日志"""
    logging.basicConfig(
        level=getattr(logging, level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


def cmd_report(args):
    """生成报告"""
    setup_logging(args.verbose and 'DEBUG' or 'INFO')
    
    monitor = AgentMonitor(args.config)
    
    # 如果启用多机模式，先同步
    if monitor.config.get('multi_machine', {}).get('enabled'):
        sync_config = monitor.config['multi_machine']
        if sync_config.get('auto_sync_on_start', True):
            print("🔄 Syncing data from all machines...")
            sync_dir = Path(sync_config['sync_dir']).expanduser()
            remote_url = sync_config.get('remote_url') or None
            
            if sync_data(monitor, sync_dir, remote_url):
                print("✅ Sync completed\n")
            else:
                print("⚠️  Sync failed, using local data only\n")
    
    report = monitor.generate_report(days=args.days)
    
    print(f"\n📊 Agent Monitor Report - Last {args.days or 'All'} Days")
    print("=" * 60)
    print(f"Total Cost: ¥{report['total_cost_cny']:.2f} CNY")
    print(f"Total Tokens: {report['total_tokens']:,}")
    print(f"Total Requests: {report['total_requests']:,}")
    
    if report.get('by_model'):
        print("\n📈 By Model:")
        for model, stats in sorted(report['by_model'].items(), 
                                   key=lambda x: x[1]['actual_cost_cny'], 
                                   reverse=True):
            print(f"  {model}:")
            print(f"    Cost: ¥{stats['actual_cost_cny']:.2f}")
            print(f"    Tokens: {stats['input_tokens'] + stats['output_tokens']:,}")
            print(f"    Requests: {stats['request_count']}")


def cmd_sync(args):
    """手动同步数据"""
    setup_logging(args.verbose and 'DEBUG' or 'INFO')
    
    monitor = AgentMonitor(args.config)
    sync_config = monitor.config.get('multi_machine', {})
    
    if not sync_config.get('enabled'):
        print("❌ Multi-machine sync is not enabled in config.yaml")
        sys.exit(1)
    
    sync_dir = Path(sync_config['sync_dir']).expanduser()
    remote_url = sync_config.get('remote_url') or None
    
    print("🔄 Syncing data...")
    if sync_data(monitor, sync_dir, remote_url):
        print("✅ Sync completed successfully")
    else:
        print("❌ Sync failed")
        sys.exit(1)


def cmd_machines(args):
    """列出所有机器"""
    setup_logging(args.verbose and 'DEBUG' or 'INFO')
    
    monitor = AgentMonitor(args.config)
    sync_config = monitor.config.get('multi_machine', {})
    
    if not sync_config.get('enabled'):
        print("❌ Multi-machine sync is not enabled in config.yaml")
        sys.exit(1)
    
    sync_dir = Path(sync_config['sync_dir']).expanduser()
    aggregator = MultiMachineAggregator(sync_dir)
    
    snapshots = aggregator.load_all_snapshots()
    
    if not snapshots:
        print("📭 No machine data found")
        print(f"   Sync directory: {sync_dir}")
        return
    
    print(f"\n🖥️  Found {len(snapshots)} machines:")
    print("=" * 60)
    
    for machine_id, snapshot in sorted(snapshots.items()):
        hostname = snapshot.get('hostname', machine_id)
        timestamp = snapshot.get('timestamp', 'N/A')
        print(f"\n  {machine_id}")
        print(f"    Hostname: {hostname}")
        print(f"    Last Update: {timestamp}")
        
        # 显示 30 天统计
        reports = snapshot.get('reports', {})
        if '30d' in reports and reports['30d']:
            report = reports['30d']
            print(f"    30d Cost: ¥{report.get('total_cost_cny', 0):.2f}")
            print(f"    30d Tokens: {report.get('total_tokens', 0):,}")


def cmd_dashboard(args):
    """启动 Web Dashboard"""
    setup_logging(args.verbose and 'DEBUG' or 'INFO')
    
    from dashboard import create_app
    
    monitor = AgentMonitor(args.config)
    
    # 如果启用多机模式且配置了自动同步，启动时同步一次
    if monitor.config.get('multi_machine', {}).get('enabled'):
        sync_config = monitor.config['multi_machine']
        if sync_config.get('auto_sync_on_start', True):
            print("🔄 Syncing data before starting dashboard...")
            sync_dir = Path(sync_config['sync_dir']).expanduser()
            remote_url = sync_config.get('remote_url') or None
            
            if sync_data(monitor, sync_dir, remote_url):
                print("✅ Sync completed\n")
            else:
                print("⚠️  Sync failed, using local data only\n")
    
    app = create_app(monitor)
    
    dashboard_config = monitor.config.get('monitor', {}).get('dashboard', {})
    host = args.host or dashboard_config.get('host', '127.0.0.1')
    port = args.port or dashboard_config.get('port', 8899)
    
    print(f"\n🚀 Starting dashboard at http://{host}:{port}")
    print("   Press Ctrl+C to stop\n")
    
    app.run(host=host, port=port, debug=args.debug)


def main():
    parser = argparse.ArgumentParser(
        description='Agent Monitor - Monitor token usage and costs'
    )
    parser.add_argument('-c', '--config', default='config.yaml',
                       help='Config file path (default: config.yaml)')
    parser.add_argument('-v', '--verbose', action='store_true',
                       help='Verbose output')
    
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # report 命令
    report_parser = subparsers.add_parser('report', help='Generate usage report')
    report_parser.add_argument('-d', '--days', type=int, default=30,
                              help='Time window in days (default: 30)')
    report_parser.set_defaults(func=cmd_report)
    
    # sync 命令
    sync_parser = subparsers.add_parser('sync', help='Sync data with Git repo')
    sync_parser.set_defaults(func=cmd_sync)
    
    # machines 命令
    machines_parser = subparsers.add_parser('machines', help='List all machines')
    machines_parser.set_defaults(func=cmd_machines)
    
    # dashboard 命令（默认）
    dashboard_parser = subparsers.add_parser('dashboard', help='Start web dashboard')
    dashboard_parser.add_argument('--host', help='Host to bind to')
    dashboard_parser.add_argument('--port', type=int, help='Port to bind to')
    dashboard_parser.add_argument('--debug', action='store_true', help='Debug mode')
    dashboard_parser.set_defaults(func=cmd_dashboard)
    
    args = parser.parse_args()
    
    # 默认启动 dashboard
    if not args.command:
        args.command = 'dashboard'
        args.host = None
        args.port = None
        args.debug = False
        cmd_dashboard(args)
    else:
        if hasattr(args, 'func'):
            args.func(args)
        else:
            parser.print_help()


if __name__ == '__main__':
    main()
