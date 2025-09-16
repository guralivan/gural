# -*- coding: utf-8 -*-
import os
import json
import base64
from io import BytesIO
import urllib.parse as _urlparse
from datetime import datetime, timedelta
import calendar

import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import requests

try:
    from PIL import Image
except Exception:
    Image = None

st.set_page_config(
    page_title="Анализ сезонности товаров", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# ================= ФУНКЦИИ ДЛЯ АНАЛИЗА СЕЗОННОСТИ =================

def detect_seasonality_pattern(data, period=12):
    """Определяет сезонный паттерн в данных"""
    if len(data) < period * 2:
        return None, None
    
    # Автокорреляция для определения сезонности
    autocorr = np.correlate(data, data, mode='full')
    autocorr = autocorr[len(autocorr)//2:]
    
    # Ищем пики в автокорреляции
    peaks = []
    for i in range(1, len(autocorr)-1):
        if autocorr[i] > autocorr[i-1] and autocorr[i] > autocorr[i+1]:
            peaks.append(i)
    
    # Определяем основной период сезонности
    if peaks:
        main_period = peaks[0]
        seasonality_strength = autocorr[main_period] / autocorr[0]
    else:
        main_period = period
        seasonality_strength = 0
    
    return main_period, seasonality_strength

def calculate_seasonal_indexes(data, period=12):
    """Вычисляет сезонные индексы"""
    if len(data) < period:
        return None
    
    # Группируем данные по позиции в периоде
    seasonal_data = []
    for i in range(period):
        seasonal_data.append([])
    
    for i, value in enumerate(data):
        pos = i % period
        seasonal_data[pos].append(value)
    
    # Вычисляем средние значения для каждой позиции
    seasonal_means = [np.mean(group) if group else 0 for group in seasonal_data]
    overall_mean = np.mean(seasonal_means)
    
    # Вычисляем сезонные индексы
    seasonal_indexes = [mean / overall_mean if overall_mean > 0 else 1 for mean in seasonal_means]
    
    return seasonal_indexes

def forecast_seasonal_values(historical_data, periods_ahead=12, seasonality_period=12):
    """Прогнозирует значения с учетом сезонности"""
    if len(historical_data) < seasonality_period:
        return None
    
    # Вычисляем сезонные индексы
    seasonal_indexes = calculate_seasonal_indexes(historical_data, seasonality_period)
    if not seasonal_indexes:
        return None
    
    # Простая модель: тренд + сезонность
    x = np.arange(len(historical_data))
    trend_coeffs = np.polyfit(x, historical_data, 1)
    trend_line = np.polyval(trend_coeffs, x)
    
    # Прогнозируем тренд
    future_x = np.arange(len(historical_data), len(historical_data) + periods_ahead)
    future_trend = np.polyval(trend_coeffs, future_x)
    
    # Применяем сезонность
    forecasts = []
    for i, trend_val in enumerate(future_trend):
        seasonal_pos = (len(historical_data) + i) % seasonality_period
        seasonal_factor = seasonal_indexes[seasonal_pos]
        forecast = trend_val * seasonal_factor
        forecasts.append(max(0, forecast))
    
    return forecasts

def analyze_product_seasonality(df, date_column, value_column, product_column=None):
    """Анализирует сезонность для товаров"""
    results = {}
    
    if product_column:
        # Анализ по отдельным товарам
        for product in df[product_column].unique():
            product_data = df[df[product_column] == product].copy()
            product_data = product_data.sort_values(date_column)
            
            # Группируем по месяцам
            product_data['month'] = product_data[date_column].dt.to_period('M')
            monthly_data = product_data.groupby('month')[value_column].sum().reset_index()
            monthly_data['month'] = monthly_data['month'].astype(str)
            
            # Анализируем сезонность
            values = monthly_data[value_column].values
            period, strength = detect_seasonality_pattern(values)
            seasonal_indexes = calculate_seasonal_indexes(values, period or 12)
            
            results[product] = {
                'monthly_data': monthly_data,
                'values': values,
                'seasonality_period': period,
                'seasonality_strength': strength,
                'seasonal_indexes': seasonal_indexes,
                'forecast': forecast_seasonal_values(values, 12, period or 12)
            }
    else:
        # Общий анализ
        df_sorted = df.sort_values(date_column)
        df_sorted['month'] = df_sorted[date_column].dt.to_period('M')
        monthly_data = df_sorted.groupby('month')[value_column].sum().reset_index()
        monthly_data['month'] = monthly_data['month'].astype(str)
        
        values = monthly_data[value_column].values
        period, strength = detect_seasonality_pattern(values)
        seasonal_indexes = calculate_seasonal_indexes(values, period or 12)
        
        results['overall'] = {
            'monthly_data': monthly_data,
            'values': values,
            'seasonality_period': period,
            'seasonality_strength': strength,
            'seasonal_indexes': seasonal_indexes,
            'forecast': forecast_seasonal_values(values, 12, period or 12)
        }
    
    return results

# ================= ФУНКЦИИ ДЛЯ РАБОТЫ С ДАННЫМИ =================

@st.cache_data(show_spinner=False)
def read_table(file_bytes: bytes, filename: str):
    """Читает таблицу из файла"""
    try:
        if filename.lower().endswith((".xlsx", ".xls")):
            df_raw = pd.read_excel(BytesIO(file_bytes), sheet_name=0, header=None)
        else:
            df_raw = pd.read_csv(BytesIO(file_bytes), header=None, sep=None, engine="python")
    except Exception as e:
        st.error(f"Ошибка чтения файла: {e}")
        return None, None, {}
    
    # Поиск строки заголовков
    key_candidates = ["Артикул", "Выручка", "Заказы", "Название", "Дата", "Месяц", "Год", "Запросы"]
    header_row = None
    for i in range(min(30, len(df_raw))):
        vals = df_raw.iloc[i].astype(str).str.strip().tolist()
        if any(k in vals for k in key_candidates):
            header_row = i
            break
    
    if header_row is None:
        header_row = 0
    
    # Чтение данных
    if filename.lower().endswith((".xlsx", ".xls")):
        df = pd.read_excel(BytesIO(file_bytes), sheet_name=0, header=header_row)
    else:
        df = pd.read_csv(BytesIO(file_bytes), header=header_row, sep=None, engine="python")
    
    # Очистка данных
    df = df.loc[:, ~df.columns.astype(str).str.startswith("Unnamed")]
    df = df.loc[:, df.columns.notna()]
    df.columns = [str(c).strip() for c in df.columns]
    
    # Переименование столбцов
    rename_map = {
        "Средняя цена без СПП": "Средняя цена",
        "Выручка, ₽": "Выручка",
        "Orders": "Заказы",
        "Creation date": "Дата создания",
        "Дата": "Дата создания",
        "Месяц": "Месяц",
        "Год": "Год",
        "Запросы": "Запросы",
        "Поиски": "Запросы",
        "Views": "Просмотры"
    }
    
    df = df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns})
    
    # Преобразование числовых столбцов
    num_cols = ["Выручка", "Заказы", "Средняя цена", "Запросы", "Просмотры"]
    for c in num_cols:
        if c in df.columns:
            df[c] = pd.to_numeric(
                df[c].astype(str).str.replace(r"[^\d,.-]", "", regex=True).str.replace(",", ".", regex=False),
                errors="coerce",
            )
    
    # Обработка дат
    if "Дата создания" in df.columns:
        df["Дата создания"] = pd.to_datetime(df["Дата создания"], errors="coerce")
    
    return df, df_raw, {"header_row": header_row, "columns": list(df.columns)}

def format_thousands(x, decimals=0):
    """Форматирует числа с разделителями"""
    if x is None or (isinstance(x, float) and np.isnan(x)):
        return ""
    try:
        xf = float(x)
    except Exception:
        return str(x) if x is not None else ""
    if decimals == 0:
        return f"{int(round(xf)):,}".replace(",", " ")
    return f"{xf:,.{decimals}f}".replace(",", " ").replace(".", ",")

def fmt_units(x, unit="ед."):
    """Форматирует единицы"""
    s = format_thousands(x, decimals=0)
    return (s + f" {unit}") if s != "" else ""

# ================= ОСНОВНОЕ ПРИЛОЖЕНИЕ =================

st.title("📈 Анализ сезонности товаров")
st.markdown("Анализ сезонных паттернов в частоте запросов и продажах товаров")

# Боковая панель для загрузки данных
with st.sidebar:
    st.header("📁 Загрузка данных")
    uploaded_file = st.file_uploader(
        "Загрузите Excel/CSV файл с данными", 
        type=["xlsx", "xls", "csv"],
        help="Файл должен содержать столбцы с датами и значениями (запросы, продажи, выручка)"
    )
    
    if uploaded_file:
        st.success(f"✅ Файл загружен: {uploaded_file.name}")
        
        # Настройки анализа
        st.header("⚙️ Настройки анализа")
        
        # Выбор столбцов
        df, raw, meta = read_table(uploaded_file.read(), uploaded_file.name)
        
        if df is not None and not df.empty:
            # Выбор столбца с датами
            date_columns = [col for col in df.columns if 'дата' in col.lower() or 'date' in col.lower()]
            if not date_columns:
                date_columns = df.columns.tolist()
            
            date_column = st.selectbox(
                "Столбец с датами:",
                date_columns,
                help="Выберите столбец, содержащий даты"
            )
            
            # Выбор столбца со значениями
            value_columns = [col for col in df.columns if col in ['Запросы', 'Заказы', 'Выручка', 'Просмотры']]
            if not value_columns:
                value_columns = df.columns.tolist()
            
            value_column = st.selectbox(
                "Столбец со значениями:",
                value_columns,
                help="Выберите столбец для анализа сезонности"
            )
            
            # Выбор столбца с товарами (опционально)
            product_columns = [col for col in df.columns if col in ['Артикул', 'Название', 'Бренд']]
            product_columns = ['Без группировки'] + product_columns
            
            product_column = st.selectbox(
                "Группировка по товарам (опционально):",
                product_columns,
                help="Выберите столбец для группировки анализа по товарам"
            )
            
            if product_column == 'Без группировки':
                product_column = None

# Основной контент
if uploaded_file is None:
    st.info("👆 Загрузите файл с данными в боковой панели для начала анализа")
    
    # Пример структуры данных
    st.header("📋 Пример структуры данных")
    st.markdown("""
    Ваш файл должен содержать следующие столбцы:
    
    | Дата | Артикул | Запросы | Заказы | Выручка |
    |------|---------|---------|--------|---------|
    | 2023-01-01 | 123456 | 150 | 25 | 50000 |
    | 2023-02-01 | 123456 | 180 | 30 | 60000 |
    | ... | ... | ... | ... | ... |
    
    **Обязательные столбцы:**
    - Столбец с датами (в любом формате)
    - Столбец с числовыми значениями для анализа
    
    **Опциональные столбцы:**
    - Артикул/Название товара (для группировки)
    - Дополнительные метрики
    """)
    
else:
    if df is not None and not df.empty:
        # Проверяем наличие необходимых столбцов
        if date_column not in df.columns:
            st.error(f"❌ Столбец '{date_column}' не найден в данных")
        elif value_column not in df.columns:
            st.error(f"❌ Столбец '{value_column}' не найден в данных")
        else:
            # Проверяем и обрабатываем даты
            if df[date_column].dtype == 'object':
                df[date_column] = pd.to_datetime(df[date_column], errors='coerce')
            
            # Удаляем строки с отсутствующими датами
            df_clean = df.dropna(subset=[date_column, value_column])
            
            if df_clean.empty:
                st.error("❌ Нет данных с валидными датами и значениями")
            else:
                st.success(f"✅ Загружено {len(df_clean)} записей")
                
                # Создаем вкладки
                tab1, tab2, tab3 = st.tabs(["📊 Общий анализ", "📈 Детальный анализ", "📋 Данные"])
                
                with tab1:
                    st.header("📊 Общий анализ сезонности")
                    
                    # Анализируем сезонность
                    seasonality_results = analyze_product_seasonality(
                        df_clean, date_column, value_column, product_column
                    )
                    
                    # Общая статистика
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        total_value = df_clean[value_column].sum()
                        st.metric("Общее значение", fmt_units(total_value))
                    
                    with col2:
                        avg_value = df_clean[value_column].mean()
                        st.metric("Среднее значение", fmt_units(avg_value))
                    
                    with col3:
                        max_value = df_clean[value_column].max()
                        st.metric("Максимальное значение", fmt_units(max_value))
                    
                    with col4:
                        min_value = df_clean[value_column].min()
                        st.metric("Минимальное значение", fmt_units(min_value))
                    
                    # Временной ряд
                    st.subheader("📈 Временной ряд")
                    
                    if product_column:
                        # Анализ по товарам
                        selected_product = st.selectbox(
                            "Выберите товар для анализа:",
                            list(seasonality_results.keys())
                        )
                        
                        if selected_product:
                            product_data = seasonality_results[selected_product]
                            
                            # График временного ряда
                            fig = go.Figure()
                            
                            fig.add_trace(go.Scatter(
                                x=product_data['monthly_data']['month'],
                                y=product_data['monthly_data'][value_column],
                                mode='lines+markers',
                                name='Исторические данные',
                                line=dict(color='blue', width=2),
                                marker=dict(size=6)
                            ))
                            
                            if product_data['forecast']:
                                future_months = []
                                last_month = pd.to_datetime(product_data['monthly_data']['month'].iloc[-1])
                                for i in range(len(product_data['forecast'])):
                                    future_month = last_month + pd.DateOffset(months=i+1)
                                    future_months.append(future_month.strftime('%Y-%m'))
                                
                                fig.add_trace(go.Scatter(
                                    x=future_months,
                                    y=product_data['forecast'],
                                    mode='lines+markers',
                                    name='Прогноз',
                                    line=dict(color='red', width=2, dash='dash'),
                                    marker=dict(size=6)
                                ))
                            
                            fig.update_layout(
                                title=f"Временной ряд для {selected_product}",
                                xaxis_title="Месяц",
                                yaxis_title=value_column,
                                hovermode='x unified'
                            )
                            
                            st.plotly_chart(fig, use_container_width=True)
                            
                            # Сезонные индексы
                            if product_data['seasonal_indexes']:
                                st.subheader("📊 Сезонные индексы")
                                
                                seasonal_df = pd.DataFrame({
                                    'Месяц': [calendar.month_name[i+1] for i in range(len(product_data['seasonal_indexes']))],
                                    'Сезонный индекс': product_data['seasonal_indexes']
                                })
                                
                                fig_seasonal = px.bar(
                                    seasonal_df,
                                    x='Месяц',
                                    y='Сезонный индекс',
                                    title="Сезонные индексы по месяцам",
                                    color='Сезонный индекс',
                                    color_continuous_scale='RdYlBu'
                                )
                                
                                st.plotly_chart(fig_seasonal, use_container_width=True)
                                
                                # Интерпретация
                                max_season = seasonal_df.loc[seasonal_df['Сезонный индекс'].idxmax()]
                                min_season = seasonal_df.loc[seasonal_df['Сезонный индекс'].idxmin()]
                                
                                st.info(f"""
                                **Интерпретация сезонности:**
                                - 🟢 **Пик сезона:** {max_season['Месяц']} (индекс: {max_season['Сезонный индекс']:.2f})
                                - 🔴 **Спад сезона:** {min_season['Месяц']} (индекс: {min_season['Сезонный индекс']:.2f})
                                - 📊 **Сила сезонности:** {product_data['seasonality_strength']:.2f}
                                """)
                    else:
                        # Общий анализ
                        overall_data = seasonality_results['overall']
                        
                        # График временного ряда
                        fig = go.Figure()
                        
                        fig.add_trace(go.Scatter(
                            x=overall_data['monthly_data']['month'],
                            y=overall_data['monthly_data'][value_column],
                            mode='lines+markers',
                            name='Исторические данные',
                            line=dict(color='blue', width=2),
                            marker=dict(size=6)
                        ))
                        
                        if overall_data['forecast']:
                            future_months = []
                            last_month = pd.to_datetime(overall_data['monthly_data']['month'].iloc[-1])
                            for i in range(len(overall_data['forecast'])):
                                future_month = last_month + pd.DateOffset(months=i+1)
                                future_months.append(future_month.strftime('%Y-%m'))
                            
                            fig.add_trace(go.Scatter(
                                x=future_months,
                                y=overall_data['forecast'],
                                mode='lines+markers',
                                name='Прогноз',
                                line=dict(color='red', width=2, dash='dash'),
                                marker=dict(size=6)
                            ))
                        
                        fig.update_layout(
                            title="Общий временной ряд",
                            xaxis_title="Месяц",
                            yaxis_title=value_column,
                            hovermode='x unified'
                        )
                        
                        st.plotly_chart(fig, use_container_width=True)
                        
                        # Сезонные индексы
                        if overall_data['seasonal_indexes']:
                            st.subheader("📊 Сезонные индексы")
                            
                            seasonal_df = pd.DataFrame({
                                'Месяц': [calendar.month_name[i+1] for i in range(len(overall_data['seasonal_indexes']))],
                                'Сезонный индекс': overall_data['seasonal_indexes']
                            })
                            
                            fig_seasonal = px.bar(
                                seasonal_df,
                                x='Месяц',
                                y='Сезонный индекс',
                                title="Сезонные индексы по месяцам",
                                color='Сезонный индекс',
                                color_continuous_scale='RdYlBu'
                            )
                            
                            st.plotly_chart(fig_seasonal, use_container_width=True)
                
                with tab2:
                    st.header("📈 Детальный анализ")
                    
                    if product_column:
                        # Сравнение товаров
                        st.subheader("📊 Сравнение сезонности товаров")
                        
                        # Создаем таблицу сравнения
                        comparison_data = []
                        for product, data in seasonality_results.items():
                            comparison_data.append({
                                'Товар': product,
                                'Общее значение': data['monthly_data'][value_column].sum(),
                                'Среднее значение': data['monthly_data'][value_column].mean(),
                                'Сила сезонности': data['seasonality_strength'] if data['seasonality_strength'] else 0,
                                'Период сезонности': data['seasonality_period'] if data['seasonality_period'] else 'Не определен'
                            })
                        
                        comparison_df = pd.DataFrame(comparison_data)
                        st.dataframe(comparison_df, use_container_width=True)
                        
                        # Тепловая карта сезонности
                        st.subheader("🔥 Тепловая карта сезонности")
                        
                        # Создаем матрицу для тепловой карты
                        heatmap_data = []
                        months = [calendar.month_name[i+1] for i in range(12)]
                        
                        for product, data in seasonality_results.items():
                            if data['seasonal_indexes']:
                                heatmap_data.append(data['seasonal_indexes'])
                        
                        if heatmap_data:
                            fig_heatmap = go.Figure(data=go.Heatmap(
                                z=heatmap_data,
                                x=months,
                                y=list(seasonality_results.keys()),
                                colorscale='RdYlBu',
                                text=[[f"{val:.2f}" for val in row] for row in heatmap_data],
                                texttemplate="%{text}",
                                textfont={"size": 10},
                                hoverongaps=False
                            ))
                            
                            fig_heatmap.update_layout(
                                title="Тепловая карта сезонных индексов",
                                xaxis_title="Месяц",
                                yaxis_title="Товар"
                            )
                            
                            st.plotly_chart(fig_heatmap, use_container_width=True)
                    else:
                        st.info("Для детального анализа выберите столбец для группировки по товарам")
                
                with tab3:
                    st.header("📋 Исходные данные")
                    
                    # Отображение данных
                    st.dataframe(df_clean, use_container_width=True)
                    
                    # Статистика
                    st.subheader("📊 Статистика данных")
                    
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.metric("Всего записей", len(df_clean))
                    
                    with col2:
                        if product_column:
                            st.metric("Уникальных товаров", df_clean[product_column].nunique())
                    
                    with col3:
                        st.metric("Период данных", f"{df_clean[date_column].min().strftime('%Y-%m')} - {df_clean[date_column].max().strftime('%Y-%m')}")
                    
                    # Экспорт данных
                    csv = df_clean.to_csv(index=False, encoding='utf-8-sig')
                    st.download_button(
                        label="📥 Скачать данные (CSV)",
                        data=csv,
                        file_name="сезонность_данные.csv",
                        mime="text/csv"
                    )
    else:
        st.error("❌ Не удалось прочитать файл. Проверьте формат и содержимое файла.")

# Футер
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666;'>
    <p>📈 Анализ сезонности товаров | Создано с помощью Streamlit</p>
</div>
""", unsafe_allow_html=True)
