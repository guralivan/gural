import streamlit as st
import pandas as pd
import requests
import json
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np

# Настройка страницы
st.set_page_config(
    page_title="Wildberries Detailed Analysis",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# API ключ
API_KEY = "eyJhbGciOiJFUzI1NiIsImtpZCI6IjIwMjUwNTIwdjEiLCJ0eXAiOiJKV1QifQ.eyJlbnQiOjEsImV4cCI6MTc3MTQ1MzUxOSwiaWQiOiIwMTk4YzcwMy0wMGEyLTdhOTktYTlmMS05NzcxYjg5MThkYjkiLCJpaWQiOjE4MTczODQ1LCJvaWQiOjYyODAzLCJzIjoxMTM4Miwic2lkIjoiOTcyMmFhYTItM2M5My01MTc0LWI2MWUtMzZlZTk2NjhmODczIiwidCI6ZmFsc2UsInVpZCI6MTgxNzM4NDV9.23-CLgZixk3mkxsmfE0qDq4BPlyJw5QWhnXvPCQK0h7qAtDOCxhIzOahhc6uKqveTKvr9NI6IglvBDjHWLqohQ"

# Заголовки для API запросов
headers = {
    'Authorization': API_KEY,
    'Content-Type': 'application/json'
}

def get_stocks_data():
    """Получение данных о остатках"""
    url = "https://marketplace-api.wildberries.ru/api/v1/supplier/stocks"
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Ошибка при получении данных о остатках: {e}")
        return None

def get_orders_data(date_from, date_to):
    """Получение данных о заказах"""
    url = "https://marketplace-api.wildberries.ru/api/v1/supplier/orders"
    
    params = {
        'dateFrom': date_from.strftime('%Y-%m-%d'),
        'dateTo': date_to.strftime('%Y-%m-%d')
    }
    
    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Ошибка при получении данных о заказах: {e}")
        return None

def get_sales_data(date_from, date_to):
    """Получение данных о продажах"""
    url = "https://marketplace-api.wildberries.ru/api/v1/supplier/sales"
    
    params = {
        'dateFrom': date_from.strftime('%Y-%m-%d'),
        'dateTo': date_to.strftime('%Y-%m-%d')
    }
    
    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Ошибка при получении данных о продажах: {e}")
        return None

def process_data(data, data_type):
    """Обработка данных"""
    if not data or data_type not in data:
        return pd.DataFrame()
    
    items = data[data_type]
    if not items:
        return pd.DataFrame()
    
    df = pd.DataFrame(items)
    
    # Преобразование дат
    date_columns = ['date', 'dateFrom', 'dateTo', 'lastChangeDate']
    for col in date_columns:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col])
    
    return df

def calculate_detailed_metrics(orders_df, sales_df, stocks_df):
    """Расчет детальных метрик"""
    metrics = {}
    
    # Базовые метрики
    metrics['total_orders'] = len(orders_df) if not orders_df.empty else 0
    metrics['total_sales'] = len(sales_df) if not sales_df.empty else 0
    metrics['total_stocks'] = len(stocks_df) if not stocks_df.empty else 0
    
    # Финансовые метрики
    if not orders_df.empty:
        metrics['orders_sum'] = orders_df.get('finishedPrice', 0).sum()
        metrics['orders_avg'] = orders_df.get('finishedPrice', 0).mean()
    else:
        metrics['orders_sum'] = 0
        metrics['orders_avg'] = 0
    
    if not sales_df.empty:
        metrics['sales_sum'] = sales_df.get('finishedPrice', 0).sum()
        metrics['sales_avg'] = sales_df.get('finishedPrice', 0).mean()
    else:
        metrics['sales_sum'] = 0
        metrics['sales_avg'] = 0
    
    # Конверсия
    if metrics['total_orders'] > 0:
        metrics['conversion_rate'] = (metrics['total_sales'] / metrics['total_orders']) * 100
    else:
        metrics['conversion_rate'] = 0
    
    return metrics

def create_analytics_dashboard():
    """Создание аналитического дашборда"""
    st.title("📈 Wildberries Detailed Analysis")
    st.markdown("---")
    
    # Боковая панель
    with st.sidebar:
        st.header("⚙️ Настройки анализа")
        
        # Выбор периода
        st.subheader("Период анализа")
        date_option = st.selectbox(
            "Выберите период:",
            ["Последние 7 дней", "Последние 30 дней", "Последние 90 дней", "Произвольный период"]
        )
        
        if date_option == "Произвольный период":
            date_from = st.date_input("Дата начала", value=datetime.now() - timedelta(days=30))
            date_to = st.date_input("Дата окончания", value=datetime.now())
        else:
            days_map = {
                "Последние 7 дней": 7,
                "Последние 30 дней": 30,
                "Последние 90 дней": 90
            }
            days = days_map[date_option]
            date_from = datetime.now() - timedelta(days=days)
            date_to = datetime.now()
            st.write(f"Период: {date_from.strftime('%Y-%m-%d')} - {date_to.strftime('%Y-%m-%d')}")
        
        # Типы данных для анализа
        st.subheader("Типы данных")
        include_orders = st.checkbox("Заказы", value=True)
        include_sales = st.checkbox("Продажи", value=True)
        include_stocks = st.checkbox("Остатки", value=True)
        
        # Кнопка загрузки
        if st.button("📊 Загрузить данные", type="primary"):
            st.session_state.load_data = True
    
    # Основной контент
    if st.button("🔄 Обновить анализ") or st.session_state.get('load_data', False):
        with st.spinner("Загружаем и анализируем данные..."):
            
            # Получение данных
            orders_df = pd.DataFrame()
            sales_df = pd.DataFrame()
            stocks_df = pd.DataFrame()
            
            if include_orders:
                orders_data = get_orders_data(date_from, date_to)
                orders_df = process_data(orders_data, 'orders')
            
            if include_sales:
                sales_data = get_sales_data(date_from, date_to)
                sales_df = process_data(sales_data, 'sales')
            
            if include_stocks:
                stocks_data = get_stocks_data()
                stocks_df = process_data(stocks_data, 'stocks')
            
            # Сохранение в session state
            st.session_state.orders_df = orders_df
            st.session_state.sales_df = sales_df
            st.session_state.stocks_df = stocks_df
            st.session_state.load_data = False
            
            st.success("Данные успешно загружены!")
    
    # Отображение результатов
    if hasattr(st.session_state, 'orders_df'):
        orders_df = st.session_state.orders_df
        sales_df = st.session_state.sales_df
        stocks_df = st.session_state.stocks_df
        
        # Расчет метрик
        metrics = calculate_detailed_metrics(orders_df, sales_df, stocks_df)
        
        # Отображение метрик
        st.subheader("📊 Ключевые метрики")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                label="📦 Заказы",
                value=metrics['total_orders'],
                delta=None
            )
            st.metric(
                label="💰 Сумма заказов",
                value=f"{metrics['orders_sum']:,.0f} ₽"
            )
        
        with col2:
            st.metric(
                label="🛒 Продажи",
                value=metrics['total_sales'],
                delta=None
            )
            st.metric(
                label="💵 Сумма продаж",
                value=f"{metrics['sales_sum']:,.0f} ₽"
            )
        
        with col3:
            st.metric(
                label="📊 Конверсия",
                value=f"{metrics['conversion_rate']:.1f}%",
                delta=None
            )
            st.metric(
                label="📦 Остатки",
                value=metrics['total_stocks']
            )
        
        with col4:
            st.metric(
                label="📈 Средний чек заказов",
                value=f"{metrics['orders_avg']:,.0f} ₽"
            )
            st.metric(
                label="📈 Средний чек продаж",
                value=f"{metrics['sales_avg']:,.0f} ₽"
            )
        
        # Детальный анализ
        st.markdown("---")
        st.subheader("📈 Детальный анализ")
        
        tab1, tab2, tab3, tab4 = st.tabs(["📊 Обзор", "📦 Заказы", "🛒 Продажи", "📦 Остатки"])
        
        with tab1:
            st.write("### Общий обзор данных")
            
            # Сводная таблица
            summary_data = {
                'Метрика': ['Всего заказов', 'Всего продаж', 'Сумма заказов', 'Сумма продаж', 'Конверсия'],
                'Значение': [
                    metrics['total_orders'],
                    metrics['total_sales'],
                    f"{metrics['orders_sum']:,.0f} ₽",
                    f"{metrics['sales_sum']:,.0f} ₽",
                    f"{metrics['conversion_rate']:.1f}%"
                ]
            }
            
            summary_df = pd.DataFrame(summary_data)
            st.dataframe(summary_df, use_container_width=True)
            
            # График трендов
            if not orders_df.empty or not sales_df.empty:
                fig = go.Figure()
                
                if not orders_df.empty and 'date' in orders_df.columns:
                    daily_orders = orders_df.groupby(orders_df['date'].dt.date).agg({
                        'finishedPrice': 'sum',
                        'nmId': 'count'
                    }).reset_index()
                    daily_orders.columns = ['date', 'orders_sum', 'orders_count']
                    
                    fig.add_trace(go.Scatter(
                        x=daily_orders['date'],
                        y=daily_orders['orders_sum'],
                        mode='lines+markers',
                        name='Сумма заказов',
                        line=dict(color='blue')
                    ))
                
                if not sales_df.empty and 'date' in sales_df.columns:
                    daily_sales = sales_df.groupby(sales_df['date'].dt.date).agg({
                        'finishedPrice': 'sum',
                        'nmId': 'count'
                    }).reset_index()
                    daily_sales.columns = ['date', 'sales_sum', 'sales_count']
                    
                    fig.add_trace(go.Scatter(
                        x=daily_sales['date'],
                        y=daily_sales['sales_sum'],
                        mode='lines+markers',
                        name='Сумма продаж',
                        line=dict(color='green')
                    ))
                
                fig.update_layout(
                    title='Тренды заказов и продаж',
                    xaxis_title='Дата',
                    yaxis_title='Сумма (₽)',
                    hovermode='x unified'
                )
                
                st.plotly_chart(fig, use_container_width=True)
        
        with tab2:
            if not orders_df.empty:
                st.write("### Анализ заказов")
                st.dataframe(orders_df, use_container_width=True)
                
                # Статистика по заказам
                if 'finishedPrice' in orders_df.columns:
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        fig = px.histogram(orders_df, x='finishedPrice', title='Распределение цен заказов')
                        st.plotly_chart(fig, use_container_width=True)
                    
                    with col2:
                        fig = px.box(orders_df, y='finishedPrice', title='Боксплот цен заказов')
                        st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Нет данных о заказах")
        
        with tab3:
            if not sales_df.empty:
                st.write("### Анализ продаж")
                st.dataframe(sales_df, use_container_width=True)
                
                # Статистика по продажам
                if 'finishedPrice' in sales_df.columns:
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        fig = px.histogram(sales_df, x='finishedPrice', title='Распределение цен продаж')
                        st.plotly_chart(fig, use_container_width=True)
                    
                    with col2:
                        fig = px.box(sales_df, y='finishedPrice', title='Боксплот цен продаж')
                        st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Нет данных о продажах")
        
        with tab4:
            if not stocks_df.empty:
                st.write("### Анализ остатков")
                st.dataframe(stocks_df, use_container_width=True)
                
                # Анализ остатков
                if 'quantity' in stocks_df.columns:
                    fig = px.histogram(stocks_df, x='quantity', title='Распределение остатков')
                    st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Нет данных об остатках")

def main():
    """Главная функция"""
    # Инициализация session state
    if 'load_data' not in st.session_state:
        st.session_state.load_data = False
    
    create_analytics_dashboard()

if __name__ == "__main__":
    main()
