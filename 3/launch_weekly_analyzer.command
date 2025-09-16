#!/bin/bash

# Переходим в директорию скрипта
cd "$(dirname "$0")"

# Проверяем, существует ли виртуальное окружение
if [ ! -d "venv" ]; then
    echo "Создаем виртуальное окружение..."
    python3 -m venv venv
fi

# Активируем виртуальное окружение
source venv/bin/activate

# Устанавливаем зависимости
echo "Устанавливаем зависимости..."
pip install -r requirements.txt

# Запускаем анализатор
echo "Запускаем анализатор еженедельных продаж..."
streamlit run weekly_sales_analyzer.py

# Держим терминал открытым
echo "Нажмите Enter для закрытия..."
read
