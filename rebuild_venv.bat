@echo off
setlocal EnableExtensions
chcp 65001 >nul

echo Rebuilding Virtual Environment for Backend
echo ==========================================

pushd backend

echo Step 1: Removing corrupted virtual environment...
if exist "venv" (
    echo Deleting existing venv directory...
    rmdir /s /q venv
    echo OK Old virtual environment removed
) else (
    echo OK No existing virtual environment found
)

echo.
echo Step 2: Creating fresh virtual environment...
python -m venv venv

if not exist "venv" (
    echo ERROR: Failed to create virtual environment
    echo Make sure Python is installed and accessible
    pause
    exit /b 1
)

echo OK Virtual environment created successfully

echo.
echo Step 3: Activating virtual environment...
call venv\Scripts\activate.bat

echo.
echo Step 4: Upgrading pip to latest version...
python -m pip install --upgrade pip

echo.
echo Step 5: Installing dependencies from requirements.txt...
pip install -r requirements.txt

echo.
echo Step 6: Installing project in editable mode...
pip install -e .

echo.
echo Step 7: Verifying installations...
echo.

python -c "import uvicorn; print('OK Uvicorn installed:', uvicorn.__version__)" || echo "ERROR: Uvicorn installation failed"
python -c "import fastapi; print('OK FastAPI installed:', fastapi.__version__)" || echo "ERROR: FastAPI installation failed"
python -c "import sqlalchemy; print('OK SQLAlchemy installed:', sqlalchemy.__version__)" || echo "ERROR: SQLAlchemy installation failed"

echo.
echo Virtual environment rebuild completed!
echo You can now run start.bat to launch the application
echo.

popd

pause
endlocal