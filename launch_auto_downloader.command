#!/bin/bash

# Переход в директорию проекта
cd "$(dirname "$0")"

# Активация виртуального окружения (если есть)
if [ -d "venv" ]; then
    source venv/bin/activate
    echo "✅ Виртуальное окружение активировано"
fi

# Проверка установки зависимостей
echo "🔍 Проверка зависимостей..."

if ! python -c "import selenium" 2>/dev/null; then
    echo "📦 Установка Selenium..."
    pip install selenium
fi

if ! python -c "import webdriver_manager" 2>/dev/null; then
    echo "📦 Установка WebDriver Manager..."
    pip install webdriver-manager
fi

if ! python -c "import streamlit" 2>/dev/null; then
    echo "📦 Установка Streamlit..."
    pip install streamlit
fi

if ! python -c "import pandas" 2>/dev/null; then
    echo "📦 Установка Pandas..."
    pip install pandas
fi

if ! python -c "import openpyxl" 2>/dev/null; then
    echo "📦 Установка OpenPyXL..."
    pip install openpyxl
fi

echo "🚀 Запуск автоматического скачивания отчетов WB..."
echo "📱 Откройте браузер и введите данные для входа в личный кабинет"
echo ""

# Запуск приложения
streamlit run wb_auto_downloader.py --server.port 8508 --server.headless false

echo ""
echo "👋 Приложение закрыто"
