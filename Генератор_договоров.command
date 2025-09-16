#!/bin/bash

# Переходим в папку с приложением
cd "/Users/ivangural/Downloads/wb_dashboard_streamlit"

# Активируем виртуальное окружение
source venv/bin/activate

# Запускаем приложение
python3 -m streamlit run contract_generator_app.py --server.port 8507

# Оставляем терминал открытым
echo "Приложение остановлено. Нажмите любую клавишу для закрытия..."
read -n 1
