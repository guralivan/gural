#!/bin/bash

# Переходим в директорию приложения
cd "/Users/ivangural/Downloads/wb_dashboard_streamlit"

# Активируем виртуальное окружение
source venv/bin/activate

# Запускаем новое приложение на порту 8510
streamlit run app_45_combined_api_new.py --server.port 8510

# Ждем нажатия клавиши для закрытия
read -p "Нажмите Enter для закрытия..."
