# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import requests
import json
import time
import os
import pickle
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import threading
from queue import Queue

# Настройка страницы
st.set_page_config(
    page_title="Wildberries API Dashboard (Оптимизированный)",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# API ключ
API_KEY = "eyJhbGciOiJFUzI1NiIsImtpZCI6IjIwMjUwNTIwdjEiLCJ0eXAiOiJKV1QifQ.eyJlbnQiOjEsImV4cCI6MTc3MTQ1MzUxOSwiaWQiOiIwMTk4YzcwMy0wMGEyLTdhOTktYTlmMS05NzcxYjg5MThkYjkiLCJpaWQiOjE4MTczODQ1LCJvaWQiOjYyODAzLCJzIjoxMTM4Miwic2lkIjoiOTcyMmFhYTItM2M5My01MTc0LWI2MWUtMzZlZTk2NjhmODczIiwidCI6ZmFsc2UsInVpZCI6MTgxNzM4NDV9.23-CLgZixk3mkxsmfE0qDq4BPlyJw5QWhnXvPCQK0h7qAtDOCxhIzOahhc6uKqveTKvr9NI6IglvBDjHWLqohQ"

# Заголовки для API запросов
headers = {
    'Authorization': f'Bearer {API_KEY}',
    'Content-Type': 'application/json',
    'Accept': 'application/json'
}

# Базовые URL
BASE_URLS = {
    'marketplace': 'https://marketplace-api.wildberries.ru',
    'statistics': 'https://statistics-api.wildberries.ru', 
    'seller_analytics': 'https://seller-analytics-api.wildberries.ru',
    'suppliers': 'https://suppliers-api.wildberries.ru',
    'content': 'https://content-api.wildberries.ru',
    'feedbacks': 'https://feedbacks-api.wildberries.ru',
    'questions': 'https://questions-api.wildberries.ru'
}

# Лимиты API согласно документации
API_LIMITS = {
    'marketplace': {
        'requests_per_minute': 300,
        'interval_ms': 200,
        'burst_limit': 20
    },
    'statistics': {
        'requests_per_minute': 100,
        'interval_ms': 600,
        'burst_limit': 10
    },
    'seller_analytics': {
        'requests_per_minute': 60,
        'interval_ms': 1000,
        'burst_limit': 5
    }
}

# Настройки кеширования
CACHE_SETTINGS = {
    'orders': {'ttl_hours': 1, 'file': 'cache_orders.pkl'},
    'sales': {'ttl_hours': 1, 'file': 'cache_sales.pkl'},
    'stocks': {'ttl_hours': 6, 'file': 'cache_stocks.pkl'},
    'analytics': {'ttl_hours': 24, 'file': 'cache_analytics.pkl'},
    'content': {'ttl_hours': 24, 'file': 'cache_content.pkl'},
    'feedbacks': {'ttl_hours': 12, 'file': 'cache_feedbacks.pkl'},
    'finance': {'ttl_hours': 6, 'file': 'cache_finance.pkl'}
}

# Глобальные переменные для управления запросами
request_queue = Queue()
last_request_time = {}
request_counts = {}

class APIRateLimiter:
    """Класс для управления лимитами API запросов"""
    
    def __init__(self):
        self.limits = API_LIMITS
        self.last_requests = {}
        self.request_counts = {}
    
    def can_make_request(self, api_type):
        """Проверяет, можно ли сделать запрос"""
        if api_type not in self.limits:
            return True
        
        now = time.time()
        limit = self.limits[api_type]
        
        # Сброс счетчика каждую минуту
        if api_type not in self.last_requests:
            self.last_requests[api_type] = now
            self.request_counts[api_type] = 0
        
        if now - self.last_requests[api_type] > 60:
            self.last_requests[api_type] = now
            self.request_counts[api_type] = 0
        
        # Проверка лимита запросов в минуту
        if self.request_counts[api_type] >= limit['requests_per_minute']:
            return False
        
        # Проверка интервала между запросами
        if api_type in last_request_time:
            time_since_last = (now - last_request_time[api_type]) * 1000
            if time_since_last < limit['interval_ms']:
                return False
        
        return True
    
    def record_request(self, api_type):
        """Записывает выполненный запрос"""
        now = time.time()
        last_request_time[api_type] = now
        
        if api_type not in self.request_counts:
            self.request_counts[api_type] = 0
        self.request_counts[api_type] += 1

# Глобальный экземпляр rate limiter
rate_limiter = APIRateLimiter()

class DataCache:
    """Класс для кеширования данных"""
    
    def __init__(self):
        self.cache_dir = "wb_cache"
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)
    
    def get_cache_path(self, cache_type):
        """Получает путь к файлу кеша"""
        return os.path.join(self.cache_dir, CACHE_SETTINGS[cache_type]['file'])
    
    def is_cache_valid(self, cache_type):
        """Проверяет, действителен ли кеш"""
        cache_path = self.get_cache_path(cache_type)
        if not os.path.exists(cache_path):
            return False
        
        # Проверяем время создания файла
        file_time = os.path.getmtime(cache_path)
        ttl_seconds = CACHE_SETTINGS[cache_type]['ttl_hours'] * 3600
        
        return (time.time() - file_time) < ttl_seconds
    
    def load_cache(self, cache_type):
        """Загружает данные из кеша"""
        if not self.is_cache_valid(cache_type):
            return None
        
        try:
            cache_path = self.get_cache_path(cache_type)
            with open(cache_path, 'rb') as f:
                return pickle.load(f)
        except Exception as e:
            st.warning(f"⚠️ Ошибка загрузки кеша {cache_type}: {e}")
            return None
    
    def save_cache(self, cache_type, data):
        """Сохраняет данные в кеш"""
        try:
            cache_path = self.get_cache_path(cache_type)
            with open(cache_path, 'wb') as f:
                pickle.dump({
                    'data': data,
                    'timestamp': time.time(),
                    'ttl_hours': CACHE_SETTINGS[cache_type]['ttl_hours']
                }, f)
        except Exception as e:
            st.warning(f"⚠️ Ошибка сохранения кеша {cache_type}: {e}")

# Глобальный экземпляр кеша
data_cache = DataCache()

def make_api_request(url, params=None, api_type='marketplace', retry_count=3):
    """Выполняет API запрос с учетом лимитов и повторных попыток"""
    
    # Проверяем лимиты
    if not rate_limiter.can_make_request(api_type):
        wait_time = 60 - (time.time() - rate_limiter.last_requests.get(api_type, 0))
        if wait_time > 0:
            st.warning(f"⚠️ Превышен лимит запросов для {api_type}. Ожидание {wait_time:.1f} сек...")
            time.sleep(wait_time)
    
    for attempt in range(retry_count):
        try:
            response = requests.get(url, headers=headers, params=params, timeout=15)
            
            # Записываем запрос
            rate_limiter.record_request(api_type)
            
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
                # Обработка лимитов
                retry_after = response.headers.get('Retry-After', 60)
                st.warning(f"⚠️ Превышен лимит запросов. Повтор через {retry_after} сек...")
                time.sleep(int(retry_after))
                continue
            elif response.status_code >= 500:
                st.warning(f"⚠️ Ошибка сервера ({response.status_code}). Попытка {attempt + 1}/{retry_count}")
                if attempt < retry_count - 1:
                    time.sleep(2 ** attempt)  # Экспоненциальная задержка
                continue
            else:
                st.warning(f"⚠️ Неожиданный ответ: {response.status_code}")
                return None
                
        except requests.exceptions.RequestException as e:
            st.warning(f"⚠️ Ошибка подключения (попытка {attempt + 1}/{retry_count}): {e}")
            if attempt < retry_count - 1:
                time.sleep(2 ** attempt)
            continue
    
    return None

def get_working_endpoints():
    """Определяет рабочие endpoints на основе предыдущих тестов"""
    # Рабочие endpoints (обновляются на основе тестов)
    working_endpoints = {
        'orders': [
            f"{BASE_URLS['statistics']}/api/v1/supplier/orders",
        ],
        'sales': [
            f"{BASE_URLS['statistics']}/api/v1/supplier/sales",
        ],
        'stocks': [
            f"{BASE_URLS['statistics']}/api/v1/supplier/stocks",
        ],
        'analytics': [
            f"{BASE_URLS['statistics']}/api/v5/supplier/reportDetailByPeriod",
        ],
        'content': [
            f"{BASE_URLS['marketplace']}/api/lite/products/wb_categories",
        ]
    }
    return working_endpoints

def get_orders_data(date_from, date_to, use_cache=True):
    """Получение данных о заказах с кешированием"""
    if use_cache:
        cached_data = data_cache.load_cache('orders')
        if cached_data:
            st.info("📦 Используем кешированные данные о заказах")
            return cached_data['data']
    
    working_endpoints = get_working_endpoints()
    for url in working_endpoints['orders']:
        params = {
            'dateFrom': date_from.strftime('%Y-%m-%d'),
            'dateTo': date_to.strftime('%Y-%m-%d')
        }
        data = make_api_request(url, params, 'statistics')
        if data:
            if use_cache:
                data_cache.save_cache('orders', data)
            return data
    return None

def get_sales_data(date_from, date_to, use_cache=True):
    """Получение данных о продажах с кешированием"""
    if use_cache:
        cached_data = data_cache.load_cache('sales')
        if cached_data:
            st.info("🛒 Используем кешированные данные о продажах")
            return cached_data['data']
    
    working_endpoints = get_working_endpoints()
    for url in working_endpoints['sales']:
        params = {
            'dateFrom': date_from.strftime('%Y-%m-%d'),
            'dateTo': date_to.strftime('%Y-%m-%d')
        }
        data = make_api_request(url, params, 'statistics')
        if data:
            if use_cache:
                data_cache.save_cache('sales', data)
            return data
    return None

def get_stocks_data(use_cache=True):
    """Получение данных об остатках с кешированием"""
    if use_cache:
        cached_data = data_cache.load_cache('stocks')
        if cached_data:
            st.info("📦 Используем кешированные данные об остатках")
            return cached_data['data']
    
    working_endpoints = get_working_endpoints()
    for url in working_endpoints['stocks']:
        data = make_api_request(url, None, 'statistics')
        if data:
            if use_cache:
                data_cache.save_cache('stocks', data)
            return data
    return None

def get_analytics_data(date_from, date_to, use_cache=True):
    """Получение аналитических данных с кешированием"""
    if use_cache:
        cached_data = data_cache.load_cache('analytics')
        if cached_data:
            st.info("📊 Используем кешированные аналитические данные")
            return cached_data['data']
    
    working_endpoints = get_working_endpoints()
    for url in working_endpoints['analytics']:
        params = {
            'dateFrom': date_from.strftime('%Y-%m-%d'),
            'dateTo': date_to.strftime('%Y-%m-%d'),
            'rrdid': 0,
            'limit': 100000
        }
        data = make_api_request(url, params, 'statistics')
        if data:
            if use_cache:
                data_cache.save_cache('analytics', data)
            return data
    return None

def get_content_data(use_cache=True):
    """Получение данных о контенте с кешированием"""
    if use_cache:
        cached_data = data_cache.load_cache('content')
        if cached_data:
            st.info("📝 Используем кешированные данные о контенте")
            return cached_data['data']
    
    working_endpoints = get_working_endpoints()
    for url in working_endpoints['content']:
        data = make_api_request(url, None, 'marketplace')
        if data:
            if use_cache:
                data_cache.save_cache('content', data)
            return data
    return None

def test_working_endpoints():
    """Тестирует только рабочие endpoints"""
    working_endpoints = get_working_endpoints()
    results = {}
    
    for category, endpoints in working_endpoints.items():
        st.write(f"🔍 Тестируем {category}...")
        category_results = []
        
        for url in endpoints:
            try:
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
                
                if response.status_code == 200:
                    result['error'] = None
                elif response.status_code == 401:
                    result['error'] = 'Ошибка авторизации'
                elif response.status_code == 403:
                    result['error'] = 'Доступ запрещен'
                elif response.status_code == 404:
                    result['error'] = 'Endpoint не найден'
                elif response.status_code == 429:
                    result['error'] = 'Превышен лимит запросов'
                elif response.status_code >= 500:
                    result['error'] = 'Ошибка сервера'
                else:
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

def clear_cache():
    """Очищает весь кеш"""
    try:
        for cache_type in CACHE_SETTINGS:
            cache_path = data_cache.get_cache_path(cache_type)
            if os.path.exists(cache_path):
                os.remove(cache_path)
        st.success("✅ Кеш очищен!")
    except Exception as e:
        st.error(f"❌ Ошибка очистки кеша: {e}")

def show_cache_status():
    """Показывает статус кеша"""
    st.subheader("📊 Статус кеша")
    
    for cache_type, settings in CACHE_SETTINGS.items():
        cache_path = data_cache.get_cache_path(cache_type)
        
        if os.path.exists(cache_path):
            file_time = os.path.getmtime(cache_path)
            age_hours = (time.time() - file_time) / 3600
            ttl_hours = settings['ttl_hours']
            
            if age_hours < ttl_hours:
                remaining_hours = ttl_hours - age_hours
                st.success(f"✅ {cache_type}: кеш действителен еще {remaining_hours:.1f} часов")
            else:
                st.warning(f"⚠️ {cache_type}: кеш устарел ({age_hours:.1f} часов)")
        else:
            st.info(f"ℹ️ {cache_type}: кеш отсутствует")

def create_dashboard():
    """Создание оптимизированного дашборда"""
    st.title("📊 Wildberries API Dashboard (Оптимизированный)")
    st.markdown("---")
    
    # Информация об оптимизации
    st.info("""
    🚀 **Оптимизированная версия с учетом лимитов API:**
    
    ⚡ **Лимиты API** - соблюдение ограничений запросов
    💾 **Кеширование** - сохранение данных для ускорения работы
    🔄 **Повторные запросы** - автоматические повторы при ошибках
    📊 **Только рабочие endpoints** - использование проверенных URL
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
        
        # Настройки кеширования
        st.subheader("💾 Кеширование")
        use_cache = st.checkbox("Использовать кеш", value=True)
        
        if st.button("🗑️ Очистить кеш"):
            clear_cache()
        
        # Статус кеша
        show_cache_status()
    
    # Основной контент
    st.subheader("🔍 Тестирование рабочих endpoints")
    
    if st.button("🚀 Тестировать рабочие endpoints", type="primary"):
        with st.spinner("Тестируем только рабочие endpoints..."):
            results = test_working_endpoints()
            
            # Отображение результатов
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
                    for result in failed:
                        st.warning(f"  • {result['url']} - {result['error']}")
                
                st.markdown("---")
    
    # Кнопки для получения данных
    st.subheader("📊 Получение данных")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("📦 Заказы"):
            with st.spinner("Загружаем данные о заказах..."):
                orders_data = get_orders_data(date_from, date_to, use_cache)
                
                if orders_data:
                    st.session_state.orders_data = orders_data
                    st.success("✅ Данные о заказах загружены!")
                else:
                    st.error("❌ Не удалось загрузить данные о заказах")
    
    with col2:
        if st.button("🛒 Продажи"):
            with st.spinner("Загружаем данные о продажах..."):
                sales_data = get_sales_data(date_from, date_to, use_cache)
                
                if sales_data:
                    st.session_state.sales_data = sales_data
                    st.success("✅ Данные о продажах загружены!")
                else:
                    st.error("❌ Не удалось загрузить данные о продажах")
    
    with col3:
        if st.button("📦 Остатки"):
            with st.spinner("Загружаем данные об остатках..."):
                stocks_data = get_stocks_data(use_cache)
                
                if stocks_data:
                    st.session_state.stocks_data = stocks_data
                    st.success("✅ Данные об остатках загружены!")
                else:
                    st.error("❌ Не удалось загрузить данные об остатках")
    
    with col4:
        if st.button("📊 Аналитика"):
            with st.spinner("Загружаем аналитические данные..."):
                analytics_data = get_analytics_data(date_from, date_to, use_cache)
                
                if analytics_data:
                    st.session_state.analytics_data = analytics_data
                    st.success("✅ Аналитические данные загружены!")
                else:
                    st.error("❌ Не удалось загрузить аналитические данные")
    
    # Дополнительные кнопки
    col5, col6 = st.columns(2)
    
    with col5:
        if st.button("📝 Контент"):
            with st.spinner("Загружаем данные о контенте..."):
                content_data = get_content_data(use_cache)
                
                if content_data:
                    st.session_state.content_data = content_data
                    st.success("✅ Данные о контенте загружены!")
                else:
                    st.error("❌ Не удалось загрузить данные о контенте")
    
    with col6:
        if st.button("🔄 Обновить все данные"):
            with st.spinner("Обновляем все данные (игнорируя кеш)..."):
                # Загружаем все данные без кеша
                orders_data = get_orders_data(date_from, date_to, False)
                sales_data = get_sales_data(date_from, date_to, False)
                stocks_data = get_stocks_data(False)
                analytics_data = get_analytics_data(date_from, date_to, False)
                content_data = get_content_data(False)
                
                if orders_data:
                    st.session_state.orders_data = orders_data
                if sales_data:
                    st.session_state.sales_data = sales_data
                if stocks_data:
                    st.session_state.stocks_data = stocks_data
                if analytics_data:
                    st.session_state.analytics_data = analytics_data
                if content_data:
                    st.session_state.content_data = content_data
                
                st.success("✅ Все данные обновлены!")
    
    # Отображение загруженных данных
    st.markdown("---")
    st.subheader("📊 Просмотр данных")
    
    # Создаем вкладки для разных типов данных
    tabs = ["📦 Заказы", "🛒 Продажи", "📦 Остатки", "📊 Аналитика", "📝 Контент"]
    
    tab_objects = st.tabs(tabs)
    
    with tab_objects[0]:
        if hasattr(st.session_state, 'orders_data') and st.session_state.orders_data:
            st.write("### Данные о заказах")
            st.json(st.session_state.orders_data)
        else:
            st.info("ℹ️ Нет данных о заказах. Нажмите '📦 Заказы' для загрузки.")
    
    with tab_objects[1]:
        if hasattr(st.session_state, 'sales_data') and st.session_state.sales_data:
            st.write("### Данные о продажах")
            st.json(st.session_state.sales_data)
        else:
            st.info("ℹ️ Нет данных о продажах. Нажмите '🛒 Продажи' для загрузки.")
    
    with tab_objects[2]:
        if hasattr(st.session_state, 'stocks_data') and st.session_state.stocks_data:
            st.write("### Данные об остатках")
            st.json(st.session_state.stocks_data)
        else:
            st.info("ℹ️ Нет данных об остатках. Нажмите '📦 Остатки' для загрузки.")
    
    with tab_objects[3]:
        if hasattr(st.session_state, 'analytics_data') and st.session_state.analytics_data:
            st.write("### Аналитические данные")
            st.json(st.session_state.analytics_data)
        else:
            st.info("ℹ️ Нет аналитических данных. Нажмите '📊 Аналитика' для загрузки.")
    
    with tab_objects[4]:
        if hasattr(st.session_state, 'content_data') and st.session_state.content_data:
            st.write("### Данные о контенте")
            st.json(st.session_state.content_data)
        else:
            st.info("ℹ️ Нет данных о контенте. Нажмите '📝 Контент' для загрузки.")

def main():
    """Главная функция"""
    create_dashboard()

if __name__ == "__main__":
    main()


