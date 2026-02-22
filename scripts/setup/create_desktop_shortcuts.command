#!/bin/bash

# Скрипт для создания ярлыков на рабочем столе

echo "🖥️ Создание ярлыков на рабочем столе..."

# Путь к проекту
PROJECT_PATH="/Users/ivangural/Downloads/wb_dashboard_streamlit"

# Создаем ярлык для календаря производства
cat > ~/Desktop/📅_Календарь_производства.command << 'EOF'
#!/bin/bash
cd "/Users/ivangural/Downloads/wb_dashboard_streamlit"
if [ -d "venv" ]; then
    source venv/bin/activate
elif [ -d ".venv" ]; then
    source .venv/bin/activate
fi
streamlit run apps/production_calendar/production_calendar.py --server.port 8506 --server.address localhost
EOF

chmod +x ~/Desktop/📅_Календарь_производства.command

# Создаем ярлык для основного приложения
cat > ~/Desktop/📈_Дашборд.command << 'EOF'
#!/bin/bash
cd "/Users/ivangural/Downloads/wb_dashboard_streamlit"
if [ -d "venv" ]; then
    source venv/bin/activate
elif [ -d ".venv" ]; then
    source .venv/bin/activate
fi
streamlit run apps/dashboard/dashboard_final.py --server.port 8502 --server.address localhost
EOF

chmod +x ~/Desktop/📈_Дашборд.command

# Создаем ярлык для запуска всех приложений
cat > ~/Desktop/🚀_Все_приложения.command << 'EOF'
#!/bin/bash
cd "/Users/ivangural/Downloads/wb_dashboard_streamlit"
./launch_all_apps_improved.command
EOF

chmod +x ~/Desktop/🚀_Все_приложения.command

echo "✅ Ярлыки созданы на рабочем столе:"
echo "   📅 Календарь производства"
echo "   📈 Дашборд"
echo "   🚀 Все приложения"