@echo off
setlocal EnableExtensions
chcp 65001 >nul

REM Kill existing listeners (8000/5173)
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8000 ^| findstr LISTENING') do taskkill /F /PID %%a >nul 2>&1
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :5173 ^| findstr LISTENING') do taskkill /F /PID %%a >nul 2>&1

REM Backend
pushd backend
if not exist "venv" python -m venv venv
call venv\Scripts\activate.bat
pip install -e . >nul 2>&1
start "Backend" cmd /c "venv\Scripts\activate.bat && python -m uvicorn src.main:app --host 127.0.0.1 --port 8000"
popd

REM Frontend
pushd frontend
if not exist "node_modules" npm install >nul 2>&1
set VITE_DISABLE_FALLBACK=true
start "Frontend" cmd /c "npm run dev"
popd

start "" "http://localhost:5173"
endlocal
exit /b 0
