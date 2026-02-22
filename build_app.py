#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для сборки WB Dashboard в исполняемый файл
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path

def clean_build():
    """Очистка предыдущих сборок"""
    print("🧹 Очистка предыдущих сборок...")
    
    dirs_to_clean = ["build", "dist", "__pycache__"]
    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            shutil.rmtree(dir_name)
            print(f"✅ Удалена директория: {dir_name}")
    
    # Удаляем файлы .pyc
    for root, dirs, files in os.walk("."):
        for file in files:
            if file.endswith(".pyc"):
                os.remove(os.path.join(root, file))
        # Удаляем __pycache__ директории
        for dir_name in dirs[:]:
            if dir_name == "__pycache__":
                shutil.rmtree(os.path.join(root, dir_name))
                dirs.remove(dir_name)

def build_with_pyinstaller():
    """Сборка с помощью PyInstaller"""
    print("🔨 Сборка приложения с PyInstaller...")
    
    try:
        # Команда PyInstaller
        cmd = [
            "pyinstaller",
            "--onefile",
            "--windowed",
            "--name=WB_Dashboard",
            "--add-data=dashboard_final.py:.",
            "--add-data=*.json:.",
            "--add-data=*.csv:.",
            "--add-data=*.xlsx:.",
            "--hidden-import=streamlit",
            "--hidden-import=pandas",
            "--hidden-import=numpy",
            "--hidden-import=plotly",
            "--hidden-import=requests",
            "--hidden-import=PIL",
            "--hidden-import=openpyxl",
            "--hidden-import=prophet",
            "--hidden-import=scipy",
            "launcher.py"
        ]
        
        print("Выполняется команда:", " ".join(cmd))
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        
        print("✅ Сборка завершена успешно!")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Ошибка сборки: {e}")
        print(f"Вывод: {e.stdout}")
        print(f"Ошибки: {e.stderr}")
        return False

def build_with_spec():
    """Сборка с помощью spec файла"""
    print("🔨 Сборка приложения с помощью spec файла...")
    
    try:
        cmd = ["pyinstaller", "wb_dashboard.spec"]
        print("Выполняется команда:", " ".join(cmd))
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        
        print("✅ Сборка завершена успешно!")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Ошибка сборки: {e}")
        print(f"Вывод: {e.stdout}")
        print(f"Ошибки: {e.stderr}")
        return False

def create_macos_app():
    """Создание macOS App Bundle"""
    print("🍎 Создание macOS App Bundle...")
    
    app_name = "WB Dashboard.app"
    app_path = Path("dist") / app_name
    contents_path = app_path / "Contents"
    macos_path = contents_path / "MacOS"
    resources_path = contents_path / "Resources"
    
    # Создаем структуру App Bundle
    macos_path.mkdir(parents=True, exist_ok=True)
    resources_path.mkdir(parents=True, exist_ok=True)
    
    # Создаем Info.plist
    info_plist = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key>
    <string>WB_Dashboard</string>
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
</dict>
</plist>"""
    
    with open(contents_path / "Info.plist", "w") as f:
        f.write(info_plist)
    
    # Копируем исполняемый файл
    exe_path = Path("dist") / "WB_Dashboard"
    if exe_path.exists():
        shutil.copy2(exe_path, macos_path / "WB_Dashboard")
        print(f"✅ Создан {app_name}")
        return True
    else:
        print(f"❌ Исполняемый файл не найден: {exe_path}")
        return False

def main():
    """Основная функция"""
    print("🚀 WB Dashboard - Сборка приложения")
    print("=" * 50)
    
    # Проверяем, что мы в правильной директории
    if not os.path.exists("dashboard_final.py"):
        print("❌ Ошибка: Файл dashboard_final.py не найден!")
        print("Запустите скрипт из директории с проектом")
        return
    
    # Очистка
    clean_build()
    
    print("\nВыберите метод сборки:")
    print("1. PyInstaller (простой)")
    print("2. PyInstaller с spec файлом")
    print("3. Создать macOS App Bundle")
    print("4. Все варианты")
    
    choice = input("\nВведите номер (1-4): ").strip()
    
    if choice == "1":
        success = build_with_pyinstaller()
    elif choice == "2":
        success = build_with_spec()
    elif choice == "3":
        if build_with_spec():
            success = create_macos_app()
        else:
            success = False
    elif choice == "4":
        print("\n🔨 Сборка всех вариантов...")
        success1 = build_with_pyinstaller()
        success2 = build_with_spec()
        success3 = create_macos_app()
        success = success1 or success2 or success3
    else:
        print("❌ Неверный выбор!")
        return
    
    if success:
        print("\n✅ Сборка завершена!")
        print("\n📁 Результаты:")
        
        if os.path.exists("dist"):
            for item in os.listdir("dist"):
                item_path = os.path.join("dist", item)
                if os.path.isfile(item_path):
                    size = os.path.getsize(item_path) / (1024 * 1024)
                    print(f"  📄 {item} ({size:.1f} МБ)")
                else:
                    print(f"  📁 {item}/")
        
        print("\n🎉 Приложение готово к использованию!")
        print("💡 Для запуска дважды кликните на файл в папке dist/")
    else:
        print("\n❌ Сборка не удалась!")
        print("💡 Попробуйте установить недостающие зависимости")

if __name__ == "__main__":
    main()
