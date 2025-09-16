#!/bin/bash

# Переходим в директорию проекта
cd "/Users/ivangural/Downloads/wb_dashboard_streamlit"

# Активируем виртуальное окружение
source venv/bin/activate

echo "📦 Запуск калькулятора заказов и баланса..."
echo ""

# Запускаем калькулятор баланса
streamlit run order_balance_app.py --server.port 8503 --server.address localhost

echo ""
echo "✅ Калькулятор баланса запущен на http://localhost:8503"




