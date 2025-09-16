#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import pandas as pd

def test_data_structure():
    """Тестирует структуру данных в файле 3.xlsx"""
    try:
        # Загружаем данные
        df = pd.read_excel('3.xlsx')
        
        print("✅ Файл успешно загружен!")
        print(f"📊 Размер данных: {df.shape[0]} строк, {df.shape[1]} столбцов")
        print("\n📋 Столбцы в файле:")
        for i, col in enumerate(df.columns, 1):
            print(f"  {i}. {col}")
        
        print("\n🔍 Проверяем нужные столбцы:")
        required_columns = ['Дата начала', 'Дата конца', 'Итого к оплате']
        for col in required_columns:
            if col in df.columns:
                print(f"  ✅ {col} - найден")
            else:
                print(f"  ❌ {col} - НЕ НАЙДЕН")
        
        print("\n📅 Первые 3 строки с датами:")
        if 'Дата начала' in df.columns and 'Дата конца' in df.columns:
            print(df[['Дата начала', 'Дата конца']].head(3))
        
        print("\n💰 Финансовые данные:")
        financial_columns = ['Итого к оплате', 'Прочие удержания', 'Стоимость логистики', 
                           'Стоимость хранения', 'Стоимость возврата', 'Стоимость размещения']
        
        for col in financial_columns:
            if col in df.columns:
                total = df[col].sum()
                print(f"  {col}: {total:,.0f} ₽")
            else:
                print(f"  {col}: НЕ НАЙДЕН")
        
        print("\n📈 Общая сумма всех платежей:")
        total_payments = 0
        available_columns = []
        for col in financial_columns:
            if col in df.columns:
                total_payments += df[col].sum()
                available_columns.append(col)
        
        print(f"  Общая сумма: {total_payments:,.0f} ₽")
        print(f"  Включенные столбцы: {', '.join(available_columns)}")
        
    except Exception as e:
        print(f"❌ Ошибка: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_data_structure()
