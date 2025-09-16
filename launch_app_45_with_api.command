В#!/bin/bash

# Переходим в директорию проекта
cd "$(dirname "$0")"

# Активируем виртуальное окружение
source venv/bin/activate

# Запускаем приложение
streamlit run app_45_analysis_with_api.py --server.port 8521

echo "Приложение запущено на http://localhost:8521"
Выкупили, шт