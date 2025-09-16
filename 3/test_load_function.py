import pandas as pd
import sys
import os

# Добавляем текущую директорию в путь для импорта
sys.path.append('.')

# Импортируем функцию
from weekly_expenses_analyzer import load_expenses_data_from_df

def test_load_function():
    """Тестирует функцию load_expenses_data_from_df"""
    
    print("🔍 Тестирование функции load_expenses_data_from_df")
    
    # Загружаем исходный файл
    print("\n📁 Загружаем файл 4.xlsx...")
    df_original = pd.read_excel('4.xlsx')
    print(f"📊 Исходный размер: {df_original.shape}")
    
    # Показываем первые и последние даты исходного файла
    print(f"📅 Исходные даты:")
    print(f"  Первая дата начала: {df_original['Дата начала'].min()}")
    print(f"  Последняя дата конца: {df_original['Дата конца'].max()}")
    
    # Применяем функцию
    print("\n🔄 Применяем load_expenses_data_from_df...")
    df_processed = load_expenses_data_from_df(df_original)
    
    if df_processed is None:
        print("❌ Функция вернула None!")
        return
    
    print(f"📊 Обработанный размер: {df_processed.shape}")
    
    # Показываем результаты обработки
    print(f"📅 Обработанные даты:")
    print(f"  Первая дата начала: {df_processed['Дата начала'].min()}")
    print(f"  Последняя дата конца: {df_processed['Дата конца'].max()}")
    
    # Проверяем данные по годам
    records_2024 = len(df_processed[df_processed['Дата начала'].dt.year == 2024])
    records_2025 = len(df_processed[df_processed['Дата начала'].dt.year == 2025])
    
    print(f"📈 Данные по годам:")
    print(f"  2024 год: {records_2024} записей")
    print(f"  2025 год: {records_2025} записей")
    
    # Показываем несколько последних записей
    print(f"\n📋 Последние 5 записей:")
    last_records = df_processed.sort_values('Дата начала').tail(5)
    for i, (idx, row) in enumerate(last_records.iterrows(), 1):
        print(f"  {i}. {row['Дата начала']} - {row['Дата конца']} (год: {row['Дата начала'].year})")

if __name__ == "__main__":
    test_load_function()




