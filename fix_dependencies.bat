@echo off
setlocal EnableExtensions
chcp 65001 >nul

echo Quick Fix for Backend Dependencies
echo ===================================

pushd backend

echo Activating virtual environment...
call venv\Scripts\activate.bat

echo Upgrading pip...
pip install --upgrade pip

echo Installing dependencies from requirements.txt...
pip install -r requirements.txt

echo Installing project package...
pip install -e .

echo.
echo Checking installed modules...
echo.

python -c "import uvicorn; print('OK Uvicorn installed:', uvicorn.__version__)" || echo "ERROR: Uvicorn installation failed"
python -c "import fastapi; print('OK FastAPI installed:', fastapi.__version__)" || echo "ERROR: FastAPI installation failed"
python -c "import sqlalchemy; print('OK SQLAlchemy installed:', sqlalchemy.__version__)" || echo "ERROR: SQLAlchemy installation failed"

echo.
echo Fix completed! You can now run start.bat
echo.

popd

pause
endlocal