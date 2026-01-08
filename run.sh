#!/bin/bash

echo "========================================"
echo "   AlloyPredictor - Запуск сервера"
echo "========================================"
echo

cd "$(dirname "$0")/backend"

echo "Проверка виртуального окружения..."
if [ ! -d "venv" ]; then
    echo "Создание виртуального окружения..."
    python3 -m venv venv
fi

echo "Активация виртуального окружения..."
source venv/bin/activate

echo "Установка зависимостей..."
pip install -r requirements.txt -q

echo
echo "========================================"
echo "Запуск AlloyPredictor API..."
echo "API: http://localhost:8000"
echo "Docs: http://localhost:8000/docs"
echo "========================================"
echo

python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
