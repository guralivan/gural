import pandas as pd
import os

def check_which_file():
    """Проверяет, какой файл загружается в приложении"""
    
    files_to_check = ['3.xlsx', '4.xlsx']
    
    for filename in files_to_check:
        if os.path.exists(filename):
            print(f"\n📁 Проверяем файл: {filename}")
            try:
                df = pd.read_excel(filename)
                
                # Преобразуем даты
                df['Дата начала'] = pd.to_datetime(df['Дата начала'], errors='coerce')
                df['Дата конца'] = pd.to_datetime(df['Дата конца'], errors='coerce')
                
                # Удаляем строки с пустыми датами
                df_clean = df.dropna(subset=['Дата начала', 'Дата конца'])
                
                # Проверяем данные по годам
                records_2024 = len(df_clean[df_clean['Дата начала'].dt.year == 2024])
                records_2025 = len(df_clean[df_clean['Дата начала'].dt.year == 2025])
                
                min_date = df_clean['Дата начала'].min()
                max_date = df_clean['Дата конца'].max()
                
                print(f"📊 Общее количество строк: {len(df_clean)}")
                print(f"📅 Диапазон дат: с {min_date.strftime('%d.%m.%Y')} по {max_date.strftime('%d.%m.%Y')}")
                print(f"📈 2024 год: {records_2024} записей")
                print(f"📈 2025 год: {records_2025} записей")
                
                # Проверяем юридическое лицо
                if 'Юридическое лицо' in df_clean.columns:
                    legal_entities = df_clean['Юридическое лицо'].unique()
                    print(f"🏢 Юридические лица: {legal_entities}")
                
            except Exception as e:
                print(f"❌ Ошибка при чтении файла: {e}")
        else:
            print(f"❌ Файл {filename} не найден")

if __name__ == "__main__":
    check_which_file()

