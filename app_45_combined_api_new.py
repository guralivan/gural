# -*- coding: utf-8 -*-
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import json
import os
import requests
import numpy as np

# Настройка страницы
st.set_page_config(page_title="🚀 Wildberries Analytics Dashboard", layout="wide")

# Конфигурация API (обновлено согласно актуальной документации)
API_KEY = "eyJhbGciOiJFUzI1NiIsImtpZCI6IjIwMjUwNTIwdjEiLCJ0eXAiOiJKV1QifQ.eyJlbnQiOjEsImV4cCI6MTc3MjY3OTM1MCwiaWQiOiIwMTk5MTAxMy1iMTBmLTc3NDItYTRmZS01MDhkZDc1OWI4MmIiLCJpaWQiOjE4MTczODQ1LCJvaWQiOjYyODAzLCJzIjoxMDM0MCwic2lkIjoiOTcyMmFhYTItM2M5My01MTc0LWI2MWUtMzZlZTk2NjhmODczIiwidCI6ZmFsc2UsInVpZCI6MTgxNzM4NDV9.9TcWM0HFJIsLRgRyuNsiD5D8x_dTyqdZwT9eYwqZLNIzRWwP-_RzpIEpKQeq8CJfYrrxkXpq8QTjctdwmPRNHA"

# Актуальные базовые URL для API Wildberries (обновлено с 15.04.2025)
BASE_URLS = {
    'marketplace': 'https://marketplace-api.wildberries.ru',
    'statistics': 'https://statistics-api.wildberries.ru', 
    'seller_analytics': 'https://seller-analytics-api.wildberries.ru',
    'suppliers': 'https://suppliers-api.wildberries.ru'
}

# Обновленные заголовки с Bearer токеном
headers = {
    'Authorization': f'Bearer {API_KEY}',
    'Content-Type': 'application/json',
    'Accept': 'application/json'
}

# Функции для работы с API
@st.cache_data(ttl=7200)  # Кеширование на 2 часа
def get_data_from_api(endpoint, params=None):
    """Получение данных с API через прокси"""
    try:
        # Используем актуальные базовые URL вместо прокси
        base_url = BASE_URLS.get('marketplace', BASE_URLS['marketplace'])
        url = f"{base_url}{endpoint}"
        if params:
            query_string = "&".join([f"{k}={v}" for k, v in params.items()])
            url += f"?{query_string}"
        
        response = requests.get(url, headers=headers, timeout=30)
        
        if response.status_code == 200:
            try:
                data = response.json()
                return data
            except Exception as e:
                st.error(f"❌ Ошибка парсинга JSON: {e}")
                return None
        elif response.status_code == 401:
            st.error("❌ Ошибка авторизации API. Проверьте токен.")
            return None
        elif response.status_code == 404:
            st.error(f"❌ Эндпоинт {endpoint} не найден (404).")
            return None
        elif response.status_code == 400:
            st.error(f"❌ Неверный запрос (400). Проверьте параметры: {params}")
            return None
        elif response.status_code == 429:
            st.error("❌ Слишком много запросов (429). Попробуйте позже.")
            return None
        else:
            st.error(f"❌ Ошибка API: {response.status_code}")
            return None
            
    except requests.exceptions.Timeout:
        st.error("❌ Таймаут запроса. Сервер не отвечает.")
        return None
    except requests.exceptions.ConnectionError:
        st.error("❌ Ошибка подключения к серверу.")
        return None
    except Exception as e:
        st.error(f"❌ Неожиданная ошибка: {str(e)}")
        return None

# Новые функции для получения данных с новых эндпоинтов
@st.cache_data(ttl=7200)
def get_sales_funnel(date_from, date_to):
    """Получение данных воронки продаж"""
    params = {'dateFrom': date_from, 'dateTo': date_to}
    return get_data_from_api('/api/v1/sales-funnel', params)

@st.cache_data(ttl=7200)
def get_orders_data(date_from, date_to):
    """Получение данных заказов"""
    params = {'dateFrom': date_from, 'dateTo': date_to}
    return get_data_from_api('/api/v1/supplier/orders', params)

@st.cache_data(ttl=7200)
def get_sales_data(date_from, date_to):
    """Получение данных продаж"""
    params = {'dateFrom': date_from, 'dateTo': date_to}
    return get_data_from_api('/api/v1/supplier/sales', params)

@st.cache_data(ttl=7200)
def get_report_detail_data(date_from, date_to):
    """Получение детальной статистики по периодам"""
    params = {'dateFrom': date_from, 'dateTo': date_to}
    return get_data_from_api('/api/v5/supplier/reportDetailByPeriod', params)

@st.cache_data(ttl=7200)
def get_stocks_data():
    """Получение данных остатков"""
    return get_data_from_api('/api/v3/supplies/stocks')

@st.cache_data(ttl=7200)
def get_supplies_data():
    """Получение данных поставок"""
    return get_data_from_api('/api/v3/supplies')

@st.cache_data(ttl=7200)
def get_returns_data():
    """Получение данных возвратов"""
    return get_data_from_api('/api/v1/supplier/returns')

@st.cache_data(ttl=7200)
def get_categories_data():
    """Получение категорий товаров"""
    return get_data_from_api('/api/lite/products/wb_categories')

@st.cache_data(ttl=7200)
def get_search_queries_data():
    """Получение поисковых запросов"""
    return get_data_from_api('/api/v1/search-queries')

@st.cache_data(ttl=7200)
def get_hidden_products_data():
    """Получение скрытых товаров"""
    return get_data_from_api('/api/v1/hidden-products')

@st.cache_data(ttl=7200)
def get_brand_share_data():
    """Получение доли бренда"""
    return get_data_from_api('/api/v1/brand-share')

# Функции для работы с Excel файлами
def save_data_cache(data, filename="data_cache.csv"):
    """Сохранение данных в кеш"""
    try:
        if isinstance(data, pd.DataFrame):
            data.to_csv(filename, index=False, encoding='utf-8-sig')
        else:
            pd.DataFrame(data).to_csv(filename, index=False, encoding='utf-8-sig')
        return True
    except Exception as e:
        st.error(f"Ошибка сохранения кеша: {e}")
        return False

def load_data_cache(filename="data_cache.csv"):
    """Загрузка данных из кеша"""
    try:
        if os.path.exists(filename):
            return pd.read_csv(filename, encoding='utf-8-sig')
        return None
    except Exception as e:
        st.error(f"Ошибка загрузки кеша: {e}")
        return None

def process_uploaded_excel_file(uploaded_file):
    """Обработка загруженного Excel файла"""
    try:
        if uploaded_file.name.endswith('.xlsx'):
            df = pd.read_excel(uploaded_file, engine='openpyxl')
        elif uploaded_file.name.endswith('.xls'):
            df = pd.read_excel(uploaded_file, engine='xlrd')
        else:
            st.error("Поддерживаются только файлы .xlsx и .xls")
            return None
        
        # Автоматическое определение полей
        date_fields = []
        numeric_fields = []
        text_fields = []
        
        for col in df.columns:
            if df[col].dtype == 'object':
                # Пытаемся определить даты
                try:
                    pd.to_datetime(df[col].iloc[:10], errors='coerce')
                    date_fields.append(col)
                except:
                    text_fields.append(col)
            elif df[col].dtype in ['int64', 'float64']:
                numeric_fields.append(col)
        
        return {
            'data': df,
            'date_fields': date_fields,
            'numeric_fields': numeric_fields,
            'text_fields': text_fields
        }
    except Exception as e:
        st.error(f"Ошибка обработки файла: {e}")
        return None

def create_summary_stats(data):
    """Создание сводной статистики"""
    if not data or not isinstance(data, pd.DataFrame):
        return None
    
    summary = {}
    
    # Основные метрики
    if 'Заказали, шт' in data.columns:
        summary['total_orders'] = data['Заказали, шт'].sum()
    if 'Выкупили, шт' in data.columns:
        summary['total_sales'] = data['Выкупили, шт'].sum()
    if 'Выкупили на сумму, ₽' in data.columns:
        summary['total_revenue'] = data['Выкупили на сумму, ₽'].sum()
    
    # Процент выкупа
    if 'Заказали, шт' in data.columns and 'Выкупили, шт' in data.columns:
        total_ordered = data['Заказали, шт'].sum()
        total_sold = data['Выкупили, шт'].sum()
        if total_ordered > 0:
            summary['conversion_rate'] = (total_sold / total_ordered) * 100
    
    return summary

def main():
    st.title("🚀 Wildberries Analytics Dashboard")
    st.markdown("---")
    
    # Боковая панель для настройки
    st.sidebar.header("⚙️ Настройки")
    
    # Выбор источника данных
    data_source = st.sidebar.selectbox(
        "📊 Источник данных",
        ["Excel файл", "API Wildberries", "Комбинированный"]
    )
    
    # Настройки дат для API
    if data_source in ["API Wildberries", "Комбинированный"]:
        st.sidebar.subheader("📅 Период данных")
        date_from = st.sidebar.date_input("От", value=datetime.now() - timedelta(days=30))
        date_to = st.sidebar.date_input("До", value=datetime.now())
        
        # Преобразование в строку для API
        date_from_str = date_from.strftime('%Y-%m-%d')
        date_to_str = date_to.strftime('%Y-%m-%d')
    
    # Основной контент
    if data_source == "Excel файл":
        st.header("📁 Загрузка Excel файла")
        
        uploaded_file = st.file_uploader(
            "Выберите файл Excel (.xlsx или .xls)",
            type=['xlsx', 'xls']
        )
        
        if uploaded_file is not None:
            result = process_uploaded_excel_file(uploaded_file)
            if result:
                st.success("✅ Файл успешно загружен!")
                
                # Показываем данные
                st.subheader("📋 Данные из файла")
                st.dataframe(result['data'].head(100))
                
                # Сводная статистика
                summary = create_summary_stats(result['data'])
                if summary:
                    st.subheader("📊 Сводная статистика")
                    col1, col2, col3, col4 = st.columns(4)
                    
                    if 'total_orders' in summary:
                        col1.metric("Заказов", f"{summary['total_orders']:,}")
                    if 'total_sales' in summary:
                        col2.metric("Продаж", f"{summary['total_sales']:,}")
                    if 'total_revenue' in summary:
                        col3.metric("Выручка", f"{summary['total_revenue']:,.0f} ₽")
                    if 'conversion_rate' in summary:
                        col4.metric("Конверсия", f"{summary['conversion_rate']:.1f}%")
    
    elif data_source == "API Wildberries":
        st.header("🌐 Данные API Wildberries")
        
        # Тестирование подключения
        if st.button("🧪 Тестировать подключение"):
            st.info("Проверяем доступность эндпоинтов...")
            
            # Тестируем основные эндпоинты
            endpoints = [
                ('Заказы', '/api/v1/supplier/orders'),
                ('Воронка продаж', '/api/v1/sales-funnel'),
                ('Детальная статистика', '/api/v5/supplier/reportDetailByPeriod')
            ]
            
            for name, endpoint in endpoints:
                with st.spinner(f"Проверяем {name}..."):
                    if endpoint == '/api/v1/sales-funnel':
                        data = get_sales_funnel(date_from_str, date_to_str)
                    elif endpoint == '/api/v1/supplier/orders':
                        data = get_orders_data(date_from_str, date_to_str)
                    elif endpoint == '/api/v5/supplier/reportDetailByPeriod':
                        data = get_report_detail_data(date_from_str, date_to_str)
                    
                    if data:
                        st.success(f"✅ {name}: Данные получены")
                        if isinstance(data, list):
                            st.info(f"📊 Записей: {len(data)}")
                        elif isinstance(data, dict):
                            st.info(f"📊 Ключи: {list(data.keys())}")
                    else:
                        st.error(f"❌ {name}: Ошибка получения данных")
        
        # Загрузка данных
        if st.button("📥 Загрузить данные API"):
            with st.spinner("Загружаем данные..."):
                
                # Загружаем воронку продаж
                funnel_data = get_sales_funnel(date_from_str, date_to_str)
                if funnel_data:
                    st.success("✅ Воронка продаж загружена")
                    st.json(funnel_data)
                
                # Загружаем заказы
                orders_data = get_orders_data(date_from_str, date_to_str)
                if orders_data:
                    st.success("✅ Заказы загружены")
                    if isinstance(orders_data, list):
                        st.info(f"📊 Загружено {len(orders_data)} заказов")
                        # Показываем первые записи
                        df_orders = pd.DataFrame(orders_data)
                        st.dataframe(df_orders.head(10))
                
                # Загружаем детальную статистику
                report_data = get_report_detail_data(date_from_str, date_to_str)
                if report_data:
                    st.success("✅ Детальная статистика загружена")
                    if isinstance(report_data, list):
                        st.info(f"📊 Загружено {len(report_data)} записей")
                        # Показываем первые записи
                        df_report = pd.DataFrame(report_data)
                        st.dataframe(df_report.head(10))
    
    elif data_source == "Комбинированный":
        st.header("🔄 Комбинированный анализ")
        st.info("Загружаем данные из Excel и API для комплексного анализа")
        
        # Загрузка Excel
        uploaded_file = st.file_uploader(
            "📁 Выберите Excel файл",
            type=['xlsx', 'xls']
        )
        
        excel_data = None
        if uploaded_file is not None:
            result = process_uploaded_excel_file(uploaded_file)
            if result:
                excel_data = result['data']
                st.success("✅ Excel файл загружен")
        
        # Загрузка API данных
        api_data = {}
        if st.button("🌐 Загрузить данные API"):
            with st.spinner("Загружаем данные API..."):
                
                # Воронка продаж
                funnel_data = get_sales_funnel(date_from_str, date_to_str)
                if funnel_data:
                    api_data['funnel'] = funnel_data
                    st.success("✅ Воронка продаж загружена")
                
                # Заказы
                orders_data = get_orders_data(date_from_str, date_to_str)
                if orders_data:
                    api_data['orders'] = orders_data
                    st.success("✅ Заказы загружены")
                
                # Детальная статистика
                report_data = get_report_detail_data(date_from_str, date_to_str)
                if report_data:
                    api_data['report'] = report_data
                    st.success("✅ Детальная статистика загружена")
        
        # Комбинированный анализ
        if excel_data is not None and api_data:
            st.subheader("📊 Комбинированный анализ")
            
            # Сравнение данных
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("📁 Данные Excel:")
                if excel_data is not None:
                    st.write(f"Записей: {len(excel_data)}")
                    st.write(f"Колонки: {list(excel_data.columns)}")
            
            with col2:
                st.write("🌐 Данные API:")
                for key, data in api_data.items():
                    if isinstance(data, list):
                        st.write(f"{key}: {len(data)} записей")
                    elif isinstance(data, dict):
                        st.write(f"{key}: {list(data.keys())}")
    
    # Информация о кеше
    st.sidebar.markdown("---")
    st.sidebar.subheader("💾 Кеш данных")
    
    if st.sidebar.button("🗑️ Очистить кеш"):
        st.cache_data.clear()
        st.sidebar.success("✅ Кеш очищен")
    
    # Информация о приложении
    st.sidebar.markdown("---")
    st.sidebar.subheader("ℹ️ О приложении")
    st.sidebar.info("""
    **Wildberries Analytics Dashboard**
    
    Версия: 2.0
    Источники данных:
    - Excel файлы
    - Wildberries API
    - Комбинированный анализ
    
    Поддерживаемые эндпоинты:
    - Воронка продаж
    - Заказы
    - Детальная статистика
    - И другие...
    """)

if __name__ == "__main__":
    main()


