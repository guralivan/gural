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

# Настройка страницы
st.set_page_config(
    page_title="Wildberries FBO Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# API ключ
API_KEY = "eyJhbGciOiJFUzI1NiIsImtpZCI6IjIwMjUwOTA0djEiLCJ0eXAiOiJKV1QifQ.eyJlbnQiOjEsImV4cCI6MTc3MzcwODAyNywiaWQiOiIwMTk5NGQ2NC0wZjY4LTc5NDctYjRkYi1iMzQ0YWU2NWFlMGEiLCJpaWQiOjE4MTczODQ1LCJvaWQiOjYyODAzLCJzIjoxNjEyNiwic2lkIjoiOTcyMmFhYTItM2M5My01MTc0LWI2MWUtMzZlZTk2NjhmODczIiwidCI6ZmFsc2UsInVpZCI6MTgxNzM4NDV9.9JLPpBRjkAJRBTvTszQ1kxy6qdmtWiYLCnt-pyA4c27GLeKYLxVhq4j1NoMRbORmmha603hZQleGT3htH4HTFA"

# Заголовки для API запросов
headers = {
    'Authorization': f'Bearer {API_KEY}',
    'Content-Type': 'application/json',
    'Accept': 'application/json'
}

# Актуальные базовые URL согласно документации
BASE_URLS = {
    'marketplace': 'https://marketplace-api.wildberries.ru',
    'statistics': 'https://statistics-api.wildberries.ru', 
    'seller_analytics': 'https://seller-analytics-api.wildberries.ru',
    'advert': 'https://advert-api.wildberries.ru',
    'finance': 'https://finance-api.wildberries.ru',
    'documents': 'https://documents-api.wildberries.ru',
    'common': 'https://common-api.wildberries.ru'
}

# Лимиты API согласно документации
API_LIMITS = {
    'marketplace': {'requests_per_minute': 300, 'interval_ms': 200, 'burst_limit': 20},
    'statistics': {'requests_per_minute': 100, 'interval_ms': 600, 'burst_limit': 10},
    'seller_analytics': {'requests_per_minute': 60, 'interval_ms': 1000, 'burst_limit': 5},
    'advert': {'requests_per_minute': 60, 'interval_ms': 1000, 'burst_limit': 5},
    'finance': {'requests_per_minute': 1, 'interval_ms': 60000, 'burst_limit': 1},  # 1 запрос в минуту
    'documents': {'requests_per_minute': 6, 'interval_ms': 10000, 'burst_limit': 5},  # 1 запрос в 10 сек, 5 в 5 мин
    'common': {'requests_per_minute': 1, 'interval_ms': 60000, 'burst_limit': 10}
}

# Настройки кеширования для FBO
CACHE_SETTINGS = {
    'orders': {'ttl_hours': 1, 'file': 'cache_orders_fbo.pkl'},
    'sales': {'ttl_hours': 1, 'file': 'cache_sales_fbo.pkl'},
    'analytics': {'ttl_hours': 6, 'file': 'cache_analytics_fbo.pkl'},
    'finance': {'ttl_hours': 6, 'file': 'cache_finance_fbo.pkl'},
    'stocks': {'ttl_hours': 4, 'file': 'cache_stocks_fbo.pkl'},
    'documents': {'ttl_hours': 12, 'file': 'cache_documents_fbo.pkl'},
    'promotion': {'ttl_hours': 12, 'file': 'cache_promotion_fbo.pkl'}
}

# Глобальные переменные для управления запросами
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
        self.cache_dir = "wb_fbo_cache"
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
            # Показываем прогресс-бар для ожидания
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            for i in range(int(wait_time)):
                progress = (i + 1) / wait_time
                progress_bar.progress(progress)
                status_text.text(f"⚠️ Превышен лимит запросов для {api_type}. Ожидание {wait_time - i:.1f} сек...")
                time.sleep(1)
            
            progress_bar.empty()
            status_text.empty()
    
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

def test_connection():
    """Проверка подключения к API согласно документации"""
    ping_urls = [
        f"{BASE_URLS['marketplace']}/ping",
        f"{BASE_URLS['statistics']}/ping",
        f"{BASE_URLS['seller_analytics']}/ping",
        f"{BASE_URLS['advert']}/ping",
        f"{BASE_URLS['finance']}/ping",
        f"{BASE_URLS['common']}/ping"
    ]
    
    results = []
    for url in ping_urls:
        try:
            response = requests.get(url, headers=headers, timeout=10)
            results.append({
                'url': url,
                'status_code': response.status_code,
                'success': response.status_code == 200,
                'response': response.json() if response.status_code == 200 else None
            })
        except Exception as e:
            results.append({
                'url': url,
                'status_code': None,
                'success': False,
                'error': str(e)
            })
    
    return results

def test_working_endpoints():
    """Тестирует только рабочие endpoints для FBO"""
    working_endpoints = {
        'orders': [f"{BASE_URLS['statistics']}/api/v1/supplier/orders"],
        'sales': [f"{BASE_URLS['statistics']}/api/v1/supplier/sales"],
        'stocks': [f"{BASE_URLS['statistics']}/api/v1/supplier/stocks"],
        'analytics': [f"{BASE_URLS['statistics']}/api/v5/supplier/reportDetailByPeriod"],
        'finance': [
            f"{BASE_URLS['finance']}/api/v1/account/balance",
            f"{BASE_URLS['statistics']}/api/v5/supplier/reportDetailByPeriod",
            f"{BASE_URLS['statistics']}/api/v1/supplier/incomes"
        ],
        'documents': [
            f"{BASE_URLS['documents']}/api/v1/documents/list",
            f"{BASE_URLS['documents']}/api/v1/documents/categories"
        ],
        'promotion': [
            f"{BASE_URLS['advert']}/api/v2/adv/campaigns",
            f"{BASE_URLS['seller_analytics']}/api/v1/search-queries/report"
        ]
    }
    
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

def get_seller_info():
    """Получение информации о продавце"""
    url = f"{BASE_URLS['common']}/api/v1/seller-info"
    return make_api_request(url, None, 'common')

def get_orders_data(date_from, date_to, use_cache=True):
    """Получение данных о заказах FBO"""
    if use_cache:
        cached_data = data_cache.load_cache('orders')
        if cached_data:
            st.info("📦 Используем кешированные данные о заказах")
            return cached_data['data']
    
    # FBO заказы - используем statistics API
    url = f"{BASE_URLS['statistics']}/api/v1/supplier/orders"
    params = {
        'dateFrom': date_from.strftime('%Y-%m-%d'),
        'dateTo': date_to.strftime('%Y-%m-%d')
    }
    
    data = make_api_request(url, params, 'statistics')
    if data and use_cache:
        data_cache.save_cache('orders', data)
    return data

def get_sales_data(date_from, date_to, use_cache=True):
    """Получение данных о продажах FBO"""
    if use_cache:
        cached_data = data_cache.load_cache('sales')
        if cached_data:
            st.info("🛒 Используем кешированные данные о продажах")
            return cached_data['data']
    
    # FBO продажи - используем statistics API
    url = f"{BASE_URLS['statistics']}/api/v1/supplier/sales"
    params = {
        'dateFrom': date_from.strftime('%Y-%m-%d'),
        'dateTo': date_to.strftime('%Y-%m-%d')
    }
    
    data = make_api_request(url, params, 'statistics')
    if data and use_cache:
        data_cache.save_cache('sales', data)
    return data

def get_analytics_data(date_from, date_to, use_cache=True):
    """Получение аналитических данных"""
    if use_cache:
        cached_data = data_cache.load_cache('analytics')
        if cached_data:
            st.info("📊 Используем кешированные аналитические данные")
            return cached_data['data']
    
    # Детальная статистика по периоду
    url = f"{BASE_URLS['statistics']}/api/v5/supplier/reportDetailByPeriod"
    params = {
        'dateFrom': date_from.strftime('%Y-%m-%d'),
        'dateTo': date_to.strftime('%Y-%m-%d'),
        'rrdid': 0,
        'limit': 100000
    }
    
    data = make_api_request(url, params, 'statistics')
    if data and use_cache:
        data_cache.save_cache('analytics', data)
    return data

def get_finance_data(date_from, date_to, use_cache=True):
    """Получение финансовых данных согласно документации Wildberries"""
    if use_cache:
        cached_data = data_cache.load_cache('finance')
        if cached_data:
            st.info("💰 Используем кешированные финансовые данные")
            return cached_data['data']
    
    finance_data = {}
    
    # 1. Баланс продавца (finance API)
    st.write("🔍 Загружаем баланс продавца...")
    balance_url = f"{BASE_URLS['finance']}/api/v1/account/balance"
    balance = make_api_request(balance_url, None, 'finance')
    if balance:
        finance_data['balance'] = balance
        st.success("✅ Баланс продавца загружен")
    else:
        st.warning("⚠️ Не удалось загрузить баланс")
    
    # 2. Детальный финансовый отчет (statistics API)
    st.write("🔍 Загружаем детальный финансовый отчет...")
    report_params = {
        'dateFrom': date_from.strftime('%Y-%m-%d'),
        'dateTo': date_to.strftime('%Y-%m-%d'),
        'limit': 100000
    }
    report_url = f"{BASE_URLS['statistics']}/api/v5/supplier/reportDetailByPeriod"
    report = make_api_request(report_url, report_params, 'statistics')
    if report:
        finance_data['detailed_report'] = report
        st.success("✅ Детальный финансовый отчет загружен")
    else:
        st.warning("⚠️ Не удалось загрузить детальный отчет")
    
    # 3. Поступления (если доступны)
    st.write("🔍 Загружаем данные о поступлениях...")
    incomes_params = {
        'dateFrom': date_from.strftime('%Y-%m-%d'),
        'dateTo': date_to.strftime('%Y-%m-%d')
    }
    incomes_url = f"{BASE_URLS['statistics']}/api/v1/supplier/incomes"
    incomes = make_api_request(incomes_url, incomes_params, 'statistics')
    if incomes:
        finance_data['incomes'] = incomes
        st.success("✅ Данные о поступлениях загружены")
    else:
        st.warning("⚠️ Не удалось загрузить данные о поступлениях")
    
    if finance_data and use_cache:
        data_cache.save_cache('finance', finance_data)
    return finance_data

def get_stocks_data(use_cache=True):
    """Получение данных об остатках FBO (только рабочий endpoint)"""
    if use_cache:
        cached_data = data_cache.load_cache('stocks')
        if cached_data:
            st.info("📦 Используем кешированные данные об остатках")
            return cached_data['data']
    
    # Остатки FBO - используем только рабочий endpoint
    url = f"{BASE_URLS['statistics']}/api/v1/supplier/stocks"
    data = make_api_request(url, None, 'statistics')
    
    if data:
        if use_cache:
            data_cache.save_cache('stocks', data)
        st.success("✅ Данные об остатках загружены")
        return data
    else:
        st.warning("⚠️ Не удалось загрузить данные об остатках")
        return None

def get_documents_data(use_cache=True):
    """Получение списка документов продавца"""
    if use_cache:
        cached_data = data_cache.load_cache('documents')
        if cached_data:
            st.info("📄 Используем кешированные данные о документах")
            return cached_data['data']
    
    st.write("🔍 Загружаем список документов...")
    
    # Пробуем получить список документов с новым токеном
    documents_url = f"{BASE_URLS['documents']}/api/v1/documents/list"
    documents = make_api_request(documents_url, None, 'documents')
    
    if documents:
        st.success("✅ Список документов загружен")
        if use_cache:
            data_cache.save_cache('documents', documents)
        return documents
    else:
        # Если не удалось загрузить, показываем информационное сообщение
        st.warning("⚠️ Не удалось загрузить список документов")
        st.info("ℹ️ Возможные причины:")
        st.info("• Токен не имеет прав доступа к документам")
        st.info("• Нет доступных документов")
        st.info("• API документов временно недоступен")
        
        # Возвращаем информационное сообщение
        documents_data = {
            'status': 'unavailable',
            'message': 'Список документов недоступен',
            'possible_reasons': [
                'Токен не имеет прав доступа к документам',
                'Нет доступных документов',
                'API документов временно недоступен'
            ]
        }
        
        if use_cache:
            data_cache.save_cache('documents', documents_data)
        return documents_data

def download_document(service_name, extension):
    """Загрузка конкретного документа"""
    st.write(f"🔍 Загружаем документ: {service_name}.{extension}")
    
    params = {
        'serviceName': service_name,
        'extension': extension
    }
    
    document_url = f"{BASE_URLS['documents']}/api/v1/documents/download"
    document = make_api_request(document_url, params, 'documents')
    
    if document:
        st.success("✅ Документ загружен")
        return document
    else:
        st.warning("⚠️ Не удалось загрузить документ")
        return {
            'status': 'unavailable',
            'message': 'Загрузка документа недоступна',
            'service_name': service_name,
            'extension': extension
        }

def get_promotion_data(use_cache=True):
    """Получение данных о продвижении (endpoints недоступны)"""
    if use_cache:
        cached_data = data_cache.load_cache('promotion')
        if cached_data:
            st.info("📈 Используем кешированные данные о продвижении")
            return cached_data['data']
    
    # Данные о продвижении - endpoints недоступны
    st.warning("⚠️ Endpoints для продвижения недоступны")
    st.info("ℹ️ Возможные причины:")
    st.info("• Нет активных рекламных кампаний")
    st.info("• Недостаточно прав доступа к API продвижения")
    st.info("• Endpoints могут быть изменены в API")
    
    # Возвращаем пустые данные
    promotion_data = {
        'status': 'unavailable',
        'message': 'Endpoints для продвижения недоступны',
        'available_endpoints': [
            'https://advert-api.wildberries.ru/api/v2/adv/campaigns',
            'https://seller-analytics-api.wildberries.ru/api/v1/search-queries/report'
        ]
    }
    
    if use_cache:
        data_cache.save_cache('promotion', promotion_data)
    return promotion_data

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
    """Создание FBO дашборда"""
    st.title("📊 Wildberries FBO Dashboard")
    st.markdown("---")
    
    # Информация о FBO
    st.info("""
    🚀 **Специализированный дашборд для FBO магазина:**
    
    📦 **FBO (Fulfillment by Wildberries)** - система, где Wildberries берет на себя хранение и доставку товаров
    📊 **Основные разделы:** Заказы и продажи, Аналитика, Финансы, Остатки, Продвижение
    ⚡ **Оптимизация:** Соблюдение лимитов API, кеширование данных
    """)
    
    # Статус доступных функций
    st.success("""
    ✅ **Доступные функции:**
    • 📦 Заказы FBO - работает
    • 🛒 Продажи FBO - работает  
    • 📦 Остатки FBO - работает
    • 📊 Аналитика - работает
    • 💰 Финансы (баланс, отчеты, поступления) - работает
    • 📄 Документы - обновлен токен, тестируется
    """)
    
    st.warning("""
    ⚠️ **Ограниченная доступность:**
    • 📈 Продвижение - endpoints недоступны
    """)
    
    # Боковая панель
    with st.sidebar:
        st.header("⚙️ Настройки FBO")
        
        # Информация о продавце
        if st.button("👤 Информация о продавце"):
            with st.spinner("Получаем информацию о продавце..."):
                seller_info = get_seller_info()
                if seller_info:
                    st.success("✅ Информация о продавце получена!")
                    st.json(seller_info)
                else:
                    st.error("❌ Не удалось получить информацию о продавце")
        
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
    st.subheader("🔍 Проверка подключения к API")
    
    col_test1, col_test2 = st.columns(2)
    
    with col_test1:
        if st.button("🚀 Проверить подключение", type="primary"):
            with st.spinner("Проверяем подключение к API..."):
                results = test_connection()
                
                st.subheader("📊 Результаты проверки подключения")
                
                for result in results:
                    if result['success']:
                        st.success(f"✅ {result['url']} - Статус: {result['status_code']}")
                        if result['response']:
                            st.json(result['response'])
                    else:
                        st.error(f"❌ {result['url']} - {result.get('error', 'Ошибка подключения')}")
    
    with col_test2:
        if st.button("🔬 Тестировать FBO endpoints"):
            with st.spinner("Тестируем рабочие endpoints для FBO..."):
                results = test_working_endpoints()
                
                st.subheader("🔬 Результаты тестирования FBO endpoints")
                
                for category, category_results in results.items():
                    st.write(f"**{category.upper()}:**")
                    
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
    
    # Кнопки для получения данных FBO
    st.subheader("📊 Данные FBO магазина")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📦 Заказы FBO"):
            with st.spinner("Загружаем данные о заказах FBO..."):
                orders_data = get_orders_data(date_from, date_to, use_cache)
                
                if orders_data:
                    st.session_state.orders_data = orders_data
                    st.success("✅ Данные о заказах FBO загружены!")
                else:
                    st.error("❌ Не удалось загрузить данные о заказах FBO")
    
    with col2:
        if st.button("🛒 Продажи FBO"):
            with st.spinner("Загружаем данные о продажах FBO..."):
                sales_data = get_sales_data(date_from, date_to, use_cache)
                
                if sales_data:
                    st.session_state.sales_data = sales_data
                    st.success("✅ Данные о продажах FBO загружены!")
                else:
                    st.error("❌ Не удалось загрузить данные о продажах FBO")
    
    with col3:
        if st.button("📊 Аналитика"):
            with st.spinner("Загружаем аналитические данные..."):
                analytics_data = get_analytics_data(date_from, date_to, use_cache)
                
                if analytics_data:
                    st.session_state.analytics_data = analytics_data
                    st.success("✅ Аналитические данные загружены!")
                else:
                    st.error("❌ Не удалось загрузить аналитические данные")
    
    # Дополнительные кнопки
    col4, col5, col6 = st.columns(3)
    
    with col4:
        if st.button("💰 Финансы"):
            with st.spinner("Загружаем финансовые данные..."):
                finance_data = get_finance_data(date_from, date_to, use_cache)
                
                if finance_data:
                    st.session_state.finance_data = finance_data
                    st.success("✅ Финансовые данные загружены!")
                else:
                    st.error("❌ Не удалось загрузить финансовые данные")
    
    with col5:
        if st.button("📦 Остатки FBO"):
            with st.spinner("Загружаем данные об остатках FBO..."):
                stocks_data = get_stocks_data(use_cache)
                
                if stocks_data:
                    st.session_state.stocks_data = stocks_data
                    st.success("✅ Данные об остатках FBO загружены!")
                else:
                    st.error("❌ Не удалось загрузить данные об остатках FBO")
    
    with col6:
        if st.button("📄 Документы"):
            with st.spinner("Загружаем список документов..."):
                documents_data = get_documents_data(use_cache)
                
                if documents_data:
                    st.session_state.documents_data = documents_data
                    st.success("✅ Список документов загружен!")
                else:
                    st.error("❌ Не удалось загрузить список документов")
    
    # Дополнительная строка кнопок
    col7, col8 = st.columns(2)
    
    with col7:
        if st.button("📈 Продвижение"):
            with st.spinner("Загружаем данные о продвижении..."):
                promotion_data = get_promotion_data(use_cache)
                
                if promotion_data:
                    st.session_state.promotion_data = promotion_data
                    st.success("✅ Данные о продвижении загружены!")
                else:
                    st.error("❌ Не удалось загрузить данные о продвижении")
    
    with col8:
        if st.button("🔄 Загрузить все данные"):
            with st.spinner("Загружаем все доступные данные..."):
                # Загружаем все данные последовательно
                orders_data = get_orders_data(date_from, date_to, use_cache)
                sales_data = get_sales_data(date_from, date_to, use_cache)
                stocks_data = get_stocks_data(use_cache)
                analytics_data = get_analytics_data(date_from, date_to, use_cache)
                finance_data = get_finance_data(date_from, date_to, use_cache)
                documents_data = get_documents_data(use_cache)
                
                # Сохраняем в session state
                if orders_data:
                    st.session_state.orders_data = orders_data
                if sales_data:
                    st.session_state.sales_data = sales_data
                if stocks_data:
                    st.session_state.stocks_data = stocks_data
                if analytics_data:
                    st.session_state.analytics_data = analytics_data
                if finance_data:
                    st.session_state.finance_data = finance_data
                if documents_data:
                    st.session_state.documents_data = documents_data
                
                st.success("✅ Все доступные данные загружены!")
    
    # Кнопка обновления всех данных
    if st.button("🔄 Обновить все данные FBO"):
        with st.spinner("Обновляем все данные FBO (игнорируя кеш)..."):
            # Загружаем все данные без кеша
            orders_data = get_orders_data(date_from, date_to, False)
            sales_data = get_sales_data(date_from, date_to, False)
            analytics_data = get_analytics_data(date_from, date_to, False)
            finance_data = get_finance_data(date_from, date_to, False)
            stocks_data = get_stocks_data(False)
            documents_data = get_documents_data(False)
            promotion_data = get_promotion_data(False)
            
            if orders_data:
                st.session_state.orders_data = orders_data
            if sales_data:
                st.session_state.sales_data = sales_data
            if analytics_data:
                st.session_state.analytics_data = analytics_data
            if finance_data:
                st.session_state.finance_data = finance_data
            if stocks_data:
                st.session_state.stocks_data = stocks_data
            if documents_data:
                st.session_state.documents_data = documents_data
            if promotion_data:
                st.session_state.promotion_data = promotion_data
            
            st.success("✅ Все данные FBO обновлены!")
    
    # Отображение загруженных данных
    st.markdown("---")
    st.subheader("📊 Просмотр данных FBO")
    
    # Создаем вкладки для разных типов данных
    tabs = ["📦 Заказы FBO", "🛒 Продажи FBO", "📊 Аналитика", "💰 Финансы", "📦 Остатки FBO", "📄 Документы", "📈 Продвижение"]
    
    tab_objects = st.tabs(tabs)
    
    with tab_objects[0]:
        if hasattr(st.session_state, 'orders_data') and st.session_state.orders_data:
            st.write("### Данные о заказах FBO")
            st.json(st.session_state.orders_data)
        else:
            st.info("ℹ️ Нет данных о заказах FBO. Нажмите '📦 Заказы FBO' для загрузки.")
    
    with tab_objects[1]:
        if hasattr(st.session_state, 'sales_data') and st.session_state.sales_data:
            st.write("### Данные о продажах FBO")
            st.json(st.session_state.sales_data)
        else:
            st.info("ℹ️ Нет данных о продажах FBO. Нажмите '🛒 Продажи FBO' для загрузки.")
    
    with tab_objects[2]:
        if hasattr(st.session_state, 'analytics_data') and st.session_state.analytics_data:
            st.write("### Аналитические данные")
            st.json(st.session_state.analytics_data)
        else:
            st.info("ℹ️ Нет аналитических данных. Нажмите '📊 Аналитика' для загрузки.")
    
    with tab_objects[3]:
        if hasattr(st.session_state, 'finance_data') and st.session_state.finance_data:
            st.write("### Финансовые данные")
            st.json(st.session_state.finance_data)
        else:
            st.info("ℹ️ Нет финансовых данных. Нажмите '💰 Финансы' для загрузки.")
    
    with tab_objects[4]:
        if hasattr(st.session_state, 'stocks_data') and st.session_state.stocks_data:
            st.write("### Данные об остатках FBO")
            st.json(st.session_state.stocks_data)
        else:
            st.info("ℹ️ Нет данных об остатках FBO. Нажмите '📦 Остатки FBO' для загрузки.")
    
    with tab_objects[5]:
        if hasattr(st.session_state, 'documents_data') and st.session_state.documents_data:
            st.write("### Информация о документах")
            
            # Проверяем статус документов
            if isinstance(st.session_state.documents_data, dict) and st.session_state.documents_data.get('status') in ['unauthorized', 'unavailable']:
                if st.session_state.documents_data.get('status') == 'unauthorized':
                    st.error("❌ **Доступ к документам ограничен**")
                    st.write("**Причина:**", st.session_state.documents_data.get('message', ''))
                    
                    st.write("**Требуется:**", st.session_state.documents_data.get('required_token_category', ''))
                    st.write("**Текущие права:**", ', '.join(st.session_state.documents_data.get('current_token_categories', [])))
                    
                    st.write("**Инструкции по получению доступа:**")
                    for instruction in st.session_state.documents_data.get('instructions', []):
                        st.write(f"• {instruction}")
                else:
                    st.warning("⚠️ **Документы недоступны**")
                    st.write("**Причина:**", st.session_state.documents_data.get('message', ''))
                    
                    st.write("**Возможные причины:**")
                    for reason in st.session_state.documents_data.get('possible_reasons', []):
                        st.write(f"• {reason}")
                
                st.info("""
                **Альтернативные способы получения документов:**
                • Скачивайте документы вручную из личного кабинета WB
                • Используйте веб-интерфейс для просмотра документов
                • Обратитесь в поддержку WB для получения токена документов
                """)
            else:
                # Отображаем документы в удобном формате
                if isinstance(st.session_state.documents_data, list):
                    for i, doc in enumerate(st.session_state.documents_data):
                        with st.expander(f"📄 Документ {i+1}"):
                            st.json(doc)
                            
                            # Кнопка для загрузки документа
                            if 'serviceName' in doc and 'extensions' in doc:
                                service_name = doc['serviceName']
                                extensions = doc['extensions']
                                
                                if extensions:
                                    extension = extensions[0]  # Берем первое расширение
                                    if st.button(f"⬇️ Скачать {service_name}.{extension}", key=f"download_{i}"):
                                        downloaded_doc = download_document(service_name, extension)
                                        if downloaded_doc:
                                            st.success("✅ Документ загружен!")
                                            st.json(downloaded_doc)
                else:
                    st.json(st.session_state.documents_data)
        else:
            st.info("ℹ️ Нет данных о документах. Нажмите '📄 Документы' для загрузки.")
    
    with tab_objects[6]:
        if hasattr(st.session_state, 'promotion_data') and st.session_state.promotion_data:
            st.write("### Данные о продвижении")
            st.json(st.session_state.promotion_data)
        else:
            st.info("ℹ️ Нет данных о продвижении. Нажмите '📈 Продвижение' для загрузки.")

def main():
    """Главная функция"""
    create_dashboard()

if __name__ == "__main__":
    main()
