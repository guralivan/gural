#!/bin/bash

# Переходим в директорию проекта
cd "/Users/ivangural/Downloads/wb_dashboard_streamlit"

# Активируем виртуальное окружение
source venv/bin/activate

echo "📅 Запуск Календаря производства и логистики..."
echo ""

# Запускаем календарь производства
streamlit run apps/production_calendar/production_calendar.py --server.port 8506 --server.address localhost

echo ""
echo "✅ Календарь производства запущен на http://localhost:8506" 