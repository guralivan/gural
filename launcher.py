#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WB Dashboard Launcher
Запускает Streamlit приложение с правильными настройками
"""

import os
import sys
import subprocess
import webbrowser
import time
from pathlib import Path

def main():
    """Основная функция запуска"""
    
    # Получаем путь к текущему файлу
    current_dir = Path(__file__).parent.absolute()
    dashboard_file = current_dir / "dashboard_final.py"
    
    print("🚀 Запуск WB Dashboard...")
    print(f"📁 Директория: {current_dir}")
    print(f"📄 Файл приложения: {dashboard_file}")
    
    # Проверяем, что файл существует
    if not dashboard_file.exists():
        print(f"❌ Ошибка: Файл {dashboard_file} не найден!")
        input("Нажмите Enter для выхода...")
        return
    
    # Настройки Streamlit
    streamlit_config = {
        "server.headless": "true",
        "server.enableCORS": "false",
        "server.enableXsrfProtection": "false",
        "browser.gatherUsageStats": "false"
    }
    
    # Находим свободный порт
    import socket
    def find_free_port():
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('', 0))
            s.listen(1)
            port = s.getsockname()[1]
        return port
    
    port = find_free_port()
    
    # Создаем команду запуска
    cmd = [
        sys.executable, "-m", "streamlit", "run", 
        str(dashboard_file),
        "--server.port", str(port),
        "--server.address", "localhost",
        "--server.headless", "true",
        "--browser.gatherUsageStats", "false"
    ]
    
    try:
        print("🌐 Открытие браузера через 3 секунды...")
        
        # Запускаем Streamlit в фоновом режиме
        process = subprocess.Popen(cmd, cwd=current_dir)
        
        # Ждем 3 секунды и открываем браузер
        time.sleep(3)
        url = f"http://localhost:{port}"
        webbrowser.open(url)
        
        print("✅ WB Dashboard запущен!")
        print(f"🌐 Приложение доступно по адресу: {url}")
        print("📝 Для остановки нажмите Ctrl+C")
        
        # Ждем завершения процесса
        try:
            process.wait()
        except KeyboardInterrupt:
            print("\n🛑 Остановка приложения...")
            process.terminate()

            process.wait()
            print("✅ Приложение остановлено")
            
    except Exception as e:
        print(f"❌ Ошибка запуска: {e}")
        input("Нажмите Enter для выхода...")

if __name__ == "__main__":
    main()
