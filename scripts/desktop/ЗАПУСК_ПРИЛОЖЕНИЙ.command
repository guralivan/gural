#!/bin/bash

# Скрипт для запуска WB Dashboard в разных режимах
echo "🚀 WB Dashboard - Выберите способ запуска"
echo "=========================================="

# Проверяем наличие файлов
if [ ! -f "dashboard_final.py" ]; then
    echo "❌ Ошибка: Файл dashboard_final.py не найден!"
    echo "Запустите скрипт из директории с проектом"
    exit 1
fi

echo ""
echo "Доступные варианты:"
echo "1. 🍎 macOS приложение (WB Dashboard.app)"
echo "2. 💻 Консольное приложение"
echo "3. 🐍 Обычный Python запуск"
echo "4. 🧪 Тестирование всех вариантов"
echo "5. 📦 Создание новых приложений"
echo ""

read -p "Выберите вариант (1-5): " choice

case $choice in
    1)
        echo "🍎 Запуск macOS приложения..."
        if [ -d "WB Dashboard.app" ]; then
            open "WB Dashboard.app"
            echo "✅ macOS приложение запущено!"
            echo "🌐 Приложение откроется в браузере через несколько секунд"
        else
            echo "❌ macOS приложение не найдено!"
            echo "💡 Создайте его командой: ./create_macos_app.command"
        fi
        ;;
    2)
        echo "💻 Запуск консольного приложения..."
        if [ -f "dist/WB_Dashboard_Console" ]; then
            echo "🌐 Открытие браузера через 3 секунды..."
            sleep 3
            open http://localhost:8501
            ./dist/WB_Dashboard_Console
        else
            echo "❌ Консольное приложение не найдено!"
            echo "💡 Создайте его командой: pyinstaller --onefile --console --name=WB_Dashboard_Console launcher.py"
        fi
        ;;
    3)
        echo "🐍 Запуск через Python..."
        if [ -d "venv" ]; then
            source venv/bin/activate
            python3 launcher.py
        else
            echo "❌ Виртуальное окружение не найдено!"
            echo "💡 Создайте его командой: python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
        fi
        ;;
    4)
        echo "🧪 Тестирование всех вариантов..."
        python3 test_apps.py
        ;;
    5)
        echo "📦 Создание новых приложений..."
        echo "Выберите тип:"
        echo "1. macOS приложение"
        echo "2. Консольное приложение"
        echo "3. Оба варианта"
        read -p "Введите номер (1-3): " build_choice
        
        case $build_choice in
            1)
                ./create_macos_app.command
                ;;
            2)
                source venv/bin/activate
                pyinstaller --onefile --console --name=WB_Dashboard_Console launcher.py
                ;;
            3)
                ./create_macos_app.command
                source venv/bin/activate
                pyinstaller --onefile --console --name=WB_Dashboard_Console launcher.py
                ;;
            *)
                echo "❌ Неверный выбор!"
                ;;
        esac
        ;;
    *)
        echo "❌ Неверный выбор!"
        ;;
esac

echo ""
echo "💡 Полезные команды:"
echo "   📖 Документация: open README_УПАКОВКА.md"
echo "   🧪 Тестирование: python3 test_apps.py"
echo "   🍎 macOS приложение: open 'WB Dashboard.app'"
echo "   💻 Консольное приложение: ./dist/WB_Dashboard_Console"
echo "   🐍 Python запуск: python3 launcher.py"

echo ""
read -p "Нажмите Enter для выхода..."