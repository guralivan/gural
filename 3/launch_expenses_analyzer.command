#!/bin/bash

# Переходим в директорию скрипта
cd "$(dirname "$0")"

# Активируем виртуальное окружение, если оно существует
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Запускаем Streamlit приложение
streamlit run weekly_expenses_analyzer.py --server.port 8501 --server.address localhost

# Ждем нажатия клавиши перед закрытием
echo "Нажмите любую клавишу для закрытия..."
read -n 1
