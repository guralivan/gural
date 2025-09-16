import streamlit as st
import pandas as pd
import requests
import json
import time
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Настройка страницы
st.set_page_config(
    page_title="Wildberries API Dashboard",
    page_icon="📊",
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

def get_orders_data(date_from, date_to):
    """Получение данных о заказах"""
    # Попробуем несколько вариантов URL
    urls = [
        "https://marketplace-api.wildberries.ru/api/v1/supplier/orders",
        "https://statistics-api.wildberries.ru/api/v1/supplier/orders",
        "https://suppliers-api.wildberries.ru/api/v1/supplier/orders"
    ]
    
    params = {
        'dateFrom': date_from.strftime('%Y-%m-%d'),
        'dateTo': date_to.strftime('%Y-%m-%d')
    }
    
    for url in urls:
        try:
            response = requests.get(url, headers=headers, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            st.warning(f"Не удалось подключиться к {url}: {e}")
            continue
    
    st.error("Не удалось подключиться ни к одному из API endpoints")
    return None

def get_sales_data(date_from, date_to):
    """Получение данных о продажах (выкупах)"""
    # Попробуем несколько вариантов URL
    urls = [
        "https://marketplace-api.wildberries.ru/api/v1/supplier/sales",
        "https://statistics-api.wildberries.ru/api/v1/supplier/sales",
        "https://suppliers-api.wildberries.ru/api/v1/supplier/sales"
    ]
    
    params = {
        'dateFrom': date_from.strftime('%Y-%m-%d'),
        'dateTo': date_to.strftime('%Y-%m-%d')
    }
    
    for url in urls:
        try:
            response = requests.get(url, headers=headers, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            st.warning(f"Не удалось подключиться к {url}: {e}")
            continue
    
    st.error("Не удалось подключиться ни к одному из API endpoints")
    return None

def test_api_connection():
    """Тестирование подключения к API"""
    test_urls = [
        "https://seller-analytics-api.wildberries.ru/ping",
        "https://marketplace-api.wildberries.ru/api/v1/supplier/orders",
        "https://statistics-api.wildberries.ru/api/v1/supplier/orders"
    ]
    
    for url in test_urls:
        try:
            response = requests.get(url, headers=headers, timeout=5)
            if response.status_code == 200:
                return True, url
        except:
            continue
    
    return False, None

def get_statistics_data(date_from, date_to):
    """Получение статистических данных"""
    url = "https://statistics-api.wildberries.ru/api/v5/supplier/reportDetailByPeriod"
    
    params = {
        'dateFrom': date_from.strftime('%Y-%m-%d'),
        'dateTo': date_to.strftime('%Y-%m-%d'),
        'rrdid': 0,
        'limit': 100000
    }
    
    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Ошибка при получении статистики: {e}")
        return None

def get_categories_data():
    """Получение категорий товаров"""
    url = "https://marketplace-api.wildberries.ru/api/lite/products/wb_categories"
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Ошибка при получении категорий: {e}")
        return None

def get_search_queries_report(date_from, date_to):
    """Получение отчета по поисковым запросам"""
    # Создание отчета
    create_url = "https://seller-analytics-api.wildberries.ru/api/v1/search-queries/report"
    
    create_data = {
        "dateFrom": date_from.strftime('%Y-%m-%d'),
        "dateTo": date_to.strftime('%Y-%m-%d')
    }
    
    try:
        # Создаем отчет
        response = requests.post(create_url, headers=headers, json=create_data)
        response.raise_for_status()
        report_data = response.json()
        
        if 'reportId' in report_data:
            report_id = report_data['reportId']
            
            # Проверяем готовность отчета
            check_url = f"https://seller-analytics-api.wildberries.ru/api/v1/search-queries/report/{report_id}"
            
            for _ in range(10):  # Проверяем до 10 раз
                check_response = requests.get(check_url, headers=headers)
                if check_response.status_code == 200:
                    check_data = check_response.json()
                    if check_data.get('status') == 'ready':
                        # Скачиваем готовый отчет
                        download_url = f"https://seller-analytics-api.wildberries.ru/api/v1/search-queries/report/{report_id}/download"
                        download_response = requests.get(download_url, headers=headers)
                        if download_response.status_code == 200:
                            return download_response.json()
                
                time.sleep(2)  # Ждем 2 секунды перед следующей проверкой
            
            st.warning("Отчет не готов в течение ожидаемого времени")
            return None
            
    except requests.exceptions.RequestException as e:
        st.error(f"Ошибка при получении отчета по поисковым запросам: {e}")
        return None

def get_sales_funnel(date_from, date_to):
    """Получение данных воронки продаж"""
    url = "https://seller-analytics-api.wildberries.ru/api/v1/sales-funnel"
    
    params = {
        'dateFrom': date_from.strftime('%Y-%m-%d'),
        'dateTo': date_to.strftime('%Y-%m-%d')
    }
    
    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Ошибка при получении воронки продаж: {e}")
        return None

def get_hidden_products():
    """Получение данных о скрытых товарах"""
    url = "https://seller-analytics-api.wildberries.ru/api/v1/hidden-products"
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Ошибка при получении скрытых товаров: {e}")
        return None

def get_brand_share():
    """Получение данных о доле бренда"""
    url = "https://seller-analytics-api.wildberries.ru/api/v1/brand-share"
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Ошибка при получении доли бренда: {e}")
        return None

def get_warehouse_stocks():
    """Получение остатков по складам"""
    url = "https://seller-analytics-api.wildberries.ru/api/v1/warehouse-stocks"
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Ошибка при получении остатков по складам: {e}")
        return None

def get_orders_summary(date_from, date_to):
    """Получение сводки по заказам"""
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
        st.error(f"Ошибка при получении сводки по заказам: {e}")
        return None

def create_demo_data():
    """Создание демо-данных для тестирования"""
    from datetime import datetime, timedelta
    import random
    
    # Создаем тестовые данные за последние 7 дней
    dates = [(datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d') for i in range(7)]
    
    # Демо-заказы
    demo_orders = []
    for date in dates:
        for _ in range(random.randint(5, 15)):
            demo_orders.append({
                'date': date,
                'nmId': random.randint(1000000, 9999999),
                'finishedPrice': random.randint(1000, 5000),
                'orderId': random.randint(100000000, 999999999),
                'status': 'new'
            })
    
    # Демо-продажи
    demo_sales = []
    for date in dates:
        for _ in range(random.randint(3, 10)):
            demo_sales.append({
                'date': date,
                'nmId': random.randint(1000000, 9999999),
                'finishedPrice': random.randint(1000, 5000),
                'saleId': random.randint(100000000, 999999999),
                'status': 'sold'
            })
    
    return {'orders': demo_orders}, {'sales': demo_sales}

def process_orders_data(data):
    """Обработка данных о заказах"""
    if not data or 'orders' not in data:
        return pd.DataFrame()
    
    orders = data['orders']
    if not orders:
        return pd.DataFrame()
    
    df = pd.DataFrame(orders)
    
    # Преобразование дат
    if 'date' in df.columns:
        df['date'] = pd.to_datetime(df['date'])
    
    return df

def process_sales_data(data):
    """Обработка данных о продажах"""
    if not data or 'sales' not in data:
        return pd.DataFrame()
    
    sales = data['sales']
    if not sales:
        return pd.DataFrame()
    
    df = pd.DataFrame(sales)
    
    # Преобразование дат
    if 'date' in df.columns:
        df['date'] = pd.to_datetime(df['date'])
    
    return df

def calculate_metrics(orders_df, sales_df):
    """Расчет метрик"""
    metrics = {}
    
    # Метрики по заказам
    if not orders_df.empty:
        metrics['total_orders'] = len(orders_df)
        metrics['orders_sum'] = orders_df.get('finishedPrice', 0).sum() if 'finishedPrice' in orders_df.columns else 0
    else:
        metrics['total_orders'] = 0
        metrics['orders_sum'] = 0
    
    # Метрики по продажам
    if not sales_df.empty:
        metrics['total_sales'] = len(sales_df)
        metrics['sales_sum'] = sales_df.get('finishedPrice', 0).sum() if 'finishedPrice' in sales_df.columns else 0
    else:
        metrics['total_sales'] = 0
        metrics['sales_sum'] = 0
    
    return metrics

def create_dashboard():
    """Создание основного дашборда"""
    st.title("📊 Wildberries API Dashboard")
    st.markdown("---")
    
    # Боковая панель для настроек
    with st.sidebar:
        st.header("⚙️ Настройки")
        
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
        
        # Кнопка обновления данных
        if st.button("🔄 Обновить данные", type="primary"):
            st.session_state.refresh_data = True
    
    # Основной контент
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("📈 Анализ данных")
        
        # Тестирование подключения
        if st.button("🔍 Тестировать подключение к API"):
            with st.spinner("Проверяем подключение..."):
                is_connected, working_url = test_api_connection()
                if is_connected:
                    st.success(f"✅ Подключение успешно! Рабочий URL: {working_url}")
                else:
                    st.error("❌ Не удалось подключиться к API Wildberries")
        
        # Получение данных
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("📊 Загрузить данные") or st.session_state.get('refresh_data', False):
                with st.spinner("Загружаем данные..."):
                    # Получение данных о заказах
                    orders_data = get_orders_data(date_from, date_to)
                    orders_df = process_orders_data(orders_data)
                    
                    # Получение данных о продажах
                    sales_data = get_sales_data(date_from, date_to)
                    sales_df = process_sales_data(sales_data)
                    
                    # Сохранение данных в session state
                    st.session_state.orders_df = orders_df
                    st.session_state.sales_df = sales_df
                    st.session_state.refresh_data = False
                    
                    if not orders_df.empty or not sales_df.empty:
                        st.success("Данные успешно загружены!")
                    else:
                        st.warning("Данные не найдены за выбранный период")
        
        with col2:
            if st.button("🎮 Загрузить демо-данные"):
                with st.spinner("Создаем демо-данные..."):
                    # Создание демо-данных
                    demo_orders, demo_sales = create_demo_data()
                    orders_df = process_orders_data(demo_orders)
                    sales_df = process_sales_data(demo_sales)
                    
                    # Сохранение данных в session state
                    st.session_state.orders_df = orders_df
                    st.session_state.sales_df = sales_df
                    
                    st.success("Демо-данные успешно загружены!")
        
        with col3:
            if st.button("📈 Получить статистику"):
                with st.spinner("Загружаем статистику..."):
                    # Получение статистики
                    stats_data = get_statistics_data(date_from, date_to)
                    if stats_data:
                        st.session_state.stats_data = stats_data
                        st.success("Статистика успешно загружена!")
                    else:
                        st.error("Не удалось загрузить статистику")
            
            if st.button("📂 Получить категории"):
                with st.spinner("Загружаем категории..."):
                    # Получение категорий
                    categories_data = get_categories_data()
                    if categories_data:
                        st.session_state.categories_data = categories_data
                        st.success("Категории успешно загружены!")
                    else:
                        st.error("Не удалось загрузить категории")
    
    # Дополнительные кнопки аналитики
    st.markdown("---")
    st.subheader("🔍 Аналитика Wildberries")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("🔍 Поисковые запросы"):
            with st.spinner("Создаем отчет по поисковым запросам..."):
                search_data = get_search_queries_report(date_from, date_to)
                if search_data:
                    st.session_state.search_data = search_data
                    st.success("Отчет по поисковым запросам готов!")
                else:
                    st.error("Не удалось создать отчет")
    
    with col2:
        if st.button("📊 Воронка продаж"):
            with st.spinner("Загружаем воронку продаж..."):
                funnel_data = get_sales_funnel(date_from, date_to)
                if funnel_data:
                    st.session_state.funnel_data = funnel_data
                    st.success("Воронка продаж загружена!")
                else:
                    st.error("Не удалось загрузить воронку продаж")
    
    with col3:
        if st.button("👻 Скрытые товары"):
            with st.spinner("Загружаем скрытые товары..."):
                hidden_data = get_hidden_products()
                if hidden_data:
                    st.session_state.hidden_data = hidden_data
                    st.success("Скрытые товары загружены!")
                else:
                    st.error("Не удалось загрузить скрытые товары")
    
    with col4:
        if st.button("📦 Остатки по складам"):
            with st.spinner("Загружаем остатки по складам..."):
                stocks_data = get_warehouse_stocks()
                if stocks_data:
                    st.session_state.warehouse_stocks = stocks_data
                    st.success("Остатки по складам загружены!")
                else:
                    st.error("Не удалось загрузить остатки по складам")
    
    # Отображение метрик
    if hasattr(st.session_state, 'orders_df') and hasattr(st.session_state, 'sales_df'):
        orders_df = st.session_state.orders_df
        sales_df = st.session_state.sales_df
        
        metrics = calculate_metrics(orders_df, sales_df)
        
        # Метрики в колонках
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                label="📦 Всего заказов",
                value=metrics['total_orders'],
                delta=None
            )
        
        with col2:
            st.metric(
                label="💰 Сумма заказов",
                value=f"{metrics['orders_sum']:,.0f} ₽",
                delta=None
            )
        
        with col3:
            st.metric(
                label="🛒 Всего выкупов",
                value=metrics['total_sales'],
                delta=None
            )
        
        with col4:
            st.metric(
                label="💵 Сумма выкупов",
                value=f"{metrics['sales_sum']:,.0f} ₽",
                delta=None
            )
        
        # Графики
        st.markdown("---")
        st.subheader("📊 Визуализация данных")
        
        tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9 = st.tabs([
            "📦 Заказы", "🛒 Выкупы", "📈 Сравнение", "📊 Статистика", "📂 Категории",
            "🔍 Поисковые запросы", "📊 Воронка продаж", "👻 Скрытые товары", "📦 Остатки складов"
        ])
        
        with tab1:
            if not orders_df.empty:
                st.write("### Данные о заказах")
                st.dataframe(orders_df)
                
                # График заказов по дням
                if 'date' in orders_df.columns:
                    daily_orders = orders_df.groupby(orders_df['date'].dt.date).size().reset_index(name='count')
                    fig = px.line(daily_orders, x='date', y='count', title='Заказы по дням')
                    st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Нет данных о заказах за выбранный период")
        
        with tab2:
            if not sales_df.empty:
                st.write("### Данные о выкупах")
                st.dataframe(sales_df)
                
                # График выкупов по дням
                if 'date' in sales_df.columns:
                    daily_sales = sales_df.groupby(sales_df['date'].dt.date).size().reset_index(name='count')
                    fig = px.line(daily_sales, x='date', y='count', title='Выкупы по дням')
                    st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Нет данных о выкупах за выбранный период")
        
        with tab3:
            if not orders_df.empty or not sales_df.empty:
                # Сравнительный график
                fig = go.Figure()
                
                if not orders_df.empty and 'date' in orders_df.columns:
                    daily_orders = orders_df.groupby(orders_df['date'].dt.date).size().reset_index(name='orders')
                    fig.add_trace(go.Scatter(
                        x=daily_orders['date'],
                        y=daily_orders['orders'],
                        mode='lines+markers',
                        name='Заказы',
                        line=dict(color='blue')
                    ))
                
                if not sales_df.empty and 'date' in sales_df.columns:
                    daily_sales = sales_df.groupby(sales_df['date'].dt.date).size().reset_index(name='sales')
                    fig.add_trace(go.Scatter(
                        x=daily_sales['date'],
                        y=daily_sales['sales'],
                        mode='lines+markers',
                        name='Выкупы',
                        line=dict(color='green')
                    ))
                
                fig.update_layout(
                    title='Сравнение заказов и выкупов',
                    xaxis_title='Дата',
                    yaxis_title='Количество',
                    hovermode='x unified'
                )
                
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Нет данных для сравнения")
        
        with tab4:
            if hasattr(st.session_state, 'stats_data') and st.session_state.stats_data:
                st.write("### Статистические данные")
                stats_df = pd.DataFrame(st.session_state.stats_data)
                st.dataframe(stats_df, use_container_width=True)
                
                # Анализ статистики
                if not stats_df.empty:
                    st.write("### Анализ статистики")
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write("**Основные показатели:**")
                        st.json(stats_df.head().to_dict())
                    
                    with col2:
                        st.write("**Структура данных:**")
                        st.write(f"Количество записей: {len(stats_df)}")
                        st.write(f"Количество колонок: {len(stats_df.columns)}")
            else:
                st.info("Нет данных статистики. Нажмите '📈 Получить статистику' для загрузки.")
        
        with tab5:
            if hasattr(st.session_state, 'categories_data') and st.session_state.categories_data:
                st.write("### Категории товаров")
                categories_df = pd.DataFrame(st.session_state.categories_data.get('categories', []))
                
                if not categories_df.empty:
                    st.dataframe(categories_df, use_container_width=True)
                    
                    # Визуализация категорий
                    if 'title' in categories_df.columns and 'wbCode' in categories_df.columns:
                        fig = px.bar(
                            categories_df, 
                            x='title', 
                            y='wbCode',
                            title='Категории товаров Wildberries'
                        )
                        fig.update_xaxes(tickangle=45)
                        st.plotly_chart(fig, use_container_width=True)
                else:
                    st.write("Данные о категориях:")
                    st.json(st.session_state.categories_data)
            else:
                st.info("Нет данных о категориях. Нажмите '📂 Получить категории' для загрузки.")
        
        with tab6:
            if hasattr(st.session_state, 'search_data') and st.session_state.search_data:
                st.write("### Отчет по поисковым запросам")
                search_df = pd.DataFrame(st.session_state.search_data)
                if not search_df.empty:
                    st.dataframe(search_df, use_container_width=True)
                    
                    # Анализ поисковых запросов
                    if 'query' in search_df.columns and 'clicks' in search_df.columns:
                        fig = px.bar(
                            search_df.head(20), 
                            x='query', 
                            y='clicks',
                            title='Топ-20 поисковых запросов по кликам'
                        )
                        fig.update_xaxes(tickangle=45)
                        st.plotly_chart(fig, use_container_width=True)
                else:
                    st.json(st.session_state.search_data)
            else:
                st.info("Нет данных по поисковым запросам. Нажмите '🔍 Поисковые запросы' для создания отчета.")
        
        with tab7:
            if hasattr(st.session_state, 'funnel_data') and st.session_state.funnel_data:
                st.write("### Воронка продаж")
                funnel_df = pd.DataFrame(st.session_state.funnel_data)
                if not funnel_df.empty:
                    st.dataframe(funnel_df, use_container_width=True)
                    
                    # Визуализация воронки
                    if 'stage' in funnel_df.columns and 'value' in funnel_df.columns:
                        fig = px.funnel(
                            funnel_df, 
                            x='value', 
                            y='stage',
                            title='Воронка продаж'
                        )
                        st.plotly_chart(fig, use_container_width=True)
                else:
                    st.json(st.session_state.funnel_data)
            else:
                st.info("Нет данных воронки продаж. Нажмите '📊 Воронка продаж' для загрузки.")
        
        with tab8:
            if hasattr(st.session_state, 'hidden_data') and st.session_state.hidden_data:
                st.write("### Скрытые товары")
                hidden_df = pd.DataFrame(st.session_state.hidden_data)
                if not hidden_df.empty:
                    st.dataframe(hidden_df, use_container_width=True)
                    
                    # Статистика скрытых товаров
                    st.write(f"**Всего скрытых товаров:** {len(hidden_df)}")
                    
                    if 'reason' in hidden_df.columns:
                        reason_counts = hidden_df['reason'].value_counts()
                        fig = px.pie(
                            values=reason_counts.values,
                            names=reason_counts.index,
                            title='Причины скрытия товаров'
                        )
                        st.plotly_chart(fig, use_container_width=True)
                else:
                    st.json(st.session_state.hidden_data)
            else:
                st.info("Нет данных о скрытых товарах. Нажмите '👻 Скрытые товары' для загрузки.")
        
        with tab9:
            if hasattr(st.session_state, 'warehouse_stocks') and st.session_state.warehouse_stocks:
                st.write("### Остатки по складам")
                stocks_df = pd.DataFrame(st.session_state.warehouse_stocks)
                if not stocks_df.empty:
                    st.dataframe(stocks_df, use_container_width=True)
                    
                    # Анализ остатков
                    if 'warehouse' in stocks_df.columns and 'quantity' in stocks_df.columns:
                        warehouse_summary = stocks_df.groupby('warehouse')['quantity'].sum().reset_index()
                        fig = px.bar(
                            warehouse_summary,
                            x='warehouse',
                            y='quantity',
                            title='Остатки по складам'
                        )
                        st.plotly_chart(fig, use_container_width=True)
                else:
                    st.json(st.session_state.warehouse_stocks)
            else:
                st.info("Нет данных об остатках по складам. Нажмите '📦 Остатки по складам' для загрузки.")

def main():
    """Главная функция"""
    # Инициализация session state
    if 'refresh_data' not in st.session_state:
        st.session_state.refresh_data = False
    
    create_dashboard()

if __name__ == "__main__":
    main()
