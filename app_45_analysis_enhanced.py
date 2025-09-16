# -*- coding: utf-8 -*-
import os
import json
import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import calendar
from io import BytesIO

# Настройка страницы
st.set_page_config(
    page_title="Анализ отчетов WB - 45.xlsx",
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
        margin-bottom: 1rem;
    }
    .sidebar-header {
        font-size: 1.2rem;
        font-weight: bold;
        color: #1f77b4;
        margin-bottom: 1rem;
    }
    .success-box {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        border-radius: 0.5rem;
        padding: 1rem;
        margin: 1rem 0;
    }
    .warning-box {
        background-color: #fff3cd;
        border: 1px solid #ffeaa7;
        border-radius: 0.5rem;
        padding: 1rem;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# ================= ФУНКЦИИ ДЛЯ РАБОТЫ С ДАННЫМИ =================

@st.cache_data
def load_45_data():
    """Загружает данные из файла 45.xlsx"""
    try:
        df = pd.read_excel('45.xlsx', sheet_name='Товары', header=1)
        # Преобразуем дату
        df['Дата'] = pd.to_datetime(df['Дата'])
        
        # Преобразуем числовые столбцы
        numeric_columns = [
            'Переходы в карточку', 'Положили в корзину', 'Добавили в отложенные',
            'Заказали, шт', 'Заказали ВБ клуб, шт', 'Выкупили, шт', 'Выкупили ВБ клуб, шт',
            'Отменили, шт', 'Отменили ВБ клуб, шт', 'Конверсия в корзину, %',
            'Конверсия в заказ, %', 'Процент выкупа', 'Процент выкупа ВБ клуб',
            'Заказали на сумму, ₽', 'Заказали на сумму ВБ клуб, ₽',
            'Выкупили на сумму, ₽', 'Выкупили на сумму ВБ клуб, ₽',
            'Отменили на сумму, ₽', 'Отменили на сумму ВБ клуб, ₽'
        ]
        
        for col in numeric_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Добавляем дополнительные расчеты
        df['Доходность'] = df['Выкупили на сумму, ₽'] - df['Заказали на сумму, ₽']
        df['Эффективность'] = df['Выкупили, шт'] / df['Переходы в карточку'] * 100
        
        return df
    except Exception as e:
        st.error(f"Ошибка загрузки данных: {e}")
        return None

@st.cache_data
def load_uploaded_data(file_bytes: bytes, filename: str):
    """Загружает данные из загруженного файла"""
    try:
        if filename.lower().endswith(('.xlsx', '.xls')):
            df = pd.read_excel(BytesIO(file_bytes), sheet_name=0, header=None)
        else:
            df = pd.read_csv(BytesIO(file_bytes), header=None, sep=None, engine='python')
        
        # Ищем строку с заголовками
        header_row = None
        for i in range(min(10, len(df))):
            row_str = ' '.join(df.iloc[i].astype(str))
            if 'артикул' in row_str.lower() and 'дата' in row_str.lower():
                header_row = i
                break
        
        if header_row is not None:
            df = pd.read_excel(BytesIO(file_bytes), sheet_name=0, header=header_row)
        else:
            df = pd.read_excel(BytesIO(file_bytes), sheet_name=0, header=1)
        
        # Преобразуем дату
        if 'Дата' in df.columns:
            df['Дата'] = pd.to_datetime(df['Дата'])
        
        return df
    except Exception as e:
        st.error(f"Ошибка загрузки файла: {e}")
        return None

def save_to_cache(df, filename):
    """Сохраняет данные в кеш"""
    cache_file = f"cache_{filename.replace('.', '_')}.json"
    try:
        cache_data = {
            'columns': df.columns.tolist(),
            'data': df.to_dict('records'),
            'timestamp': datetime.now().isoformat()
        }
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(cache_data, f, ensure_ascii=False, indent=2, default=str)
        return True
    except Exception as e:
        st.error(f"Ошибка сохранения в кеш: {e}")
        return False

def load_from_cache(filename):
    """Загружает данные из кеша"""
    cache_file = f"cache_{filename.replace('.', '_')}.json"
    try:
        if os.path.exists(cache_file):
            with open(cache_file, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
            df = pd.DataFrame(cache_data['data'])
            return df
    except Exception:
        pass
    return None

# ================= ФУНКЦИИ ДЛЯ АНАЛИЗА =================

def calculate_kpis(df):
    """Рассчитывает основные KPI"""
    if df is None or df.empty:
        return {}
    
    kpis = {}
    
    # Общие метрики
    kpis['total_orders'] = df['Заказали, шт'].sum()
    kpis['total_sales'] = df['Выкупили, шт'].sum()
    kpis['total_revenue'] = df['Выкупили на сумму, ₽'].sum()
    kpis['total_views'] = df['Переходы в карточку'].sum()
    kpis['total_cart_adds'] = df['Положили в корзину'].sum()
    
    # Конверсии
    kpis['conversion_rate'] = (df['Выкупили, шт'].sum() / df['Заказали, шт'].sum() * 100) if df['Заказали, шт'].sum() > 0 else 0
    kpis['cart_conversion'] = (df['Положили в корзину'].sum() / df['Переходы в карточку'].sum() * 100) if df['Переходы в карточку'].sum() > 0 else 0
    kpis['order_conversion'] = (df['Заказали, шт'].sum() / df['Положили в корзину'].sum() * 100) if df['Положили в корзину'].sum() > 0 else 0
    
    # Средние значения
    kpis['avg_orders_per_day'] = df.groupby('Дата')['Заказали, шт'].sum().mean()
    kpis['avg_sales_per_day'] = df.groupby('Дата')['Выкупили, шт'].sum().mean()
    kpis['avg_revenue_per_day'] = df.groupby('Дата')['Выкупили на сумму, ₽'].sum().mean()
    kpis['avg_revenue_per_order'] = df['Выкупили на сумму, ₽'].sum() / df['Выкупили, шт'].sum() if df['Выкупили, шт'].sum() > 0 else 0
    
    # Дополнительные метрики
    if 'Доходность' in df.columns:
        kpis['total_profit'] = df['Доходность'].sum()
        kpis['avg_profit_per_order'] = df['Доходность'].sum() / df['Выкупили, шт'].sum() if df['Выкупили, шт'].sum() > 0 else 0
    
    return kpis

def aggregate_by_period(df, period='D'):
    """Агрегирует данные по периоду (D - день, W - неделя, M - месяц)"""
    if df is None or df.empty:
        return pd.DataFrame()
    
    agg_data = df.groupby(pd.Grouper(key='Дата', freq=period)).agg({
        'Заказали, шт': 'sum',
        'Выкупили, шт': 'sum',
        'Заказали на сумму, ₽': 'sum',
        'Выкупили на сумму, ₽': 'sum',
        'Переходы в карточку': 'sum',
        'Положили в корзину': 'sum',
        'Отменили, шт': 'sum',
        'Отменили на сумму, ₽': 'sum'
    }).reset_index()
    
    # Рассчитываем конверсию
    agg_data['Конверсия в заказ, %'] = (agg_data['Заказали, шт'] / agg_data['Переходы в карточку'] * 100).fillna(0)
    agg_data['Процент выкупа'] = (agg_data['Выкупили, шт'] / agg_data['Заказали, шт'] * 100).fillna(0)
    agg_data['Конверсия в корзину, %'] = (agg_data['Положили в корзину'] / agg_data['Переходы в карточку'] * 100).fillna(0)
    
    # Добавляем доходность если есть
    if 'Доходность' in df.columns:
        agg_data['Доходность'] = agg_data['Выкупили на сумму, ₽'] - agg_data['Заказали на сумму, ₽']
    
    return agg_data

def compare_periods(df, current_period, previous_period):
    """Сравнивает два периода"""
    if df is None or df.empty:
        return {}
    
    current_data = df[df['Дата'].between(current_period[0], current_period[1])]
    previous_data = df[df['Дата'].between(previous_period[0], previous_period[1])]
    
    comparison = {}
    
    metrics = ['Заказали, шт', 'Выкупили, шт', 'Выкупили на сумму, ₽', 'Переходы в карточку', 'Положили в корзину']
    
    for metric in metrics:
        if metric in df.columns:
            current_val = current_data[metric].sum()
            previous_val = previous_data[metric].sum()
            
            if previous_val > 0:
                change_pct = ((current_val - previous_val) / previous_val) * 100
            else:
                change_pct = 0
            
            comparison[metric] = {
                'current': current_val,
                'previous': previous_val,
                'change_pct': change_pct
            }
    
    return comparison

def analyze_seasonality(df):
    """Анализ сезонности"""
    if df is None or df.empty:
        return {}
    
    # Анализ по дням недели
    df['День недели'] = df['Дата'].dt.day_name()
    df['Месяц'] = df['Дата'].dt.month_name()
    df['Неделя'] = df['Дата'].dt.isocalendar().week
    
    # Статистика по дням недели
    weekday_stats = df.groupby('День недели').agg({
        'Заказали, шт': 'sum',
        'Выкупили, шт': 'sum',
        'Выкупили на сумму, ₽': 'sum'
    }).reset_index()
    
    # Статистика по месяцам
    month_stats = df.groupby('Месяц').agg({
        'Заказали, шт': 'sum',
        'Выкупили, шт': 'sum',
        'Выкупили на сумму, ₽': 'sum'
    }).reset_index()
    
    return {
        'weekday': weekday_stats,
        'month': month_stats
    }

# ================= ФУНКЦИИ ДЛЯ ВИЗУАЛИЗАЦИИ =================

def plot_orders_trend(df, period='D'):
    """График тренда заказов"""
    if df is None or df.empty:
        return go.Figure()
    
    agg_data = aggregate_by_period(df, period)
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=agg_data['Дата'],
        y=agg_data['Заказали, шт'],
        mode='lines+markers',
        name='Заказы',
        line=dict(color='#1f77b4', width=2),
        marker=dict(size=6)
    ))
    
    fig.add_trace(go.Scatter(
        x=agg_data['Дата'],
        y=agg_data['Выкупили, шт'],
        mode='lines+markers',
        name='Выкупы',
        line=dict(color='#2ca02c', width=2),
        marker=dict(size=6)
    ))
    
    fig.add_trace(go.Scatter(
        x=agg_data['Дата'],
        y=agg_data['Отменили, шт'],
        mode='lines+markers',
        name='Отмены',
        line=dict(color='#d62728', width=2),
        marker=dict(size=6)
    ))
    
    fig.update_layout(
        title=f'Тренд заказов, выкупов и отмен по {period}',
        xaxis_title='Дата',
        yaxis_title='Количество',
        hovermode='x unified',
        height=400
    )
    
    return fig

def plot_conversion_funnel(df, period='D'):
    """Воронка конверсии"""
    if df is None or df.empty:
        return go.Figure()
    
    agg_data = aggregate_by_period(df, period)
    
    fig = go.Figure(go.Funnel(
        y=['Переходы', 'В корзину', 'Заказы', 'Выкупы'],
        x=[
            agg_data['Переходы в карточку'].sum(),
            agg_data['Положили в корзину'].sum(),
            agg_data['Заказали, шт'].sum(),
            agg_data['Выкупили, шт'].sum()
        ],
        textinfo="value+percent initial",
        marker=dict(color=['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728'])
    ))
    
    fig.update_layout(
        title='Воронка конверсии',
        height=400
    )
    
    return fig

def plot_revenue_trend(df, period='D'):
    """График выручки"""
    if df is None or df.empty:
        return go.Figure()
    
    agg_data = aggregate_by_period(df, period)
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=agg_data['Дата'],
        y=agg_data['Выкупили на сумму, ₽'],
        mode='lines+markers',
        name='Выручка',
        line=dict(color='#ff7f0e', width=2),
        marker=dict(size=6),
        fill='tonexty'
    ))
    
    if 'Доходность' in agg_data.columns:
        fig.add_trace(go.Scatter(
            x=agg_data['Дата'],
            y=agg_data['Доходность'],
            mode='lines+markers',
            name='Доходность',
            line=dict(color='#9467bd', width=2),
            marker=dict(size=6)
        ))
    
    fig.update_layout(
        title=f'Тренд выручки по {period}',
        xaxis_title='Дата',
        yaxis_title='Сумма, ₽',
        hovermode='x unified',
        height=400
    )
    
    return fig

def plot_product_performance(df):
    """Производительность по товарам"""
    if df is None or df.empty:
        return go.Figure()
    
    product_stats = df.groupby('Артикул продавца').agg({
        'Заказали, шт': 'sum',
        'Выкупили, шт': 'sum',
        'Выкупили на сумму, ₽': 'sum',
        'Процент выкупа': 'mean',
        'Переходы в карточку': 'sum'
    }).reset_index()
    
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=('Заказы по товарам', 'Выкупы по товарам', 'Выручка по товарам', 'Конверсия'),
        specs=[[{"type": "bar"}, {"type": "bar"}],
               [{"type": "bar"}, {"type": "bar"}]]
    )
    
    fig.add_trace(
        go.Bar(x=product_stats['Артикул продавца'], y=product_stats['Заказали, шт'], name='Заказы'),
        row=1, col=1
    )
    
    fig.add_trace(
        go.Bar(x=product_stats['Артикул продавца'], y=product_stats['Выкупили, шт'], name='Выкупы'),
        row=1, col=2
    )
    
    fig.add_trace(
        go.Bar(x=product_stats['Артикул продавца'], y=product_stats['Выкупили на сумму, ₽'], name='Выручка'),
        row=2, col=1
    )
    
    fig.add_trace(
        go.Bar(x=product_stats['Артикул продавца'], y=product_stats['Процент выкупа'], name='% выкупа'),
        row=2, col=2
    )
    
    fig.update_layout(height=600, showlegend=False)
    
    return fig

def plot_seasonality(df):
    """График сезонности"""
    if df is None or df.empty:
        return go.Figure(), go.Figure()
    
    seasonality = analyze_seasonality(df)
    
    # График по дням недели
    fig1 = px.bar(
        seasonality['weekday'],
        x='День недели',
        y=['Заказали, шт', 'Выкупили, шт'],
        title='Активность по дням недели',
        barmode='group'
    )
    
    # График по месяцам
    fig2 = px.bar(
        seasonality['month'],
        x='Месяц',
        y=['Заказали, шт', 'Выкупили, шт'],
        title='Активность по месяцам',
        barmode='group'
    )
    
    return fig1, fig2

# ================= ОСНОВНОЕ ПРИЛОЖЕНИЕ =================

def main():
    st.markdown('<h1 class="main-header">📊 Анализ отчетов WB</h1>', unsafe_allow_html=True)
    
    # Боковая панель
    st.sidebar.markdown('<h3 class="sidebar-header">Загрузка данных</h3>', unsafe_allow_html=True)
    
    # Загрузка файла 45.xlsx
    if st.sidebar.button("📁 Загрузить данные из 45.xlsx"):
        st.session_state['data_source'] = '45.xlsx'
        st.sidebar.success("✅ Данные из 45.xlsx загружены!")
    
    # Загрузка дополнительных отчетов
    uploaded_file = st.sidebar.file_uploader(
        "📤 Загрузить дополнительный отчет",
        type=['xlsx', 'xls', 'csv'],
        help="Загрузите Excel или CSV файл с данными WB"
    )
    
    if uploaded_file is not None:
        st.session_state['uploaded_data'] = load_uploaded_data(uploaded_file.read(), uploaded_file.name)
        if st.session_state['uploaded_data'] is not None:
            st.sidebar.success(f"✅ Файл {uploaded_file.name} загружен успешно!")
            if st.sidebar.button("💾 Сохранить в кеш"):
                if save_to_cache(st.session_state['uploaded_data'], uploaded_file.name):
                    st.sidebar.success("✅ Данные сохранены в кеш!")
    
    # Выбор источника данных
    cache_files = [f for f in os.listdir('.') if f.startswith('cache_')]
    data_source = st.sidebar.selectbox(
        "📊 Источник данных",
        options=['45.xlsx'] + cache_files,
        key='data_source'
    )
    
    # Загрузка данных
    if data_source == '45.xlsx':
        df = load_45_data()
    else:
        df = load_from_cache(data_source.replace('cache_', '').replace('.json', ''))
    
    if df is None or df.empty:
        st.warning("⚠️ Данные не загружены. Загрузите файл 45.xlsx или дополнительный отчет.")
        return
    
    # Информация о данных
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📋 Информация о данных")
    st.sidebar.write(f"**Записей:** {len(df):,}")
    st.sidebar.write(f"**Товаров:** {df['Артикул продавца'].nunique()}")
    st.sidebar.write(f"**Период:** {df['Дата'].min().strftime('%d.%m.%Y')} - {df['Дата'].max().strftime('%d.%m.%Y')}")
    
    # Основной контент
    col1, col2, col3, col4 = st.columns(4)
    
    # KPI карточки
    kpis = calculate_kpis(df)
    
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <h4>📦 Всего заказов</h4>
            <h2>{kpis.get('total_orders', 0):,.0f}</h2>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <h4>💰 Всего выкупов</h4>
            <h2>{kpis.get('total_sales', 0):,.0f}</h2>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <h4>💵 Общая выручка</h4>
            <h2>{kpis.get('total_revenue', 0):,.0f} ₽</h2>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div class="metric-card">
            <h4>📈 Конверсия</h4>
            <h2>{kpis.get('conversion_rate', 0):.1f}%</h2>
        </div>
        """, unsafe_allow_html=True)
    
    # Дополнительные метрики
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("👁️ Переходы", f"{kpis.get('total_views', 0):,.0f}")
    
    with col2:
        st.metric("🛒 В корзину", f"{kpis.get('total_cart_adds', 0):,.0f}")
    
    with col3:
        st.metric("📊 Конв. корзина", f"{kpis.get('cart_conversion', 0):.1f}%")
    
    with col4:
        st.metric("💎 Ср. чек", f"{kpis.get('avg_revenue_per_order', 0):,.0f} ₽")
    
    # Настройки анализа
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        period = st.selectbox("📅 Период агрегации", ['D', 'W', 'M'], 
                            format_func=lambda x: {'D': 'Дни', 'W': 'Недели', 'M': 'Месяцы'}[x])
    
    with col2:
        date_range = st.date_input(
            "📆 Диапазон дат",
            value=(df['Дата'].min().date(), df['Дата'].max().date()),
            min_value=df['Дата'].min().date(),
            max_value=df['Дата'].max().date()
        )
    
    with col3:
        selected_products = st.multiselect(
            "🏷️ Товары",
            options=df['Артикул продавца'].unique().tolist(),
            default=df['Артикул продавца'].unique().tolist()
        )
    
    # Фильтрация данных
    if len(date_range) == 2:
        filtered_df = df[
            (df['Дата'].dt.date >= date_range[0]) &
            (df['Дата'].dt.date <= date_range[1]) &
            (df['Артикул продавца'].isin(selected_products))
        ]
    else:
        filtered_df = df[df['Артикул продавца'].isin(selected_products)]
    
    # Графики
    st.markdown("---")
    st.markdown("## 📈 Графики и аналитика")
    
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 Тренды", "🔄 Конверсия", "💰 Выручка", "🏷️ Товары", "📅 Сезонность"])
    
    with tab1:
        st.plotly_chart(plot_orders_trend(filtered_df, period), use_container_width=True)
    
    with tab2:
        st.plotly_chart(plot_conversion_funnel(filtered_df, period), use_container_width=True)
    
    with tab3:
        st.plotly_chart(plot_revenue_trend(filtered_df, period), use_container_width=True)
    
    with tab4:
        st.plotly_chart(plot_product_performance(filtered_df), use_container_width=True)
    
    with tab5:
        fig1, fig2 = plot_seasonality(filtered_df)
        col1, col2 = st.columns(2)
        with col1:
            st.plotly_chart(fig1, use_container_width=True)
        with col2:
            st.plotly_chart(fig2, use_container_width=True)
    
    # Сравнение периодов
    st.markdown("---")
    st.markdown("## 📊 Сравнение периодов")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Текущий период")
        current_start = st.date_input("Начало", value=date_range[0] if len(date_range) == 2 else df['Дата'].min().date())
        current_end = st.date_input("Конец", value=date_range[1] if len(date_range) == 2 else df['Дата'].max().date())
    
    with col2:
        st.markdown("### Предыдущий период")
        days_diff = (current_end - current_start).days
        prev_start = current_start - timedelta(days=days_diff)
        prev_end = current_start - timedelta(days=1)
        
        st.write(f"**Начало:** {prev_start}")
        st.write(f"**Конец:** {prev_end}")
    
    # Расчет сравнения
    if st.button("🔄 Рассчитать сравнение"):
        comparison = compare_periods(filtered_df, (current_start, current_end), (prev_start, prev_end))
        
        if comparison:
            st.markdown("### Результаты сравнения")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                metric = 'Заказали, шт'
                data = comparison[metric]
                st.metric(
                    label="Заказы",
                    value=f"{data['current']:,.0f}",
                    delta=f"{data['change_pct']:+.1f}%"
                )
            
            with col2:
                metric = 'Выкупили, шт'
                data = comparison[metric]
                st.metric(
                    label="Выкупы",
                    value=f"{data['current']:,.0f}",
                    delta=f"{data['change_pct']:+.1f}%"
                )
            
            with col3:
                metric = 'Выкупили на сумму, ₽'
                data = comparison[metric]
                st.metric(
                    label="Выручка",
                    value=f"{data['current']:,.0f} ₽",
                    delta=f"{data['change_pct']:+.1f}%"
                )
            
            with col4:
                metric = 'Переходы в карточку'
                data = comparison[metric]
                st.metric(
                    label="Переходы",
                    value=f"{data['current']:,.0f}",
                    delta=f"{data['change_pct']:+.1f}%"
                )
    
    # Детальная таблица
    st.markdown("---")
    st.markdown("## 📋 Детальные данные")
    
    if st.checkbox("Показать детальную таблицу"):
        st.dataframe(filtered_df, use_container_width=True)
        
        # Экспорт данных
        csv = filtered_df.to_csv(index=False, encoding='utf-8-sig')
        st.download_button(
            label="📥 Скачать CSV",
            data=csv,
            file_name=f"wb_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )

if __name__ == "__main__":
    main()











