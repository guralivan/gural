# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# Настройка страницы
st.set_page_config(
    page_title="Анализатор WB",
    page_icon="📊",
    layout="wide"
)

st.title("📊 Анализатор отчетов Wildberries")

# Функция для обработки данных
def process_data(df):
    """Простая обработка данных"""
    try:
        # Копируем данные
        df_clean = df.copy()
        
        # Обрабатываем даты
        df_clean['Дата начала'] = pd.to_datetime(df_clean['Дата начала'], errors='coerce')
        df_clean['Дата конца'] = pd.to_datetime(df_clean['Дата конца'], errors='coerce')
        
        # Удаляем строки с пустыми датами
        df_clean = df_clean.dropna(subset=['Дата начала', 'Дата конца'])
        
        # Обрабатываем числовые столбцы
        numeric_cols = ['Итого к оплате', 'Прочие удержания', 'Стоимость логистики', 'Стоимость хранения']
        for col in numeric_cols:
            if col in df_clean.columns:
                df_clean[col] = pd.to_numeric(df_clean[col], errors='coerce').fillna(0)
        
        return df_clean
    except Exception as e:
        st.error(f"Ошибка обработки: {e}")
        return None

# Основной интерфейс
st.sidebar.markdown("## ⚙️ Настройки")

# Загрузка файла
uploaded_file = st.sidebar.file_uploader(
    "Выберите Excel файл",
    type=['xlsx', 'xls']
)

if uploaded_file is None:
    st.info("👆 Загрузите Excel файл с отчетами Wildberries")
    st.markdown("""
    **Требуемые столбцы:**
    - Дата начала, Дата конца
    - Итого к оплате, Прочие удержания
    - Стоимость логистики, Стоимость хранения
    """)
else:
    try:
        # Загружаем данные
        df = pd.read_excel(uploaded_file)
        st.success(f"✅ Загружено: {df.shape[0]} строк")
        
        # Проверяем столбцы
        required = ['Дата начала', 'Дата конца', 'Итого к оплате', 'Прочие удержания', 'Стоимость логистики', 'Стоимость хранения']
        missing = [col for col in required if col not in df.columns]
        
        if missing:
            st.error(f"❌ Отсутствуют: {', '.join(missing)}")
            st.write("**Найденные столбцы:**")
            for col in df.columns:
                st.write(f"- {col}")
        else:
            st.success("✅ Все столбцы найдены")
            
            # Обрабатываем данные
            df_clean = process_data(df)
            
            if df_clean is not None and not df_clean.empty:
                st.success(f"✅ Обработано: {len(df_clean)} записей")
                
                # Рассчитываем суммы
                total_payment = df_clean['Итого к оплате'].sum()
                total_deductions = df_clean['Прочие удержания'].sum()
                total_logistics = df_clean['Стоимость логистики'].sum()
                total_storage = df_clean['Стоимость хранения'].sum()
                total_all = total_payment + total_deductions + total_logistics + total_storage
                
                # Показываем результаты
                st.markdown("## 📊 Результаты анализа")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("### 💰 Финансовые показатели")
                    st.write(f"**Итого к оплате:** {total_payment:,.0f} ₽")
                    st.write(f"**Прочие удержания:** {total_deductions:,.0f} ₽")
                    st.write(f"**Стоимость логистики:** {total_logistics:,.0f} ₽")
                    st.write(f"**Стоимость хранения:** {total_storage:,.0f} ₽")
                    
                    st.markdown("---")
                    st.markdown(f"### 💎 **ОБЩАЯ СУММА: {total_all:,.0f} ₽**")
                
                with col2:
                    st.markdown("### 📅 Период анализа")
                    start_date = df_clean['Дата начала'].min()
                    end_date = df_clean['Дата конца'].max()
                    st.write(f"**Начало:** {start_date.strftime('%d.%m.%Y')}")
                    st.write(f"**Конец:** {end_date.strftime('%d.%m.%Y')}")
                    st.write(f"**Количество отчетов:** {len(df_clean)}")
                    
                    # Средние значения
                    st.markdown("### 📈 Средние значения")
                    st.write(f"**Среднее к оплате:** {total_payment/len(df_clean):,.0f} ₽")
                    st.write(f"**Средние удержания:** {total_deductions/len(df_clean):,.0f} ₽")
                    st.write(f"**Средняя логистика:** {total_logistics/len(df_clean):,.0f} ₽")
                    st.write(f"**Среднее хранение:** {total_storage/len(df_clean):,.0f} ₽")
                
                # Сводка по периодам
                st.markdown("## 📋 Сводка по периодам")
                
                # Создаем простую сводку
                summary = df_clean[['Дата начала', 'Дата конца', 'Итого к оплате', 'Прочие удержания', 'Стоимость логистики', 'Стоимость хранения']].copy()
                
                # Форматируем даты
                summary['Дата начала'] = summary['Дата начала'].dt.strftime('%d.%m.%Y')
                summary['Дата конца'] = summary['Дата конца'].dt.strftime('%d.%m.%Y')
                
                # Добавляем общую сумму
                summary['Общая сумма'] = summary['Итого к оплате'] + summary['Прочие удержания'] + summary['Стоимость логистики'] + summary['Стоимость хранения']
                
                # Показываем таблицу
                st.dataframe(summary, use_container_width=True)
                
                # Экспорт
                st.markdown("## 💾 Экспорт")
                csv_data = summary.to_csv(index=False, encoding='utf-8-sig')
                st.download_button(
                    label="📥 Скачать CSV",
                    data=csv_data,
                    file_name=f"wb_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
                
            else:
                st.error("❌ Нет данных для анализа")
                
    except Exception as e:
        st.error(f"❌ Ошибка: {e}")

# Футер
st.markdown("---")
st.markdown("*📊 Простой анализатор отчетов Wildberries*")




























