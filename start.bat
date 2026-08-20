@echo off
REM Agent Monitor Dashboard 启动脚本

echo ========================================
echo   Agent Monitor Dashboard
echo ========================================
echo.

REM 检查 Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到 Python，请先安装 Python 3.8+
    pause
    exit /b 1
)

REM 检查依赖
python -c "import flask" >nul 2>&1
if errorlevel 1 (
    echo [提示] 首次运行需要安装依赖...
    echo.
    pip install flask pyyaml
    echo.
)

REM 测试数据采集
echo [1/3] 测试数据采集...
python monitor.py 7 >nul 2>&1
if errorlevel 1 (
    echo [错误] 数据采集失败，请检查配置文件
    pause
    exit /b 1
)
echo [✓] 数据采集正常

REM 启动 Dashboard
echo.
echo [2/3] 启动 Dashboard...
echo [3/3] 浏览器访问: http://127.0.0.1:8899
echo.
echo ----------------------------------------
echo 按 Ctrl+C 停止服务器
echo ----------------------------------------
echo.

python dashboard.py
