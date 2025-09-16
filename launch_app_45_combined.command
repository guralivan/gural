#!/bin/bash

# Переходим в директорию проекта
cd "/Users/ivangural/Downloads/wb_dashboard_streamlit"

# Активируем виртуальное окружение
source .venv/bin/activate

# Устанавливаем зависимости
pip install -r requirements_app_45_combined.txt

# Запускаем приложение
streamlit run app_45_combined_api.py


