#!/usr/bin/env python3
"""
Скрипт для создания примера рекламодателя
"""

import json
import os

# Пример данных рекламодателя
sample_advertiser = {
    "company_name": "ООО «ПРИМЕР РЕКЛАМЫ»",
    "inn": "1234567890",
    "ogrn": "1234567890123",
    "okpo": "12345678",
    "kpp": "123456789",
    "legal_address": "г. Москва, ул. Примерная, д. 1, оф. 100",
    "actual_address": "г. Москва, ул. Примерная, д. 1, оф. 100",
    "director": "Иванов Иван Иванович",
    "director_birth": "01.01.1990",
    "email": "info@example-reklama.ru",
    "account": "40702810110000000000",
    "bank": "АО «ПРИМЕР БАНК»",
    "bank_address": "г. Москва, ул. Банковская, д. 1",
    "corr_account": "30101810100000000000",
    "bank_inn": "1234567890",
    "bank_bik": "044525000",
    "foundation": "Устав",
    "contract_amount": "75000",
    "reach": "15000",
    "posts_count": "2",
    "placement_period": "14"
}

def create_sample_data():
    """Создает файл с примером рекламодателя"""
    
    # Проверяем, существует ли уже файл с данными
    if os.path.exists('advertisers_data.json'):
        with open('advertisers_data.json', 'r', encoding='utf-8') as f:
            existing_data = json.load(f)
    else:
        existing_data = {}
    
    # Добавляем пример, если его еще нет
    if sample_advertiser['company_name'] not in existing_data:
        existing_data[sample_advertiser['company_name']] = sample_advertiser
        
        with open('advertisers_data.json', 'w', encoding='utf-8') as f:
            json.dump(existing_data, f, ensure_ascii=False, indent=2)
        
        print("✅ Создан пример рекламодателя: ООО «ПРИМЕР РЕКЛАМЫ»")
        print("📄 Теперь вы можете использовать эти данные в приложении")
    else:
        print("ℹ️ Пример рекламодателя уже существует")

if __name__ == "__main__":
    create_sample_data()

