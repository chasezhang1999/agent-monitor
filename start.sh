#!/bin/bash
# Agent Monitor 启动脚本 (macOS/Linux)

# 脚本目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "🚀 Agent Monitor - Starting..."
echo ""

# 检查 Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found. Please install Python 3."
    exit 1
fi

# 检查虚拟环境
if [ ! -d ".venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv .venv
fi

# 激活虚拟环境
source .venv/bin/activate

# 安装依赖
if [ ! -f ".venv/installed" ]; then
    echo "📦 Installing dependencies..."
    pip install -q --upgrade pip
    pip install -q -r requirements.txt
    touch .venv/installed
fi

# 检查 Git（多机同步需要）
if ! command -v git &> /dev/null; then
    echo "⚠️  Git not found. Multi-machine sync will be disabled."
    echo "   Install Git to enable data sync across machines."
    echo ""
fi

# 启动 dashboard（会自动同步数据）
echo "🌐 Starting dashboard..."
echo "   Open http://127.0.0.1:8899 in your browser"
echo ""
echo "💡 Tip: Press Ctrl+C to stop"
echo ""

python3 cli.py dashboard

# 退出时提示
echo ""
echo "👋 Dashboard stopped."
