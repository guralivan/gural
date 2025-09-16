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
import requests
import time
import uuid

# Настройка страницы
st.set_page_config(
    page_title="WB Analytics - Полная аналитика",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ================= API НАСТРОЙКИ =================

# API ключ
API_KEY = "eyJhbGciOiJFUzI1NiIsImtpZCI6IjIwMjUwOTA0djEiLCJ0eXAiOiJKV1QifQ.eyJlbnQiOjEsImV4cCI6MTc3MzcwODAyNywiaWQiOiIwMTk5NGQ2NC0wZjY4LTc5NDctYjRkYi1iMzQ0YWU2NWFlMGEiLCJpaWQiOjE4MTczODQ1LCJvaWQiOjYyODAzLCJzIjoxNjEyNiwic2lkIjoiOTcyMmFhYTItM2M5My01MTc0LWI2MWUtMzZlZTk2NjhmODczIiwidCI6ZmFsc2UsInVpZCI6MTgxNzM4NDV9.9JLPpBRjkAJRBTvTszQ1kxy6qdmtWiYLCnt-pyA4c27GLeKYLxVhq4j1NoMRbORmmha603hZQleGT3htH4HTFA"

# Заголовки для API запросов
headers = {
    'Authorization': f'Bearer {API_KEY}',
    'Content-Type': 'application/json',
    'Accept': 'application/json'
}

# Базовые URL для API
BASE_URLS = {
    'seller_analytics': 'https://seller-analytics-api.wildberries.ru',
    'statistics': 'https://statistics-api.wildberries.ru',
    'finance': 'https://finance-api.wildberries.ru',
    'documents': 'https://documents-api.wildberries.ru'
}

# Лимиты API
API_LIMITS = {
    'seller_analytics': {'requests_per_minute': 3, 'interval_ms': 20000, 'burst_limit': 3},
    'statistics': {'requests_per_minute': 100, 'interval_ms': 600, 'burst_limit': 10},
    'finance': {'requests_per_minute': 1, 'interval_ms': 60000, 'burst_limit': 1},
    'documents': {'requests_per_minute': 6, 'interval_ms': 10000, 'burst_limit': 5}
}

# Глобальные переменные для управления запросами
last_request_time = {}
request_counts = {}

# ================= API ФУНКЦИИ =================

def make_api_request(url, params=None, api_type='seller_analytics', method='GET', data=None):
    """Выполняет API запрос с соблюдением лимитов"""
    now = time.time()
    
    # Проверяем лимиты
    if api_type in API_LIMITS:
        limit = API_LIMITS[api_type]
        if api_type in last_request_time:
            time_since_last = now - last_request_time[api_type]
            if time_since_last < limit['interval_ms'] / 1000:
                wait_time = limit['interval_ms'] / 1000 - time_since_last
                st.info(f"⏳ Ожидание {wait_time:.1f} сек для соблюдения лимитов API...")
                time.sleep(wait_time)
        
        last_request_time[api_type] = time.time()
    
    try:
        if method == 'POST':
            response = requests.post(url, headers=headers, json=data, timeout=30)
        else:
            response = requests.get(url, headers=headers, params=params, timeout=30)
        
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 403:
            # Специальная обработка ошибки 403
            try:
                error_data = response.json()
                if "Report not available" in error_data.get('detail', ''):
                    st.error("❌ Ошибка доступа: Отчет недоступен")
                    st.warning("⚠️ **Требуется подписка 'Джем'**")
                    st.info("💡 **Для доступа к CSV отчетам необходимо:**")
                    st.info("• Оформить подписку 'Джем' в личном кабинете WB")
                    st.info("• Использовать альтернативные методы аналитики")
                    st.info("• Обратиться в поддержку WB: dev-info@rwb.ru")
                else:
                    st.error(f"❌ Ошибка авторизации: {error_data.get('detail', 'Неизвестная ошибка')}")
            except:
                st.error(f"❌ Ошибка API: {response.status_code} - {response.text}")
            return None
        elif response.status_code == 429:
            st.warning("⚠️ Превышен лимит запросов. Ожидание...")
            time.sleep(60)  # Ждем минуту
            return make_api_request(url, params, api_type, method, data)  # Повторяем запрос
        else:
            st.error(f"❌ Ошибка API: {response.status_code} - {response.text}")
            return None
            
    except requests.exceptions.RequestException as e:
        st.error(f"❌ Ошибка подключения: {e}")
        return None

def get_product_statistics_period(brand_names=None, object_ids=None, tag_ids=None, nm_ids=None, 
                                 start_date=None, end_date=None, timezone="Europe/Moscow"):
    """Получает статистику карточек товаров за период"""
    st.write("🔍 Загружаем статистику карточек товаров за период...")
    
    # Генерируем UUID для запроса
    request_id = str(uuid.uuid4())
    
    # Подготавливаем данные запроса
    request_data = {
        "id": request_id,
        "reportType": "DETAIL_HISTORY_REPORT",
        "userReportName": f"Product Statistics {start_date} - {end_date}",
        "params": {
            "brandNames": brand_names or [],
            "objectIDs": object_ids or [],
            "tagIDs": tag_ids or [],
            "nmIDs": nm_ids or [],
            "startDate": start_date,
            "endDate": end_date,
            "timezone": timezone,
            "aggregationLevel": "day",
            "skipDeletedNm": False
        }
    }
    
    url = f"{BASE_URLS['seller_analytics']}/api/v2/nm-report/downloads"
    response = make_api_request(url, method='POST', data=request_data, api_type='seller_analytics')
    
    if response and response.get('data') == 'Created':
        st.success(f"✅ Запрос на создание отчета создан (ID: {request_id})")
        return request_id
    else:
        # Проверяем, является ли ошибка связанной с подпиской
        st.error("❌ Не удалось создать запрос на отчет")
        st.warning("⚠️ Возможные причины:")
        st.warning("• Требуется подписка 'Джем' для создания CSV отчетов")
        st.warning("• Недостаточно прав доступа к API аналитики")
        st.warning("• Превышен лимит отчетов (20 в сутки)")
        
        st.info("💡 **Альтернативные решения:**")
        st.info("• Используйте 'Детальную статистику' вместо CSV отчетов")
        st.info("• Обратитесь в поддержку WB для получения подписки 'Джем'")
        st.info("• Проверьте статус подписки в личном кабинете")
        
        return None

def get_report_list():
    """Получает список созданных отчетов"""
    st.write("🔍 Загружаем список отчетов...")
    
    url = f"{BASE_URLS['seller_analytics']}/api/v2/nm-report/downloads"
    response = make_api_request(url, api_type='seller_analytics')
    
    if response and 'data' in response:
        st.success(f"✅ Загружено {len(response['data'])} отчетов")
        return response['data']
    else:
        st.warning("⚠️ Не удалось загрузить список отчетов")
        return []

def get_report_file(download_id):
    """Получает файл отчета по ID"""
    st.write(f"🔍 Загружаем отчет {download_id}...")
    
    url = f"{BASE_URLS['seller_analytics']}/api/v2/nm-report/downloads/file/{download_id}"
    
    try:
        response = requests.get(url, headers=headers, timeout=60)
        
        if response.status_code == 200:
            st.success("✅ Отчет загружен")
            return response.content
        else:
            st.error(f"❌ Ошибка загрузки отчета: {response.status_code}")
            return None
            
    except requests.exceptions.RequestException as e:
        st.error(f"❌ Ошибка подключения: {e}")
        return None

def retry_report(download_id):
    """Повторно генерирует отчет"""
    st.write(f"🔄 Повторно генерируем отчет {download_id}...")
    
    request_data = {
        "downloadId": download_id
    }
    
    url = f"{BASE_URLS['seller_analytics']}/api/v2/nm-report/downloads/retry"
    response = make_api_request(url, method='POST', data=request_data, api_type='seller_analytics')
    
    if response and response.get('data') == 'Retry':
        st.success("✅ Запрос на повторную генерацию отправлен")
        return True
    else:
        st.error("❌ Не удалось отправить запрос на повторную генерацию")
        return False

def get_detailed_product_statistics(brand_names=None, object_ids=None, tag_ids=None, nm_ids=None, 
                                   start_date=None, end_date=None, timezone="Europe/Moscow", page=1):
    """Получает детальную статистику карточек товаров"""
    st.write("🔍 Загружаем детальную статистику карточек товаров...")
    
    request_data = {
        "brandNames": brand_names or [],
        "objectIDs": object_ids or [],
        "tagIDs": tag_ids or [],
        "nmIDs": nm_ids or [],
        "timezone": timezone,
        "page": page,
        "period": {
            "begin": start_date,
            "end": end_date
        }
    }
    
    url = f"{BASE_URLS['seller_analytics']}/api/v2/nm-report/detail"
    response = make_api_request(url, method='POST', data=request_data, api_type='seller_analytics')
    
    if response:
        st.success("✅ Детальная статистика загружена")
        return response
    else:
        st.warning("⚠️ Не удалось загрузить детальную статистику")
        return None

def get_product_statistics_history(brand_names=None, object_ids=None, tag_ids=None, nm_ids=None, 
                                  start_date=None, end_date=None, timezone="Europe/Moscow", page=1):
    """Получает статистику карточек товаров по дням"""
    st.write("🔍 Загружаем статистику карточек товаров по дням...")
    
    request_data = {
        "brandNames": brand_names or [],
        "objectIDs": object_ids or [],
        "tagIDs": tag_ids or [],
        "nmIDs": nm_ids or [],
        "timezone": timezone,
        "page": page,
        "period": {
            "begin": start_date,
            "end": end_date
        }
    }
    
    url = f"{BASE_URLS['seller_analytics']}/api/v2/nm-report/detail/history"
    response = make_api_request(url, method='POST', data=request_data, api_type='seller_analytics')
    
    if response:
        st.success("✅ Статистика по дням загружена")
        return response
    else:
        st.warning("⚠️ Не удалось загрузить статистику по дням")
        return None

def get_group_statistics_history(brand_names=None, object_ids=None, tag_ids=None, nm_ids=None, 
                                start_date=None, end_date=None, timezone="Europe/Moscow", page=1):
    """Получает статистику групп карточек товаров по дням"""
    st.write("🔍 Загружаем статистику групп карточек товаров по дням...")
    
    request_data = {
        "brandNames": brand_names or [],
        "objectIDs": object_ids or [],
        "tagIDs": tag_ids or [],
        "nmIDs": nm_ids or [],
        "timezone": timezone,
        "page": page,
        "period": {
            "begin": start_date,
            "end": end_date
        }
    }
    
    url = f"{BASE_URLS['seller_analytics']}/api/v2/nm-report/grouped/history"
    response = make_api_request(url, method='POST', data=request_data, api_type='seller_analytics')
    
    if response:
        st.success("✅ Статистика групп по дням загружена")
        return response
    else:
        st.warning("⚠️ Не удалось загрузить статистику групп по дням")
        return None

# ================= ФУНКЦИИ ОБРАБОТКИ ДАННЫХ =================

def process_analytics_data(data, data_type):
    """Обрабатывает данные аналитики"""
    if not data:
        return None
    
    try:
        if data_type == 'detailed_statistics':
            # Обрабатываем детальную статистику
            if 'data' in data:
                df = pd.DataFrame(data['data'])
            else:
                df = pd.DataFrame(data)
            
            if not df.empty:
                # Преобразуем даты
                date_columns = ['dt', 'date', 'period_begin', 'period_end']
                for col in date_columns:
                    if col in df.columns:
                        df[col] = pd.to_datetime(df[col], errors='coerce')
                
                # Преобразуем числовые столбцы
                numeric_columns = ['nmID', 'openCardCount', 'addToCartCount', 'ordersCount', 
                                 'ordersSumRub', 'buyoutsCount', 'buyoutsSumRub', 'cancelCount', 
                                 'cancelSumRub', 'addToCartConversion', 'cartToOrderConversion', 
                                 'buyoutPercent', 'views', 'clicks', 'ctr', 'cpc']
                
                for col in numeric_columns:
                    if col in df.columns:
                        df[col] = pd.to_numeric(df[col], errors='coerce')
                
                return df
        
        elif data_type == 'history_statistics':
            # Обрабатываем статистику по дням
            if 'data' in data:
                df = pd.DataFrame(data['data'])
            else:
                df = pd.DataFrame(data)
            
            if not df.empty:
                # Преобразуем даты
                if 'dt' in df.columns:
                    df['dt'] = pd.to_datetime(df['dt'], errors='coerce')
                
                # Преобразуем числовые столбцы
                numeric_columns = ['nmID', 'openCardCount', 'addToCartCount', 'ordersCount', 
                                 'ordersSumRub', 'buyoutsCount', 'buyoutsSumRub', 'cancelCount', 
                                 'cancelSumRub', 'addToCartConversion', 'cartToOrderConversion', 
                                 'buyoutPercent']
                
                for col in numeric_columns:
                    if col in df.columns:
                        df[col] = pd.to_numeric(df[col], errors='coerce')
                
                return df
        
        elif data_type == 'group_statistics':
            # Обрабатываем статистику групп
            if 'data' in data:
                df = pd.DataFrame(data['data'])
            else:
                df = pd.DataFrame(data)
            
            if not df.empty:
                # Преобразуем даты
                if 'dt' in df.columns:
                    df['dt'] = pd.to_datetime(df['dt'], errors='coerce')
                
                # Преобразуем числовые столбцы
                numeric_columns = ['openCardCount', 'addToCartCount', 'ordersCount', 
                                 'ordersSumRub', 'buyoutsCount', 'buyoutsSumRub', 'cancelCount', 
                                 'cancelSumRub', 'addToCartConversion', 'cartToOrderConversion', 
                                 'buyoutPercent']
                
                for col in numeric_columns:
                    if col in df.columns:
                        df[col] = pd.to_numeric(df[col], errors='coerce')
                
                return df
        
        return None
        
    except Exception as e:
        st.error(f"❌ Ошибка обработки данных: {e}")
        return None

def create_analytics_visualizations(df, data_type):
    """Создает визуализации для аналитических данных"""
    if df is None or df.empty:
        return
    
    st.subheader("📊 Визуализации")
    
    if data_type == 'detailed_statistics':
        # График переходов в карточку
        if 'openCardCount' in df.columns and 'dt' in df.columns:
            daily_views = df.groupby('dt')['openCardCount'].sum().reset_index()
            
            fig = px.line(daily_views, x='dt', y='openCardCount', 
                         title='Переходы в карточку по дням')
            st.plotly_chart(fig, use_container_width=True)
        
        # График заказов
        if 'ordersCount' in df.columns and 'dt' in df.columns:
            daily_orders = df.groupby('dt')['ordersCount'].sum().reset_index()
            
            fig = px.line(daily_orders, x='dt', y='ordersCount', 
                         title='Заказы по дням')
            st.plotly_chart(fig, use_container_width=True)
        
        # График выкупов
        if 'buyoutsCount' in df.columns and 'dt' in df.columns:
            daily_buyouts = df.groupby('dt')['buyoutsCount'].sum().reset_index()
            
            fig = px.line(daily_buyouts, x='dt', y='buyoutsCount', 
                         title='Выкупы по дням')
            st.plotly_chart(fig, use_container_width=True)
        
        # Топ товары по выручке
        if 'buyoutsSumRub' in df.columns and 'nmID' in df.columns:
            top_products = df.groupby('nmID')['buyoutsSumRub'].sum().nlargest(10).reset_index()
            
            fig = px.bar(top_products, x='nmID', y='buyoutsSumRub',
                        title='Топ 10 товаров по выручке')
            st.plotly_chart(fig, use_container_width=True)
    
    elif data_type == 'history_statistics':
        # График конверсии
        if 'addToCartConversion' in df.columns and 'dt' in df.columns:
            daily_conversion = df.groupby('dt')['addToCartConversion'].mean().reset_index()
            
            fig = px.line(daily_conversion, x='dt', y='addToCartConversion', 
                         title='Конверсия в корзину по дням (%)')
            st.plotly_chart(fig, use_container_width=True)
        
        # График процента выкупа
        if 'buyoutPercent' in df.columns and 'dt' in df.columns:
            daily_buyout_percent = df.groupby('dt')['buyoutPercent'].mean().reset_index()
            
            fig = px.line(daily_buyout_percent, x='dt', y='buyoutPercent', 
                         title='Процент выкупа по дням (%)')
            st.plotly_chart(fig, use_container_width=True)

def analyze_analytics_data(df):
    """Анализирует аналитические данные"""
    if df is None or df.empty:
        return None
    
    analysis = {}
    
    # Общая статистика
    analysis['total_records'] = len(df)
    
    if 'dt' in df.columns:
        analysis['date_range'] = f"{df['dt'].min().strftime('%Y-%m-%d')} - {df['dt'].max().strftime('%Y-%m-%d')}"
    
    # Метрики
    if 'openCardCount' in df.columns:
        analysis['total_views'] = df['openCardCount'].sum()
        analysis['avg_views_per_day'] = df.groupby('dt')['openCardCount'].sum().mean() if 'dt' in df.columns else df['openCardCount'].mean()
    
    if 'addToCartCount' in df.columns:
        analysis['total_cart_adds'] = df['addToCartCount'].sum()
        analysis['avg_cart_adds_per_day'] = df.groupby('dt')['addToCartCount'].sum().mean() if 'dt' in df.columns else df['addToCartCount'].mean()
    
    if 'ordersCount' in df.columns:
        analysis['total_orders'] = df['ordersCount'].sum()
        analysis['avg_orders_per_day'] = df.groupby('dt')['ordersCount'].sum().mean() if 'dt' in df.columns else df['ordersCount'].mean()
    
    if 'buyoutsCount' in df.columns:
        analysis['total_buyouts'] = df['buyoutsCount'].sum()
        analysis['avg_buyouts_per_day'] = df.groupby('dt')['buyoutsCount'].sum().mean() if 'dt' in df.columns else df['buyoutsCount'].mean()
    
    if 'buyoutsSumRub' in df.columns:
        analysis['total_revenue'] = df['buyoutsSumRub'].sum()
        analysis['avg_revenue_per_day'] = df.groupby('dt')['buyoutsSumRub'].sum().mean() if 'dt' in df.columns else df['buyoutsSumRub'].mean()
    
    # Конверсии
    if 'addToCartConversion' in df.columns:
        analysis['avg_cart_conversion'] = df['addToCartConversion'].mean()
    
    if 'cartToOrderConversion' in df.columns:
        analysis['avg_order_conversion'] = df['cartToOrderConversion'].mean()
    
    if 'buyoutPercent' in df.columns:
        analysis['avg_buyout_percent'] = df['buyoutPercent'].mean()
    
    return analysis

# ================= ОСНОВНОЙ ИНТЕРФЕЙС =================

def main():
    st.title("📊 WB Analytics - Полная аналитика")
    st.markdown("---")
    
    # Информация о подписке
    st.info("""
    📋 **Информация о подписке 'Джем':**
    
    ✅ **Доступно без подписки:**
    • 📈 Детальная статистика карточек товаров
    • 📅 Статистика по дням
    • 👥 Статистика групп
    • 📊 История остатков (CSV отчеты)
    
    ⚠️ **Требует подписку 'Джем':**
    • 📋 CSV отчеты по воронке продаж
    • 📋 CSV отчеты по поисковым запросам
    • 📋 Расширенные CSV отчеты
    
    💡 **Для получения подписки:** Обратитесь в поддержку WB: dev-info@rwb.ru
    """)
    
    st.markdown("---")
    
    # Боковая панель
    with st.sidebar:
        st.header("⚙️ Настройки аналитики")
        
        # Период
        st.subheader("📅 Период")
        date_option = st.selectbox(
            "Выберите период:",
            ["Последние 7 дней", "Последние 30 дней", "Последние 90 дней", "Произвольный период"]
        )
        
        if date_option == "Произвольный период":
            start_date = st.date_input("Дата начала", value=datetime.now() - timedelta(days=30))
            end_date = st.date_input("Дата окончания", value=datetime.now())
        else:
            days_map = {
                "Последние 7 дней": 7,
                "Последние 30 дней": 30,
                "Последние 90 дней": 90
            }
            days = days_map[date_option]
            start_date = datetime.now() - timedelta(days=days)
            end_date = datetime.now()
            st.write(f"Период: {start_date.strftime('%Y-%m-%d')} - {end_date.strftime('%Y-%m-%d')}")
        
        # Фильтры
        st.subheader("🔍 Фильтры")
        
        # Бренды
        brand_names = st.text_area(
            "Бренды (через запятую):",
            help="Введите названия брендов через запятую"
        )
        brand_list = [b.strip() for b in brand_names.split(',') if b.strip()] if brand_names else None
        
        # Артикулы
        nm_ids = st.text_area(
            "Артикулы WB (через запятую):",
            help="Введите артикулы WB через запятую"
        )
        nm_list = [int(n.strip()) for n in nm_ids.split(',') if n.strip().isdigit()] if nm_ids else None
        
        # Временная зона
        timezone = st.selectbox(
            "Временная зона:",
            ["Europe/Moscow", "Europe/Kiev", "Asia/Almaty", "Asia/Tashkent"],
            index=0
        )
        
        # Страница (для пагинации)
        page = st.number_input(
            "Страница:",
            min_value=1,
            max_value=1000,
            value=1,
            help="Номер страницы для пагинации результатов"
        )
        
        # Тип аналитики
        st.subheader("📊 Тип аналитики")
        analytics_type = st.radio(
            "Выберите тип аналитики:",
            ["📈 Детальная статистика", "📅 Статистика по дням", "👥 Статистика групп", "📋 CSV отчеты"]
        )
        
        # Кнопки для загрузки данных
        st.subheader("🚀 Загрузка данных")
        
        if analytics_type == "📈 Детальная статистика":
            if st.button("📊 Загрузить детальную статистику", use_container_width=True):
                with st.spinner("Загружаем детальную статистику..."):
                    data = get_detailed_product_statistics(
                        brand_names=brand_list,
                        nm_ids=nm_list,
                        start_date=start_date.strftime('%Y-%m-%d'),
                        end_date=end_date.strftime('%Y-%m-%d'),
                        timezone=timezone,
                        page=page
                    )
                    if data:
                        df = process_analytics_data(data, 'detailed_statistics')
                        if df is not None:
                            st.session_state['detailed_statistics'] = df
                            st.success("✅ Детальная статистика загружена!")
        
        elif analytics_type == "📅 Статистика по дням":
            if st.button("📅 Загрузить статистику по дням", use_container_width=True):
                with st.spinner("Загружаем статистику по дням..."):
                    data = get_product_statistics_history(
                        brand_names=brand_list,
                        nm_ids=nm_list,
                        start_date=start_date.strftime('%Y-%m-%d'),
                        end_date=end_date.strftime('%Y-%m-%d'),
                        timezone=timezone,
                        page=page
                    )
                    if data:
                        df = process_analytics_data(data, 'history_statistics')
                        if df is not None:
                            st.session_state['history_statistics'] = df
                            st.success("✅ Статистика по дням загружена!")
        
        elif analytics_type == "👥 Статистика групп":
            if st.button("👥 Загрузить статистику групп", use_container_width=True):
                with st.spinner("Загружаем статистику групп..."):
                    data = get_group_statistics_history(
                        brand_names=brand_list,
                        nm_ids=nm_list,
                        start_date=start_date.strftime('%Y-%m-%d'),
                        end_date=end_date.strftime('%Y-%m-%d'),
                        timezone=timezone,
                        page=page
                    )
                    if data:
                        df = process_analytics_data(data, 'group_statistics')
                        if df is not None:
                            st.session_state['group_statistics'] = df
                            st.success("✅ Статистика групп загружена!")
        
        elif analytics_type == "📋 CSV отчеты":
            st.subheader("📋 Управление CSV отчетами")
            
            # Информация о требованиях подписки
            st.warning("⚠️ **Требуется подписка 'Джем'**")
            st.info("""
            **Для создания CSV отчетов необходимо:**
            • Оформить подписку 'Джем' в личном кабинете WB
            • Иметь активную подписку на момент создания отчета
            • Соблюдать лимиты: максимум 20 отчетов в сутки
            """)
            
            st.info("""💡 **Альтернативы без подписки:**
            • Используйте 'Детальную статистику' для получения данных
            • Скачивайте отчеты вручную из личного кабинета WB
            • Обратитесь в поддержку WB: dev-info@rwb.ru""")
            
            if st.button("📋 Создать CSV отчет", use_container_width=True):
                with st.spinner("Создаем CSV отчет..."):
                    report_id = get_product_statistics_period(
                        brand_names=brand_list,
                        nm_ids=nm_list,
                        start_date=start_date.strftime('%Y-%m-%d'),
                        end_date=end_date.strftime('%Y-%m-%d'),
                        timezone=timezone
                    )
                    if report_id:
                        st.session_state['current_report_id'] = report_id
                        st.success(f"✅ CSV отчет создан (ID: {report_id})")
            
            if st.button("📋 Обновить список отчетов", use_container_width=True):
                with st.spinner("Загружаем список отчетов..."):
                    reports = get_report_list()
                    if reports:
                        st.session_state['reports_list'] = reports
                        st.success(f"✅ Загружено {len(reports)} отчетов")
    
    # Основной контент
    st.subheader("📊 Результаты аналитики")
    
    # Показываем загруженные данные
    if 'detailed_statistics' in st.session_state:
        st.success("📈 Детальная статистика загружена")
        df = st.session_state['detailed_statistics']
        
        # Анализ данных
        analysis = analyze_analytics_data(df)
        if analysis:
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Записей", analysis['total_records'])
                if 'total_views' in analysis:
                    st.metric("Просмотры", f"{analysis['total_views']:,.0f}")
            
            with col2:
                if 'total_orders' in analysis:
                    st.metric("Заказы", f"{analysis['total_orders']:,.0f}")
                if 'total_buyouts' in analysis:
                    st.metric("Выкупы", f"{analysis['total_buyouts']:,.0f}")
            
            with col3:
                if 'total_revenue' in analysis:
                    st.metric("Выручка", f"{analysis['total_revenue']:,.0f} ₽")
                if 'avg_cart_conversion' in analysis:
                    st.metric("Конверсия в корзину", f"{analysis['avg_cart_conversion']:.1f}%")
            
            with col4:
                if 'avg_buyout_percent' in analysis:
                    st.metric("Процент выкупа", f"{analysis['avg_buyout_percent']:.1f}%")
                if 'date_range' in analysis:
                    st.metric("Период", analysis['date_range'])
        
        # Визуализации
        create_analytics_visualizations(df, 'detailed_statistics')
        
        # Таблица данных
        st.subheader("📋 Данные")
        st.dataframe(df, use_container_width=True)
    
    if 'history_statistics' in st.session_state:
        st.success("📅 Статистика по дням загружена")
        df = st.session_state['history_statistics']
        
        # Анализ данных
        analysis = analyze_analytics_data(df)
        if analysis:
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Записей", analysis['total_records'])
                if 'avg_views_per_day' in analysis:
                    st.metric("Просмотры/день", f"{analysis['avg_views_per_day']:,.0f}")
            
            with col2:
                if 'avg_orders_per_day' in analysis:
                    st.metric("Заказы/день", f"{analysis['avg_orders_per_day']:,.0f}")
                if 'avg_buyouts_per_day' in analysis:
                    st.metric("Выкупы/день", f"{analysis['avg_buyouts_per_day']:,.0f}")
            
            with col3:
                if 'avg_revenue_per_day' in analysis:
                    st.metric("Выручка/день", f"{analysis['avg_revenue_per_day']:,.0f} ₽")
                if 'avg_cart_conversion' in analysis:
                    st.metric("Конверсия в корзину", f"{analysis['avg_cart_conversion']:.1f}%")
            
            with col4:
                if 'avg_buyout_percent' in analysis:
                    st.metric("Процент выкупа", f"{analysis['avg_buyout_percent']:.1f}%")
                if 'date_range' in analysis:
                    st.metric("Период", analysis['date_range'])
        
        # Визуализации
        create_analytics_visualizations(df, 'history_statistics')
        
        # Таблица данных
        st.subheader("📋 Данные")
        st.dataframe(df, use_container_width=True)
    
    if 'group_statistics' in st.session_state:
        st.success("👥 Статистика групп загружена")
        df = st.session_state['group_statistics']
        
        # Анализ данных
        analysis = analyze_analytics_data(df)
        if analysis:
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Записей", analysis['total_records'])
                if 'total_views' in analysis:
                    st.metric("Просмотры", f"{analysis['total_views']:,.0f}")
            
            with col2:
                if 'total_orders' in analysis:
                    st.metric("Заказы", f"{analysis['total_orders']:,.0f}")
                if 'total_buyouts' in analysis:
                    st.metric("Выкупы", f"{analysis['total_buyouts']:,.0f}")
            
            with col3:
                if 'total_revenue' in analysis:
                    st.metric("Выручка", f"{analysis['total_revenue']:,.0f} ₽")
                if 'avg_cart_conversion' in analysis:
                    st.metric("Конверсия в корзину", f"{analysis['avg_cart_conversion']:.1f}%")
            
            with col4:
                if 'avg_buyout_percent' in analysis:
                    st.metric("Процент выкупа", f"{analysis['avg_buyout_percent']:.1f}%")
                if 'date_range' in analysis:
                    st.metric("Период", analysis['date_range'])
        
        # Таблица данных
        st.subheader("📋 Данные")
        st.dataframe(df, use_container_width=True)
    
    # Управление CSV отчетами
    if 'reports_list' in st.session_state:
        st.subheader("📋 CSV отчеты")
        
        reports = st.session_state['reports_list']
        
        for report in reports:
            with st.expander(f"📄 {report.get('name', 'Без названия')} - {report.get('status', 'Неизвестно')}"):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.write(f"**ID:** {report.get('id', 'N/A')}")
                    st.write(f"**Статус:** {report.get('status', 'N/A')}")
                    st.write(f"**Размер:** {report.get('size', 'N/A')} байт")
                
                with col2:
                    st.write(f"**Создан:** {report.get('createdAt', 'N/A')}")
                    st.write(f"**Период:** {report.get('startDate', 'N/A')} - {report.get('endDate', 'N/A')}")
                
                with col3:
                    if report.get('status') == 'SUCCESS':
                        if st.button(f"⬇️ Скачать", key=f"download_{report.get('id')}"):
                            with st.spinner("Загружаем отчет..."):
                                file_content = get_report_file(report.get('id'))
                                if file_content:
                                    st.success("✅ Отчет загружен!")
                                    st.download_button(
                                        label="💾 Скачать ZIP файл",
                                        data=file_content,
                                        file_name=f"report_{report.get('id')}.zip",
                                        mime="application/zip"
                                    )
                    elif report.get('status') == 'FAILED':
                        if st.button(f"🔄 Повторить", key=f"retry_{report.get('id')}"):
                            with st.spinner("Повторно генерируем отчет..."):
                                if retry_report(report.get('id')):
                                    st.success("✅ Запрос на повторную генерацию отправлен!")
                    else:
                        st.info(f"Статус: {report.get('status')}")

if __name__ == "__main__":
    main()
