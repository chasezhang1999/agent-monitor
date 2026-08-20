# Agent Monitor - 快速开始

一个跨平台的 AI Agent 监控工具，追踪 Hermes 和 OpenCode 的 token 使用和费用。

## ✨ 特性

- 📊 实时监控 token 使用和费用
- 🌐 Web Dashboard 可视化
- 🖥️ **多机数据同步**（通过 Git 私有仓库）
- 💰 自动计算实际费用（支持 apiclaude 倍率）
- 📈 多时间窗口统计（1天/7天/30天/90天）
- 🎨 **DeepSeek 风格 UI**（即将推出）

## 🚀 快速开始

### 单机使用

```bash
# 1. 克隆项目
git clone https://github.com/chasezhang1999/agent-monitor.git
cd agent-monitor

# 2. 启动（会自动创建虚拟环境并安装依赖）
./start.sh          # macOS/Linux
# 或
start.bat           # Windows

# 3. 打开浏览器访问
# http://127.0.0.1:8899
```

### 多机数据同步

如果你在多台机器上使用 AI Agent，想统一查看所有机器的用量：

```bash
# 1. 首台机器：运行设置向导
python3 setup_sync.py

# 按提示输入 Git 私有仓库 URL（如 git@github.com:你的用户名/agent-monitor-data.git）

# 2. 其他机器：重复上述步骤（使用相同的仓库 URL）

# 3. 启动 Dashboard（会自动同步）
./start.sh
```

**工作原理：**
- 每次启动自动 pull 最新数据
- 导出本机快照并 push
- Dashboard 自动聚合所有机器的数据

详细说明：[多机同步指南](MULTI_MACHINE_GUIDE.md)

## 📋 系统要求

- Python 3.8+
- Git（多机同步需要）
- Hermes 或 OpenCode（至少一个）

### 支持的平台

- ✅ macOS
- ✅ Windows
- ✅ Linux

数据库路径自动探测，一份配置跨平台通用。

## 🔧 命令行工具

```bash
# 启动 Web Dashboard
python3 cli.py dashboard

# 生成报告
python3 cli.py report --days 30

# 同步数据（多机模式）
python3 cli.py sync

# 查看所有机器
python3 cli.py machines
```

## ⚙️ 配置

编辑 `config.yaml`：

```yaml
# 数据源（自动探测路径）
sources:
  hermes:
    enabled: true
    db_path: auto        # 自动探测
  opencode:
    enabled: true
    db_path: auto

# 多机同步
multi_machine:
  enabled: true          # 启用多机功能
  sync_dir: ~/.agent-monitor-sync
  remote_url: "git@github.com:username/agent-monitor-data.git"
  auto_sync_on_start: true

# 价格配置（支持 apiclaude 倍率）
pricing:
  cny_to_usd_rate: 12
  provider_multipliers:
    openai_2x: 2.2
    anthropic_3x: 2.8
```

完整配置说明：查看 `config.yaml` 中的注释

## 📊 Dashboard 功能

打开 http://127.0.0.1:8899 后可以看到：

### 当前功能
- 📈 费用和 token 趋势图
- 🔍 按模型/Provider 分组统计
- ⏱️ 多时间窗口切换
- 📉 缓存命中率分析
- 🖥️ **多机器聚合视图**（新）

### 即将推出（v2.0）
- 🎨 DeepSeek 风格 UI 重构
- 📊 ECharts 交互式图表
- 🔄 实时数据刷新
- 📤 数据导出（CSV/Excel）
- 📱 移动端适配

## 🔐 隐私说明

- ✅ 只读取数据库，不修改任何文件
- ✅ 数据完全本地处理
- ✅ Git 同步建议使用私有仓库
- ❌ 不上传对话内容
- ❌ 不上传 API Key

## 📚 文档

- [多机同步指南](MULTI_MACHINE_GUIDE.md) - 详细的多机设置教程
- [使用说明.txt](使用说明.txt) - 原版详细说明
- [CHANGELOG.md](CHANGELOG.md) - 版本更新记录

## 🆘 故障排除

### "Permission denied" (Git push 失败)

配置 SSH Key：
```bash
ssh-keygen -t ed25519 -C "your_email@example.com"
# 将 ~/.ssh/id_ed25519.pub 添加到 GitHub
```

### 找不到数据库

检查数据库路径：
```bash
# macOS/Linux
ls ~/.hermes/state.db
ls ~/.local/share/opencode/opencode.db

# Windows
dir %LOCALAPPDATA%\hermes\state.db
dir %USERPROFILE%\.local\share\opencode\opencode.db
```

如果路径不同，在 `config.yaml` 中显式配置。

### 数据不同步

```bash
# 手动测试同步
python3 cli.py sync -v

# 查看日志
tail -f logs/monitor.log
```

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

计划中的功能：
- [ ] DeepSeek 风格 UI 重构
- [ ] 图表交互优化
- [ ] 数据导出功能
- [ ] 告警通知
- [ ] Docker 部署

## 📄 许可

MIT License

## 🙏 致谢

- Hermes Agent by Nous Research
- OpenCode CLI
- DeepSeek (UI 设计灵感)

---

💡 **提示：** 首次使用建议先看 [多机同步指南](MULTI_MACHINE_GUIDE.md)，了解如何配置跨机器数据聚合。
