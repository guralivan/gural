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
        date_columns = ['Дата формирования']
        for col in date_columns:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors='coerce')
        
        # Удаляем временные зоны только если даты в datetime формате
        for col in date_columns:
            if col in df.columns and pd.api.types.is_datetime64_any_dtype(df[col]):
                if hasattr(df[col].dt, 'tz') and df[col].dt.tz is not None:
                    df[col] = df[col].dt.tz_localize(None)
                else:
                    # Принудительно удаляем временные зоны
                    df[col] = df[col].dt.tz_localize(None)
        
        # Удаляем строки с пустыми датами
        df = df.dropna(subset=['Дата формирования'])
        
        # Проверяем, что даты действительно в datetime формате
        # Убираем эту проверку, так как она приводит к повторному преобразованию и потере данных
        # if not pd.api.types.is_datetime64_any_dtype(df['Дата начала']):
        #     df['Дата начала'] = pd.to_datetime(df['Дата начала'], errors='coerce')
        # if not pd.api.types.is_datetime64_any_dtype(df['Дата конца']):
        #     df['Дата конца'] = pd.to_datetime(df['Дата конца'], errors='coerce')
        
        # Сортируем по дате начала
        df = df.sort_values('Дата формирования')
        
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

def save_uploaded_report(uploaded_file, legal_entity):
    """Сохраняет загруженный отчет в папку и обновляет метаданные"""
    try:
        # Создаем папку если не существует
        os.makedirs('uploaded_reports', exist_ok=True)
        
        # Генерируем уникальное имя файла
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{legal_entity}_{timestamp}_{uploaded_file.name}"
        filepath = os.path.join('uploaded_reports', filename)
        
        # Сохраняем файл
        with open(filepath, 'wb') as f:
            f.write(uploaded_file.getbuffer())
        
        st.info(f"📁 Файл сохранен: {filepath}")
        
        # Загружаем и анализируем данные для получения метаданных
        df = pd.read_excel(uploaded_file)
        
        # Используем стандартную функцию обработки данных
        df = load_expenses_data_from_df(df)
        
        if df is None:
            st.error("Ошибка при обработке данных")
            return None, None
        
        # Получаем метаданные
        min_date = df['Дата формирования'].min()
        max_date = df['Дата конца'].max()
        total_records = len(df)
        records_2024 = len(df[df['Дата формирования'].dt.year == 2024])
        records_2025 = len(df[df['Дата формирования'].dt.year == 2025])
        
        # Создаем метаданные
        metadata = {
            'filename': filename,
            'original_name': uploaded_file.name,
            'legal_entity': legal_entity,
            'upload_date': datetime.now().isoformat(),
            'min_date': min_date.isoformat(),
            'max_date': max_date.isoformat(),
            'total_records': total_records,
            'records_2024': records_2024,
            'records_2025': records_2025
        }
        
        st.info(f"📊 Метаданные созданы: {total_records} записей")
        
        # Сохраняем метаданные
        save_report_metadata(metadata)
        
        st.success(f"✅ Отчет успешно сохранен: {filename}")
        
        return filepath, metadata
        
    except Exception as e:
        st.error(f"Ошибка сохранения отчета: {e}")
        import traceback
        st.error(f"Детали ошибки: {traceback.format_exc()}")
        return None, None

def save_report_metadata(metadata):
    """Сохраняет метаданные отчета в JSON файл"""
    try:
        metadata_file = 'uploaded_reports_metadata.json'
        
        # Загружаем существующие метаданные
        if os.path.exists(metadata_file):
            with open(metadata_file, 'r', encoding='utf-8') as f:
                all_metadata = json.load(f)
                st.info(f"📋 Загружены существующие метаданные: {len(all_metadata)} отчетов")
        else:
            all_metadata = []
            st.info("📋 Создан новый файл метаданных")
        
        # Добавляем новые метаданные
        all_metadata.append(metadata)
        
        # Сохраняем обновленные метаданные
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(all_metadata, f, ensure_ascii=False, indent=2)
        
        st.success(f"💾 Метаданные сохранены в {metadata_file}")
        st.info(f"📊 Всего отчетов в кеше: {len(all_metadata)}")
            
    except Exception as e:
        st.error(f"Ошибка сохранения метаданных: {e}")
        import traceback
        st.error(f"Детали ошибки: {traceback.format_exc()}")

def load_report_metadata():
    """Загружает метаданные всех сохраненных отчетов"""
    try:
        metadata_file = 'uploaded_reports_metadata.json'
        if os.path.exists(metadata_file):
            with open(metadata_file, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
                st.info(f"📋 Загружены метаданные: {len(metadata)} отчетов")
                return metadata
        else:
            st.info("📋 Файл метаданных не найден")
            return []
    except Exception as e:
        st.error(f"Ошибка загрузки метаданных: {e}")
        import traceback
        st.error(f"Детали ошибки: {traceback.format_exc()}")
        return []

def load_saved_report(filename):
    """Загружает сохраненный отчет по имени файла"""
    try:
        filepath = os.path.join('uploaded_reports', filename)
        if os.path.exists(filepath):
            return pd.read_excel(filepath)
        return None
    except Exception as e:
        st.error(f"Ошибка загрузки сохраненного отчета: {e}")
        return None

def get_latest_report_for_legal_entity(legal_entity):
    """Получает последний сохраненный отчет для указанного юридического лица"""
    try:
        metadata = load_report_metadata()
        entity_reports = [r for r in metadata if r['legal_entity'] == legal_entity]
        
        if entity_reports:
            # Сортируем по дате загрузки и берем последний
            latest_report = max(entity_reports, key=lambda x: x['upload_date'])
            return latest_report
        return None
    except Exception as e:
        st.error(f"Ошибка получения последнего отчета: {e}")
        return None

def auto_load_latest_reports():
    """Автоматически загружает последние отчеты для обоих юридических лиц"""
    auto_loaded = {}
    
    # Загружаем последний отчет для ЮЛ 1
    latest_ul1 = get_latest_report_for_legal_entity("ЮЛ 1")
    if latest_ul1:
        df1 = load_saved_report(latest_ul1['filename'])
        if df1 is not None:
            df1 = load_expenses_data_from_df(df1)
            auto_loaded['df1'] = df1
            auto_loaded['file_name_1'] = latest_ul1['original_name']
            auto_loaded['latest_ul1'] = latest_ul1
    
    # Загружаем последний отчет для ИП Гураль Д. Д.
    latest_ul2 = get_latest_report_for_legal_entity("ИП Гураль Д. Д.")
    if latest_ul2:
        df2 = load_saved_report(latest_ul2['filename'])
        if df2 is not None:
            df2 = load_expenses_data_from_df(df2)
            auto_loaded['df2'] = df2
            auto_loaded['file_name_2'] = latest_ul2['original_name']
            auto_loaded['latest_ul2'] = latest_ul2
    
    return auto_loaded

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
        # Преобразуем все даты в datetime.date объекты
        normalized_dates = []
        for date in dates:
            if isinstance(date, str):
                normalized_dates.append(pd.to_datetime(date).date())
            elif isinstance(date, pd.Timestamp):
                normalized_dates.append(date.date())
            else:
                normalized_dates.append(date)
        
        # Преобразуем даты в дни от первой даты
        first_date = min(normalized_dates)
        days = [(d - first_date).days for d in normalized_dates]
        
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

def calculate_roi_forecast_with_remaining_stock(current_roi, total_invested, remaining_stock_revenue, 
                                               remaining_stock_date, current_date=None, use_first_investment=False, 
                                               first_investment_date=None, current_profit=None):
    """
    Рассчитывает прогноз ROI с учетом реализации остатков
    
    Args:
        current_roi: текущий ROI в процентах
        total_invested: общая сумма вложений
        remaining_stock_revenue: выручка от реализации остатков (с учетом налога)
        remaining_stock_date: дата планируемой реализации остатков
        current_date: текущая дата (если None, используется сегодняшняя)
        use_first_investment: использовать расчет с даты первого вложения
        first_investment_date: дата первого вложения
        current_profit: текущая прибыль (если None, рассчитывается из ROI)
    
    Returns:
        dict: словарь с прогнозными данными
    """
    try:
        if current_date is None:
            current_date = datetime.now()
        
        # Преобразуем даты в datetime если они строки
        if isinstance(remaining_stock_date, str):
            remaining_stock_date = pd.to_datetime(remaining_stock_date)
        if isinstance(current_date, str):
            current_date = pd.to_datetime(current_date)
        
        # Проверяем, что общие вложения не равны нулю для расчета текущей прибыли
        if total_invested <= 0:
            st.warning("⚠️ Общие вложения равны нулю. Для расчета ROI необходимо добавить вложения.")
            return None
        
        # Текущая прибыль (используем переданную или рассчитываем из ROI)
        if current_profit is None:
            current_profit = (current_roi / 100) * total_invested
        
        # Выручка от остатков (вычитаем налог 7%)
        remaining_stock_profit = remaining_stock_revenue * 0.93  # минус 7% налог
        remaining_stock_revenue_after_tax = remaining_stock_revenue * 0.93  # выручка после налога
        
        # Проверяем корректность значений
        if remaining_stock_revenue < 0:
            st.warning("⚠️ Выручка от остатков не может быть отрицательной. Используем 0.")
            remaining_stock_profit = 0
            remaining_stock_revenue = 0
        
        # Общая прогнозируемая прибыль
        total_forecast_profit = current_profit + remaining_stock_profit
        
        # Общие вложения (остатки не добавляются к вложениям, так как это выручка)
        total_forecast_invested = total_invested
        
        # Проверяем, что общие вложения не равны нулю
        if total_forecast_invested <= 0:
            st.warning("⚠️ Общие вложения равны нулю. Для расчета ROI необходимо добавить вложения.")
            return None
        
        # Прогнозный ROI
        forecast_roi = (total_forecast_profit / total_forecast_invested) * 100
        
        # Дни до реализации остатков
        if use_first_investment and first_investment_date:
            # Если используется расчет с даты первого вложения, считаем дни от даты первого вложения
            days_to_realization = (remaining_stock_date - first_investment_date).days
            st.info(f"📅 Расчет производится с даты первого вложения: {first_investment_date.strftime('%d.%m.%Y')}")
        else:
            # Обычный расчет от текущей даты
            days_to_realization = (remaining_stock_date - current_date).days
        
        # Проверяем корректность дат
        if days_to_realization < 0:
            if use_first_investment and first_investment_date:
                st.warning("⚠️ Дата реализации остатков раньше даты первого вложения. Используем текущий ROI.")
            else:
                st.warning("⚠️ Дата реализации остатков в прошлом. Используем текущий ROI.")
            days_to_realization = 0
        
        # Годовой ROI (если остатки реализуются в течение года)
        if days_to_realization > 0:
            annualized_roi = (total_forecast_profit / total_forecast_invested) * (365 / days_to_realization) * 100
        else:
            annualized_roi = forecast_roi
        
        return {
            'current_roi': current_roi,
            'current_profit': current_profit,
            'remaining_stock_revenue': remaining_stock_revenue,
            'remaining_stock_revenue_after_tax': remaining_stock_revenue_after_tax,
            'remaining_stock_profit': remaining_stock_profit,
            'total_forecast_profit': total_forecast_profit,
            'total_forecast_invested': total_forecast_invested,
            'forecast_roi': forecast_roi,
            'annualized_roi': annualized_roi,
            'days_to_realization': days_to_realization,
            'remaining_stock_date': remaining_stock_date,
            'current_date': current_date,
            'use_first_investment': use_first_investment,
            'first_investment_date': first_investment_date
        }
        
    except Exception as e:
        st.error(f"Ошибка расчета прогноза ROI: {e}")
        return None

def calculate_period_format(start_date, end_date):
    """Рассчитывает период в формате 'год дней'"""
    try:
        # Рассчитываем разность в днях
        days_diff = (end_date - start_date).days
        
        # Рассчитываем годы и оставшиеся дни
        years = days_diff // 365
        remaining_days = days_diff % 365
        
        if years > 0:
            if remaining_days > 0:
                return f"{years} год {remaining_days} дней"
            else:
                return f"{years} год"
        else:
            return f"{remaining_days} дней"
    except:
        return "Н/Д"

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

def analyze_single_file_data(df, file_name, tab_prefix=""):
    """Анализирует данные одного файла"""
    # Показываем информацию о загруженных данных
    df_display = df.copy()
    
    # Обрабатываем только столбец "Дата формирования"
    
    # Определяем min_date и max_date для использования в инвестициях
    if pd.api.types.is_datetime64_any_dtype(df_display['Дата формирования']):
        min_date = df_display['Дата формирования'].min()
        max_date = df_display['Дата формирования'].max()
    else:
        # Если столбец не datetime, конвертируем его
        df_display['Дата формирования'] = pd.to_datetime(df_display['Дата формирования'])
        min_date = df_display['Дата формирования'].min()
        max_date = df_display['Дата формирования'].max()
    
    # Убираем временные зоны из min_date и max_date
    if hasattr(min_date, 'tz') and min_date.tz is not None:
        min_date = min_date.tz_localize(None)
    if hasattr(max_date, 'tz') and max_date.tz is not None:
        max_date = max_date.tz_localize(None)
    
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
            <p><strong>Период:</strong> с {min_date.strftime('%d.%m.%Y') if hasattr(min_date, 'strftime') else str(min_date)} по {max_date.strftime('%d.%m.%Y') if hasattr(max_date, 'strftime') else str(max_date)}</p>
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
                        if st.button("✏️", key=f"{tab_prefix}edit_{legal_entity}_{i}", help=f"Редактировать вложение #{i}"):
                            st.session_state[f"{tab_prefix}editing_{legal_entity}_{i}"] = True
                        
                        if st.button("🗑️", key=f"{tab_prefix}delete_{legal_entity}_{i}", help=f"Удалить вложение #{i}"):
                            investments_list.pop(i-1)
                            investment_data[f"{legal_entity}_list"] = investments_list
                            st.session_state.investment_data = investment_data
                            save_investments_to_file(investment_data)
                            st.success(f"✅ Вложение #{i} удалено!")
                            st.rerun()
                    
                    # Форма редактирования
                    if st.session_state.get(f"{tab_prefix}editing_{legal_entity}_{i}", False):
                        with st.form(key=f"{tab_prefix}edit_form_{legal_entity}_{i}"):
                            new_amount = st.number_input("Сумма вложения (₽)", value=float(inv['amount']), key=f"{tab_prefix}edit_amount_{legal_entity}_{i}")
                            new_date = st.date_input("Дата вложения", value=inv['date'], key=f"{tab_prefix}edit_date_{legal_entity}_{i}")
                            
                            col_submit, col_cancel = st.columns(2)
                            with col_submit:
                                if st.form_submit_button("💾 Сохранить"):
                                    inv['amount'] = new_amount
                                    inv['date'] = new_date
                                    investment_data[f"{legal_entity}_list"] = investments_list
                                    st.session_state.investment_data = investment_data
                                    save_investments_to_file(investment_data)
                                    st.session_state[f"{tab_prefix}editing_{legal_entity}_{i}"] = False
                                    st.success(f"✅ Вложение #{i} обновлено!")
                                    st.rerun()
                            
                            with col_cancel:
                                if st.form_submit_button("❌ Отмена"):
                                    st.session_state[f"{tab_prefix}editing_{legal_entity}_{i}"] = False
                                    st.rerun()
        
        # Добавление нового вложения
        with st.form(key=f"{tab_prefix}add_investment_{legal_entity}"):
            st.markdown("#### ➕ Добавить новое вложение")
            new_amount = st.number_input("Сумма вложения (₽)", min_value=0.0, key=f"{tab_prefix}new_amount_{legal_entity}")
            new_date = st.date_input("Дата вложения", key=f"{tab_prefix}new_date_{legal_entity}")
            
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
        if st.button("💾 Сохранить вложения в кеш", key=f"{tab_prefix}save_cache_{legal_entity}"):
            save_investments_to_file(investment_data)
            st.success("✅ Вложения сохранены в кеш!")
    
    # Прогноз ROI с учетом остатков
    with st.expander(f"🔮 Прогноз ROI с учетом остатков ({legal_entity})", expanded=False):
        st.markdown(f"### 🔮 Прогноз ROI с учетом реализации остатков - {legal_entity}")
        
        # Получаем текущие данные для расчета
        total_invested_amount = saved_amount
        
        # Рассчитываем ROI и прибыль для прогноза
        if has_investment and total_invested_amount > 0:
            # Используем те же расчеты, что и в основной части
            if investments_list and len(investments_list) > 0:
                first_investment_date_for_roi = min(inv['date'] for inv in investments_list)
                
                # Фильтруем данные с даты первого вложения
                # Используем df вместо df_filtered, так как df_filtered еще не определена
                df_temp = df.copy()
                if not pd.api.types.is_datetime64_any_dtype(df_temp['Дата формирования']):
                    df_temp['Дата формирования'] = pd.to_datetime(df_temp['Дата формирования'])
                if df_temp['Дата формирования'].dt.tz is not None:
                    df_temp['Дата формирования'] = df_temp['Дата формирования'].dt.tz_localize(None)
                
                df_from_investment = df_temp[df_temp['Дата формирования'] >= pd.to_datetime(first_investment_date_for_roi)]
                
                if not df_from_investment.empty:
                    # Рассчитываем расходы с даты первого вложения
                    expenses_from_investment = calculate_expenses(df_from_investment)
                    total_after_tax_from_investment = expenses_from_investment['total_to_pay']['amount'] * 0.93  # минус 7% налог
                    
                    # ROI с даты первого вложения
                    current_profit_amount = total_after_tax_from_investment - total_invested_amount
                    current_roi = (current_profit_amount / total_invested_amount) * 100 if total_invested_amount > 0 else 0
                else:
                    # Если нет данных с даты вложения, используем текущий период
                    current_profit_amount = total_after_tax - total_invested_amount
                    current_roi = (current_profit_amount / total_invested_amount) * 100 if total_invested_amount > 0 else 0
            else:
                # Если нет списка вложений, используем текущий период
                current_profit_amount = total_after_tax - total_invested_amount
                current_roi = (current_profit_amount / total_invested_amount) * 100 if total_invested_amount > 0 else 0
        else:
            # Если нет вложений
            current_roi = 0
            current_profit_amount = 0
        
        # Получаем дату первого вложения
        first_investment_date = None
        if investments_list:
            first_investment_date = min(inv['date'] for inv in investments_list)
        
        st.info(f"📊 **Текущие данные:** ROI = {current_roi:.1f}%, Общие вложения = {total_invested_amount:,.0f} ₽, Прибыль = {current_profit_amount:,.0f} ₽")
        
        # Форма для ввода данных об остатках
        with st.form(key=f"{tab_prefix}roi_forecast_{legal_entity}"):
            st.markdown("#### 📦 Данные об остатках")
            
            # Галочка для расчета с первого вложения
            use_first_investment = st.checkbox(
                    "📅 Начать расчет с даты первого вложения",
                    value=True,
                    key=f"{tab_prefix}use_first_investment_{legal_entity}"
                )
                
            if use_first_investment and first_investment_date:
                # Проверяем тип first_investment_date и форматируем соответственно
                if hasattr(first_investment_date, 'strftime'):
                    date_str = first_investment_date.strftime('%d.%m.%Y')
                else:
                    # Если это строка, пытаемся преобразовать в datetime
                    try:
                        date_obj = pd.to_datetime(first_investment_date)
                        date_str = date_obj.strftime('%d.%m.%Y')
                    except:
                        date_str = str(first_investment_date)
                
                st.info(f"📅 Расчет будет производиться с даты первого вложения: {date_str}")
            
            col1, col2 = st.columns(2)
            with col1:
                remaining_stock_revenue = st.number_input(
                        "💰 Выручка от реализации остатков (₽)", 
                        min_value=0.0, 
                        value=0.0,
                        step=1000.0,
                        help="Выручка с учетом налога (7%)",
                        key=f"{tab_prefix}remaining_stock_revenue_{legal_entity}"
                    )
                
            with col2:
                remaining_stock_date = st.date_input(
                    "📅 Дата планируемой реализации остатков",
                    value=datetime.now().date() + timedelta(days=30),
                    key=f"{tab_prefix}remaining_stock_date_{legal_entity}"
                )
            
            # Дата расчета
            if first_investment_date:
                # Проверяем тип first_investment_date и преобразуем в date
                if hasattr(first_investment_date, 'year') and hasattr(first_investment_date, 'month') and hasattr(first_investment_date, 'day'):
                    # Если это уже date объект (имеет атрибуты year, month, day)
                    default_calculation_date = first_investment_date
                elif hasattr(first_investment_date, 'date'):
                    # Если это datetime объект
                    default_calculation_date = first_investment_date.date()
                elif hasattr(first_investment_date, 'strftime'):
                    # Если это datetime, получаем date
                    default_calculation_date = first_investment_date.date()
                else:
                    # Если это строка, пытаемся преобразовать
                    try:
                        date_obj = pd.to_datetime(first_investment_date)
                        default_calculation_date = date_obj.date()
                    except:
                        default_calculation_date = datetime.now().date()
            else:
                default_calculation_date = datetime.now().date()
                
            current_date = st.date_input(
                "📅 Дата расчета",
                value=default_calculation_date,
                key=f"{tab_prefix}current_date_{legal_entity}"
            )
            
            if st.form_submit_button("🔮 Рассчитать прогноз"):
                if remaining_stock_revenue > 0:
                    # Рассчитываем прогноз
                    forecast_data = calculate_roi_forecast_with_remaining_stock(
                        current_roi=current_roi,
                        total_invested=total_invested_amount,
                        remaining_stock_revenue=remaining_stock_revenue,
                        remaining_stock_date=remaining_stock_date,
                        current_date=current_date,
                        use_first_investment=use_first_investment,
                        first_investment_date=first_investment_date,
                        current_profit=current_profit_amount
                    )
                        
                    if forecast_data:
                        # Отображаем результаты
                        st.markdown("#### 📊 Результаты прогноза")
                        
                        col_metrics1, col_metrics2 = st.columns(2)
                        
                        with col_metrics1:
                            st.metric(
                                "📈 Текущий ROI",
                                f"{forecast_data['current_roi']:.1f}%",
                                help="Текущая доходность без учета остатков"
                            )
                            
                            st.metric(
                                "💰 Текущая прибыль",
                                f"{forecast_data['current_profit']:,.0f} ₽",
                                help="Прибыль от текущих операций"
                            )
                            
                            st.metric(
                                "📦 Выручка от остатков",
                                f"{forecast_data['remaining_stock_revenue']:,.0f} ₽",
                                help="Выручка от реализации остатков (до налога)"
                            )
                            
                            st.metric(
                                "📦 Выручка от остатков (налог)",
                                f"{forecast_data['remaining_stock_revenue_after_tax']:,.0f} ₽",
                                help="Выручка от реализации остатков (после налога 7%)"
                            )
                        
                        with col_metrics2:
                            st.metric(
                                "🔮 Прогнозный ROI",
                                f"{forecast_data['forecast_roi']:.1f}%",
                                delta=f"{forecast_data['forecast_roi'] - forecast_data['current_roi']:.1f}%",
                                help="Прогнозная доходность с учетом остатков"
                            )
                            
                            st.metric(
                                "📈 Годовой ROI",
                                f"{forecast_data['annualized_roi']:.1f}%",
                                help="Годовая доходность с учетом времени реализации"
                            )
                            
                            st.metric(
                                "⏰ Дней до реализации",
                                f"{forecast_data['days_to_realization']}",
                                help="Количество дней до планируемой реализации"
                            )
                        
                        # Детальная информация
                        st.markdown("#### 📋 Детальная информация")
                        st.markdown(f"""
                        <div class="total-card">
                            <h4>🔮 Прогноз ROI с учетом остатков</h4>
                            <ul>
                                <li><strong>Текущий ROI:</strong> {forecast_data['current_roi']:.1f}%</li>
                                <li><strong>Текущая прибыль:</strong> {forecast_data['current_profit']:,.0f} ₽</li>
                                <li><strong>Выручка от остатков:</strong> {forecast_data['remaining_stock_revenue']:,.0f} ₽</li>
                                <li><strong>Прибыль от остатков:</strong> {forecast_data['remaining_stock_profit']:,.0f} ₽</li>
                                <li><strong>Общая прогнозируемая прибыль:</strong> {forecast_data['total_forecast_profit']:,.0f} ₽</li>
                                <li><strong>Общие вложения:</strong> {forecast_data['total_forecast_invested']:,.0f} ₽</li>
                                <li><strong>Прогнозный ROI:</strong> {forecast_data['forecast_roi']:.1f}%</li>
                                <li><strong>Годовой ROI:</strong> {forecast_data['annualized_roi']:.1f}%</li>
                                <li><strong>Дней до реализации остатков:</strong> {forecast_data['days_to_realization']}</li>
                                <li><strong>Дата планируемой реализации:</strong> {forecast_data['remaining_stock_date'].strftime('%d.%m.%Y')}</li>
                            </ul>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # График сравнения
                        fig_comparison = go.Figure()
                        
                        # Текущий ROI
                        fig_comparison.add_trace(go.Bar(
                            name='Текущий ROI',
                            x=['ROI'],
                            y=[forecast_data['current_roi']],
                            marker_color='lightblue',
                            text=f"{forecast_data['current_roi']:.1f}%",
                            textposition='auto'
                        ))
                        
                        # Прогнозный ROI
                        fig_comparison.add_trace(go.Bar(
                            name='Прогнозный ROI',
                            x=['ROI'],
                            y=[forecast_data['forecast_roi']],
                            marker_color='lightgreen',
                            text=f"{forecast_data['forecast_roi']:.1f}%",
                            textposition='auto'
                        ))
                        
                        fig_comparison.update_layout(
                            title="Сравнение текущего и прогнозного ROI",
                            yaxis_title="ROI (%)",
                            height=400,
                            showlegend=True
                        )
                        
                        st.plotly_chart(fig_comparison, use_container_width=True)
                        
                else:
                    st.warning("⚠️ Введите выручку от остатков для расчета прогноза")
            
            # Кнопки сохранения данных прогноза (вне формы)
            if 'forecast_data' in locals() and forecast_data:
                st.markdown("#### 💾 Сохранение данных прогноза")
                col_save1, col_save2, col_save3 = st.columns(3)
                
                with col_save1:
                    if st.button("💾 Сохранить прогноз в CSV", key=f"{tab_prefix}save_forecast_{legal_entity}"):
                        # Создаем DataFrame с данными прогноза
                        forecast_df = pd.DataFrame([{
                            'Юридическое лицо': legal_entity,
                            'Дата расчета': datetime.now().strftime('%d.%m.%Y %H:%M'),
                            'Текущий ROI (%)': forecast_data['current_roi'],
                            'Текущая прибыль (₽)': forecast_data['current_profit'],
                            'Выручка от остатков (₽)': forecast_data['remaining_stock_revenue'],
                            'Выручка от остатков после налога (₽)': forecast_data['remaining_stock_revenue_after_tax'],
                            'Прибыль от остатков (₽)': forecast_data['remaining_stock_profit'],
                            'Общая прогнозируемая прибыль (₽)': forecast_data['total_forecast_profit'],
                            'Общие вложения (₽)': forecast_data['total_forecast_invested'],
                            'Прогнозный ROI (%)': forecast_data['forecast_roi'],
                            'Годовой ROI (%)': forecast_data['annualized_roi'],
                            'Дней до реализации': forecast_data['days_to_realization'],
                            'Дата планируемой реализации': forecast_data['remaining_stock_date'].strftime('%d.%m.%Y'),
                            'Использована дата первого вложения': forecast_data['use_first_investment']
                        }])
                        
                        # Сохраняем прогноз в кеш
                        cache_key = f"forecast_cache_{legal_entity}_{tab_prefix}"
                        st.session_state[cache_key] = {
                            'forecast_data': forecast_data,
                            'forecast_df': forecast_df,
                            'timestamp': datetime.now().strftime('%d.%m.%Y %H:%M'),
                            'legal_entity': legal_entity
                        }
                        
                        # Сохраняем в CSV
                        filename = f"прогноз_roi_{legal_entity}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
                        forecast_df.to_csv(filename, index=False, encoding='utf-8-sig')
                        
                        st.success(f"✅ Прогноз сохранен в файл: {filename} и в кеш")
                
                with col_save2:
                    if st.button("📊 Показать данные прогноза", key=f"{tab_prefix}show_forecast_{legal_entity}"):
                        st.dataframe(forecast_df, use_container_width=True)
                
                with col_save3:
                    # Проверяем, есть ли сохраненный прогноз в кеше
                    cache_key = f"forecast_cache_{legal_entity}_{tab_prefix}"
                    if cache_key in st.session_state:
                        cached_data = st.session_state[cache_key]
                        st.info(f"💾 Кешированный прогноз от {cached_data['timestamp']}")
                        
                        if st.button("🔄 Загрузить из кеша", key=f"{tab_prefix}load_cache_{legal_entity}"):
                            # Восстанавливаем данные из кеша
                            st.session_state[f"{tab_prefix}forecast_loaded_from_cache"] = True
                            st.session_state[f"{tab_prefix}cached_forecast_data"] = cached_data['forecast_data']
                            st.success("✅ Прогноз загружен из кеша!")
                            st.rerun()
                    else:
                        st.info("💾 Кеш пуст")
    
    # Информация о периоде данных
    st.markdown("### 📊 Информация о данных")
    
    # Проверяем данные по годам (используем столбец "Дата формирования")
    if pd.api.types.is_datetime64_any_dtype(df_display['Дата формирования']):
        records_2024 = len(df_display[df_display['Дата формирования'].dt.year == 2024])
        records_2025 = len(df_display[df_display['Дата формирования'].dt.year == 2025])
    else:
        # Если столбец не datetime, конвертируем его
        df_display['Дата формирования'] = pd.to_datetime(df_display['Дата формирования'])
        records_2024 = len(df_display[df_display['Дата формирования'].dt.year == 2024])
        records_2025 = len(df_display[df_display['Дата формирования'].dt.year == 2025])
    
    # Показываем информацию о полном периоде данных
    st.info(f"📊 **Полный период данных в таблице:** с {min_date.strftime('%d.%m.%Y') if hasattr(min_date, 'strftime') else str(min_date)} по {max_date.strftime('%d.%m.%Y') if hasattr(max_date, 'strftime') else str(max_date)} ({len(df_display)} недель)")
    
    # Показываем данные по годам
    if records_2024 > 0:
        st.success(f"📈 **2024 год:** {records_2024} записей")
    if records_2025 > 0:
        st.success(f"📈 **2025 год:** {records_2025} записей")
    elif records_2025 == 0 and records_2024 > 0:
        st.info(f"ℹ️ **Данные за 2025 год отсутствуют** - в таблице только данные за 2024 год")
    
    # Фильтр дат с ползунком
    st.markdown("### 📅 Фильтр по периодам")
    
    # Галочки для ROI
    if has_investment and investments_list:
        col1, col2 = st.columns(2)
        
        with col1:
            st.checkbox(
                "Считать ROI с даты первого вложения (автоматически установить фильтр с этой даты)",
                value=st.session_state.get(f"{tab_prefix}roi_first_date_{legal_entity}", True),
                key=f"{tab_prefix}roi_first_date_{legal_entity}",
                help="При включении фильтр автоматически установится с даты первого вложения"
            )
        
        with col2:
            # Проверяем, есть ли второе вложение
            if len(investments_list) > 1:
                second_investment_date = investments_list[1]['date']
                st.checkbox(
                    f"Считать ROI с даты второго вложения ({second_investment_date.strftime('%d.%m.%Y')})",
                    value=st.session_state.get(f"{tab_prefix}roi_second_date_{legal_entity}", False),
                    key=f"{tab_prefix}roi_second_date_{legal_entity}",
                    help="При включении ROI будет рассчитываться с даты второго вложения"
                )
            else:
                st.info("ℹ️ Второе вложение отсутствует")
    
    # Проверяем настройку ROI с даты первого вложения
    use_first_investment_date = st.session_state.get(f"{tab_prefix}roi_first_date_{legal_entity}", False)
    
    # Определяем начальную дату для фильтра
    if use_first_investment_date and investments_list:
        # Используем дату первого вложения как начальную дату
        filter_start_date = investments_list[0]['date']
        # Показываем информацию о том, что фильтр установлен автоматически
        st.info(f"📅 Фильтр автоматически установлен с даты первого вложения: {filter_start_date.strftime('%d.%m.%Y') if hasattr(filter_start_date, 'strftime') else str(filter_start_date)}")
    else:
        # По умолчанию используем полный период из таблицы
        filter_start_date = min_date.date()
    
    # Убеждаемся, что filter_start_date имеет правильный тип
    if hasattr(filter_start_date, 'date'):
        filter_start_date = filter_start_date.date()
    elif not hasattr(filter_start_date, 'year'):
        # Если это строка, пытаемся преобразовать
        try:
            filter_start_date = pd.to_datetime(filter_start_date).date()
        except:
            filter_start_date = min_date.date()
    

    
    # Ползунок для выбора периода (по умолчанию полный период)
    date_range = st.slider(
        "Выберите период (по умолчанию полный период из таблицы)",
        min_value=min_date.date(),
        max_value=max_date.date(),
        value=(filter_start_date, max_date.date()),
        format="DD.MM.YYYY",
        key=f"{tab_prefix}date_slider_{legal_entity}"
    )
    
    # Поле для ввода банковского процента
    bank_interest_rate = st.number_input(
        "🏦 Годовой банковский процент (%)",
        min_value=0.0,
        max_value=50.0,
        value=17.0,
        step=0.1,
        help="Процент, под который деньги могли бы храниться в банке",
        key=f"{tab_prefix}bank_interest_{legal_entity}"
    )
    
    start_date, end_date = date_range
    
    # Применяем фильтр
    start_datetime = pd.to_datetime(start_date)
    end_datetime = pd.to_datetime(end_date)
    
    # Копируем данные для фильтрации
    df_filtered = df.copy()
    
    # Убеждаемся, что столбец "Дата формирования" является datetime
    if not pd.api.types.is_datetime64_any_dtype(df_filtered['Дата формирования']):
        df_filtered['Дата формирования'] = pd.to_datetime(df_filtered['Дата формирования'])
    
    # Убираем временные зоны из столбца "Дата формирования"
    if df_filtered['Дата формирования'].dt.tz is not None:
        df_filtered['Дата формирования'] = df_filtered['Дата формирования'].dt.tz_localize(None)
    
    # Фильтруем данные по столбцу "Дата формирования"
    filtered_df = df_filtered[
        (df_filtered['Дата формирования'] >= start_datetime) & 
        (df_filtered['Дата формирования'] <= end_datetime)
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
    
    # Рассчитываем ROI и прибыль для использования в прогнозе ROI
    if has_investment and saved_amount > 0:
        # Расчет ROI с учетом выбранной галочки
        if investments_list and len(investments_list) > 0:
            first_investment_date = min(inv['date'] for inv in investments_list)
            
            # Проверяем, включена ли галочка ROI с даты второго вложения
            use_second_investment_date = st.session_state.get(f"{tab_prefix}roi_second_date_{legal_entity}", False)
            
            # Определяем дату для расчета ROI
            if use_second_investment_date and len(investments_list) > 1:
                roi_calculation_date = investments_list[1]['date']  # Второе вложение
                st.info(f"ℹ️ ROI рассчитывается с даты второго вложения: {roi_calculation_date.strftime('%d.%m.%Y')}")
            else:
                roi_calculation_date = first_investment_date  # Первое вложение
            
            # Проверяем, не выбрана ли дата после вложения
            if start_date > roi_calculation_date:
                # Если дата выбрана после даты расчета ROI, учитываем только вложения после выбранной даты
                st.info(f"ℹ️ Выбранная дата ({start_date.strftime('%d.%m.%Y')}) позже даты расчета ROI ({roi_calculation_date.strftime('%d.%m.%Y')}). Учитываются только вложения после выбранной даты.")
                
                # Фильтруем вложения, которые были сделаны после выбранной даты
                filtered_investments = [inv for inv in investments_list if inv['date'] >= start_date]
                
                if filtered_investments:
                    # Рассчитываем сумму отфильтрованных вложений
                    filtered_saved_amount = sum(inv['amount'] for inv in filtered_investments)
                    
                    # ROI с учетом только отфильтрованных вложений
                    profit_after_tax = total_after_tax - filtered_saved_amount
                    roi = (profit_after_tax / filtered_saved_amount) * 100 if filtered_saved_amount > 0 else 0
                else:
                    # Если нет вложений после выбранной даты
                    profit_after_tax = total_after_tax
                    roi = 0
            else:
                # Фильтруем данные с даты расчета ROI
                df_from_investment = df_filtered[df_filtered['Дата формирования'] >= pd.to_datetime(roi_calculation_date)]
                
                if not df_from_investment.empty:
                    # Рассчитываем расходы с даты расчета ROI
                    expenses_from_investment = calculate_expenses(df_from_investment)
                    total_after_tax_from_investment = expenses_from_investment['total_to_pay']['amount'] * 0.93  # минус 7% налог
                    
                    # ROI с даты расчета ROI
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
    else:
        # Если нет вложений
        roi = 0
        profit_after_tax = 0
    
    # Создаем сетку KPI метрик (4 колонки)
    col1, col2, col3, col4 = st.columns(4)
    
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
            delta=f"{calculate_period_format(start_date, end_date)} (с {start_date.strftime('%d.%m.%Y')} по {end_date.strftime('%d.%m.%Y')})"
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
            # Проверяем, не выбрана ли дата до вложения
            if investments_list and len(investments_list) > 0:
                if start_date > roi_calculation_date:
                    # Если дата выбрана после даты расчета ROI, показываем только вложения после выбранной даты
                    filtered_investments = [inv for inv in investments_list if inv['date'] >= start_date]
                    if filtered_investments:
                        filtered_saved_amount = sum(inv['amount'] for inv in filtered_investments)
                        st.metric(
                            label="💰 Итого вложено",
                            value=f"{filtered_saved_amount:,.0f} ₽",
                            delta=f"{len(filtered_investments)} вложений (после {start_date.strftime('%d.%m.%Y')})"
                        )
                    else:
                        st.metric(
                            label="💰 Итого вложено",
                            value="0 ₽",
                            delta="Нет вложений после выбранной даты"
                        )
                else:
                    # KPI Итого вложено
                    st.metric(
                        label="💰 Итого вложено",
                        value=f"{saved_amount:,.0f} ₽",
                        delta=f"{len(investments_list)} вложений"
                    )
            else:
                # KPI Итого вложено
                st.metric(
                    label="💰 Итого вложено",
                    value=f"{saved_amount:,.0f} ₽",
                    delta=f"{len(investments_list)} вложений"
                )
            
            # Расчет ROI с даты первого вложения
            if investments_list and len(investments_list) > 0:
                first_investment_date = min(inv['date'] for inv in investments_list)
                
                # Фильтруем данные с даты первого вложения
                df_from_investment = df_filtered[df_filtered['Дата формирования'] >= pd.to_datetime(first_investment_date)]
                
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
            
            # Расчет ROI за выбранный период (не с даты расчета ROI)
            if start_date > roi_calculation_date:
                # Если дата выбрана после даты расчета ROI, учитываем только вложения после выбранной даты
                filtered_investments = [inv for inv in investments_list if inv['date'] >= start_date]
                if filtered_investments:
                    filtered_saved_amount = sum(inv['amount'] for inv in filtered_investments)
                    roi_selected_period = ((total_after_tax - filtered_saved_amount) / filtered_saved_amount) * 100 if filtered_saved_amount > 0 else 0
                else:
                    roi_selected_period = 0
            else:
                roi_selected_period = ((total_after_tax - saved_amount) / saved_amount) * 100 if saved_amount > 0 else 0
            
            # Расчет банковского дохода
            if investments_list and len(investments_list) > 0:
                # Проверяем, не выбрана ли дата после вложения
                if start_date > roi_calculation_date:
                    # Если дата выбрана после даты расчета ROI, учитываем только вложения после выбранной даты
                    filtered_investments = [inv for inv in investments_list if inv['date'] >= start_date]
                    if filtered_investments:
                        filtered_saved_amount = sum(inv['amount'] for inv in filtered_investments)
                        # Рассчитываем количество дней с выбранной даты до конца периода
                        end_date_datetime = pd.to_datetime(end_date)
                        days_invested = (end_date_datetime - pd.to_datetime(start_date)).days
                        
                        # Рассчитываем банковский доход (простой процент)
                        bank_income = filtered_saved_amount * (bank_interest_rate / 100) * (days_invested / 365)
                        bank_roi = (bank_income / filtered_saved_amount) * 100 if filtered_saved_amount > 0 else 0
                    else:
                        bank_income = 0
                        bank_roi = 0
                else:
                    # Рассчитываем количество дней с даты расчета ROI до конца выбранного периода
                    end_date_datetime = pd.to_datetime(end_date)
                    days_invested = (end_date_datetime - pd.to_datetime(roi_calculation_date)).days
                    
                    # Рассчитываем банковский доход (простой процент)
                    bank_income = saved_amount * (bank_interest_rate / 100) * (days_invested / 365)
                    bank_roi = (bank_income / saved_amount) * 100 if saved_amount > 0 else 0
            else:
                bank_income = 0
                bank_roi = 0
            
            # Расчет настоящего XIRR
            if investments_list and len(investments_list) > 0:
                # Проверяем, не выбрана ли дата после вложения
                if start_date > roi_calculation_date:
                    # Если дата выбрана после даты расчета ROI, учитываем только вложения после выбранной даты
                    filtered_investments = [inv for inv in investments_list if inv['date'] >= start_date]
                    if filtered_investments:
                        # Создаем денежные потоки для XIRR только с отфильтрованными вложениями
                        cashflows = []
                        dates = []
                        
                        # Добавляем отфильтрованные вложения (отрицательные потоки)
                        for inv in filtered_investments:
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
                else:
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
                label="📈 ROI (с первого вложения)",
                value=f"{roi:.1f}%",
                delta=f"С даты первого вложения"
            )
            
            st.metric(
                label="📊 ROI (выбранный период)",
                value=f"{roi_selected_period:.1f}%",
                delta=f"За выбранный период"
            )
            
            st.metric(
                label="🏦 Банк",
                value=f"{bank_income:,.0f} ₽",
                delta=f"ROI: {bank_roi:.1f}% ({bank_interest_rate:.1f}% годовых)"
            )
            
            st.metric(
                label="🎯 XIRR",
                value=f"{xirr:.1f}%",
                delta=f"Внутренняя норма доходности"
            )
        else:
            st.metric(
                label="💰 Итого вложено",
                value="0 ₽",
                delta="Нет вложений"
            )
            
            st.metric(
                label="💵 Прибыль после налога",
                value="0 ₽",
                delta="Нет вложений"
            )
            
            st.metric(
                label="📈 ROI (с первого вложения)",
                value="0%",
                delta="Нет вложений"
            )
            
            st.metric(
                label="📊 ROI (выбранный период)",
                value="0%",
                delta="Нет вложений"
            )
            
            st.metric(
                label="🏦 Банк",
                value="0 ₽",
                delta="Нет вложений"
            )
            
            st.metric(
                label="🎯 XIRR",
                value="0%",
                delta="Нет вложений"
            )
    
    with col4:
        st.metric(
            label="🚚 Сумма логистики",
            value=f"{expenses['logistics']['amount']:,.0f} ₽",
            delta=f"{(expenses['logistics']['amount']/total_amount*100):.1f}% от общей суммы"
        )
        
        st.metric(
            label="📦 Сумма хранения",
            value=f"{expenses['storage']['amount']:,.0f} ₽",
            delta=f"{(expenses['storage']['amount']/total_amount*100):.1f}% от общей суммы"
        )
        
        st.metric(
            label="📋 Прочие удержания",
            value=f"{expenses['other']['amount']:,.0f} ₽",
            delta=f"{(expenses['other']['amount']/total_amount*100):.1f}% от общей суммы"
        )
    
    # Детальная таблица расходов по неделям
    st.markdown("### 📋 Детальная таблица расходов по неделям")
    
    # Создаем копию для отображения с форматированием
    display_df = filtered_df.copy()
    
    # Выбираем только нужные столбцы для отображения
    display_columns = ['Дата формирования', 'Стоимость логистики', 'Стоимость хранения', 'Прочие удержания']
    if 'Итого к оплате' in display_df.columns:
        display_columns.append('Итого к оплате')
    if 'Общая сумма штрафов' in display_df.columns:
        display_columns.append('Общая сумма штрафов')
    
    # Фильтруем только нужные столбцы
    display_df = display_df[display_columns]
    
    # Форматируем даты для лучшей читаемости
    if 'Дата формирования' in display_df.columns:
        display_df['Дата формирования'] = display_df['Дата формирования'].dt.strftime('%d.%m.%Y')
    
    # Форматируем числовые колонки
    format_columns = ['Стоимость логистики', 'Стоимость хранения', 'Прочие удержания']
    if 'Итого к оплате' in display_df.columns:
        format_columns.append('Итого к оплате')
    if 'Общая сумма штрафов' in display_df.columns:
        format_columns.append('Общая сумма штрафов')
    
    for col in format_columns:
        if col in display_df.columns:
            display_df[col] = display_df[col].apply(lambda x: f"{x:,.0f} ₽" if pd.notna(x) else "0 ₽")
    
    # Отображаем таблицу с улучшенным форматированием
    st.markdown("### 📋 Детальная таблица расходов по неделям")
    
    # Показываем количество записей
    st.info(f"📊 Всего записей в таблице: {len(display_df)}")
    
    # Отображаем таблицу с настройками
    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,  # Скрываем индекс
        column_config={
            "Дата формирования": st.column_config.TextColumn(
                "📅 Дата формирования",
                help="Дата формирования отчета",
                width="medium"
            ),
            "Стоимость логистики": st.column_config.TextColumn(
                "🚚 Логистика",
                help="Стоимость логистики",
                width="medium"
            ),
            "Стоимость хранения": st.column_config.TextColumn(
                "📦 Хранение",
                help="Стоимость хранения",
                width="medium"
            ),
            "Прочие удержания": st.column_config.TextColumn(
                "💰 Прочие",
                help="Прочие удержания",
                width="medium"
            ),
            "Итого к оплате": st.column_config.TextColumn(
                "💳 Итого к оплате",
                help="Итого к оплате",
                width="medium"
            ),
            "Общая сумма штрафов": st.column_config.TextColumn(
                "⚠️ Штрафы",
                help="Общая сумма штрафов",
                width="medium"
            )
        }
    )
    
    # Графики на полную ширину
    st.markdown("### 📈 Графики по метрике 'Итого к оплате'")
    
    # График 1: Оплаты по месяцам
    if 'Итого к оплате' in filtered_df.columns:
        # Создаем копию данных для группировки по месяцам
        monthly_df = filtered_df.copy()
        
        # Добавляем столбец с месяцем
        monthly_df['Месяц'] = monthly_df['Дата формирования'].dt.to_period('M')
        
        # Группируем по месяцам и суммируем
        monthly_payments = monthly_df.groupby('Месяц')['Итого к оплате'].sum().reset_index()
        monthly_payments['Месяц'] = monthly_payments['Месяц'].astype(str)
        
        # Создаем график
        fig_monthly = px.bar(
            x=monthly_payments['Месяц'],
            y=monthly_payments['Итого к оплате'],
            title='Оплаты по месяцам',
            labels={'x': 'Месяц', 'y': 'Итого к оплате (₽)'}
        )
        fig_monthly.update_layout(
            height=500,
            bargap=0.1,  # Уменьшаем промежутки между столбцами
            bargroupgap=0.05  # Уменьшаем промежутки между группами
        )
        # Убираем неправильное свойство width
        fig_monthly.update_yaxes(tickformat=",")
        fig_monthly.update_xaxes(tickangle=45)
        st.plotly_chart(fig_monthly, use_container_width=True)
    else:
        st.warning("⚠️ Данные 'Итого к оплате' отсутствуют в выбранном периоде")
    
    # График 2: Столбчатый график "Итого к оплате" по неделям
    if 'Итого к оплате' in filtered_df.columns:
        # Убираем временные зоны для корректного отображения
        def remove_timezone(x):
            if hasattr(x, 'tz') and x.tz is not None:
                return x.tz_localize(None)
            return x
        
        # Создаем копию данных для обработки
        graph_df = filtered_df.copy()
        graph_df['Дата формирования'] = graph_df['Дата формирования'].apply(remove_timezone)
        
        # Группируем по датам и суммируем значения, чтобы избежать дублирования
        weekly_data = graph_df.groupby('Дата формирования')['Итого к оплате'].sum().reset_index()
        weekly_data = weekly_data.sort_values('Дата формирования')  # Сортируем по дате
        
        # Показываем информацию о группировке
        original_count = len(graph_df)
        grouped_count = len(weekly_data)
        if original_count != grouped_count:
            st.info(f"📊 Данные сгруппированы: {original_count} записей → {grouped_count} уникальных дат")
        
        # Округляем суммы до целых рублей для графиков
        amounts_rounded = weekly_data['Итого к оплате'].round(0).astype(int)
        
        # Создаем столбчатый график
        fig_total_bar = px.bar(
            x=weekly_data['Дата формирования'],
            y=amounts_rounded,
            title='"Итого к оплате" по неделям',
            labels={'x': 'Дата', 'y': 'Итого к оплате (₽)'},
            text=amounts_rounded  # Добавляем текст на столбцы
        )
        
        # Настраиваем внешний вид
        fig_total_bar.update_layout(
            height=500,
            bargap=0.1,  # Уменьшаем промежутки между столбцами
            bargroupgap=0.05,  # Уменьшаем промежутки между группами
            showlegend=False
        )
        
        # Настраиваем оси
        fig_total_bar.update_yaxes(
            tickformat=",",
            title="Сумма (₽)"
        )
        fig_total_bar.update_xaxes(
            title="Дата",
            tickangle=45
        )
        
        # Настраиваем столбцы
        fig_total_bar.update_traces(
            marker_color='#1f77b4',  # Синий цвет столбцов
            opacity=0.8,  # Прозрачность
            texttemplate='%{text:,.0f}',  # Формат текста на столбцах
            textposition='outside',  # Позиция текста
            hovertemplate='<b>Дата:</b> %{x}<br><b>Сумма:</b> %{y:,.0f} ₽<extra></extra>'  # Шаблон при наведении
        )
        
        st.plotly_chart(fig_total_bar, use_container_width=True)
    else:
        st.warning("⚠️ Данные 'Итого к оплате' отсутствуют в выбранном периоде")
    
    # График 3: Сравнение оплат по неделям между 2024 и 2025 годами
    if 'Итого к оплате' in filtered_df.columns:
        # Создаем копию данных для анализа по годам
        year_comparison_df = filtered_df.copy()
        
        # Добавляем столбец с годом
        year_comparison_df['Год'] = year_comparison_df['Дата формирования'].dt.year
        
        # Проверяем наличие данных за оба года
        years_present = year_comparison_df['Год'].unique()
        
        if len(years_present) >= 2:
            # Группируем по году и неделе
            year_comparison_df['Неделя'] = year_comparison_df['Дата формирования'].dt.isocalendar().week
            year_comparison_df['Год-Неделя'] = year_comparison_df['Год'].astype(str) + '-W' + year_comparison_df['Неделя'].astype(str).str.zfill(2)
            
            # Группируем по году-неделе и суммируем
            weekly_by_year = year_comparison_df.groupby(['Год', 'Неделя', 'Год-Неделя'])['Итого к оплате'].sum().reset_index()
            
            # Сортируем по году и неделе
            weekly_by_year = weekly_by_year.sort_values(['Год', 'Неделя'])
            
            # Создаем график сравнения
            fig_comparison = px.bar(
                x=weekly_by_year['Год-Неделя'],
                y=weekly_by_year['Итого к оплате'],
                color=weekly_by_year['Год'].astype(str),
                title='Сравнение оплат по неделям: 2024 vs 2025',
                labels={'x': 'Год-Неделя', 'y': 'Итого к оплате (₽)', 'color': 'Год'},
                barmode='group'  # Группируем столбцы по годам
            )
            
            # Настраиваем внешний вид
            fig_comparison.update_layout(
                height=500,
                bargap=0.1,
                bargroupgap=0.05,
                showlegend=True,
                legend_title="Год"
            )
            
            # Настраиваем оси
            fig_comparison.update_yaxes(
                tickformat=",",
                title="Сумма (₽)"
            )
            fig_comparison.update_xaxes(
                title="Год-Неделя",
                tickangle=45
            )
            
            # Настраиваем столбцы
            fig_comparison.update_traces(
                opacity=0.8,
                texttemplate='%{y:,.0f}',
                textposition='outside',
                hovertemplate='<b>Период:</b> %{x}<br><b>Год:</b> %{fullData.name}<br><b>Сумма:</b> %{y:,.0f} ₽<extra></extra>'
            )
            
            # Добавляем статистику по годам
            year_stats = year_comparison_df.groupby('Год')['Итого к оплате'].agg(['sum', 'mean', 'count']).round(0)
            
            st.plotly_chart(fig_comparison, use_container_width=True)
            
            # Показываем статистику сравнения
            st.markdown("### 📊 Статистика сравнения по годам")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### 📈 Сравнение по годам")
                for year in sorted(years_present):
                    year_data = year_stats.loc[year]
                    st.metric(
                        label=f"💰 {year} год",
                        value=f"{year_data['sum']:,.0f} ₽",
                        delta=f"Среднее: {year_data['mean']:,.0f} ₽/нед ({year_data['count']} недель)"
                    )
            
            with col2:
                st.markdown("#### 📊 Детальная статистика")
                st.dataframe(
                    year_stats.reset_index().rename(columns={
                        'Год': 'Год',
                        'sum': 'Общая сумма (₽)',
                        'mean': 'Среднее за неделю (₽)',
                        'count': 'Количество недель'
                    }),
                    use_container_width=True,
                    hide_index=True
                )
            

            
        else:
            st.info(f"ℹ️ Для сравнения по годам необходимо наличие данных за минимум 2 года. В данных присутствуют годы: {', '.join(map(str, years_present))}")
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
    
    if st.button("📥 Скачать отчет о расходах (Excel)", key=f"{tab_prefix}export_{legal_entity}"):
        # Создаем Excel файл с отчетами
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            # Основная таблица
            export_columns = ['Дата формирования', 'Стоимость логистики', 'Стоимость хранения', 'Прочие удержания']
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

def main():
    # Настройка страницы
    st.set_page_config(
        page_title="Анализ еженедельных расходов Wildberries",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Переключатель темы в сайдбаре
    with st.sidebar:
        st.markdown("### 🎨 Настройки темы")
        theme = st.selectbox(
            "Выберите тему:",
            ["Светлая", "Темная"],
            key="theme_selector"
        )
        
        # Применяем тему
        if theme == "Темная":
            st.markdown("""
            <style>
            .stApp {
                background-color: #1e1e1e;
                color: #ffffff;
            }
            .stMarkdown {
                color: #ffffff;
            }
            .stMetric {
                background-color: #2d2d2d;
                border-radius: 10px;
                padding: 10px;
            }
            .stExpander {
                background-color: #2d2d2d;
                border-radius: 10px;
            }
            .stButton > button {
                background-color: #4a4a4a;
                color: #ffffff;
                border: 1px solid #666666;
            }
            .stButton > button:hover {
                background-color: #5a5a5a;
            }
            </style>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <style>
            .stApp {
                background-color: #ffffff;
                color: #000000;
            }
            .stMarkdown {
                color: #000000;
            }
            .stMetric {
                background-color: #f8f9fa;
                border-radius: 10px;
                padding: 10px;
            }
            .stExpander {
                background-color: #f8f9fa;
                border-radius: 10px;
            }
            .stButton > button {
                background-color: #ffffff;
                color: #000000;
                border: 1px solid #cccccc;
            }
            .stButton > button:hover {
                background-color: #f0f0f0;
            }
            </style>
            """, unsafe_allow_html=True)
    
    # Инициализируем пустой auto_loaded_reports если его нет
    if 'auto_loaded_reports' not in st.session_state:
        st.session_state.auto_loaded_reports = {}
    
    # Создаем вкладки
    tab1, tab2, tab3 = st.tabs(["📊 Юридическое лицо 1", "📊 Юридическое лицо 2", "📈 Общий KPI"])
    
    with tab1:
        st.markdown("## 📊 Анализ отчетов Wildberries - Юридическое лицо 1")
        
        # Сайдбар для загрузки данных первого файла
        with st.sidebar:
            st.markdown("### 📁 Загрузка данных - ЮЛ 1")
            
            # Показываем сохраненные отчеты
            saved_reports = load_report_metadata()
            legal_entity_1_reports = [r for r in saved_reports if r['legal_entity'] == 'ЮЛ 1']
            
            # Кнопка обновления списка
            if st.button("🔄 Обновить список отчетов", key="refresh_reports_1"):
                st.rerun()
            
            if legal_entity_1_reports:
                st.markdown("#### 📋 Сохраненные отчеты:")
                for report in legal_entity_1_reports:
                    upload_date = datetime.fromisoformat(report['upload_date']).strftime('%d.%m.%Y %H:%M')
                    st.markdown(f"**{report['original_name']}** ({upload_date})")
                    st.markdown(f"Записей: {report['total_records']} (2024: {report['records_2024']}, 2025: {report['records_2025']})")
                    
                    # Кнопка для загрузки сохраненного отчета
                    if st.button(f"📂 Загрузить {report['original_name']}", key=f"load_1_{report['filename']}"):
                        df1 = load_saved_report(report['filename'])
                        if df1 is not None:
                            df1 = load_expenses_data_from_df(df1)
                            st.session_state['df1'] = df1
                            st.session_state['file_name_1'] = report['original_name']
                            st.success(f"✅ Загружен сохраненный отчет: {report['original_name']}")
                            st.rerun()
            else:
                st.info("📋 Нет сохраненных отчетов для ЮЛ 1")
            
            uploaded_file_1 = st.file_uploader(
                "Выберите Excel файл с отчетами WB (ЮЛ 1)", 
                type=['xlsx', 'xls'],
                key="file_uploader_1",
                help="Загрузите файл с отчетами Wildberries для первого юридического лица"
            )
        
        # Определяем какой файл использовать для первого ЮЛ
        if uploaded_file_1 is not None:
            df1 = pd.read_excel(uploaded_file_1)
            df1 = load_expenses_data_from_df(df1)
            
            # Сохраняем загруженный отчет
            if st.button("💾 Сохранить отчет", key="save_report_1"):
                filepath, metadata = save_uploaded_report(uploaded_file_1, "ЮЛ 1")
                if filepath:
                    st.success(f"✅ Отчет сохранен: {metadata['filename']}")
                    st.rerun()
            
            st.success(f"✅ Файл {uploaded_file_1.name} успешно загружен")
            file_name_1 = uploaded_file_1.name
        elif 'df1' in st.session_state:
            # Используем сохраненный отчет из session_state
            df1 = st.session_state['df1']
            file_name_1 = st.session_state['file_name_1']
        else:
            st.info("📁 Загрузите файл для начала работы")
            return
        
        # Анализируем данные первого файла только если они загружены
        if 'df1' in locals() and df1 is not None:
            analyze_single_file_data(df1, file_name_1, "tab1_")
    
    with tab2:
        st.markdown("## 📊 Анализ отчетов Wildberries - Юридическое лицо 2")
        
        # Сайдбар для загрузки данных второго файла
        with st.sidebar:
            st.markdown("### 📁 Загрузка данных - ЮЛ 2")
            
            # Кнопка очистки кеша
            if st.button("🗑️ Очистить кеш данных", key="clear_cache_2"):
                if 'df2' in st.session_state:
                    del st.session_state['df2']
                if 'file_name_2' in st.session_state:
                    del st.session_state['file_name_2']
                st.success("✅ Кеш данных очищен")
                st.rerun()
            
            # Показываем сохраненные отчеты
            saved_reports = load_report_metadata()
            legal_entity_2_reports = [r for r in saved_reports if r['legal_entity'] == 'ЮЛ 2']
            
            # Кнопка обновления списка
            if st.button("🔄 Обновить список отчетов", key="refresh_reports_2"):
                st.rerun()
            
            if legal_entity_2_reports:
                st.markdown("#### 📋 Сохраненные отчеты:")
                for report in legal_entity_2_reports:
                    upload_date = datetime.fromisoformat(report['upload_date']).strftime('%d.%m.%Y %H:%M')
                    st.markdown(f"**{report['original_name']}** ({upload_date})")
                    st.markdown(f"Записей: {report['total_records']} (2024: {report['records_2024']}, 2025: {report['records_2025']})")
                    
                    # Кнопка для загрузки сохраненного отчета
                    if st.button(f"📂 Загрузить {report['original_name']}", key=f"load_2_{report['filename']}"):
                        df2 = load_saved_report(report['filename'])
                        if df2 is not None:
                            df2 = load_expenses_data_from_df(df2)
                            st.session_state['df2'] = df2
                            st.session_state['file_name_2'] = report['original_name']
                            st.success(f"✅ Загружен сохраненный отчет: {report['original_name']}")
                            st.rerun()
            else:
                st.info("📋 Нет сохраненных отчетов для ЮЛ 2")
            
            uploaded_file_2 = st.file_uploader(
                "Выберите Excel файл с отчетами WB (ЮЛ 2)", 
                type=['xlsx', 'xls'],
                key="file_uploader_2",
                help="Загрузите файл с отчетами Wildberries для ЮЛ 2"
            )
        
        # Определяем какой файл использовать для второго ЮЛ
        if uploaded_file_2 is not None:
            df2 = pd.read_excel(uploaded_file_2)
            df2 = load_expenses_data_from_df(df2)
            
            # Сохраняем загруженный отчет
            if st.button("💾 Сохранить отчет", key="save_report_2"):
                filepath, metadata = save_uploaded_report(uploaded_file_2, "ЮЛ 2")
                if filepath:
                    st.success(f"✅ Отчет сохранен: {metadata['filename']}")
                    st.rerun()
            
            st.success(f"✅ Файл {uploaded_file_2.name} успешно загружен")
            file_name_2 = uploaded_file_2.name
            st.info(f"🔍 Источник данных: Загруженный пользователем файл")
        elif 'df2' in st.session_state:
            # Используем сохраненный отчет из session_state
            df2 = st.session_state['df2']
            file_name_2 = st.session_state['file_name_2']
            st.info(f"🔍 Источник данных: Session state - {file_name_2}")
        else:
            st.info("📁 Загрузите файл для начала работы")
            return
        
        # Анализируем данные второго файла только если они загружены
        if 'df2' in locals() and df2 is not None:
            analyze_single_file_data(df2, file_name_2, "tab2_")
    
    with tab3:
        st.markdown("## 📈 Общий KPI по всем юридическим лицам")
        
        # Проверяем наличие данных в обеих вкладках
        df1_available = 'df1' in st.session_state or 'df1' in locals()
        df2_available = 'df2' in st.session_state or 'df2' in locals()
        
        if not df1_available and not df2_available:
            st.warning("⚠️ Для отображения общего KPI необходимо загрузить данные хотя бы в одной из вкладок")
            return
        
        # Загружаем данные из session_state если они есть
        combined_df = pd.DataFrame()
        
        if df1_available:
            if 'df1' in st.session_state:
                df1 = st.session_state['df1']
            else:
                df1 = locals().get('df1')
            
            if df1 is not None:
                df1_copy = df1.copy()
                df1_copy['Источник'] = 'ЮЛ 1'
                combined_df = pd.concat([combined_df, df1_copy], ignore_index=True)
        
        if df2_available:
            if 'df2' in st.session_state:
                df2 = st.session_state['df2']
            else:
                df2 = locals().get('df2')
            
            if df2 is not None:
                df2_copy = df2.copy()
                df2_copy['Источник'] = 'ЮЛ 2'
                combined_df = pd.concat([combined_df, df2_copy], ignore_index=True)
        
        if combined_df.empty:
            st.warning("⚠️ Нет данных для анализа")
            return
        
        # Загружаем все вложения из всех юридических лиц
        if 'investment_data' not in st.session_state:
            st.session_state.investment_data = load_investments_from_file()
        
        investment_data = st.session_state.investment_data
        
        # Собираем все вложения
        all_investments = []
        all_legal_entities = []
        
        # Проверяем все возможные названия юридических лиц
        possible_legal_entities = [
            'Юридическое лицо 1', 'Юридическое лицо 2',
            'Гураль Иван Сергеевич ИП', 'ИП Гураль Д. Д.',
            'ЮЛ 1', 'ЮЛ 2'
        ]
        
        for legal_entity in possible_legal_entities:
            investments_list = investment_data.get(f"{legal_entity}_list", [])
            if investments_list:
                all_investments.extend(investments_list)
                all_legal_entities.extend([legal_entity] * len(investments_list))
        
        # Если нет вложений в новом формате, проверяем старый формат
        if not all_investments:
            for legal_entity in possible_legal_entities:
                saved_amount = investment_data.get(legal_entity, 0.0)
                if saved_amount > 0:
                    saved_date = investment_data.get(f"{legal_entity}_date", datetime.now().date())
                    all_investments.append({
                        'amount': saved_amount,
                        'date': saved_date,
                        'id': len(all_investments) + 1
                    })
                    all_legal_entities.append(legal_entity)
        
        # Информация о данных
        st.markdown("### 📊 Общая информация о данных")
        
        # Определяем общий период
        min_date = combined_df['Дата формирования'].min()
        max_date = combined_df['Дата формирования'].max()
        
        st.info(f"""
        📊 **Общий период данных:** с {min_date.strftime('%d.%m.%Y')} по {max_date.strftime('%d.%m.%Y')}
        
        📈 **Всего записей:** {len(combined_df)}
        
        🏢 **Юридические лица:**
        - ЮЛ 1: {len(combined_df[combined_df['Источник'] == 'ЮЛ 1'])} записей
        - ЮЛ 2: {len(combined_df[combined_df['Источник'] == 'ЮЛ 2'])} записей
        
        💰 **Всего вложений:** {len(all_investments)} на сумму {sum(inv['amount'] for inv in all_investments):,.0f} ₽
        """)
        
        # Общая сумма вложений
        total_invested = sum(inv['amount'] for inv in all_investments)
        saved_amount = total_invested  # Для совместимости с остальным кодом
        
        # Рассчитываем общие расходы (по умолчанию за весь период)
        expenses = calculate_expenses(combined_df)
        
        # Получаем данные для отображения (по умолчанию за весь период)
        total_to_pay = expenses['total_to_pay']
        tax_amount = total_to_pay['amount'] * 0.07  # 7% налог
        total_after_tax = total_to_pay['amount'] - tax_amount
        
        # Общие суммы (по умолчанию за весь период)
        total_expenses = expenses['logistics']['amount'] + expenses['storage']['amount'] + expenses['other']['amount']
        total_amount = total_to_pay['amount'] + total_expenses
        
        # Процент расходов от общей суммы
        expenses_percentage = (total_expenses / total_amount) * 100 if total_amount > 0 else 0
        
        # Галочка для расчета от самой ранней даты вложения
        if all_investments:
            # Конвертируем даты в объекты datetime.date если они строки
            for inv in all_investments:
                if isinstance(inv['date'], str):
                    inv['date'] = datetime.strptime(inv['date'], '%Y-%m-%d').date()
            
            first_investment_date = min(inv['date'] for inv in all_investments)
            use_first_investment_date = st.checkbox(
                f"Считать общий KPI с даты первого вложения ({first_investment_date.strftime('%d.%m.%Y')})",
                value=st.session_state.get("general_kpi_first_date", True),
                key="general_kpi_first_date",
                help="При включении все расчеты будут производиться с даты первого вложения"
            )
            
            if use_first_investment_date:
                st.info(f"📅 Общий KPI рассчитывается с даты первого вложения: {first_investment_date.strftime('%d.%m.%Y')}")
        else:
            use_first_investment_date = False
        
        # Поле для ввода банковского процента в общем KPI
        bank_interest_rate_general = st.number_input(
            "🏦 Годовой банковский процент (%) - Общий KPI",
            min_value=0.0,
            max_value=50.0,
            value=17.0,
            step=0.1,
            help="Процент, под который деньги могли бы храниться в банке",
            key="bank_interest_general"
        )
        
        # Ползунок для выбора периода в общем KPI
        st.markdown("### 📅 Фильтр по периодам - Общий KPI")
        
        # Определяем начальную дату для фильтра общего KPI
        if use_first_investment_date and all_investments:
            # Используем дату первого вложения как начальную дату
            filter_start_date_general = first_investment_date
            st.info(f"📅 Фильтр автоматически установлен с даты первого вложения: {filter_start_date_general.strftime('%d.%m.%Y')}")
        else:
            # По умолчанию используем полный период из таблицы
            filter_start_date_general = min_date.date()
        
        # Ползунок для выбора периода (по умолчанию полный период)
        date_range_general = st.slider(
            "Выберите период для общего KPI (по умолчанию полный период из таблицы)",
            min_value=min_date.date(),
            max_value=max_date.date(),
            value=(filter_start_date_general, max_date.date()),
            format="DD.MM.YYYY",
            key="date_slider_general"
        )
        
        start_date_general, end_date_general = date_range_general
        
        # Применяем фильтр для общего KPI
        start_datetime_general = pd.to_datetime(start_date_general)
        end_datetime_general = pd.to_datetime(end_date_general)
        
        # Фильтруем данные для общего KPI
        combined_df_filtered = combined_df[
            (combined_df['Дата формирования'] >= start_datetime_general) & 
            (combined_df['Дата формирования'] <= end_datetime_general)
        ]
        
        if combined_df_filtered.empty:
            st.warning("⚠️ Нет данных в выбранном периоде для общего KPI")
            return
        
        # Рассчитываем общие расходы для выбранного периода
        expenses_general = calculate_expenses(combined_df_filtered)
        
        # Получаем данные для отображения (для выбранного периода)
        total_to_pay_general = expenses_general['total_to_pay']
        tax_amount_general = total_to_pay_general['amount'] * 0.07  # 7% налог
        total_after_tax_general = total_to_pay_general['amount'] - tax_amount_general
        
        # Общие суммы (для выбранного периода)
        total_expenses_general = expenses_general['logistics']['amount'] + expenses_general['storage']['amount'] + expenses_general['other']['amount']
        total_amount_general = total_to_pay_general['amount'] + total_expenses_general
        
        # Процент расходов от общей суммы
        expenses_percentage_general = (total_expenses_general / total_amount_general) * 100 if total_amount_general > 0 else 0
        
        # Расчет ROI и XIRR с первой даты вложений
        if all_investments:
            # Находим первую дату вложений
            first_investment_date = min(inv['date'] for inv in all_investments)
            
            if use_first_investment_date:
                # Фильтруем данные с даты первого вложения (в рамках выбранного периода)
                df_from_investment = combined_df_filtered[combined_df_filtered['Дата формирования'] >= pd.to_datetime(first_investment_date)]
                
                if not df_from_investment.empty:
                    # Рассчитываем расходы с даты первого вложения
                    expenses_from_investment = calculate_expenses(df_from_investment)
                    
                    # Обновляем данные для отображения с даты первого вложения
                    total_to_pay = expenses_from_investment['total_to_pay']
                    tax_amount = total_to_pay['amount'] * 0.07  # 7% налог
                    total_after_tax = total_to_pay['amount'] - tax_amount
                    total_expenses = expenses_from_investment['logistics']['amount'] + expenses_from_investment['storage']['amount'] + expenses_from_investment['other']['amount']
                    total_amount = total_to_pay['amount'] + total_expenses
                    expenses_percentage = (total_expenses / total_amount) * 100 if total_amount > 0 else 0
                    
                    # ROI с даты первого вложения
                    profit_after_tax_from_investment = total_after_tax - total_invested
                    roi = (profit_after_tax_from_investment / total_invested) * 100 if total_invested > 0 else 0
                    
                    # Прибыль после налога для отображения (с даты первого вложения)
                    profit_after_tax = total_after_tax - total_invested
                else:
                    # Если нет данных с даты вложения, используем выбранный период
                    profit_after_tax = total_after_tax_general - total_invested
                    roi = (profit_after_tax / total_invested) * 100 if total_invested > 0 else 0
            else:
                # Используем выбранный период
                profit_after_tax = total_after_tax_general - total_invested
                roi = (profit_after_tax / total_invested) * 100 if total_invested > 0 else 0
        else:
            profit_after_tax = total_after_tax_general
            roi = 0
        
        # Расчет ROI за выбранный период (не с даты первого вложения)
        roi_selected_period = ((total_after_tax_general - total_invested) / total_invested) * 100 if total_invested > 0 else 0
        
        # Расчет банковского дохода в общем KPI
        if all_investments:
            # Находим дату первого вложения
            first_investment_date = min(inv['date'] for inv in all_investments)
            
            # Рассчитываем количество дней с первого вложения до конца выбранного периода
            days_invested_general = (end_date_general - first_investment_date).days
            
            # Рассчитываем банковский доход (простой процент)
            bank_income_general = total_invested * (bank_interest_rate_general / 100) * (days_invested_general / 365)
            bank_roi_general = (bank_income_general / total_invested) * 100 if total_invested > 0 else 0
        else:
            bank_income_general = 0
            bank_roi_general = 0
        
        # Расчет настоящего XIRR
        if all_investments:
            # Создаем денежные потоки для XIRR
            cashflows = []
            dates = []
            
            # Добавляем все вложения (отрицательные потоки)
            for inv in all_investments:
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
        
        # Создаем сетку KPI метрик (4 колонки)
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                label="💰 Итого к оплате (общий)",
                value=f"{total_to_pay_general['amount']:,.0f} ₽",
                delta=f"Среднее: {total_to_pay_general['avg_per_week']:,.0f} ₽/нед"
            )
            
            st.metric(
                label="📊 Общая сумма (общий)",
                value=f"{total_amount_general:,.0f} ₽",
                delta=f"Доходы + Расходы"
            )
            
            # Показываем выбранный период
            period_weeks = len(combined_df_filtered)
            period_start = start_date_general
            period_end = end_date_general
            
            st.metric(
                label="📅 Выбранный период",
                value=f"{period_weeks} недель",
                delta=f"{calculate_period_format(period_start, period_end)}"
            )
        
        with col2:
            st.metric(
                label="💸 Налог (7%)",
                value=f"{tax_amount_general:,.0f} ₽",
                delta=f"{(tax_amount_general/total_to_pay_general['amount']*100):.1f}% от дохода"
            )
            
            st.metric(
                label="📈 Все расходы (общий)",
                value=f"{total_expenses_general:,.0f} ₽",
                delta=f"{expenses_percentage_general:.1f}% от общей суммы"
            )
            
            st.metric(
                label="✅ Итого к оплате (налог)",
                value=f"{total_after_tax_general:,.0f} ₽",
                delta=f"Чистая прибыль"
            )
        
        with col3:
            st.metric(
                label="💰 Итого вложено (общий)",
                value=f"{total_invested:,.0f} ₽",
                delta=f"{len(all_investments)} вложений"
            )
            
            st.metric(
                label="💵 Прибыль после налога",
                value=f"{profit_after_tax:,.0f} ₽",
                delta=f"Чистая прибыль"
            )
            
            st.metric(
                label="📈 ROI (с первого вложения)",
                value=f"{roi:.1f}%",
                delta=f"С первой даты вложений"
            )
            
            st.metric(
                label="📊 ROI (выбранный период)",
                value=f"{roi_selected_period:.1f}%",
                delta=f"За выбранный период"
            )
            
            st.metric(
                label="🏦 Банк (общий)",
                value=f"{bank_income_general:,.0f} ₽",
                delta=f"ROI: {bank_roi_general:.1f}% ({bank_interest_rate_general:.1f}% годовых)"
            )
            
            st.metric(
                label="🎯 XIRR (общий)",
                value=f"{xirr:.1f}%",
                delta=f"Внутренняя норма доходности"
            )
        
        with col4:
            st.metric(
                label="🚚 Сумма логистики (общий)",
                value=f"{expenses_general['logistics']['amount']:,.0f} ₽",
                delta=f"{(expenses_general['logistics']['amount']/total_amount_general*100):.1f}% от общей суммы"
            )
            
            st.metric(
                label="📦 Сумма хранения (общий)",
                value=f"{expenses_general['storage']['amount']:,.0f} ₽",
                delta=f"{(expenses_general['storage']['amount']/total_amount_general*100):.1f}% от общей суммы"
            )
            
            st.metric(
                label="📋 Прочие удержания (общий)",
                value=f"{expenses_general['other']['amount']:,.0f} ₽",
                delta=f"{(expenses_general['other']['amount']/total_amount_general*100):.1f}% от общей суммы"
            )
        
        # Детальная информация о вложениях
        if all_investments:
            st.markdown("### 💰 Детальная информация о вложениях")
            
            # Создаем DataFrame для отображения вложений
            investments_df = pd.DataFrame(all_investments)
            investments_df['Дата'] = investments_df['date'].apply(lambda x: x.strftime('%d.%m.%Y') if hasattr(x, 'strftime') else str(x))
            investments_df['Сумма'] = investments_df['amount'].apply(lambda x: f"{x:,.0f} ₽")
            
            # Отображаем таблицу вложений
            st.dataframe(
                investments_df[['Дата', 'Сумма']],
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Дата": st.column_config.TextColumn(
                        "📅 Дата вложения",
                        help="Дата вложения средств",
                        width="medium"
                    ),
                    "Сумма": st.column_config.TextColumn(
                        "💰 Сумма",
                        help="Сумма вложения",
                        width="medium"
                    )
                }
            )
            
        # Прогноз ROI с учетом остатков (общий)
        with st.expander("🔮 Общий прогноз ROI с учетом остатков", expanded=False):
            st.markdown("### 🔮 Общий прогноз ROI с учетом реализации остатков")
            
            # Получаем текущие данные для расчета
            total_invested_amount = saved_amount
            
            # Рассчитываем ROI и прибыль для раздела прогноза ROI
            if total_invested_amount > 0:
                current_profit_amount = total_after_tax - total_invested_amount
                current_roi = (current_profit_amount / total_invested_amount) * 100
            else:
                current_profit_amount = 0
                current_roi = 0
            
            st.info(f"📊 **Текущие данные:** ROI = {current_roi:.1f}%, Общие вложения = {total_invested_amount:,.0f} ₽, Прибыль = {current_profit_amount:,.0f} ₽")
            
            # Форма для ввода данных об остатках
            with st.form(key="roi_forecast_overall"):
                st.markdown("#### 📦 Общие данные об остатках")
                
                # Галочка для расчета с первого вложения
                use_first_investment = st.checkbox(
                    "📅 Начать расчет с даты первого вложения",
                    value=True,
                    key="use_first_investment_overall"
                )
                
                if use_first_investment and first_investment_date:
                    st.info(f"📅 Расчет будет производиться с даты первого вложения: {first_investment_date.strftime('%d.%m.%Y')}")
                
                col1, col2 = st.columns(2)
                with col1:
                    remaining_stock_revenue = st.number_input(
                        "💰 Общая выручка от реализации остатков (₽)", 
                        min_value=0.0, 
                        value=0.0,
                        step=1000.0,
                        help="Выручка с учетом налога (7%)",
                        key="remaining_stock_revenue_overall"
                    )
                
                with col2:
                    remaining_stock_date = st.date_input(
                        "📅 Дата планируемой реализации остатков",
                        value=datetime.now().date() + timedelta(days=30),
                        key="remaining_stock_date_overall"
                    )
                
                # Дата расчета
                default_calculation_date = first_investment_date if first_investment_date else datetime.now().date()
                current_date = st.date_input(
                    "📅 Дата расчета",
                    value=default_calculation_date,
                    key="current_date_overall"
                )
                
                if st.form_submit_button("🔮 Рассчитать общий прогноз"):
                    if remaining_stock_revenue > 0:
                        # Рассчитываем прогноз
                        forecast_data = calculate_roi_forecast_with_remaining_stock(
                            current_roi=current_roi,
                            total_invested=total_invested_amount,
                            remaining_stock_revenue=remaining_stock_revenue,
                            remaining_stock_date=remaining_stock_date,
                            current_date=current_date,
                            use_first_investment=use_first_investment,
                            first_investment_date=first_investment_date,
                            current_profit=current_profit_amount
                        )
                        
                        if forecast_data:
                            # Отображаем результаты
                            st.markdown("#### 📊 Результаты общего прогноза")
                            
                            col_metrics1, col_metrics2 = st.columns(2)
                            
                            with col_metrics1:
                                st.metric(
                                    "📈 Текущий ROI",
                                    f"{forecast_data['current_roi']:.1f}%",
                                    help="Текущая доходность без учета остатков"
                                )
                                
                                st.metric(
                                    "💰 Текущая прибыль",
                                    f"{forecast_data['current_profit']:,.0f} ₽",
                                    help="Прибыль от текущих операций"
                                )
                                
                                st.metric(
                                    "📦 Выручка от остатков",
                                    f"{forecast_data['remaining_stock_revenue']:,.0f} ₽",
                                    help="Выручка от реализации остатков (с учетом налога)"
                                )
                            
                            with col_metrics2:
                                st.metric(
                                    "🔮 Прогнозный ROI",
                                    f"{forecast_data['forecast_roi']:.1f}%",
                                    delta=f"{forecast_data['forecast_roi'] - forecast_data['current_roi']:.1f}%",
                                    help="Прогнозная доходность с учетом остатков"
                                )
                                
                                st.metric(
                                    "📈 Годовой ROI",
                                    f"{forecast_data['annualized_roi']:.1f}%",
                                    help="Годовая доходность с учетом времени реализации"
                                )
                                
                                st.metric(
                                    "⏰ Дней до реализации",
                                    f"{forecast_data['days_to_realization']}",
                                    help="Количество дней до планируемой реализации"
                                )
                            
                            # KPI карточки для общего прогноза ROI
                            st.markdown("#### 🎯 KPI Общего прогноза ROI")
                            
                            # Первый ряд KPI
                            col_kpi1, col_kpi2, col_kpi3, col_kpi4 = st.columns(4)
                            
                            with col_kpi1:
                                st.metric(
                                    "📈 Текущий ROI",
                                    f"{forecast_data['current_roi']:.1f}%",
                                    help="Текущая доходность без учета остатков"
                                )
                            
                            with col_kpi2:
                                st.metric(
                                    "🔮 Прогнозный ROI",
                                    f"{forecast_data['forecast_roi']:.1f}%",
                                    delta=f"{forecast_data['forecast_roi'] - forecast_data['current_roi']:.1f}%",
                                    help="Прогнозная доходность с учетом остатков"
                                )
                            
                            with col_kpi3:
                                st.metric(
                                    "📊 Годовой ROI",
                                    f"{forecast_data['annualized_roi']:.1f}%",
                                    help="Годовая доходность с учетом времени реализации"
                                )
                            
                            with col_kpi4:
                                st.metric(
                                    "⏰ Дней до реализации",
                                    f"{forecast_data['days_to_realization']}",
                                    help="Количество дней до планируемой реализации остатков"
                                )
                            
                            # Второй ряд KPI
                            col_kpi5, col_kpi6, col_kpi7, col_kpi8 = st.columns(4)
                            
                            with col_kpi5:
                                st.metric(
                                    "💰 Текущая прибыль",
                                    f"{forecast_data['current_profit']:,.0f} ₽",
                                    help="Прибыль от текущих операций"
                                )
                            
                            with col_kpi6:
                                st.metric(
                                    "📦 Выручка от остатков",
                                    f"{forecast_data['remaining_stock_revenue']:,.0f} ₽",
                                    help="Выручка от реализации остатков (до налога)"
                                )
                            
                            with col_kpi7:
                                st.metric(
                                    "💵 Прибыль от остатков",
                                    f"{forecast_data['remaining_stock_profit']:,.0f} ₽",
                                    help="Прибыль от реализации остатков"
                                )
                            
                            with col_kpi8:
                                st.metric(
                                    "🎯 Общая прогнозируемая прибыль",
                                    f"{forecast_data['total_forecast_profit']:,.0f} ₽",
                                    delta=f"{forecast_data['total_forecast_profit'] - forecast_data['current_profit']:,.0f} ₽",
                                    help="Общая прибыль с учетом остатков"
                                )
                            
                            # Третий ряд KPI
                            col_kpi9, col_kpi10, col_kpi11, col_kpi12 = st.columns(4)
                            
                            with col_kpi9:
                                st.metric(
                                    "💼 Общие вложения",
                                    f"{forecast_data['total_forecast_invested']:,.0f} ₽",
                                    help="Общая сумма вложенных средств"
                                )
                            
                            with col_kpi10:
                                st.metric(
                                    "📦 Выручка от остатков (налог)",
                                    f"{forecast_data['remaining_stock_revenue_after_tax']:,.0f} ₽",
                                    help="Выручка от реализации остатков (после налога 7%)"
                                )
                            
                            with col_kpi11:
                                # Рассчитываем процент роста прибыли
                                profit_growth = ((forecast_data['total_forecast_profit'] - forecast_data['current_profit']) / forecast_data['current_profit'] * 100) if forecast_data['current_profit'] > 0 else 0
                                st.metric(
                                    "📈 Рост прибыли",
                                    f"{profit_growth:.1f}%",
                                    delta=f"{forecast_data['total_forecast_profit'] - forecast_data['current_profit']:,.0f} ₽",
                                    help="Процент роста прибыли с учетом остатков"
                                )
                            
                            with col_kpi12:
                                # Рассчитываем эффективность вложений
                                investment_efficiency = (forecast_data['total_forecast_profit'] / forecast_data['total_forecast_invested'] * 100) if forecast_data['total_forecast_invested'] > 0 else 0
                                st.metric(
                                    "⚡ Эффективность вложений",
                                    f"{investment_efficiency:.1f}%",
                                    help="Прибыль на рубль вложений"
                                )
                            
                            # График сравнения
                            fig_comparison = go.Figure()
                            
                            # Текущий ROI
                            fig_comparison.add_trace(go.Bar(
                                name='Текущий ROI',
                                x=['ROI'],
                                y=[forecast_data['current_roi']],
                                marker_color='lightblue',
                                text=f"{forecast_data['current_roi']:.1f}%",
                                textposition='auto'
                            ))
                            
                            # Прогнозный ROI
                            fig_comparison.add_trace(go.Bar(
                                name='Прогнозный ROI',
                                x=['ROI'],
                                y=[forecast_data['forecast_roi']],
                                marker_color='lightgreen',
                                text=f"{forecast_data['forecast_roi']:.1f}%",
                                textposition='auto'
                            ))
                            
                            fig_comparison.update_layout(
                                title="Сравнение текущего и прогнозного ROI (Общий)",
                                yaxis_title="ROI (%)",
                                height=400,
                                showlegend=True
                            )
                            
                            st.plotly_chart(fig_comparison, use_container_width=True)
                            
                    else:
                        st.warning("⚠️ Введите выручку от остатков для расчета прогноза")
                
                # Кнопки сохранения данных общего прогноза (вне формы)
                if 'forecast_data' in locals() and forecast_data:
                    st.markdown("#### 💾 Сохранение данных общего прогноза")
                    col_save1, col_save2, col_save3 = st.columns(3)
                    
                    with col_save1:
                        if st.button("💾 Сохранить общий прогноз в CSV", key="save_forecast_overall"):
                            # Создаем DataFrame с данными общего прогноза
                            forecast_df = pd.DataFrame([{
                                'Тип': 'Общий прогноз',
                                'Дата расчета': datetime.now().strftime('%d.%m.%Y %H:%M'),
                                'Текущий ROI (%)': forecast_data['current_roi'],
                                'Текущая прибыль (₽)': forecast_data['current_profit'],
                                'Выручка от остатков (₽)': forecast_data['remaining_stock_revenue'],
                                'Выручка от остатков после налога (₽)': forecast_data['remaining_stock_revenue_after_tax'],
                                'Прибыль от остатков (₽)': forecast_data['remaining_stock_profit'],
                                'Общая прогнозируемая прибыль (₽)': forecast_data['total_forecast_profit'],
                                'Общие вложения (₽)': forecast_data['total_forecast_invested'],
                                'Прогнозный ROI (%)': forecast_data['forecast_roi'],
                                'Годовой ROI (%)': forecast_data['annualized_roi'],
                                'Дней до реализации': forecast_data['days_to_realization'],
                                'Дата планируемой реализации': forecast_data['remaining_stock_date'].strftime('%d.%m.%Y'),
                                'Использована дата первого вложения': forecast_data['use_first_investment']
                            }])
                            
                            # Сохраняем общий прогноз в кеш
                            st.session_state['forecast_cache_overall'] = {
                                'forecast_data': forecast_data,
                                'forecast_df': forecast_df,
                                'timestamp': datetime.now().strftime('%d.%m.%Y %H:%M'),
                                'type': 'overall'
                            }
                            
                            # Сохраняем в CSV
                            filename = f"общий_прогноз_roi_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
                            forecast_df.to_csv(filename, index=False, encoding='utf-8-sig')
                            
                            st.success(f"✅ Общий прогноз сохранен в файл: {filename} и в кеш")
                    
                    with col_save2:
                        if st.button("📊 Показать данные общего прогноза", key="show_forecast_overall"):
                            st.dataframe(forecast_df, use_container_width=True)
                    
                    with col_save3:
                        # Проверяем, есть ли сохраненный общий прогноз в кеше
                        if 'forecast_cache_overall' in st.session_state:
                            cached_data = st.session_state['forecast_cache_overall']
                            st.info(f"💾 Кешированный общий прогноз от {cached_data['timestamp']}")
                            
                            if st.button("🔄 Загрузить общий прогноз из кеша", key="load_cache_overall"):
                                # Восстанавливаем данные из кеша
                                st.session_state['forecast_loaded_from_cache_overall'] = True
                                st.session_state['cached_forecast_data_overall'] = cached_data['forecast_data']
                                st.success("✅ Общий прогноз загружен из кеша!")
                                st.rerun()
                        else:
                            st.info("💾 Кеш общего прогноза пуст")
        
        # График общих доходов по месяцам
        st.markdown("### 📈 Общие доходы по месяцам")
        
        if 'Итого к оплате' in combined_df.columns:
            # Создаем копию данных для группировки по месяцам
            monthly_df = combined_df.copy()
            
            # Добавляем столбец с месяцем
            monthly_df['Месяц'] = monthly_df['Дата формирования'].dt.to_period('M')
            
            # Группируем по месяцам и суммируем
            monthly_payments = monthly_df.groupby('Месяц')['Итого к оплате'].sum().reset_index()
            monthly_payments['Месяц'] = monthly_payments['Месяц'].astype(str)
            
            # Создаем график
            fig_monthly = px.bar(
                x=monthly_payments['Месяц'],
                y=monthly_payments['Итого к оплате'],
                title='Общие доходы по месяцам',
                labels={'x': 'Месяц', 'y': 'Итого к оплате (₽)'}
            )
            fig_monthly.update_layout(
                height=500,
                bargap=0.1,
                bargroupgap=0.05
            )
            fig_monthly.update_yaxes(tickformat=",")
            fig_monthly.update_xaxes(tickangle=45)
            st.plotly_chart(fig_monthly, use_container_width=True)
        
        # Сводка
        st.markdown("### 📋 Общая сводка")
        
        # Определяем правильный период для сводки
        if use_first_investment_date and all_investments:
            summary_period_start = first_investment_date.strftime('%d.%m.%Y')
            summary_period_end = max_date.strftime('%d.%m.%Y')
            summary_weeks = len(combined_df[combined_df['Дата формирования'] >= pd.to_datetime(first_investment_date)])
            summary_avg_expenses = expenses['total'] / summary_weeks if summary_weeks > 0 else 0
        else:
            summary_period_start = min_date.strftime('%d.%m.%Y')
            summary_period_end = max_date.strftime('%d.%m.%Y')
            summary_weeks = len(combined_df)
            summary_avg_expenses = expenses['total'] / summary_weeks if summary_weeks > 0 else 0
        
        st.markdown(f"""
        <div class="total-card">
            <h3>📊 Общие итоги за {'период с даты первого вложения' if use_first_investment_date and all_investments else 'весь период'}</h3>
            <ul>
                <li><strong>Общий период:</strong> {summary_period_start} - {summary_period_end}</li>
                <li><strong>Количество недель:</strong> {summary_weeks}</li>
                <li><strong>Итого к оплате:</strong> {expenses['total_to_pay']['amount']:,.0f} ₽</li>
                <li><strong>Налог (7%):</strong> {tax_amount:,.0f} ₽</li>
                <li><strong>Итого к оплате (налог):</strong> {total_after_tax:,.0f} ₽</li>
                <li><strong>Общая сумма (Итого к оплате + расходы):</strong> {total_amount:,.0f} ₽</li>
                <li><strong>Все расходы:</strong> {total_expenses:,.0f} ₽</li>
                <li><strong>Доля расходов от общей суммы:</strong> {expenses_percentage:.1f}%</li>
                <li><strong>Итого вложено:</strong> {total_invested:,.0f} ₽</li>
                <li><strong>Прибыль после налога:</strong> {profit_after_tax:,.0f} ₽</li>
                <li><strong>ROI:</strong> {roi:.1f}%</li>
                <li><strong>XIRR:</strong> {xirr:.1f}%</li>
                <li><strong>Стоимость логистики:</strong> {expenses['logistics']['amount']:,.0f} ₽</li>
                <li><strong>Стоимость хранения:</strong> {expenses['storage']['amount']:,.0f} ₽</li>
                <li><strong>Прочие удержания:</strong> {expenses['other']['amount']:,.0f} ₽</li>
                <li><strong>Общая сумма штрафов:</strong> {expenses['penalties']['amount']:,.0f} ₽</li>
                <li><strong>Средние расходы за неделю:</strong> {summary_avg_expenses:,.0f} ₽</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
