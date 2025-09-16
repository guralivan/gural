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

def save_future_expenses_to_file(expenses_data, filename='future_expenses_data.json'):
    """Сохраняет данные о будущих расходах в JSON файл"""
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(expenses_data, f, ensure_ascii=False, indent=2, default=str)
        return True
    except Exception as e:
        st.error(f"Ошибка сохранения будущих расходов: {e}")
        return False

def load_future_expenses_from_file(filename='future_expenses_data.json'):
    """Загружает данные о будущих расходах из JSON файла"""
    try:
        if os.path.exists(filename):
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
            # Конвертируем строки дат обратно в объекты date
            for legal_entity in data:
                if f"{legal_entity}_list" in data:
                    for expense in data[f"{legal_entity}_list"]:
                        if isinstance(expense['date'], str):
                            expense['date'] = datetime.strptime(expense['date'], '%Y-%m-%d').date()
            return data
        return {}
    except Exception as e:
        st.error(f"Ошибка загрузки будущих расходов: {e}")
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

def save_unrealized_revenue_data(data):
    """Сохраняет данные о нереализованной выручке в JSON файл"""
    try:
        with open('unrealized_revenue_data.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2, default=str)
        return True
    except Exception as e:
        st.error(f"Ошибка сохранения данных о нереализованной выручке: {e}")
        return False

def load_unrealized_revenue_data():
    """Загружает данные о нереализованной выручке из JSON файла"""
    try:
        if os.path.exists('unrealized_revenue_data.json'):
            with open('unrealized_revenue_data.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
                # Преобразуем строки дат обратно в объекты date
                for legal_entity_key in data:
                    if isinstance(data[legal_entity_key].get('realization_date'), str):
                        data[legal_entity_key]['realization_date'] = datetime.strptime(data[legal_entity_key]['realization_date'], '%Y-%m-%d').date()
                    if isinstance(data[legal_entity_key].get('current_date'), str):
                        data[legal_entity_key]['current_date'] = datetime.strptime(data[legal_entity_key]['current_date'], '%Y-%m-%d').date()
                return data
        else:
            return {}
    except Exception as e:
        st.error(f"Ошибка загрузки данных о нереализованной выручке: {e}")
        return {}

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
        
        # Проверяем базовые условия для XIRR
        total_investments = sum(cf for cf in cashflows if cf < 0)
        total_returns = sum(cf for cf in cashflows if cf > 0)
        
        # Если общая сумма вложений равна общей сумме доходов, XIRR = 0%
        if abs(total_investments + total_returns) < 1:
            return 0.0
        
        # Если нет вложений или нет доходов, XIRR не определен
        if total_investments == 0 or total_returns == 0:
            return None
        
        # Пробуем разные начальные значения с более широким диапазоном
        guesses = [0.1, 0.05, 0.2, -0.1, 0.01, 0.5, -0.5, 1.0, -0.9]
        
        for initial_guess in guesses:
            try:
                # Используем метод Ньютона для нахождения ставки, при которой NPV = 0
                xirr_rate = newton(npv, initial_guess, fprime=npv_derivative, maxiter=2000, tol=1e-6)
                
                # Проверяем, что результат разумен и NPV близок к нулю
                if -0.99 < xirr_rate < 10:  # от -99% до 1000%
                    npv_at_rate = npv(xirr_rate)
                    if abs(npv_at_rate) < 1000:  # NPV должен быть близок к нулю
                        return xirr_rate * 100
            except (ValueError, RuntimeError, OverflowError):
                continue
        
        # Если не удалось найти решение, пробуем простой расчет ROI
        try:
            # Простой расчет: общий доход / общие вложения
            simple_roi = (total_returns + total_investments) / abs(total_investments)
            if simple_roi > 0:
                return simple_roi * 100
        except:
            pass
        
        # Если не удалось найти решение с разными начальными значениями
        return None
            
    except (ValueError, RuntimeError, OverflowError):
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

def calculate_roi_with_unrealized_revenue(current_roi, total_invested, unrealized_revenue,
                                        realization_date, current_date=None, current_profit=None, investments_list=None, future_expenses_list=None):
    """
    Рассчитывает ROI с учетом нереализованной выручки и будущих расходов
    
    Args:
        current_roi: текущий ROI в процентах
        total_invested: общая сумма вложений
        unrealized_revenue: нереализованная выручка
        realization_date: дата планируемой реализации
        current_profit: текущая прибыль (если None, рассчитывается из ROI)
        investments_list: список инвестиций для расчета XIRR
        future_expenses_list: список будущих расходов
    
    Returns:
        dict: словарь с прогнозными данными
    """
    try:
        # Используем переданную дату или сегодняшнюю как текущую
        if current_date is None:
            current_date = datetime.now().date()
        
        # Преобразуем даты в datetime если они строки
        if isinstance(realization_date, str):
            realization_date = pd.to_datetime(realization_date).date()
        if isinstance(current_date, str):
            current_date = pd.to_datetime(current_date).date()
        
        # Проверяем, что вложения больше нуля
        if total_invested <= 0:
            st.error("Ошибка: сумма вложений должна быть больше нуля")
            return None
        
        # Текущая прибыль (используем переданную или рассчитываем из ROI)
        if current_profit is None:
            current_profit = (current_roi / 100) * total_invested
        
        # Нереализованная выручка без учета налога - рассчитываем прибыль с учетом налога 7%
        unrealized_revenue_with_tax = unrealized_revenue * 0.93  # Вычитаем налог 7%
        
        # Рассчитываем будущие расходы
        future_expenses_total = 0
        if future_expenses_list:
            future_expenses_total = sum(expense['amount'] for expense in future_expenses_list)
        
        # Нереализованная прибыль с учетом будущих расходов
        unrealized_profit = unrealized_revenue_with_tax - future_expenses_total
        
        # Общая прогнозируемая прибыль
        total_forecast_profit = current_profit + unrealized_profit
        
        # Общие вложения (нереализованная выручка не добавляется к вложениям)
        total_forecast_invested = total_invested
        
        # Прогнозный ROI (проверяем деление на ноль)
        if total_forecast_invested > 0:
            forecast_roi = (total_forecast_profit / total_forecast_invested) * 100
        else:
            forecast_roi = 0
        
        # Дни до реализации
        days_to_realization = (realization_date - current_date).days
        
        # Годовой ROI (если реализация в течение года)
        if days_to_realization > 0 and total_forecast_invested > 0:
            annualized_roi = (total_forecast_profit / total_forecast_invested) * (365 / days_to_realization) * 100
        else:
            annualized_roi = forecast_roi
        
        # Проверяем на бесконечность и NaN
        if not np.isfinite(forecast_roi):
            forecast_roi = 0
        if not np.isfinite(annualized_roi):
            annualized_roi = forecast_roi
        
        # Рассчитываем XIRR с учетом нереализованной выручки
        forecast_xirr = None
        if investments_list and len(investments_list) > 0:
            try:
                # Создаем денежные потоки для XIRR с объединением по датам
                cashflow_dict = {}
                
                # Добавляем все инвестиции (отрицательные потоки)
                for investment in investments_list:
                    date_key = investment['date']
                    amount = investment['amount']
                    if date_key in cashflow_dict:
                        cashflow_dict[date_key] -= amount
                    else:
                        cashflow_dict[date_key] = -amount
                
                # Добавляем текущую прибыль (положительный поток на текущую дату)
                # НО только если она не совпадает с датой инвестиции
                if current_profit > 0:
                    # Проверяем, есть ли инвестиции на текущую дату
                    investment_on_current_date = sum(inv['amount'] for inv in investments_list if inv['date'] == current_date)
                    
                    if investment_on_current_date > 0:
                        # Если есть инвестиция на текущую дату, добавляем прибыль как отдельный поток
                        # на следующий день или на конец текущего дня
                        profit_date = current_date + timedelta(days=1)
                        if profit_date in cashflow_dict:
                            cashflow_dict[profit_date] += current_profit
                        else:
                            cashflow_dict[profit_date] = current_profit
                    else:
                        # Если нет инвестиции на текущую дату, добавляем как обычно
                        if current_date in cashflow_dict:
                            cashflow_dict[current_date] += current_profit
                        else:
                            cashflow_dict[current_date] = current_profit
                
                # Добавляем нереализованную прибыль с учетом будущих расходов (положительный поток на дату реализации)
                if unrealized_profit > 0:
                    if realization_date in cashflow_dict:
                        cashflow_dict[realization_date] += unrealized_profit
                    else:
                        cashflow_dict[realization_date] = unrealized_profit
                
                # Преобразуем обратно в списки и сортируем по датам
                sorted_items = sorted(cashflow_dict.items(), key=lambda x: x[0])
                dates = [item[0] for item in sorted_items]
                cashflows = [item[1] for item in sorted_items]
                
                # Рассчитываем XIRR
                if len(cashflows) > 1:
                    forecast_xirr = calculate_xirr(cashflows, dates)
            except Exception as e:
                st.warning(f"Не удалось рассчитать XIRR: {e}")
        
        return {
            'current_roi': current_roi,
            'current_profit': current_profit,
            'unrealized_revenue': unrealized_revenue,
            'unrealized_revenue_with_tax': unrealized_revenue_with_tax,
            'unrealized_profit': unrealized_profit,
            'future_expenses_total': future_expenses_total,
            'total_forecast_profit': total_forecast_profit,
            'total_forecast_invested': total_forecast_invested,
            'forecast_roi': forecast_roi,
            'annualized_roi': annualized_roi,
            'forecast_xirr': forecast_xirr,
            'days_to_realization': days_to_realization,
            'realization_date': realization_date,
            'current_date': current_date
        }
        
    except Exception as e:
        st.error(f"Ошибка расчета ROI с нереализованной выручкой: {e}")
        return None

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
    
    # Загрузка и кеширование будущих расходов по юридическому лицу
    if 'future_expenses_data' not in st.session_state:
        st.session_state.future_expenses_data = load_future_expenses_from_file()
    
    future_expenses_data = st.session_state.future_expenses_data
    
    # Получаем список всех будущих расходов для данного юридического лица
    future_expenses_list = future_expenses_data.get(f"{legal_entity}_list", [])
    
    # Загрузка и кеширование данных о нереализованной выручке
    if 'unrealized_revenue_data' not in st.session_state:
        st.session_state.unrealized_revenue_data = load_unrealized_revenue_data()
    
    unrealized_revenue_data = st.session_state.unrealized_revenue_data
    
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
    
    # Галочка для ROI с даты первого вложения
    if has_investment and investments_list:
        st.checkbox(
            "Считать ROI с даты первого вложения (автоматически установить фильтр с этой даты)",
            value=st.session_state.get(f"{tab_prefix}roi_first_date_{legal_entity}", True),
            key=f"{tab_prefix}roi_first_date_{legal_entity}",
            help="При включении фильтр автоматически установится с даты первого вложения"
        )
    
    # Проверяем настройку ROI с даты первого вложения
    use_first_investment_date = st.session_state.get(f"{tab_prefix}roi_first_date_{legal_entity}", False)
    
    # Определяем начальную дату для фильтра
    if use_first_investment_date and investments_list:
        # Используем дату первого вложения как начальную дату
        filter_start_date = investments_list[0]['date']
        # Убеждаемся, что это объект date
        if isinstance(filter_start_date, str):
            filter_start_date = datetime.strptime(filter_start_date, '%Y-%m-%d').date()
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
        key=f"{tab_prefix}date_slider_{legal_entity}"
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
                label="📈 ROI",
                value="0%",
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
    
    # ROI с учетом нереализованной выручки (для всех юридических лиц)
    if tab_prefix in ["tab1_", "tab2_"]:  # Для всех юридических лиц
        with st.expander("🔮 ROI с учетом нереализованной выручки", expanded=False):
            st.markdown("### 🔮 Расчет ROI с учетом нереализованной выручки")
            
            # Получаем текущие данные для расчета
            # Проверяем, есть ли вложения
            if has_investment and investments_list:
                # Рассчитываем ROI и прибыль на основе вложений
                total_invested_amount = sum(inv['amount'] for inv in investments_list)
                
                # Рассчитываем прибыль на основе данных из таблицы
                if 'Итого к оплате' in filtered_df.columns:
                    total_revenue = filtered_df['Итого к оплате'].sum()
                    # Вычитаем налог 7%
                    tax_amount = total_revenue * 0.07
                    total_after_tax = total_revenue - tax_amount
                    current_profit_amount = total_after_tax - total_invested_amount
                    current_roi = (current_profit_amount / total_invested_amount * 100) if total_invested_amount > 0 else 0
                else:
                    current_profit_amount = 0
                    current_roi = 0
            else:
                total_invested_amount = 0
                current_profit_amount = 0
                current_roi = 0
            
            # Получаем дату первого вложения
            first_investment_date = None
            if investments_list:
                first_investment_date = min(inv['date'] for inv in investments_list)
            
            # Показываем информацию о данных
            if total_invested_amount > 0:
                st.info(f"📊 **Текущие данные:** ROI = {current_roi:.1f}%, Общие вложения = {total_invested_amount:,.0f} ₽, Прибыль = {current_profit_amount:,.0f} ₽")
            else:
                st.warning("⚠️ Для расчета ROI необходимо добавить вложения в разделе 'Управление вложениями'")
            
            # Форма для ввода данных о нереализованной выручке
            if total_invested_amount > 0:
                # Загружаем сохраненные данные о нереализованной выручке
                saved_unrealized_data = unrealized_revenue_data.get(legal_entity, {})
                saved_revenue = saved_unrealized_data.get('unrealized_revenue', 0.0)
                saved_realization_date = saved_unrealized_data.get('realization_date', datetime.now().date() + timedelta(days=30))
                saved_current_date = saved_unrealized_data.get('current_date', first_investment_date if first_investment_date else datetime.now().date())
                
                with st.form(key=f"{tab_prefix}unrealized_revenue_roi"):
                    st.markdown("#### 💰 Данные о нереализованной выручке")
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        unrealized_revenue = st.number_input(
                            "💰 Нереализованная выручка (₽)", 
                            min_value=0.0, 
                            value=saved_revenue,
                            step=1000.0,
                            help="Сумма нереализованной выручки без учета налога 7%",
                            key=f"{tab_prefix}unrealized_revenue"
                        )
                    
                    with col2:
                        realization_date = st.date_input(
                            "📅 Дата планируемой реализации",
                            value=saved_realization_date,
                            key=f"{tab_prefix}realization_date"
                        )
                    
                    with col3:
                        # Дата расчета по умолчанию с даты первого вложения
                        default_calculation_date = first_investment_date if first_investment_date else datetime.now().date()
                        current_date = st.date_input(
                            "📅 Дата расчета",
                            value=saved_current_date,
                            key=f"{tab_prefix}current_date_unrealized"
                        )
                    
                    if st.form_submit_button("🔮 Рассчитать ROI"):
                        if unrealized_revenue > 0:
                            # Сохраняем данные о нереализованной выручке
                            unrealized_revenue_data[legal_entity] = {
                                'unrealized_revenue': unrealized_revenue,
                                'realization_date': realization_date,
                                'current_date': current_date
                            }
                            
                            if save_unrealized_revenue_data(unrealized_revenue_data):
                                st.session_state.unrealized_revenue_data = unrealized_revenue_data
                            
                            # Рассчитываем ROI с нереализованной выручкой
                            forecast_data = calculate_roi_with_unrealized_revenue(
                                current_roi=current_roi,
                                total_invested=total_invested_amount,
                                unrealized_revenue=unrealized_revenue,
                                realization_date=realization_date,
                                current_date=current_date,
                                current_profit=current_profit_amount,
                                investments_list=investments_list,
                                future_expenses_list=future_expenses_list
                            )
                        
                        if forecast_data:
                            # Отображаем результаты
                            st.markdown("#### 📊 Результаты расчета")
                            
                            # Общая информация о вложениях и прибыли
                            col_summary1, col_summary2, col_summary3, col_summary4 = st.columns(4)
                            
                            with col_summary1:
                                st.metric(
                                    "💰 Всего вложенных средств",
                                    f"{forecast_data['total_forecast_invested']:,.0f} ₽",
                                    help="Общая сумма всех вложений"
                                )
                            
                            with col_summary2:
                                st.metric(
                                    "📈 Общая сумма прибыли с реализации",
                                    f"{forecast_data['total_forecast_profit']:,.0f} ₽",
                                    help="Общая прибыль с учетом текущей и нереализованной"
                                )
                            
                            with col_summary3:
                                st.metric(
                                    "🎯 Общая доходность",
                                    f"{forecast_data['forecast_roi']:.1f}%",
                                    help="Общая доходность с учетом всех факторов"
                                )
                            
                            with col_summary4:
                                # Рассчитываем общую выручку с реализации
                                # Это должна быть сумма: Итого к оплате (налог) + Нереализованная выручка (с налогом)
                                total_revenue_with_realization = total_after_tax + forecast_data['unrealized_revenue_with_tax']
                                st.metric(
                                    "💵 Общая выручка с реализации",
                                    f"{total_revenue_with_realization:,.0f} ₽",
                                    help="Общая выручка: Итого к оплате (налог) + Нереализованная выручка (с налогом)"
                                )
                            
                            st.markdown("---")
                            
                            col_metrics1, col_metrics2 = st.columns(2)
                            
                            with col_metrics1:
                                st.metric(
                                    "📈 Текущий ROI",
                                    f"{forecast_data['current_roi']:.1f}%",
                                    help="Текущая доходность без учета нереализованной выручки"
                                )
                                
                                st.metric(
                                    "💰 Текущая прибыль",
                                    f"{forecast_data['current_profit']:,.0f} ₽",
                                    help="Прибыль от текущих операций"
                                )
                                
                                st.metric(
                                    "💵 Нереализованная выручка (без налога)",
                                    f"{forecast_data['unrealized_revenue']:,.0f} ₽",
                                    help="Сумма нереализованной выручки без учета налога 7%"
                                )
                                
                                st.metric(
                                    "💵 Нереализованная выручка (с налогом)",
                                    f"{forecast_data['unrealized_revenue_with_tax']:,.0f} ₽",
                                    help="Сумма нереализованной выручки с учетом налога 7%"
                                )
                                
                                st.metric(
                                    "💰 Прибыль с реализации",
                                    f"{forecast_data['unrealized_profit']:,.0f} ₽",
                                    help="Прибыль от реализации нереализованной выручки"
                                )
                                
                                st.metric(
                                    "💸 Будущие расходы",
                                    f"{forecast_data['future_expenses_total']:,.0f} ₽",
                                    help="Общая сумма будущих расходов"
                                )
                            
                            with col_metrics2:
                                st.metric(
                                    "🔮 Прогнозный ROI",
                                    f"{forecast_data['forecast_roi']:.1f}%",
                                    delta=f"{forecast_data['forecast_roi'] - forecast_data['current_roi']:.1f}%",
                                    help="Прогнозная доходность с учетом нереализованной выручки"
                                )
                                
                                st.metric(
                                    "📈 Годовой ROI",
                                    f"{forecast_data['annualized_roi']:.1f}%",
                                    help="Годовая доходность с учетом времени реализации"
                                )
                                
                                # XIRR метрика
                                if forecast_data['forecast_xirr'] is not None:
                                    st.metric(
                                        "📊 Прогнозный XIRR",
                                        f"{forecast_data['forecast_xirr']:.1f}%",
                                        help="Внутренняя ставка доходности с учетом нереализованной выручки"
                                    )
                                else:
                                    st.metric(
                                        "📊 Прогнозный XIRR",
                                        "Н/Д",
                                        help="Не удалось рассчитать XIRR"
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
                                <h4>🔮 ROI с учетом нереализованной выручки</h4>
                                <ul>
                                    <li><strong>Текущий ROI:</strong> {forecast_data['current_roi']:.1f}%</li>
                                    <li><strong>Текущая прибыль:</strong> {forecast_data['current_profit']:,.0f} ₽</li>
                                    <li><strong>Нереализованная выручка (без налога):</strong> {forecast_data['unrealized_revenue']:,.0f} ₽</li>
                                    <li><strong>Нереализованная выручка (с налогом 7%):</strong> {forecast_data['unrealized_revenue_with_tax']:,.0f} ₽</li>
                                    <li><strong>Прибыль от нереализованной выручки:</strong> {forecast_data['unrealized_profit']:,.0f} ₽</li>
                                    <li><strong>Будущие расходы:</strong> {forecast_data['future_expenses_total']:,.0f} ₽</li>
                                    <li><strong>Общая прогнозируемая прибыль:</strong> {forecast_data['total_forecast_profit']:,.0f} ₽</li>
                                    <li><strong>Общие вложения:</strong> {forecast_data['total_forecast_invested']:,.0f} ₽</li>
                                    <li><strong>Прогнозный ROI:</strong> {forecast_data['forecast_roi']:.1f}%</li>
                                    <li><strong>Годовой ROI:</strong> {forecast_data['annualized_roi']:.1f}%</li>
                                    <li><strong>Прогнозный XIRR:</strong> {f"{forecast_data['forecast_xirr']:.1f}%" if forecast_data['forecast_xirr'] is not None else 'Н/Д'}</li>
                                    <li><strong>Дней до реализации:</strong> {forecast_data['days_to_realization']}</li>
                                    <li><strong>Дата планируемой реализации:</strong> {forecast_data['realization_date'].strftime('%d.%m.%Y')}</li>
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
                        st.warning("⚠️ Введите сумму нереализованной выручки для расчета")
            else:
                st.info("ℹ️ Для расчета ROI с нереализованной выручкой необходимо добавить вложения в разделе 'Управление вложениями' выше")
    
    # Управление будущими расходами (для всех юридических лиц)
    if tab_prefix in ["tab1_", "tab2_"]:  # Для всех юридических лиц
        with st.expander("💸 Управление будущими расходами", expanded=False):
            st.markdown("### 💸 Управление будущими расходами")
            
            # Используем уже загруженные данные о будущих расходах
            future_expenses_data = st.session_state.future_expenses_data
            
            # Показываем сохраненные данные
            if future_expenses_list:
                saved_amount = sum(exp['amount'] for exp in future_expenses_list)
                saved_date = future_expenses_list[0]['date']
                st.info(f"💾 **Сохраненные данные:** {len(future_expenses_list)} будущих расходов на общую сумму {saved_amount:,.0f} ₽")
            else:
                st.info("ℹ️ Будущие расходы не добавлены")
            
            # Форма для добавления нового будущего расхода
            with st.form(key=f"{tab_prefix}add_future_expense"):
                st.markdown("#### ➕ Добавить будущий расход")
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    expense_amount = st.number_input(
                        "💰 Сумма расхода (₽)", 
                        min_value=0.0, 
                        value=0.0,
                        step=1000.0,
                        help="Сумма будущего расхода",
                        key=f"{tab_prefix}expense_amount"
                    )
                
                with col2:
                    expense_date = st.date_input(
                        "📅 Дата расхода",
                        value=datetime.now().date() + timedelta(days=30),
                        key=f"{tab_prefix}expense_date"
                    )
                
                with col3:
                    expense_description = st.text_input(
                        "📝 Описание",
                        value="",
                        placeholder="Например: Логистика, Хранение, Штрафы...",
                        key=f"{tab_prefix}expense_description"
                    )
                
                if st.form_submit_button("➕ Добавить расход"):
                    if expense_amount > 0:
                        # Создаем новый будущий расход
                        new_expense = {
                            'id': max([exp['id'] for exp in future_expenses_list], default=0) + 1,
                            'amount': expense_amount,
                            'date': expense_date,
                            'description': expense_description or "Будущий расход"
                        }
                        
                        future_expenses_list.append(new_expense)
                        future_expenses_data[f"{legal_entity}_list"] = future_expenses_list
                        
                        # Сохраняем в файл
                        if save_future_expenses_to_file(future_expenses_data):
                            st.success(f"✅ Будущий расход на сумму {expense_amount:,.0f} ₽ добавлен!")
                            st.rerun()
                        else:
                            st.error("❌ Ошибка при сохранении данных")
                    else:
                        st.warning("⚠️ Введите сумму расхода больше нуля")
            
            # Список будущих расходов с возможностью удаления
            if future_expenses_list:
                st.markdown("#### 📋 Список будущих расходов")
                
                # Создаем DataFrame для отображения
                expenses_df = pd.DataFrame(future_expenses_list)
                
                # Безопасное форматирование дат
                def format_date(x):
                    if isinstance(x, str):
                        try:
                            # Пытаемся преобразовать строку в дату
                            date_obj = datetime.strptime(x, '%Y-%m-%d').date()
                            return date_obj.strftime('%d.%m.%Y')
                        except:
                            return x
                    elif hasattr(x, 'strftime'):
                        return x.strftime('%d.%m.%Y')
                    else:
                        return str(x)
                
                expenses_df['Дата'] = expenses_df['date'].apply(format_date)
                expenses_df['Сумма'] = expenses_df['amount'].apply(lambda x: f"{x:,.0f} ₽")
                
                # Отображаем таблицу
                st.dataframe(
                    expenses_df[['id', 'description', 'Сумма', 'Дата']],
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "id": st.column_config.NumberColumn(
                            "🆔 ID",
                            help="Идентификатор расхода",
                            width="small"
                        ),
                        "description": st.column_config.TextColumn(
                            "📝 Описание",
                            help="Описание расхода",
                            width="medium"
                        ),
                        "Сумма": st.column_config.TextColumn(
                            "💰 Сумма",
                            help="Сумма расхода",
                            width="medium"
                        ),
                        "Дата": st.column_config.TextColumn(
                            "📅 Дата",
                            help="Дата расхода",
                            width="medium"
                        )
                    }
                )
                
                # Форма для удаления расхода
                with st.form(key=f"{tab_prefix}delete_future_expense"):
                    st.markdown("#### 🗑️ Удалить будущий расход")
                    
                    expense_to_delete = st.selectbox(
                        "Выберите расход для удаления:",
                        options=[f"{exp['id']} - {exp['description']} ({exp['amount']:,.0f} ₽)" for exp in future_expenses_list],
                        key=f"{tab_prefix}expense_to_delete"
                    )
                    
                    if st.form_submit_button("🗑️ Удалить"):
                        if expense_to_delete:
                            # Извлекаем ID из строки
                            expense_id = int(expense_to_delete.split(' - ')[0])
                            
                            # Удаляем расход
                            future_expenses_list = [exp for exp in future_expenses_list if exp['id'] != expense_id]
                            future_expenses_data[f"{legal_entity}_list"] = future_expenses_list
                            
                            # Сохраняем в файл
                            if save_future_expenses_to_file(future_expenses_data):
                                st.success("✅ Будущий расход удален!")
                                st.rerun()
                            else:
                                st.error("❌ Ошибка при сохранении данных")
    
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
    
    # Получаем текущую тему
    current_theme = st.session_state.get("theme_selector", "Светлая")
    is_dark_theme = current_theme == "Темная"
    
    # График 1: Оплаты по месяцам
    if 'Итого к оплате' in filtered_df.columns:
        # Создаем копию данных для группировки по месяцам
        monthly_df = filtered_df.copy()
        
        # Добавляем столбец с месяцем и годом
        monthly_df['Месяц'] = monthly_df['Дата формирования'].dt.to_period('M')
        monthly_df['Год'] = monthly_df['Дата формирования'].dt.year
        
        # Группируем по месяцам и суммируем
        monthly_payments = monthly_df.groupby('Месяц')['Итого к оплате'].sum().reset_index()
        monthly_payments['Месяц'] = monthly_payments['Месяц'].astype(str)
        
        # Сортируем по хронологическому порядку
        monthly_payments = monthly_payments.sort_values('Месяц')
        
        # Создаем график
        fig_monthly = px.bar(
            x=monthly_payments['Месяц'],
            y=monthly_payments['Итого к оплате'],
            title='Оплаты по месяцам',
            labels={'x': 'Месяц', 'y': 'Итого к оплате (₽)'},
            text=monthly_payments['Итого к оплате']  # Добавляем текст на столбцы
        )
        
        # Настраиваем тему в зависимости от выбранной темы
        if is_dark_theme:
            fig_monthly.update_layout(
                height=500,
                bargap=0.2,
                bargroupgap=0.1,
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(color='white'),  # Белый текст для темной темы
                title_font_color='white'
            )
            # Настраиваем оси для темной темы
            fig_monthly.update_yaxes(
                tickformat=",",
                title="Сумма (₽)",
                gridcolor='rgba(255,255,255,0.1)',
                zeroline=False,
                tickfont=dict(color='white'),
                title_font_color='white'
            )
            fig_monthly.update_xaxes(
                title="Месяц",
                tickangle=45,
                gridcolor='rgba(255,255,255,0.1)',
                tickfont=dict(color='white'),
                title_font_color='white'
            )
        else:
            fig_monthly.update_layout(
                height=500,
                bargap=0.2,
                bargroupgap=0.1,
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(color='black'),  # Черный текст для светлой темы
                title_font_color='black'
            )
            # Настраиваем оси для светлой темы
            fig_monthly.update_yaxes(
                tickformat=",",
                title="Сумма (₽)",
                gridcolor='rgba(128,128,128,0.2)',
                zeroline=False,
                tickfont=dict(color='black'),
                title_font_color='black'
            )
            fig_monthly.update_xaxes(
                title="Месяц",
                tickangle=45,
                gridcolor='rgba(128,128,128,0.2)',
                tickfont=dict(color='black'),
                title_font_color='black'
            )
        
        # Настраиваем столбцы
        fig_monthly.update_traces(
            marker_color='#A23B72',
            opacity=0.9,
            texttemplate='%{text:,.0f}',
            textposition='outside',
            textfont_size=11,
            textfont_color='white' if is_dark_theme else 'black',  # Цвет текста на столбцах
            hovertemplate='<b>Месяц:</b> %{x}<br><b>Сумма:</b> %{y:,.0f} ₽<extra></extra>'
        )
        st.plotly_chart(fig_monthly, use_container_width=True)
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
            # Группируем по году и неделе с улучшенным форматированием
            year_comparison_df['Неделя'] = year_comparison_df['Дата формирования'].dt.isocalendar().week
            year_comparison_df['Месяц'] = year_comparison_df['Дата формирования'].dt.strftime('%b')
            year_comparison_df['Месяц_Неделя_Год'] = year_comparison_df['Месяц'] + ' W' + year_comparison_df['Неделя'].astype(str) + ' ' + year_comparison_df['Год'].astype(str)
            
            # Группируем по году-неделе и суммируем
            weekly_by_year = year_comparison_df.groupby(['Год', 'Неделя', 'Месяц_Неделя_Год'])['Итого к оплате'].sum().reset_index()
            
            # Сортируем по году и неделе
            weekly_by_year = weekly_by_year.sort_values(['Год', 'Неделя'])
            
            # Создаем график сравнения - ВАРИАНТ 3: Наложенные столбцы
            fig_comparison = go.Figure()
            
            # Добавляем данные для каждого года отдельно
            for year in sorted(years_present):
                year_data = weekly_by_year[weekly_by_year['Год'] == year]
                color = '#F18F01' if year == 2024 else '#C73E1D'  # Оранжевый для 2024, красный для 2025
                
                fig_comparison.add_trace(go.Bar(
                    x=year_data['Месяц_Неделя_Год'],
                    y=year_data['Итого к оплате'],
                    name=f'{year} год',
                    marker_color=color,
                    opacity=0.7,
                    hovertemplate=f'<b>Неделя:</b> %{{x}}<br><b>{year} год:</b> %{{y:,.0f}} ₽<extra></extra>'
                ))
            
            # Настраиваем внешний вид в зависимости от темы
            if is_dark_theme:
                fig_comparison.update_layout(
                    title='Сравнение оплат по неделям: 2024 vs 2025',
                    height=500,
                    barmode='overlay',  # Наложенные столбцы
                    showlegend=True,
                    legend_title="Год",
                    legend_title_font_color='white',
                    legend_font_color='white',
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    font=dict(color='white', size=12),
                    title_font_color='white',
                    title_font_size=16
                )
                # Настраиваем оси для темной темы
                fig_comparison.update_yaxes(
                    tickformat=",",
                    title="Сумма (₽)",
                    gridcolor='rgba(255,255,255,0.1)',
                    zeroline=False,
                    tickfont=dict(color='white', size=10),
                    title_font_color='white',
                    title_font_size=12
                )
                fig_comparison.update_xaxes(
                    title="Месяц-Неделя-Год",
                    tickangle=45,
                    gridcolor='rgba(255,255,255,0.1)',
                    tickfont=dict(color='white', size=9),
                    title_font_color='white',
                    title_font_size=12
                )
            else:
                fig_comparison.update_layout(
                    title='Сравнение оплат по неделям: 2024 vs 2025',
                    height=500,
                    barmode='overlay',  # Наложенные столбцы
                    showlegend=True,
                    legend_title="Год",
                    legend_title_font_color='black',
                    legend_font_color='black',
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    font=dict(color='black', size=12),
                    title_font_color='black',
                    title_font_size=16
                )
                # Настраиваем оси для светлой темы
                fig_comparison.update_yaxes(
                    tickformat=",",
                    title="Сумма (₽)",
                    gridcolor='rgba(128,128,128,0.2)',
                    zeroline=False,
                    tickfont=dict(color='black', size=10),
                    title_font_color='black',
                    title_font_size=12
                )
                fig_comparison.update_xaxes(
                    title="Месяц-Неделя-Год",
                    tickangle=45,
                    gridcolor='rgba(128,128,128,0.2)',
                    tickfont=dict(color='black', size=9),
                    title_font_color='black',
                    title_font_size=12
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
        
        # Расчет ROI и XIRR с первой даты вложений
        if all_investments:
            # Находим первую дату вложений
            first_investment_date = min(inv['date'] for inv in all_investments)
            
            if use_first_investment_date:
                # Фильтруем данные с даты первого вложения
                df_from_investment = combined_df[combined_df['Дата формирования'] >= pd.to_datetime(first_investment_date)]
                
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
                    # Если нет данных с даты вложения, используем текущий период
                    profit_after_tax = total_after_tax - total_invested
                    roi = (profit_after_tax / total_invested) * 100 if total_invested > 0 else 0
            else:
                # Используем текущий период
                profit_after_tax = total_after_tax - total_invested
                roi = (profit_after_tax / total_invested) * 100 if total_invested > 0 else 0
        else:
            profit_after_tax = total_after_tax
            roi = 0
        
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
        
        # Результаты расчета - общая сводка
        st.markdown("### 📊 Результаты расчета")
        
        col_summary1, col_summary2, col_summary3, col_summary4 = st.columns(4)
        
        with col_summary1:
            st.metric(
                "💰 Всего вложенных средств",
                f"{total_invested:,.0f} ₽",
                help="Общая сумма всех вложений по всем юридическим лицам"
            )
        
        with col_summary2:
            st.metric(
                "📈 Общая сумма прибыли с реализации",
                f"{profit_after_tax:,.0f} ₽",
                help="Общая прибыль после налога по всем юридическим лицам"
            )
        
        with col_summary3:
            st.metric(
                "🎯 Общая доходность",
                f"{roi:.1f}%",
                help="Общая доходность (ROI) по всем юридическим лицам"
            )
        
        with col_summary4:
            # Рассчитываем общую выручку с реализации
            # В общем KPI это общая выручка после налога (без нереализованной выручки)
            total_revenue_with_realization = total_after_tax
            st.metric(
                "💵 Общая выручка с реализации",
                f"{total_revenue_with_realization:,.0f} ₽",
                help="Общая выручка после налога по всем юридическим лицам"
            )
        
        st.markdown("---")
        
        # ROI с учетом нереализованной выручки для общего KPI
        with st.expander("🔮 ROI с учетом нереализованной выручки (Общий KPI)", expanded=False):
            st.markdown("### 🔮 Расчет ROI с учетом нереализованной выручки (Общий KPI)")
            
            # Показываем текущие данные
            if total_invested > 0:
                st.info(f"📊 **Текущие данные:** ROI = {roi:.1f}%, Общие вложения = {total_invested:,.0f} ₽, Прибыль = {profit_after_tax:,.0f} ₽, Итого к оплате (налог) = {total_after_tax:,.0f} ₽")
            else:
                st.warning("⚠️ Для расчета ROI необходимо добавить вложения в разделах 'Управление вложениями'")
            
            # Автоматический сбор данных о нереализованной выручке из юридических лиц
            if total_invested > 0:
                # Загружаем данные о нереализованной выручке
                if 'unrealized_revenue_data' not in st.session_state:
                    st.session_state.unrealized_revenue_data = load_unrealized_revenue_data()
                
                unrealized_revenue_data = st.session_state.unrealized_revenue_data
                
                # Собираем данные из всех юридических лиц
                total_unrealized_revenue = 0.0
                all_realization_dates = []
                
                # Проверяем все возможные названия юридических лиц
                possible_legal_entities = [
                    'Юридическое лицо 1', 'Юридическое лицо 2',
                    'Гураль Иван Сергеевич ИП', 'ИП Гураль Д. Д.',
                    'ЮЛ 1', 'ЮЛ 2'
                ]
                
                for legal_entity in possible_legal_entities:
                    if legal_entity in unrealized_revenue_data:
                        entity_data = unrealized_revenue_data[legal_entity]
                        if 'unrealized_revenue' in entity_data:
                            total_unrealized_revenue += entity_data['unrealized_revenue']
                            if 'realization_date' in entity_data:
                                all_realization_dates.append(entity_data['realization_date'])
                
                # Определяем общую дату реализации (максимальную из всех)
                if all_realization_dates:
                    overall_realization_date = max(all_realization_dates)
                else:
                    overall_realization_date = datetime.now().date() + timedelta(days=30)
                
                # Дата расчета по умолчанию с даты первого вложения
                default_calculation_date = first_investment_date if all_investments and first_investment_date else datetime.now().date()
                
                # Показываем собранные данные
                st.markdown("#### 💰 Данные о нереализованной выручке (Общий KPI)")
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric(
                        "💰 Общая нереализованная выручка",
                        f"{total_unrealized_revenue:,.0f} ₽",
                        help="Сумма нереализованной выручки из всех юридических лиц"
                    )
                
                with col2:
                    st.metric(
                        "📅 Дата реализации",
                        f"{overall_realization_date.strftime('%d.%m.%Y')}",
                        help="Максимальная дата реализации из всех юридических лиц"
                    )
                
                with col3:
                    st.metric(
                        "📅 Дата расчета",
                        f"{default_calculation_date.strftime('%d.%m.%Y')}",
                        help="Дата расчета (с даты первого вложения)"
                    )
                
                                # Кнопка для расчета
                if st.button("🔮 Рассчитать ROI с нереализованной выручкой", key="tab3_calculate_roi"):
                    if total_unrealized_revenue > 0:
                        # Рассчитываем ROI с нереализованной выручкой
                        forecast_data = calculate_roi_with_unrealized_revenue(
                            current_roi=roi,
                            total_invested=total_invested,
                            unrealized_revenue=total_unrealized_revenue,
                            realization_date=overall_realization_date,
                            current_date=default_calculation_date,
                            current_profit=profit_after_tax,
                            investments_list=all_investments,
                            future_expenses_list=[]  # Пока без будущих расходов для общего KPI
                        )
                        
                        if forecast_data:
                            # Отображаем результаты
                            st.markdown("#### 📊 Результаты расчета (Общий KPI)")
                            
                            # Общая информация о вложениях и прибыли
                            col_summary1, col_summary2, col_summary3, col_summary4 = st.columns(4)
                            
                            with col_summary1:
                                st.metric(
                                    "💰 Всего вложенных средств",
                                    f"{forecast_data['total_forecast_invested']:,.0f} ₽",
                                    help="Общая сумма всех вложений"
                                )
                            
                            with col_summary2:
                                st.metric(
                                    "📈 Общая сумма прибыли с реализации",
                                    f"{forecast_data['total_forecast_profit']:,.0f} ₽",
                                    help="Общая прибыль с учетом текущей и нереализованной"
                                )
                            
                            with col_summary3:
                                st.metric(
                                    "🎯 Общая доходность",
                                    f"{forecast_data['forecast_roi']:.1f}%",
                                    help="Общая доходность с учетом всех факторов"
                                )
                            
                            with col_summary4:
                                # Рассчитываем общую выручку с реализации
                                # Это должна быть сумма: Итого к оплате (налог) + Нереализованная выручка (с налогом)
                                total_revenue_with_realization = total_after_tax + forecast_data['unrealized_revenue_with_tax']
                                st.metric(
                                    "💵 Общая выручка с реализации",
                                    f"{total_revenue_with_realization:,.0f} ₽",
                                    help="Общая выручка: Итого к оплате (налог) + Нереализованная выручка (с налогом)"
                                )
                            
                            st.markdown("---")
                            
                            col_metrics1, col_metrics2 = st.columns(2)
                            
                            with col_metrics1:
                                st.metric(
                                    "📈 Текущий ROI",
                                    f"{forecast_data['current_roi']:.1f}%",
                                    help="Текущая доходность без учета нереализованной выручки"
                                )
                                
                                st.metric(
                                    "💰 Текущая прибыль",
                                    f"{forecast_data['current_profit']:,.0f} ₽",
                                    help="Прибыль от текущих операций"
                                )
                                
                                st.metric(
                                    "💵 Нереализованная выручка (без налога)",
                                    f"{forecast_data['unrealized_revenue']:,.0f} ₽",
                                    help="Сумма нереализованной выручки без учета налога 7%"
                                )
                                
                                st.metric(
                                    "💵 Нереализованная выручка (с налогом)",
                                    f"{forecast_data['unrealized_revenue_with_tax']:,.0f} ₽",
                                    help="Сумма нереализованной выручки с учетом налога 7%"
                                )
                                
                                st.metric(
                                    "💰 Прибыль с реализации",
                                    f"{forecast_data['unrealized_profit']:,.0f} ₽",
                                    help="Прибыль от реализации нереализованной выручки"
                                )
                            
                            with col_metrics2:
                                st.metric(
                                    "🔮 Прогнозный ROI",
                                    f"{forecast_data['forecast_roi']:.1f}%",
                                    delta=f"{forecast_data['forecast_roi'] - forecast_data['current_roi']:.1f}%",
                                    help="Прогнозная доходность с учетом нереализованной выручки"
                                )
                                
                                st.metric(
                                    "📈 Годовой ROI",
                                    f"{forecast_data['annualized_roi']:.1f}%",
                                    help="Годовая доходность с учетом времени реализации"
                                )
                                
                                # XIRR метрика
                                if forecast_data['forecast_xirr'] is not None:
                                    st.metric(
                                        "📊 Прогнозный XIRR",
                                        f"{forecast_data['forecast_xirr']:.1f}%",
                                        help="Внутренняя ставка доходности с учетом нереализованной выручки"
                                    )
                                else:
                                    st.metric(
                                        "📊 Прогнозный XIRR",
                                        "Н/Д",
                                        help="Не удалось рассчитать XIRR"
                                    )
                                
                                st.metric(
                                    "📅 Дней до реализации",
                                    f"{forecast_data['days_to_realization']}",
                                    help="Количество дней до планируемой реализации"
                                )
                                
                                st.metric(
                                    "📅 Дата реализации",
                                    f"{forecast_data['realization_date'].strftime('%d.%m.%Y')}",
                                    help="Дата планируемой реализации"
                                )
                        else:
                            st.warning("⚠️ Введите сумму нереализованной выручки для расчета")
            else:
                st.info("ℹ️ Для расчета ROI с нереализованной выручкой необходимо добавить вложения в разделах 'Управление вложениями'")
        
        # Создаем сетку KPI метрик (4 колонки)
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                label="💰 Итого к оплате (общий)",
                value=f"{total_to_pay['amount']:,.0f} ₽",
                delta=f"Среднее: {total_to_pay['avg_per_week']:,.0f} ₽/нед"
            )
            
            st.metric(
                label="📊 Общая сумма (общий)",
                value=f"{total_amount:,.0f} ₽",
                delta=f"Доходы + Расходы"
            )
            
            # Показываем правильный период в зависимости от галочки
            if use_first_investment_date and all_investments:
                period_df = combined_df[combined_df['Дата формирования'] >= pd.to_datetime(first_investment_date)]
                period_weeks = len(period_df)
                period_start = first_investment_date
                period_end = max_date.date()
            else:
                period_weeks = len(combined_df)
                period_start = min_date.date()
                period_end = max_date.date()
            
            st.metric(
                label="📅 Общий период",
                value=f"{period_weeks} недель",
                delta=f"{calculate_period_format(period_start, period_end)}"
            )
        
        with col2:
            st.metric(
                label="💸 Налог (7%)",
                value=f"{tax_amount:,.0f} ₽",
                delta=f"{(tax_amount/total_to_pay['amount']*100):.1f}% от дохода"
            )
            
            st.metric(
                label="📈 Все расходы (общий)",
                value=f"{total_expenses:,.0f} ₽",
                delta=f"{expenses_percentage:.1f}% от общей суммы"
            )
            
            st.metric(
                label="✅ Итого к оплате (налог)",
                value=f"{total_after_tax:,.0f} ₽",
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
                label="📈 ROI (общий)",
                value=f"{roi:.1f}%",
                delta=f"С первой даты вложений"
            )
            
            st.metric(
                label="🎯 XIRR (общий)",
                value=f"{xirr:.1f}%",
                delta=f"Внутренняя норма доходности"
            )
        
        with col4:
            st.metric(
                label="🚚 Сумма логистики (общий)",
                value=f"{expenses['logistics']['amount']:,.0f} ₽",
                delta=f"{(expenses['logistics']['amount']/total_amount*100):.1f}% от общей суммы"
            )
            
            st.metric(
                label="📦 Сумма хранения (общий)",
                value=f"{expenses['storage']['amount']:,.0f} ₽",
                delta=f"{(expenses['storage']['amount']/total_amount*100):.1f}% от общей суммы"
            )
            
            st.metric(
                label="📋 Прочие удержания (общий)",
                value=f"{expenses['other']['amount']:,.0f} ₽",
                delta=f"{(expenses['other']['amount']/total_amount*100):.1f}% от общей суммы"
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
