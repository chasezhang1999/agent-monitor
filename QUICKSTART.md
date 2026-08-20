# Agent Monitor - 快速使用指南

## 🎯 系统概览

Agent Monitor 是一个完整的 AI Agent 使用监控系统，主动探查 Hermes 和 OpenCode 的 token 使用和费用，无需修改任何原有 agent 文件。

**已验证运行正常！** ✅

最近 7 天统计（示例）：
- 51 个会话
- 20.7M tokens
- 缓存命中率 84.1%
- 实际费用 ¥18.16 CNY

---

## 📦 快速开始（3 步）

### 1. 安装依赖

```bash
cd agent-monitor

# macOS / Linux（推荐虚拟环境）
python3 -m venv .venv
.venv/bin/pip install flask pyyaml

# Windows
pip install flask pyyaml
```

### 2. 测试运行

```bash
# 运行测试
python test.py

# 命令行查看统计
python cli.py -d 7
```

### 3. 启动 Dashboard

**macOS / Linux**
```bash
./start.sh
# 或 .venv/bin/python dashboard.py
```

**Windows：双击 `start.bat`**
或命令行 `python dashboard.py`

然后访问: http://127.0.0.1:8899

---

## 💡 主要功能

### 📊 Web Dashboard

实时可视化监控面板，包含：

- **总览统计卡片**：会话数、总 Token、API 调用、缓存命中率、费用
- **按 Agent 对比**：Hermes vs OpenCode 使用对比
- **按模型排行**：Token 使用 Top 10
- **按 Provider 分析**：不同 Provider 的使用分布
- **时间窗口切换**：全部 / 1天 / 7天 / 30天 / 90天
- **自动刷新**：每分钟自动刷新数据

### 🖥️ 命令行工具

```bash
# 查看全部历史
python cli.py

# 最近 24 小时
python cli.py -d 1

# 最近 7 天
python cli.py -d 7

# 最近 30 天（详细模式）
python cli.py -d 30 --details

# 导出 JSON
python cli.py -d 7 --json > report.json
```

### 📈 监控指标

系统会统计以下维度：

1. **Token 使用**
   - Input tokens（输入）
   - Output tokens（输出）
   - Reasoning tokens（推理，仅 o3 等模型）
   - Cache read tokens（缓存读）
   - Cache write tokens（缓存写）

2. **费用计算**
   - 标准费用（USD）：基于官方定价
   - 实际费用（CNY）：基于你的倍率配置

3. **聚合统计**
   - 按 Agent（hermes / opencode）
   - 按 Model（gpt-5.6-sol, claude-opus-5 等）
   - 按 Provider（openai_2x, anthropic_3x 等）

4. **性能指标**
   - 缓存命中率
   - API 调用次数
   - 会话数量

---

## ⚙️ 配置说明

### 价格配置（`config.yaml`）

系统已预配置了以下模型价格：

**OpenAI 模型**
- gpt-5.6-sol / terra / luna

**Claude 模型**
- claude-fable-5 / opus-5 / sonnet-5

**DeepSeek 模型**
- deepseek-v4-flash / v4-pro

**Moonshot 模型**
- kimi-k3

### 添加新模型价格

编辑 `config.yaml`：

```yaml
pricing:
  standard_prices:
    your-new-model:
      input: 5        # USD per million tokens
      output: 25
      cache_write: 6.25
      cache_read: 0.5
```

### 配置 Provider 倍率

```yaml
pricing:
  provider_multipliers:
    your_provider: 3.5
```

### 覆盖特定价格

如果你有特殊的价格协议：

```yaml
pricing:
  price_overrides:
    model-name@provider-name:
      input: 0.92     # CNY per million tokens
      output: 5.5
      cache_write: 1.15
      cache_read: 0.092
```

---

## 📂 目录结构

```
agent-monitor/
├── config.yaml              # 配置文件（数据源、价格规则）
├── monitor.py               # 核心监控逻辑
├── dashboard.py             # Web Dashboard 服务器
├── cli.py                   # 命令行工具
├── test.py                  # 测试脚本
├── start.bat                # Windows 启动脚本
├── requirements.txt         # Python 依赖
├── templates/
│   └── index.html           # Web 前端界面
├── logs/
│   └── monitor.log          # 运行日志
└── README.md                # 完整文档
```

---

## 🔍 使用示例

### 示例 1：查看今天的使用情况

```bash
python cli.py -d 1
```

输出示例：
```
【总览】
  会话数:               5
  API 调用:           120
  总 Token:         1.2M
  缓存命中率:       85.3%
  实际费用:      ¥2.50 CNY
```

### 示例 2：对比不同 Agent 的使用

```bash
python cli.py -d 7
```

输出示例：
```
【按 Agent】
  Agent        会话       Token        实际费用
  ----------------------------------------------------
  hermes       30       18.68M       ¥14.0912
  opencode     21        2.02M       ¥4.0689
```

### 示例 3：导出数据进行分析

```bash
# 导出最近 30 天的数据
python cli.py -d 30 --json > monthly_report.json

# 查看模型排行
python cli.py -d 30 --json | jq '.statistics.by_model'

# 查看总费用
python cli.py -d 30 --json | jq '.statistics.total.actual_cost_cny'
```

### 示例 4：Web Dashboard 实时监控

1. 启动 Dashboard：`python dashboard.py`
2. 访问：http://127.0.0.1:8899
3. 切换时间窗口查看不同时期的统计
4. 自动每分钟刷新

---

## 🛠️ 故障排查

### 问题 1：数据库不存在

```
ERROR: Hermes DB not found: ...
```

**解决方法**：
1. 确认 Hermes / OpenCode 已经运行过（产生过数据）
2. `config.yaml` 里 `db_path` 默认是 `auto`，会按当前系统自动探测路径；
   如果你的安装位置不标准，改成显式绝对路径（各系统默认路径见 `paths.py`）

### 问题 2：价格为 0

```
WARNING: Unknown model pricing: new-model
```

**解决方法**：在 `config.yaml` 的 `standard_prices` 中添加该模型的价格配置

### 问题 3：Web 界面无法访问

**解决方法**：
1. 检查端口是否被占用
2. 修改 `config.yaml` 中的端口：`monitor.dashboard.port: 8899 → 8900`

### 问题 4：OpenCode 配置读取失败

```
WARNING: Failed to read OpenCode config: ...
```

**说明**：这个警告只影响 Provider 显示名称，不影响核心统计功能。
旧版在解析 `opencode.json` 里的 `//` 注释时可能误删 URL（如 `https://`），
现已改为字符串感知的 JSONC 解析，正常情况下不会再出现。

---

## 📊 当前运行状态

### 数据源

✅ **Hermes**
- 数据库：`C:\Users\xczha\AppData\Local\hermes\state.db`
- 采集到 73 条记录（最近 7 天）
- 统计正常

✅ **OpenCode**
- 数据库：`C:\Users\xczha\.local\share\opencode\opencode.db`
- 采集到 21 条记录（最近 7 天）
- 统计正常

### 支持的模型

已配置价格：
- ✅ gpt-5.6-sol / terra / luna
- ✅ claude-fable-5 / opus-5 / sonnet-5
- ✅ deepseek-v4-flash / v4-pro
- ✅ kimi-k3

---

## 🚀 下一步

### 1. 定时监控

使用 Windows 任务计划定时运行：

```bash
# 每小时生成报告
schtasks /create /tn "Agent Monitor" /tr "python C:\Users\xczha\agent-monitor\cli.py -d 1" /sc hourly
```

### 2. 告警通知

当费用超过阈值时发送通知（待实现）：

```yaml
alerts:
  enabled: true
  daily_cost_threshold_cny: 50
  daily_token_threshold: 10000000
```

### 3. 历史趋势

将统计结果写入时序数据库，绘制趋势图（待实现）

### 4. 导出报告

生成 PDF/Excel 月度报告（待实现）

---

## 📝 注意事项

1. **只读操作**：监控系统只读取数据库，不会修改任何 agent 文件
2. **数据安全**：所有数据都在本地处理，不会上传到外部服务器
3. **性能影响**：数据库读取使用 SQLite，性能开销极小
4. **配置同步**：修改 `config.yaml` 后立即生效，无需重启服务

---

## 📞 支持

如有问题：
1. 查看日志：`logs/monitor.log`
2. 运行测试：`python test.py`
3. 查看文档：`README.md`

---

## 🎉 完成！

系统已完全部署并验证运行正常。

**现在就可以使用：**

```bash
# 方式 1：命令行快速查看
python cli.py -d 7

# 方式 2：Web Dashboard
python dashboard.py
# 访问 http://127.0.0.1:8899
```

享受你的 AI Agent 监控系统吧！ 🚀
