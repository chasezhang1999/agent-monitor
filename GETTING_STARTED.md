# 🎉 Agent Monitor v2.0 - 完成！

## ✅ 已完成的功能

### 1️⃣ 多机数据同步
- ✅ Git 私有仓库自动同步
- ✅ 机器自动识别（hostname）
- ✅ 启动时自动 pull → export → push
- ✅ 数据聚合展示
- ✅ 交互式设置向导

### 2️⃣ DeepSeek 风格 UI
- ✅ 全新配色方案（蓝 + 粉）
- ✅ 2列卡片布局
- ✅ 筛选器（时间 + 机器）
- ✅ 3列统计卡片
- ✅ ECharts 交互式图表
- ✅ 响应式布局

### 3️⃣ 命令行工具
- ✅ `dashboard` - 启动 Web 界面
- ✅ `sync` - 手动同步数据
- ✅ `machines` - 查看所有机器
- ✅ `report` - 生成聚合报告

## 🚀 立即开始

### 方式一：单机使用（本地统计）

```bash
cd ~/Code/agent-monitor

# 启动
./start.sh

# 访问
open http://127.0.0.1:8899
```

### 方式二：多机同步（推荐）

#### 第一步：创建 GitHub 私有仓库

1. 访问 https://github.com/new
2. 仓库名：`agent-monitor-data`
3. 类型：**Private**（重要！）
4. 不要初始化 README
5. 创建仓库

#### 第二步：首台机器设置

```bash
cd ~/Code/agent-monitor

# 运行设置向导
python3 setup_sync.py

# 按提示输入：
# - 同步目录: ~/.agent-monitor-sync（默认）
# - 远程仓库: git@github.com:你的用户名/agent-monitor-data.git
```

#### 第三步：配置 SSH Key（如果还没有）

```bash
# 生成 SSH Key
ssh-keygen -t ed25519 -C "your_email@example.com"

# 复制公钥
cat ~/.ssh/id_ed25519.pub

# 添加到 GitHub
# Settings → SSH and GPG keys → New SSH key → 粘贴
```

#### 第四步：启动

```bash
./start.sh

# 会自动：
# 1. Pull 最新数据
# 2. 导出本机快照
# 3. Push 到远程
# 4. 启动 Dashboard
```

#### 第五步：其他机器（Windows/Mac/Linux）

```bash
# 1. 克隆项目
git clone https://github.com/chasezhang1999/agent-monitor.git
cd agent-monitor

# 2. 运行设置向导（用相同的仓库 URL）
python3 setup_sync.py

# 3. 启动
./start.sh  # macOS/Linux
# 或
start.bat   # Windows
```

## 📊 Dashboard 功能

访问 http://127.0.0.1:8899 后：

### 顶部摘要
- **累计消费金额** - 所有时间的总消费
- **本周期消费** - 当前时间窗口的消费

### 筛选器
- **时间维度** - 今天/7天/30天/90天
- **机器** - 全部机器/单个机器（多机模式）
- **同步数据** - 手动触发同步
- **清除缓存** - 刷新数据
- **价格配置** - 管理模型价格

### 统计卡片
- 消费金额
- API 请求次数
- Tokens 总量

### 图表
- **消费金额图** - 按模型/Provider 展示
- **Tokens 图** - Input/Output/Reasoning 堆叠

### 详细数据
- 点击模型展开详情
- 显示所有 Token 类型和费用

## 🔧 命令行使用

```bash
# 查看所有机器
python3 cli.py machines

# 输出示例：
# 🖥️  Found 3 machines:
#   chases-macbook-pro-2021
#     Hostname: Chases-MacBook-Pro-2021.local
#     30d Cost: ¥125.34
#     30d Tokens: 15,234,567

# 手动同步
python3 cli.py sync

# 生成报告
python3 cli.py report --days 30
```

## 📁 文件说明

```
agent-monitor/
├── README.md                    # 项目说明
├── MULTI_MACHINE_GUIDE.md       # 多机同步详细指南
├── RELEASE_v2.0.md              # v2.0 发布说明
├── config.yaml                  # 配置文件
├── start.sh / start.bat         # 启动脚本
├── setup_sync.py                # 多机同步设置向导
├── cli.py                       # 命令行工具
├── monitor.py                   # 数据采集核心
├── multi_machine.py             # 多机同步模块
├── dashboard.py                 # Web 服务器
├── paths.py                     # 跨平台路径解析
└── templates/
    └── index.html               # DeepSeek 风格 UI
```

## 🔐 安全说明

- ✅ 数据只包含统计（Token 数、费用）
- ✅ 不包含对话内容
- ✅ 不包含 API Key
- ⚠️ 务必使用**私有仓库**
- 💡 建议用 SSH Key 而非 HTTPS Token

## 🐛 故障排除

### 问题 1：Push 失败 "Permission denied"

```bash
# 检查 SSH
ssh -T git@github.com

# 如果失败，重新配置 SSH Key
# 参考：https://docs.github.com/en/authentication
```

### 问题 2：数据不同步

```bash
# 手动测试
python3 cli.py sync -v

# 查看日志
tail -f logs/monitor.log

# 检查 Git 状态
cd ~/.agent-monitor-sync
git status
git log --oneline -5
```

### 问题 3：找不到数据库

```bash
# 检查路径
ls ~/.hermes/state.db
ls ~/.local/share/opencode/opencode.db

# 如果路径不同，在 config.yaml 中配置：
# sources:
#   hermes:
#     db_path: /your/custom/path/state.db
```

## 📚 更多文档

- **快速开始**: `README.md`
- **多机同步**: `MULTI_MACHINE_GUIDE.md`
- **发布说明**: `RELEASE_v2.0.md`
- **实现总结**: `IMPLEMENTATION_STATUS.md`

## 🎯 下一步

1. ✅ **现在就试用** - 运行 `./start.sh`
2. 📖 **多机同步** - 运行 `python3 setup_sync.py`
3. 🎨 **查看新 UI** - 访问 http://127.0.0.1:8899
4. 💡 **反馈建议** - GitHub Issues

---

**版本**: v2.0  
**状态**: ✅ 已完成并测试  
**代码**: https://github.com/chasezhang1999/agent-monitor  
**最后更新**: 2026-08-20

🎉 **享受你的多机 AI Agent 监控系统！**
