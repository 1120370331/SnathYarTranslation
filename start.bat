@echo off
chcp 65001 > nul
setlocal EnableDelayedExpansion

REM 沙斯亚尔语翻译器启动脚本 / Shathyar Translator Startup Script
REM 启动后端和前端服务 / Start backend and frontend services

echo 🔮 启动沙斯亚尔语翻译器 / Starting Shathyar Translator
echo ==================================================

REM Check if Node.js is installed
echo [INFO] 🔍 检查系统要求 / Checking system requirements...
node --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Node.js is not installed. Please install Node.js 18+ to continue.
    pause
    exit /b 1
)
echo [SUCCESS] Node.js detected ✓

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed. Please install Python 3.11+ to continue.
    pause
    exit /b 1
)
echo [SUCCESS] Python detected ✓

echo.
echo [INFO] 📦 安装依赖 / Installing dependencies...

REM Setup backend
echo [INFO] 🐍 设置后端环境 / Setting up backend environment...
cd backend

REM Create virtual environment if it doesn't exist
if not exist "venv" (
    echo [INFO] Creating Python virtual environment...
    python -m venv venv
)

REM Activate virtual environment and install dependencies
echo [INFO] Installing Python dependencies...
call venv\Scripts\activate.bat
pip install -e . >nul 2>&1
echo [SUCCESS] Backend setup complete ✓

cd ..

REM Setup frontend
echo [INFO] ⚛️ 设置前端环境 / Setting up frontend environment...
cd frontend

if not exist "node_modules" (
    echo [INFO] Installing Node.js dependencies...
    npm install >nul 2>&1
) else (
    echo [INFO] Dependencies already installed, checking for updates...
    npm ci >nul 2>&1
)
echo [SUCCESS] Frontend setup complete ✓

cd ..

echo.
echo [INFO] 🚀 启动服务 / Starting services...

REM Start backend server
echo [INFO] 🚀 启动后端服务器 / Starting backend server...
cd backend
start "Shathyar Backend" cmd /c "venv\Scripts\activate.bat && python -m uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload"
echo [SUCCESS] Backend server starting...
echo [INFO] 📍 Backend URL: http://localhost:8000
echo [INFO] 📚 API Docs: http://localhost:8000/docs
cd ..

REM Wait a moment for backend to start
timeout /t 3 /nobreak >nul

REM Start frontend server
echo [INFO] 🎨 启动前端服务器 / Starting frontend server...
cd frontend
start "Shathyar Frontend" cmd /c "npm run dev"
echo [SUCCESS] Frontend server starting...
echo [INFO] 🌐 Frontend URL: http://localhost:5173
cd ..

REM Wait for servers to be ready
echo [INFO] ⏳ 等待服务器启动 / Waiting for servers to start...
timeout /t 5 /nobreak >nul

echo.
echo 🎉 沙斯亚尔语翻译器启动成功！/ Shathyar Translator started successfully!
echo ==================================================
echo 🔮 翻译门户 / Translation Portal: http://localhost:5173
echo 📚 API 文档 / API Documentation: http://localhost:8000/docs
echo 💚 后端健康检查 / Backend Health: http://localhost:8000/health
echo.
echo 提示 / Tips:
echo • 两个终端窗口将会打开 / Two terminal windows will open
echo • 后端运行在端口 8000 / Backend runs on port 8000
echo • 前端运行在端口 5173 / Frontend runs on port 5173
echo • 关闭终端窗口以停止服务 / Close terminal windows to stop services
echo.
echo 🌟 准备开始您的沙斯亚尔语翻译之旅！/ Ready to start your Shathyar translation journey!

REM Open the application in browser
timeout /t 3 /nobreak >nul
start http://localhost:5173

echo.
echo 按任意键退出此脚本... / Press any key to exit this script...
pause >nul