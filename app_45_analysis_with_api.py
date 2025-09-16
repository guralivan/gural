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

# Настройка страницы
st.set_page_config(
    page_title="Анализ отчетов WB - 45.xlsx + API",
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
    'statistics': 'https://statistics-api.wildberries.ru',
    'finance': 'https://finance-api.wildberries.ru',
    'documents': 'https://documents-api.wildberries.ru'
}

# Лимиты API
API_LIMITS = {
    'statistics': {'requests_per_minute': 100, 'interval_ms': 600},
    'finance': {'requests_per_minute': 1, 'interval_ms': 60000},
    'documents': {'requests_per_minute': 6, 'interval_ms': 10000}
}

# Глобальные переменные для управления запросами
last_request_time = {}
request_counts = {}

# ================= API ФУНКЦИИ =================

def make_api_request(url, params=None, api_type='statistics'):
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
        response = requests.get(url, headers=headers, params=params, timeout=15)
        
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 429:
            st.warning("⚠️ Превышен лимит запросов. Ожидание...")
            time.sleep(60)  # Ждем минуту
            return make_api_request(url, params, api_type)  # Повторяем запрос
        else:
            st.error(f"❌ Ошибка API: {response.status_code} - {response.text}")
            return None
            
    except requests.exceptions.RequestException as e:
        st.error(f"❌ Ошибка подключения: {e}")
        return None

def get_financial_report_api(date_from, date_to):
    """Получает детальный финансовый отчет через API"""
    st.write("🔍 Загружаем финансовый отчет через API...")
    
    params = {
        'dateFrom': date_from.strftime('%Y-%m-%d'),
        'dateTo': date_to.strftime('%Y-%m-%d'),
        'limit': 100000
    }
    
    url = f"{BASE_URLS['statistics']}/api/v5/supplier/reportDetailByPeriod"
    data = make_api_request(url, params, 'statistics')
    
    if data:
        st.success("✅ Финансовый отчет загружен через API")
        return data
    else:
        st.warning("⚠️ Не удалось загрузить отчет через API")
        return None

def get_balance_api():
    """Получает баланс продавца через API"""
    st.write("🔍 Загружаем баланс через API...")
    
    url = f"{BASE_URLS['finance']}/api/v1/account/balance"
    data = make_api_request(url, None, 'finance')
    
    if data:
        st.success("✅ Баланс загружен через API")
        return data
    else:
        st.warning("⚠️ Не удалось загрузить баланс через API")
        return None

def get_orders_api(date_from, date_to):
    """Получает данные о заказах через API"""
    st.write("🔍 Загружаем заказы через API...")
    
    params = {
        'dateFrom': date_from.strftime('%Y-%m-%d'),
        'dateTo': date_to.strftime('%Y-%m-%d')
    }
    
    url = f"{BASE_URLS['statistics']}/api/v1/supplier/orders"
    data = make_api_request(url, params, 'statistics')
    
    if data:
        st.success("✅ Заказы загружены через API")
        return data
    else:
        st.warning("⚠️ Не удалось загрузить заказы через API")
        return None

def get_sales_api(date_from, date_to):
    """Получает данные о продажах через API"""
    st.write("🔍 Загружаем продажи через API...")
    
    params = {
        'dateFrom': date_from.strftime('%Y-%m-%d'),
        'dateTo': date_to.strftime('%Y-%m-%d')
    }
    
    url = f"{BASE_URLS['statistics']}/api/v1/supplier/sales"
    data = make_api_request(url, params, 'statistics')
    
    if data:
        st.success("✅ Продажи загружены через API")
        return data
    else:
        st.warning("⚠️ Не удалось загрузить продажи через API")
        return None

def convert_api_data_to_dataframe(api_data, data_type):
    """Конвертирует данные API в DataFrame для анализа"""
    if not api_data:
        return None
    
    try:
        if data_type == 'financial_report':
            # Конвертируем финансовый отчет
            df = pd.DataFrame(api_data)
            if not df.empty:
                # Преобразуем даты
                if 'date_from' in df.columns:
                    df['date_from'] = pd.to_datetime(df['date_from'])
                if 'date_to' in df.columns:
                    df['date_to'] = pd.to_datetime(df['date_to'])
                
                # Преобразуем числовые столбцы
                numeric_columns = ['realizationreport_id', 'suppliercontract_code', 'rrd_id', 'gi_id', 'subject_name', 'nm_id', 'brand_name', 'sa_name', 'ts_name', 'barcode', 'doc_type_name', 'quantity', 'retail_price', 'retail_amount', 'sale_percent', 'commission_amount', 'office_name', 'supplier_oper_name', 'order_dt', 'sale_dt', 'rr_dt', 'shk_id', 'retail_price_withdisc_rub', 'delivery_amount', 'return_amount', 'delivery_rub', 'gi_box_type_name', 'product_discount_for_report', 'supplier_promo', 'rid', 'ppvz_spp_prc', 'ppvz_kvw_prc_base', 'ppvz_kvw_prc', 'ppvz_sales_commission', 'ppvz_for_pay', 'ppvz_reward', 'acquiring_fee', 'acquiring_bank', 'ppvz_vw', 'ppvz_vw_nds', 'ppvz_office_id', 'ppvz_office_name', 'ppvz_supplier_id', 'ppvz_supplier_name', 'ppvz_inn', 'declaration_number', 'bonus_type_name', 'sticker_id', 'site_country', 'penalty', 'additional_payment', 'rebill_logistic_cost', 'rebill_logistic_org', 'kiz', 'srid', 'fiscal_dt', 'nm_id', 'brand_name', 'sa_name', 'ts_name', 'barcode', 'doc_type_name', 'quantity', 'retail_price', 'retail_amount', 'sale_percent', 'commission_amount', 'office_name', 'supplier_oper_name', 'order_dt', 'sale_dt', 'rr_dt', 'shk_id', 'retail_price_withdisc_rub', 'delivery_amount', 'return_amount', 'delivery_rub', 'gi_box_type_name', 'product_discount_for_report', 'supplier_promo', 'rid', 'ppvz_spp_prc', 'ppvz_kvw_prc_base', 'ppvz_kvw_prc', 'ppvz_sales_commission', 'ppvz_for_pay', 'ppvz_reward', 'acquiring_fee', 'acquiring_bank', 'ppvz_vw', 'ppvz_vw_nds', 'ppvz_office_id', 'ppvz_office_name', 'ppvz_supplier_id', 'ppvz_supplier_name', 'ppvz_inn', 'declaration_number', 'bonus_type_name', 'sticker_id', 'site_country', 'penalty', 'additional_payment', 'rebill_logistic_cost', 'rebill_logistic_org', 'kiz', 'srid', 'fiscal_dt']
                
                for col in numeric_columns:
                    if col in df.columns:
                        df[col] = pd.to_numeric(df[col], errors='coerce')
                
                return df
        
        elif data_type == 'orders':
            # Конвертируем заказы
            df = pd.DataFrame(api_data)
            if not df.empty:
                # Преобразуем даты
                if 'date' in df.columns:
                    df['date'] = pd.to_datetime(df['date'])
                
                return df
        
        elif data_type == 'sales':
            # Конвертируем продажи
            df = pd.DataFrame(api_data)
            if not df.empty:
                # Преобразуем даты
                if 'date' in df.columns:
                    df['date'] = pd.to_datetime(df['date'])
                
                return df
        
        return None
        
    except Exception as e:
        st.error(f"❌ Ошибка конвертации данных: {e}")
        return None

# ================= ОРИГИНАЛЬНЫЕ ФУНКЦИИ =================

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
            df['Дата'] = pd.to_datetime(df['Дата'], errors='coerce')
        
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
        if 'Выкупили на сумму, ₽' in df.columns and 'Заказали на сумму, ₽' in df.columns:
            df['Доходность'] = df['Выкупили на сумму, ₽'] - df['Заказали на сумму, ₽']
        
        if 'Выкупили, шт' in df.columns and 'Переходы в карточку' in df.columns:
            df['Эффективность'] = df['Выкупили, шт'] / df['Переходы в карточку'] * 100
        
        return df
    except Exception as e:
        st.error(f"Ошибка загрузки файла: {e}")
        return None

# ================= ФУНКЦИИ АНАЛИЗА =================

def analyze_data(df):
    """Анализирует загруженные данные"""
    if df is None or df.empty:
        return None
    
    analysis = {}
    
    # Общая статистика
    analysis['total_products'] = len(df)
    analysis['date_range'] = f"{df['Дата'].min().strftime('%Y-%m-%d')} - {df['Дата'].max().strftime('%Y-%m-%d')}"
    
    # Метрики
    if 'Выкупили на сумму, ₽' in df.columns:
        analysis['total_revenue'] = df['Выкупили на сумму, ₽'].sum()
        analysis['avg_revenue_per_product'] = df['Выкупили на сумму, ₽'].mean()
    
    if 'Выкупили, шт' in df.columns:
        analysis['total_sales'] = df['Выкупили, шт'].sum()
        analysis['avg_sales_per_product'] = df['Выкупили, шт'].mean()
    
    if 'Переходы в карточку' in df.columns:
        analysis['total_views'] = df['Переходы в карточку'].sum()
        analysis['avg_views_per_product'] = df['Переходы в карточку'].mean()
    
    # Топ товары
    if 'Выкупили на сумму, ₽' in df.columns:
        analysis['top_products_revenue'] = df.nlargest(10, 'Выкупили на сумму, ₽')[['Артикул', 'Выкупили на сумму, ₽']].to_dict('records')
    
    if 'Выкупили, шт' in df.columns:
        analysis['top_products_sales'] = df.nlargest(10, 'Выкупили, шт')[['Артикул', 'Выкупили, шт']].to_dict('records')
    
    return analysis

def create_visualizations(df):
    """Создает визуализации данных"""
    if df is None or df.empty:
        return
    
    # График продаж по времени
    if 'Дата' in df.columns and 'Выкупили на сумму, ₽' in df.columns:
        daily_sales = df.groupby('Дата')['Выкупили на сумму, ₽'].sum().reset_index()
        
        fig = px.line(daily_sales, x='Дата', y='Выкупили на сумму, ₽', 
                     title='Продажи по дням')
        st.plotly_chart(fig, use_container_width=True)
    
    # Топ товары по выручке
    if 'Выкупили на сумму, ₽' in df.columns:
        top_products = df.nlargest(10, 'Выкупили на сумму, ₽')
        
        fig = px.bar(top_products, x='Артикул', y='Выкупили на сумму, ₽',
                    title='Топ 10 товаров по выручке')
        st.plotly_chart(fig, use_container_width=True)
    
    # Распределение конверсии
    if 'Конверсия в заказ, %' in df.columns:
        fig = px.histogram(df, x='Конверсия в заказ, %', 
                          title='Распределение конверсии в заказ')
        st.plotly_chart(fig, use_container_width=True)

# ================= ОСНОВНОЙ ИНТЕРФЕЙС =================

def main():
    st.title("📊 Анализ отчетов WB - 45.xlsx + API")
    st.markdown("---")
    
    # Боковая панель
    with st.sidebar:
        st.header("📁 Источники данных")
        
        # Выбор источника данных
        data_source = st.radio(
            "Выберите источник данных:",
            ["📄 Загрузить файл", "🌐 API Wildberries", "📊 Комбинированный анализ"]
        )
        
        if data_source == "📄 Загрузить файл":
            st.subheader("📤 Загрузка файла")
            uploaded_file = st.file_uploader(
                "Выберите файл Excel (.xlsx, .xls) или CSV",
                type=['xlsx', 'xls', 'csv'],
                help="Поддерживаются файлы с отчетами WB"
            )
            
            if uploaded_file is not None:
                st.session_state['uploaded_data'] = load_uploaded_data(uploaded_file.read(), uploaded_file.name)
                if st.session_state['uploaded_data'] is not None:
                    st.success(f"✅ Файл {uploaded_file.name} загружен успешно!")
        
        elif data_source == "🌐 API Wildberries":
            st.subheader("🔗 API настройки")
            
            # Период для API
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
            
            # Кнопки для загрузки данных через API
            st.subheader("📊 Загрузка данных")
            
            if st.button("💰 Финансовый отчет", use_container_width=True):
                with st.spinner("Загружаем финансовый отчет..."):
                    api_data = get_financial_report_api(date_from, date_to)
                    if api_data:
                        df = convert_api_data_to_dataframe(api_data, 'financial_report')
                        if df is not None:
                            st.session_state['api_financial_data'] = df
                            st.success("✅ Финансовый отчет загружен и обработан!")
            
            if st.button("📦 Заказы", use_container_width=True):
                with st.spinner("Загружаем заказы..."):
                    api_data = get_orders_api(date_from, date_to)
                    if api_data:
                        df = convert_api_data_to_dataframe(api_data, 'orders')
                        if df is not None:
                            st.session_state['api_orders_data'] = df
                            st.success("✅ Заказы загружены и обработаны!")
            
            if st.button("🛒 Продажи", use_container_width=True):
                with st.spinner("Загружаем продажи..."):
                    api_data = get_sales_api(date_from, date_to)
                    if api_data:
                        df = convert_api_data_to_dataframe(api_data, 'sales')
                        if df is not None:
                            st.session_state['api_sales_data'] = df
                            st.success("✅ Продажи загружены и обработаны!")
            
            if st.button("💳 Баланс", use_container_width=True):
                with st.spinner("Загружаем баланс..."):
                    balance_data = get_balance_api()
                    if balance_data:
                        st.session_state['api_balance_data'] = balance_data
                        st.success("✅ Баланс загружен!")
        
        elif data_source == "📊 Комбинированный анализ":
            st.subheader("🔄 Комбинированный анализ")
            st.info("Объединяет данные из файлов и API для комплексного анализа")
            
            # Загрузка файла для комбинированного анализа
            uploaded_file = st.file_uploader(
                "Загрузите файл для комбинированного анализа",
                type=['xlsx', 'xls', 'csv'],
                key="combo_file"
            )
            
            if uploaded_file is not None:
                st.session_state['combo_file_data'] = load_uploaded_data(uploaded_file.read(), uploaded_file.name)
                if st.session_state['combo_file_data'] is not None:
                    st.success(f"✅ Файл {uploaded_file.name} загружен!")
            
            # Период для API
            date_option = st.selectbox(
                "Период для API данных:",
                ["Последние 7 дней", "Последние 30 дней", "Последние 90 дней"],
                key="combo_date"
            )
            
            days_map = {
                "Последние 7 дней": 7,
                "Последние 30 дней": 30,
                "Последние 90 дней": 90
            }
            days = days_map[date_option]
            date_from = datetime.now() - timedelta(days=days)
            date_to = datetime.now()
            
            if st.button("🔄 Загрузить API данные", use_container_width=True):
                with st.spinner("Загружаем данные через API..."):
                    # Загружаем все типы данных
                    financial_data = get_financial_report_api(date_from, date_to)
                    orders_data = get_orders_api(date_from, date_to)
                    sales_data = get_sales_api(date_from, date_to)
                    balance_data = get_balance_api()
                    
                    # Сохраняем в session state
                    if financial_data:
                        df = convert_api_data_to_dataframe(financial_data, 'financial_report')
                        if df is not None:
                            st.session_state['combo_financial_data'] = df
                    
                    if orders_data:
                        df = convert_api_data_to_dataframe(orders_data, 'orders')
                        if df is not None:
                            st.session_state['combo_orders_data'] = df
                    
                    if sales_data:
                        df = convert_api_data_to_dataframe(sales_data, 'sales')
                        if df is not None:
                            st.session_state['combo_sales_data'] = df
                    
                    if balance_data:
                        st.session_state['combo_balance_data'] = balance_data
                    
                    st.success("✅ Все API данные загружены!")
    
    # Основной контент
    st.subheader("📊 Анализ данных")
    
    # Определяем какие данные показывать
    if data_source == "📄 Загрузить файл":
        if 'uploaded_data' in st.session_state and st.session_state['uploaded_data'] is not None:
            df = st.session_state['uploaded_data']
            st.success(f"📁 Анализируем файл: {len(df)} записей")
            
            # Анализ данных
            analysis = analyze_data(df)
            if analysis:
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Товаров", analysis['total_products'])
                
                with col2:
                    if 'total_revenue' in analysis:
                        st.metric("Выручка", f"{analysis['total_revenue']:,.0f} ₽")
                
                with col3:
                    if 'total_sales' in analysis:
                        st.metric("Продажи", f"{analysis['total_sales']:,.0f} шт")
                
                with col4:
                    if 'total_views' in analysis:
                        st.metric("Просмотры", f"{analysis['total_views']:,.0f}")
                
                # Визуализации
                create_visualizations(df)
                
                # Таблица данных
                st.subheader("📋 Данные")
                st.dataframe(df, use_container_width=True)
    
    elif data_source == "🌐 API Wildberries":
        st.subheader("🌐 Данные из API")
        
        # Показываем загруженные данные
        if 'api_financial_data' in st.session_state:
            st.success("💰 Финансовый отчет загружен")
            df = st.session_state['api_financial_data']
            st.dataframe(df.head(), use_container_width=True)
        
        if 'api_orders_data' in st.session_state:
            st.success("📦 Заказы загружены")
            df = st.session_state['api_orders_data']
            st.dataframe(df.head(), use_container_width=True)
        
        if 'api_sales_data' in st.session_state:
            st.success("🛒 Продажи загружены")
            df = st.session_state['api_sales_data']
            st.dataframe(df.head(), use_container_width=True)
        
        if 'api_balance_data' in st.session_state:
            st.success("💳 Баланс загружен")
            balance = st.session_state['api_balance_data']
            st.json(balance)
    
    elif data_source == "📊 Комбинированный анализ":
        st.subheader("🔄 Комбинированный анализ")
        
        # Показываем файловые данные
        if 'combo_file_data' in st.session_state:
            st.success("📁 Файловые данные загружены")
            df = st.session_state['combo_file_data']
            st.dataframe(df.head(), use_container_width=True)
        
        # Показываем API данные
        if 'combo_financial_data' in st.session_state:
            st.success("💰 API финансовый отчет загружен")
            df = st.session_state['combo_financial_data']
            st.dataframe(df.head(), use_container_width=True)
        
        if 'combo_orders_data' in st.session_state:
            st.success("📦 API заказы загружены")
            df = st.session_state['combo_orders_data']
            st.dataframe(df.head(), use_container_width=True)
        
        if 'combo_sales_data' in st.session_state:
            st.success("🛒 API продажи загружены")
            df = st.session_state['combo_sales_data']
            st.dataframe(df.head(), use_container_width=True)
        
        if 'combo_balance_data' in st.session_state:
            st.success("💳 API баланс загружен")
            balance = st.session_state['combo_balance_data']
            st.json(balance)

if __name__ == "__main__":
    main()
