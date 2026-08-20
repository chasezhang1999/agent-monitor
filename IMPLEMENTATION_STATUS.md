# 多机数据同步功能 - 实现总结

## ✅ 已完成功能

### 1. 核心同步模块 (`multi_machine.py`)

- **MachineIdentifier** - 自动识别机器（基于 hostname）
- **DataSnapshot** - 导出本机监控数据快照
- **GitSync** - Git 仓库管理（init/pull/push）
- **MultiMachineAggregator** - 聚合所有机器的数据

### 2. CLI 命令 (`cli.py`)

```bash
# Dashboard（启动时自动同步）
python3 cli.py dashboard

# 手动同步
python3 cli.py sync

# 查看所有机器
python3 cli.py machines

# 生成聚合报告
python3 cli.py report --days 30
```

### 3. 设置向导 (`setup_sync.py`)

交互式配置：
- 选择同步目录
- 输入 Git 远程仓库 URL
- 自动初始化并首次推送
- 更新 config.yaml

### 4. 配置文件 (`config.yaml`)

新增 `multi_machine` 配置段：
```yaml
multi_machine:
  enabled: true
  sync_dir: ~/.agent-monitor-sync
  remote_url: ""  # Git 仓库 URL
  auto_sync_on_start: true
  show_machine_filter: true
```

### 5. 启动脚本更新

- `start.sh` - macOS/Linux 一键启动
- 自动检查 Git 并提示
- 启动时自动同步数据

### 6. 文档

- `MULTI_MACHINE_GUIDE.md` - 详细使用指南
- `README.md` - 快速开始更新

## 🔄 工作流程

```
启动 Dashboard
    ↓
检查 multi_machine.enabled
    ↓
自动同步流程：
    1. git pull（拉取其他机器的数据）
    2. 导出本机快照 → machines/{hostname}.json
    3. git commit + push
    ↓
Dashboard 读取所有 machines/*.json
    ↓
聚合展示（支持按机器筛选）
```

## 📁 数据结构

### Git 仓库结构
```
~/.agent-monitor-sync/
├── .git/
├── machines/
│   ├── chases-macbook-pro-2021.json
│   ├── asus-desktop.json
│   └── ubuntu-server.json
├── README.md
└── .gitignore
```

### 快照格式
```json
{
  "machine_id": "chases-macbook-pro-2021",
  "hostname": "Chases-MacBook-Pro-2021.local",
  "timestamp": "2026-08-20T20:30:15",
  "reports": {
    "1d": {...},
    "7d": {...},
    "30d": {...},
    "90d": {...}
  },
  "metadata": {
    "monitor_version": "1.0",
    "hermes_enabled": true,
    "opencode_enabled": true
  }
}
```

## 🚀 使用步骤

### 第一台机器

```bash
cd ~/Code/agent-monitor

# 1. 运行设置向导
python3 setup_sync.py
# 输入: git@github.com:username/agent-monitor-data.git

# 2. 启动（会自动同步）
./start.sh
```

### 其他机器

```bash
# 1. 克隆项目
git clone <agent-monitor-repo>
cd agent-monitor

# 2. 运行设置向导（用相同的 Git 仓库 URL）
python3 setup_sync.py

# 3. 启动
./start.sh
```

## 🎯 下一步：UI 重构（DeepSeek 风格）

现在数据聚合已完成，接下来：

1. **保留现有 Flask Dashboard 作为基础**
2. **用 DeepSeek 的设计语言重构前端**
   - 配色方案
   - 布局结构（2列卡片 → 筛选器 → 统计卡片 → 图表）
   - ECharts 替代 matplotlib
   - 添加机器筛选下拉框

3. **新增功能**
   - 机器筛选器
   - 数据导出（CSV/Excel）
   - 图表交互（hover 显示详情）
   - 响应式布局

## 📝 注意事项

- Git 仓库建议设为**私有**（包含用量数据）
- 需要配置 SSH Key 或 Personal Access Token
- 如果不配置 `remote_url`，只做本地聚合（单机多数据源）
- 每台机器用 hostname 区分，确保 hostname 有意义

## 🐛 已知限制

1. **首次 push 可能失败** - 需要先创建远程仓库
2. **并发冲突** - 多台机器同时 push 会冲突（但不影响数据，下次 pull 会自动合并）
3. **大数据量** - 90 天以上数据可能导致快照文件较大

## 🔧 可优化项（未来）

1. **增量同步** - 只同步变化的数据
2. **压缩** - 快照文件 gzip 压缩
3. **冲突处理** - 自动 merge 策略
4. **定时同步** - cron 自动后台同步
5. **通知** - 同步失败时发送通知

---

**状态：** ✅ 多机同步功能已完成，可以测试使用
**下一步：** UI 重构（DeepSeek 风格）
