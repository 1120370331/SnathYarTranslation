@echo off
setlocal EnableExtensions
chcp 65001 >nul

REM Kill existing listeners (8000/5173)
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8000 ^| findstr LISTENING') do taskkill /F /PID %%a >nul 2>&1
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :5173 ^| findstr LISTENING') do taskkill /F /PID %%a >nul 2>&1

REM Backend
pushd backend
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Test if pip is working, if not recreate venv
pip --version >nul 2>&1
if errorlevel 1 (
    echo Virtual environment is corrupted, rebuilding...
    cd ..
    rmdir /s /q backend\venv
    cd backend
    python -m venv venv
    call venv\Scripts\activate.bat
)

echo Installing backend dependencies...
python -m pip install --upgrade pip
pip install -r requirements.txt
pip install -e .
start "Backend" cmd /k "venv\Scripts\activate.bat && python -m uvicorn src.main:app --host 127.0.0.1 --port 8000 --reload || pause"
popd

REM Frontend
pushd frontend
if not exist "node_modules" npm install >nul 2>&1
set VITE_DISABLE_FALLBACK=true
start "Frontend" cmd /k "npm run dev || pause"
popd

start "" "http://localhost:5173"
endlocal
exit /b 0
