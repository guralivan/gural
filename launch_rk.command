#!/bin/bash

# Запуск приложения эффективной рекламы маркетплейса (RK)

echo "🚀 Запуск приложения Реклама маркетплейса (RK)..."

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 не найден. Установите Python3."
    read -n 1 -r
    exit 1
fi

if ! python3 -c "import streamlit" 2>/dev/null; then
    echo "📦 Установка зависимостей (streamlit, pandas, openpyxl)..."
    if ! python3 -m pip install streamlit pandas openpyxl; then
        echo "❌ Ошибка установки. Попробуйте: python3 -m pip install streamlit pandas openpyxl"
        read -n 1 -r
        exit 1
    fi
    echo "✅ Зависимости установлены."
fi

echo "🎯 Запуск Streamlit (RK)..."
cd "$SCRIPT_DIR/RK"
if ! python3 -m streamlit run app_rk.py --server.port 8509 --server.address localhost; then
    echo ""
    echo "❌ Ошибка запуска. Проверьте вывод выше."
    read -n 1 -r -p "Нажмите любую клавишу для выхода..."
    exit 1
fi
echo ""
echo "✅ Приложение было на http://localhost:8509"
read -n 1 -r -p "Нажмите любую клавишу для выхода..."
