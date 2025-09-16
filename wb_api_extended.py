# -*- coding: utf-8 -*-
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
    page_title="Wildberries API Dashboard (Расширенный)",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# API ключ (замените на ваш актуальный ключ)
API_KEY = "eyJhbGciOiJFUzI1NiIsImtpZCI6IjIwMjUwNTIwdjEiLCJ0eXAiOiJKV1QifQ.eyJlbnQiOjEsImV4cCI6MTc3MTQ1MzUxOSwiaWQiOiIwMTk4YzcwMy0wMGEyLTdhOTktYTlmMS05NzcxYjg5MThkYjkiLCJpaWQiOjE4MTczODQ1LCJvaWQiOjYyODAzLCJzIjoxMTM4Miwic2lkIjoiOTcyMmFhYTItM2M5My01MTc0LWI2MWUtMzZlZTk2NjhmODczIiwidCI6ZmFsc2UsInVpZCI6MTgxNzM4NDV9.23-CLgZixk3mkxsmfE0qDq4BPlyJw5QWhnXvPCQK0h7qAtDOCxhIzOahhc6uKqveTKvr9NI6IglvBDjHWLqohQ"

# Актуальные заголовки для API запросов
headers = {
    'Authorization': f'Bearer {API_KEY}',
    'Content-Type': 'application/json',
    'Accept': 'application/json'
}

# Актуальные базовые URL для API Wildberries
BASE_URLS = {
    'marketplace': 'https://marketplace-api.wildberries.ru',
    'statistics': 'https://statistics-api.wildberries.ru', 
    'seller_analytics': 'https://seller-analytics-api.wildberries.ru',
    'suppliers': 'https://suppliers-api.wildberries.ru',
    'content': 'https://content-api.wildberries.ru',
    'feedbacks': 'https://feedbacks-api.wildberries.ru',
    'questions': 'https://questions-api.wildberries.ru'
}

# Расширенный список всех возможных endpoints согласно документации
ALL_ENDPOINTS = {
    'orders': [
        f"{BASE_URLS['statistics']}/api/v1/supplier/orders",
        f"{BASE_URLS['statistics']}/api/v2/supplier/orders",
        f"{BASE_URLS['marketplace']}/api/v1/supplier/orders",
        f"{BASE_URLS['marketplace']}/api/v2/supplier/orders",
        f"{BASE_URLS['marketplace']}/api/v3/supplier/orders"
    ],
    'sales': [
        f"{BASE_URLS['statistics']}/api/v1/supplier/sales",
        f"{BASE_URLS['statistics']}/api/v2/supplier/sales",
        f"{BASE_URLS['marketplace']}/api/v1/supplier/sales",
        f"{BASE_URLS['marketplace']}/api/v2/supplier/sales",
        f"{BASE_URLS['marketplace']}/api/v3/supplier/sales"
    ],
    'stocks': [
        f"{BASE_URLS['statistics']}/api/v1/supplier/stocks",
        f"{BASE_URLS['marketplace']}/api/v1/supplier/stocks",
        f"{BASE_URLS['seller_analytics']}/api/v1/warehouse-stocks"
    ],
    'analytics': [
        f"{BASE_URLS['statistics']}/api/v5/supplier/reportDetailByPeriod",
        f"{BASE_URLS['statistics']}/api/v1/supplier/reportDetailByPeriod",
        f"{BASE_URLS['seller_analytics']}/api/v1/sales-funnel",
        f"{BASE_URLS['seller_analytics']}/api/v1/brand-share",
        f"{BASE_URLS['seller_analytics']}/api/v1/hidden-products"
    ],
    'content': [
        f"{BASE_URLS['marketplace']}/api/lite/products/wb_categories",
        f"{BASE_URLS['content']}/api/v1/cards/list",
        f"{BASE_URLS['content']}/api/v1/cards/filter"
    ],
    'feedbacks': [
        f"{BASE_URLS['feedbacks']}/api/v1/summary",
        f"{BASE_URLS['feedbacks']}/api/v1/feedbacks"
    ],
    'questions': [
        f"{BASE_URLS['questions']}/api/v1/questions",
        f"{BASE_URLS['questions']}/api/v1/questions/count"
    ],
    'promotion': [
        f"{BASE_URLS['seller_analytics']}/api/v1/search-queries/report",
        f"{BASE_URLS['seller_analytics']}/api/v1/search-queries/statistics"
    ],
    'finance': [
        f"{BASE_URLS['statistics']}/api/v1/supplier/incomes",
        f"{BASE_URLS['statistics']}/api/v1/supplier/outcomes",
        f"{BASE_URLS['statistics']}/api/v1/supplier/balance"
    ]
}

def test_all_endpoints_by_category():
    """Тестирование всех endpoints по категориям"""
    results = {}
    
    for category, endpoints in ALL_ENDPOINTS.items():
        st.write(f"🔍 Тестируем {category}...")
        category_results = []
        
        for url in endpoints:
            try:
                # Параметры для тестового запроса
                params = {
                    'dateFrom': (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d'),
                    'dateTo': datetime.now().strftime('%Y-%m-%d')
                }
                
                response = requests.get(url, headers=headers, params=params, timeout=10)
                
                result = {
                    'url': url,
                    'status_code': response.status_code,
                    'success': response.status_code == 200,
                    'response_size': len(response.content) if response.status_code == 200 else 0,
                    'error': None
                }
                
                if response.status_code == 401:
                    result['error'] = 'Ошибка авторизации'
                elif response.status_code == 403:
                    result['error'] = 'Доступ запрещен'
                elif response.status_code == 404:
                    result['error'] = 'Endpoint не найден'
                elif response.status_code == 429:
                    result['error'] = 'Превышен лимит запросов'
                elif response.status_code >= 500:
                    result['error'] = 'Ошибка сервера'
                elif not result['success']:
                    result['error'] = f'HTTP {response.status_code}'
                
                category_results.append(result)
                
            except Exception as e:
                category_results.append({
                    'url': url,
                    'status_code': None,
                    'success': False,
                    'response_size': 0,
                    'error': str(e)
                })
        
        results[category] = category_results
    
    return results

def get_data_from_endpoint(url, params=None):
    """Универсальная функция для получения данных с любого endpoint"""
    try:
        response = requests.get(url, headers=headers, params=params, timeout=15)
        
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 401:
            st.error("❌ Ошибка авторизации. Проверьте API ключ.")
            return None
        elif response.status_code == 403:
            st.warning("⚠️ Доступ запрещен. Проверьте права доступа.")
            return None
        elif response.status_code == 404:
            st.warning("⚠️ Endpoint не найден.")
            return None
        elif response.status_code == 429:
            st.warning("⚠️ Превышен лимит запросов. Попробуйте позже.")
            return None
        else:
            st.warning(f"⚠️ Неожиданный ответ: {response.status_code}")
            return None
            
    except requests.exceptions.RequestException as e:
        st.error(f"❌ Ошибка подключения: {e}")
        return None

def get_orders_data(date_from, date_to):
    """Получение данных о заказах"""
    for url in ALL_ENDPOINTS['orders']:
        params = {
            'dateFrom': date_from.strftime('%Y-%m-%d'),
            'dateTo': date_to.strftime('%Y-%m-%d')
        }
        data = get_data_from_endpoint(url, params)
        if data:
            return data
    return None

def get_sales_data(date_from, date_to):
    """Получение данных о продажах"""
    for url in ALL_ENDPOINTS['sales']:
        params = {
            'dateFrom': date_from.strftime('%Y-%m-%d'),
            'dateTo': date_to.strftime('%Y-%m-%d')
        }
        data = get_data_from_endpoint(url, params)
        if data:
            return data
    return None

def get_stocks_data():
    """Получение данных об остатках"""
    for url in ALL_ENDPOINTS['stocks']:
        data = get_data_from_endpoint(url)
        if data:
            return data
    return None

def get_analytics_data(date_from, date_to):
    """Получение аналитических данных"""
    analytics_data = {}
    
    # Статистика по периоду
    for url in ALL_ENDPOINTS['analytics'][:2]:  # reportDetailByPeriod
        params = {
            'dateFrom': date_from.strftime('%Y-%m-%d'),
            'dateTo': date_to.strftime('%Y-%m-%d'),
            'rrdid': 0,
            'limit': 100000
        }
        data = get_data_from_endpoint(url, params)
        if data:
            analytics_data['report'] = data
            break
    
    # Воронка продаж
    url = ALL_ENDPOINTS['analytics'][2]
    params = {
        'dateFrom': date_from.strftime('%Y-%m-%d'),
        'dateTo': date_to.strftime('%Y-%m-%d')
    }
    data = get_data_from_endpoint(url, params)
    if data:
        analytics_data['funnel'] = data
    
    # Доля бренда
    url = ALL_ENDPOINTS['analytics'][3]
    data = get_data_from_endpoint(url)
    if data:
        analytics_data['brand_share'] = data
    
    # Скрытые товары
    url = ALL_ENDPOINTS['analytics'][4]
    data = get_data_from_endpoint(url)
    if data:
        analytics_data['hidden_products'] = data
    
    return analytics_data

def get_content_data():
    """Получение данных о контенте"""
    content_data = {}
    
    # Категории
    url = ALL_ENDPOINTS['content'][0]
    data = get_data_from_endpoint(url)
    if data:
        content_data['categories'] = data
    
    # Список карточек товаров
    url = ALL_ENDPOINTS['content'][1]
    data = get_data_from_endpoint(url)
    if data:
        content_data['cards'] = data
    
    return content_data

def get_feedbacks_data():
    """Получение данных об отзывах"""
    feedbacks_data = {}
    
    # Сводка по отзывам
    url = ALL_ENDPOINTS['feedbacks'][0]
    data = get_data_from_endpoint(url)
    if data:
        feedbacks_data['summary'] = data
    
    # Детальные отзывы
    url = ALL_ENDPOINTS['feedbacks'][1]
    data = get_data_from_endpoint(url)
    if data:
        feedbacks_data['feedbacks'] = data
    
    return feedbacks_data

def get_questions_data():
    """Получение данных о вопросах"""
    questions_data = {}
    
    # Вопросы
    url = ALL_ENDPOINTS['questions'][0]
    data = get_data_from_endpoint(url)
    if data:
        questions_data['questions'] = data
    
    # Количество вопросов
    url = ALL_ENDPOINTS['questions'][1]
    data = get_data_from_endpoint(url)
    if data:
        questions_data['count'] = data
    
    return questions_data

def get_finance_data():
    """Получение финансовых данных"""
    finance_data = {}
    
    # Поступления
    url = ALL_ENDPOINTS['finance'][0]
    data = get_data_from_endpoint(url)
    if data:
        finance_data['incomes'] = data
    
    # Расходы
    url = ALL_ENDPOINTS['finance'][1]
    data = get_data_from_endpoint(url)
    if data:
        finance_data['outcomes'] = data
    
    # Баланс
    url = ALL_ENDPOINTS['finance'][2]
    data = get_data_from_endpoint(url)
    if data:
        finance_data['balance'] = data
    
    return finance_data

def create_dashboard():
    """Создание расширенного дашборда"""
    st.title("📊 Wildberries API Dashboard (Расширенный)")
    st.markdown("---")
    
    # Информация о доступных данных
    st.info("""
    🚀 **Расширенные возможности API Wildberries:**
    
    📦 **Заказы и продажи** - детальная статистика по заказам и выкупам
    📊 **Аналитика** - воронка продаж, доля бренда, скрытые товары
    📝 **Контент** - управление карточками товаров и категориями
    💬 **Отзывы и вопросы** - работа с обратной связью покупателей
    💰 **Финансы** - поступления, расходы, баланс
    📈 **Продвижение** - поисковые запросы и статистика
    """)
    
    # Боковая панель
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
    
    # Основной контент
    st.subheader("🔍 Тестирование всех endpoints")
    
    if st.button("🚀 Полное тестирование API", type="primary"):
        with st.spinner("Тестируем все endpoints по категориям..."):
            results = test_all_endpoints_by_category()
            
            # Отображение результатов по категориям
            for category, category_results in results.items():
                st.subheader(f"📊 {category.upper()}")
                
                working = [r for r in category_results if r['success']]
                failed = [r for r in category_results if not r['success']]
                
                if working:
                    st.success(f"✅ Рабочих endpoints: {len(working)}")
                    for result in working:
                        st.success(f"  • {result['url']} (размер: {result['response_size']} байт)")
                
                if failed:
                    st.warning(f"⚠️ Нерабочих endpoints: {len(failed)}")
                    for result in failed[:3]:  # Показываем только первые 3
                        st.warning(f"  • {result['url']} - {result['error']}")
                    if len(failed) > 3:
                        st.warning(f"  ... и еще {len(failed) - 3} endpoints")
                
                st.markdown("---")
    
    # Кнопки для получения данных
    st.subheader("📊 Получение данных")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("📦 Заказы и продажи"):
            with st.spinner("Загружаем данные о заказах и продажах..."):
                orders_data = get_orders_data(date_from, date_to)
                sales_data = get_sales_data(date_from, date_to)
                
                if orders_data:
                    st.session_state.orders_data = orders_data
                    st.success("✅ Данные о заказах загружены!")
                else:
                    st.error("❌ Не удалось загрузить данные о заказах")
                
                if sales_data:
                    st.session_state.sales_data = sales_data
                    st.success("✅ Данные о продажах загружены!")
                else:
                    st.error("❌ Не удалось загрузить данные о продажах")
    
    with col2:
        if st.button("📊 Аналитика"):
            with st.spinner("Загружаем аналитические данные..."):
                analytics_data = get_analytics_data(date_from, date_to)
                
                if analytics_data:
                    st.session_state.analytics_data = analytics_data
                    st.success(f"✅ Загружено {len(analytics_data)} типов аналитики!")
                else:
                    st.error("❌ Не удалось загрузить аналитические данные")
    
    with col3:
        if st.button("📝 Контент"):
            with st.spinner("Загружаем данные о контенте..."):
                content_data = get_content_data()
                
                if content_data:
                    st.session_state.content_data = content_data
                    st.success(f"✅ Загружено {len(content_data)} типов контента!")
                else:
                    st.error("❌ Не удалось загрузить данные о контенте")
    
    with col4:
        if st.button("💬 Отзывы и вопросы"):
            with st.spinner("Загружаем отзывы и вопросы..."):
                feedbacks_data = get_feedbacks_data()
                questions_data = get_questions_data()
                
                if feedbacks_data:
                    st.session_state.feedbacks_data = feedbacks_data
                    st.success("✅ Данные об отзывах загружены!")
                
                if questions_data:
                    st.session_state.questions_data = questions_data
                    st.success("✅ Данные о вопросах загружены!")
    
    # Дополнительные кнопки
    col5, col6, col7 = st.columns(3)
    
    with col5:
        if st.button("💰 Финансы"):
            with st.spinner("Загружаем финансовые данные..."):
                finance_data = get_finance_data()
                
                if finance_data:
                    st.session_state.finance_data = finance_data
                    st.success(f"✅ Загружено {len(finance_data)} типов финансовых данных!")
                else:
                    st.error("❌ Не удалось загрузить финансовые данные")
    
    with col6:
        if st.button("📦 Остатки"):
            with st.spinner("Загружаем данные об остатках..."):
                stocks_data = get_stocks_data()
                
                if stocks_data:
                    st.session_state.stocks_data = stocks_data
                    st.success("✅ Данные об остатках загружены!")
                else:
                    st.error("❌ Не удалось загрузить данные об остатках")
    
    with col7:
        if st.button("📈 Продвижение"):
            with st.spinner("Загружаем данные о продвижении..."):
                # Здесь можно добавить функции для продвижения
                st.info("ℹ️ Функция продвижения в разработке")
    
    # Отображение загруженных данных
    st.markdown("---")
    st.subheader("📊 Просмотр данных")
    
    # Создаем вкладки для разных типов данных
    tabs = ["📦 Заказы/Продажи", "📊 Аналитика", "📝 Контент", "💬 Отзывы/Вопросы", "💰 Финансы", "📦 Остатки"]
    
    tab_objects = st.tabs(tabs)
    
    with tab_objects[0]:
        if hasattr(st.session_state, 'orders_data') and st.session_state.orders_data:
            st.write("### Данные о заказах")
            st.json(st.session_state.orders_data)
        
        if hasattr(st.session_state, 'sales_data') and st.session_state.sales_data:
            st.write("### Данные о продажах")
            st.json(st.session_state.sales_data)
    
    with tab_objects[1]:
        if hasattr(st.session_state, 'analytics_data') and st.session_state.analytics_data:
            for key, value in st.session_state.analytics_data.items():
                st.write(f"### {key}")
                st.json(value)
    
    with tab_objects[2]:
        if hasattr(st.session_state, 'content_data') and st.session_state.content_data:
            for key, value in st.session_state.content_data.items():
                st.write(f"### {key}")
                st.json(value)
    
    with tab_objects[3]:
        if hasattr(st.session_state, 'feedbacks_data') and st.session_state.feedbacks_data:
            st.write("### Отзывы")
            st.json(st.session_state.feedbacks_data)
        
        if hasattr(st.session_state, 'questions_data') and st.session_state.questions_data:
            st.write("### Вопросы")
            st.json(st.session_state.questions_data)
    
    with tab_objects[4]:
        if hasattr(st.session_state, 'finance_data') and st.session_state.finance_data:
            for key, value in st.session_state.finance_data.items():
                st.write(f"### {key}")
                st.json(value)
    
    with tab_objects[5]:
        if hasattr(st.session_state, 'stocks_data') and st.session_state.stocks_data:
            st.write("### Остатки")
            st.json(st.session_state.stocks_data)

def main():
    """Главная функция"""
    create_dashboard()

if __name__ == "__main__":
    main()


