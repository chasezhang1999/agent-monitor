# Agent Monitor - 多机数据同步使用指南

## 📖 概述

Agent Monitor 现在支持**多机数据同步**功能：
- ✅ 通过 Git 私有仓库同步数据
- ✅ 每次启动自动 pull → export → push
- ✅ Dashboard 自动聚合所有机器的数据
- ✅ 支持按机器筛选查看

## 🚀 快速开始

### 1. 首次设置（第一台机器）

```bash
cd ~/Code/agent-monitor

# 运行设置向导
python3 setup_sync.py
```

向导会引导你：
1. 选择本地同步目录（默认 `~/.agent-monitor-sync`）
2. 输入 Git 远程仓库 URL（建议私有仓库）
3. 自动初始化 Git 仓库并推送

**示例仓库 URL：**
```
# GitHub SSH (推荐)
git@github.com:yourusername/agent-monitor-data.git

# GitHub HTTPS
https://github.com/yourusername/agent-monitor-data.git
```

### 2. 其他机器设置

在其他机器上：

```bash
# 1. 克隆 agent-monitor 项目
git clone <your-agent-monitor-repo>
cd agent-monitor

# 2. 运行设置向导（使用相同的远程 URL）
python3 setup_sync.py
```

### 3. 日常使用

```bash
# 启动 Dashboard（会自动同步）
./start.sh

# 或直接运行
python3 cli.py dashboard
```

**启动时自动执行：**
1. 📥 Pull 最新数据（从其他机器）
2. 📊 导出本机快照
3. 📤 Push 到远程仓库
4. 🌐 启动 Dashboard

## 🔧 高级功能

### 手动同步

```bash
# 立即同步数据
python3 cli.py sync
```

### 查看所有机器

```bash
# 列出已同步的机器
python3 cli.py machines
```

输出示例：
```
🖥️  Found 3 machines:
==================================================================

  chases-macbook-pro-2021
    Hostname: Chases-MacBook-Pro-2021.local
    Last Update: 2026-08-20T20:30:15
    30d Cost: ¥125.34
    30d Tokens: 15,234,567

  asus-desktop
    Hostname: ASUS-WIN11
    Last Update: 2026-08-20T19:45:22
    30d Cost: ¥89.12
    30d Tokens: 10,123,456
```

### 生成报告

```bash
# 生成 30 天报告（聚合所有机器）
python3 cli.py report --days 30

# 生成 7 天报告
python3 cli.py report --days 7
```

## 📁 数据结构

### 本地同步目录

```
~/.agent-monitor-sync/
├── .git/                          # Git 仓库
├── machines/
│   ├── chases-macbook-pro-2021.json    # Mac 的数据快照
│   ├── asus-desktop.json               # Windows 的数据快照
│   └── ubuntu-server.json              # Linux 的数据快照
└── README.md
```

### 快照数据格式

每个 `{machine-id}.json` 包含：

```json
{
  "machine_id": "chases-macbook-pro-2021",
  "hostname": "Chases-MacBook-Pro-2021.local",
  "timestamp": "2026-08-20T20:30:15",
  "reports": {
    "1d": { /* 最近 1 天的统计 */ },
    "7d": { /* 最近 7 天的统计 */ },
    "30d": { /* 最近 30 天的统计 */ },
    "90d": { /* 最近 90 天的统计 */ }
  },
  "metadata": {
    "monitor_version": "1.0",
    "hermes_enabled": true,
    "opencode_enabled": true
  }
}
```

## ⚙️ 配置选项

在 `config.yaml` 中：

```yaml
multi_machine:
  enabled: true                          # 启用多机同步
  sync_dir: ~/.agent-monitor-sync        # 本地同步目录
  remote_url: "git@github.com:..."       # Git 远程仓库（留空=仅本地）
  auto_sync_on_start: true               # 启动时自动同步
  show_machine_filter: true              # Dashboard 显示机器筛选器
```

## 🔐 安全建议

### 1. 使用私有仓库

数据包含 AI 使用统计（token、费用），请务必使用**私有仓库**：

- GitHub: 创建时选择 "Private"
- GitLab: 创建时选择 "Private"

### 2. SSH Key 认证（推荐）

比 HTTPS + Personal Access Token 更安全：

```bash
# 生成 SSH Key
ssh-keygen -t ed25519 -C "your_email@example.com"

# 添加到 GitHub
# Settings → SSH and GPG keys → New SSH key
cat ~/.ssh/id_ed25519.pub
```

### 3. 数据内容

快照数据包含：
- ✅ Token 数量、费用统计
- ✅ 模型名称、Provider 名称
- ❌ **不包含**对话内容
- ❌ **不包含**API Key

## 🐛 故障排除

### Push 失败："Permission denied"

**原因：** SSH Key 未配置或权限不足

**解决：**
```bash
# 1. 检查 SSH Key
ssh -T git@github.com

# 2. 如果失败，重新配置 SSH Key
# 参考: https://docs.github.com/en/authentication/connecting-to-github-with-ssh
```

### 数据不同步

**检查步骤：**

1. 确认 Git 仓库正常：
   ```bash
   cd ~/.agent-monitor-sync
   git status
   git log --oneline -5
   ```

2. 手动同步测试：
   ```bash
   python3 cli.py sync -v
   ```

3. 查看日志：
   ```bash
   tail -f logs/monitor.log
   ```

### 机器识别错误

机器 ID 基于 `hostname`，如果看到重复或错误的机器名：

```bash
# 查看当前 hostname
hostname

# 修改 hostname (macOS)
sudo scutil --set HostName new-name

# 修改 hostname (Linux)
sudo hostnamectl set-hostname new-name
```

## 📊 Dashboard 多机功能

启动后访问 http://127.0.0.1:8899

**新增功能：**
- 🖥️ 机器筛选器（顶部下拉框）
- 📈 聚合统计（所有机器汇总）
- 🔄 最后同步时间显示
- 💡 每台机器的贡献占比

## 🎯 最佳实践

### 1. 定期同步

虽然启动时自动同步，但建议：
- 长时间运行时，偶尔手动 `python3 cli.py sync`
- 或配置 cron 定时同步

### 2. 命名规范

为机器设置有意义的 hostname：
- ✅ `chases-macbook-pro-2021`
- ✅ `asus-work-desktop`
- ❌ `localhost`
- ❌ `computer-1`

### 3. 数据备份

Git 仓库本身就是备份，但建议：
- 定期检查远程仓库是否正常
- 重要数据额外导出 CSV

## 🆘 需要帮助？

- 📖 完整文档：`README.md`
- 🐛 问题反馈：GitHub Issues
- 💬 讨论交流：GitHub Discussions
