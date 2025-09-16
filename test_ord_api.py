#!/usr/bin/env python3
"""
Демонстрационный скрипт для тестирования API ОРД Яндекс
"""

import requests
import json
from datetime import datetime, date

# Конфигурация
API_BASE_URL = "https://ord-prestable.yandex.net/api/v6"
API_DOCS_URL = "https://ord-prestable.yandex.net/api/docs"

def test_api_connection():
    """Тест подключения к API"""
    print("🔍 Тестирование подключения к API ОРД Яндекс...")
    
    try:
        response = requests.get(f"{API_BASE_URL}/status")
        print(f"Статус ответа: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ API доступен")
            return True
        else:
            print(f"❌ API недоступен: {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Ошибка подключения: {e}")
        return False

def show_api_info():
    """Показать информацию об API"""
    print("\n📊 Информация об API ОРД Яндекс")
    print("=" * 50)
    print(f"Базовый URL: {API_BASE_URL}")
    print(f"Документация: {API_DOCS_URL}")
    print("\nДоступные эндпоинты:")
    
    endpoints = [
        ("POST /creative", "Создание креатива"),
        ("GET /creative", "Получение информации о креативе"),
        ("POST /organization", "Создание организации"),
        ("GET /organization", "Получение информации об организации"),
        ("POST /contract", "Создание контракта"),
        ("GET /contract", "Получение информации о контракте"),
        ("POST /invoice", "Создание акта"),
        ("GET /invoice", "Получение информации об акте"),
        ("POST /statistics", "Создание статистики"),
        ("GET /status", "Получение статуса API")
    ]
    
    for endpoint, description in endpoints:
        print(f"  {endpoint:<20} - {description}")

def show_sample_data():
    """Показать примеры данных для API"""
    print("\n📋 Примеры данных для API")
    print("=" * 50)
    
    # Пример организации
    print("\n🏢 Пример организации:")
    org_example = {
        "id": "test_org_001",
        "type": "ul",
        "name": "ООО Тестовая компания",
        "inn": "1234567890",
        "kpp": "123456789",
        "isOrs": False,
        "isRr": True
    }
    print(json.dumps(org_example, indent=2, ensure_ascii=False))
    
    # Пример креатива
    print("\n🎨 Пример креатива:")
    creative_example = {
        "id": "test_creative_001",
        "type": "banner",
        "description": "Реклама товаров для дома",
        "urls": ["https://example.com/product1", "https://example.com/product2"],
        "textData": [{"text": "Скидки до 50% на товары для дома!"}],
        "mediaData": [{
            "mediaUrl": "https://example.com/banner.jpg",
            "mediaUrlFileType": "image"
        }],
        "targeting": {
            "regions": ["77", "78"],
            "sexes": ["male", "female"],
            "ages": ["25:45"]
        }
    }
    print(json.dumps(creative_example, indent=2, ensure_ascii=False))
    
    # Пример контракта
    print("\n📋 Пример контракта:")
    contract_example = {
        "id": "test_contract_001",
        "type": "contract",
        "clientId": "test_org_001",
        "contractorId": "test_org_002",
        "clientRole": "rd",
        "contractorRole": "ra",
        "startDate": "2024-01-01",
        "endDate": "2024-12-31",
        "amount": {
            "excludingVat": "100000.00",
            "vatRate": "20.00",
            "vat": "20000.00",
            "includingVat": "120000.00"
        }
    }
    print(json.dumps(contract_example, indent=2, ensure_ascii=False))

def show_validation_rules():
    """Показать правила валидации"""
    print("\n⚠️ Правила валидации данных")
    print("=" * 50)
    
    rules = [
        "ИНН: 10 цифр для юр.лиц, 12 цифр для физ.лиц и ИП",
        "КПП: 9 цифр, только для российских юр.лиц",
        "Даты: формат YYYY-MM-DD",
        "Суммы: максимум 2 знака после запятой",
        "Текст креатива: максимум 65,000 символов",
        "ID объектов: только латинские буквы, цифры, дефисы и подчеркивания",
        "URL: должны быть валидными ссылками"
    ]
    
    for rule in rules:
        print(f"  • {rule}")

def main():
    """Основная функция"""
    print("🚀 Демонстрационный скрипт для API ОРД Яндекс")
    print("=" * 60)
    
    # Тест подключения
    if test_api_connection():
        print("\n✅ API доступен для работы")
    else:
        print("\n❌ API недоступен. Проверьте подключение к интернету.")
    
    # Показать информацию об API
    show_api_info()
    
    # Показать примеры данных
    show_sample_data()
    
    # Показать правила валидации
    show_validation_rules()
    
    print("\n" + "=" * 60)
    print("📖 Для получения токена API посетите:")
    print(f"   {API_DOCS_URL}")
    print("\n🎯 Для запуска веб-приложения используйте:")
    print("   ./launch_ord_app.command (базовая версия)")
    print("   ./launch_ord_app_full.command (полная версия)")

if __name__ == "__main__":
    main()
