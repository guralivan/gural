#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import pandas as pd

def test_data_loading():
    """Тестирует загрузку данных из файла 3.xlsx"""
    try:
        # Загружаем данные
        df = pd.read_excel('3.xlsx')
        
        # Преобразуем даты
        df['Дата начала'] = pd.to_datetime(df['Дата начала'], errors='coerce')
        df['Дата конца'] = pd.to_datetime(df['Дата конца'], errors='coerce')
        
        # Удаляем строки с пустыми датами
        df = df.dropna(subset=['Дата начала', 'Дата конца'])
        
        # Сортируем по дате начала
        df = df.sort_values('Дата начала')
        
        print("=== ТЕСТ ЗАГРУЗКИ ДАННЫХ ===")
        print(f"Общее количество записей: {len(df)}")
        print(f"Диапазон дат: с {df['Дата начала'].min()} по {df['Дата конца'].max()}")
        
        # Анализ по годам
        df['Год'] = df['Дата начала'].dt.year
        year_counts = df['Год'].value_counts().sort_index()
        
        print("\nКоличество записей по годам:")
        for year, count in year_counts.items():
            print(f"  {year}: {count} записей")
        
        # Проверяем наличие данных за 2025
        data_2025 = df[df['Год'] == 2025]
        print(f"\nДанные за 2025 год:")
        print(f"  Количество записей: {len(data_2025)}")
        if len(data_2025) > 0:
            print(f"  Первая запись: {data_2025['Дата начала'].min()}")
            print(f"  Последняя запись: {data_2025['Дата конца'].max()}")
        
        # Проверяем столбцы
        print(f"\nДоступные столбцы: {list(df.columns)}")
        
        return True
        
    except Exception as e:
        print(f"Ошибка при загрузке данных: {e}")
        return False

if __name__ == "__main__":
    test_data_loading()






