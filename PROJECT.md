# Agent Monitor System

一套完整的 AI Agent 使用监控系统，用于监控 Hermes 和 OpenCode 的 token 使用和费用统计。

## ✨ 特性

✅ **主动探查** - 直接读取 SQLite 数据库，不修改任何 agent 文件  
✅ **双 Agent 支持** - 同时监控 Hermes 和 OpenCode  
✅ **完整统计** - Token 使用、模型、Provider、缓存命中、价格  
✅ **价格配置** - 支持配置倍率和各模型实际价格  
✅ **Web Dashboard** - 实时可视化监控面板  
✅ **命令行工具** - 快速查看统计数据  
✅ **多维度分析** - 按 Agent/Model/Provider 聚合统计  

## 🚀 快速开始

### 1. 安装依赖

```bash
cd C:\Users\xczha\agent-monitor
pip install flask pyyaml
```

### 2. 测试运行

```bash
python test.py
```

### 3. 查看统计

```bash
# 命令行查看
python cli.py -d 7

# 启动 Web Dashboard
python dashboard.py
# 访问 http://127.0.0.1:8899
```

## 📖 文档

- **[快速使用指南 (QUICKSTART.md)](QUICKSTART.md)** - 3 步上手，5 分钟掌握
- **[完整文档 (README.md)](README.md)** - 详细的架构、配置和扩展说明

## 🎯 系统架构

```
数据采集 → 价格计算 → 多维聚合 → Web 展示
   ↓           ↓           ↓          ↓
SQLite     config.yaml   统计引擎   Dashboard
```

**数据源**：
- Hermes: `state.db` → `session_model_usage` 表
- OpenCode: `opencode.db` → `session` 表

**核心组件**：
- `monitor.py` - 数据采集和聚合引擎
- `dashboard.py` - Flask Web 服务器
- `cli.py` - 命令行工具
- `config.yaml` - 价格配置

## 📊 功能展示

### Web Dashboard

![Dashboard](https://via.placeholder.com/800x400/1e293b/60a5fa?text=Agent+Monitor+Dashboard)

- 📈 实时统计卡片（会话数、Token、费用）
- 🔄 自动刷新（每分钟）
- ⏱️ 时间窗口切换（全部/1天/7天/30天/90天）
- 📊 多维度表格（Agent/Model/Provider）

### 命令行工具

```bash
$ python cli.py -d 7

======================================================================
📊 Agent Monitor Report - 7 days
======================================================================

【总览】
  会话数:              51
  总 Token:        20.70M
  缓存命中率:       84.1%
  实际费用:      ¥18.16 CNY

【按 Agent】
  Agent        会话       Token        实际费用
  ----------------------------------------------------
  hermes       30       18.68M       ¥14.09
  opencode     21        2.02M       ¥4.07

【按模型 Top 10】
  模型                  会话     Token        命中率      实际费用
  ----------------------------------------------------------------------
  gpt-5.6-sol           6      14.23M         73.1% ¥13.20
  gpt-5.6-luna          4       2.42M         86.9% ¥0.51
  deepseek-v4-pro      16       1.60M         97.7% ¥1.18
  ...
```

## 🎨 特色功能

### 1. 智能价格计算

三层价格机制：

1. **标准价格**：官方 USD 定价
2. **Provider 倍率**：自动推断倍率
3. **价格覆盖**：优先级最高的自定义价格

公式：`actual CNY/M = standard USD/M * multiplier / 12`

### 2. 缓存命中率分析

准确计算缓存命中率：

```
cache_hit_rate = cache_read / (input + cache_read + cache_write)
```

帮助你优化 prompt caching 策略。

### 3. 多维度聚合

- 按 Agent 对比（Hermes vs OpenCode）
- 按 Model 排行（哪个模型用得最多）
- 按 Provider 分析（不同价格档位的使用分布）
- 按时间窗口（趋势分析）

## ⚙️ 配置示例

### 添加新模型

```yaml
pricing:
  standard_prices:
    your-new-model:
      input: 5
      output: 25
      cache_write: 6.25
      cache_read: 0.5
```

### 配置特殊价格

```yaml
pricing:
  price_overrides:
    gpt-5.6-sol@openai_2x:
      input: 0.9166667     # CNY per million tokens
      output: 5.5
```

## 📦 项目结构

```
agent-monitor/
├── config.yaml              # 配置文件
├── monitor.py               # 核心引擎（400+ 行）
├── dashboard.py             # Web 服务器
├── cli.py                   # 命令行工具
├── test.py                  # 测试脚本
├── start.bat                # Windows 启动脚本
├── templates/
│   └── index.html           # Web 前端（深色主题）
├── logs/
│   └── monitor.log          # 运行日志
├── README.md                # 完整文档
├── QUICKSTART.md            # 快速指南
└── requirements.txt         # 依赖
```

## 🔧 技术栈

- **后端**：Python 3.8+, Flask, SQLite3
- **前端**：原生 HTML/CSS/JS（无框架依赖）
- **配置**：YAML
- **数据库**：SQLite（只读）

## 📈 当前状态

✅ **已完成并验证**

- [x] 数据采集（Hermes + OpenCode）
- [x] 价格计算（三层机制）
- [x] 多维聚合统计
- [x] Web Dashboard
- [x] 命令行工具
- [x] 测试验证

🎯 **运行正常**

- 73 条 Hermes 记录
- 21 条 OpenCode 记录
- 支持 8 个主流模型
- 缓存命中率计算准确

## 🚀 后续扩展

- [ ] 定时采集和告警
- [ ] 历史趋势图表
- [ ] 导出 PDF/Excel 报告
- [ ] 支持更多 Agent（Claude Code, Codex 等）
- [ ] 成本预测和优化建议

## 📝 许可

MIT License

## 🙏 致谢

基于 Hermes Agent 和 OpenCode 的数据库结构设计。

---

**开始使用：**

```bash
# 测试
python test.py

# 命令行
python cli.py -d 7

# Web Dashboard
python dashboard.py
```

**或双击运行：** `start.bat`
