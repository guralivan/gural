#!/bin/bash

# Переход в директорию проекта
cd "$(dirname "$0")"

# Активация виртуального окружения
source .venv/bin/activate

# Установка зависимостей
pip install -r requirements_unit_economics.txt

# Запуск финальной версии приложения
streamlit run unit_economics_products_table_FINAL.py --server.port 8505 --server.address localhost

# Ожидание нажатия клавиши для закрытия
echo "Нажмите любую клавишу для закрытия..."
read -n 1
