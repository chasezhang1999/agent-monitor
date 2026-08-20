#!/bin/bash
source .venv/bin/activate
echo "🚀 启动 Dashboard 测试..."
echo "   访问 http://127.0.0.1:8899"
echo ""
python3 cli.py dashboard --host 127.0.0.1 --port 8899
