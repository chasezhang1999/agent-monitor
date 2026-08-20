#!/usr/bin/env python3
"""
多机同步设置向导
帮助用户配置 Git 私有仓库进行数据同步
"""

import os
import sys
import subprocess
from pathlib import Path
import yaml


def run_command(cmd, cwd=None, check=True):
    """运行命令并返回结果"""
    try:
        result = subprocess.run(
            cmd, 
            cwd=cwd, 
            check=check, 
            capture_output=True, 
            text=True
        )
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.CalledProcessError as e:
        return False, e.stdout, e.stderr
    except FileNotFoundError:
        return False, "", f"Command not found: {cmd[0]}"


def check_git():
    """检查 Git 是否安装"""
    success, _, _ = run_command(['git', '--version'], check=False)
    return success


def get_input(prompt, default=None):
    """获取用户输入"""
    if default:
        prompt = f"{prompt} [{default}]: "
    else:
        prompt = f"{prompt}: "
    
    value = input(prompt).strip()
    return value if value else default


def confirm(prompt):
    """确认提示"""
    response = input(f"{prompt} (y/n): ").strip().lower()
    return response in ['y', 'yes']


def main():
    print("=" * 70)
    print("🔧 Agent Monitor - 多机同步设置向导")
    print("=" * 70)
    print()
    
    # 检查 Git
    if not check_git():
        print("❌ Git 未安装")
        print()
        print("请先安装 Git：")
        print("  macOS:   brew install git")
        print("  Ubuntu:  sudo apt install git")
        print("  Windows: https://git-scm.com/download/win")
        sys.exit(1)
    
    print("✅ Git 已安装")
    print()
    
    # 加载配置
    config_path = Path('config.yaml')
    if not config_path.exists():
        print(f"❌ 配置文件不存在: {config_path}")
        sys.exit(1)
    
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    multi_config = config.get('multi_machine', {})
    
    # 获取配置
    print("📝 配置同步参数")
    print("-" * 70)
    print()
    
    # 同步目录
    default_sync_dir = multi_config.get('sync_dir', '~/.agent-monitor-sync')
    sync_dir = get_input("本地同步目录", default_sync_dir)
    sync_dir_path = Path(sync_dir).expanduser()
    
    # Git 远程仓库
    print()
    print("Git 远程仓库 URL (留空则只本地同步，不推送到远程)")
    print("示例:")
    print("  GitHub: https://github.com/username/agent-monitor-data.git")
    print("  私有仓库建议使用 SSH: git@github.com:username/agent-monitor-data.git")
    print()
    
    default_remote = multi_config.get('remote_url', '')
    remote_url = get_input("远程仓库 URL", default_remote or None)
    
    # 确认配置
    print()
    print("=" * 70)
    print("📋 配置摘要:")
    print(f"  同步目录: {sync_dir_path}")
    print(f"  远程仓库: {remote_url or '(无 - 仅本地同步)'}")
    print("=" * 70)
    print()
    
    if not confirm("确认配置并开始设置?"):
        print("已取消")
        sys.exit(0)
    
    print()
    print("🚀 开始设置...")
    print()
    
    # 创建同步目录
    sync_dir_path.mkdir(parents=True, exist_ok=True)
    print(f"✅ 创建同步目录: {sync_dir_path}")
    
    # 初始化 Git 仓库
    if not (sync_dir_path / '.git').exists():
        success, _, stderr = run_command(['git', 'init'], cwd=sync_dir_path)
        if success:
            print(f"✅ 初始化 Git 仓库")
        else:
            print(f"❌ 初始化失败: {stderr}")
            sys.exit(1)
        
        # 创建目录结构
        machines_dir = sync_dir_path / 'machines'
        machines_dir.mkdir(exist_ok=True)
        
        # 创建 README
        readme_path = sync_dir_path / 'README.md'
        readme_content = """# Agent Monitor - 多机数据同步

这个仓库存储来自多台机器的监控数据快照。

## 目录结构

- `machines/{machine-id}.json` - 每台机器的数据快照
- `README.md` - 说明文档

## 使用方法

每台机器运行 Agent Monitor 时会自动：
1. Pull 最新数据
2. 导出本机快照到 `machines/{hostname}.json`
3. Commit 并 Push

Dashboard 会聚合所有机器的数据展示。

## 隐私说明

此仓库包含 AI 模型使用统计数据（token 数量、费用等），
请设置为**私有仓库**以保护隐私。
"""
        readme_path.write_text(readme_content, encoding='utf-8')
        print("✅ 创建项目结构")
        
        # 创建 .gitignore
        gitignore_path = sync_dir_path / '.gitignore'
        gitignore_content = """*.pyc
__pycache__/
.DS_Store
*.log
.vscode/
.idea/
"""
        gitignore_path.write_text(gitignore_content, encoding='utf-8')
        
        # 初始提交
        run_command(['git', 'add', '-A'], cwd=sync_dir_path)
        run_command(['git', 'commit', '-m', 'Initial commit'], cwd=sync_dir_path)
        print("✅ 初始提交完成")
    else:
        print("ℹ️  Git 仓库已存在，跳过初始化")
    
    # 配置远程仓库
    if remote_url:
        # 检查 remote 是否已存在
        success, stdout, _ = run_command(['git', 'remote'], cwd=sync_dir_path, check=False)
        
        if 'origin' in stdout:
            # 更新 remote
            run_command(['git', 'remote', 'set-url', 'origin', remote_url], cwd=sync_dir_path)
            print(f"✅ 更新远程仓库 URL")
        else:
            # 添加 remote
            run_command(['git', 'remote', 'add', 'origin', remote_url], cwd=sync_dir_path)
            print(f"✅ 添加远程仓库")
        
        # 尝试推送
        print()
        print("🔄 尝试推送到远程仓库...")
        success, _, stderr = run_command(
            ['git', 'push', '-u', 'origin', 'main'], 
            cwd=sync_dir_path, 
            check=False
        )
        
        if success:
            print("✅ 推送成功")
        else:
            print(f"⚠️  推送失败: {stderr}")
            print()
            print("可能的原因:")
            print("  1. 远程仓库不存在 - 请先在 GitHub 创建仓库")
            print("  2. 没有推送权限 - 请配置 SSH key 或 Personal Access Token")
            print("  3. 分支名称不匹配 - 远程仓库可能使用 'master' 而非 'main'")
            print()
            print("💡 SSH Key 配置:")
            print("   https://docs.github.com/en/authentication/connecting-to-github-with-ssh")
            print()
    
    # 更新配置文件
    print()
    if confirm("是否更新 config.yaml 中的同步配置?"):
        config['multi_machine'] = {
            'enabled': True,
            'sync_dir': sync_dir,
            'remote_url': remote_url or "",
            'auto_sync_on_start': True,
            'show_machine_filter': True,
        }
        
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, allow_unicode=True, default_flow_style=False)
        
        print(f"✅ 已更新 {config_path}")
    
    # 完成
    print()
    print("=" * 70)
    print("🎉 设置完成！")
    print("=" * 70)
    print()
    print("📚 下一步:")
    print("  1. 在其他机器上克隆这个项目")
    print("  2. 运行相同的设置向导（使用相同的远程仓库 URL）")
    print("  3. 启动 Dashboard: ./start.sh")
    print()
    print("💡 提示:")
    print("  - 每次启动会自动同步数据")
    print("  - Dashboard 会显示所有机器的汇总统计")
    print("  - 手动同步: python3 cli.py sync")
    print("  - 查看所有机器: python3 cli.py machines")
    print()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n已取消")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        sys.exit(1)
