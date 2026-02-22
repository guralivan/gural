#!/bin/bash

# Скрипт для создания macOS приложения WB Dashboard
echo "🍎 Создание macOS приложения WB Dashboard..."

# Активируем виртуальное окружение
source venv/bin/activate

# Создаем директории
mkdir -p "WB Dashboard.app/Contents/MacOS"
mkdir -p "WB Dashboard.app/Contents/Resources"

# Создаем Info.plist
cat > "WB Dashboard.app/Contents/Info.plist" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key>
    <string>launcher</string>
    <key>CFBundleIdentifier</key>
    <string>com.wb.dashboard</string>
    <key>CFBundleName</key>
    <string>WB Dashboard</string>
    <key>CFBundleVersion</key>
    <string>1.0</string>
    <key>CFBundleShortVersionString</key>
    <string>1.0</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>CFBundleSignature</key>
    <string>????</string>
    <key>LSMinimumSystemVersion</key>
    <string>10.13</string>
    <key>NSHighResolutionCapable</key>
    <true/>
    <key>NSRequiresAquaSystemAppearance</key>
    <false/>
</dict>
</plist>
EOF

# Создаем скрипт запуска
cat > "WB Dashboard.app/Contents/MacOS/launcher" << 'EOF'
#!/bin/bash

# Получаем директорию приложения
APP_DIR="$(dirname "$0")"
PROJECT_DIR="$(dirname "$APP_DIR")"
PROJECT_DIR="$(dirname "$PROJECT_DIR")"

# Переходим в директорию проекта
cd "$PROJECT_DIR"

# Активируем виртуальное окружение
source venv/bin/activate

# Запускаем приложение
python3 launcher.py

# Ждем нажатия клавиши перед закрытием
read -p "Нажмите Enter для закрытия..."
EOF

# Делаем скрипт исполняемым
chmod +x "WB Dashboard.app/Contents/MacOS/launcher"

# Копируем необходимые файлы
cp dashboard_final.py "WB Dashboard.app/Contents/Resources/"
cp launcher.py "WB Dashboard.app/Contents/Resources/"
cp *.json "WB Dashboard.app/Contents/Resources/" 2>/dev/null || true
cp *.csv "WB Dashboard.app/Contents/Resources/" 2>/dev/null || true
cp *.xlsx "WB Dashboard.app/Contents/Resources/" 2>/dev/null || true

echo "✅ macOS приложение создано!"
echo "📁 Расположение: $(pwd)/WB Dashboard.app"
echo "🚀 Для запуска дважды кликните на 'WB Dashboard.app'"

# Открываем папку с приложением
open .
