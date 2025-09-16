@echo off
setlocal EnableExtensions
chcp 65001 >nul

echo 🔍 诊断后端启动问题...
echo =============================================

REM 检查当前目录
echo 当前目录: %CD%
echo.

REM 切换到backend目录
pushd backend
echo 切换到backend目录: %CD%
echo.

REM 检查虚拟环境
if exist "venv" (
    echo ✅ 虚拟环境存在
) else (
    echo ❌ 虚拟环境不存在
    echo 正在创建虚拟环境...
    python -m venv venv
)

REM 检查activate.bat
if exist "venv\Scripts\activate.bat" (
    echo ✅ activate.bat 存在
) else (
    echo ❌ activate.bat 不存在
)

echo.
echo 🔧 激活虚拟环境并安装/检查依赖...
call venv\Scripts\activate.bat

echo.
echo Python 版本:
python --version

echo.
echo 🔧 安装/更新依赖包...
echo 升级 pip...
pip install --upgrade pip

echo.
echo 安装 requirements.txt 中的依赖...
pip install -r requirements.txt

echo.
echo 安装项目本身...
pip install -e .

echo.
echo 🔍 检查关键依赖安装状态:
python -c "import fastapi; print('✅ FastAPI:', fastapi.__version__)" 2>nul || echo "❌ FastAPI 未安装"
python -c "import uvicorn; print('✅ Uvicorn:', uvicorn.__version__)" 2>nul || echo "❌ Uvicorn 未安装"
python -c "import sqlalchemy; print('✅ SQLAlchemy:', sqlalchemy.__version__)" 2>nul || echo "❌ SQLAlchemy 未安装"

echo.
echo 🚀 尝试启动服务器...
echo 如果这里失败，你会看到具体的错误信息：
echo.

python -m uvicorn src.main:app --host 127.0.0.1 --port 8000 --reload

echo.
echo 按任意键继续...
pause >nul

popd
endlocal