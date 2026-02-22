#!/bin/bash
cd "$(dirname "$0")"
echo "🚀 Запуск ультра-простого анализатора отчетов Wildberries..."
if [ ! -d "venv" ]; then
    echo "📦 Создание виртуального окружения..."
    python3 -m venv venv
fi
echo "🔧 Активация виртуального окружения..."
source venv/bin/activate
echo "📥 Установка зависимостей..."
pip install -r requirements.txt
echo "🌐 Запуск приложения..."
echo "📊 Приложение будет доступно по адресу: http://localhost:8501"
echo "🔄 Для остановки нажмите Ctrl+C"
echo ""
streamlit run wb_analyzer_ultra_simple.py --server.port 8501 --server.address localhost




























