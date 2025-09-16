#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from io import BytesIO
import warnings
warnings.filterwarnings('ignore')

# Настройка страницы
st.set_page_config(
    page_title="Анализатор еженедельных продаж WB",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Настройка стилей
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
        margin: 0.5rem 0;
    }
    .period-info {
        background-color: #e8f4fd;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #ff6b35;
        margin: 1rem 0;
    }
    .summary-box {
        background-color: #d4edda;
        padding: 1.5rem;
        border-radius: 0.5rem;
        border-left: 4px solid #28a745;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Заголовок приложения
st.markdown('<h1 class="main-header">📊 Анализатор еженедельных продаж Wildberries</h1>', unsafe_allow_html=True)

@st.cache_data
def load_sales_data(file_path='3.xlsx'):
    """Загружает данные о продажах из Excel файла"""
    try:
        df = pd.read_excel(file_path)
        
        # Преобразуем даты
        date_columns = ['Дата начала', 'Дата конца']
        for col in date_columns:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors='coerce')
        
        # Удаляем строки с пустыми датами
        df = df.dropna(subset=['Дата начала', 'Дата конца'])
        
        # Убеждаемся, что даты имеют правильный тип
        for col in date_columns:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors='coerce')
        
        # Сортируем по дате начала
        df = df.sort_values('Дата начала')
        
        return df
    except Exception as e:
        st.error(f"Ошибка при загрузке файла: {str(e)}")
        return None

def calculate_total_payments(df):
    """Рассчитывает общую сумму всех платежей"""
    payment_columns = [
        'Итого к оплате', 'Прочие удержания', 'Стоимость логистики', 
        'Стоимость хранения', 'Стоимость возврата', 'Стоимость размещения'
    ]
    
    total = 0
    available_columns = []
    
    for col in payment_columns:
        if col in df.columns:
            total += df[col].sum()
            available_columns.append(col)
    
    return total, available_columns

def main():
    # Загружаем данные
    df = load_sales_data()
    
    if df is None:
        st.error("Не удалось загрузить данные. Проверьте файл 3.xlsx")
        return
    
    # Показываем информацию о загруженных данных
    min_start = df['Дата начала'].min()
    max_end = df['Дата конца'].max()
    
    st.markdown(f"""
    <div class="period-info">
        <h3>📋 Информация о данных</h3>
        <p><strong>Всего отчетов:</strong> {len(df)}</p>
        <p><strong>Период:</strong> с {min_start.strftime('%d.%m.%Y') if pd.notna(min_start) else 'Н/Д'} по {max_end.strftime('%d.%m.%Y') if pd.notna(max_end) else 'Н/Д'}</p>
        <p><strong>Доступные столбцы:</strong> {', '.join(df.columns.tolist())}</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Фильтр дат
    st.markdown("### 📅 Фильтр по датам")
    
    min_date = df['Дата начала'].min()
    max_date = df['Дата конца'].max()
    
    col1, col2 = st.columns(2)
    
    with col1:
        start_date = st.date_input(
            "Дата начала периода",
            value=min_date.date(),
            min_value=min_date.date(),
            max_value=max_date.date()
        )
    
    with col2:
        end_date = st.date_input(
            "Дата конца периода",
            value=max_date.date(),
            min_value=min_date.date(),
            max_value=max_date.date()
        )
    
    # Применяем фильтр
    # Преобразуем start_date и end_date в datetime для корректного сравнения
    start_datetime = pd.to_datetime(start_date)
    end_datetime = pd.to_datetime(end_date)
    
    filtered_df = df[
        (df['Дата начала'] >= start_datetime) & 
        (df['Дата конца'] <= end_datetime)
    ]
    
    if filtered_df.empty:
        st.warning("⚠️ Нет данных для выбранного периода")
        return
    
    # Основные метрики
    st.markdown("### 💰 Основные финансовые показатели")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_to_pay = filtered_df['Итого к оплате'].sum() if 'Итого к оплате' in filtered_df.columns else 0
        st.markdown(f"""
        <div class="metric-card">
            <h4>Итого к оплате</h4>
            <h2>{total_to_pay:,.0f} ₽</h2>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        total_payments, payment_columns = calculate_total_payments(filtered_df)
        st.markdown(f"""
        <div class="metric-card">
            <h4>Общая сумма платежей</h4>
            <h2>{total_payments:,.0f} ₽</h2>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        avg_per_week = total_to_pay / len(filtered_df) if len(filtered_df) > 0 else 0
        st.markdown(f"""
        <div class="metric-card">
            <h4>Среднее за неделю</h4>
            <h2>{avg_per_week:,.0f} ₽</h2>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        weeks_count = len(filtered_df)
        st.markdown(f"""
        <div class="metric-card">
            <h4>Количество недель</h4>
            <h2>{weeks_count}</h2>
        </div>
        """, unsafe_allow_html=True)
    
    # Детальная таблица
    st.markdown("### 📊 Детальная таблица отчетов")
    
    # Подготавливаем данные для отображения
    display_df = filtered_df.copy()
    
    # Форматируем даты
    display_df['Дата начала'] = display_df['Дата начала'].apply(lambda x: x.strftime('%d.%m.%Y') if pd.notna(x) else 'Н/Д')
    display_df['Дата конца'] = display_df['Дата конца'].apply(lambda x: x.strftime('%d.%m.%Y') if pd.notna(x) else 'Н/Д')
    
    # Форматируем числовые столбцы
    numeric_columns = ['Итого к оплате', 'Прочие удержания', 'Стоимость логистики', 
                      'Стоимость хранения', 'Стоимость возврата', 'Стоимость размещения']
    
    for col in numeric_columns:
        if col in display_df.columns:
            display_df[col] = display_df[col].apply(lambda x: f"{x:,.0f} ₽" if pd.notna(x) else "0 ₽")
    
    st.dataframe(display_df, use_container_width=True)
    
    # Графики
    st.markdown("### 📈 Графики")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # График "Итого к оплате" по неделям
        if 'Итого к оплате' in filtered_df.columns:
            fig_payment = px.line(
                filtered_df, 
                x='Дата начала', 
                y='Итого к оплате',
                title='Итого к оплате по неделям',
                labels={'Дата начала': 'Дата', 'Итого к оплате': 'Сумма (₽)'}
            )
            fig_payment.update_layout(height=400)
            st.plotly_chart(fig_payment, use_container_width=True)
    
    with col2:
        # График общей суммы платежей
        if payment_columns:
            # Создаем сводную таблицу для всех платежей
            payment_data = []
            for _, row in filtered_df.iterrows():
                for col in payment_columns:
                    if pd.notna(row[col]):
                        payment_data.append({
                            'Дата': row['Дата начала'],
                            'Тип платежа': col,
                            'Сумма': row[col]
                        })
            
            if payment_data:
                payment_df = pd.DataFrame(payment_data)
                fig_total = px.bar(
                    payment_df.groupby('Тип платежа')['Сумма'].sum().reset_index(),
                    x='Тип платежа',
                    y='Сумма',
                    title='Общая сумма по типам платежей',
                    labels={'Сумма': 'Сумма (₽)', 'Тип платежа': 'Тип'}
                )
                fig_total.update_layout(height=400)
                fig_total.update_xaxes(tickangle=45)
                st.plotly_chart(fig_total, use_container_width=True)
    
    # Сводка
    st.markdown("### 📋 Сводка по выбранному периоду")
    
    st.markdown(f"""
    <div class="summary-box">
        <h3>📊 Итоги за период {start_date.strftime('%d.%m.%Y')} - {end_date.strftime('%d.%m.%Y')}</h3>
        <ul>
            <li><strong>Количество недель:</strong> {len(filtered_df)}</li>
            <li><strong>Итого к оплате:</strong> {total_to_pay:,.0f} ₽</li>
            <li><strong>Общая сумма всех платежей:</strong> {total_payments:,.0f} ₽</li>
            <li><strong>Среднее за неделю:</strong> {avg_per_week:,.0f} ₽</li>
        </ul>
        <p><strong>Включенные типы платежей:</strong> {', '.join(payment_columns)}</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Экспорт данных
    st.markdown("### 💾 Экспорт данных")
    
    if st.button("📥 Скачать отфильтрованные данные (Excel)"):
        # Создаем Excel файл
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            filtered_df.to_excel(writer, sheet_name='Отчет', index=False)
        
        output.seek(0)
        st.download_button(
            label="Скачать файл",
            data=output.getvalue(),
            file_name=f"wb_отчет_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

if __name__ == "__main__":
    main()
