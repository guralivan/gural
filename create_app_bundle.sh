#!/bin/bash

# Создаем структуру приложения
mkdir -p "Генератор договоров.app/Contents/MacOS"
mkdir -p "Генератор договоров.app/Contents/Resources"

# Создаем Info.plist
cat > "Генератор договоров.app/Contents/Info.plist" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key>
    <string>Генератор договоров</string>
    <key>CFBundleIdentifier</key>
    <string>com.blogger.contract-generator</string>
    <key>CFBundleName</key>
    <string>Генератор договоров</string>
    <key>CFBundleVersion</key>
    <string>1.0</string>
    <key>CFBundleShortVersionString</key>
    <string>1.0</string>
    <key>CFBundleInfoDictionaryVersion</key>
    <string>6.0</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>CFBundleSignature</key>
    <string>????</string>
    <key>LSMinimumSystemVersion</key>
    <string>10.15</string>
</dict>
</plist>
EOF

# Создаем исполняемый файл
cat > "Генератор договоров.app/Contents/MacOS/Генератор договоров" << 'EOF'
#!/bin/bash

# Получаем путь к приложению
APP_PATH="$(dirname "$0")"
PROJECT_PATH="$(dirname "$APP_PATH")"
PROJECT_PATH="$(dirname "$PROJECT_PATH")"
PROJECT_PATH="$(dirname "$PROJECT_PATH")"

# Переходим в папку с проектом
cd "$PROJECT_PATH"

# Активируем виртуальное окружение
source venv/bin/activate

# Запускаем приложение
python3 -m streamlit run contract_generator_app.py --server.port 8507
EOF

# Делаем исполняемым
chmod +x "Генератор договоров.app/Contents/MacOS/Генератор договоров"

echo "Приложение создано: Генератор договоров.app"
echo "Можете переместить его в папку Applications"
