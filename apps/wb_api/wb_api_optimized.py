# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import requests
import json
import time
import os
import pickle
from datetime import datetime, timedelta, date
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import threading
from queue import Queue
import re

# Настройка страницы
st.set_page_config(
    page_title="Wildberries API Dashboard (Оптимизированный)",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# API ключ
API_KEY = "eyJhbGciOiJFUzI1NiIsImtpZCI6IjIwMjUwOTA0djEiLCJ0eXAiOiJKV1QifQ.eyJhY2MiOjMsImVudCI6MSwiZXhwIjoxNzgwMDk3OTMxLCJmb3IiOiJzZWxmIiwiaWQiOiIwMTlhY2E0Mi00NDUwLTc5NGYtYTVkMS1lNzk5Nzk1MDcyM2MiLCJpaWQiOjE4MTczODQ1LCJvaWQiOjYyODAzLCJzIjoxNjEyNiwic2lkIjoiOTcyMmFhYTItM2M5My01MTc0LWI2MWUtMzZlZTk2NjhmODczIiwidCI6ZmFsc2UsInVpZCI6MTgxNzM4NDV9.RkaPlIsujPBV1rZkMblz20n9KWwmJnEuMYH7hsfpdzYEF7H2iWaD6b-6k8FIx8s2ZLHqLlnRFjsFarnZchZ-OA"

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
    'finance': {'ttl_hours': 6, 'file': 'cache_finance.pkl'},
    'balance': {'ttl_hours': 3, 'file': 'cache_balance.pkl'}
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

def load_session_dataframe(session_key):
    """Преобразует данные из session_state в DataFrame"""
    data = getattr(st.session_state, session_key, None)
    if not data:
        return None
    try:
        df = pd.DataFrame(data)
        return df
    except ValueError:
        return None

def summarize_orders_data():
    """Возвращает агрегаты по заказам для ИИ"""
    df = load_session_dataframe('orders_data')
    if df is None or df.empty:
        return None
    if 'date' in df.columns:
        df['date'] = pd.to_datetime(df['date'], errors='coerce')
    df['isCancel'] = df.get('isCancel', False)
    df['status'] = df['isCancel'].map({True: 'Отменён', False: 'Завершён'})
    df['netRevenue'] = df.get('finishedPrice', 0)
    summary = {
        'total_orders': len(df),
        'completed': int((df['status'] == 'Завершён').sum()),
        'cancelled': int((df['status'] == 'Отменён').sum()),
        'net': float(df['netRevenue'].sum()),
        'top_warehouses': [],
        'top_articles': []
    }
    if summary['total_orders'] > 0:
        summary['cancel_rate'] = summary['cancelled'] / summary['total_orders']
    else:
        summary['cancel_rate'] = 0.0
    if 'warehouseName' in df.columns:
        top_wh = (
            df.groupby('warehouseName')
            .size()
            .sort_values(ascending=False)
            .head(3)
        )
        summary['top_warehouses'] = list(top_wh.items())
    if 'supplierArticle' in df.columns:
        top_art = (
            df.groupby('supplierArticle')
            .size()
            .sort_values(ascending=False)
            .head(3)
        )
        summary['top_articles'] = list(top_art.items())
    return summary

def summarize_sales_data():
    """Возвращает агрегаты по продажам/возвратам"""
    df = load_session_dataframe('sales_data')
    if df is None or df.empty:
        return None
    if 'date' in df.columns:
        df['date'] = pd.to_datetime(df['date'], errors='coerce')
    df['finishedPrice'] = df.get('finishedPrice', 0)
    df['operationType'] = df['finishedPrice'].apply(lambda x: 'Продажа' if x >= 0 else 'Возврат')
    summary = {
        'total_records': len(df),
        'sales_count': int((df['operationType'] == 'Продажа').sum()),
        'return_count': int((df['operationType'] == 'Возврат').sum()),
        'net_sales': float(df.loc[df['operationType'] == 'Продажа', 'finishedPrice'].sum()),
        'net_returns': float(df.loc[df['operationType'] == 'Возврат', 'finishedPrice'].sum()),
        'avg_price': float(df.loc[df['operationType'] == 'Продажа', 'finishedPrice'].mean() or 0)
    }
    if summary['total_records'] > 0:
        summary['return_rate'] = summary['return_count'] / summary['total_records']
    else:
        summary['return_rate'] = 0.0
    return summary

def summarize_balance_data():
    """Агрегаты по балансу"""
    raw = getattr(st.session_state, 'balance_data', None)
    if not raw:
        return None
    if isinstance(raw, dict) and 'data' in raw:
        raw = raw['data']
    try:
        df = pd.json_normalize(raw)
    except ValueError:
        return None
    summary = {}
    for col in ['availableToWithdraw', 'balance', 'cashToPay', 'inReserve', 'commission']:
        if col in df.columns:
            summary[col] = float(df[col].sum())
    return summary if summary else None

def summarize_finance_data():
    """Агрегаты по фин. отчету"""
    raw = getattr(st.session_state, 'finance_data', None)
    if not raw:
        return None
    if isinstance(raw, dict) and 'data' in raw:
        raw = raw['data']
    try:
        df = pd.DataFrame(raw)
    except ValueError:
        return None
    summary = {'records': len(df)}
    for col in ['ppvz_for_pay', 'forPay', 'ppvz_for_pay_nds', 'commission_percent', 'delivery_rub', 'penalty']:
        if col in df.columns:
            summary[col] = float(df[col].sum())
    return summary

def describe_orders_range(df_orders, start_date, end_date, label):
    """Возвращает текст с количеством заказов за указанный период"""
    if df_orders is None or df_orders.empty or 'date' not in df_orders.columns:
        return None
    start_date = pd.Timestamp(start_date).date()
    end_date = pd.Timestamp(end_date).date()
    mask = (df_orders['date'].dt.date >= start_date) & (df_orders['date'].dt.date <= end_date)
    period_df = df_orders[mask]
    if period_df.empty:
        return f"{label}: заказов нет."
    active = int((~period_df['isCancel']).sum())
    cancelled = int(period_df['isCancel'].sum())
    return (
        f"{label}: {len(period_df)} заказов, "
        f"{active} в работе/выкуп, {cancelled} отмен."
    )

def parse_date_from_prompt(prompt):
    """Пытается извлечь дату из текста запроса"""
    prompt = prompt.strip()
    # dd.mm.yyyy
    match = re.search(r'(\d{1,2})[\./](\d{1,2})[\./](\d{4})', prompt)
    if match:
        day, month, year = map(int, match.groups())
        return date(year, month, day)
    # yyyy-mm-dd
    match = re.search(r'(\d{4})-(\d{1,2})-(\d{1,2})', prompt)
    if match:
        year, month, day = map(int, match.groups())
        return date(year, month, day)
    # dd.mm (текущий год)
    match = re.search(r'(\d{1,2})[\./](\d{1,2})', prompt)
    if match:
        day, month = map(int, match.groups())
        year = datetime.now().year
        return date(year, month, day)
    # dd month (русский)
    months = {
        'январ': 1, 'феврал': 2, 'март': 3, 'апрел': 4, 'мая': 5, 'июн': 6,
        'июл': 7, 'август': 8, 'сентябр': 9, 'октябр': 10, 'ноябр': 11, 'декабр': 12
    }
    match = re.search(r'(\d{1,2})\s+([а-я]+)', prompt)
    if match:
        day = int(match.group(1))
        month_text = match.group(2)
        for key, value in months.items():
            if key in month_text:
                year = datetime.now().year
                return date(year, value, day)
    return None

def generate_ai_response(prompt, orders_summary, sales_summary, balance_summary, finance_summary):
    """Генерирует текст ответа ИИ на основе доступных данных"""
    prompt = prompt or ""
    prompt_lower = prompt.lower()
    sections = []
    today = datetime.now().date()
    
    today_orders_info = ""
    df_orders = load_session_dataframe('orders_data')
    if df_orders is not None and not df_orders.empty and 'date' in df_orders.columns:
        df_orders['date'] = pd.to_datetime(df_orders['date'], errors='coerce')
        df_orders['isCancel'] = df_orders.get('isCancel', False)
        today_orders = df_orders[df_orders['date'].dt.date == today]
        if not today_orders.empty:
            today_orders_info = (
                f"За сегодня ({today.strftime('%d.%m')}): {len(today_orders)} заказов, "
                f"{int((~today_orders['isCancel']).sum())} в работе, "
                f"{int(today_orders['isCancel'].sum())} отменены."
            )
    
    df_sales = load_session_dataframe('sales_data')
    today_sales_info = ""
    if df_sales is not None and not df_sales.empty and 'date' in df_sales.columns:
        df_sales['date'] = pd.to_datetime(df_sales['date'], errors='coerce')
        today_sales = df_sales[df_sales['date'].dt.date == today]
        if not today_sales.empty:
            today_sales_info = (
                f"Продажи за сегодня: {len(today_sales)} записей, "
                f"выручка {today_sales['finishedPrice'].clip(lower=0).sum():,.0f} ₽."
            )
    
    # Если запрос явно про сегодняшние заказы/продажи
    if 'сегодня' in prompt_lower or 'today' in prompt_lower:
        today_parts = []
        if today_orders_info:
            today_parts.append(today_orders_info)
        if today_sales_info:
            today_parts.append(today_sales_info)
        if today_parts:
            sections.append(" ".join(today_parts))
        else:
            sections.append("За сегодня данных пока нет: заказы и продажи ещё не зафиксированы.")
    
    # Запросы про вчера/неделю/конкретную дату
    if df_orders is not None and not df_orders.empty and 'date' in df_orders.columns:
        if 'вчера' in prompt_lower:
            y_day = today - timedelta(days=1)
            text = describe_orders_range(df_orders, y_day, y_day, f"Вчера ({y_day.strftime('%d.%m')})")
            if text:
                sections.append(text)
        if any(keyword in prompt_lower for keyword in ['недел', '7 д', '7д', 'последнюю неделю']):
            start = today - timedelta(days=6)
            text = describe_orders_range(df_orders, start, today, "За последние 7 дней")
            if text:
                sections.append(text)
        asked_date = parse_date_from_prompt(prompt_lower)
        if asked_date:
            text = describe_orders_range(df_orders, asked_date, asked_date, asked_date.strftime('%d.%m.%Y'))
            if text:
                sections.append(text)
    
    if orders_summary:
        tone = "устойчивая динамика" if orders_summary.get('cancel_rate', 0) < 0.1 else "есть тревожные сигналы"
        top_wh = ", ".join(f"{name} ({count})" for name, count in orders_summary.get('top_warehouses', []))
        top_art = ", ".join(f"{name} ({count})" for name, count in orders_summary.get('top_articles', []))
        section = (
            f"📦 **Заказы**: {orders_summary['total_orders']} всего ({tone}), "
            f"{orders_summary['completed']} завершены, {orders_summary['cancelled']} отменены "
            f"(доля {orders_summary.get('cancel_rate', 0):.1%}). Net: {orders_summary['net']:,.0f} ₽."
        )
        if top_wh:
            section += f" Лидируют склады: {top_wh}."
        if top_art and ('артик' in prompt_lower or 'sku' in prompt_lower or 'товар' in prompt_lower):
            section += f" По артикулам впереди: {top_art}."
        sections.append(section)
    
    if sales_summary:
        sales_delta = sales_summary['net_sales'] + sales_summary['net_returns']
        mood = "продажи растут" if sales_delta > 0 else "возвраты давят на выручку"
        section = (
            f"🛒 **Продажи**: {sales_summary['sales_count']} продаж, "
            f"{sales_summary['return_count']} возвратов (доля {sales_summary.get('return_rate', 0):.1%}) — {mood}. "
            f"Net продажи {sales_summary['net_sales']:,.0f} ₽, возвраты {sales_summary['net_returns']:,.0f} ₽, средний чек {sales_summary['avg_price']:,.0f} ₽."
        )
        sections.append(section)
    
    if balance_summary and ('баланс' in prompt_lower or 'выплат' in prompt_lower or 'кэш' in prompt_lower):
        section = "💰 **Баланс**: "
        if 'availableToWithdraw' in balance_summary:
            section += f"к выводу {balance_summary['availableToWithdraw']:,.0f} ₽. "
        if 'inReserve' in balance_summary:
            section += f"в резерве {balance_summary['inReserve']:,.0f} ₽. "
        sections.append(section.strip())
    
    if finance_summary and any(keyword in prompt_lower for keyword in ['фин', 'выплат', 'комис', 'штраф']):
        section = (
            f"📑 **Финансы**: записей {finance_summary.get('records', 0)}, "
        )
        if 'forPay' in finance_summary:
            section += f"к выплате {finance_summary['forPay']:,.0f} ₽. "
        if 'commission_percent' in finance_summary:
            section += f"комиссии {finance_summary['commission_percent']:,.0f} ₽. "
        if 'delivery_rub' in finance_summary:
            section += f"логистика {finance_summary['delivery_rub']:,.0f} ₽. "
        if 'penalty' in finance_summary and finance_summary['penalty'] > 0:
            section += f"штрафы {finance_summary['penalty']:,.0f} ₽."
        sections.append(section.strip())
    
    recommendations = []
    if orders_summary and orders_summary.get('cancel_rate', 0) > 0.25:
        recommendations.append("Отмен больше 25% — сделайте проверку логистики и наличия на складах.")
    if sales_summary and sales_summary.get('return_rate', 0) > 0.2:
        recommendations.append("Возвратов >20% — стоит пересмотреть описание и фото товаров.")
    if balance_summary and balance_summary.get('inReserve', 0) > balance_summary.get('availableToWithdraw', 0):
        recommendations.append("В резерве лежит больше средств, чем доступно к выводу — проверьте зависшие выплаты.")
    if finance_summary and finance_summary.get('penalty', 0) > 0:
        recommendations.append("Есть штрафы — откройте детализацию фин. отчёта и устраните причины.")
    
    if not sections:
        sections.append("Пока нет достаточно данных. Загрузите заказы и продажи, чтобы я мог дать конкретные цифры.")
    
    response = "\n\n".join(sections)
    if recommendations:
        response += "\n\n🔧 **Что можно сделать**:\n" + "\n".join(f"- {rec}" for rec in recommendations)
    
    return response
def get_balance_data(use_cache=True):
    """Получение данных по балансу поставщика"""
    if use_cache:
        cached_data = data_cache.load_cache('balance')
        if cached_data:
            st.info("💰 Используем кешированный баланс")
            return cached_data['data']
    
    url = f"{BASE_URLS['marketplace']}/api/v1/supplier/balance"
    data = make_api_request(url, None, 'marketplace')
    if data and use_cache:
        data_cache.save_cache('balance', data)
    return data

def get_finance_report(date_from, date_to, use_cache=True):
    """Получение финансового отчета с детализацией"""
    if use_cache:
        cached_data = data_cache.load_cache('finance')
        if cached_data:
            st.info("📑 Используем кешированный финансовый отчёт")
            return cached_data['data']
    
    url = f"{BASE_URLS['statistics']}/api/v1/supplier/reportDetailByPeriod"
    params = {
        'dateFrom': date_from.strftime('%Y-%m-%d'),
        'dateTo': date_to.strftime('%Y-%m-%d'),
        'rrdid': 0,
        'limit': 100000
    }
    data = make_api_request(url, params, 'statistics')
    if data and use_cache:
        data_cache.save_cache('finance', data)
    return data

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
            ["Последние 7 дней", "Последние 30 дней", "Последние 90 дней", "Произвольный период"],
            index=1
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
    
    # Автозагрузка ключевых данных
    if (not hasattr(st.session_state, 'orders_data')) or (not st.session_state.orders_data):
        with st.spinner("Автоматически загружаем данные о заказах..."):
            auto_orders = get_orders_data(date_from, date_to, use_cache)
            if auto_orders:
                st.session_state.orders_data = auto_orders
            else:
                st.warning("⚠️ Автозагрузка заказов не удалась. Попробуйте нажать кнопку '📦 Заказы'.")
    
    if (not hasattr(st.session_state, 'sales_data')) or (not st.session_state.sales_data):
        with st.spinner("Автоматически загружаем данные о продажах..."):
            auto_sales = get_sales_data(date_from, date_to, use_cache)
            if auto_sales:
                st.session_state.sales_data = auto_sales
            else:
                st.warning("⚠️ Автозагрузка продаж не удалась. Попробуйте нажать кнопку '🛒 Продажи'.")
    
    # AI агент (вверху страницы)
    st.markdown("---")
    st.header("🤖 AI агент анализа")
    st.caption("Мгновенно отвечает на вопросы по заказам, продажам, балансу и фин. отчётам.")
    orders_summary_ai = summarize_orders_data()
    sales_summary_ai = summarize_sales_data()
    balance_summary_ai = summarize_balance_data()
    finance_summary_ai = summarize_finance_data()
    
    if 'ai_chat_history' not in st.session_state:
        st.session_state.ai_chat_history = []
    
    chat_history = st.session_state.ai_chat_history
    for message in chat_history:
        with st.chat_message(message['role']):
            st.markdown(message['content'])
    
    user_prompt = st.chat_input("Задайте вопрос ИИ-аналитику")
    if user_prompt:
        chat_history.append({"role": "user", "content": user_prompt})
        with st.chat_message("user"):
            st.markdown(user_prompt)
        
        ai_reply = generate_ai_response(user_prompt, orders_summary_ai, sales_summary_ai, balance_summary_ai, finance_summary_ai)
        chat_history.append({"role": "assistant", "content": ai_reply})
        with st.chat_message("assistant"):
            st.markdown(ai_reply)
    
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
                balance_data = get_balance_data(False)
                finance_data = get_finance_report(date_from, date_to, False)
                
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
                if balance_data:
                    st.session_state.balance_data = balance_data
                if finance_data:
                    st.session_state.finance_data = finance_data
                
                st.success("✅ Все данные обновлены!")
    
    col7, col8 = st.columns(2)
    with col7:
        if st.button("💰 Баланс"):
            with st.spinner("Загружаем баланс..."):
                balance_data = get_balance_data(use_cache)
                if balance_data:
                    st.session_state.balance_data = balance_data
                    st.success("✅ Баланс загружен!")
                else:
                    st.error("❌ Не удалось загрузить баланс")
    with col8:
        if st.button("📑 Фин. отчёт"):
            with st.spinner("Загружаем финансовый отчёт..."):
                finance_data = get_finance_report(date_from, date_to, use_cache)
                if finance_data:
                    st.session_state.finance_data = finance_data
                    st.success("✅ Финансовый отчёт загружен!")
                else:
                    st.error("❌ Не удалось загрузить финансовый отчёт")
    
    # Отображение загруженных данных
    st.markdown("---")
    st.subheader("📊 Общие KPI")
    
    orders_df_raw = None
    sales_df_raw = None
    if hasattr(st.session_state, 'orders_data') and st.session_state.orders_data:
        try:
            orders_df_raw = pd.DataFrame(st.session_state.orders_data)
        except ValueError:
            orders_df_raw = None
    if hasattr(st.session_state, 'sales_data') and st.session_state.sales_data:
        try:
            sales_df_raw = pd.DataFrame(st.session_state.sales_data)
        except ValueError:
            sales_df_raw = None
    
    if orders_df_raw is None and sales_df_raw is None:
        st.info("ℹ️ Нет данных для расчёта KPI. Загрузите заказы и продажи.")
    else:
        kpi_col1, kpi_col2, kpi_col3, kpi_col4 = st.columns(4)
        use_orders = kpi_col1.checkbox("Учитывать заказы", True, key="kpi_use_orders")
        use_sales = kpi_col2.checkbox("Учитывать продажи", True, key="kpi_use_sales")
        include_cancellations = kpi_col3.checkbox("Отмены", True, key="kpi_include_cancellations")
        include_returns = kpi_col4.checkbox("Возвраты", True, key="kpi_include_returns")
        
        total_operations = 0
        total_net = 0.0
        total_gmv = 0.0
        
        if use_orders and orders_df_raw is not None and not orders_df_raw.empty:
            orders_df_raw["isCancel"] = orders_df_raw.get("isCancel", False)
            if not include_cancellations:
                orders_df_calc = orders_df_raw[orders_df_raw["isCancel"] == False].copy()
            else:
                orders_df_calc = orders_df_raw.copy()
            orders_df_calc["gmv"] = orders_df_calc.get("priceWithDisc", 0)
            orders_df_calc["netRevenue"] = orders_df_calc.get("finishedPrice", 0)
            
            total_operations += len(orders_df_calc)
            total_gmv += float(orders_df_calc["gmv"].sum())
            total_net += float(orders_df_calc["netRevenue"].sum())
        
        if use_sales and sales_df_raw is not None and not sales_df_raw.empty:
            sales_df_raw["finishedPrice"] = sales_df_raw.get("finishedPrice", 0)
            sales_df_raw["operationType"] = sales_df_raw["finishedPrice"].apply(lambda x: "Продажа" if x >= 0 else "Возврат")
            if not include_returns:
                sales_df_calc = sales_df_raw[sales_df_raw["operationType"] == "Продажа"].copy()
            else:
                sales_df_calc = sales_df_raw.copy()
            sales_df_calc["gmv"] = sales_df_calc.get("priceWithDisc", 0)
            
            total_operations += len(sales_df_calc)
            total_gmv += float(sales_df_calc["gmv"].sum())
            total_net += float(sales_df_calc["finishedPrice"].sum())
        
        if total_operations == 0:
            st.info("ℹ️ По выбранным параметрам нет данных.")
        else:
            gk_cols = st.columns(3)
            gk_cols[0].metric("Всего операций", total_operations)
            gk_cols[1].metric("Net (заказы+продажи)", f"{total_net:,.0f} ₽")
            gk_cols[2].metric("GMV", f"{total_gmv:,.0f} ₽")
    
    st.markdown("---")
    st.subheader("📊 Просмотр данных")
    
    # Создаем вкладки для разных типов данных
    tabs = ["📦 Заказы", "🛒 Продажи", "📦 Остатки", "📊 Аналитика", "📝 Контент", "💰 Баланс", "📑 Финансовый отчёт"]
    
    tab_objects = st.tabs(tabs)
    
    with tab_objects[0]:
        if hasattr(st.session_state, 'orders_data') and st.session_state.orders_data:
            st.write("### 📦 Данные о заказах и KPI")
            
            try:
                orders_df = pd.DataFrame(st.session_state.orders_data)
            except ValueError:
                st.warning("⚠️ Не удалось преобразовать данные в таблицу. Показываем исходный JSON.")
                st.json(st.session_state.orders_data)
                orders_df = None
            
            if orders_df is not None and not orders_df.empty:
                # Подготовка данных
                date_columns = ["date", "lastChangeDate", "cancelDate"]
                for col in date_columns:
                    if col in orders_df.columns:
                        orders_df[col] = pd.to_datetime(orders_df[col], errors='coerce')
                
                orders_df["status"] = orders_df["isCancel"].map({True: "Отменён", False: "Завершён"})
                orders_df["gmv"] = orders_df.get("priceWithDisc", 0)
                orders_df["netRevenue"] = orders_df.get("finishedPrice", 0)
                orders_df["margin"] = orders_df["netRevenue"] - orders_df["gmv"] * 0.15
                
                # Фильтры
                st.subheader("🎯 Фильтры")
                col_f1, col_f2, col_f3 = st.columns(3)
                
                with col_f1:
                    supplier_filter = st.multiselect(
                        "Артикулы",
                        sorted(orders_df["supplierArticle"].dropna().unique()) if "supplierArticle" in orders_df else [],
                        default=None,
                        key="orders_supplier_filter"
                    )
                with col_f2:
                    warehouse_filter = st.multiselect(
                        "Склады",
                        sorted(orders_df["warehouseName"].dropna().unique()) if "warehouseName" in orders_df else [],
                        default=None,
                        key="orders_warehouse_filter"
                    )
                with col_f3:
                    status_filter = st.multiselect(
                        "Статус", options=["Завершён", "Отменён"], default=None, key="orders_status_filter"
                    )
                
                date_min = orders_df["date"].min()
                date_max = orders_df["date"].max()
                if pd.notna(date_min) and pd.notna(date_max):
                    min_dt = date_min.to_pydatetime()
                    max_dt = date_max.to_pydatetime()
                    date_range = st.slider(
                        "Дата заказа",
                        value=(min_dt, max_dt),
                        min_value=min_dt,
                        max_value=max_dt
                    )
                else:
                    date_range = None
                
                filtered_df = orders_df.copy()
                if supplier_filter:
                    filtered_df = filtered_df[filtered_df["supplierArticle"].isin(supplier_filter)]
                if warehouse_filter:
                    filtered_df = filtered_df[filtered_df["warehouseName"].isin(warehouse_filter)]
                if status_filter:
                    filtered_df = filtered_df[filtered_df["status"].isin(status_filter)]
                if date_range:
                    filtered_df = filtered_df[
                        (filtered_df["date"] >= date_range[0]) & (filtered_df["date"] <= date_range[1])
                    ]
                
                if filtered_df.empty:
                    st.warning("⚠️ По выбранным фильтрам данных нет.")
                else:
                    # Подготовка продаж для KPI/графиков с учётом тех же фильтров
                    sales_chart_df = None
                    if hasattr(st.session_state, 'sales_data') and st.session_state.sales_data:
                        try:
                            sales_chart_df = pd.DataFrame(st.session_state.sales_data)
                        except ValueError:
                            sales_chart_df = None
                    
                    if sales_chart_df is not None and not sales_chart_df.empty:
                        if "date" in sales_chart_df.columns:
                            sales_chart_df["date"] = pd.to_datetime(sales_chart_df["date"], errors='coerce')
                        if supplier_filter and "supplierArticle" in sales_chart_df.columns:
                            sales_chart_df = sales_chart_df[sales_chart_df["supplierArticle"].isin(supplier_filter)]
                        if warehouse_filter and "warehouseName" in sales_chart_df.columns:
                            sales_chart_df = sales_chart_df[sales_chart_df["warehouseName"].isin(warehouse_filter)]
                        if date_range and "date" in sales_chart_df.columns:
                            sales_chart_df = sales_chart_df[
                                (sales_chart_df["date"] >= date_range[0]) &
                                (sales_chart_df["date"] <= date_range[1])
                            ]
                        sales_chart_df["operationType"] = sales_chart_df.get("finishedPrice", 0).apply(
                            lambda x: "Продажа" if x >= 0 else "Возврат"
                        )
                        sales_chart_df["gmv"] = sales_chart_df.get("priceWithDisc", 0)
                    else:
                        sales_chart_df = None
                    
                    # KPI (общие)
                    total_orders = len(filtered_df)
                    completed_orders_mask = filtered_df["status"] == "Завершён"
                    canceled_orders_mask = filtered_df["status"] == "Отменён"
                    completed_orders = completed_orders_mask.sum()
                    canceled_orders = canceled_orders_mask.sum()
                    completed_net = filtered_df.loc[completed_orders_mask, "netRevenue"].sum()
                    canceled_net = filtered_df.loc[canceled_orders_mask, "netRevenue"].sum()
                    total_sales = 0
                    total_returns = 0
                    sales_net = 0.0
                    returns_net = 0.0
                    if sales_chart_df is not None and not sales_chart_df.empty:
                        total_sales = (sales_chart_df["operationType"] == "Продажа").sum()
                        total_returns = (sales_chart_df["operationType"] == "Возврат").sum()
                        sales_net = sales_chart_df.loc[sales_chart_df["operationType"] == "Продажа", "finishedPrice"].sum()
                        returns_net = sales_chart_df.loc[sales_chart_df["operationType"] == "Возврат", "finishedPrice"].sum()
                    
                    st.subheader("📌 KPI (заказы + продажи)")
                    kpi_cols = st.columns(5)
                    kpi_cols[0].metric("Всего заказов", total_orders)
                    kpi_cols[1].metric("Завершённые", completed_orders, delta=f"{completed_net:,.0f} ₽")
                    kpi_cols[2].metric("Отмены", canceled_orders, delta=f"{canceled_net:,.0f} ₽")
                    kpi_cols[3].metric("Продажи", total_sales, delta=f"{sales_net:,.0f} ₽")
                    kpi_cols[4].metric("Возвраты", total_returns, delta=f"{returns_net:,.0f} ₽")
                    
                    # Графики
                    st.subheader("📈 Динамика заказов и продаж")
                    combined_series = []
                    
                    orders_timeline = (
                        filtered_df.groupby([filtered_df["date"].dt.date, "status"])
                        .size()
                        .reset_index(name="count")
                        .rename(columns={"date": "event_date"})
                    )
                    if not orders_timeline.empty:
                        orders_timeline["series"] = orders_timeline["status"].apply(lambda x: f"Заказы: {x}")
                        combined_series.append(orders_timeline[["event_date", "series", "count"]])
                    
                    if sales_chart_df is not None and not sales_chart_df.empty:
                        sales_timeline = (
                            sales_chart_df.groupby([sales_chart_df["date"].dt.date, "operationType"])
                            .size()
                            .reset_index(name="count")
                            .rename(columns={"date": "event_date"})
                        )
                        if not sales_timeline.empty:
                            sales_timeline["series"] = sales_timeline["operationType"].apply(lambda x: f"Продажи: {x}")
                            combined_series.append(sales_timeline[["event_date", "series", "count"]])
                    
                    if combined_series:
                        combined_df = pd.concat(combined_series, ignore_index=True)
                        unique_series = combined_df["series"].unique().tolist()
                        series_selection = {}
                        checkbox_cols = st.columns(len(unique_series)) if unique_series else []
                        for series_name, col in zip(unique_series, checkbox_cols):
                            series_selection[series_name] = col.checkbox(series_name, True, key=f"series_{series_name}")
                        selected_series = [name for name, enabled in series_selection.items() if enabled]
                        filtered_series_df = combined_df[combined_df["series"].isin(selected_series)]
                        
                        if not filtered_series_df.empty:
                            fig_timeline = px.line(
                                filtered_series_df,
                                x="event_date",
                                y="count",
                                color="series",
                                markers=True,
                                title="Заказы, продажи и возвраты по датам"
                            )
                            fig_timeline.update_layout(xaxis_title="Дата", yaxis_title="Количество операций")
                            st.plotly_chart(fig_timeline, width="stretch")
                        else:
                            st.info("ℹ️ Выберите хотя бы один параметр для отображения графика.")
                    else:
                        st.info("ℹ️ Нет данных для построения графика.")
                    
                    st.subheader("🏬 Склады и отмены")
                    warehouse_stats = (
                        filtered_df.groupby(["warehouseName", "status"])
                        .size()
                        .reset_index(name="count")
                    )
                    if not warehouse_stats.empty:
                        fig_warehouses = px.bar(
                            warehouse_stats,
                            x="warehouseName",
                            y="count",
                            color="status",
                            text_auto=True,
                            title="Статусы заказов по складам"
                        )
                        fig_warehouses.update_layout(xaxis_title="Склад", yaxis_title="Количество")
                        st.plotly_chart(fig_warehouses, width="stretch")
                    
                    st.subheader("📏 Размеры и статус")
                    if "techSize" in filtered_df.columns:
                        sizes_stats = (
                            filtered_df.groupby(["techSize", "status"])
                            .size()
                            .reset_index(name="count")
                        )
                        if not sizes_stats.empty:
                            fig_sizes = px.bar(
                                sizes_stats,
                                x="techSize",
                                y="count",
                                color="status",
                                barmode="group",
                                text_auto=True,
                                title="Распределение заказов по размерам"
                            )
                            fig_sizes.update_layout(xaxis_title="Размер", yaxis_title="Количество")
                            st.plotly_chart(fig_sizes, width="stretch")
                    
                    st.subheader("📋 Таблица заказов")
                    display_cols = [
                        "date", "lastChangeDate", "warehouseName", "regionName",
                        "supplierArticle", "techSize", "status", "gmv", "netRevenue",
                        "discountPercent", "spp", "sticker", "srid"
                    ]
                    display_cols = [col for col in display_cols if col in filtered_df.columns]
                    st.dataframe(
                        filtered_df[display_cols].sort_values(by="date", ascending=False),
                        use_container_width=True
                    )
                    
                    with st.expander("🧾 Показать исходный JSON"):
                        st.json(st.session_state.orders_data)
            else:
                st.info("ℹ️ Не удалось подготовить таблицу заказов. См. исходный JSON ниже.")
            st.json(st.session_state.orders_data)
        else:
            st.info("ℹ️ Нет данных о заказах. Нажмите '📦 Заказы' для загрузки.")
    
    with tab_objects[1]:
        if hasattr(st.session_state, 'sales_data') and st.session_state.sales_data:
            st.write("### 🛒 Данные о продажах и KPI")
            
            try:
                sales_df = pd.DataFrame(st.session_state.sales_data)
            except ValueError:
                st.warning("⚠️ Не удалось преобразовать продажи в таблицу. Показываем исходный JSON.")
                st.json(st.session_state.sales_data)
                sales_df = None
            
            if sales_df is not None and not sales_df.empty:
                date_cols = ["date", "lastChangeDate"]
                for col in date_cols:
                    if col in sales_df.columns:
                        sales_df[col] = pd.to_datetime(sales_df[col], errors='coerce')
                
                sales_df["operationType"] = sales_df.get("finishedPrice", 0).apply(
                    lambda x: "Возврат" if x < 0 else "Продажа"
                )
                sales_df["gmv"] = sales_df.get("priceWithDisc", 0)
                sales_df["netRevenue"] = sales_df.get("finishedPrice", 0)
                sales_df["payout"] = sales_df.get("forPay", sales_df["netRevenue"])
                
                st.subheader("🎯 Фильтры")
                col_s1, col_s2, col_s3 = st.columns(3)
                with col_s1:
                    sales_supplier_filter = st.multiselect(
                        "Артикулы",
                        sorted(sales_df["supplierArticle"].dropna().unique()) if "supplierArticle" in sales_df else [],
                        default=None,
                        key="sales_supplier_filter"
                    )
                with col_s2:
                    sales_warehouse_filter = st.multiselect(
                        "Склады",
                        sorted(sales_df["warehouseName"].dropna().unique()) if "warehouseName" in sales_df else [],
                        default=None,
                        key="sales_warehouse_filter"
                    )
                with col_s3:
                    sales_operation_filter = st.multiselect(
                        "Тип операции", options=["Продажа", "Возврат"], default=None, key="sales_operation_filter"
                    )
                
                sales_date_min = sales_df["date"].min()
                sales_date_max = sales_df["date"].max()
                if pd.notna(sales_date_min) and pd.notna(sales_date_max):
                    s_min = sales_date_min.to_pydatetime()
                    s_max = sales_date_max.to_pydatetime()
                    sales_date_range = st.slider(
                        "Дата операции",
                        value=(s_min, s_max),
                        min_value=s_min,
                        max_value=s_max
                    )
                else:
                    sales_date_range = None
                
                filtered_sales = sales_df.copy()
                if sales_supplier_filter:
                    filtered_sales = filtered_sales[filtered_sales["supplierArticle"].isin(sales_supplier_filter)]
                if sales_warehouse_filter:
                    filtered_sales = filtered_sales[filtered_sales["warehouseName"].isin(sales_warehouse_filter)]
                if sales_operation_filter:
                    filtered_sales = filtered_sales[filtered_sales["operationType"].isin(sales_operation_filter)]
                if sales_date_range:
                    filtered_sales = filtered_sales[
                        (filtered_sales["date"] >= sales_date_range[0]) &
                        (filtered_sales["date"] <= sales_date_range[1])
                    ]
                
                if filtered_sales.empty:
                    st.warning("⚠️ По выбранным фильтрам продаж нет.")
                else:
                    total_operations = len(filtered_sales)
                    sales_count = (filtered_sales["operationType"] == "Продажа").sum()
                    returns_count = (filtered_sales["operationType"] == "Возврат").sum()
                    returns_share = returns_count / total_operations if total_operations else 0
                    gmv_sales = filtered_sales["gmv"].sum()
                    net_sales = filtered_sales["netRevenue"].sum()
                    payout_total = filtered_sales["payout"].sum()
                    avg_spp_sales = filtered_sales.get("spp", pd.Series(dtype=float)).mean()
                    avg_discount_sales = filtered_sales.get("discountPercent", pd.Series(dtype=float)).mean()
                    
                    st.subheader("📌 KPI по продажам")
                    sales_kpi_cols = st.columns(4)
                    sales_kpi_cols[0].metric("Операций", total_operations, delta=f"возвраты {returns_share:.1%}")
                    sales_kpi_cols[1].metric("Net выручка", f"{net_sales:,.0f} ₽", delta=f"Выплаты {payout_total:,.0f} ₽")
                    sales_kpi_cols[2].metric("GMV", f"{gmv_sales:,.0f} ₽")
                    sales_kpi_cols[3].metric("Средн. скидка / SPP",
                                             f"{avg_discount_sales:.1f}% / {avg_spp_sales:.1f}%"
                                             if not pd.isna(avg_discount_sales) else "—")
                    
                    st.subheader("📈 Динамика операций")
                    sales_timeline = (
                        filtered_sales.groupby([filtered_sales["date"].dt.date, "operationType"])
                        .size()
                        .reset_index(name="count")
                        .rename(columns={"date": "operation_date"})
                    )
                    if not sales_timeline.empty:
                        fig_sales_timeline = px.line(
                            sales_timeline,
                            x="operation_date",
                            y="count",
                            color="operationType",
                            markers=True,
                            title="Продажи vs Возвраты по датам"
                        )
                        st.plotly_chart(fig_sales_timeline, width="stretch")
                    
                    st.subheader("🏷️ Артикулы и маржинальность")
                    article_stats = (
                        filtered_sales.groupby(["supplierArticle", "operationType"])["netRevenue"]
                        .sum()
                        .reset_index()
                    )
                    if not article_stats.empty:
                        fig_articles = px.bar(
                            article_stats,
                            x="supplierArticle",
                            y="netRevenue",
                            color="operationType",
                            text_auto=".0f",
                            title="Net-выручка по артикулам"
                        )
                        fig_articles.update_layout(xaxis_title="Артикул", yaxis_title="Net-выручка, ₽")
                        st.plotly_chart(fig_articles, width="stretch")
                    
                    st.subheader("📋 Таблица продаж")
                    sales_display_cols = [
                        "date", "warehouseName", "regionName", "supplierArticle", "techSize",
                        "operationType", "gmv", "netRevenue", "payout", "discountPercent",
                        "spp", "saleID", "sticker", "srid"
                    ]
                    sales_display_cols = [col for col in sales_display_cols if col in filtered_sales.columns]
                    st.dataframe(
                        filtered_sales[sales_display_cols].sort_values(by="date", ascending=False),
                        use_container_width=True
                    )
                    
                    with st.expander("🧾 Показать исходный JSON (продажи)"):
                        st.json(st.session_state.sales_data)
            else:
                st.info("ℹ️ Не удалось подготовить таблицу продаж. См. JSON ниже.")
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

    with tab_objects[5]:
        if hasattr(st.session_state, 'balance_data') and st.session_state.balance_data:
            st.write("### 💰 Баланс поставщика")
            balance_raw = st.session_state.balance_data
            if isinstance(balance_raw, dict) and 'data' in balance_raw:
                balance_raw = balance_raw['data']
            try:
                balance_df = pd.json_normalize(balance_raw)
            except ValueError:
                st.warning("⚠️ Не удалось преобразовать баланс в таблицу. Показываем исходные данные.")
                st.json(st.session_state.balance_data)
                balance_df = None
            
            if balance_df is not None and not balance_df.empty:
                def pick_sum(df, columns):
                    for col in columns:
                        if col in df.columns:
                            return float(df[col].sum())
                    return None
                
                st.subheader("📌 KPI по балансу")
                metric_plan = [
                    ("Доступно к выводу", ["availableToWithdraw", "balance", "cashToPay"]),
                    ("На удержании", ["inReserve", "hold", "debit"]),
                    ("Комиссии", ["commission", "cashCommission"]),
                    ("В пути", ["inTransit", "futureBalance"])
                ]
                metric_values = [(title, pick_sum(balance_df, cols)) for title, cols in metric_plan]
                metric_values = [item for item in metric_values if item[1] is not None]
                
                if metric_values:
                    metric_cols = st.columns(len(metric_values))
                    for (title, value), col in zip(metric_values, metric_cols):
                        col.metric(title, f"{value:,.0f} ₽")
                else:
                    st.info("ℹ️ Нет числовых колонок для отображения KPI.")
                
                currency_col = None
                for candidate in ["currencyName", "currencyCode"]:
                    if candidate in balance_df.columns:
                        currency_col = candidate
                        break
                amount_col = None
                for candidate in ["availableToWithdraw", "balance", "cashToPay", "amount"]:
                    if candidate in balance_df.columns:
                        amount_col = candidate
                        break
                
                if currency_col and amount_col:
                    st.subheader("💱 Баланс по валютам/кошелькам")
                    currency_stats = (
                        balance_df.groupby(currency_col)[amount_col]
                        .sum()
                        .reset_index()
                        .sort_values(by=amount_col, ascending=False)
                    )
                    fig_balance = px.bar(
                        currency_stats,
                        x=currency_col,
                        y=amount_col,
                        text_auto=".0f",
                        title="Распределение средств"
                    )
                    fig_balance.update_layout(xaxis_title="Валюта/кошелёк", yaxis_title="Сумма, ₽")
                    st.plotly_chart(fig_balance, width="stretch")
                
                st.subheader("📋 Детализация баланса")
                st.dataframe(balance_df, use_container_width=True)
            else:
                st.json(st.session_state.balance_data)
        else:
            st.info("ℹ️ Баланс не загружен. Нажмите '💰 Баланс'.")

    with tab_objects[6]:
        if hasattr(st.session_state, 'finance_data') and st.session_state.finance_data:
            st.write("### 📑 Финансовый отчёт")
            finance_raw = st.session_state.finance_data
            if isinstance(finance_raw, dict) and 'data' in finance_raw:
                finance_raw = finance_raw['data']
            try:
                finance_df = pd.DataFrame(finance_raw)
            except ValueError:
                st.warning("⚠️ Не удалось преобразовать финансовые данные в таблицу. Показываем исходный JSON.")
                st.json(st.session_state.finance_data)
                finance_df = None
            
            if finance_df is not None and not finance_df.empty:
                date_candidates = ["rr_dt", "retail_date", "sale_date", "date", "lastChangeDate"]
                active_date_col = next((col for col in date_candidates if col in finance_df.columns), None)
                if active_date_col:
                    finance_df[active_date_col] = pd.to_datetime(finance_df[active_date_col], errors='coerce')
                
                st.subheader("🎯 Фильтры")
                f_col1, f_col2, f_col3 = st.columns(3)
                with f_col1:
                    finance_article_filter = st.multiselect(
                        "Артикулы",
                        sorted(finance_df["supplierArticle"].dropna().unique()) if "supplierArticle" in finance_df else [],
                        default=None,
                        key="finance_article_filter"
                    )
                with f_col2:
                    finance_subject_filter = st.multiselect(
                        "Предмет",
                        sorted(finance_df["subject_name"].dropna().unique()) if "subject_name" in finance_df else [],
                        default=None,
                        key="finance_subject_filter"
                    )
                with f_col3:
                    finance_warehouse_filter = st.multiselect(
                        "Склад",
                        sorted(finance_df["warehouse_name"].dropna().unique()) if "warehouse_name" in finance_df else [],
                        default=None,
                        key="finance_warehouse_filter"
                    )
                
                if active_date_col and finance_df[active_date_col].notna().any():
                    fin_date_min = finance_df[active_date_col].min().to_pydatetime()
                    fin_date_max = finance_df[active_date_col].max().to_pydatetime()
                    finance_date_range = st.slider(
                        "Дата операции (фин. отчёт)",
                        value=(fin_date_min, fin_date_max),
                        min_value=fin_date_min,
                        max_value=fin_date_max,
                        key="finance_date_slider"
                    )
                else:
                    finance_date_range = None
                
                filtered_finance = finance_df.copy()
                if finance_article_filter:
                    filtered_finance = filtered_finance[filtered_finance["supplierArticle"].isin(finance_article_filter)]
                if finance_subject_filter:
                    filtered_finance = filtered_finance[filtered_finance["subject_name"].isin(finance_subject_filter)]
                if finance_warehouse_filter:
                    filtered_finance = filtered_finance[filtered_finance["warehouse_name"].isin(finance_warehouse_filter)]
                if finance_date_range and active_date_col:
                    filtered_finance = filtered_finance[
                        (filtered_finance[active_date_col] >= finance_date_range[0]) &
                        (filtered_finance[active_date_col] <= finance_date_range[1])
                    ]
                
                if filtered_finance.empty:
                    st.warning("⚠️ По выбранным фильтрам финансовых данных нет.")
                else:
                    def sum_fin(col_names):
                        for col in col_names:
                            if col in filtered_finance.columns:
                                return float(filtered_finance[col].sum())
                        return None
                    
                    operations = len(filtered_finance)
                    payout = sum_fin(["ppvz_for_pay", "forPay", "ppvz_for_pay_nds"])
                    commission = sum_fin(["commission_percent", "ppvz_vw_nds"])
                    logistics = sum_fin(["delivery_rub", "delivery_amount"])
                    penalty = sum_fin(["penalty", "fine"])
                    
                    st.subheader("📌 KPI по фин. отчёту")
                    fin_metrics = []
                    fin_metrics.append(("Записей", operations))
                    if payout is not None:
                        fin_metrics.append(("Начислено к выплате", f"{payout:,.0f} ₽"))
                    if commission is not None:
                        fin_metrics.append(("Комиссии", f"{commission:,.0f} ₽"))
                    if logistics is not None:
                        fin_metrics.append(("Логистика", f"{logistics:,.0f} ₽"))
                    if penalty is not None:
                        fin_metrics.append(("Штрафы/коррекции", f"{penalty:,.0f} ₽"))
                    
                    metric_cols = st.columns(len(fin_metrics)) if fin_metrics else []
                    for (title, value), col in zip(fin_metrics, metric_cols):
                        col.metric(title, value)
                    
                    st.subheader("📈 Net выплаты по артикулам")
                    payout_col = next((c for c in ["ppvz_for_pay", "forPay", "ppvz_for_pay_nds"] if c in filtered_finance.columns), None)
                    if payout_col and "supplierArticle" in filtered_finance.columns:
                        article_payout = (
                            filtered_finance.groupby("supplierArticle")[payout_col]
                            .sum()
                            .reset_index()
                            .sort_values(by=payout_col, ascending=False)
                        )
                        fig_fin_articles = px.bar(
                            article_payout.head(20),
                            x="supplierArticle",
                            y=payout_col,
                            text_auto=".0f",
                            title="ТОП-20 артикулов по выплатам"
                        )
                        fig_fin_articles.update_layout(xaxis_title="Артикул", yaxis_title="Сумма, ₽")
                        st.plotly_chart(fig_fin_articles, width="stretch")
                    
                    st.subheader("📋 Детализация отчёта")
                    display_columns = [
                        active_date_col, "supplierArticle", "subject_name", "brand_name",
                        "warehouse_name", payout_col, "commission_percent", "delivery_rub", "penalty"
                    ]
                    display_columns = [col for col in display_columns if col and col in filtered_finance.columns]
                    if display_columns:
                        st.dataframe(
                            filtered_finance[display_columns].sort_values(by=active_date_col or display_columns[0], ascending=False),
                            use_container_width=True
                        )
                    else:
                        st.dataframe(filtered_finance, use_container_width=True)
                    
                    with st.expander("🧾 Исходный JSON фин. отчёта"):
                        st.json(st.session_state.finance_data)
            else:
                st.info("ℹ️ Финансовые данные пустые. Проверьте период.")
        else:
            st.info("ℹ️ Финансовый отчёт не загружен. Нажмите '📑 Фин. отчёт'.")


def main():
    """Главная функция"""
    create_dashboard()

if __name__ == "__main__":
    main()


