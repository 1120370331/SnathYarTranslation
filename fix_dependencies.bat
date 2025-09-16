@echo off
setlocal EnableExtensions
chcp 65001 >nul

echo 🚀 快速修复后端依赖
echo ==================

pushd backend

echo 🔧 激活虚拟环境...
call venv\Scripts\activate.bat

echo 🔄 升级 pip...
pip install --upgrade pip

echo 📦 安装 requirements.txt 中的所有依赖...
pip install -r requirements.txt

echo 🔧 安装项目包...
pip install -e .

echo.
echo ✅ 依赖安装完成！现在检查关键模块...
echo.

python -c "import uvicorn; print('✅ Uvicorn 已安装:', uvicorn.__version__)" || echo "❌ Uvicorn 安装失败"
python -c "import fastapi; print('✅ FastAPI 已安装:', fastapi.__version__)" || echo "❌ FastAPI 安装失败"
python -c "import sqlalchemy; print('✅ SQLAlchemy 已安装:', sqlalchemy.__version__)" || echo "❌ SQLAlchemy 安装失败"

echo.
echo 🎉 修复完成！现在可以运行 start.bat 或 debug_backend.bat
echo.

popd

pause
endlocal