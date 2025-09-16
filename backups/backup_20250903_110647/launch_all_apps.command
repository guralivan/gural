#!/bin/bash

# Скрипт запуска всех приложений на разных портах
# Автоматически активирует виртуальное окружение и запускает все приложения

echo "🚀 Запуск всех приложений на разных портах..."

# Переходим в директорию проекта
cd "/Users/ivangural/Downloads/wb_dashboard_streamlit"

# Активируем виртуальное окружение
echo "📦 Активация виртуального окружения..."
source venv/bin/activate

# Функция для остановки процесса на порту
stop_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null ; then
        echo "⚠️  Порт $port уже занят. Останавливаю процесс..."
        lsof -ti:$port | xargs kill -9
        sleep 2
    fi
}

# Останавливаем процессы на всех портах
echo "🛑 Остановка процессов на портах..."
stop_port 8501
stop_port 8502
stop_port 8503
stop_port 8504
stop_port 8505
stop_port 8506
stop_port 8507
stop_port 8508
stop_port 8509

# Запускаем приложения на разных портах
echo "🌐 Запуск приложений..."

# Приложение анализа 45.xlsx на порту 8509 (основное)
echo "📊 Запуск приложения анализа 45.xlsx на порту 8509..."
streamlit run app_45_simple.py --server.port 8509 --server.address localhost &
sleep 3

# 1. Юнит экономика на порту 8501 (если существует)
if [ -f "UNIT/unit_economics_products_table_FINAL.py" ]; then
    echo "🏪 Запуск приложения Юнит экономика на порту 8501..."
    streamlit run "UNIT/unit_economics_products_table_FINAL.py" --server.port 8501 --server.address localhost &
    sleep 3
fi

# 2. Анализ отчетов на порту 8502 (если существует)
if [ -f "3/weekly_expenses_analyzer_final_stable.py" ]; then
    echo "📋 Запуск приложения Анализ отчетов на порту 8502..."
    streamlit run "3/weekly_expenses_analyzer_final_stable.py" --server.port 8502 --server.address localhost &
    sleep 3
fi

# 3. Калькулятор заказов на порту 8503 (если существует)
if [ -f "order_balance_app.py" ]; then
    echo "📦 Запуск приложения Калькулятор заказов на порту 8503..."
    streamlit run order_balance_app.py --server.port 8503 --server.address localhost &
    sleep 3
fi

# 4. Сезонный калькулятор на порту 8504 (если существует)
if [ -f "seasonal_expenses_calculator.py" ]; then
    echo "🌡️ Запуск приложения Сезонный калькулятор на порту 8504..."
    streamlit run seasonal_expenses_calculator.py --server.port 8504 --server.address localhost &
    sleep 3
fi

# 5. Основное приложение на порту 8505 (если существует)
if [ -f "dashboard_final.py" ]; then
    echo "🎯 Запуск приложения Основное приложение на порту 8505..."
    streamlit run dashboard_final.py --server.port 8505 --server.address localhost &
    sleep 3
fi

# 6. Календарь производства на порту 8506 (если существует)
if [ -f "production_calendar.py" ]; then
    echo "📅 Запуск приложения Календарь производства на порту 8506..."
    streamlit run production_calendar.py --server.port 8506 --server.address localhost &
    sleep 3
fi

echo ""
echo "✅ Все приложения запущены!"
echo ""
echo "🌐 Доступные приложения:"
echo "   📊 Анализ 45.xlsx: http://localhost:8509 (основное)"
if [ -f "UNIT/unit_economics_products_table_FINAL.py" ]; then
    echo "   🏪 Юнит экономика: http://localhost:8501"
fi
if [ -f "3/weekly_expenses_analyzer_final_stable.py" ]; then
    echo "   📋 Анализ отчетов: http://localhost:8502"
fi
if [ -f "order_balance_app.py" ]; then
    echo "   📦 Калькулятор заказов: http://localhost:8503"
fi
if [ -f "seasonal_expenses_calculator.py" ]; then
    echo "   🌡️ Сезонный калькулятор: http://localhost:8504"
fi
if [ -f "dashboard_final.py" ]; then
    echo "   🎯 Основное приложение: http://localhost:8505"
fi
if [ -f "production_calendar.py" ]; then
    echo "   📅 Календарь производства: http://localhost:8506"
fi
echo ""
echo "💡 Для остановки всех приложений используйте: pkill -f streamlit"
echo ""

# Ждем завершения всех процессов
wait
