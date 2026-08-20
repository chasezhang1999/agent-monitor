# 前端数据不显示 - 故障排查指南

## 问题描述
Dashboard 打开后看不到数据，页面显示为空或默认值。

## 已确认的事实
✅ 后端 API 正常工作
✅ 数据采集正常 (32 条记录)
✅ API 返回正确的 JSON (¥4.32, 2.9M tokens)
✅ 数据格式已修复匹配前端

## 可能的原因

### 1. JavaScript 加载/执行问题
**症状**: 页面显示但没有数据
**检查方法**:
```
1. 打开浏览器开发者工具 (F12)
2. 切换到 Console 标签
3. 刷新页面
4. 查看是否有红色错误信息
```

**常见错误**:
- `Uncaught ReferenceError: echarts is not defined`
  → ECharts CDN 加载失败
- `Failed to fetch` 
  → API 请求被阻止
- `Unexpected token` 
  → JavaScript 语法错误

### 2. CDN 资源加载失败
**症状**: Console 显示 CDN 加载 404/超时
**解决**:
```html
<!-- 检查 index.html 中的 CDN 链接 -->
<script src="https://cdn.jsdelivr.net/npm/echarts@5.4.3/dist/echarts.min.js"></script>
```

如果 CDN 被墙或超时，换成国内镜像:
```html
<script src="https://lib.baomitu.com/echarts/5.4.3/echarts.min.js"></script>
```

### 3. 浏览器缓存问题
**解决**: 硬刷新页面
- Mac: Cmd + Shift + R
- Windows/Linux: Ctrl + Shift + R

### 4. 跨域问题 (CORS)
**症状**: Console 显示 CORS 错误
**解决**: Dashboard 和 API 应该在同一域名，不应该有跨域问题

## 调试步骤

### 第1步: 使用调试页面
```bash
cd ~/Code/agent-monitor
./start.sh

# 访问调试页面
open http://127.0.0.1:8899/debug
```

调试页面会自动:
- 测试 API 连接
- 验证数据字段
- 显示原始 JSON
- 记录详细日志

### 第2步: 检查主页面控制台
```bash
# 访问主页面
open http://127.0.0.1:8899/

# 按 F12 打开开发者工具
# 查看 Console 标签的错误信息
```

### 第3步: 检查 Network
```
1. 开发者工具 → Network 标签
2. 刷新页面
3. 找到 /api/report 请求
4. 查看:
   - Status (应该是 200)
   - Response (应该有数据)
   - Preview (应该能看到 JSON)
```

### 第4步: 手动测试 JavaScript
在 Console 中手动执行:
```javascript
// 测试 ECharts 是否加载
console.log(typeof echarts);  // 应该输出 "object"

// 测试 API
fetch('/api/report?days=30')
  .then(r => r.json())
  .then(d => console.log(d));

// 应该输出完整的数据对象
```

## 快速修复方案

### 方案 A: 重新安装 (清除缓存)
```bash
cd ~/Code/agent-monitor
rm -rf .venv
rm -rf cache/
./start.sh
```

### 方案 B: 使用国内 CDN
编辑 `templates/index.html`:
```html
<!-- 替换 -->
<script src="https://cdn.jsdelivr.net/npm/echarts@5.4.3/dist/echarts.min.js"></script>

<!-- 为 -->
<script src="https://lib.baomitu.com/echarts/5.4.3/echarts.min.js"></script>
```

### 方案 C: 本地化 ECharts (终极方案)
```bash
cd ~/Code/agent-monitor
mkdir -p static/js
curl -o static/js/echarts.min.js https://cdn.jsdelivr.net/npm/echarts@5.4.3/dist/echarts.min.js

# 修改 templates/index.html
<script src="/static/js/echarts.min.js"></script>
```

## 收集诊断信息

如果上述方法都不work，请提供以下信息:

1. **浏览器控制台截图**
   - Console 标签的错误
   - Network 标签的 /api/report 请求

2. **调试页面结果**
   - 访问 http://127.0.0.1:8899/debug
   - 截图或复制所有输出

3. **浏览器信息**
   - 浏览器类型和版本
   - 操作系统

4. **服务器日志**
   ```bash
   cd ~/Code/agent-monitor
   tail -50 logs/monitor.log
   ```

## 联系方式
把上述信息发给我，我会帮你排查！

