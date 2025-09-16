#!/bin/bash

# Скрипт для создания ярлыков на рабочем столе

echo "🖥️ Создание ярлыков на рабочем столе..."

# Путь к проекту
PROJECT_PATH="/Users/ivangural/Downloads/wb_dashboard_streamlit"

# Создаем ярлык для календаря производства
cat > ~/Desktop/📅_Календарь_производства.command << 'EOF'
#!/bin/bash
cd "/Users/ivangural/Downloads/wb_dashboard_streamlit"
source venv/bin/activate
streamlit run production_calendar.py --server.port 8506
EOF

chmod +x ~/Desktop/📅_Календарь_производства.command

# Создаем ярлык для основного приложения
cat > ~/Desktop/🎯_WB_Dashboard.command << 'EOF'
#!/bin/bash
cd "/Users/ivangural/Downloads/wb_dashboard_streamlit"
source venv/bin/activate
streamlit run dashboard_final.py --server.port 8505
EOF

chmod +x ~/Desktop/🎯_WB_Dashboard.command

# Создаем ярлык для запуска всех приложений
cat > ~/Desktop/🚀_Все_приложения.command << 'EOF'
#!/bin/bash
cd "/Users/ivangural/Downloads/wb_dashboard_streamlit"
./launch_all_apps_improved.command
EOF

chmod +x ~/Desktop/🚀_Все_приложения.command

echo "✅ Ярлыки созданы на рабочем столе:"
echo "   📅 Календарь производства"
echo "   🎯 WB Dashboard"
echo "   🚀 Все приложения"