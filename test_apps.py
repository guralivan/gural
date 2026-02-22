#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для тестирования созданных приложений
"""

import os
import sys
import subprocess
import time
from pathlib import Path

def test_launcher():
    """Тестирование launcher.py"""
    print("🧪 Тестирование launcher.py...")
    
    try:
        # Проверяем, что файл существует
        launcher_path = Path("launcher.py")
        if not launcher_path.exists():
            print("❌ Файл launcher.py не найден!")
            return False
        
        # Проверяем синтаксис
        with open(launcher_path, 'r', encoding='utf-8') as f:
            code = f.read()
        
        compile(code, str(launcher_path), 'exec')
        print("✅ Синтаксис launcher.py корректен")
        
        # Проверяем импорты
        import ast
        tree = ast.parse(code)
        
        required_imports = ['os', 'sys', 'subprocess', 'webbrowser', 'time', 'pathlib']
        imports_found = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports_found.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports_found.append(node.module)
        
        print(f"✅ Найдены импорты: {imports_found}")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка тестирования launcher.py: {e}")
        return False

def test_dashboard():
    """Тестирование dashboard_final.py"""
    print("🧪 Тестирование dashboard_final.py...")
    
    try:
        dashboard_path = Path("dashboard_final.py")
        if not dashboard_path.exists():
            print("❌ Файл dashboard_final.py не найден!")
            return False
        
        # Проверяем синтаксис
        with open(dashboard_path, 'r', encoding='utf-8') as f:
            code = f.read()
        
        compile(code, str(dashboard_path), 'exec')
        print("✅ Синтаксис dashboard_final.py корректен")
        
        # Проверяем ключевые компоненты
        key_components = [
            'import streamlit as st',
            'def main()',
            'st.set_page_config',
            'st.title',
            'st.dataframe',
            'st.data_editor'
        ]
        
        for component in key_components:
            if component in code:
                print(f"✅ Найден компонент: {component}")
            else:
                print(f"⚠️ Не найден компонент: {component}")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка тестирования dashboard_final.py: {e}")
        return False

def test_executable():
    """Тестирование исполняемого файла"""
    print("🧪 Тестирование исполняемого файла...")
    
    exe_path = Path("dist/WB_Dashboard_Console")
    if not exe_path.exists():
        print("❌ Исполняемый файл не найден!")
        return False
    
    # Проверяем права на выполнение
    if not os.access(exe_path, os.X_OK):
        print("❌ Нет прав на выполнение!")
        return False
    
    print("✅ Исполняемый файл найден и имеет права на выполнение")
    
    # Проверяем размер
    size_mb = exe_path.stat().st_size / (1024 * 1024)
    print(f"✅ Размер файла: {size_mb:.1f} МБ")
    
    return True

def test_macos_app():
    """Тестирование macOS приложения"""
    print("🧪 Тестирование macOS приложения...")
    
    app_path = Path("WB Dashboard.app")
    if not app_path.exists():
        print("❌ macOS приложение не найдено!")
        return False
    
    # Проверяем структуру
    contents_path = app_path / "Contents"
    macos_path = contents_path / "MacOS"
    resources_path = contents_path / "Resources"
    info_plist = contents_path / "Info.plist"
    
    required_items = [contents_path, macos_path, resources_path, info_plist]
    
    for item in required_items:
        if item.exists():
            print(f"✅ Найден: {item}")
        else:
            print(f"❌ Не найден: {item}")
            return False
    
    # Проверяем launcher скрипт
    launcher_path = macos_path / "launcher"
    if launcher_path.exists() and os.access(launcher_path, os.X_OK):
        print("✅ Launcher скрипт найден и исполняемый")
    else:
        print("❌ Launcher скрипт не найден или не исполняемый")
        return False
    
    return True

def main():
    """Основная функция тестирования"""
    print("🧪 Тестирование созданных приложений WB Dashboard")
    print("=" * 60)
    
    tests = [
        ("Launcher скрипт", test_launcher),
        ("Dashboard приложение", test_dashboard),
        ("Исполняемый файл", test_executable),
        ("macOS приложение", test_macos_app)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n🔍 {test_name}")
        print("-" * 40)
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Критическая ошибка: {e}")
            results.append((test_name, False))
    
    # Итоговый отчет
    print("\n" + "=" * 60)
    print("📊 ИТОГОВЫЙ ОТЧЕТ")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ ПРОШЕЛ" if result else "❌ НЕ ПРОШЕЛ"
        print(f"{status:12} | {test_name}")
        if result:
            passed += 1
    
    print("-" * 60)
    print(f"📈 Результат: {passed}/{total} тестов пройдено")
    
    if passed == total:
        print("🎉 Все тесты пройдены! Приложения готовы к использованию!")
        print("\n💡 Инструкции по запуску:")
        print("1. macOS приложение: Дважды кликните на 'WB Dashboard.app'")
        print("2. Консольное приложение: ./dist/WB_Dashboard_Console")
        print("3. Обычный запуск: python3 launcher.py")
    else:
        print("⚠️ Некоторые тесты не пройдены. Проверьте ошибки выше.")

if __name__ == "__main__":
    main()
