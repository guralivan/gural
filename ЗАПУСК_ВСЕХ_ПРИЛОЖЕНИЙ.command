#!/bin/bash

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  🚀 ЗАПУСК 6 ОСНОВНЫХ ПРИЛОЖЕНИЙ${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Переходим в директорию проекта
echo -e "${YELLOW}📁 Переход в директорию проекта...${NC}"
cd "/Users/ivangural/Downloads/wb_dashboard_streamlit"

# Проверяем виртуальное окружение
if [ -d "venv" ]; then
    echo -e "${GREEN}✅ Виртуальное окружение найдено${NC}"
    source venv/bin/activate
elif [ -d ".venv" ]; then
    echo -e "${GREEN}✅ Виртуальное окружение найдено${NC}"
    source .venv/bin/activate
else
    echo -e "${RED}❌ Виртуальное окружение не найдено!${NC}"
    exit 1
fi

echo ""
echo -e "${BLUE}🚀 Запуск 6 основных приложений...${NC}"
echo ""

# Проверяем, что порты свободны
check_port() {
    if lsof -Pi :$1 -sTCP:LISTEN -t >/dev/null ; then
        echo -e "${RED}❌ Порт $1 уже занят! Останавливаем процесс...${NC}"
        lsof -ti :$1 | xargs kill -9
        sleep 2
    fi
}

# Проверяем все порты
check_port 8501
check_port 8502
check_port 8503
check_port 8504
check_port 8505
check_port 8506

# 1. Запускаем Юнит экономику (приоритетное приложение - порт 8501)
echo -e "${PURPLE}🏭 Запуск Юнит экономики (порт 8501)...${NC}"
streamlit run unit_economics_products_table_FINAL.py --server.port 8501 --server.address localhost &
APP1_PID=$!
sleep 3

# 2. Запускаем Анализ отчетов (порт 8502)
echo -e "${YELLOW}📋 Запуск Анализа отчетов (порт 8502)...${NC}"
cd 3
streamlit run weekly_expenses_analyzer_final_stable.py --server.port 8502 --server.address localhost &
APP2_PID=$!
cd ..
sleep 3

# 3. Запускаем Калькулятор заказов (порт 8503)
echo -e "${GREEN}📦 Запуск Калькулятора заказов (порт 8503)...${NC}"
streamlit run order_balance_app.py --server.port 8503 --server.address localhost &
APP3_PID=$!
sleep 3

# 4. Запускаем Сезонный калькулятор (порт 8504)
echo -e "${BLUE}🌡️ Запуск Сезонного калькулятора (порт 8504)...${NC}"
streamlit run seasonal_expenses_calculator.py --server.port 8504 --server.address localhost &
APP4_PID=$!
sleep 3

# 5. Запускаем Основное приложение (порт 8505)
echo -e "${CYAN}🎯 Запуск Основного приложения (порт 8505)...${NC}"
streamlit run dashboard_final.py --server.port 8505 --server.address localhost &
APP5_PID=$!
sleep 3

# 6. Запускаем Календарь производства и логистики (порт 8506)
echo -e "${RED}📅 Запуск Календаря производства и логистики (порт 8506)...${NC}"
streamlit run production_calendar.py --server.port 8506 --server.address localhost &
APP6_PID=$!
sleep 3

echo ""
echo -e "${GREEN}✅ Все 6 приложений запущены!${NC}"
echo ""
echo -e "${BLUE}🌐 Доступные приложения:${NC}"
echo -e "   ${PURPLE}🏭 Юнит экономика: ${YELLOW}http://localhost:8501${NC}"
echo -e "   ${YELLOW}📋 Анализ отчетов: ${YELLOW}http://localhost:8502${NC}"
echo -e "   ${GREEN}📦 Калькулятор заказов: ${YELLOW}http://localhost:8503${NC}"
echo -e "   ${BLUE}🌡️ Сезонный калькулятор: ${YELLOW}http://localhost:8504${NC}"
echo -e "   ${CYAN}🎯 Основное приложение: ${YELLOW}http://localhost:8505${NC}"
echo -e "   ${RED}📅 Календарь производства: ${YELLOW}http://localhost:8506${NC}"
echo ""
echo -e "${YELLOW}💡 Приложения автоматически откроются в браузере через несколько секунд${NC}"
echo -e "${RED}Нажмите Ctrl+C для остановки всех приложений...${NC}"

# Ждем сигнала для остановки
trap "echo ''; echo -e '${RED}🛑 Остановка всех приложений...${NC}'; kill $APP1_PID $APP2_PID $APP3_PID $APP4_PID $APP5_PID $APP6_PID 2>/dev/null; echo -e '${GREEN}✅ Все приложения остановлены${NC}'; exit" INT

# Ждем завершения
wait
