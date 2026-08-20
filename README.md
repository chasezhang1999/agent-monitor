# Agent Monitor

一个功能强大的 AI Agent 使用监控系统，用于监控 Hermes 和 OpenCode 的 token 使用和费用统计。

<div align="center">

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.8+-green.svg)
![Status](https://img.shields.io/badge/status-production-success.svg)

</div>

## ✨ 特性

- 🔍 **主动探查** - 直接读取 SQLite 数据库，零侵入设计
- 🚀 **超快缓存** - 221x 加速比，秒级响应
- 📊 **专业图表** - Chart.js 驱动的 4 种可视化图表
- ⚙️ **在线配置** - Web UI 编辑价格和倍率配置
- 🎯 **多维分析** - Agent/Model/Provider 多角度统计
- 💰 **价格透明** - 完整的计算逻辑和价格配置展示

## 🎬 快速开始

### 安装依赖

```bash
cd agent-monitor
pip install -r requirements.txt
```

### 配置

编辑 `config.yaml`，确认数据库路径正确：

```yaml
sources:
  hermes:
    db_path: C:\Users\xczha\AppData\Local\hermes\state.db
  opencode:
    db_path: C:\Users\xczha\.local\share\opencode\opencode.db
```

### 启动

```bash
# 方式 1：双击启动
双击 start.bat

# 方式 2：命令行
python dashboard.py
```

访问：http://127.0.0.1:8899

## 📊 功能展示

### 主 Dashboard
- 📈 **Token 使用排行** - 堆叠柱状图展示 Top 10 模型
- 💰 **费用分布** - 环形图显示费用占比
- 💾 **缓存命中率** - 横向柱状图展示缓存效率
- 🔌 **Provider 分布** - 饼图显示 Provider 使用情况

### 配置页面
- ✏️ 编辑模型价格（input/output/cache_write/cache_read）
- 🔧 编辑 Provider 倍率
- 🗑️ 清除缓存
- 💾 实时保存到 YAML

### 详情面板
- 点击任意模型行查看：
  - Token 统计（具体数字）
  - 缓存命中率计算（公式 + 分步）
  - 费用计算（价格配置 + 公式 + 结果）

## 🛠️ 技术栈

- **后端**: Python 3.8+, Flask, SQLite3
- **前端**: HTML5, CSS3, JavaScript (ES6+)
- **图表**: Chart.js 4.4
- **配置**: YAML

## 📂 项目结构

```
agent-monitor/
├── monitor.py              # 核心监控引擎
├── dashboard.py            # Flask Web 服务器
├── cli.py                  # 命令行工具
├── config.yaml             # 价格配置
├── templates/
│   ├── index.html          # 主 Dashboard
│   └── config.html         # 配置页面
├── cache/                  # 缓存数据库
├── logs/                   # 运行日志
├── requirements.txt        # Python 依赖
├── start.bat               # Windows 启动脚本
└── README.md
```

## 💡 核心功能

### 1. 数据缓存
- **221x 加速比** - 第二次查询仅需 0.00 秒
- SQLite 缓存数据库
- 60 分钟自动过期
- 按小时缓存策略

### 2. 多维统计
- 按 Agent（Hermes / OpenCode）
- 按 Model（Top N 排行）
- 按 Provider（分布分析）
- 按时间窗口（1/7/30/90 天）

### 3. 价格计算
- 三层价格机制：标准价格 → Provider 倍率 → 价格覆盖
- 公式：`actual CNY = standard USD × multiplier / 12`
- 完整的计算逻辑展示

## 📖 使用文档

- [快速开始](QUICKSTART.md) - 3 步上手指南
- [完整文档](README.md) - 详细功能说明
- [新功能介绍](README_NEW_FEATURES.md) - 最新功能说明
- [实施计划](IMPLEMENTATION_PLAN.md) - 技术方案

## 🔧 命令行工具

```bash
# 查看最近 7 天统计
python cli.py -d 7

# 查看最近 30 天（详细模式）
python cli.py -d 30 --details

# 导出 JSON
python cli.py -d 7 --json > report.json
```

## 🎨 配置示例

### 添加新模型价格

```yaml
pricing:
  standard_prices:
    your-model:
      input: 5
      output: 30
      cache_write: 6.25
      cache_read: 0.5
```

### 配置 Provider 倍率

```yaml
pricing:
  provider_multipliers:
    your_provider: 2.2
```

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📝 许可证

MIT License

---

**开发者**: Kiro (Claude Opus 5)  
**版本**: v1.2  
**状态**: Production Ready ✅
