#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import json
import os
from io import BytesIO
import numpy as np
from scipy.optimize import newton
import warnings
warnings.filterwarnings('ignore')

# Настройка страницы
st.set_page_config(
    page_title="Анализатор еженедельных расходов WB",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Настройка стилей
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
        margin: 0.5rem 0;
    }
    .expense-card {
        background-color: #fff3cd;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #ffc107;
        margin: 0.5rem 0;
    }
    .total-card {
        background-color: #d4edda;
        padding: 1.5rem;
        border-radius: 0.5rem;
        border-left: 4px solid #28a745;
        margin: 1rem 0;
    }
    .period-info {
        background-color: #e8f4fd;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #ff6b35;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Заголовок приложения
st.markdown('<h1 class="main-header">💰 Анализатор еженедельных расходов Wildberries</h1>', unsafe_allow_html=True)

@st.cache_data
def load_expenses_data(file_path='3.xlsx'):
    """Загружает данные о расходах из Excel файла"""
    try:
        df = pd.read_excel(file_path)
        return load_expenses_data_from_df(df)
    except Exception as e:
        st.error(f"Ошибка при загрузке файла: {str(e)}")
        return None

def load_expenses_data_from_df(df):
    """Обрабатывает DataFrame с данными о расходах"""
    try:
        # Преобразуем даты
        date_columns = ['Дата начала', 'Дата конца']
        for col in date_columns:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors='coerce')
        
        # Удаляем строки с пустыми датами
        df = df.dropna(subset=['Дата начала', 'Дата конца'])
        
        # Сортируем по дате начала
        df = df.sort_values('Дата начала')
        
        return df
    except Exception as e:
        st.error(f"Ошибка при обработке данных: {str(e)}")
        return None

def save_investments_to_file(investment_data, filename='investments_data.json'):
    """Сохраняет данные о вложениях в JSON файл"""
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(investment_data, f, ensure_ascii=False, indent=2, default=str)
        return True
    except Exception as e:
        st.error(f"Ошибка сохранения данных: {e}")
        return False

def save_uploaded_table(df, filename, table_name):
    """Сохраняет загруженную таблицу в папку uploaded_tables"""
    try:
        # Создаем папку если её нет
        os.makedirs('uploaded_tables', exist_ok=True)
        
        # Сохраняем таблицу
        file_path = f'uploaded_tables/{filename}'
        df.to_excel(file_path, index=False)
        
        # Сохраняем метаданные
        metadata_file = 'uploaded_tables/metadata.json'
        metadata = {}
        
        if os.path.exists(metadata_file):
            with open(metadata_file, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
        
        metadata[filename] = {
            'name': table_name,
            'upload_date': datetime.now().isoformat(),
            'rows': len(df),
            'columns': list(df.columns),
            'file_path': file_path
        }
        
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
        
        return True
    except Exception as e:
        st.error(f"Ошибка сохранения таблицы: {e}")
        return False

def load_uploaded_tables():
    """Загружает список сохраненных таблиц"""
    try:
        metadata_file = 'uploaded_tables/metadata.json'
        if os.path.exists(metadata_file):
            with open(metadata_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    except Exception as e:
        st.error(f"Ошибка загрузки списка таблиц: {e}")
        return {}

def load_table_by_filename(filename):
    """Загружает таблицу по имени файла"""
    try:
        file_path = f'uploaded_tables/{filename}'
        if os.path.exists(file_path):
            return pd.read_excel(file_path)
        return None
    except Exception as e:
        st.error(f"Ошибка загрузки таблицы {filename}: {e}")
        return None

def analyze_single_file(filename, info):
    """Анализирует отдельный файл"""
    st.markdown(f"## 📄 {info['name']}")
    
    # Загружаем данные
    df = load_table_by_filename(filename)
    if df is None:
        st.error("Не удалось загрузить файл")
        return
    
    # Обрабатываем данные
    df = load_expenses_data_from_df(df)
    if df is None:
        st.error("Ошибка при обработке данных")
        return
    
    # Анализируем файл
    analyze_single_file_data(df, info['name'])

def analyze_single_file_data(df, file_name):
    """Анализирует данные одного файла"""
    # Показываем информацию о загруженных данных
    df_display = df.copy()
    
    # Проверяем и преобразуем даты в datetime если нужно
    if not pd.api.types.is_datetime64_any_dtype(df_display['Дата начала']):
        df_display['Дата начала'] = pd.to_datetime(df_display['Дата начала'], errors='coerce')
    if not pd.api.types.is_datetime64_any_dtype(df_display['Дата конца']):
        df_display['Дата конца'] = pd.to_datetime(df_display['Дата конца'], errors='coerce')
    
    # Убираем временные зоны
    if df_display['Дата начала'].dt.tz is not None:
        df_display['Дата начала'] = df_display['Дата начала'].dt.tz_localize(None)
    if df_display['Дата конца'].dt.tz is not None:
        df_display['Дата конца'] = df_display['Дата конца'].dt.tz_localize(None)
    
    min_start = df_display['Дата начала'].min()
    max_end = df_display['Дата конца'].max()
    
    # Определяем min_date и max_date для использования в инвестициях
    min_date = df_display['Дата начала'].min()
    max_date = df_display['Дата конца'].max()
    
    # Получаем юридическое лицо из данных
    legal_entity = df['Юридическое лицо'].iloc[0] if 'Юридическое лицо' in df.columns else "Неизвестно"
    
    # Загрузка и кеширование вложенных средств по юридическому лицу
    if 'investment_data' not in st.session_state:
        st.session_state.investment_data = load_investments_from_file()
    
    investment_data = st.session_state.investment_data
    
    # Получаем список всех вложений для данного юридического лица
    investments_list = investment_data.get(f"{legal_entity}_list", [])
    
    # Проверяем есть ли сохраненные данные
    if investments_list:
        saved_amount = sum(inv['amount'] for inv in investments_list)
        saved_date = investments_list[0]['date']
        has_investment = True
    else:
        saved_amount = investment_data.get(legal_entity, 0.0)
        saved_date = investment_data.get(f"{legal_entity}_date", min_date.date())
        has_investment = saved_amount > 0
        
        # Если есть старое формате данных, конвертируем в новый
        if has_investment:
            investments_list = [{
                'amount': saved_amount,
                'date': saved_date,
                'id': 1
            }]
            investment_data[f"{legal_entity}_list"] = investments_list
    
    # Сворачиваемый блок информации о данных
    with st.expander("📋 Информация о данных", expanded=False):
        st.markdown(f"""
        <div class="period-info">
            <p><strong>Файл:</strong> {file_name}</p>
            <p><strong>Юридическое лицо:</strong> {legal_entity}</p>
            <p><strong>Всего отчетов:</strong> {len(df)}</p>
            <p><strong>Период:</strong> с {min_start.strftime('%d.%m.%Y') if pd.notna(min_start) else 'Н/Д'} по {max_end.strftime('%d.%m.%Y') if pd.notna(max_end) else 'Н/Д'}</p>
            <p><strong>Доступные столбцы:</strong> {', '.join(df.columns.tolist())}</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Управление вложениями для данного юридического лица
    with st.expander(f"💰 Управление вложениями ({legal_entity})", expanded=False):
        st.markdown(f"### 💰 Управление вложенными средствами - {legal_entity}")
        
        # Показываем историю вложений
        if investments_list:
            st.markdown("#### 📋 История вложений")
            for i, inv in enumerate(investments_list, 1):
                with st.container():
                    col_info, col_actions = st.columns([3, 1])
                    
                    with col_info:
                        st.markdown(f"""
                        **Вложение #{i}**  
                        💰 Сумма: {inv['amount']:,.0f} ₽  
                        📅 Дата: {inv['date']}
                        """)
                    
                    with col_actions:
                        if st.button("✏️", key=f"edit_{legal_entity}_{i}", help=f"Редактировать вложение #{i}"):
                            st.session_state[f"editing_{legal_entity}_{i}"] = True
                        
                        if st.button("🗑️", key=f"delete_{legal_entity}_{i}", help=f"Удалить вложение #{i}"):
                            investments_list.pop(i-1)
                            investment_data[f"{legal_entity}_list"] = investments_list
                            st.session_state.investment_data = investment_data
                            save_investments_to_file(investment_data)
                            st.success(f"✅ Вложение #{i} удалено!")
                            st.rerun()
                    
                    # Форма редактирования
                    if st.session_state.get(f"editing_{legal_entity}_{i}", False):
                        with st.form(key=f"edit_form_{legal_entity}_{i}"):
                            new_amount = st.number_input("Сумма вложения (₽)", value=float(inv['amount']), key=f"edit_amount_{legal_entity}_{i}")
                            new_date = st.date_input("Дата вложения", value=inv['date'], key=f"edit_date_{legal_entity}_{i}")
                            
                            col_submit, col_cancel = st.columns(2)
                            with col_submit:
                                if st.form_submit_button("💾 Сохранить"):
                                    inv['amount'] = new_amount
                                    inv['date'] = new_date
                                    investment_data[f"{legal_entity}_list"] = investments_list
                                    st.session_state.investment_data = investment_data
                                    save_investments_to_file(investment_data)
                                    st.session_state[f"editing_{legal_entity}_{i}"] = False
                                    st.success(f"✅ Вложение #{i} обновлено!")
                                    st.rerun()
                            
                            with col_cancel:
                                if st.form_submit_button("❌ Отмена"):
                                    st.session_state[f"editing_{legal_entity}_{i}"] = False
                                    st.rerun()
        
        # Добавление нового вложения
        with st.form(key=f"add_investment_{legal_entity}"):
            st.markdown("#### ➕ Добавить новое вложение")
            new_amount = st.number_input("Сумма вложения (₽)", min_value=0.0, key=f"new_amount_{legal_entity}")
            new_date = st.date_input("Дата вложения", key=f"new_date_{legal_entity}")
            
            if st.form_submit_button("💾 Добавить вложение"):
                if new_amount > 0:
                    new_id = max([inv['id'] for inv in investments_list], default=0) + 1
                    new_investment = {
                        'amount': new_amount,
                        'date': new_date,
                        'id': new_id
                    }
                    investments_list.append(new_investment)
                    investment_data[f"{legal_entity}_list"] = investments_list
                    st.session_state.investment_data = investment_data
                    save_investments_to_file(investment_data)
                    st.success(f"✅ Новое вложение добавлено!")
                    st.rerun()
                else:
                    st.error("Сумма должна быть больше 0")
        
        # Кнопка сохранения в кеш
        if st.button("💾 Сохранить вложения в кеш", key=f"save_cache_{legal_entity}"):
            save_investments_to_file(investment_data)
            st.success("✅ Вложения сохранены в кеш!")
    
    # Фильтр дат с ползунком
    st.markdown("### 📅 Фильтр по периодам")
    
    # Показываем информацию о полном периоде данных
    st.info(f"📊 **Полный период данных в таблице:** с {min_date.strftime('%d.%m.%Y')} по {max_date.strftime('%d.%m.%Y')} ({len(df)} недель)")
    
    # Проверяем настройку ROI с даты первого вложения
    use_first_investment_date = st.session_state.get(f"roi_first_date_{legal_entity}", False)
    
    # Определяем начальную дату для фильтра
    if use_first_investment_date and investments_list:
        # Используем дату первого вложения как начальную дату
        filter_start_date = investments_list[0]['date']
        # Показываем информацию о том, что фильтр установлен автоматически
        st.info(f"📅 Фильтр автоматически установлен с даты первого вложения: {filter_start_date.strftime('%d.%m.%Y')}")
    else:
        # По умолчанию используем полный период из таблицы
        filter_start_date = min_date.date()
    
    # Ползунок для выбора периода (по умолчанию полный период)
    date_range = st.slider(
        "Выберите период (по умолчанию полный период из таблицы)",
        min_value=min_date.date(),
        max_value=max_date.date(),
        value=(filter_start_date, max_date.date()),
        format="DD.MM.YYYY",
        key=f"date_slider_{legal_entity}"
    )
    
    start_date, end_date = date_range
    
    # Применяем фильтр
    start_datetime = pd.to_datetime(start_date)
    end_datetime = pd.to_datetime(end_date)
    
    # Убираем временные зоны из дат в данных для корректного сравнения
    df_filtered = df.copy()
    
    # Проверяем и преобразуем даты в datetime если нужно
    if not pd.api.types.is_datetime64_any_dtype(df_filtered['Дата начала']):
        df_filtered['Дата начала'] = pd.to_datetime(df_filtered['Дата начала'], errors='coerce')
    if not pd.api.types.is_datetime64_any_dtype(df_filtered['Дата конца']):
        df_filtered['Дата конца'] = pd.to_datetime(df_filtered['Дата конца'], errors='coerce')
    
    # Убираем временные зоны
    if df_filtered['Дата начала'].dt.tz is not None:
        df_filtered['Дата начала'] = df_filtered['Дата начала'].dt.tz_localize(None)
    if df_filtered['Дата конца'].dt.tz is not None:
        df_filtered['Дата конца'] = df_filtered['Дата конца'].dt.tz_localize(None)
    
    # Фильтруем данные по выбранному периоду
    filtered_df = df_filtered[
        (df_filtered['Дата начала'] >= start_datetime) & 
        (df_filtered['Дата конца'] <= end_datetime)
    ]
    
    if filtered_df.empty:
        st.warning("⚠️ Нет данных в выбранном периоде")
        return
    
    # Рассчитываем расходы
    expenses = calculate_expenses(filtered_df)
    
    # Получаем данные для отображения
    total_to_pay = expenses['total_to_pay']
    tax_amount = total_to_pay['amount'] * 0.07  # 7% налог
    total_after_tax = total_to_pay['amount'] - tax_amount
    
    # Общие суммы
    total_expenses = expenses['logistics']['amount'] + expenses['storage']['amount'] + expenses['other']['amount']
    total_amount = total_to_pay['amount'] + total_expenses
    
    # Процент расходов от общей суммы
    expenses_percentage = (total_expenses / total_amount) * 100 if total_amount > 0 else 0
    
    # Создаем сетку KPI метрик (3x3)
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            label="💰 Итого к оплате",
            value=f"{total_to_pay['amount']:,.0f} ₽",
            delta=f"Среднее: {total_to_pay['avg_per_week']:,.0f} ₽/нед"
        )
        
        st.metric(
            label="📊 Общая сумма",
            value=f"{total_amount:,.0f} ₽",
            delta=f"Доходы + Расходы"
        )
        
        st.metric(
            label="📅 Период",
            value=f"{len(filtered_df)} недель",
            delta=f"С {start_date.strftime('%d.%m.%Y')} по {end_date.strftime('%d.%m.%Y')}"
        )
    
    with col2:
        st.metric(
            label="💸 Налог (7%)",
            value=f"{tax_amount:,.0f} ₽",
            delta=f"{(tax_amount/total_to_pay['amount']*100):.1f}% от дохода"
        )
        
        st.metric(
            label="📈 Все расходы",
            value=f"{total_expenses:,.0f} ₽",
            delta=f"{expenses_percentage:.1f}% от общей суммы"
        )
        
        st.metric(
            label="✅ Итого к оплате (налог)",
            value=f"{total_after_tax:,.0f} ₽",
            delta=f"Чистая прибыль"
        )
    
    with col3:
        # Метрики инвестиций (если есть вложения)
        if has_investment and saved_amount > 0:
            # Расчет ROI с даты первого вложения
            if investments_list and len(investments_list) > 0:
                first_investment_date = min(inv['date'] for inv in investments_list)
                
                # Фильтруем данные с даты первого вложения
                df_from_investment = df_filtered[df_filtered['Дата начала'] >= pd.to_datetime(first_investment_date)]
                
                if not df_from_investment.empty:
                    # Рассчитываем расходы с даты первого вложения
                    expenses_from_investment = calculate_expenses(df_from_investment)
                    total_after_tax_from_investment = expenses_from_investment['total_to_pay']['amount'] * 0.93  # минус 7% налог
                    
                    # ROI с даты первого вложения
                    profit_after_tax_from_investment = total_after_tax_from_investment - saved_amount
                    roi = (profit_after_tax_from_investment / saved_amount) * 100 if saved_amount > 0 else 0
                    
                    # Прибыль после налога для отображения (с выбранного периода)
                    profit_after_tax = total_after_tax - saved_amount
                else:
                    # Если нет данных с даты вложения, используем текущий период
                    profit_after_tax = total_after_tax - saved_amount
                    roi = (profit_after_tax / saved_amount) * 100 if saved_amount > 0 else 0
            else:
                # Если нет списка вложений, используем текущий период
                profit_after_tax = total_after_tax - saved_amount
                roi = (profit_after_tax / saved_amount) * 100 if saved_amount > 0 else 0
            
            # Расчет настоящего XIRR
            if investments_list and len(investments_list) > 0:
                # Создаем денежные потоки для XIRR
                cashflows = []
                dates = []
                
                # Добавляем все вложения (отрицательные потоки)
                for inv in investments_list:
                    cashflows.append(-inv['amount'])  # Отрицательные = вложения
                    dates.append(inv['date'])
                
                # Добавляем финальный доход (положительный поток)
                if total_after_tax > 0:
                    cashflows.append(total_after_tax)  # Положительный = доход
                    dates.append(pd.Timestamp.now().date())
                
                # Рассчитываем XIRR
                if len(cashflows) >= 2:
                    xirr_result = calculate_xirr(cashflows, dates)
                    xirr = xirr_result if xirr_result is not None else 0
                else:
                    xirr = 0
            else:
                xirr = 0
            
            st.metric(
                label="💵 Прибыль после налога",
                value=f"{profit_after_tax:,.0f} ₽",
                delta=f"Чистая прибыль"
            )
            
            st.metric(
                label="📈 ROI",
                value=f"{roi:.1f}%",
                delta=f"С даты первого вложения"
            )
            
            st.metric(
                label="🎯 XIRR",
                value=f"{xirr:.1f}%",
                delta=f"Внутренняя норма доходности"
            )
        else:
            st.metric(
                label="💵 Прибыль после налога",
                value="0 ₽",
                delta="Нет вложений"
            )
            
            st.metric(
                label="📈 ROI",
                value="0%",
                delta="Нет вложений"
            )
            
            st.metric(
                label="🎯 XIRR",
                value="0%",
                delta="Нет вложений"
            )
    
    # Детальная таблица расходов по неделям
    st.markdown("### 📋 Детальная таблица расходов по неделям")
    
    # Создаем копию для отображения с форматированием
    display_df = filtered_df.copy()
    
    # Форматируем числовые колонки
    format_columns = ['Стоимость логистики', 'Стоимость хранения', 'Прочие удержания']
    if 'Итого к оплате' in display_df.columns:
        format_columns.append('Итого к оплате')
    if 'Общая сумма штрафов' in display_df.columns:
        format_columns.append('Общая сумма штрафов')
    
    for col in format_columns:
        if col in display_df.columns:
            display_df[col] = display_df[col].apply(lambda x: f"{x:,.0f} ₽" if pd.notna(x) else "0 ₽")
    
    st.dataframe(display_df, use_container_width=True)
    
    # Графики на полную ширину
    st.markdown("### 📈 Графики по метрике 'Итого к оплате'")
    
    # График 1: Динамика "Итого к оплате" по неделям
    if 'Итого к оплате' in filtered_df.columns:
        # Убираем временные зоны для корректного отображения
        def remove_timezone(x):
            if hasattr(x, 'tz') and x.tz is not None:
                return x.tz_localize(None)
            return x
        
        dates_without_tz = filtered_df['Дата начала'].apply(remove_timezone)
        
        # Округляем суммы до целых рублей для графиков
        amounts_rounded = filtered_df['Итого к оплате'].round(0).astype(int)
        
        fig_total_pay = px.line(
            x=dates_without_tz,
            y=amounts_rounded,
            title='Динамика "Итого к оплате" по неделям',
            labels={'x': 'Дата', 'y': 'Итого к оплате (₽)'}
        )
        fig_total_pay.update_layout(height=400)
        fig_total_pay.update_yaxes(tickformat=",")
        st.plotly_chart(fig_total_pay, use_container_width=True)
    else:
        st.warning("⚠️ Данные 'Итого к оплате' отсутствуют в выбранном периоде")
    
    # График 2: Столбчатый график "Итого к оплате" по неделям
    if 'Итого к оплате' in filtered_df.columns:
        fig_total_bar = px.bar(
            x=dates_without_tz,
            y=amounts_rounded,
            title='"Итого к оплате" по неделям',
            labels={'x': 'Дата', 'y': 'Итого к оплате (₽)'}
        )
        fig_total_bar.update_layout(height=400)
        fig_total_bar.update_yaxes(tickformat=",")
        st.plotly_chart(fig_total_bar, use_container_width=True)
    else:
        st.warning("⚠️ Данные 'Итого к оплате' отсутствуют в выбранном периоде")
    
    # Сводка
    st.markdown("### 📋 Сводка по выбранному периоду")
    
    st.markdown(f"""
    <div class="total-card">
        <h3>📊 Итоги за период {start_date.strftime('%d.%m.%Y')} - {end_date.strftime('%d.%m.%Y')}</h3>
        <ul>
            <li><strong>Количество недель:</strong> {len(filtered_df)}</li>
            <li><strong>Итого к оплате:</strong> {expenses['total_to_pay']['amount']:,.0f} ₽</li>
            <li><strong>Налог (7%):</strong> {tax_amount:,.0f} ₽</li>
            <li><strong>Итого к оплате (налог):</strong> {total_after_tax:,.0f} ₽</li>
            <li><strong>Общая сумма (Итого к оплате + расходы):</strong> {total_amount:,.0f} ₽</li>
            <li><strong>Все расходы:</strong> {total_expenses:,.0f} ₽</li>
            <li><strong>Доля расходов от общей суммы:</strong> {expenses_percentage:.1f}%</li>
            <li><strong>Стоимость логистики:</strong> {expenses['logistics']['amount']:,.0f} ₽ ({expenses['logistics']['amount']/expenses['total']*100:.1f}%)</li>
            <li><strong>Стоимость хранения:</strong> {expenses['storage']['amount']:,.0f} ₽ ({expenses['storage']['amount']/expenses['total']*100:.1f}%)</li>
            <li><strong>Прочие удержания:</strong> {expenses['other']['amount']:,.0f} ₽ ({expenses['other']['amount']/expenses['total']*100:.1f}%)</li>
            <li><strong>Общая сумма штрафов:</strong> {expenses['penalties']['amount']:,.0f} ₽</li>
            <li><strong>Средние расходы за неделю:</strong> {expenses['total'] / len(filtered_df):,.0f} ₽</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    
    # Экспорт данных
    st.markdown("### 💾 Экспорт данных")
    
    if st.button("📥 Скачать отчет о расходах (Excel)", key=f"export_{legal_entity}"):
        # Создаем Excel файл с отчетами
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            # Основная таблица
            export_columns = ['Дата начала', 'Дата конца', 'Стоимость логистики', 'Стоимость хранения', 'Прочие удержания']
            if 'Итого к оплате' in filtered_df.columns:
                export_columns.append('Итого к оплате')
            if 'Общая сумма штрафов' in filtered_df.columns:
                export_columns.append('Общая сумма штрафов')
            
            filtered_df[export_columns].to_excel(
                writer, sheet_name='Детальные данные', index=False
            )
            
            # Сводка
            summary_indicators = ['Итого к оплате', 'Налог (7%)', 'Итого к оплате (налог)', 'Общая сумма (Итого к оплате + расходы)', 'Все расходы', 'Доля расходов от общей суммы (%)', 'Стоимость логистики', 'Стоимость хранения', 'Прочие удержания', 'Общая сумма штрафов', 'Количество недель']
            summary_values = [
                expenses['total_to_pay']['amount'],
                tax_amount,
                total_after_tax,
                total_amount,
                total_expenses,
                round(expenses_percentage, 1),
                expenses['logistics']['amount'],
                expenses['storage']['amount'],
                expenses['other']['amount'],
                expenses['penalties']['amount'],
                len(filtered_df)
            ]
            
            summary_data = {
                'Показатель': summary_indicators,
                'Значение': summary_values
            }
            pd.DataFrame(summary_data).to_excel(writer, sheet_name='Сводка', index=False)
        
        output.seek(0)
        st.download_button(
            label="Скачать файл",
            data=output.getvalue(),
            file_name=f"wb_расходы_{legal_entity}_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

def analyze_all_files(saved_tables):
    """Анализирует все файлы вместе (общий отчет)"""
    st.markdown("## 📊 Общий отчет по всем файлам")
    
    all_data = []
    legal_entities = set()
    
    # Загружаем все данные
    for filename, info in saved_tables.items():
        df = load_table_by_filename(filename)
        if df is not None:
            df = load_expenses_data_from_df(df)
            if df is not None:
                all_data.append(df)
                if 'Юридическое лицо' in df.columns:
                    legal_entities.update(df['Юридическое лицо'].unique())
    
    if not all_data:
        st.error("Нет данных для анализа")
        return
    
    # Объединяем все данные
    combined_df = pd.concat(all_data, ignore_index=True)
    
    # Показываем общую статистику
    st.markdown("### 📈 Общая статистика")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            label="📄 Всего файлов",
            value=len(saved_tables),
            delta="Загружено"
        )
    
    with col2:
        st.metric(
            label="📊 Всего записей",
            value=len(combined_df),
            delta="Строк данных"
        )
    
    with col3:
        st.metric(
            label="🏢 Юридических лиц",
            value=len(legal_entities),
            delta="Уникальных"
        )
    
    # Показываем юридические лица
    if legal_entities:
        st.markdown("### 🏢 Юридические лица")
        for entity in sorted(legal_entities):
            st.write(f"• {entity}")
    
    # Общий анализ расходов
    st.markdown("### 💰 Общий анализ расходов")
    
    # Рассчитываем общие расходы
    total_expenses = 0
    total_to_pay = 0
    
    if 'Стоимость логистики' in combined_df.columns:
        total_expenses += combined_df['Стоимость логистики'].sum()
    if 'Стоимость хранения' in combined_df.columns:
        total_expenses += combined_df['Стоимость хранения'].sum()
    if 'Прочие удержания' in combined_df.columns:
        total_expenses += combined_df['Прочие удержания'].sum()
    if 'Итого к оплате' in combined_df.columns:
        total_to_pay = combined_df['Итого к оплате'].sum()
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            label="💰 Общие расходы",
            value=f"{total_expenses:,.0f} ₽",
            delta="Все файлы"
        )
    
    with col2:
        st.metric(
            label="📈 Итого к оплате",
            value=f"{total_to_pay:,.0f} ₽",
            delta="Все файлы"
        )
    
    with col3:
        profit = total_to_pay - total_expenses
        st.metric(
            label="💵 Прибыль",
            value=f"{profit:,.0f} ₽",
            delta="Чистая прибыль"
        )
    
    # График по всем данным
    if 'Итого к оплате' in combined_df.columns and 'Дата начала' in combined_df.columns:
        st.markdown("### 📊 График по всем данным")
        
        # Сортируем по дате
        combined_df_sorted = combined_df.sort_values('Дата начала')
        
        fig_all = px.line(
            x=combined_df_sorted['Дата начала'],
            y=combined_df_sorted['Итого к оплате'],
            title='Динамика "Итого к оплате" по всем файлам',
            labels={'x': 'Дата', 'y': 'Итого к оплате (₽)'}
        )
        fig_all.update_layout(height=400)
        st.plotly_chart(fig_all, use_container_width=True)

def analyze_sales_data(df):
    """Анализ данных продаж"""
    if df is None or df.empty:
        return None
    
    # Проверяем наличие колонок продаж
    sales_columns = [col for col in df.columns if 'продаж' in col.lower() or 'продажа' in col.lower()]
    
    if not sales_columns:
        st.warning("В таблице не найдены колонки с данными о продажах")
        return None
    
    analysis = {
        'total_sales': df[sales_columns[0]].sum() if sales_columns else 0,
        'avg_sales_per_week': df[sales_columns[0]].mean() if sales_columns else 0,
        'max_sales': df[sales_columns[0]].max() if sales_columns else 0,
        'min_sales': df[sales_columns[0]].min() if sales_columns else 0,
        'sales_columns': sales_columns,
        'weeks_count': len(df)
    }
    
    return analysis

def analyze_profit_margin(df):
    """Анализ прибыльности"""
    if df is None or df.empty:
        return None
    
    # Ищем колонки с доходами и расходами
    income_columns = [col for col in df.columns if 'продаж' in col.lower() or 'продажа' in col.lower() or 'доход' in col.lower()]
    expense_columns = [col for col in df.columns if 'стоимость' in col.lower() or 'расход' in col.lower() or 'штраф' in col.lower()]
    
    if not income_columns:
        st.warning("Не найдены колонки с доходами")
        return None
    
    total_income = df[income_columns[0]].sum()
    total_expenses = sum(df[col].sum() for col in expense_columns) if expense_columns else 0
    
    profit = total_income - total_expenses
    margin = (profit / total_income * 100) if total_income > 0 else 0
    
    analysis = {
        'total_income': total_income,
        'total_expenses': total_expenses,
        'profit': profit,
        'margin_percent': margin,
        'income_columns': income_columns,
        'expense_columns': expense_columns
    }
    
    return analysis

def load_investments_from_file(filename='investments_data.json'):
    """Загружает данные о вложениях из JSON файла"""
    try:
        if os.path.exists(filename):
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
            # Конвертируем строки дат обратно в объекты date
            for legal_entity in data:
                if f"{legal_entity}_list" in data:
                    for investment in data[f"{legal_entity}_list"]:
                        if isinstance(investment['date'], str):
                            investment['date'] = datetime.strptime(investment['date'], '%Y-%m-%d').date()
            return data
        return {}
    except Exception as e:
        st.error(f"Ошибка загрузки данных: {e}")
        return {}

def calculate_xirr(cashflows, dates, guess=0.1):
    """
    Рассчитывает XIRR (Extended Internal Rate of Return)
    
    Args:
        cashflows: список денежных потоков (отрицательные = вложения, положительные = доходы)
        dates: список дат для каждого потока
        guess: начальное предположение для ставки (по умолчанию 10%)
    
    Returns:
        XIRR в процентах или None если не удалось рассчитать
    """
    try:
        # Преобразуем даты в дни от первой даты
        first_date = min(dates)
        days = [(d - first_date).days for d in dates]
        
        def npv(rate):
            """Рассчитывает NPV для данной ставки"""
            return sum(cf / ((1 + rate) ** (day / 365.25)) for cf, day in zip(cashflows, days))
        
        def npv_derivative(rate):
            """Производная NPV для метода Ньютона"""
            return sum(-cf * day / 365.25 / ((1 + rate) ** (day / 365.25 + 1)) for cf, day in zip(cashflows, days))
        
        # Используем метод Ньютона для нахождения ставки, при которой NPV = 0
        xirr_rate = newton(npv, guess, fprime=npv_derivative, maxiter=1000, tol=1e-8)
        
        # Проверяем, что результат разумен
        if -0.99 < xirr_rate < 10:  # от -99% до 1000%
            return xirr_rate * 100
        else:
            return None
            
    except (ValueError, RuntimeError, OverflowError):
        return None

def calculate_expenses(df):
    """Рассчитывает общую сумму расходов по категориям, итого к оплате и штрафы"""
    expense_columns = {
        'Стоимость логистики': 'logistics',
        'Стоимость хранения': 'storage', 
        'Прочие удержания': 'other'
    }
    
    expenses = {}
    total = 0
    
    for col, key in expense_columns.items():
        if col in df.columns:
            expenses[key] = {
                'name': col,
                'amount': df[col].sum(),
                'avg_per_week': df[col].sum() / len(df) if len(df) > 0 else 0
            }
            total += expenses[key]['amount']
        else:
            expenses[key] = {
                'name': col,
                'amount': 0,
                'avg_per_week': 0
            }
    
    # Добавляем "Итого к оплате"
    if 'Итого к оплате' in df.columns:
        expenses['total_to_pay'] = {
            'name': 'Итого к оплате',
            'amount': df['Итого к оплате'].sum(),
            'avg_per_week': df['Итого к оплате'].sum() / len(df) if len(df) > 0 else 0
        }
    else:
        expenses['total_to_pay'] = {
            'name': 'Итого к оплате',
            'amount': 0,
            'avg_per_week': 0
        }
    
    # Добавляем "Общую сумму штрафов"
    if 'Общая сумма штрафов' in df.columns:
        expenses['penalties'] = {
            'name': 'Общая сумма штрафов',
            'amount': df['Общая сумма штрафов'].sum(),
            'avg_per_week': df['Общая сумма штрафов'].sum() / len(df) if len(df) > 0 else 0
        }
    else:
        expenses['penalties'] = {
            'name': 'Общая сумма штрафов',
            'amount': 0,
            'avg_per_week': 0
        }
    
    expenses['total'] = total
    return expenses

def main():
    # Сайдбар для загрузки данных
    with st.sidebar:
        st.markdown("### 📁 Загрузка данных")
        
        uploaded_file = st.file_uploader(
            "Выберите Excel файл с отчетами WB", 
            type=['xlsx', 'xls'],
            help="Загрузите файл с отчетами Wildberries"
        )
        
        if uploaded_file is not None:
            # Сохраняем загруженный файл
            filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uploaded_file.name}"
            df = pd.read_excel(uploaded_file)
            
            # Сохраняем в папку uploaded_tables
            if save_uploaded_table(df, filename, uploaded_file.name):
                st.success(f"✅ Файл {uploaded_file.name} успешно загружен и сохранен")
                st.rerun()  # Перезагружаем страницу для обновления вкладок
    
    # Загружаем список всех сохраненных таблиц
    saved_tables = load_uploaded_tables()
    
    # Создаем вкладки для каждого файла + общий отчет
    if saved_tables:
        # Создаем вкладки для каждого файла
        tab_names = []
        for filename, info in saved_tables.items():
            tab_name = f"📄 {info['name'][:20]}..." if len(info['name']) > 20 else f"📄 {info['name']}"
            tab_names.append(tab_name)
        
        # Добавляем вкладку общего отчета
        tab_names.append("📊 Общий отчет")
        
        # Создаем вкладки
        tabs = st.tabs(tab_names)
        
        # Обрабатываем каждую вкладку с файлом
        for i, (filename, info) in enumerate(saved_tables.items()):
            with tabs[i]:
                analyze_single_file(filename, info)
        
        # Вкладка общего отчета
        with tabs[-1]:
            analyze_all_files(saved_tables)
    else:
        st.info("📁 Загрузите первый файл для начала работы")
        
        # Показываем кешированные данные если есть
        @st.cache_data
        def load_cached_data():
            try:
                return pd.read_excel('3.xlsx')
            except:
                return None
        
        df = load_cached_data()
        if df is not None:
            st.markdown("## 📄 Текущие данные (3.xlsx)")
            analyze_single_file_data(df, "Текущие данные")
    
    # Проверяем и преобразуем даты в datetime если нужно
    if not pd.api.types.is_datetime64_any_dtype(df_display['Дата начала']):
        df_display['Дата начала'] = pd.to_datetime(df_display['Дата начала'], errors='coerce')
    if not pd.api.types.is_datetime64_any_dtype(df_display['Дата конца']):
        df_display['Дата конца'] = pd.to_datetime(df_display['Дата конца'], errors='coerce')
    
    # Убираем временные зоны
    if df_display['Дата начала'].dt.tz is not None:
        df_display['Дата начала'] = df_display['Дата начала'].dt.tz_localize(None)
    if df_display['Дата конца'].dt.tz is not None:
        df_display['Дата конца'] = df_display['Дата конца'].dt.tz_localize(None)
    
    min_start = df_display['Дата начала'].min()
    max_end = df_display['Дата конца'].max()
    

    
    # Загрузка и кеширование вложенных средств по юридическому лицу
    if 'investment_data' not in st.session_state:
        # Загружаем данные из файла при первом запуске
        st.session_state.investment_data = load_investments_from_file()
    
    investment_data = st.session_state.investment_data
    
    # Получаем юридическое лицо из данных (используем исходные данные, а не отфильтрованные)
    legal_entity = df['Юридическое лицо'].iloc[0] if 'Юридическое лицо' in df.columns else "Неизвестно"
    
    # Определяем min_date и max_date для использования в инвестициях
    min_date = df_display['Дата начала'].min()
    max_date = df_display['Дата конца'].max()
    
    # Получаем список всех вложений для данного юридического лица
    investments_list = investment_data.get(f"{legal_entity}_list", [])
    
    # Проверяем есть ли сохраненные данные
    if investments_list:
        saved_amount = sum(inv['amount'] for inv in investments_list)
        saved_date = investments_list[0]['date']
        has_investment = True
    else:
        saved_amount = investment_data.get(legal_entity, 0.0)
        saved_date = investment_data.get(f"{legal_entity}_date", min_date.date())
        has_investment = saved_amount > 0
        
        # Если есть старое формате данных, конвертируем в новый
        if has_investment:
            investments_list = [{
                'amount': saved_amount,
                'date': saved_date,
                'id': 1
            }]
            investment_data[f"{legal_entity}_list"] = investments_list
    
    # Для демонстрации добавляем тестовые данные (можно удалить позже)
    if not investments_list:
        # Добавляем демонстрационные данные
        demo_investments = [
            {
                'amount': 1000000.0,
                'date': pd.Timestamp('2024-02-01').date(),
                'id': 1
            },
            {
                'amount': 500000.0,
                'date': pd.Timestamp('2024-06-15').date(),
                'id': 2
            }
        ]
        investment_data[f"{legal_entity}_list"] = demo_investments
        investments_list = demo_investments
        has_investment = True  # Показываем историю для демонстрации
    
    # Сворачиваемый блок информации о данных
    with st.expander("📋 Информация о данных", expanded=False):
        st.markdown(f"""
        <div class="period-info">
            <p><strong>Всего отчетов:</strong> {len(df)}</p>
            <p><strong>Период:</strong> с {min_start.strftime('%d.%m.%Y') if pd.notna(min_start) else 'Н/Д'} по {max_end.strftime('%d.%m.%Y') if pd.notna(max_end) else 'Н/Д'}</p>
            <p><strong>Доступные столбцы:</strong> {', '.join(df.columns.tolist())}</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Фильтр дат с ползунком
    st.markdown("### 📅 Фильтр по периодам")
    
    # Показываем информацию о полном периоде данных
    st.info(f"📊 **Полный период данных в таблице:** с {min_date.strftime('%d.%m.%Y')} по {max_date.strftime('%d.%m.%Y')} ({len(df)} недель)")
    
    # Проверяем настройку ROI с даты первого вложения
    use_first_investment_date = st.session_state.get(f"roi_first_date_{legal_entity}", False)
    
    # Определяем начальную дату для фильтра
    if use_first_investment_date and investments_list:
        # Используем дату первого вложения как начальную дату
        filter_start_date = investments_list[0]['date']
        # Показываем информацию о том, что фильтр установлен автоматически
        st.info(f"📅 Фильтр автоматически установлен с даты первого вложения: {filter_start_date.strftime('%d.%m.%Y')}")
    else:
        # По умолчанию используем полный период из таблицы
        filter_start_date = min_date.date()
    
    # Ползунок для выбора периода (по умолчанию полный период)
    date_range = st.slider(
        "Выберите период (по умолчанию полный период из таблицы)",
        min_value=min_date.date(),
        max_value=max_date.date(),
        value=(filter_start_date, max_date.date()),
        format="DD.MM.YYYY"
    )
    
    start_date, end_date = date_range
    
    # Применяем фильтр
    start_datetime = pd.to_datetime(start_date)
    end_datetime = pd.to_datetime(end_date)
    
    # Убираем временные зоны из дат в данных для корректного сравнения
    df_filtered = df.copy()
    
    # Проверяем и преобразуем даты в datetime если нужно
    if not pd.api.types.is_datetime64_any_dtype(df_filtered['Дата начала']):
        df_filtered['Дата начала'] = pd.to_datetime(df_filtered['Дата начала'], errors='coerce')
    if not pd.api.types.is_datetime64_any_dtype(df_filtered['Дата конца']):
        df_filtered['Дата конца'] = pd.to_datetime(df_filtered['Дата конца'], errors='coerce')
    
    # Убираем временные зоны
    if df_filtered['Дата начала'].dt.tz is not None:
        df_filtered['Дата начала'] = df_filtered['Дата начала'].dt.tz_localize(None)
    if df_filtered['Дата конца'].dt.tz is not None:
        df_filtered['Дата конца'] = df_filtered['Дата конца'].dt.tz_localize(None)
    
    filtered_df = df_filtered[
        (df_filtered['Дата начала'] >= start_datetime) & 
        (df_filtered['Дата конца'] <= end_datetime)
    ]
    
    if filtered_df.empty:
        st.warning("⚠️ Нет данных для выбранного периода")
        return
    
    # Рассчитываем расходы
    expenses = calculate_expenses(filtered_df)
    
    # Ввод суммы вложенных средств
    st.markdown("### 💰 Управление вложенными средствами")
    st.info(f"📋 Юридическое лицо: {legal_entity}")
    
    if has_investment:
        # Показываем текущие данные
        st.success(f"✅ Текущие вложения: {saved_amount:,.0f} ₽ от {saved_date.strftime('%d.%m.%Y')}")
        
        # Кнопка сохранения в кеш и файл
        if st.button("💾 Сохранить вложения", key=f"save_to_cache_{legal_entity}"):
            st.session_state.investment_data = investment_data
            if save_investments_to_file(investment_data):
                st.success("✅ Вложения сохранены в кеш и файл!")
            else:
                st.warning("⚠️ Вложения сохранены только в кеш!")
            st.rerun()
        
        # Галочка для выбора расчета ROI с даты первого вложения
        use_first_investment_date = st.checkbox(
            "📅 Считать ROI с даты первого вложения",
            value=False,
            key=f"roi_first_date_{legal_entity}",
            help="Если включено, ROI будет считаться только с даты первого вложения, автоматически устанавливая эту дату в фильтре"
        )
        
        # Показываем ROI от суммы после налога
        total_to_pay = expenses['total_to_pay']['amount']
        tax_amount = total_to_pay * 0.07  # 7% налог
        total_after_tax = total_to_pay - tax_amount
        
        # Используем общую сумму всех вложений для расчета ROI
        roi_amount = saved_amount  # Общая сумма всех вложений
        roi_label = "от всех вложений"
        
        roi = ((total_after_tax - roi_amount) / roi_amount) * 100 if roi_amount > 0 else 0
        st.info(f"💰 ROI {roi_label}: {roi:.1f}% (Прибыль после налога: {total_after_tax - roi_amount:,.0f} ₽)")
        
    else:
        # Если нет вложений, показываем подсказку
        st.info("💡 Добавьте данные о вложенных средствах для расчета ROI. Используйте кнопку '➕ Добавить вложение' в разделе истории вложений.")
    
    # Показываем все сохраненные вложения для данного юридического лица
    st.markdown("### 📋 История вложений")
    
    if has_investment:
        
        # Создаем красивый список вложений
        total_invested = 0
        for i, investment in enumerate(investments_list, 1):
            total_invested += investment['amount']
            days_invested = (pd.Timestamp.now().date() - investment['date']).days
            
            # Создаем компактные карточки вложений
            col1, col2 = st.columns([4, 1])
            
            with col1:
                st.markdown(f"""
                <div style="background-color: #f0f2f6; padding: 8px 12px; border-radius: 8px; border-left: 3px solid #00ff00; margin-bottom: 8px;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div style="font-weight: bold; color: #1f77b4; font-size: 0.9em;">💰 #{i}</div>
                        <div style="text-align: right; font-weight: bold; color: #00aa00;">{investment['amount']:,.0f} ₽</div>
                    </div>
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 4px;">
                        <div style="font-size: 0.8em; color: #666;">📅 {investment['date'].strftime('%d.%m.%Y')}</div>
                        <div style="font-size: 0.8em; color: #666;">⏱️ {days_invested} дн.</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                st.write("")  # Отступ для выравнивания
                
                # Кнопки управления порядком, редактирования и удаления
                col_up, col_down, col_edit, col_delete = st.columns(4)
                
                with col_up:
                    if st.button("⬆️", key=f"move_up_{legal_entity}_{i}", help=f"Переместить вложение #{i} вверх", disabled=(i==1)):
                        if i > 1:
                            # Меняем местами с предыдущим вложением
                            investments_list[i-1], investments_list[i-2] = investments_list[i-2], investments_list[i-1]
                            
                            # Обновляем данные
                            investment_data[f"{legal_entity}_list"] = investments_list
                            st.session_state.investment_data = investment_data
                            save_investments_to_file(investment_data)
                            st.success(f"✅ Вложение #{i} перемещено вверх!")
                            st.rerun()
                
                with col_down:
                    if st.button("⬇️", key=f"move_down_{legal_entity}_{i}", help=f"Переместить вложение #{i} вниз", disabled=(i==len(investments_list))):
                        if i < len(investments_list):
                            # Меняем местами со следующим вложением
                            investments_list[i-1], investments_list[i] = investments_list[i], investments_list[i-1]
                            
                            # Обновляем данные
                            investment_data[f"{legal_entity}_list"] = investments_list
                            st.session_state.investment_data = investment_data
                            save_investments_to_file(investment_data)
                            st.success(f"✅ Вложение #{i} перемещено вниз!")
                            st.rerun()
                
                with col_edit:
                    if st.button("✏️", key=f"edit_investment_{legal_entity}_{i}", help=f"Редактировать вложение #{i}"):
                        # Переключаемся в режим редактирования
                        st.session_state[f"editing_{legal_entity}_{i}"] = True
                        st.rerun()
                
                with col_delete:
                    if st.button("🗑️", key=f"delete_investment_{legal_entity}_{i}", help=f"Удалить вложение #{i}"):
                        # Удаляем конкретное вложение
                        investments_list.pop(i-1)
                        
                        # Обновляем общую сумму
                        if investments_list:
                            total_sum = sum(inv['amount'] for inv in investments_list)
                            investment_data[legal_entity] = total_sum
                            investment_data[f"{legal_entity}_date"] = investments_list[0]['date']
                            investment_data[f"{legal_entity}_list"] = investments_list
                        else:
                            # Если все вложения удалены, очищаем данные
                            if legal_entity in investment_data:
                                del investment_data[legal_entity]
                            if f"{legal_entity}_date" in investment_data:
                                del investment_data[f"{legal_entity}_date"]
                            if f"{legal_entity}_list" in investment_data:
                                del investment_data[f"{legal_entity}_list"]
                        
                        # Обновляем session_state и сохраняем в файл
                        st.session_state.investment_data = investment_data
                        save_investments_to_file(investment_data)
                        st.success(f"✅ Вложение #{i} удалено!")
                        st.rerun()
                
                # Проверяем режим редактирования
                if st.session_state.get(f"editing_{legal_entity}_{i}", False):
                    st.markdown("---")
                    st.markdown(f"**Редактирование вложения #{i}**")
                    
                    # Поля для редактирования
                    new_amount = st.number_input(
                        "Новая сумма (₽)",
                        min_value=0.0,
                        value=float(investment['amount']),
                        step=1000.0,
                        format="%.0f",
                        key=f"edit_amount_{legal_entity}_{i}"
                    )
                    
                    new_date = st.date_input(
                        "Новая дата",
                        value=investment['date'],
                        min_value=min_date.date(),
                        max_value=max_date.date(),
                        key=f"edit_date_{legal_entity}_{i}"
                    )
                    
                    col_save, col_cancel = st.columns(2)
                    with col_save:
                        if st.button("💾 Сохранить", key=f"save_edit_{legal_entity}_{i}"):
                            # Обновляем вложение
                            investments_list[i-1]['amount'] = new_amount
                            investments_list[i-1]['date'] = new_date
                            
                            # Обновляем общую сумму
                            total_sum = sum(inv['amount'] for inv in investments_list)
                            investment_data[legal_entity] = total_sum
                            investment_data[f"{legal_entity}_date"] = investments_list[0]['date']
                            investment_data[f"{legal_entity}_list"] = investments_list
                            
                            # Обновляем session_state и сохраняем в файл
                            st.session_state.investment_data = investment_data
                            save_investments_to_file(investment_data)
                            st.success(f"✅ Вложение #{i} обновлено!")
                            st.session_state[f"editing_{legal_entity}_{i}"] = False
                            st.rerun()
                    
                    with col_cancel:
                        if st.button("❌ Отмена", key=f"cancel_edit_{legal_entity}_{i}"):
                            st.session_state[f"editing_{legal_entity}_{i}"] = False
                            st.rerun()
        
        # Дополнительная информация
        col1, col2 = st.columns(2)
        with col1:
            st.metric("📊 Всего вложено", f"{total_invested:,.0f} ₽")
        with col2:
            if investments_list:
                earliest_date = min(inv['date'] for inv in investments_list)
                days_invested = (pd.Timestamp.now().date() - earliest_date).days
                years = days_invested // 365
                remaining_days = days_invested % 365
                if years > 0:
                    time_format = f"{years} г. {remaining_days} дн."
                else:
                    time_format = f"{days_invested} дн."
                st.metric("⏱️ Дней с первого вложения", time_format)
        
        # Кнопки управления
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("🔄 Сбросить кеш", key=f"reset_cache_{legal_entity}"):
                st.session_state.investment_data = {}
                save_investments_to_file({})  # Сохраняем пустой файл
                st.success("✅ Кеш очищен и файл обновлен!")
                st.rerun()
        with col2:
            if st.button("🗑️ Очистить демо-данные", key=f"clear_demo_{legal_entity}"):
                if f"{legal_entity}_list" in investment_data:
                    del investment_data[f"{legal_entity}_list"]
                    st.session_state.investment_data = investment_data
                    save_investments_to_file(investment_data)
                st.success("✅ Демонстрационные данные удалены!")
                st.rerun()
        with col3:
            if st.button("➕ Добавить вложение", key=f"add_investment_{legal_entity}"):
                st.session_state[f"adding_investment_{legal_entity}"] = True
                st.rerun()
    
    else:
        # Если нет вложений, показываем подсказку
        st.info("💡 История вложений пуста. Добавьте первое вложение, чтобы начать отслеживание.")
        
        # Кнопка добавления первого вложения
        if st.button("➕ Добавить первое вложение", key=f"add_first_investment_{legal_entity}"):
            st.session_state[f"adding_investment_{legal_entity}"] = True
            st.rerun()
    
    # Форма добавления нового вложения (общая для всех случаев)
    if st.session_state.get(f"adding_investment_{legal_entity}", False):
            st.markdown("---")
            st.markdown("**➕ Добавление нового вложения**")
            
            col_add1, col_add2 = st.columns(2)
            with col_add1:
                new_investment_amount = st.number_input(
                    "Сумма вложения (₽)",
                    min_value=0.0,
                    value=0.0,
                    step=1000.0,
                    format="%.0f",
                    key=f"new_investment_amount_{legal_entity}"
                )
            
            with col_add2:
                new_investment_date = st.date_input(
                    "Дата вложения",
                    value=min_date.date(),
                    min_value=min_date.date(),
                    max_value=max_date.date(),
                    key=f"new_investment_date_{legal_entity}"
                )
            
            col_save_add, col_cancel_add = st.columns(2)
            with col_save_add:
                if st.button("💾 Добавить", key=f"save_new_investment_{legal_entity}"):
                    if new_investment_amount > 0:
                        # Добавляем новое вложение
                        new_investment = {
                            'amount': new_investment_amount,
                            'date': new_investment_date,
                            'id': len(investments_list) + 1
                        }
                        investments_list.append(new_investment)
                        
                        # Обновляем общую сумму
                        total_sum = sum(inv['amount'] for inv in investments_list)
                        investment_data[legal_entity] = total_sum
                        investment_data[f"{legal_entity}_date"] = investments_list[0]['date']
                        investment_data[f"{legal_entity}_list"] = investments_list
                        
                        # Обновляем session_state и сохраняем в файл
                        st.session_state.investment_data = investment_data
                        save_investments_to_file(investment_data)
                        st.success("✅ Новое вложение добавлено!")
                        st.session_state[f"adding_investment_{legal_entity}"] = False
                        st.rerun()
                    else:
                        st.error("❌ Сумма должна быть больше 0")
            
            with col_cancel_add:
                if st.button("❌ Отмена", key=f"cancel_new_investment_{legal_entity}"):
                    st.session_state[f"adding_investment_{legal_entity}"] = False
                    st.rerun()
    
    # Главные KPI метрики
    st.markdown("### 💰 Ключевые показатели (KPI)")
    
    total_to_pay = expenses['total_to_pay']
    tax_amount = total_to_pay['amount'] * 0.07  # 7% налог
    total_after_tax = total_to_pay['amount'] - tax_amount
    
    # Общая сумма (Итого к оплате + все расходы)
    total_expenses = expenses['logistics']['amount'] + expenses['storage']['amount'] + expenses['other']['amount']
    total_amount = total_to_pay['amount'] + total_expenses
    
    # Процент расходов от общей суммы
    expenses_percentage = (total_expenses / total_amount) * 100 if total_amount > 0 else 0
    
    # Создаем сетку KPI метрик (3x3)
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            label="💰 Итого к оплате",
            value=f"{total_to_pay['amount']:,.0f} ₽",
            delta=f"Среднее: {total_to_pay['avg_per_week']:,.0f} ₽/нед"
        )
        
        st.metric(
            label="📊 Общая сумма",
            value=f"{total_amount:,.0f} ₽",
            delta=f"Доходы + Расходы"
        )
        
        st.metric(
            label="📅 Период",
            value=f"{len(filtered_df)} недель",
            delta=f"С {start_date.strftime('%d.%m.%Y')} по {end_date.strftime('%d.%m.%Y')}"
        )
    
    with col2:
        st.metric(
            label="💸 Налог (7%)",
            value=f"{tax_amount:,.0f} ₽",
            delta=f"{(tax_amount/total_to_pay['amount']*100):.1f}% от дохода"
        )
        
        st.metric(
            label="📈 Все расходы",
            value=f"{total_expenses:,.0f} ₽",
            delta=f"{expenses_percentage:.1f}% от общей суммы"
        )
        
        st.metric(
            label="✅ Итого к оплате (налог)",
            value=f"{total_after_tax:,.0f} ₽",
            delta=f"Чистая прибыль"
        )
    
    with col3:
        # Метрики инвестиций (если есть вложения)
        if has_investment and saved_amount > 0:
            # Расчет ROI с даты первого вложения
            if investments_list and len(investments_list) > 0:
                first_investment_date = min(inv['date'] for inv in investments_list)
                
                # Фильтруем данные с даты первого вложения
                df_from_investment = df_filtered[df_filtered['Дата начала'] >= pd.to_datetime(first_investment_date)]
                
                if not df_from_investment.empty:
                    # Рассчитываем расходы с даты первого вложения
                    expenses_from_investment = calculate_expenses(df_from_investment)
                    total_after_tax_from_investment = expenses_from_investment['total_to_pay']['amount'] * 0.93  # минус 7% налог
                    
                    # ROI с даты первого вложения
                    profit_after_tax_from_investment = total_after_tax_from_investment - saved_amount
                    roi = (profit_after_tax_from_investment / saved_amount) * 100 if saved_amount > 0 else 0
                    
                    # Прибыль после налога для отображения (с выбранного периода)
                    profit_after_tax = total_after_tax - saved_amount
                else:
                    # Если нет данных с даты вложения, используем текущий период
                    profit_after_tax = total_after_tax - saved_amount
                    roi = (profit_after_tax / saved_amount) * 100 if saved_amount > 0 else 0
            else:
                # Если нет списка вложений, используем текущий период
                profit_after_tax = total_after_tax - saved_amount
                roi = (profit_after_tax / saved_amount) * 100 if saved_amount > 0 else 0
            
            # Расчет настоящего XIRR
            if investments_list and len(investments_list) > 0:
                # Создаем денежные потоки для XIRR
                cashflows = []
                dates = []
                
                # Добавляем все вложения (отрицательные потоки)
                for inv in investments_list:
                    cashflows.append(-inv['amount'])  # Отрицательные = вложения
                    dates.append(inv['date'])
                
                # Добавляем финальный доход (положительный поток)
                if total_after_tax > 0:
                    cashflows.append(total_after_tax)  # Положительный = доход
                    dates.append(pd.Timestamp.now().date())
                
                # Рассчитываем XIRR
                if len(cashflows) >= 2:
                    xirr_result = calculate_xirr(cashflows, dates)
                    xirr = xirr_result if xirr_result is not None else 0
                else:
                    xirr = 0
            else:
                xirr = 0
            
            st.metric(
                label="💵 Прибыль после налога",
                value=f"{profit_after_tax:,.0f} ₽",
                delta=f"Чистая прибыль"
            )
            
            st.metric(
                label="📈 ROI",
                value=f"{roi:.1f}%",
                delta=f"С даты первого вложения"
            )
            
            st.metric(
                label="🎯 XIRR",
                value=f"{xirr:.1f}%",
                delta=f"Внутренняя норма доходности"
            )
        else:
            st.metric(
                label="💵 Прибыль после налога",
                value="0 ₽",
                delta="Нет вложений"
            )
            
            st.metric(
                label="📈 ROI",
                value="0%",
                delta="Нет вложений"
            )
            
            st.metric(
                label="🎯 XIRR",
                value="0%",
                delta="Нет вложений"
            )
    
    # Дополнительные метрики
    st.markdown("### 📊 Дополнительные метрики")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        logistics = expenses['logistics']
        st.markdown(f"""
        <div class="expense-card">
            <h4>🚚 Стоимость логистики</h4>
            <h2>{logistics['amount']:,.0f} ₽</h2>
            <p>Среднее за неделю: {logistics['avg_per_week']:,.0f} ₽</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        storage = expenses['storage']
        st.markdown(f"""
        <div class="expense-card">
            <h4>📦 Стоимость хранения</h4>
            <h2>{storage['amount']:,.0f} ₽</h2>
            <p>Среднее за неделю: {storage['avg_per_week']:,.0f} ₽</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        other = expenses['other']
        st.markdown(f"""
        <div class="expense-card">
            <h4>📋 Прочие удержания</h4>
            <h2>{other['amount']:,.0f} ₽</h2>
            <p>Среднее за неделю: {other['avg_per_week']:,.0f} ₽</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        penalties = expenses['penalties']
        st.markdown(f"""
        <div class="expense-card">
            <h4>⚠️ Общая сумма штрафов</h4>
            <h2>{penalties['amount']:,.0f} ₽</h2>
            <p>Среднее за неделю: {penalties['avg_per_week']:,.0f} ₽</p>
        </div>
        """, unsafe_allow_html=True)
    

    
    # Детальная таблица
    st.markdown("### 📋 Детальная таблица расходов по неделям")
    
    # Подготавливаем данные для отображения
    display_columns = ['Дата начала', 'Дата конца', 'Стоимость логистики', 'Стоимость хранения', 'Прочие удержания']
    if 'Итого к оплате' in filtered_df.columns:
        display_columns.append('Итого к оплате')
    if 'Общая сумма штрафов' in filtered_df.columns:
        display_columns.append('Общая сумма штрафов')
    
    display_df = filtered_df[display_columns].copy()
    
    # Форматируем даты
    display_df['Дата начала'] = display_df['Дата начала'].apply(lambda x: x.strftime('%d.%m.%Y') if pd.notna(x) else 'Н/Д')
    display_df['Дата конца'] = display_df['Дата конца'].apply(lambda x: x.strftime('%d.%m.%Y') if pd.notna(x) else 'Н/Д')
    
    # Добавляем столбец с общей суммой расходов за неделю
    expense_columns = ['Стоимость логистики', 'Стоимость хранения', 'Прочие удержания']
    display_df['Общая сумма расходов'] = filtered_df[expense_columns].sum(axis=1)
    
    # Форматируем числовые столбцы
    format_columns = expense_columns + ['Общая сумма расходов']
    if 'Итого к оплате' in display_df.columns:
        format_columns.append('Итого к оплате')
    if 'Общая сумма штрафов' in display_df.columns:
        format_columns.append('Общая сумма штрафов')
    
    for col in format_columns:
        if col in display_df.columns:
            display_df[col] = display_df[col].apply(lambda x: f"{x:,.0f} ₽" if pd.notna(x) else "0 ₽")
    
    st.dataframe(display_df, use_container_width=True)
    
    # Графики на полную ширину
    st.markdown("### 📈 Графики по метрике 'Итого к оплате'")
    
    # График 1: Динамика "Итого к оплате" по неделям
    if 'Итого к оплате' in filtered_df.columns:
        # Убираем временные зоны для корректного отображения
        def remove_timezone(x):
            if hasattr(x, 'tz') and x.tz is not None:
                return x.tz_localize(None)
            return x
        
        dates_without_tz = filtered_df['Дата начала'].apply(remove_timezone)
        
        # Округляем суммы до целых рублей для графиков
        amounts_rounded = filtered_df['Итого к оплате'].round(0).astype(int)
        
        fig_total_pay = px.line(
            x=dates_without_tz,
            y=amounts_rounded,
            title='Динамика "Итого к оплате" по неделям',
            labels={'x': 'Дата', 'y': 'Итого к оплате (₽)'}
        )
        fig_total_pay.update_layout(height=400)
        fig_total_pay.update_yaxes(tickformat=",")
        st.plotly_chart(fig_total_pay, use_container_width=True)
    else:
        st.warning("⚠️ Данные 'Итого к оплате' отсутствуют в выбранном периоде")
    
    # График 2: Столбчатый график "Итого к оплате" по неделям
    if 'Итого к оплате' in filtered_df.columns:
        fig_total_bar = px.bar(
            x=dates_without_tz,
            y=amounts_rounded,
            title='"Итого к оплате" по неделям',
            labels={'x': 'Дата', 'y': 'Итого к оплате (₽)'}
        )
        fig_total_bar.update_layout(height=400)
        fig_total_bar.update_yaxes(tickformat=",")
        st.plotly_chart(fig_total_bar, use_container_width=True)
    else:
        st.warning("⚠️ Данные 'Итого к оплате' отсутствуют в выбранном периоде")
    

    
    # Сводка
    st.markdown("### 📋 Сводка по выбранному периоду")
    
    st.markdown(f"""
    <div class="total-card">
        <h3>📊 Итоги за период {start_date.strftime('%d.%m.%Y')} - {end_date.strftime('%d.%m.%Y')}</h3>
        <ul>
            <li><strong>Количество недель:</strong> {len(filtered_df)}</li>
            <li><strong>Итого к оплате:</strong> {expenses['total_to_pay']['amount']:,.0f} ₽</li>
            <li><strong>Налог (7%):</strong> {tax_amount:,.0f} ₽</li>
            <li><strong>Итого к оплате (налог):</strong> {total_after_tax:,.0f} ₽</li>
            <li><strong>Общая сумма (Итого к оплате + расходы):</strong> {total_amount:,.0f} ₽</li>
            <li><strong>Все расходы:</strong> {total_expenses:,.0f} ₽</li>
            <li><strong>Доля расходов от общей суммы:</strong> {expenses_percentage:.1f}%</li>
            <li><strong>Стоимость логистики:</strong> {expenses['logistics']['amount']:,.0f} ₽ ({expenses['logistics']['amount']/expenses['total']*100:.1f}%)</li>
            <li><strong>Стоимость хранения:</strong> {expenses['storage']['amount']:,.0f} ₽ ({expenses['storage']['amount']/expenses['total']*100:.1f}%)</li>
            <li><strong>Прочие удержания:</strong> {expenses['other']['amount']:,.0f} ₽ ({expenses['other']['amount']/expenses['total']*100:.1f}%)</li>
            <li><strong>Общая сумма штрафов:</strong> {expenses['penalties']['amount']:,.0f} ₽</li>
            <li><strong>Средние расходы за неделю:</strong> {expenses['total'] / len(filtered_df):,.0f} ₽</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    
    # Экспорт данных
    st.markdown("### 💾 Экспорт данных")
    
    if st.button("📥 Скачать отчет о расходах (Excel)"):
        # Создаем Excel файл с отчетами
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            # Основная таблица
            export_columns = ['Дата начала', 'Дата конца', 'Стоимость логистики', 'Стоимость хранения', 'Прочие удержания']
            if 'Итого к оплате' in filtered_df.columns:
                export_columns.append('Итого к оплате')
            if 'Общая сумма штрафов' in filtered_df.columns:
                export_columns.append('Общая сумма штрафов')
            
            filtered_df[export_columns].to_excel(
                writer, sheet_name='Детальные данные', index=False
            )
            
            # Сводка
            summary_indicators = ['Итого к оплате', 'Налог (7%)', 'Итого к оплате (налог)', 'Общая сумма (Итого к оплате + расходы)', 'Все расходы', 'Доля расходов от общей суммы (%)', 'Стоимость логистики', 'Стоимость хранения', 'Прочие удержания', 'Общая сумма штрафов', 'Количество недель']
            summary_values = [
                expenses['total_to_pay']['amount'],
                tax_amount,
                total_after_tax,
                total_amount,
                total_expenses,
                round(expenses_percentage, 1),
                expenses['logistics']['amount'],
                expenses['storage']['amount'],
                expenses['other']['amount'],
                expenses['penalties']['amount'],
                len(filtered_df)
            ]
            
            summary_data = {
                'Показатель': summary_indicators,
                'Значение': summary_values
            }
            pd.DataFrame(summary_data).to_excel(writer, sheet_name='Сводка', index=False)
        
        output.seek(0)
        st.download_button(
            label="Скачать файл",
            data=output.getvalue(),
            file_name=f"wb_расходы_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    
    # Вкладка 2: Анализ продаж
    with tab2:
        st.markdown("## 📊 Анализ продаж")
        
        if df is not None:
            # Анализ продаж
            sales_analysis = analyze_sales_data(df)
            if sales_analysis:
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric(
                        label="💰 Общие продажи",
                        value=f"{sales_analysis['total_sales']:,.0f} ₽",
                        delta=f"За {sales_analysis['weeks_count']} недель"
                    )
                
                with col2:
                    st.metric(
                        label="📈 Средние продажи",
                        value=f"{sales_analysis['avg_sales_per_week']:,.0f} ₽/нед",
                        delta="В неделю"
                    )
                
                with col3:
                    st.metric(
                        label="🎯 Максимальные продажи",
                        value=f"{sales_analysis['max_sales']:,.0f} ₽",
                        delta="За неделю"
                    )
                
                # График продаж
                if 'Продажа' in df.columns:
                    fig_sales = px.line(
                        x=df['Дата начала'],
                        y=df['Продажа'],
                        title='Динамика продаж по неделям',
                        labels={'x': 'Дата', 'y': 'Продажи (₽)'}
                    )
                    fig_sales.update_layout(height=400)
                    st.plotly_chart(fig_sales, use_container_width=True)
            else:
                st.warning("Не удалось проанализировать данные продаж")
        else:
            st.error("Нет данных для анализа")
    
    # Вкладка 3: Управление данными
    with tab3:
        st.markdown("## 📁 Управление данными")
        
        # Показываем сохраненные таблицы
        saved_tables = load_uploaded_tables()
        
        if saved_tables:
            st.markdown("### 📋 Сохраненные таблицы")
            
            for filename, info in saved_tables.items():
                with st.expander(f"📄 {info['name']} ({info['upload_date'][:10]})"):
                    col1, col2, col3 = st.columns([2, 1, 1])
                    
                    with col1:
                        st.write(f"**Файл:** {filename}")
                        st.write(f"**Строк:** {info['rows']}")
                        st.write(f"**Колонок:** {len(info['columns'])}")
                    
                    with col2:
                        if st.button("👁️ Просмотр", key=f"view_{filename}"):
                            table_df = load_table_by_filename(filename)
                            if table_df is not None:
                                st.dataframe(table_df.head(10), use_container_width=True)
                    
                    with col3:
                        if st.button("🗑️ Удалить", key=f"delete_{filename}"):
                            try:
                                os.remove(f'uploaded_tables/{filename}')
                                # Обновляем метаданные
                                del saved_tables[filename]
                                with open('uploaded_tables/metadata.json', 'w', encoding='utf-8') as f:
                                    json.dump(saved_tables, f, ensure_ascii=False, indent=2)
                                st.success(f"Таблица {info['name']} удалена")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Ошибка удаления: {e}")
        else:
            st.info("Нет сохраненных таблиц")
        
        # Статистика
        st.markdown("### 📊 Статистика")
        st.write(f"**Всего сохранено таблиц:** {len(saved_tables)}")
        
        if saved_tables:
            total_rows = sum(info['rows'] for info in saved_tables.values())
            st.write(f"**Общее количество строк:** {total_rows:,}")

if __name__ == "__main__":
    main()
