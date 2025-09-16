import pandas as pd
import os

def check_legal_entity():
    """Проверяет название юридического лица в файле"""
    try:
        filename = '3_combined_2024_2025.xlsx'
        
        if not os.path.exists(filename):
            print(f"❌ Файл {filename} не найден!")
            return
        
        print(f"📁 Загружаем файл {filename}...")
        df = pd.read_excel(filename)
        
        # Проверяем колонку с юридическим лицом
        if 'Юридическое лицо' in df.columns:
            legal_entities = df['Юридическое лицо'].unique()
            print(f"🏢 Юридические лица в файле: {legal_entities}")
            
            # Показываем количество записей для каждого ЮЛ
            for entity in legal_entities:
                entity_data = df[df['Юридическое лицо'] == entity]
                print(f"📊 {entity}: {len(entity_data)} записей")
                
                # Проверяем даты для этого ЮЛ
                if 'Дата начала' in entity_data.columns:
                    entity_data['Дата начала'] = pd.to_datetime(entity_data['Дата начала'], errors='coerce')
                    entity_data['Дата конца'] = pd.to_datetime(entity_data['Дата конца'], errors='coerce')
                    
                    entity_data_clean = entity_data.dropna(subset=['Дата начала', 'Дата конца'])
                    
                    records_2024 = len(entity_data_clean[entity_data_clean['Дата начала'].dt.year == 2024])
                    records_2025 = len(entity_data_clean[entity_data_clean['Дата начала'].dt.year == 2025])
                    
                    min_date = entity_data_clean['Дата начала'].min()
                    max_date = entity_data_clean['Дата конца'].max()
                    
                    print(f"   📅 Период: с {min_date.strftime('%d.%m.%Y')} по {max_date.strftime('%d.%m.%Y')}")
                    print(f"   📈 2024 год: {records_2024} записей")
                    print(f"   📈 2025 год: {records_2025} записей")
        else:
            print("❌ Колонка 'Юридическое лицо' не найдена!")
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        print(f"Детали: {traceback.format_exc()}")

if __name__ == "__main__":
    check_legal_entity()
