#!/bin/bash

# Переходим в директорию проекта
cd "$(dirname "$0")"

# Активируем виртуальное окружение
source venv/bin/activate

# Запускаем приложение
streamlit run app_analytics_full.py --server.port 8522

echo "Приложение запущено на http://localhost:8522"
