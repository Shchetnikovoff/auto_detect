@echo off
echo ========================================
echo    AlloyPredictor - Запуск сервера
echo ========================================
echo.

cd /d "%~dp0backend"

echo Проверка виртуального окружения...
if not exist "venv" (
    echo Создание виртуального окружения...
    python -m venv venv
)

echo Активация виртуального окружения...
call venv\Scripts\activate.bat

echo Установка зависимостей...
pip install -r requirements.txt -q

echo.
echo ========================================
echo Запуск AlloyPredictor API...
echo API: http://localhost:8000
echo Docs: http://localhost:8000/docs
echo ========================================
echo.

python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
