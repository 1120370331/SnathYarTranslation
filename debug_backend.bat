@echo off
setlocal EnableExtensions
chcp 65001 >nul

echo Diagnosing Backend Startup Issues...
echo ====================================

REM Check current directory
echo Current directory: %CD%
echo.

REM Switch to backend directory
pushd backend
echo Switched to backend directory: %CD%
echo.

REM Check virtual environment
if exist "venv" (
    echo OK Virtual environment exists
) else (
    echo ERROR Virtual environment does not exist
    echo Creating virtual environment...
    python -m venv venv
)

REM Check activate.bat
if exist "venv\Scripts\activate.bat" (
    echo OK activate.bat exists
) else (
    echo ERROR activate.bat does not exist
)

echo.
echo Activating virtual environment and installing dependencies...
call venv\Scripts\activate.bat

echo.
echo Python version:
python --version

echo.
echo Installing/updating packages...
echo Upgrading pip...
pip install --upgrade pip

echo.
echo Installing dependencies from requirements.txt...
pip install -r requirements.txt

echo.
echo Installing project itself...
pip install -e .

echo.
echo Checking key dependencies installation status:
python -c "import fastapi; print('OK FastAPI:', fastapi.__version__)" 2>nul || echo "ERROR FastAPI not installed"
python -c "import uvicorn; print('OK Uvicorn:', uvicorn.__version__)" 2>nul || echo "ERROR Uvicorn not installed"
python -c "import sqlalchemy; print('OK SQLAlchemy:', sqlalchemy.__version__)" 2>nul || echo "ERROR SQLAlchemy not installed"

echo.
echo Attempting to start server...
echo If this fails, you will see the specific error message:
echo.

python -m uvicorn src.main:app --host 127.0.0.1 --port 8000 --reload

echo.
echo Press any key to continue...
pause >nul

popd
endlocal