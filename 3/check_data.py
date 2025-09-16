#!/usr/bin/env python3
import pandas as pd

def check_data():
    print("Проверка данных для второй вкладки:")
    
    # Загружаем данные
    df = pd.read_excel('3.xlsx')
    print(f"Всего записей: {len(df)}")
    
    # Преобразуем даты
    df['Дата начала'] = pd.to_datetime(df['Дата начала'])
    df['Дата конца'] = pd.to_datetime(df['Дата конца'])
    
    # Очищаем данные
    df_clean = df.dropna(subset=['Дата начала', 'Дата конца'])
    print(f"После очистки: {len(df_clean)}")
    
    # Анализируем по годам
    year_counts = df_clean['Дата начала'].dt.year.value_counts().sort_index()
    print("По годам:")
    for year, count in year_counts.items():
        print(f"  {year}: {count} записей")
    
    # Проверяем данные за 2025
    data_2025 = df_clean[df_clean['Дата начала'].dt.year == 2025]
    print(f"Данные 2025: {len(data_2025)} записей")
    
    if len(data_2025) > 0:
        print(f"Период 2025: {data_2025['Дата начала'].min()} - {data_2025['Дата конца'].max()}")
        print("Первые 3 записи 2025:")
        print(data_2025[['Дата начала', 'Дата конца', 'Итого к оплате']].head(3))
    else:
        print("Данные за 2025 год не найдены!")

if __name__ == "__main__":
    check_data()






