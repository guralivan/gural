# -*- coding: utf-8 -*-
import os
import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
from io import BytesIO
import warnings
warnings.filterwarnings('ignore')

# Настройка страницы
st.set_page_config(
    page_title="Анализатор отчетов WB",
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
    }
    .chart-container {
        background-color: white;
        padding: 1rem;
        border-radius: 0.5rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .period-info {
        background-color: #e8f4fd;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #ff6b35;
    }
</style>
""", unsafe_allow_html=True)

# Заголовок приложения
st.markdown('<h1 class="main-header">📊 Анализатор отчетов Wildberries</h1>', unsafe_allow_html=True)

# Функции для работы с данными
@st.cache_data
def load_excel_file(file_path):
    """Загружает Excel файл и возвращает все листы"""
    try:
        excel_file = pd.ExcelFile(file_path)
        sheets = {}
        
        for sheet_name in excel_file.sheet_names:
            df = pd.read_excel(file_path, sheet_name=sheet_name)
            sheets[sheet_name] = df
            
        return sheets, excel_file.sheet_names
    except Exception as e:
        st.error(f"Ошибка при загрузке файла: {str(e)}")
        return None, []

def clean_wb_data(df):
    """Очищает и подготавливает данные отчетов WB"""
    df_clean = df.copy()
    
    # Преобразуем даты
    date_columns = ['Дата начала', 'Дата конца', 'Дата формирования']
    for col in date_columns:
        if col in df_clean.columns:
            df_clean[col] = pd.to_datetime(df_clean[col], errors='coerce', utc=True).dt.tz_convert(None)
    
    # Удаляем строки с пустыми датами
    df_clean = df_clean.dropna(subset=['Дата начала', 'Дата конца'])
    
    # Сортируем по дате начала
    df_clean = df_clean.sort_values('Дата начала')
    
    return df_clean

def calculate_period_metrics(df):
    """Рассчитывает метрики по периодам"""
    if df.empty:
        return {}
    
    metrics = {}
    
    # Основные финансовые показатели
    financial_columns = {
        'Итого к оплате': 'total_payment',
        'Прочие удержания': 'other_deductions', 
        'Стоимость логистики': 'logistics_cost',
        'Стоимость хранения': 'storage_cost'
    }
    
    for col, key in financial_columns.items():
        if col in df.columns:
            metrics[key] = {
                'total': df[col].sum(),
                'average': df[col].mean(),
                'max': df[col].max(),
                'min': df[col].min(),
                'count': df[col].count()
            }
    
    # Общая сумма всех показателей
    total_sum = 0
    for col in financial_columns.keys():
        if col in df.columns:
            total_sum += df[col].sum()
    metrics['total_all'] = total_sum
    
    # Период анализа
    if 'Дата начала' in df.columns and 'Дата конца' in df.columns:
        start_date = df['Дата начала'].min()
        end_date = df['Дата конца'].max()
        metrics['period'] = f"{start_date.strftime('%d.%m.%Y')} - {end_date.strftime('%d.%m.%Y')}"
        metrics['total_periods'] = len(df)
    
    # Анализ по месяцам
    if 'Дата начала' in df.columns:
        df['Месяц'] = df['Дата начала'].dt.to_period('M')
        monthly_data = df.groupby('Месяц').agg({
            'Итого к оплате': 'sum',
            'Прочие удержания': 'sum',
            'Стоимость логистики': 'sum',
            'Стоимость хранения': 'sum'
        }).reset_index()
        monthly_data['Месяц'] = monthly_data['Месяц'].astype(str)
        metrics['monthly_data'] = monthly_data
    
    return metrics

def create_period_summary(df):
    """Создает сводку по каждому периоду"""
    if df.empty:
        return pd.DataFrame()
    
    summary = df[['Дата начала', 'Дата конца', '№ отчета', 'Итого к оплате', 
                  'Прочие удержания', 'Стоимость логистики', 'Стоимость хранения']].copy()
    
    # Форматируем даты
    summary['Дата начала'] = summary['Дата начала'].dt.strftime('%d.%m.%Y')
    summary['Дата конца'] = summary['Дата конца'].dt.strftime('%d.%m.%Y')
    
    # Добавляем общую сумму по периоду
    summary['Общая сумма'] = (summary['Итого к оплате'] + summary['Прочие удержания'] + 
                             summary['Стоимость логистики'] + summary['Стоимость хранения'])
    
    return summary

# Основной интерфейс
st.sidebar.markdown("## ⚙️ Настройки")

# Выбор файла
uploaded_file = st.sidebar.file_uploader(
    "Выберите Excel файл с отчетами WB",
    type=['xlsx', 'xls'],
    help="Загрузите файл с отчетами Wildberries"
)

# Если файл не загружен, показываем инструкции
if uploaded_file is None:
    st.info("👆 Загрузите Excel файл с отчетами Wildberries в боковой панели")
    
    st.markdown("### 📋 Требования к файлу:")
    st.markdown("""
    - Файл должен содержать столбцы: **Дата начала**, **Дата конца**
    - Финансовые столбцы: **Итого к оплате**, **Прочие удержания**, **Стоимость логистики**, **Стоимость хранения**
    - Каждая строка - отдельный отчет за период
    - Поддерживаются форматы .xlsx и .xls
    """)
    
    # Показываем пример структуры данных
    st.markdown("### 📝 Пример структуры данных:")
    example_data = pd.DataFrame({
        '№ отчета': [250007587, 252210306],
        'Дата начала': ['2024-01-29', '2024-02-05'],
        'Дата конца': ['2024-02-04', '2024-02-11'],
        'Итого к оплате': [20889.11, 24812.18],
        'Прочие удержания': [1500.00, 1800.00],
        'Стоимость логистики': [2500.00, 2800.00],
        'Стоимость хранения': [500.00, 600.00]
    })
    st.dataframe(example_data, use_container_width=True)
    
else:
    # Загружаем данные
    with st.spinner("Загружаем данные..."):
        # Сохраняем временный файл
        temp_file_path = f"temp_{uploaded_file.name}"
        with open(temp_file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        # Загружаем Excel файл
        sheets, sheet_names = load_excel_file(temp_file_path)
        
        # Удаляем временный файл
        os.remove(temp_file_path)
    
    if sheets is None:
        st.error("Не удалось загрузить файл. Проверьте формат файла.")
    else:
        # Выбор листа
        if len(sheet_names) > 1:
            selected_sheet = st.sidebar.selectbox(
                "Выберите лист для анализа:",
                sheet_names,
                index=0
            )
        else:
            selected_sheet = sheet_names[0]
        
        df = sheets[selected_sheet]
        
        # Показываем информацию о данных
        st.sidebar.markdown("### 📊 Информация о данных")
        st.sidebar.write(f"**Размер данных:** {df.shape[0]} отчетов, {df.shape[1]} столбцов")
        st.sidebar.write(f"**Выбранный лист:** {selected_sheet}")
        
        # Проверяем наличие необходимых столбцов
        required_columns = ['Дата начала', 'Дата конца', 'Итого к оплате', 'Прочие удержания', 'Стоимость логистики', 'Стоимость хранения']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            st.error(f"❌ В файле отсутствуют необходимые столбцы: {', '.join(missing_columns)}")
            st.markdown("### 📋 Найденные столбцы:")
            st.write(df.columns.tolist())
        else:
            # Очищаем и подготавливаем данные
            df_clean = clean_wb_data(df)
            
            if not df_clean.empty:
                # Рассчитываем метрики
                metrics = calculate_period_metrics(df_clean)
                
                # Отображаем основные метрики
                st.markdown("### 📈 Основные показатели")
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric(
                        "Итого к оплате",
                        f"{metrics.get('total_payment', {}).get('total', 0):,.0f} ₽",
                        help="Общая сумма к оплате за все периоды"
                    )
                
                with col2:
                    st.metric(
                        "Прочие удержания",
                        f"{metrics.get('other_deductions', {}).get('total', 0):,.0f} ₽",
                        help="Общая сумма прочих удержаний"
                    )
                
                with col3:
                    st.metric(
                        "Стоимость логистики",
                        f"{metrics.get('logistics_cost', {}).get('total', 0):,.0f} ₽",
                        help="Общая стоимость логистики"
                    )
                
                with col4:
                    st.metric(
                        "Стоимость хранения",
                        f"{metrics.get('storage_cost', {}).get('total', 0):,.0f} ₽",
                        help="Общая стоимость хранения"
                    )
                
                # Общая сумма
                st.markdown("### 💰 Общая сумма всех показателей")
                st.markdown(f"""
                <div class="metric-card">
                    <h3>💰 {metrics.get('total_all', 0):,.0f} ₽</h3>
                    <p>Сумма всех финансовых показателей за период</p>
                </div>
                """, unsafe_allow_html=True)
                
                # Информация о периоде
                if 'period' in metrics:
                    st.markdown(f"""
                    <div class="period-info">
                        <h4>📅 Период анализа: {metrics['period']}</h4>
                        <p>Количество отчетов: {metrics.get('total_periods', 0)}</p>
                    </div>
                    """, unsafe_allow_html=True)
                
                # Графики
                st.markdown("### 📊 Графики анализа")
                
                # График по месяцам
                if 'monthly_data' in metrics:
                    monthly_df = metrics['monthly_data']
                    
                    fig_monthly = go.Figure()
                    
                    # Добавляем линии для каждого показателя
                    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728']
                    columns = ['Итого к оплате', 'Прочие удержания', 'Стоимость логистики', 'Стоимость хранения']
                    
                    for i, col in enumerate(columns):
                        if col in monthly_df.columns:
                            fig_monthly.add_trace(go.Scatter(
                                x=monthly_df['Месяц'],
                                y=monthly_df[col],
                                mode='lines+markers',
                                name=col,
                                line=dict(color=colors[i % len(colors)]),
                                hovertemplate=f'{col}: %{{y:,.0f}} ₽<extra></extra>'
                            ))
                    
                    fig_monthly.update_layout(
                        title="Динамика показателей по месяцам",
                        xaxis_title="Месяц",
                        yaxis_title="Сумма (₽)",
                        height=500,
                        hovermode='x unified'
                    )
                    
                    st.plotly_chart(fig_monthly, use_container_width=True)
                
                # Сводка по периодам
                st.markdown("### 📋 Сводка по периодам")
                period_summary = create_period_summary(df_clean)
                st.dataframe(period_summary, use_container_width=True)
                
                # Детальная статистика
                st.markdown("### 📊 Детальная статистика")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("#### Итого к оплате:")
                    payment_metrics = metrics.get('total_payment', {})
                    st.write(f"- **Общая сумма:** {payment_metrics.get('total', 0):,.0f} ₽")
                    st.write(f"- **Среднее значение:** {payment_metrics.get('average', 0):,.0f} ₽")
                    st.write(f"- **Максимум:** {payment_metrics.get('max', 0):,.0f} ₽")
                    st.write(f"- **Минимум:** {payment_metrics.get('min', 0):,.0f} ₽")
                
                with col2:
                    st.markdown("#### Прочие удержания:")
                    deduction_metrics = metrics.get('other_deductions', {})
                    st.write(f"- **Общая сумма:** {deduction_metrics.get('total', 0):,.0f} ₽")
                    st.write(f"- **Среднее значение:** {deduction_metrics.get('average', 0):,.0f} ₽")
                    st.write(f"- **Максимум:** {deduction_metrics.get('max', 0):,.0f} ₽")
                    st.write(f"- **Минимум:** {deduction_metrics.get('min', 0):,.0f} ₽")
                
                col3, col4 = st.columns(2)
                
                with col3:
                    st.markdown("#### Стоимость логистики:")
                    logistics_metrics = metrics.get('logistics_cost', {})
                    st.write(f"- **Общая сумма:** {logistics_metrics.get('total', 0):,.0f} ₽")
                    st.write(f"- **Среднее значение:** {logistics_metrics.get('average', 0):,.0f} ₽")
                    st.write(f"- **Максимум:** {logistics_metrics.get('max', 0):,.0f} ₽")
                    st.write(f"- **Минимум:** {logistics_metrics.get('min', 0):,.0f} ₽")
                
                with col4:
                    st.markdown("#### Стоимость хранения:")
                    storage_metrics = metrics.get('storage_cost', {})
                    st.write(f"- **Общая сумма:** {storage_metrics.get('total', 0):,.0f} ₽")
                    st.write(f"- **Среднее значение:** {storage_metrics.get('average', 0):,.0f} ₽")
                    st.write(f"- **Максимум:** {storage_metrics.get('max', 0):,.0f} ₽")
                    st.write(f"- **Минимум:** {storage_metrics.get('min', 0):,.0f} ₽")
                
                # Экспорт данных
                st.markdown("### 💾 Экспорт данных")
                
                # Подготовка данных для экспорта
                export_data = period_summary.copy()
                
                # CSV экспорт
                csv_data = export_data.to_csv(index=False, encoding='utf-8-sig')
                st.download_button(
                    label="📥 Скачать сводку в CSV",
                    data=csv_data,
                    file_name=f"wb_reports_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
                
                # Excel экспорт с метриками
                buffer = BytesIO()
                with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                    export_data.to_excel(writer, sheet_name='Сводка по периодам', index=False)
                    
                    # Добавляем лист с метриками
                    metrics_data = []
                    for key, value in metrics.items():
                        if isinstance(value, dict) and 'total' in value:
                            metrics_data.append({
                                'Показатель': key.replace('_', ' ').title(),
                                'Общая сумма': value['total'],
                                'Среднее значение': value['average'],
                                'Максимум': value['max'],
                                'Минимум': value['min']
                            })
                    
                    if metrics_data:
                        pd.DataFrame(metrics_data).to_excel(writer, sheet_name='Метрики', index=False)
                    
                    # Добавляем месячные данные
                    if 'monthly_data' in metrics:
                        metrics['monthly_data'].to_excel(writer, sheet_name='Данные по месяцам', index=False)
                
                buffer.seek(0)
                st.download_button(
                    label="📥 Скачать полный отчет в Excel",
                    data=buffer.getvalue(),
                    file_name=f"wb_reports_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
                
            else:
                st.error("После очистки данных не осталось записей для анализа. Проверьте формат дат.")

# Футер
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666;'>
    📊 Анализатор отчетов Wildberries | Создано для анализа финансовых показателей по периодам
</div>
""", unsafe_allow_html=True)
