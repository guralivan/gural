# -*- coding: utf-8 -*-
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import os
import json
import pickle
import numpy as np

# Настройка страницы
st.set_page_config(page_title="Анализ воронки продаж", layout="wide")

# Динамический заголовок будет установлен после загрузки данных

# Функция для сворачиваемых разделов в сайдбаре
def sidebar_expander(title, key, default_expanded=False):
    """Создает сворачиваемый раздел в сайдбаре"""
    return st.sidebar.expander(title, expanded=default_expanded)

def get_season_from_date(date_str):
    """Определяет сезон по дате
    1 сезон: 1 июля - 31 декабря
    2 сезон: 1 февраля - 30 июня
    """
    try:
        # Парсим дату из формата "2024.01 (нед. 01)" или "2024.01"
        if '(' in date_str:
            date_part = date_str.split(' (')[0]  # "2024.01"
        else:
            date_part = date_str  # "2024.01"
        
        year, month = date_part.split('.')
        year = int(year)
        month = int(month)
        
        # Определяем сезон
        if month >= 7:  # Июль-декабрь
            return f"{year}-1"  # 1 сезон
        else:  # Январь-июнь
            return f"{year}-2"  # 2 сезон
    except:
        return None

def calculate_seasonal_kpi(pivot_data):
    """Рассчитывает KPI по сезонам"""
    seasons_data = {}
    
    # Получаем все столбцы с датами
    date_columns = [col for col in pivot_data.columns if any(year in col for year in ['2023', '2024', '2025'])]
    
    # Группируем столбцы по сезонам
    for col in date_columns:
        season = get_season_from_date(col)
        if season:
            if season not in seasons_data:
                seasons_data[season] = []
            seasons_data[season].append(col)
    
    # Рассчитываем KPI для каждого сезона
    kpi_results = {}
    
    for season, columns in seasons_data.items():
        season_kpi = {
            'season': season,
            'columns': columns,
            'orders_plan': 0,
            'orders_fact': 0,
            'sales_plan': 0,
            'sales_fact': 0,
            'revenue_plan': 0,
            'revenue_fact': 0,
            'conversion_rate': 0,
            'avg_price': 0,
            'has_data': False
        }
        
        # Суммируем данные по всем столбцам сезона
        for col in columns:
            # Заказы план
            if "Заказ план" in pivot_data.index:
                plan_val = pivot_data.loc["Заказ план", col] if pd.notna(pivot_data.loc["Заказ план", col]) else 0
                season_kpi['orders_plan'] += plan_val
            
            # Заказы факт
            if "Заказали, шт" in pivot_data.index:
                fact_val = pivot_data.loc["Заказали, шт", col] if pd.notna(pivot_data.loc["Заказали, шт", col]) else 0
                season_kpi['orders_fact'] += fact_val
            
            # Продажи план
            if "Продажа план" in pivot_data.index:
                plan_val = pivot_data.loc["Продажа план", col] if pd.notna(pivot_data.loc["Продажа план", col]) else 0
                season_kpi['sales_plan'] += plan_val
            
            # Продажи факт
            if "Выкупили, шт" in pivot_data.index:
                fact_val = pivot_data.loc["Выкупили, шт", col] if pd.notna(pivot_data.loc["Выкупили, шт", col]) else 0
                season_kpi['sales_fact'] += fact_val
            
            # Выручка план
            if "Выручка план" in pivot_data.index:
                plan_val = pivot_data.loc["Выручка план", col] if pd.notna(pivot_data.loc["Выручка план", col]) else 0
                season_kpi['revenue_plan'] += plan_val
            
            # Выручка факт
            if "Выкупили на сумму, ₽" in pivot_data.index:
                fact_val = pivot_data.loc["Выкупили на сумму, ₽", col] if pd.notna(pivot_data.loc["Выкупили на сумму, ₽", col]) else 0
                season_kpi['revenue_fact'] += fact_val
        
        # Рассчитываем дополнительные показатели
        if season_kpi['orders_fact'] > 0:
            season_kpi['conversion_rate'] = (season_kpi['sales_fact'] / season_kpi['orders_fact']) * 100
            season_kpi['has_data'] = True
        
        if season_kpi['sales_fact'] > 0:
            season_kpi['avg_price'] = season_kpi['revenue_fact'] / season_kpi['sales_fact']
            season_kpi['has_data'] = True
        
        kpi_results[season] = season_kpi
    
    return kpi_results

# Функции для кеширования данных
def get_current_week_column():
    """Возвращает название столбца для текущей недели"""
    current_date = datetime.now()
    year = current_date.year
    week_num = current_date.isocalendar().week
    
    # Определяем правильное соответствие недель и месяцев (неделя отдается месяцу с большим количеством дней)
    week_to_month_mapping = {
        # 2025 год - правильное распределение по дням в неделе
        27: 7, 28: 7, 29: 7, 30: 7, 31: 7,  # Июль
        32: 8, 33: 8, 34: 8, 35: 8,          # Август  
        36: 9, 37: 9, 38: 9, 39: 9, 40: 9,   # Сентябрь (недели 39-40 имеют больше дней в сентябре)
        41: 10, 42: 10, 43: 10, 44: 10,      # Октябрь
        45: 11, 46: 11, 47: 11, 48: 11,      # Ноябрь
        49: 12, 50: 12, 51: 12, 52: 12,      # Декабрь
        # Для недель в начале года (январь исключен)
        5: 2, 6: 2, 7: 2, 8: 2,              # Февраль
        9: 3, 10: 3, 11: 3, 12: 3, 13: 3,   # Март
        14: 4, 15: 4, 16: 4, 17: 4,          # Апрель
        18: 5, 19: 5, 20: 5, 21: 5, 22: 5,  # Май
        23: 6, 24: 6, 25: 6, 26: 6,          # Июнь
    }
    
    # Определяем правильный месяц для данной недели
    month = week_to_month_mapping.get(week_num, current_date.month)
    
    # Создаем название столбца в правильном формате
    if month == 9:  # Для сентября используем формат без ведущего нуля
        return f"{year}.{month} (нед. {week_num:02d})"
    else:
        return f"{year}.{month:02d} (нед. {week_num:02d})"

def generate_future_columns():
    """Генерирует столбцы с датами с выбранной недели начала плана до конца 2025 года"""
    future_columns = []
    
    # Получаем выбранную неделю начала плана
    start_week_for_plan = st.session_state.table_settings.get('start_week_for_plan', 26)
    
    # Начинаем с выбранной недели начала плана
    current_date = datetime.now()
    current_week = current_date.isocalendar().week
    current_year = current_date.year
    
    # Вычисляем дату начала выбранной недели
    if start_week_for_plan >= current_week:
        # Если выбранная неделя в текущем году
        weeks_ahead = start_week_for_plan - current_week
        start_date = current_date + timedelta(weeks=weeks_ahead)
    else:
        # Если выбранная неделя в следующем году
        weeks_ahead = (53 - current_week) + start_week_for_plan
        start_date = current_date + timedelta(weeks=weeks_ahead)
    
    # Определяем правильное соответствие недель и месяцев (неделя отдается месяцу с большим количеством дней)
    week_to_month_mapping = {
        # 2025 год - правильное распределение по дням в неделе
        27: 7, 28: 7, 29: 7, 30: 7, 31: 7,  # Июль
        32: 8, 33: 8, 34: 8, 35: 8,          # Август  
        36: 9, 37: 9, 38: 9, 39: 9, 40: 9,   # Сентябрь (недели 39-40 имеют больше дней в сентябре)
        41: 10, 42: 10, 43: 10, 44: 10,      # Октябрь
        45: 11, 46: 11, 47: 11, 48: 11,      # Ноябрь
        49: 12, 50: 12, 51: 12, 52: 12,      # Декабрь
        # Для недель в начале года (январь исключен)
        5: 2, 6: 2, 7: 2, 8: 2,              # Февраль
        9: 3, 10: 3, 11: 3, 12: 3, 13: 3,   # Март
        14: 4, 15: 4, 16: 4, 17: 4,          # Апрель
        18: 5, 19: 5, 20: 5, 21: 5, 22: 5,  # Май
        23: 6, 24: 6, 25: 6, 26: 6,          # Июнь
    }
    
    # Генерируем будущие столбцы до конца 2025 года
    while start_date.year <= 2025:
        year = start_date.year
        week_num = start_date.isocalendar().week
        
        # Определяем правильный месяц для данной недели
        month = week_to_month_mapping.get(week_num, start_date.month)
        
        # Создаем название столбца в правильном формате
        if month == 9:  # Для сентября используем формат без ведущего нуля
            column_name = f"{year}.{month} (нед. {week_num:02d})"
        else:
            column_name = f"{year}.{month:02d} (нед. {week_num:02d})"
        
        future_columns.append(column_name)
        
        # Переходим к следующей неделе
        start_date += timedelta(weeks=1)
        
        # Останавливаемся, если достигли конца 2025 года
        if start_date.year > 2025:
            break
    
    # Сортируем столбцы в прямом порядке (старые недели первыми, слева направо)
    sorted_columns = sorted(future_columns, reverse=False)
    return sorted_columns

def generate_seasonal_rentability_plan(pivot_data, monthly_rentability_percentages, base_rentability=15.0):
    """Генерирует план рентабельности с плавными переходами между месяцами"""
    try:
        import math
        import random
        
        
        # Ищем все недельные столбцы (содержат "(" и "нед.")
        weekly_columns = [col for col in pivot_data.columns if "(" in col and "нед." in col]
        
        
        if not weekly_columns:
            st.warning("⚠️ Не найдены недельные столбцы")
            return False
        
        # Сортируем столбцы по дате
        weekly_columns.sort()
        
        plan_generated = 0
        total_weeks = len(weekly_columns)
        
        # Создаем плавные переходы между месяцами для рентабельности
        for i, col in enumerate(weekly_columns):
            # Извлекаем год, месяц и неделю из названия столбца
            # Формат: "2025.9 (нед. 36)"
            try:
                # Разделяем по точке и скобке
                parts = col.split(" (")
                if len(parts) >= 2:
                    year_month = parts[0]  # "2025.9"
                    week_part = parts[1].split(")")[0]  # "нед. 36"
                    
                    # Извлекаем год и месяц
                    year_month_parts = year_month.split(".")
                    if len(year_month_parts) >= 2:
                        year = int(year_month_parts[0])
                        month = int(year_month_parts[1])
                        
                        # Извлекаем номер недели
                        week_num = int(week_part.split("нед. ")[1])
                    else:
                        continue
                else:
                    continue
            except (ValueError, IndexError):
                continue
            
            # Получаем базовый процент для месяца
            base_percentage = monthly_rentability_percentages.get(month, 100.0)
            
            # Определяем позицию недели в месяце (1-5)
            week_in_month = ((week_num - 1) % 5) + 1
            
            # Создаем плавные переходы внутри месяца
            monthly_variation = math.sin((week_in_month - 1) * math.pi / 2) * 0.02
            
            # Плавные переходы между месяцами
            month_transition = 0.0
            
            # Находим предыдущий и следующий месяцы
            prev_month = month - 1 if month > 1 else 12
            next_month = month + 1 if month < 12 else 1
            
            prev_percentage = monthly_rentability_percentages.get(prev_month, 100.0)
            next_percentage = monthly_rentability_percentages.get(next_month, 100.0)
            
            # Плавная интерполяция между месяцами
            if week_in_month == 1:  # Первая неделя месяца
                month_transition = (prev_percentage - base_percentage) * 0.2
            elif week_in_month == 5:  # Последняя неделя месяца
                month_transition = (next_percentage - base_percentage) * 0.2
            elif week_in_month == 2:  # Вторая неделя месяца
                month_transition = (prev_percentage - base_percentage) * 0.1
            elif week_in_month == 4:  # Четвертая неделя месяца
                month_transition = (next_percentage - base_percentage) * 0.1
            elif week_in_month == 3:  # Средняя неделя месяца
                month_transition = ((prev_percentage + next_percentage) / 2 - base_percentage) * 0.05
            
            # Применяем переходы
            final_percentage = base_percentage + month_transition + (base_percentage * monthly_variation)
            
            # Добавляем реалистичные колебания для рентабельности
            seasonal_factor = 1.0
            if month in [12, 1]:  # Новогодние праздники
                seasonal_factor = 0.95  # Снижение рентабельности
            elif month in [6, 7, 8]:  # Летний период
                seasonal_factor = 1.05  # Повышение рентабельности
            elif month in [2, 3]:  # После праздников
                seasonal_factor = 1.02  # Небольшое повышение
            
            # Случайные колебания (±1% для рентабельности)
            random_factor = 1.0 + (random.random() - 0.5) * 0.02
            
            # Финальный процент
            final_percentage = final_percentage * seasonal_factor * random_factor
            
            # Рассчитываем план рентабельности
            rentability_plan = base_rentability * (final_percentage / 100)
            
            # Автоматическое исправление падений в неделях 39, 40, 45, 49
            if week_num in [39, 40, 45, 49]:
                # Находим соседние недели для интерполяции
                prev_week_num = week_num - 1
                next_week_num = week_num + 1
                
                # Ищем соседние недели в данных
                prev_week_col = None
                next_week_col = None
                
                for other_col in weekly_columns:
                    if f"нед. {prev_week_num}" in other_col:
                        prev_week_col = other_col
                    elif f"нед. {next_week_num}" in other_col:
                        next_week_col = other_col
                
                # Интерполируем значение для проблемных недель
                if prev_week_col and next_week_col:
                    # Используем среднее между соседними неделями
                    prev_value = st.session_state.rentability_plan_values.get(prev_week_col, base_rentability * (final_percentage / 100))
                    next_value = st.session_state.rentability_plan_values.get(next_week_col, base_rentability * (final_percentage / 100))
                    rentability_plan = (prev_value + next_value) / 2
                elif prev_week_col:
                    # Если нет следующей недели, используем предыдущую с небольшим снижением
                    prev_value = st.session_state.rentability_plan_values.get(prev_week_col, base_rentability * (final_percentage / 100))
                    rentability_plan = prev_value * 0.95
                elif next_week_col:
                    # Если нет предыдущей недели, используем следующую с небольшим снижением
                    next_value = st.session_state.rentability_plan_values.get(next_week_col, base_rentability * (final_percentage / 100))
                    rentability_plan = next_value * 0.95
            
            # Сохраняем в session state
            st.session_state.rentability_plan_values[col] = round(rentability_plan, 1)
            
            # Специальная обработка для недель 39 и 40 - принудительно обновляем значения рентабельности
            if week_num in [39, 40]:
                # Убеждаемся, что значения не равны нулю
                if st.session_state.rentability_plan_values[col] == 0:
                    # Используем среднее значение соседних недель или базовое значение
                    if week_num == 39:
                        # Для недели 39 используем значение недели 38 с небольшим увеличением
                        week_38_col = f"{current_year}.9 (нед. 38)"
                        if week_38_col in st.session_state.rentability_plan_values:
                            base_val = st.session_state.rentability_plan_values[week_38_col]
                            if base_val > 0:
                                st.session_state.rentability_plan_values[col] = round(base_val * 1.02, 1)
                            else:
                                st.session_state.rentability_plan_values[col] = round(base_rentability * (final_percentage / 100), 1)
                        else:
                            st.session_state.rentability_plan_values[col] = round(base_rentability * (final_percentage / 100), 1)
                    elif week_num == 40:
                        # Для недели 40 используем значение недели 39 или недели 41
                        week_39_col = f"{current_year}.9 (нед. 39)"
                        week_41_col = f"{current_year}.10 (нед. 41)"
                        if week_39_col in st.session_state.rentability_plan_values and st.session_state.rentability_plan_values[week_39_col] > 0:
                            base_val = st.session_state.rentability_plan_values[week_39_col]
                            st.session_state.rentability_plan_values[col] = round(base_val * 0.99, 1)
                        elif week_41_col in st.session_state.rentability_plan_values and st.session_state.rentability_plan_values[week_41_col] > 0:
                            base_val = st.session_state.rentability_plan_values[week_41_col]
                            st.session_state.rentability_plan_values[col] = round(base_val * 1.01, 1)
                        else:
                            st.session_state.rentability_plan_values[col] = round(base_rentability * (final_percentage / 100), 1)
            plan_generated += 1
        
        
        if plan_generated > 0:
            save_settings_to_cache()  # Сохраняем значения в кеш
            st.success(f"✅ Сгенерирован план рентабельности для {plan_generated} недель")
            return True
        else:
            st.warning("⚠️ Не удалось сгенерировать план рентабельности")
            return False
            
    except Exception as e:
        st.error(f"❌ Ошибка при генерации плана рентабельности: {str(e)}")
        return False

def fix_weeks_39_40_plans():
    """Принудительно исправляет нулевые значения планов для недель 39 и 40"""
    current_year = datetime.now().year
    
    # Проверяем и исправляем планы заказов
    week_39_col = f"{current_year}.9 (нед. 39)"
    week_40_col = f"{current_year}.9 (нед. 40)"
    week_38_col = f"{current_year}.9 (нед. 38)"
    week_41_col = f"{current_year}.10 (нед. 41)"
    
    # Исправляем план заказов для недели 39
    if week_39_col in st.session_state.orders_plan_values and st.session_state.orders_plan_values[week_39_col] == 0:
        if week_38_col in st.session_state.orders_plan_values and st.session_state.orders_plan_values[week_38_col] > 0:
            base_val = st.session_state.orders_plan_values[week_38_col]
            st.session_state.orders_plan_values[week_39_col] = round(base_val * 1.05, 1)
        else:
            st.session_state.orders_plan_values[week_39_col] = 50.0  # Базовое значение
    
    # Исправляем план заказов для недели 40
    if week_40_col in st.session_state.orders_plan_values and st.session_state.orders_plan_values[week_40_col] == 0:
        if week_39_col in st.session_state.orders_plan_values and st.session_state.orders_plan_values[week_39_col] > 0:
            base_val = st.session_state.orders_plan_values[week_39_col]
            st.session_state.orders_plan_values[week_40_col] = round(base_val * 0.98, 1)
        elif week_41_col in st.session_state.orders_plan_values and st.session_state.orders_plan_values[week_41_col] > 0:
            base_val = st.session_state.orders_plan_values[week_41_col]
            st.session_state.orders_plan_values[week_40_col] = round(base_val * 1.02, 1)
        else:
            st.session_state.orders_plan_values[week_40_col] = 50.0  # Базовое значение
    
    # Исправляем план рентабельности для недели 39
    if week_39_col in st.session_state.rentability_plan_values and st.session_state.rentability_plan_values[week_39_col] == 0:
        if week_38_col in st.session_state.rentability_plan_values and st.session_state.rentability_plan_values[week_38_col] > 0:
            base_val = st.session_state.rentability_plan_values[week_38_col]
            st.session_state.rentability_plan_values[week_39_col] = round(base_val * 1.02, 1)
        else:
            st.session_state.rentability_plan_values[week_39_col] = 15.0  # Базовое значение
    
    # Исправляем план рентабельности для недели 40
    if week_40_col in st.session_state.rentability_plan_values and st.session_state.rentability_plan_values[week_40_col] == 0:
        if week_39_col in st.session_state.rentability_plan_values and st.session_state.rentability_plan_values[week_39_col] > 0:
            base_val = st.session_state.rentability_plan_values[week_39_col]
            st.session_state.rentability_plan_values[week_40_col] = round(base_val * 0.99, 1)
        elif week_41_col in st.session_state.rentability_plan_values and st.session_state.rentability_plan_values[week_41_col] > 0:
            base_val = st.session_state.rentability_plan_values[week_41_col]
            st.session_state.rentability_plan_values[week_40_col] = round(base_val * 1.01, 1)
        else:
            st.session_state.rentability_plan_values[week_40_col] = 15.0  # Базовое значение
    
    # Сохраняем изменения в кеш
    save_settings_to_cache()

def generate_seasonal_orders_plan(pivot_data, monthly_percentages, base_orders=50):
    """Генерирует план заказов с плавными переходами между месяцами и реалистичными колебаниями"""
    try:
        import math
        import random
        
        # Получаем текущую дату
        current_date = datetime.now()
        current_year = current_date.year
        
        # Ищем столбцы текущего года
        current_year_columns = [col for col in pivot_data.columns if str(current_year) in col and "(" in col]
        
        if not current_year_columns:
            st.warning(f"⚠️ Не найдены столбцы за {current_year} год")
            return False
        
        # Сортируем столбцы по дате
        current_year_columns.sort()
        
        plan_generated = 0
        total_weeks = len(current_year_columns)
        
        # Создаем базовую кривую на основе месячных процентов
        monthly_curve = []
        for col in current_year_columns:
            if f"{current_year}." in col:
                # Извлекаем месяц из названия столбца
                month_part = col.split(f"{current_year}.")[1].split(" (")[0]
                month = int(month_part)
                
                # Получаем процент для этого месяца
                percentage = monthly_percentages.get(month, 100.0)
                monthly_curve.append(percentage)
            else:
                monthly_curve.append(100.0)
        
        # Проверяем на дублирующиеся недели
        week_counts = {}
        for col in current_year_columns:
            if f"{current_year}." in col:
                week_part = col.split(" (нед. ")[1].split(")")[0]
                week_num = int(week_part)
                if week_num not in week_counts:
                    week_counts[week_num] = []
                week_counts[week_num].append(col)
        
        # Создаем плавные переходы между месяцами
        for i, col in enumerate(current_year_columns):
            if f"{current_year}." in col:
                # Извлекаем месяц и неделю
                month_part = col.split(f"{current_year}.")[1].split(" (")[0]
                month = int(month_part)
                week_part = col.split(" (нед. ")[1].split(")")[0]
                week_num = int(week_part)
                
                # Получаем базовый процент для месяца
                base_percentage = monthly_percentages.get(month, 100.0)
                
                # Определяем позицию недели в месяце (1-5) с более плавными переходами
                week_in_month = ((week_num - 1) % 5) + 1
                
                # Создаем плавные переходы внутри месяца
                # Небольшая вариация внутри месяца (±3% вместо ±5%)
                monthly_variation = math.sin((week_in_month - 1) * math.pi / 2) * 0.03
                
                # Плавные переходы между месяцами с более мягкими коэффициентами
                month_transition = 0.0
                
                # Находим предыдущий и следующий месяцы
                prev_month = month - 1 if month > 1 else 12
                next_month = month + 1 if month < 12 else 1
                
                prev_percentage = monthly_percentages.get(prev_month, 100.0)
                next_percentage = monthly_percentages.get(next_month, 100.0)
                
                # Более плавная интерполяция между месяцами
                if week_in_month == 1:  # Первая неделя месяца
                    # Плавный переход от предыдущего месяца (20% влияния вместо 30%)
                    month_transition = (prev_percentage - base_percentage) * 0.2
                elif week_in_month == 5:  # Последняя неделя месяца
                    # Плавный переход к следующему месяцу (20% влияния вместо 30%)
                    month_transition = (next_percentage - base_percentage) * 0.2
                elif week_in_month == 2:  # Вторая неделя месяца
                    # Меньшее влияние предыдущего месяца (10% вместо 15%)
                    month_transition = (prev_percentage - base_percentage) * 0.1
                elif week_in_month == 4:  # Четвертая неделя месяца
                    # Меньшее влияние следующего месяца (10% вместо 15%)
                    month_transition = (next_percentage - base_percentage) * 0.1
                elif week_in_month == 3:  # Средняя неделя месяца
                    # Минимальное влияние соседних месяцев (5%)
                    month_transition = ((prev_percentage + next_percentage) / 2 - base_percentage) * 0.05
                
                # Применяем переходы
                final_percentage = base_percentage + month_transition + (base_percentage * monthly_variation)
                
                # Добавляем реалистичные колебания
                # Сезонные колебания
                seasonal_factor = 1.0
                if month in [12, 1]:  # Новогодние праздники
                    seasonal_factor += 0.15
                elif month in [6, 7, 8]:  # Летние месяцы
                    seasonal_factor -= 0.1
                elif month in [3, 4]:  # Весенний подъем
                    seasonal_factor += 0.08
                
                # Небольшие случайные колебания (±2% вместо ±3%)
                random_factor = random.uniform(0.98, 1.02)
                
                # Объединяем все факторы
                final_percentage = final_percentage * seasonal_factor * random_factor
                
                # Рассчитываем план заказов
                orders_plan = base_orders * (final_percentage / 100)
                
                # Дублирование недель теперь устранено при группировке данных
                # Не нужно делить пополам, так как каждая неделя уникальна после группировки
                
                # Автоматическое исправление падений в неделях 39, 40, 45, 49
                if week_num in [39, 40, 45, 49]:
                    # Находим соседние недели для интерполяции
                    prev_week_num = week_num - 1
                    next_week_num = week_num + 1
                    
                    # Ищем соседние недели в данных
                    prev_week_col = None
                    next_week_col = None
                    
                    for other_col in current_year_columns:
                        if f"нед. {prev_week_num}" in other_col:
                            prev_week_col = other_col
                        elif f"нед. {next_week_num}" in other_col:
                            next_week_col = other_col
                    
                    # Интерполируем значение для проблемных недель
                    if prev_week_col and next_week_col:
                        # Используем среднее между соседними неделями
                        prev_value = st.session_state.orders_plan_values.get(prev_week_col, base_orders * (final_percentage / 100))
                        next_value = st.session_state.orders_plan_values.get(next_week_col, base_orders * (final_percentage / 100))
                        orders_plan = (prev_value + next_value) / 2
                    elif prev_week_col:
                        # Если нет следующей недели, используем предыдущую с небольшим снижением
                        prev_value = st.session_state.orders_plan_values.get(prev_week_col, base_orders * (final_percentage / 100))
                        orders_plan = prev_value * 0.95
                    elif next_week_col:
                        # Если нет предыдущей недели, используем следующую с небольшим снижением
                        next_value = st.session_state.orders_plan_values.get(next_week_col, base_orders * (final_percentage / 100))
                        orders_plan = next_value * 0.95
                
                # Сохраняем в session state
                st.session_state.orders_plan_values[col] = round(orders_plan, 1)
                plan_generated += 1
                
                # Специальная обработка для недель 39 и 40 - принудительно обновляем значения
                if week_num in [39, 40]:
                    # Убеждаемся, что значения не равны нулю
                    if st.session_state.orders_plan_values[col] == 0:
                        # Используем среднее значение соседних недель или базовое значение
                        if week_num == 39:
                            # Для недели 39 используем значение недели 38 с небольшим увеличением
                            week_38_col = f"{current_year}.9 (нед. 38)"
                            if week_38_col in st.session_state.orders_plan_values:
                                base_val = st.session_state.orders_plan_values[week_38_col]
                                if base_val > 0:
                                    st.session_state.orders_plan_values[col] = round(base_val * 1.05, 1)
                                else:
                                    st.session_state.orders_plan_values[col] = round(base_orders * (final_percentage / 100), 1)
                            else:
                                st.session_state.orders_plan_values[col] = round(base_orders * (final_percentage / 100), 1)
                        elif week_num == 40:
                            # Для недели 40 используем значение недели 39 или недели 41
                            week_39_col = f"{current_year}.9 (нед. 39)"
                            week_41_col = f"{current_year}.10 (нед. 41)"
                            if week_39_col in st.session_state.orders_plan_values and st.session_state.orders_plan_values[week_39_col] > 0:
                                base_val = st.session_state.orders_plan_values[week_39_col]
                                st.session_state.orders_plan_values[col] = round(base_val * 0.98, 1)
                            elif week_41_col in st.session_state.orders_plan_values and st.session_state.orders_plan_values[week_41_col] > 0:
                                base_val = st.session_state.orders_plan_values[week_41_col]
                                st.session_state.orders_plan_values[col] = round(base_val * 1.02, 1)
                            else:
                                st.session_state.orders_plan_values[col] = round(base_orders * (final_percentage / 100), 1)
        
        if plan_generated > 0:
            save_settings_to_cache()
            st.success(f"✅ Сгенерирован реалистичный план заказов для {plan_generated} недель")
            st.info(f"📊 Использованы плавные переходы между месяцами и реалистичные колебания")
            return True
        else:
            st.warning("⚠️ Не удалось сгенерировать план - нет подходящих данных")
            return False
            
    except Exception as e:
        st.error(f"❌ Ошибка при генерации плана: {e}")
        return False




def save_cache_data(data, filename):
    """Сохраняет данные в кеш файл"""
    try:
        with open(filename, 'wb') as f:
            pickle.dump(data, f)
    except Exception as e:
        st.error(f"Ошибка сохранения кеша: {e}")

def load_cache_data(filename):
    """Загружает данные из кеш файла"""
    try:
        if os.path.exists(filename):
            with open(filename, 'rb') as f:
                return pickle.load(f)
    except Exception as e:
        st.error(f"Ошибка загрузки кеша: {e}")
    return None

def save_settings_to_cache():
    """Сохраняет настройки рекламы, планов и рентабельности в кеш"""
    settings = {
        'reklama_values': st.session_state.get('reklama_values', {}),
        'orders_plan_values': st.session_state.get('orders_plan_values', {}),
        'sales_plan_values': st.session_state.get('sales_plan_values', {}),
        'rentabelnost_fact_values': st.session_state.get('rentabelnost_fact_values', {}),
        'rentability_plan_values': st.session_state.get('rentability_plan_values', {}),
        'rentability_params': st.session_state.get('rentability_params', {}),
        'rentability_cache': st.session_state.get('rentability_cache', {}),  # Кеш рассчитанных значений
        'uploaded_files_history': st.session_state.get('uploaded_files_history', []),  # История загруженных файлов
        'table_settings': st.session_state.get('table_settings', {}),  # Настройки таблицы
        'monthly_percentages': st.session_state.get('monthly_percentages', {}),  # Проценты по месяцам для планирования заказов
        'monthly_rentability_percentages': st.session_state.get('monthly_rentability_percentages', {}),  # Проценты по месяцам для планирования рентабельности
        'base_orders_value': st.session_state.get('base_orders_value', 50.0),  # Базовое значение заказов
        'base_rentability_value': st.session_state.get('base_rentability_value', 15.0),  # Базовое значение рентабельности
        'timestamp': datetime.now().isoformat()
    }
    save_cache_data(settings, 'settings_cache.pkl')

def load_settings_from_cache():
    """Загружает настройки рекламы, планов и рентабельности из кеша"""
    settings = load_cache_data('settings_cache.pkl')
    if settings:
        st.session_state.reklama_values = settings.get('reklama_values', {})
        st.session_state.orders_plan_values = settings.get('orders_plan_values', {})
        st.session_state.sales_plan_values = settings.get('sales_plan_values', {})
        st.session_state.rentabelnost_fact_values = settings.get('rentabelnost_fact_values', {})
        st.session_state.rentability_plan_values = settings.get('rentability_plan_values', {})
        st.session_state.rentability_params = settings.get('rentability_params', {})
        st.session_state.rentability_cache = settings.get('rentability_cache', {})  # Кеш рассчитанных значений
        st.session_state.uploaded_files_history = settings.get('uploaded_files_history', [])  # История загруженных файлов
        st.session_state.table_settings = settings.get('table_settings', {})  # Настройки таблицы
        st.session_state.monthly_percentages = settings.get('monthly_percentages', {})  # Проценты по месяцам для планирования заказов
        st.session_state.monthly_rentability_percentages = settings.get('monthly_rentability_percentages', {})  # Проценты по месяцам для планирования рентабельности
        st.session_state.base_orders_value = settings.get('base_orders_value', 50.0)  # Базовое значение заказов
        st.session_state.base_rentability_value = settings.get('base_rentability_value', 15.0)  # Базовое значение рентабельности
        return True
    return False

def save_table_structure_to_cache(pivot_data, final_columns):
    """Сохраняет структуру таблицы и порядок столбцов в кеш"""
    try:
        table_structure = {
            'columns_order': final_columns,
            'data_hash': hash(str(pivot_data.values.tobytes())),
            'timestamp': datetime.now().isoformat()
        }
        save_cache_data(table_structure, 'table_structure_cache.pkl')
    except Exception as e:
        st.error(f"Ошибка сохранения структуры таблицы: {e}")

def load_table_structure_from_cache():
    """Загружает структуру таблицы и порядок столбцов из кеша"""
    try:
        structure = load_cache_data('table_structure_cache.pkl')
        if structure:
            return structure.get('columns_order', None)
    except Exception as e:
        st.error(f"Ошибка загрузки структуры таблицы: {e}")
    return None

def save_data_to_cache(df, filename='data_cache.pkl'):
    """Сохраняет основные данные в кеш"""
    try:
        cache_data = {
            'dataframe': df,
            'timestamp': datetime.now().isoformat()
        }
        save_cache_data(cache_data, filename)
    except Exception as e:
        st.error(f"Ошибка сохранения данных: {e}")

def save_file_data_to_cache(file_data, filename):
    """Сохраняет данные файла в кеш с именем файла"""
    try:
        cache_filename = f"file_cache_{filename.replace('.', '_')}.pkl"
        cache_data = {
            'dataframe': file_data,
            'filename': filename,
            'timestamp': datetime.now().isoformat()
        }
        save_cache_data(cache_data, cache_filename)
        return True
    except Exception as e:
        st.error(f"Ошибка сохранения файла в кеш: {e}")
        return False

def load_file_data_from_cache(filename):
    """Загружает данные файла из кеша по имени файла"""
    try:
        cache_filename = f"file_cache_{filename.replace('.', '_')}.pkl"
        cache_data = load_cache_data(cache_filename)
        if cache_data:
            return cache_data.get('dataframe', None)
    except Exception as e:
        st.error(f"Ошибка загрузки файла из кеша: {e}")
    return None

def load_data_from_cache(filename='data_cache.pkl'):
    """Загружает основные данные из кеша"""
    try:
        cache_data = load_cache_data(filename)
        if cache_data:
            return cache_data.get('dataframe', None)
    except Exception as e:
        st.error(f"Ошибка загрузки данных: {e}")
    return None

# Функции расчета рентабельности (из приложения себестоимости)
def calculate_unit_economics(
    cost_price,           # Себестоимость
    retail_price,         # Текущая розн. цена (до скидки)
    discount_percent,     # Текущая скидка на сайте, %
    commission_rate,      # Комиссия, тариф базовый
    logistics_cost,       # Логистика тариф, руб
    advertising_percent,  # Реклама как доля от цены продажи, %
    buyout_percent,       # % выкупа
    storage_cost=0,       # Хранение (опционально)
    spp_discount=25.0     # СПП скидка
):
    """Расчет юнит-экономики по формулам из таблицы себестоимости"""
    
    # 1. Цена со скидкой
    price_with_discount = retail_price * (1 - discount_percent / 100)
    
    # 2. Цена с учетом СПП (не участвует в расчетах)
    price_with_spp = price_with_discount * (1 - spp_discount / 100)
    
    # 3. Комиссия в рублях
    commission_amount = price_with_discount * (commission_rate / 100)
    
    # 4. Реклама как доля от цены продажи
    advertising_cost = price_with_discount * (advertising_percent / 100)
    
    # 5. Доставка (упрощенная формула)
    delivery_cost = logistics_cost
    
    # 6. Налог с единицы (7%)
    tax_per_unit = price_with_discount * 0.07
    
    # 7. Прибыль с единицы (упрощенная формула)
    # Прибыль = Цена - Себестоимость - Комиссия - Реклама - Доставка - Налог - Хранение
    profit_per_unit = price_with_discount - cost_price - commission_amount - advertising_cost - delivery_cost - tax_per_unit - storage_cost
    
    # 9. Маржинальность (%)
    margin_percent = (profit_per_unit / price_with_discount) * 100 if price_with_discount > 0 else 0
    
    # 10. Рентабельность (%)
    profitability_percent = (profit_per_unit / cost_price) * 100 if cost_price > 0 else 0
    
    return {
        'Цена со скидкой': price_with_discount,
        'Цена с учетом СПП': price_with_spp,
        'Комиссия, руб': commission_amount,
        'Выручка с ед.': price_with_discount - commission_amount - advertising_cost - delivery_cost - tax_per_unit - storage_cost,
        'Реклама, руб': advertising_cost,
        'Налог с ед., руб': tax_per_unit,
        'Доставка с учетом выкупа': delivery_cost,
        'Прибыль с ед.': profit_per_unit,
        'Маржинальность, %': margin_percent,
        'Рентабельность, %': profitability_percent
    }

def get_rentability_cache_key(average_price, cost_price, discount_percent, commission_rate, 
                             logistics_cost, advertising_percent, buyout_percent, storage_cost, spp_discount):
    """Создает ключ для кеша рентабельности на основе всех параметров"""
    return f"{average_price:.2f}_{cost_price:.2f}_{discount_percent:.2f}_{commission_rate:.2f}_{logistics_cost:.2f}_{advertising_percent:.2f}_{buyout_percent:.2f}_{storage_cost:.2f}_{spp_discount:.2f}"

def calculate_complex_rentability(average_price, cost_price, discount_percent=0, commission_rate=15, 
                                 logistics_cost=50, advertising_percent=0, buyout_percent=85, 
                                 storage_cost=0, spp_discount=25.0, use_cache=True):
    """Сложный расчет рентабельности на основе средней цены (как "Цена со скидкой") с кешированием"""
    if average_price <= 0 or cost_price <= 0:
        return 0.0
    
    # Инициализируем кеш если его нет
    if 'rentability_cache' not in st.session_state:
        st.session_state.rentability_cache = {}
    
    # Создаем ключ для кеша
    cache_key = get_rentability_cache_key(average_price, cost_price, discount_percent, commission_rate, 
                                        logistics_cost, advertising_percent, buyout_percent, storage_cost, spp_discount)
    
    # Проверяем кеш
    if use_cache and cache_key in st.session_state.rentability_cache:
        return st.session_state.rentability_cache[cache_key]
    
    # Используем среднюю цену как "Цена со скидкой" из таблицы себестоимости
    price_with_discount = average_price
    
    # 1. Цена с учетом СПП (не участвует в расчетах)
    price_with_spp = price_with_discount * (1 - spp_discount / 100)
    
    # 2. Комиссия в рублях
    commission_amount = price_with_discount * (commission_rate / 100)
    
    # 3. Реклама как доля от цены продажи
    advertising_cost = price_with_discount * (advertising_percent / 100)
    
    # 4. Доставка (упрощенная формула)
    delivery_cost = logistics_cost
    
    # 5. Налог с единицы (7%)
    tax_per_unit = price_with_discount * 0.07
    
    # 6. Прибыль с единицы (упрощенная формула)
    # Прибыль = Цена - Себестоимость - Комиссия - Реклама - Доставка - Налог - Хранение
    profit_per_unit = price_with_discount - cost_price - commission_amount - advertising_cost - delivery_cost - tax_per_unit - storage_cost
    
    # 8. Рентабельность (%)
    profitability_percent = (profit_per_unit / cost_price) * 100 if cost_price > 0 else 0
    
    result = profitability_percent  # Показываем реальную рентабельность (включая отрицательную)
    
    # Сохраняем в кеш
    if use_cache:
        st.session_state.rentability_cache[cache_key] = result
        save_settings_to_cache()  # Сохраняем кеш
    
    return result

def calculate_profit_per_unit(average_price, cost_price, discount_percent=0, commission_rate=15, 
                             logistics_cost=50, advertising_percent=0, buyout_percent=85, 
                             storage_cost=0, spp_discount=25.0, use_cache=True):
    """Расчет прибыли на единицу на основе средней цены с кешированием"""
    if average_price <= 0 or cost_price <= 0:
        return 0.0
    
    # Инициализируем кеш если его нет
    if 'profit_per_unit_cache' not in st.session_state:
        st.session_state.profit_per_unit_cache = {}
    
    # Создаем ключ для кеша
    cache_key = get_rentability_cache_key(average_price, cost_price, discount_percent, commission_rate, 
                                        logistics_cost, advertising_percent, buyout_percent, storage_cost, spp_discount)
    
    # Проверяем кеш
    if use_cache and cache_key in st.session_state.profit_per_unit_cache:
        return st.session_state.profit_per_unit_cache[cache_key]
    
    # Используем среднюю цену как "Цена со скидкой" из таблицы себестоимости
    price_with_discount = average_price
    
    # 1. Цена с учетом СПП (не участвует в расчетах)
    price_with_spp = price_with_discount * (1 - spp_discount / 100)
    
    # 2. Комиссия в рублях
    commission_amount = price_with_discount * (commission_rate / 100)
    
    # 3. Реклама как доля от цены продажи
    advertising_cost = price_with_discount * (advertising_percent / 100)
    
    # 4. Доставка (упрощенная формула)
    delivery_cost = logistics_cost
    
    # 5. Налог с единицы (7%)
    tax_per_unit = price_with_discount * 0.07
    
    # 6. Прибыль с единицы (упрощенная формула)
    # Прибыль = Цена - Себестоимость - Комиссия - Реклама - Доставка - Налог - Хранение
    profit_per_unit = price_with_discount - cost_price - commission_amount - advertising_cost - delivery_cost - tax_per_unit - storage_cost
    
    # Сохраняем в кеш
    if use_cache:
        st.session_state.profit_per_unit_cache[cache_key] = profit_per_unit
        save_settings_to_cache()  # Сохраняем кеш
    
    return profit_per_unit

def load_additional_data(uploaded_file):
    """Загружает дополнительные данные из загруженного файла"""
    try:
        # Определяем тип файла
        if uploaded_file.name.endswith('.xlsx') or uploaded_file.name.endswith('.xls'):
            # Загружаем Excel файл с улучшенной обработкой
            df = None
            
            # Простая загрузка файла
            try:
                # Пробуем с заголовком на строке 1 (как показала диагностика)
                df = pd.read_excel(uploaded_file, sheet_name="Товары", header=1)
                st.info("✅ Файл загружен с заголовком на строке 1")
            except Exception as e1:
                try:
                    # Если не получилось, пробуем с обычными заголовками
                    df = pd.read_excel(uploaded_file, sheet_name="Товары", header=0)
                    st.info("✅ Файл загружен с обычными заголовками")
                except Exception as e2:
                    st.error(f"❌ Не удалось загрузить файл. Ошибки: {e1}, {e2}")
                    return None
            
            if df is None or len(df) == 0:
                st.error("❌ Файл пуст или не содержит данных")
                return None
            
            # Очищаем данные от текста "Детальный отчет воронки продаж по карточкам товаров"
            # Убираем этот текст из всех столбцов
            for col in df.columns:
                if df[col].dtype == 'object':
                    # Убираем строки, которые содержат только этот текст
                    mask = df[col].astype(str).str.contains('Детальный отчет воронки продаж по карточкам товаров', na=False)
                    if mask.any():
                        df = df[~mask]
                    
                    # Убираем этот текст из содержимого ячеек
                    df[col] = df[col].astype(str).str.replace('Детальный отчет воронки продаж по карточкам товаров', '', regex=False)
            
            # Убираем этот текст из названий столбцов
            df.columns = [str(col).replace('Детальный отчет воронки продаж по карточкам товаров', '').strip() 
                         for col in df.columns]
            
            st.info(f"📊 Загружено {len(df)} строк и {len(df.columns)} столбцов")
            
            return df
        else:
            st.error("Поддерживаются только файлы Excel (.xlsx, .xls)")
            return None
    except Exception as e:
        st.error(f"Ошибка загрузки файла: {e}")
        return None

def replace_dataframes(df1, df2):
    """Заменяет данные новым файлом (не объединяет)"""
    try:
        # Просто возвращаем новый файл (заменяем старые данные)
        # Не проверяем общие столбцы, так как новый файл может иметь другую структуру
        st.info(f"🔄 Данные заменены новым файлом")
        st.info(f"📊 Количество строк в новом файле: {len(df2)}")
        st.info(f"📋 Количество столбцов в новом файле: {len(df2.columns)}")
        
        # Показываем информацию о столбцах для отладки
        if len(df2.columns) > 0:
            st.info(f"📝 Первые 5 столбцов: {list(df2.columns[:5])}")
        
        return df2
        
    except Exception as e:
        st.error(f"Ошибка замены данных: {e}")
        return df1

# Функция для загрузки данных
@st.cache_data
def load_voronka_data():
    """Загружает данные из файла Voronka.xlsx"""
    try:
        voronka_path = "Voronka.xlsx"
        
        if not os.path.exists(voronka_path):
            st.error(f"Файл {voronka_path} не найден!")
            return None
        
        # Пробуем загрузить данные с листа "Товары"
        # Сначала пробуем с заголовком на строке 1 (как показала диагностика)
        try:
            df = pd.read_excel(voronka_path, sheet_name="Товары", header=1)
        except Exception as e1:
            try:
                # Если не получилось, пробуем с обычными заголовками
                df = pd.read_excel(voronka_path, sheet_name="Товары", header=0)
            except Exception as e2:
                st.error(f"❌ Не удалось загрузить файл {voronka_path}. Ошибки: {e1}, {e2}")
                return None
            
            # Убираем длинный префикс из названий столбцов
            prefix = "Детальный отчет воронки продаж по карточкам товаров "
        df.columns = [str(col).replace(prefix, "").replace("Детальный отчет воронки продаж по карточкам товаров", "").strip() 
                     for col in df.columns]
        
        # Удаляем строки с текстом "Детальный отчет воронки продаж по карточкам товаров"
        # и очищаем содержимое ячеек от этого текста
        for col in df.columns:
            if df[col].dtype == 'object':  # Только для текстовых столбцов
                # Убираем строки, которые содержат только этот текст
                mask = df[col].astype(str).str.contains('Детальный отчет воронки продаж по карточкам товаров', na=False)
                if mask.any():
                    df = df[~mask]
                
                # Убираем этот текст из содержимого ячеек
                df[col] = df[col].astype(str).str.replace('Детальный отчет воронки продаж по карточкам товаров', '', regex=False)
        
        # Проверяем и удаляем дубликаты
        initial_count = len(df)
        
        # Сначала удаляем полные дубликаты
        df = df.drop_duplicates()
        
        # Затем проверяем дубликаты по ключевым полям (если есть столбец с датой)
        date_columns = [col for col in df.columns if 'дата' in col.lower() or 'date' in col.lower()]
        if date_columns:
            # НЕ удаляем дубликаты по дате - они нужны для правильной агрегации
            # Вместо этого просто информируем о них
            date_duplicates = df.duplicated(subset=date_columns).sum()
            if date_duplicates > 0:
                st.info(f"ℹ️ Найдено {date_duplicates} записей с одинаковыми датами - они будут агрегированы")
        
        final_count = len(df)
        if initial_count != final_count:
            st.warning(f"⚠️ Удалено {initial_count - final_count} дубликатов из файла Voronka.xlsx")
            
        # Дополнительная проверка на дубликаты по неделям (информационная)
        if 'Неделя_Год' in df.columns:
            week_counts = df['Неделя_Год'].value_counts()
            suspicious_weeks = week_counts[week_counts > 1]
            if len(suspicious_weeks) > 0:
                st.info(f"ℹ️ Найдены недели с несколькими записями: {list(suspicious_weeks.index)}")
                for week in suspicious_weeks.index:
                    st.info(f"   - {week}: {suspicious_weeks[week]} записей (будут агрегированы)")
            else:
                st.info("✅ Каждая неделя имеет только одну запись")
                
        # Дополнительная диагностика: проверяем общие дубликаты
        total_duplicates = df.duplicated().sum()
        if total_duplicates > 0:
            st.warning(f"⚠️ Найдено {total_duplicates} полных дубликатов в исходных данных")
        else:
            st.info("✅ Полные дубликаты в исходных данных не найдены")
        
        return df
        
    except Exception as e:
        st.error(f"❌ Ошибка загрузки файла: {e}")
        return None

# Инициализируем список загруженных файлов в самом начале
if 'uploaded_files_history' not in st.session_state:
    st.session_state.uploaded_files_history = []

# Автоматически загружаем последний файл при запуске
if st.session_state.uploaded_files_history and 'auto_loaded_data' not in st.session_state:
    last_file = st.session_state.uploaded_files_history[-1]
    cached_file_data = load_file_data_from_cache(last_file['name'])
    if cached_file_data is not None:
        # Сохраняем данные в глобальную переменную для использования в основной логике
        st.session_state['auto_loaded_data'] = cached_file_data
        st.session_state['auto_loaded_filename'] = last_file['name']
        st.sidebar.success(f"✅ Автоматически загружен последний файл: {last_file['name']}")
    else:
        st.sidebar.warning(f"⚠️ Не удалось загрузить последний файл: {last_file['name']}")

# Чистый и организованный сайдбар
st.sidebar.markdown("---")
st.sidebar.markdown("## 📊 Управление данными")

# Загрузка файлов
with st.sidebar.expander("📁 Загрузка файлов", expanded=True):
    uploaded_file = st.file_uploader(
        "Загрузить новый файл:",
        type=['xlsx', 'xls'],
        help="Файл заменит текущие данные",
        key="main_file_uploader"
    )
    
    # История файлов (компактная версия)
    if st.session_state.uploaded_files_history:
        st.markdown("**📂 Последние файлы:**")
        recent_files = st.session_state.uploaded_files_history[-2:]  # Только 2 последних
        
        for i, file_info in enumerate(recent_files):
            file_name = file_info['name']
            upload_time = file_info['time']
        
            col1, col2 = st.columns([3, 1])
        with col1:
                st.caption(f"📄 {file_name}")
                st.caption(f"⏰ {upload_time}")
        with col2:
                if st.button("📥", key=f"load_file_{i}", help="Загрузить"):
                    cached_file_data = load_file_data_from_cache(file_name)
                if cached_file_data is not None:
                    st.session_state['auto_loaded_data'] = cached_file_data
                    st.session_state['auto_loaded_filename'] = file_name
                    save_data_to_cache(cached_file_data)
                    st.success(f"✅ Загружен: {file_name}")
                else:
                    st.error(f"❌ Ошибка загрузки")
        
        if st.button("🔄 Загрузить последний", help="Загрузить самый последний файл"):
            last_file = st.session_state.uploaded_files_history[-1]
            cached_file_data = load_file_data_from_cache(last_file['name'])
            if cached_file_data is not None:
                st.session_state['auto_loaded_data'] = cached_file_data
                st.session_state['auto_loaded_filename'] = last_file['name']
                save_data_to_cache(cached_file_data)
                st.success(f"✅ Загружен: {last_file['name']}")
        else:
                st.error("❌ Ошибка загрузки")
    else:
        st.info("📂 История файлов пуста")


# Приоритет загрузки: 1) Автоматически загруженные данные, 2) Кеш, 3) Voronka.xlsx
df = None

# 1. Сначала проверяем автоматически загруженные данные (последний файл из истории)
if 'auto_loaded_data' in st.session_state:
    df = st.session_state['auto_loaded_data']
    filename = st.session_state.get('auto_loaded_filename', 'неизвестный файл')
    st.sidebar.success(f"✅ Данные автоматически загружены из последнего файла: {filename}")

# 2. Если автоматически загруженных данных нет, проверяем кеш
if df is None:
    df = load_data_from_cache()
    if df is not None:
        st.sidebar.success("📊 Данные автоматически загружены из кеша!")

# 3. Если кеш пуст, пытаемся загрузить Voronka.xlsx
if df is None:
    df = load_voronka_data()
    if df is not None:
        st.sidebar.info("📄 Загружен файл Voronka.xlsx")

# 4. Если ничего не найдено
if df is None:
    st.sidebar.warning("⚠️ Файлы не найдены. Загрузите файл для начала работы.")

# Если данные загружены, сохраняем их в кеш и устанавливаем заголовок
if df is not None:
    save_data_to_cache(df)
    
    # Устанавливаем динамический заголовок
    if 'auto_loaded_filename' in st.session_state:
        filename = st.session_state['auto_loaded_filename']
        st.title(f"📊 Анализ воронки продаж ({filename})")
    else:
        st.title("📊 Анализ воронки продаж")

# Если загружен новый файл, заменяем данные
if uploaded_file is not None:
    st.info(f"🔄 Загружается файл: {uploaded_file.name}")
    additional_df = load_additional_data(uploaded_file)
    if additional_df is not None:
        # Заменяем данные независимо от наличия старых данных
        df = replace_dataframes(df, additional_df)
        
        # Сохраняем обновленные данные в кеш
        save_data_to_cache(df)
        
        # Сохраняем данные файла в отдельный кеш для автоматической загрузки
        save_file_data_to_cache(df, uploaded_file.name)
        
        # Обновляем auto_loaded_data для следующего запуска
        st.session_state['auto_loaded_data'] = df
        st.session_state['auto_loaded_filename'] = uploaded_file.name
        
        # ОБНОВЛЯЕМ ГЛАВНУЮ ПЕРЕМЕННУЮ df для отображения в таблице
        # Это критически важно для корректного отображения данных
        # Принудительно обновляем df из session_state
        if 'auto_loaded_data' in st.session_state:
            df = st.session_state['auto_loaded_data']
        
        # Добавляем файл в историю
        if 'uploaded_files_history' not in st.session_state:
            st.session_state.uploaded_files_history = []
        
        # Создаем информацию о файле
        file_info = {
            'name': uploaded_file.name,
            'time': datetime.now().strftime("%d.%m.%Y %H:%M"),
            'size': uploaded_file.size,
            'type': uploaded_file.type
        }
        
        # Добавляем в историю (избегаем дублирования)
        if file_info not in st.session_state.uploaded_files_history:
            st.session_state.uploaded_files_history.append(file_info)
            
            # Ограничиваем историю до 10 файлов
            if len(st.session_state.uploaded_files_history) > 10:
                st.session_state.uploaded_files_history = st.session_state.uploaded_files_history[-10:]
        
        # Сохраняем настройки в кеш
        save_settings_to_cache()
        
        st.sidebar.success(f"✅ Файл {uploaded_file.name} успешно заменил данные!")
        st.sidebar.info(f"📊 Количество строк в новом файле: {len(df)}")
        st.sidebar.info(f"📂 Файл добавлен в историю и сохранен в кеш")
        
        # Обновляем заголовок
        st.title(f"📊 Анализ воронки продаж ({uploaded_file.name})")
        
    else:
        st.sidebar.error("❌ Не удалось загрузить файл. Проверьте формат файла.")

# Управление кешем (компактная версия)
with st.sidebar.expander("🗂️ Управление кешем", expanded=False):
    col1, col2 = st.columns(2)
with col1:
        if st.button("💾 Сохранить", help="Сохранить данные в кеш"):
            if df is not None:
                save_data_to_cache(df)
                st.success("✅ Сохранено!")
        else:
                st.warning("Нет данных")
with col2:
        if st.button("🔄 Загрузить", help="Загрузить из кеша"):
            cached_df = load_data_from_cache()
            if cached_df is not None:
                df = cached_df
                st.session_state['auto_loaded_data'] = cached_df
                st.success("✅ Загружено!")
            else:
                st.warning("Кеш пуст")

        if st.button("🗑️ Очистить кеш", help="Удалить все файлы кеша"):
            cache_files = ['settings_cache.pkl', 'table_structure_cache.pkl', 'data_cache.pkl']
            for cache_file in cache_files:
                if os.path.exists(cache_file):
                    os.remove(cache_file)
            if 'rentability_cache' in st.session_state:
                st.session_state.rentability_cache = {}
            st.success("✅ Кеш очищен!")

# Информация о кеше рентабельности
if 'rentability_cache' in st.session_state:
    cache_count = len(st.session_state.rentability_cache)
    st.caption(f"💰 Кеш рентабельности: {cache_count} значений")
    
    if st.button("🔄 Пересчитать", help="Пересчитать рентабельность"):
        st.session_state.rentability_cache = {}
        save_settings_to_cache()
        st.success("✅ Кеш очищен! Будет пересчет.")

# Настройки таблицы (компактная версия)
with st.sidebar.expander("⚙️ Настройки таблицы", expanded=False):
    # Инициализируем session state для настроек таблицы (если не инициализирован)
    if 'table_settings' not in st.session_state:
        st.session_state.table_settings = {
                    'show_future_dates': True,
                    'start_week_for_plan': 26  # Начальная неделя для плана продаж (можно выбрать любую неделю)
    }

# Настройка отображения будущих дат
    show_future_dates = st.checkbox(
    "📅 Показать столбцы до конца 2025 года",
    value=st.session_state.table_settings.get('show_future_dates', True),
    help="Показывает все недели с текущей даты до конца 2025 года с пустыми ячейками для планирования продаж"
)

    # Настройка недели начала плана продаж
    st.markdown("---")
    st.markdown("**📊 План продаж:**")
    
    # Получаем текущую неделю
    current_week = datetime.now().isocalendar().week
    
    start_week_for_plan = st.number_input(
        "🎯 Неделя начала плана продаж:",
        min_value=1,
        max_value=53,
        value=st.session_state.table_settings.get('start_week_for_plan', 26),
        help="Выберите с какой недели начинать план продаж (можно выбрать прошедшие недели, например 26)"
    )
    
    # Показываем информацию о выбранной неделе
    if start_week_for_plan == current_week:
        st.info(f"📅 Выбрана текущая неделя {start_week_for_plan}")
    elif start_week_for_plan < current_week:
        st.success(f"✅ План начинается с прошедшей недели {start_week_for_plan} (текущая: {current_week})")
    else:
        st.info(f"📋 План начинается с будущей недели {start_week_for_plan} (текущая: {current_week})")
    
    # Кнопка для скрытия недель до выбранной
    if st.button("👁️ Скрыть недели до выбранной", help=f"Скрыть из таблицы все недели до недели {start_week_for_plan}"):
        # Сохраняем неделю начала плана для скрытия недель
        st.session_state.table_settings['hide_weeks_before'] = start_week_for_plan
        
        st.success(f"✅ Настроено скрытие недель до {start_week_for_plan}")
        st.info(f"ℹ️ Недели до {start_week_for_plan} будут скрыты из таблицы и расчетов")
        st.rerun()
    
    # Кнопка для показа всех недель
    if 'hide_weeks_before' in st.session_state.table_settings:
        if st.button("🔄 Показать все недели", help="Показать все недели в таблице"):
            del st.session_state.table_settings['hide_weeks_before']
            st.success("✅ Все недели будут показаны в таблице")
            st.rerun()

# Обновляем настройки
if show_future_dates != st.session_state.table_settings.get('show_future_dates', True):
    st.session_state.table_settings['show_future_dates'] = show_future_dates

    if start_week_for_plan != st.session_state.table_settings.get('start_week_for_plan', current_week):
        st.session_state.table_settings['start_week_for_plan'] = start_week_for_plan
        # Очищаем кеш планов при изменении недели начала
        st.session_state.orders_plan_values = {}
        st.session_state.rentability_plan_values = {}
        save_settings_to_cache()
        st.success(f"✅ План продаж будет начинаться с недели {start_week_for_plan}")

# Инициализируем параметры рентабельности если их нет
if 'rentability_params' not in st.session_state:
    st.session_state.rentability_params = {
        'cost_price': 100.0,  # Себестоимость
        'discount_percent': 0.0,  # Скидка на сайте
        'commission_rate': 15.0,  # Комиссия WB
        'logistics_cost': 50.0,  # Логистика
        'advertising_percent': 0.0,  # Реклама
        'buyout_percent': 22.0,  # % выкупа
        'storage_cost': 0.0,  # Хранение
        'spp_discount': 25.0  # СПП скидка
    }

# Параметры рентабельности (компактная версия)
with st.sidebar.expander("💰 Параметры рентабельности", expanded=False):
    
    # Простой интерфейс для настройки рентабельности
    st.markdown("**Настройка рентабельности:**")

# Себестоимость
    cost_price = st.number_input(
    "Себестоимость (₽):",
    min_value=0.0,
    value=st.session_state.rentability_params.get('cost_price', 100.0),
    step=10.0,
        help="Себестоимость товара"
    )
    
    # Скидка на сайте
    discount_percent = st.number_input(
        "Скидка на сайте (%):",
        min_value=0.0,
        max_value=100.0,
        value=st.session_state.rentability_params.get('discount_percent', 0.0),
        step=1.0,
        help="Скидка на сайте в процентах"
)

# Комиссия WB
    commission_rate = st.number_input(
    "Комиссия WB (%):",
    min_value=0.0,
    max_value=50.0,
    value=st.session_state.rentability_params.get('commission_rate', 15.0),
    step=0.5,
        help="Комиссия Wildberries в процентах"
)

# Логистика
    logistics_cost = st.number_input(
    "Логистика (₽):",
    min_value=0.0,
    value=st.session_state.rentability_params.get('logistics_cost', 50.0),
    step=5.0,
    help="Стоимость логистики"
)

# Реклама
    advertising_percent = st.number_input(
        "Реклама (%):",
    min_value=0.0,
    max_value=100.0,
    value=st.session_state.rentability_params.get('advertising_percent', 0.0),
    step=1.0,
        help="Процент на рекламу"
)

# % выкупа
    buyout_percent = st.number_input(
        "% выкупа (%):",
    min_value=0.0,
    max_value=100.0,
    value=st.session_state.rentability_params.get('buyout_percent', 22.0),
    step=1.0,
    help="Процент выкупа товара (по умолчанию 22%)"
)

# Хранение
    storage_cost = st.number_input(
    "Хранение (₽):",
    min_value=0.0,
    value=st.session_state.rentability_params.get('storage_cost', 0.0),
    step=1.0,
    help="Стоимость хранения"
)

# СПП скидка
    spp_discount = st.number_input(
    "СПП скидка (%):",
    min_value=0.0,
    max_value=100.0,
    value=st.session_state.rentability_params.get('spp_discount', 25.0),
    step=1.0,
        help="Скидка СПП"
    )


# Инициализируем кеш рентабельности если его нет
if 'rentability_cache' not in st.session_state:
    st.session_state.rentability_cache = {}

# Автоматически загружаем настройки из кеша при старте
if not load_settings_from_cache():
    # Если кеш не найден, инициализируем значения по умолчанию
    if 'reklama_values' not in st.session_state:
        st.session_state.reklama_values = {}
    if 'orders_plan_values' not in st.session_state:
        st.session_state.orders_plan_values = {}
    if 'sales_plan_values' not in st.session_state:
        st.session_state.sales_plan_values = {}
    if 'rentabelnost_fact_values' not in st.session_state:
        st.session_state.rentabelnost_fact_values = {}
    if 'rentability_plan_values' not in st.session_state:
        st.session_state.rentability_plan_values = {}
    if 'uploaded_files_history' not in st.session_state:
        st.session_state.uploaded_files_history = []
    if 'table_settings' not in st.session_state:
        st.session_state.table_settings = {
            'show_future_dates': True
        }
    if 'monthly_percentages' not in st.session_state:
        st.session_state.monthly_percentages = {}
    if 'monthly_rentability_percentages' not in st.session_state:
        st.session_state.monthly_rentability_percentages = {}
    if 'base_orders_value' not in st.session_state:
        st.session_state.base_orders_value = 50.0
    
    # Загружаем настройки из кеша при инициализации
    if not hasattr(st.session_state, '_settings_loaded'):
        load_settings_from_cache()
        st.session_state._settings_loaded = True
        
        # Исправляем нулевые значения для недель 39 и 40
        if hasattr(st.session_state, '_settings_loaded'):
            fix_weeks_39_40_plans()
    if 'rentability_params' not in st.session_state:
        st.session_state.rentability_params = {
            'cost_price': 100.0,  # Себестоимость
            'discount_percent': 0.0,  # Скидка
            'commission_rate': 15.0,  # Комиссия WB
            'logistics_cost': 50.0,  # Логистика
            'advertising_percent': 0.0,  # Реклама
            'buyout_percent': 22.0,  # % выкупа
            'storage_cost': 0.0  # Хранение
        }

        
        # Предупреждение если % выкупа слишком низкий
        if buyout_percent < 50:
            st.warning(f"⚠️ % выкупа {buyout_percent}% слишком низкий! Рекомендуется 80-95%")


# Обновляем параметры рентабельности
params_changed = False
if cost_price != st.session_state.rentability_params.get('cost_price', 100.0):
    st.session_state.rentability_params['cost_price'] = cost_price
    params_changed = True
if commission_rate != st.session_state.rentability_params.get('commission_rate', 15.0):
    st.session_state.rentability_params['commission_rate'] = commission_rate
    params_changed = True
if logistics_cost != st.session_state.rentability_params.get('logistics_cost', 50.0):
    st.session_state.rentability_params['logistics_cost'] = logistics_cost
    params_changed = True
if discount_percent != st.session_state.rentability_params.get('discount_percent', 0.0):
    st.session_state.rentability_params['discount_percent'] = discount_percent
    params_changed = True
if advertising_percent != st.session_state.rentability_params.get('advertising_percent', 0.0):
    st.session_state.rentability_params['advertising_percent'] = advertising_percent
    params_changed = True
if buyout_percent != st.session_state.rentability_params.get('buyout_percent', 22.0):
    st.session_state.rentability_params['buyout_percent'] = buyout_percent
    params_changed = True
if storage_cost != st.session_state.rentability_params.get('storage_cost', 0.0):
    st.session_state.rentability_params['storage_cost'] = storage_cost
    params_changed = True
if spp_discount != st.session_state.rentability_params.get('spp_discount', 25.0):
    st.session_state.rentability_params['spp_discount'] = spp_discount
    params_changed = True

    # Сохраняем изменения если они есть
if params_changed:
        save_settings_to_cache()
        # Очищаем кеш рентабельности при изменении параметров
        st.session_state.rentability_cache = {}


# КРИТИЧЕСКОЕ ИСПРАВЛЕНИЕ: Обновляем df из session_state перед отображением таблицы
if 'auto_loaded_data' in st.session_state and st.session_state['auto_loaded_data'] is not None:
    df = st.session_state['auto_loaded_data']

if df is not None:
    # Ищем столбцы с заказами и выкупами
    
    orders_col = None
    sales_col = None
    date_col = None
    prodazha_col = None
    orders_sum_col = None
    sales_sum_col = None
    conversion_col = None
    cart_conversion_col = None
    cancelled_col = None
    order_conversion_col = None
    card_views_col = None
    cancelled_wb_col = None
    orders_plan_col = None
    sales_plan_col = None
    
    # Простой поиск по точному совпадению
    for col in df.columns:
        col_str = str(col).strip()
        col_lower = col_str.lower()
        
        # Очищаем название столбца от лишнего текста для поиска
        clean_col_lower = col_lower.replace('детальный отчет воронки продаж по карточкам товаров', '').strip()
        # Убираем лишние пробелы
        clean_col_lower = ' '.join(clean_col_lower.split())
        
        # Ищем столбцы с заказами (точное совпадение)
        if clean_col_lower == 'заказали, шт' or col_lower == 'заказали, шт':
            orders_col = col
        
        # Ищем столбцы с выкупами (точное совпадение)
        elif clean_col_lower == 'выкупили, шт' or col_lower == 'выкупили, шт':
            sales_col = col
        
        # Ищем столбцы с датами
        elif any(word in col_lower for word in ['дата', 'date', 'день', 'day']):
            date_col = col
        
        # Ищем столбец "Продажа"
        elif clean_col_lower == 'продажа' or col_lower == 'продажа':
            prodazha_col = col
        
        # Ищем столбец "Заказали на сумму, ₽" (исключаем ВБ клуб)
        elif (('заказали на сумму' in clean_col_lower and '₽' in col_str and 'вб клуб' not in clean_col_lower) or 
              ('заказали на сумму' in col_lower and '₽' in col_str and 'вб клуб' not in col_lower)):
            orders_sum_col = col
        
        # Ищем столбец "Выкупили на сумму, ₽" (исключаем ВБ клуб)
        elif (('выкупили на сумму' in clean_col_lower and '₽' in col_str and 'вб клуб' not in clean_col_lower) or 
              ('выкупили на сумму' in col_lower and '₽' in col_str and 'вб клуб' not in col_lower)):
            sales_sum_col = col
        
        # Ищем столбец "Процент выкупа" (исключаем ВБ клуб)
        elif (('процент выкупа' in clean_col_lower and 'вб клуб' not in clean_col_lower) or 
              ('процент выкупа' in col_lower and 'вб клуб' not in col_lower)):
            conversion_col = col
        
        # Ищем столбец "Конверсия в корзину, %"
        elif 'конверсия в корзину' in clean_col_lower or 'конверсия в корзину' in col_lower:
            cart_conversion_col = col
        
        # Ищем столбец "Отменили, шт" (исключаем ВБ клуб)
        elif (('отменили' in clean_col_lower and 'шт' in col_str and 'вб клуб' not in clean_col_lower) or 
              ('отменили' in col_lower and 'шт' in col_str and 'вб клуб' not in col_lower)):
            cancelled_col = col
        
        # Ищем столбец "Конверсия в заказ, %"
        elif 'конверсия в заказ' in clean_col_lower or 'конверсия в заказ' in col_lower:
            order_conversion_col = col
        
        # Ищем столбец "Переходы в карточку"
        elif 'переходы в карточку' in clean_col_lower or 'переходы в карточку' in col_lower:
            card_views_col = col
        
        # Ищем столбец "Заказ план"
        elif 'заказ план' in clean_col_lower or 'заказ план' in col_lower:
            orders_plan_col = col
        
        # Ищем столбец "Продажа план"
        elif 'продажа план' in clean_col_lower or 'продажа план' in col_lower:
            sales_plan_col = col
        
        # Ищем столбец "Отменили ВБ клуб, шт" (делаем последним)
        elif 'отменили' in clean_col_lower and 'вб клуб' in clean_col_lower and 'шт' in col_str:
            cancelled_wb_col = col
    
    
    # Анализируем данные
    if orders_col and sales_col:
        
        # Создаем простую таблицу
        st.subheader("📈 Сводная таблица")
        
        # Используем даты из Voronka.xlsx для группировки по неделям (приоритет)
        if date_col:
            try:
                # Безопасно конвертируем в datetime
                df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
                
                # Проверяем, что конвертация прошла успешно
                valid_dates = df[date_col].notna()
                if valid_dates.any():
                    # Создаем столбцы только для валидных дат
                    df.loc[valid_dates, 'Неделя'] = df.loc[valid_dates, date_col].dt.isocalendar().week
                    df.loc[valid_dates, 'Год'] = df.loc[valid_dates, date_col].dt.year
                    df.loc[valid_dates, 'Месяц'] = df.loc[valid_dates, date_col].dt.month
                    # Создаем уникальный формат дат для недель (избегаем дублирования)
                    # Используем ISO номер недели для уникальности
                    df.loc[valid_dates, 'Неделя_Год'] = (
                        df.loc[valid_dates, 'Год'].astype(int).astype(str) + '.' + 
                        df.loc[valid_dates, 'Месяц'].astype(int).astype(str) + 
                        ' (нед. ' + df.loc[valid_dates, 'Неделя'].astype(int).astype(str) + ')'
                    )
                    
                    # Дублирование недель будет устранено при группировке данных
                    # Создаем столбец для группировки по месяцам
                    df.loc[valid_dates, 'Месяц_Год'] = (
                        df.loc[valid_dates, 'Год'].astype(int).astype(str) + '.' + 
                        df.loc[valid_dates, 'Месяц'].astype(int).astype(str).str.zfill(2)
                    )
                    
                    # Для строк без валидных дат создаем простую группировку
                    invalid_mask = ~valid_dates
                    if invalid_mask.any():
                        df.loc[invalid_mask, 'Неделя_Год'] = 'Неделя ' + (df[invalid_mask].index + 1).astype(str)
                        df.loc[invalid_mask, 'Месяц_Год'] = 'Месяц ' + (df[invalid_mask].index + 1).astype(str)
                else:
                    # Создаем простую группировку по порядку
                    df['Неделя_Год'] = 'Неделя ' + (df.index + 1).astype(str)
                    df['Месяц_Год'] = 'Месяц ' + (df.index + 1).astype(str)
            except Exception as e:
                # Создаем простую группировку по порядку
                df['Неделя_Год'] = 'Неделя ' + (df.index + 1).astype(str)
                df['Месяц_Год'] = 'Месяц ' + (df.index + 1).astype(str)
        else:
            # Если нет дат в Voronka.xlsx, создаем простую группировку по порядку
            df['Неделя_Год'] = 'Неделя ' + (df.index + 1).astype(str)
            df['Месяц_Год'] = 'Месяц ' + (df.index + 1).astype(str)
        
        # Группируем по неделям - суммируем данные внутри недели, но неделя перезаписывается при загрузке нового файла
        agg_dict = {
            orders_col: 'sum',  # Суммируем внутри недели
            sales_col: 'sum'    # Суммируем внутри недели
        }
        
        # Добавляем все найденные столбцы
        if prodazha_col and pd.api.types.is_numeric_dtype(df[prodazha_col]):
            agg_dict[prodazha_col] = 'sum'  # Суммируем внутри недели
        if orders_sum_col and pd.api.types.is_numeric_dtype(df[orders_sum_col]):
            agg_dict[orders_sum_col] = 'sum'  # Суммируем все заказы за неделю
        if sales_sum_col and pd.api.types.is_numeric_dtype(df[sales_sum_col]):
            agg_dict[sales_sum_col] = 'sum'  # Суммируем внутри недели
        if conversion_col and pd.api.types.is_numeric_dtype(df[conversion_col]):
            agg_dict[conversion_col] = 'mean'  # Для процентов используем среднее
        if cart_conversion_col and pd.api.types.is_numeric_dtype(df[cart_conversion_col]):
            agg_dict[cart_conversion_col] = 'mean'  # Для процентов используем среднее
        if cancelled_col and pd.api.types.is_numeric_dtype(df[cancelled_col]):
            agg_dict[cancelled_col] = 'sum'  # Суммируем внутри недели
        if order_conversion_col and pd.api.types.is_numeric_dtype(df[order_conversion_col]):
            agg_dict[order_conversion_col] = 'mean'  # Для процентов используем среднее
        if card_views_col and pd.api.types.is_numeric_dtype(df[card_views_col]):
            agg_dict[card_views_col] = 'sum'  # Суммируем внутри недели
        if orders_plan_col and pd.api.types.is_numeric_dtype(df[orders_plan_col]):
            agg_dict[orders_plan_col] = 'sum'  # Суммируем планы заказов внутри недели
        if sales_plan_col and pd.api.types.is_numeric_dtype(df[sales_plan_col]):
            agg_dict[sales_plan_col] = 'sum'  # Суммируем планы продаж внутри недели
        # Убираем агрегацию для "Отменили" по запросу пользователя
        # if cancelled_wb_col and pd.api.types.is_numeric_dtype(df[cancelled_wb_col]):
        #     agg_dict[cancelled_wb_col] = 'sum'
        
        weekly_data = df.groupby('Неделя_Год').agg(agg_dict).reset_index()
        
        # Убрано временное исправление для 37 недели - проблема была в дублированных записях
        
        # Данные успешно обработаны и сгруппированы по неделям
        
        # Данные загружены и готовы к обработке
        
        # Сортируем недели по дате (от старых к новым - слева направо для плавного отображения)
        # Создаем временную колонку для сортировки по году, месяцу и неделе
        weekly_data['year'] = weekly_data['Неделя_Год'].str.extract(r'(\d{4})').astype(int)
        weekly_data['month'] = weekly_data['Неделя_Год'].str.extract(r'(\d{4})\.(\d+)')[1].astype(int)
        weekly_data['week'] = weekly_data['Неделя_Год'].str.extract(r'нед\. (\d+)').astype(int)
        weekly_data = weekly_data.sort_values(['year', 'month', 'week'], ascending=True).drop(['year', 'month', 'week'], axis=1)
        
        # Создаем сводную таблицу по неделям
        weekly_pivot_data = weekly_data.set_index('Неделя_Год').T
        
        # Создаем сводную таблицу по месяцам
        monthly_data = df.groupby('Месяц_Год').agg(agg_dict).reset_index()
        # Сортируем месяцы (от старых к новым для плавного отображения)
        monthly_data['year'] = monthly_data['Месяц_Год'].str.extract(r'(\d{4})').astype(int)
        monthly_data['month'] = monthly_data['Месяц_Год'].str.extract(r'(\d{4})\.(\d+)')[1].astype(int)
        monthly_data = monthly_data.sort_values(['year', 'month'], ascending=True).drop(['year', 'month'], axis=1)
        monthly_pivot_data = monthly_data.set_index('Месяц_Год').T
        
        # Создаем итоговую таблицу, начиная с недельных данных
        pivot_data = weekly_pivot_data.copy()
        
        # Добавляем столбец "Общие по месяцам"
        pivot_data["Общие по месяцам"] = 0.0
        
        # Добавляем месячные столбцы в pivot_data
        for col in monthly_pivot_data.columns:
            if col not in pivot_data.columns:
                pivot_data[col] = monthly_pivot_data[col]
            else:
                # Если столбец уже существует, обновляем его значения
                pivot_data[col] = monthly_pivot_data[col]
        
        # Добавляем недостающие месячные столбцы для 2025 года
        # Проверяем, какие месяцы уже есть в данных
        existing_2025_months = [col for col in pivot_data.columns if col.startswith("2025.") and '(' not in col]
        
        # Добавляем только те месяцы, которых действительно нет
        required_months = ['2025.9', '2025.10', '2025.11', '2025.12']
        for month in required_months:
            # Проверяем, есть ли этот месяц в разных форматах
            month_exists = False
            for existing_month in existing_2025_months:
                # Нормализуем оба формата для сравнения
                year1, month1 = month.split('.')
                year2, month2 = existing_month.split('.')
                normalized1 = f"{year1}.{month1.zfill(2)}"
                normalized2 = f"{year2}.{month2.zfill(2)}"
                if normalized1 == normalized2:
                    month_exists = True
                    break
            
            if not month_exists and month not in pivot_data.columns:
                # Создаем пустой столбец для недостающего месяца
                pivot_data[month] = 0.0
        
        # Добавляем недостающие недельные столбцы для месяцев 2025.09, 2025.10, 2025.11, 2025.12
        missing_weeks = [
            # Сентябрь 2025 (недели 39-40) - недели 39-40 имеют больше дней в сентябре
            '2025.9 (нед. 39)', '2025.9 (нед. 40)',
            # Октябрь 2025 (недели 41-44)
            '2025.10 (нед. 41)', '2025.10 (нед. 42)', '2025.10 (нед. 43)', '2025.10 (нед. 44)',
            # Ноябрь 2025 (недели 45-48)
            '2025.11 (нед. 45)', '2025.11 (нед. 46)', '2025.11 (нед. 47)', '2025.11 (нед. 48)',
            # Декабрь 2025 (недели 49-52)
            '2025.12 (нед. 49)', '2025.12 (нед. 50)', '2025.12 (нед. 51)', '2025.12 (нед. 52)'
        ]
        
        for week in missing_weeks:
            if week not in pivot_data.columns:
                pivot_data[week] = 0.0
                # st.write(f"🔧 Добавлен недостающий недельный столбец: {week}")  # Убрано по запросу пользователя
        
        # Переупорядочиваем столбцы: группируем недели по месяцам
        # Создаем новый порядок столбцов
        new_columns = []
        
        # Определяем порядок месяцев и их недель (неделя отдается месяцу с большим количеством дней)
        month_week_mapping = {
            '2025.07': ['2025.7 (нед. 27)', '2025.7 (нед. 28)', '2025.7 (нед. 29)', '2025.7 (нед. 30)', '2025.7 (нед. 31)'],
            '2025.08': ['2025.8 (нед. 31)', '2025.8 (нед. 32)', '2025.8 (нед. 33)', '2025.8 (нед. 34)', '2025.8 (нед. 35)'],
            '2025.09': ['2025.9 (нед. 36)', '2025.9 (нед. 37)', '2025.9 (нед. 38)', '2025.9 (нед. 39)', '2025.9 (нед. 40)'],  # Сентябрь - недели 39-40 имеют больше дней в сентябре
            '2025.10': ['2025.10 (нед. 41)', '2025.10 (нед. 42)', '2025.10 (нед. 43)', '2025.10 (нед. 44)'],  # Октябрь
            '2025.11': ['2025.11 (нед. 45)', '2025.11 (нед. 46)', '2025.11 (нед. 47)', '2025.11 (нед. 48)'],
            '2025.12': ['2025.12 (нед. 49)', '2025.12 (нед. 50)', '2025.12 (нед. 51)', '2025.12 (нед. 52)']
        }
        
        # Добавляем недели и месячные столбцы в правильном порядке
        for month, weeks in month_week_mapping.items():
            # Добавляем недели этого месяца
            for week in weeks:
                if week in pivot_data.columns:
                    new_columns.append(week)
            # Добавляем месячный столбец
            if month in pivot_data.columns:
                new_columns.append(month)
        
        # Добавляем остальные столбцы
        for col in pivot_data.columns:
            if col not in new_columns:
                new_columns.append(col)
        
        # Переупорядочиваем DataFrame
        pivot_data = pivot_data[new_columns]
        
        
        
        # Используем уже созданный правильный порядок столбцов
        final_columns = new_columns
        
        # Принудительно отключаем кеш для отладки
        cached_columns = None

        # Используем кешированный порядок столбцов или создаем новый
        if False and cached_columns and all(col in pivot_data.columns for col in cached_columns):
            # Проверяем, есть ли в кеше месячные столбцы
            monthly_cols_in_cache = [col for col in cached_columns if col.startswith(("2024.", "2023.", "2022.", "2025.")) and '(' not in col]
            monthly_cols_in_data = [col for col in pivot_data.columns if col.startswith(("2024.", "2023.", "2022.", "2025.")) and '(' not in col]
            
            if len(monthly_cols_in_cache) == len(monthly_cols_in_data):
                # Используем кешированный порядок
                final_columns = [col for col in cached_columns if col in pivot_data.columns]
                # Добавляем новые столбцы, которых не было в кеше
                for col in pivot_data.columns:
                    if col not in final_columns:
                        final_columns.append(col)
                # Удаляем дублирующиеся месячные столбцы в кешированной версии, но сохраняем их в правильных местах
                # Создаем новый final_columns без дублирующихся месячных столбцов
                new_final_columns = []
                seen_monthly_cols = set()
                
                for col in final_columns:
                    if col.startswith(("2024.", "2023.", "2022.", "2025.")) and '(' not in col:
                        # Это месячный столбец - проверяем на дублирование
                        year, month = col.split('.')
                        normalized = f"{year}.{month.zfill(2)}"
                        if normalized not in seen_monthly_cols:
                            new_final_columns.append(col)
                            seen_monthly_cols.add(normalized)
                    else:
                        # Это не месячный столбец - добавляем как есть
                        new_final_columns.append(col)
                
                final_columns = new_final_columns
                
            else:
                cached_columns = None  # Принудительно создаем новый порядок
        
        if not cached_columns or not all(col in pivot_data.columns for col in cached_columns):
            # Создаем новый порядок столбцов
            final_columns = []
            
            # Получаем уникальные месяцы из недельных данных
            weekly_months = set()
            for col in weekly_pivot_data.columns:
                if '(' in col and 'нед.' in col:
                    # Извлекаем месяц из формата "2024.01 (нед. 01)" или "2025.9 (нед. 38)"
                    month_part = col.split(' (')[0]  # "2024.01" или "2025.9"
                    # Унифицируем формат: добавляем ведущий ноль если нужно
                    year, month = month_part.split('.')
                    month_normalized = f"{year}.{month.zfill(2)}"
                    weekly_months.add(month_normalized)
            
            # Добавляем месяцы из monthly_pivot_data, которых может не быть в недельных данных
            for col in monthly_pivot_data.columns:
                # Унифицируем формат и для месячных столбцов
                year, month = col.split('.')
                month_normalized = f"{year}.{month.zfill(2)}"
                weekly_months.add(month_normalized)
            
            # Принудительно добавляем месяцы 2025.9, 2025.10, 2025.11, 2025.12 если их нет
            required_2025_months = ['2025.09', '2025.10', '2025.11', '2025.12']
            for month in required_2025_months:
                weekly_months.add(month)
            
            # Сортируем месяцы по возрастанию (сначала год, потом месяц)
            sorted_months = sorted(weekly_months, key=lambda x: (int(x.split('.')[0]), int(x.split('.')[1])))
            
            
            # Создаем правильный порядок столбцов: недели месяца, затем месячный столбец
            for month in sorted_months:
                # Добавляем недельные столбцы этого месяца
                month_weeks = []
                for col in pivot_data.columns:
                    if '(' in col and 'нед.' in col:
                        col_month_part = col.split(' (')[0]
                        # Унифицируем формат для сравнения
                        col_year, col_month = col_month_part.split('.')
                        col_month_normalized = f"{col_year}.{col_month.zfill(2)}"
                        
                        if col_month_normalized == month:
                            month_weeks.append(col)
                
                # Сортируем недели по возрастанию (слева направо)
                month_weeks.sort(key=lambda x: int(x.split('нед. ')[1].split(')')[0]), reverse=False)
                final_columns.extend(month_weeks)
                
                # Добавляем месячный столбец после недель этого месяца
                monthly_col = None
                for col in pivot_data.columns:
                    # Проверяем только месячные столбцы (содержат год.месяц без скобок)
                    if '(' not in col and '.' in col and col.startswith(("2024.", "2023.", "2022.", "2025.")) and col not in month_weeks:
                        col_year, col_month = col.split('.')
                        col_month_normalized = f"{col_year}.{col_month.zfill(2)}"
                        # Проверяем как нормализованный формат, так и оригинальный
                        if col_month_normalized == month or col == month:
                            monthly_col = col
                            break
                
                # Если не нашли месячный столбец, создаем его для месяцев 2025.9-2025.12
                if not monthly_col and month in ['2025.09', '2025.10', '2025.11', '2025.12']:
                    # Преобразуем нормализованный формат обратно в оригинальный
                    year, month_num = month.split('.')
                    original_month = f"{year}.{int(month_num)}"  # Убираем ведущий ноль
                    if original_month in pivot_data.columns:
                        monthly_col = original_month
                
                if monthly_col:
                    final_columns.append(monthly_col)
            
            
            
            # Добавляем столбец "Общие по месяцам" в конец
            final_columns.append("Общие по месяцам")
            
            
            # Убеждаемся, что все столбцы из pivot_data включены в final_columns
            # Но только те, которые не являются месячными (они уже добавлены в правильном порядке)
            for col in pivot_data.columns:
                if col not in final_columns and not (col.startswith(("2024.", "2023.", "2022.", "2025.")) and '(' not in col):
                    final_columns.append(col)
            
            # Удаляем дублирующиеся месячные столбцы, но сохраняем их в правильных местах
            # Создаем новый final_columns без дублирующихся месячных столбцов
            new_final_columns = []
            seen_monthly_cols = set()
            
            for col in final_columns:
                if col.startswith(("2024.", "2023.", "2022.", "2025.")) and '(' not in col:
                    # Это месячный столбец - проверяем на дублирование
                    year, month = col.split('.')
                    normalized = f"{year}.{month.zfill(2)}"
                    if normalized not in seen_monthly_cols:
                        new_final_columns.append(col)
                        seen_monthly_cols.add(normalized)
                else:
                    # Это не месячный столбец - добавляем как есть
                    new_final_columns.append(col)
            
            final_columns = new_final_columns
        
        # Добавляем будущие столбцы если включена опция
        if st.session_state.table_settings.get('show_future_dates', True):
            future_columns = generate_future_columns()
            
            # Добавляем будущие столбцы
            
            # Проверяем дублирование и добавляем только новые столбцы
            existing_columns = set(final_columns)
            new_future_columns = []
            for col in future_columns:
                if col not in existing_columns:
                    new_future_columns.append(col)
            
            if new_future_columns:
                # Добавляем только новые будущие столбцы в начало final_columns
                final_columns = new_future_columns + final_columns
            
            # Создаем пустые столбцы для будущих дат в pivot_data
            added_columns = []
            for col in new_future_columns:
                if col not in pivot_data.columns:
                    pivot_data[col] = 0.0
                    added_columns.append(col)
            
            # Столбцы добавлены в таблицу
        # Будущие столбцы отключены
        
        # Применяем скрытие недель, если настроено (перед переупорядочиванием)
        if 'hide_weeks_before' in st.session_state.table_settings:
            hide_weeks_before = st.session_state.table_settings['hide_weeks_before']
            
            # Фильтруем столбцы, скрывая недели до выбранной
            filtered_columns = []
            for col in final_columns:
                if "(" in col and "нед." in col:
                    try:
                        week_part = col.split("(нед.")[1].split(")")[0].strip()
                        week_num = int(week_part)
                        if week_num >= hide_weeks_before:
                            filtered_columns.append(col)
                    except (ValueError, IndexError):
                        # Если не удается распарсить номер недели, оставляем столбец
                        filtered_columns.append(col)
                else:
                    # Не недельные столбцы оставляем
                    filtered_columns.append(col)
            
            # Обновляем final_columns с отфильтрованными столбцами
            final_columns = filtered_columns
        
        # Сохраняем структуру таблицы в кеш
        save_table_structure_to_cache(pivot_data, final_columns)
        
        # Переупорядочиваем DataFrame
        pivot_data = pivot_data[final_columns]
        
        # Обновляем индексы для отображения и очищаем от лишнего текста
        index_names = []
        
        # Функция для очистки названий от лишнего текста
        def clean_column_name(name):
            if name:
                # Убираем "Детальный отчет воронки продаж по карточкам товаров" из любого места
                cleaned = str(name).replace('Детальный отчет воронки продаж по карточкам товаров', '').strip()
                # Убираем лишние пробелы и переносы строк
                cleaned = ' '.join(cleaned.split())
                # Убираем пустые значения
                if not cleaned or cleaned == 'nan' or cleaned == 'None':
                    return name
                # Если название начинается с пробела, убираем его
                if cleaned.startswith(' '):
                    cleaned = cleaned.lstrip()
                return cleaned
            return name
        
        # Очищаем все названия индексов в pivot_data
        cleaned_index = []
        for idx in pivot_data.index:
            cleaned_idx = clean_column_name(idx)
            cleaned_index.append(cleaned_idx)
        pivot_data.index = cleaned_index
        
        # Создаем список названий индексов в правильном порядке
        index_names = []
        
        if orders_col:
            index_names.append(clean_column_name(orders_col))
        
        if sales_col:
            index_names.append(clean_column_name(sales_col))
        
        if prodazha_col and pd.api.types.is_numeric_dtype(df[prodazha_col]):
            index_names.append(clean_column_name(prodazha_col))
        if orders_sum_col and pd.api.types.is_numeric_dtype(df[orders_sum_col]):
            index_names.append(clean_column_name(orders_sum_col))  # Очищаем название
        if sales_sum_col and pd.api.types.is_numeric_dtype(df[sales_sum_col]):
            index_names.append(clean_column_name(sales_sum_col))
        if conversion_col and pd.api.types.is_numeric_dtype(df[conversion_col]):
            index_names.append(clean_column_name(conversion_col))
        if cart_conversion_col and pd.api.types.is_numeric_dtype(df[cart_conversion_col]):
            index_names.append(clean_column_name(cart_conversion_col))
        if cancelled_col and pd.api.types.is_numeric_dtype(df[cancelled_col]):
            index_names.append(clean_column_name(cancelled_col))
        if order_conversion_col and pd.api.types.is_numeric_dtype(df[order_conversion_col]):
            index_names.append(clean_column_name(order_conversion_col))
        if card_views_col and pd.api.types.is_numeric_dtype(df[card_views_col]):
            index_names.append(clean_column_name(card_views_col))
        if orders_plan_col and pd.api.types.is_numeric_dtype(df[orders_plan_col]):
            index_names.append(clean_column_name(orders_plan_col))
        if sales_plan_col and pd.api.types.is_numeric_dtype(df[sales_plan_col]):
            index_names.append(clean_column_name(sales_plan_col))
        # Убираем строку "Отменили" по запросу пользователя
        # if cancelled_wb_col and pd.api.types.is_numeric_dtype(df[cancelled_wb_col]):
        #     index_names.append("Отменили, шт")
        
        # Добавляем названия для новых строк в правильном порядке (сначала базовые, потом зависимые)
        # Порядок: Средняя цена -> Реклама -> ДРР -> Заказ план -> Продажа план -> Рентабельность факт -> Рентабельность план -> Прибыль на ед. -> Прибыль
        index_names.extend(["Средняя цена", "Реклама", "ДРР", "Заказ план", "Продажа план", "Рентабельность факт", "Рентабельность план", "Прибыль на ед.", "Прибыль"])
        
        # Месячные данные уже добавлены в правильном порядке выше
        
        # Создаем пустые строки для дополнительных метрик
        additional_rows = []
        
        # Инициализируем session state для всех значений (без столбца "Общие по месяцам" и месячных столбцов)
        week_columns = [col for col in pivot_data.columns if col != "Общие по месяцам" and not (col.startswith(("2024.", "2023.", "2022.", "2025.")) and '(' not in col)]
        
        # Загружаем настройки из кеша при первом запуске
        if 'settings_loaded' not in st.session_state:
            load_settings_from_cache()
            st.session_state.settings_loaded = True
        
        if 'reklama_values' not in st.session_state:
            st.session_state.reklama_values = {week: 0.0 for week in week_columns}
        if 'orders_plan_values' not in st.session_state:
            st.session_state.orders_plan_values = {week: 0.0 for week in week_columns}
        if 'sales_plan_values' not in st.session_state:
            st.session_state.sales_plan_values = {week: 0.0 for week in week_columns}
        if 'rentabelnost_fact_values' not in st.session_state:
            st.session_state.rentabelnost_fact_values = {week: 0.0 for week in week_columns}
        if 'rentabelnost_plan_values' not in st.session_state:
            st.session_state.rentabelnost_plan_values = {week: 0.0 for week in week_columns}
        
        # Инициализация параметров расчета рентабельности
        if 'rentability_params' not in st.session_state:
            st.session_state.rentability_params = {
                'cost_price': 100.0,  # Себестоимость
                'discount_percent': 0.0,  # Скидка на сайте
                'commission_rate': 15.0,  # Комиссия WB
                'logistics_cost': 50.0,  # Логистика
                'advertising_percent': 0.0,  # Реклама
                'buyout_percent': 22.0,  # % выкупа
                'storage_cost': 0.0  # Хранение
            }
        
        # Сначала добавляем строку "Средняя цена" в основную таблицу
        avg_price_values = []
        for col in pivot_data.columns:
            if col == "Общие по месяцам":
                avg_price_values.append(0.0)  # Будет рассчитано позже
            else:
                # Ищем столбцы с заказами и суммой заказов
                orders_count_col = None
                orders_sum_col = None
                
                for existing_idx in pivot_data.index:
                    if "Заказали, шт" in existing_idx:
                        orders_count_col = existing_idx
                    elif "Заказали на сумму" in existing_idx:
                        orders_sum_col = existing_idx
                
                if orders_count_col and orders_sum_col:
                    try:
                        orders_count = pivot_data.loc[orders_count_col, col]
                        orders_sum = pivot_data.loc[orders_sum_col, col]
                        if pd.notna(orders_count) and pd.notna(orders_sum) and orders_count != 0:
                            avg_price = orders_sum / orders_count
                            avg_price_values.append(avg_price)
                        else:
                            avg_price_values.append(0.0)
                    except:
                        avg_price_values.append(0.0)
                else:
                    avg_price_values.append(0.0)
        
        # Добавляем строку "Средняя цена" в основную таблицу
        avg_price_row = pd.Series(avg_price_values, index=pivot_data.columns)
        avg_price_row.name = "Средняя цена"
        pivot_data = pd.concat([pivot_data, avg_price_row.to_frame().T])
        
        # Создаем строки в правильном порядке согласно index_names
        # Сначала создаем базовые строки, затем зависимые
        for idx_name in index_names:
            if idx_name == "Средняя цена":
                # Строка уже добавлена выше, пропускаем
                continue
            elif idx_name == "Реклама":
                # Загружаем значения из session state
                values = []
                for col in pivot_data.columns:
                    if col == "Общие по месяцам":
                        values.append(0.0)  # Будет рассчитано позже
                    elif col.startswith(("2024.", "2023.", "2022.", "2025.")) and '(' not in col:
                        # Месячные столбцы - рассчитываем сумму по неделям
                        month_weeks = [c for c in pivot_data.columns if c.startswith(col + ' (')]
                        reklama_total = sum(st.session_state.get('reklama_values', {}).get(week, 0.0) for week in month_weeks)
                        values.append(reklama_total)
                    else:
                        week_reklama = st.session_state.reklama_values.get(col, 0.0)
                        values.append(week_reklama)
                row = pd.Series(values, index=pivot_data.columns)
                row.name = "Реклама"
                additional_rows.append(row.to_frame().T)
            elif idx_name == "ДРР":
                # Рассчитываем ДРР для всех столбцов
                values = []
                # Проверяем наличие столбца для расчета ДРР
                if not orders_sum_col:
                    st.warning(f"⚠️ orders_sum_col не найден для расчета ДРР")
                
                for col in pivot_data.columns:
                    if col == "Общие по месяцам":
                        values.append(0.0)  # Будет рассчитано позже
                    elif col.startswith(("2024.", "2023.", "2022.", "2025.")) and '(' not in col:
                        # Месячные столбцы - среднее ДРР по неделям этого месяца
                        month_weeks = [c for c in pivot_data.columns if c.startswith(col + ' (')]
                        drr_values = []
                        for week_col in month_weeks:
                            reklama_value = st.session_state.get('reklama_values', {}).get(week_col, 0.0)
                            if orders_sum_col:
                                # Используем очищенное название столбца из индекса
                                orders_sum_col_clean = clean_column_name(orders_sum_col)
                                if orders_sum_col_clean in pivot_data.index:
                                    week_orders_sum = pivot_data.loc[orders_sum_col_clean, week_col]
                                    if pd.notna(week_orders_sum) and week_orders_sum > 0 and reklama_value > 0:
                                        drr_week_value = (reklama_value / week_orders_sum) * 100  # ДРР = (Реклама / Заказали на сумму) * 100%
                                        drr_values.append(drr_week_value)
                        if drr_values:
                            values.append(sum(drr_values) / len(drr_values))
                        else:
                            values.append(0.0)
                    else:
                        # Недельные столбцы
                        reklama_value = st.session_state.get('reklama_values', {}).get(col, 0.0)
                        if orders_sum_col:
                            # Используем очищенное название столбца из индекса
                            orders_sum_col_clean = clean_column_name(orders_sum_col)
                            if orders_sum_col_clean in pivot_data.index:
                                orders_sum_value = pivot_data.loc[orders_sum_col_clean, col]
                                if pd.notna(orders_sum_value) and orders_sum_value > 0 and reklama_value > 0:
                                    drr_value = (reklama_value / orders_sum_value) * 100  # ДРР = (Реклама / Заказали на сумму) * 100%
                                    values.append(drr_value)
                                else:
                                    values.append(0.0)
                            else:
                                values.append(0.0)
                        else:
                            values.append(0.0)
                row = pd.Series(values, index=pivot_data.columns)
                row.name = "ДРР"
                additional_rows.append(row.to_frame().T)
            elif idx_name == "Заказ план":
                # Сначала проверяем данные из исходного файла, потом из session state
                values = []
                for col in pivot_data.columns:
                    if col == "Общие по месяцам":
                        values.append(0.0)  # Будет рассчитано позже
                    elif col.startswith(("2024.", "2023.", "2022.", "2025.")) and '(' not in col:
                        # Месячные столбцы - рассчитываем сумму по неделям
                        month_weeks = [c for c in pivot_data.columns if c.startswith(col + ' (')]
                        orders_plan_total = 0.0
                        for week in month_weeks:
                            # Сначала проверяем данные из исходного файла
                            if orders_plan_col and week in pivot_data.index:
                                file_value = pivot_data.loc[week, orders_plan_col] if pd.notna(pivot_data.loc[week, orders_plan_col]) else 0.0
                                if file_value > 0:
                                    orders_plan_total += file_value
                                else:
                                    orders_plan_total += st.session_state.get('orders_plan_values', {}).get(week, 0.0)
                            else:
                                orders_plan_total += st.session_state.get('orders_plan_values', {}).get(week, 0.0)
                        values.append(orders_plan_total)
                    else:
                        # Сначала проверяем данные из исходного файла
                        if orders_plan_col and col in pivot_data.index:
                            file_value = pivot_data.loc[col, orders_plan_col] if pd.notna(pivot_data.loc[col, orders_plan_col]) else 0.0
                            if file_value > 0:
                                values.append(file_value)
                            else:
                                values.append(st.session_state.orders_plan_values.get(col, 0.0))
                        else:
                            values.append(st.session_state.orders_plan_values.get(col, 0.0))
                row = pd.Series(values, index=pivot_data.columns)
                row.name = "Заказ план"
                additional_rows.append(row.to_frame().T)
            elif idx_name == "Продажа план":
                # Сначала проверяем данные из исходного файла, потом рассчитываем как Заказ план × % выкупа
                values = []
                buyout_percent = st.session_state.rentability_params.get('buyout_percent', 22.0)
                
                for col in pivot_data.columns:
                    if col == "Общие по месяцам":
                        values.append(0.0)  # Будет рассчитано позже
                    elif col.startswith(("2024.", "2023.", "2022.", "2025.")) and '(' not in col:
                        # Месячные столбцы - рассчитываем сумму по неделям
                        month_weeks = [c for c in pivot_data.columns if c.startswith(col + ' (')]
                        sales_plan_total = 0.0
                        for week in month_weeks:
                            # Сначала проверяем данные из исходного файла
                            if sales_plan_col and week in pivot_data.index:
                                file_value = pivot_data.loc[week, sales_plan_col] if pd.notna(pivot_data.loc[week, sales_plan_col]) else 0.0
                                if file_value > 0:
                                    sales_plan_total += file_value
                                else:
                                    # Рассчитываем как Заказ план × % выкупа
                                    orders_plan = st.session_state.get('orders_plan_values', {}).get(week, 0.0)
                                    sales_plan = orders_plan * (buyout_percent / 100)
                                    sales_plan_total += sales_plan
                            else:
                                # Рассчитываем как Заказ план × % выкупа
                                orders_plan = st.session_state.get('orders_plan_values', {}).get(week, 0.0)
                                sales_plan = orders_plan * (buyout_percent / 100)
                                sales_plan_total += sales_plan
                        values.append(sales_plan_total)
                    else:
                        # Сначала проверяем данные из исходного файла
                        if sales_plan_col and col in pivot_data.index:
                            file_value = pivot_data.loc[col, sales_plan_col] if pd.notna(pivot_data.loc[col, sales_plan_col]) else 0.0
                            if file_value > 0:
                                values.append(file_value)
                            else:
                                # Рассчитываем как Заказ план × % выкупа
                                orders_plan = st.session_state.get('orders_plan_values', {}).get(col, 0.0)
                                sales_plan = orders_plan * (buyout_percent / 100)
                                values.append(sales_plan)
                        else:
                            # Рассчитываем как Заказ план × % выкупа
                            orders_plan = st.session_state.get('orders_plan_values', {}).get(col, 0.0)
                            sales_plan = orders_plan * (buyout_percent / 100)
                            values.append(sales_plan)
                
                row = pd.Series(values, index=pivot_data.columns)
                row.name = "Продажа план"
                additional_rows.append(row.to_frame().T)
            elif idx_name == "Рентабельность факт":
                # Сложный расчет рентабельности на основе средней цены
                values = []
                for col in pivot_data.columns:
                    if col == "Общие по месяцам":
                        values.append(0.0)  # Будет рассчитано позже
                    elif col.startswith(("2024.", "2023.", "2022.", "2025.")) and '(' not in col:
                        # Месячные столбцы - рассчитываем среднее по неделям
                        month_weeks = [c for c in pivot_data.columns if c.startswith(col + ' (')]
                        rentability_values = []
                        for week in month_weeks:
                            # Получаем среднюю цену для этой недели
                            avg_price = pivot_data.loc["Средняя цена", week] if "Средняя цена" in pivot_data.index else 0.0
                            if avg_price > 0:
                                # Сложный расчет рентабельности
                                # Используем ДРР (долю рекламных расходов) вместо абсолютной суммы рекламы
                                drr_value = 0.0
                                if "ДРР" in pivot_data.index:
                                    drr_value = pivot_data.loc["ДРР", week] if pd.notna(pivot_data.loc["ДРР", week]) else 0.0
                                advertising_percent = drr_value  # ДРР уже в процентах
                                
                                rentability = calculate_complex_rentability(
                                    average_price=avg_price,
                                    cost_price=st.session_state.rentability_params.get('cost_price', 100.0),
                                    discount_percent=st.session_state.rentability_params.get('discount_percent', 0.0),
                                    commission_rate=st.session_state.rentability_params.get('commission_rate', 15.0),
                                    logistics_cost=st.session_state.rentability_params.get('logistics_cost', 50.0),
                                    advertising_percent=advertising_percent,
                                    buyout_percent=st.session_state.rentability_params.get('buyout_percent', 22.0),
                                    storage_cost=st.session_state.rentability_params.get('storage_cost', 0.0),
                                    spp_discount=st.session_state.rentability_params.get('spp_discount', 25.0)
                                )
                                rentability_values.append(rentability)
                        
                        if rentability_values:
                            values.append(sum(rentability_values) / len(rentability_values))
                        else:
                            values.append(0.0)
                    else:
                        # Недельные столбцы - рассчитываем рентабельность на основе средней цены
                        avg_price = pivot_data.loc["Средняя цена", col] if "Средняя цена" in pivot_data.index else 0.0
                        if avg_price > 0:
                            # Используем ДРР (долю рекламных расходов) вместо абсолютной суммы рекламы
                            # ДРР уже рассчитан в строке "ДРР" таблицы
                            drr_value = 0.0
                            if "ДРР" in pivot_data.index:
                                drr_value = pivot_data.loc["ДРР", col] if pd.notna(pivot_data.loc["ДРР", col]) else 0.0
                            advertising_percent = drr_value  # ДРР уже в процентах
                            
                            rentability = calculate_complex_rentability(
                                average_price=avg_price,
                                cost_price=st.session_state.rentability_params.get('cost_price', 100.0),
                                discount_percent=st.session_state.rentability_params.get('discount_percent', 0.0),
                                commission_rate=st.session_state.rentability_params.get('commission_rate', 15.0),
                                logistics_cost=st.session_state.rentability_params.get('logistics_cost', 50.0),
                                advertising_percent=advertising_percent,
                                buyout_percent=st.session_state.rentability_params.get('buyout_percent', 22.0),
                                storage_cost=st.session_state.rentability_params.get('storage_cost', 0.0),
                                spp_discount=st.session_state.rentability_params.get('spp_discount', 25.0)
                            )
                            values.append(rentability)
                        else:
                            values.append(0.0)
                row = pd.Series(values, index=pivot_data.columns)
                row.name = "Рентабельность факт"
                additional_rows.append(row.to_frame().T)
            elif idx_name == "Рентабельность план":
                # Загружаем значения из session state (аналогично План заказов)
                values = []
                
                for col in pivot_data.columns:
                    if col == "Общие по месяцам":
                        values.append(0.0)  # Будет рассчитано позже
                    elif col.startswith(("2024.", "2023.", "2022.", "2025.")) and '(' not in col:
                        # Месячные столбцы - рассчитываем среднее по неделям
                        month_weeks = [c for c in pivot_data.columns if c.startswith(col + ' (')]
                        rentability_plan_total = 0.0
                        for week in month_weeks:
                            rentability_plan_total += st.session_state.rentability_plan_values.get(week, 0.0)
                        if len(month_weeks) > 0:
                            rentability_plan_avg = rentability_plan_total / len(month_weeks)
                        else:
                            rentability_plan_avg = 0.0
                        values.append(rentability_plan_avg)
                    else:
                        # Для недельных столбцов - берем значения из session state
                        value = st.session_state.rentability_plan_values.get(col, 0.0)
                        values.append(value)
                
                row = pd.Series(values, index=pivot_data.columns)
                row.name = "Рентабельность план"
                additional_rows.append(row.to_frame().T)
            elif idx_name == "Прибыль на ед.":
                # Создаем строку "Прибыль на ед." здесь, чтобы она была доступна для расчета общей прибыли
                profit_per_unit_values = []
                for col in pivot_data.columns:
                    if col == "Общие по месяцам":
                        # Рассчитываем среднюю прибыль на единицу по всем недельным столбцам
                        total_profit_per_unit = 0.0
                        count = 0
                        for week_col in pivot_data.columns:
                            if week_col != "Общие по месяцам" and not (week_col.startswith(("2024.", "2023.", "2022.", "2025.")) and '(' not in week_col):
                                if "Средняя цена" in pivot_data.index:
                                    avg_price = pivot_data.loc["Средняя цена", week_col] if pd.notna(pivot_data.loc["Средняя цена", week_col]) else 0.0
                                else:
                                    avg_price = 0.0
                                if avg_price > 0:
                                    drr_value = 0.0
                                    if "ДРР" in pivot_data.index:
                                        drr_value = pivot_data.loc["ДРР", week_col] if pd.notna(pivot_data.loc["ДРР", week_col]) else 0.0
                                    advertising_percent = drr_value
                                    
                                    # Получаем параметры рентабельности
                                    cost_price = st.session_state.rentability_params.get('cost_price', 100.0)
                                    commission_rate = st.session_state.rentability_params.get('commission_rate', 15.0)
                                    logistics_cost = st.session_state.rentability_params.get('logistics_cost', 50.0)
                                    buyout_percent = st.session_state.rentability_params.get('buyout_percent', 22.0)
                                    storage_cost = st.session_state.rentability_params.get('storage_cost', 0.0)
                                    spp_discount = st.session_state.rentability_params.get('spp_discount', 25.0)
                                    
                                    profit_per_unit = calculate_profit_per_unit(
                                        average_price=avg_price,
                                        cost_price=cost_price,
                                        discount_percent=0.0,
                                        commission_rate=commission_rate,
                                        logistics_cost=logistics_cost,
                                        advertising_percent=advertising_percent,
                                        buyout_percent=buyout_percent,
                                        storage_cost=storage_cost,
                                        spp_discount=spp_discount
                                    )
                                    if profit_per_unit == 0.0 and avg_price > 0:
                                        commission_amount = avg_price * (commission_rate / 100)
                                        advertising_cost = avg_price * (advertising_percent / 100)
                                        delivery_cost = logistics_cost
                                        profit_per_unit = avg_price - cost_price - commission_amount - advertising_cost - delivery_cost - storage_cost
                                    
                                    
                                    # Отладочная информация для отрицательных значений
                                    if profit_per_unit < 0:
                                        st.warning(f"⚠️ Отрицательная прибыль на ед. для {week}: {profit_per_unit:.2f} (цена: {avg_price:.2f}, себестоимость: {cost_price:.2f}, реклама: {advertising_percent:.2f}%)")
                                    
                                    total_profit_per_unit += profit_per_unit
                                    count += 1
                        if count > 0:
                            profit_per_unit_values.append(total_profit_per_unit / count)
                        else:
                            profit_per_unit_values.append(0.0)
                    elif col.startswith(("2024.", "2023.", "2022.", "2025.")) and '(' not in col:
                        # Месячные столбцы - рассчитываем среднее по неделям
                        # Нормализуем формат месяца (2025.08 -> 2025.8)
                        if '.' in col:
                            year, month = col.split('.')
                            normalized_month = f"{year}.{int(month)}"
                        else:
                            normalized_month = col
                        
                        month_weeks = [c for c in pivot_data.columns if c.startswith(normalized_month + ' (')]
                        profit_values = []
                        # Используем уже рассчитанные значения из pivot_data
                        for week in month_weeks:
                            if week in pivot_data.columns and "Прибыль на ед." in pivot_data.index:
                                profit_per_unit = pivot_data.loc["Прибыль на ед.", week] if pd.notna(pivot_data.loc["Прибыль на ед.", week]) else 0.0
                                profit_values.append(profit_per_unit)
                        if profit_values:
                            profit_per_unit_values.append(sum(profit_values) / len(profit_values))
                        else:
                            profit_per_unit_values.append(0.0)
                    else:
                        # Для недельных столбцов
                        if "Средняя цена" in pivot_data.index:
                            avg_price = pivot_data.loc["Средняя цена", col] if pd.notna(pivot_data.loc["Средняя цена", col]) else 0.0
                        else:
                            avg_price = 0.0
                        
                        
                        
                        if avg_price > 0:
                            drr_value = 0.0
                            if "ДРР" in pivot_data.index:
                                drr_value = pivot_data.loc["ДРР", col] if pd.notna(pivot_data.loc["ДРР", col]) else 0.0
                            advertising_percent = drr_value  # ДРР уже в процентах
                            
                            # Получаем параметры рентабельности
                            cost_price = st.session_state.rentability_params.get('cost_price', 100.0)
                            commission_rate = st.session_state.rentability_params.get('commission_rate', 15.0)
                            logistics_cost = st.session_state.rentability_params.get('logistics_cost', 50.0)
                            buyout_percent = st.session_state.rentability_params.get('buyout_percent', 22.0)
                            storage_cost = st.session_state.rentability_params.get('storage_cost', 0.0)
                            spp_discount = st.session_state.rentability_params.get('spp_discount', 25.0)
                            
                            profit_per_unit = calculate_profit_per_unit(
                                average_price=avg_price,
                                cost_price=cost_price,
                                discount_percent=0.0,
                                commission_rate=commission_rate,
                                logistics_cost=logistics_cost,
                                advertising_percent=advertising_percent,
                                buyout_percent=buyout_percent,
                                storage_cost=storage_cost,
                                spp_discount=spp_discount
                            )
                            # Если прибыль на единицу равна 0, попробуем простой расчет
                            if profit_per_unit == 0.0 and avg_price > 0:
                                # Простой расчет: цена - себестоимость - комиссия - логистика - реклама
                                commission_amount = avg_price * (commission_rate / 100)
                                advertising_cost = avg_price * (advertising_percent / 100)
                                delivery_cost = logistics_cost
                                profit_per_unit = avg_price - cost_price - commission_amount - advertising_cost - delivery_cost - storage_cost
                            
                            profit_per_unit_values.append(profit_per_unit)
                        else:
                            profit_per_unit_values.append(0.0)
                
                # Создаем строку "Прибыль на ед."
                profit_per_unit_row = pd.Series(profit_per_unit_values, index=pivot_data.columns)
                profit_per_unit_row.name = "Прибыль на ед."
                additional_rows.append(profit_per_unit_row.to_frame().T)
                
                # Сохраняем данные для расчета общей прибыли
                st.session_state.profit_per_unit_data = profit_per_unit_row
                
                # СРАЗУ добавляем в pivot_data для корректного расчета общей прибыли
                pivot_data = pd.concat([pivot_data, profit_per_unit_row.to_frame().T])
                
            elif idx_name == "Прибыль":
                # Расчет общей прибыли: Прибыль на ед. * Выкупили, шт
                values = []
                # Получаем данные прибыли на единицу из session_state
                profit_per_unit_data = st.session_state.get('profit_per_unit_data', None)
                
                
                for col in pivot_data.columns:
                    if col == "Общие по месяцам":
                        # Рассчитываем общую прибыль по всем недельным столбцам
                        total_profit = 0.0
                        for week_col in pivot_data.columns:
                            if week_col != "Общие по месяцам" and not (week_col.startswith(("2024.", "2023.", "2022.", "2025.")) and '(' not in week_col):
                                # Получаем прибыль на единицу из pivot_data (уже рассчитанную)
                                if "Прибыль на ед." in pivot_data.index:
                                    profit_per_unit = pivot_data.loc["Прибыль на ед.", week_col] if pd.notna(pivot_data.loc["Прибыль на ед.", week_col]) else 0.0
                                else:
                                    profit_per_unit = 0.0
                                if "Выкупили, шт" in pivot_data.index:
                                    sales_count = pivot_data.loc["Выкупили, шт", week_col] if pd.notna(pivot_data.loc["Выкупили, шт", week_col]) else 0.0
                                else:
                                    sales_count = 0.0
                                profit_contribution = profit_per_unit * sales_count
                                total_profit += profit_contribution
                        values.append(total_profit)
                    elif col.startswith(("2024.", "2023.", "2022.", "2025.")) and '(' not in col:
                        # Месячные столбцы - рассчитываем сумму по неделям
                        # Нормализуем формат месяца (2025.08 -> 2025.8)
                        if '.' in col:
                            year, month = col.split('.')
                            normalized_month = f"{year}.{int(month)}"
                        else:
                            normalized_month = col
                        
                        month_weeks = [c for c in pivot_data.columns if c.startswith(normalized_month + ' (')]
                        profit_total = 0.0
                        for week in month_weeks:
                            if week in pivot_data.columns:
                                # Получаем прибыль на единицу из pivot_data (уже рассчитанную)
                                if "Прибыль на ед." in pivot_data.index:
                                    profit_per_unit = pivot_data.loc["Прибыль на ед.", week] if pd.notna(pivot_data.loc["Прибыль на ед.", week]) else 0.0
                                else:
                                    profit_per_unit = 0.0
                                if "Выкупили, шт" in pivot_data.index:
                                    sales_count = pivot_data.loc["Выкупили, шт", week] if pd.notna(pivot_data.loc["Выкупили, шт", week]) else 0.0
                                else:
                                    sales_count = 0.0
                                profit_contribution = profit_per_unit * sales_count
                                profit_total += profit_contribution
                        values.append(profit_total)
                    else:
                        # Для недельных столбцов
                        # Получаем прибыль на единицу из pivot_data (уже рассчитанную)
                        if "Прибыль на ед." in pivot_data.index:
                            profit_per_unit = pivot_data.loc["Прибыль на ед.", col] if pd.notna(pivot_data.loc["Прибыль на ед.", col]) else 0.0
                        else:
                            profit_per_unit = 0.0
                        if "Выкупили, шт" in pivot_data.index:
                            sales_count = pivot_data.loc["Выкупили, шт", col] if pd.notna(pivot_data.loc["Выкупили, шт", col]) else 0.0
                        else:
                            sales_count = 0.0
                        
                        total_profit = profit_per_unit * sales_count
                        values.append(total_profit)
                
                # Проверяем наличие данных для общей прибыли
                if not any(values):
                    st.warning("⚠️ Нет данных для расчета общей прибыли. Убедитесь, что загружены данные с продажами.")
                else:
                    # Показываем пример расчета общей прибыли
                    first_col_with_profit = None
                    for col in pivot_data.columns:
                        if col != "Общие по месяцам" and not col.startswith(("2024.", "2023.", "2022.", "2025.")) or '(' in col:
                            if "Прибыль на ед." in pivot_data.index and "Выкупили, шт" in pivot_data.index:
                                profit_per_unit = pivot_data.loc["Прибыль на ед.", col] if pd.notna(pivot_data.loc["Прибыль на ед.", col]) else 0.0
                                sales_count = pivot_data.loc["Выкупили, шт", col] if pd.notna(pivot_data.loc["Выкупили, шт", col]) else 0.0
                                if profit_per_unit > 0 and sales_count > 0:
                                    first_col_with_profit = col
                                    break
                    
                    if first_col_with_profit:
                        profit_per_unit = pivot_data.loc["Прибыль на ед.", first_col_with_profit]
                        sales_count = pivot_data.loc["Выкупили, шт", first_col_with_profit]
                        total_profit = profit_per_unit * sales_count
                
                row = pd.Series(values, index=pivot_data.columns)
                row.name = "Прибыль"
                additional_rows.append(row.to_frame().T)
        
        
        # Добавляем строки в таблицу в правильном порядке (кроме "Прибыль на ед.", которая уже добавлена)
        if additional_rows:
            # Фильтруем строки, которые уже добавлены в pivot_data
            filtered_additional_rows = []
            for row in additional_rows:
                if row.index[0] != "Прибыль на ед.":
                    filtered_additional_rows.append(row)
            if filtered_additional_rows:
                # Удаляем старую строку "Реклама" если она есть
                if "Реклама" in pivot_data.index:
                    pivot_data = pivot_data.drop("Реклама")
                pivot_data = pd.concat([pivot_data] + filtered_additional_rows)
        
        # НЕ устанавливаем индексы, чтобы избежать перестановки строк!
        # Оставляем оригинальные названия строк
        
        # Перезаписываем месячные значения для строк "Реклама", "Заказ план", "Продажа план"
        for col in pivot_data.columns:
            if col.startswith(("2024.", "2023.", "2022.", "2025.")) and '(' not in col:
                # Ищем недели для этого месяца, учитывая разные форматы (2025.09 и 2025.9)
                month_weeks = []
                for week_col in pivot_data.columns:
                    if '(' in week_col and 'нед.' in week_col:
                        # Извлекаем год и месяц из недели (например, "2025.9" из "2025.9 (нед. 38)")
                        week_year_month = week_col.split(' (')[0]
                        # Нормализуем формат месяца (2025.9 -> 2025.09)
                        if '.' in week_year_month:
                            year, month = week_year_month.split('.')
                            normalized_week_month = f"{year}.{month.zfill(2)}"
                            if normalized_week_month == col:
                                month_weeks.append(week_col)
                
                # Средняя цена - среднее по неделям
                if "Средняя цена" in pivot_data.index:
                    avg_price_values = []
                    for week in month_weeks:
                        avg_price = pivot_data.loc["Средняя цена", week] if "Средняя цена" in pivot_data.index else 0.0
                        if avg_price > 0:
                            avg_price_values.append(avg_price)
                    
                    if avg_price_values:
                        avg_price_avg = sum(avg_price_values) / len(avg_price_values)
                    else:
                        avg_price_avg = 0.0
                    pivot_data.loc["Средняя цена", col] = avg_price_avg
                
                # Реклама - сумма по неделям (ТОЛЬКО для месячных столбцов, НЕ для недельных!)
                if "Реклама" in pivot_data.index and col.endswith(('.09', '.08', '.07', '.10', '.11', '.12')):
                    reklama_total = sum(st.session_state.get('reklama_values', {}).get(week, 0.0) for week in month_weeks)
                    pivot_data.loc["Реклама", col] = reklama_total
                
                # Заказ план - сумма по неделям (сначала из файла, потом из session state)
                if "Заказ план" in pivot_data.index:
                    orders_plan_total = 0.0
                    for week in month_weeks:
                        # Сначала проверяем данные из исходного файла
                        if orders_plan_col and week in pivot_data.index:
                            file_value = pivot_data.loc[week, orders_plan_col] if pd.notna(pivot_data.loc[week, orders_plan_col]) else 0.0
                            if file_value > 0:
                                orders_plan_total += file_value
                            else:
                                orders_plan_total += st.session_state.get('orders_plan_values', {}).get(week, 0.0)
                        else:
                            orders_plan_total += st.session_state.get('orders_plan_values', {}).get(week, 0.0)
                    pivot_data.loc["Заказ план", col] = orders_plan_total
                
                # Продажа план - сначала из файла, потом рассчитываем как Заказ план × % выкупа
                if "Продажа план" in pivot_data.index:
                    buyout_percent = st.session_state.rentability_params.get('buyout_percent', 22.0)
                    sales_plan_total = 0.0
                    for week in month_weeks:
                        # Сначала проверяем данные из исходного файла
                        if sales_plan_col and week in pivot_data.index:
                            file_value = pivot_data.loc[week, sales_plan_col] if pd.notna(pivot_data.loc[week, sales_plan_col]) else 0.0
                            if file_value > 0:
                                sales_plan_total += file_value
                            else:
                                # Рассчитываем как Заказ план × % выкупа
                                orders_plan = st.session_state.get('orders_plan_values', {}).get(week, 0.0)
                                sales_plan = orders_plan * (buyout_percent / 100)
                                sales_plan_total += sales_plan
                        else:
                            # Рассчитываем как Заказ план × % выкупа
                            orders_plan = st.session_state.get('orders_plan_values', {}).get(week, 0.0)
                            sales_plan = orders_plan * (buyout_percent / 100)
                            sales_plan_total += sales_plan
                    pivot_data.loc["Продажа план", col] = sales_plan_total
                
                # Рентабельность факт - среднее по неделям (пересчитываем на основе средней цены)
                if "Рентабельность факт" in pivot_data.index:
                    rentability_values = []
                    for week in month_weeks:
                        # Получаем среднюю цену для этой недели
                        avg_price = pivot_data.loc["Средняя цена", week] if "Средняя цена" in pivot_data.index else 0.0
                        if avg_price > 0:
                            # Сложный расчет рентабельности
                            # Используем ДРР (долю рекламных расходов) вместо абсолютной суммы рекламы
                            drr_value = 0.0
                            if "ДРР" in pivot_data.index:
                                drr_value = pivot_data.loc["ДРР", week] if pd.notna(pivot_data.loc["ДРР", week]) else 0.0
                            advertising_percent = drr_value  # ДРР уже в процентах
                            
                            rentability = calculate_complex_rentability(
                                average_price=avg_price,
                                cost_price=st.session_state.rentability_params.get('cost_price', 100.0),
                                discount_percent=st.session_state.rentability_params.get('discount_percent', 0.0),
                                commission_rate=st.session_state.rentability_params.get('commission_rate', 15.0),
                                logistics_cost=st.session_state.rentability_params.get('logistics_cost', 50.0),
                                advertising_percent=advertising_percent,
                                buyout_percent=st.session_state.rentability_params.get('buyout_percent', 22.0),
                                storage_cost=st.session_state.rentability_params.get('storage_cost', 0.0),
                                spp_discount=st.session_state.rentability_params.get('spp_discount', 25.0)
                            )
                            rentability_values.append(rentability)
                    
                    if rentability_values:
                        rentabelnost_fact_avg = sum(rentability_values) / len(rentability_values)
                    else:
                        rentabelnost_fact_avg = 0.0
                    pivot_data.loc["Рентабельность факт", col] = rentabelnost_fact_avg
                
                # Прибыль на ед. - среднее по неделям
                if "Прибыль на ед." in pivot_data.index:
                    profit_values = []
                    for week in month_weeks:
                        if week in pivot_data.columns:
                            avg_price = pivot_data.loc["Средняя цена", week] if pd.notna(pivot_data.loc["Средняя цена", week]) else 0.0
                            if avg_price > 0:
                                drr_value = 0.0
                                if "ДРР" in pivot_data.index:
                                    drr_value = pivot_data.loc["ДРР", week] if pd.notna(pivot_data.loc["ДРР", week]) else 0.0
                                advertising_percent = drr_value  # ДРР уже в процентах
                                
                                profit_per_unit = calculate_profit_per_unit(
                                    average_price=avg_price,
                                    cost_price=st.session_state.rentability_params.get('cost_price', 100.0),
                                    discount_percent=st.session_state.rentability_params.get('discount_percent', 0.0),
                                    commission_rate=st.session_state.rentability_params.get('commission_rate', 15.0),
                                    logistics_cost=st.session_state.rentability_params.get('logistics_cost', 50.0),
                                    advertising_percent=advertising_percent,
                                    buyout_percent=st.session_state.rentability_params.get('buyout_percent', 22.0),
                                    storage_cost=st.session_state.rentability_params.get('storage_cost', 0.0),
                                    spp_discount=st.session_state.rentability_params.get('spp_discount', 25.0)
                                )
                                profit_values.append(profit_per_unit)
                    
                    if profit_values:
                        profit_avg = sum(profit_values) / len(profit_values)
                    else:
                        profit_avg = 0.0
                    pivot_data.loc["Прибыль на ед.", col] = profit_avg
                
                # Рентабельность план - среднее по неделям (аналогично План заказов)
                if "Рентабельность план" in pivot_data.index:
                    rentability_plan_total = 0.0
                    for week in month_weeks:
                        rentability_plan_total += st.session_state.rentability_plan_values.get(week, 0.0)
                    if len(month_weeks) > 0:
                        rentability_plan_avg = rentability_plan_total / len(month_weeks)
                    else:
                        rentability_plan_avg = 0.0
                    pivot_data.loc["Рентабельность план", col] = rentability_plan_avg
                
                # ДРР - среднее по неделям этого месяца
                if "ДРР" in pivot_data.index and orders_sum_col:
                    # Используем очищенное название столбца из индекса
                    orders_sum_col_clean = clean_column_name(orders_sum_col)
                    if orders_sum_col_clean in pivot_data.index:
                        drr_values = []
                        for week_col in month_weeks:
                            reklama_value = st.session_state.get('reklama_values', {}).get(week_col, 0.0)
                            week_orders_sum = pivot_data.loc[orders_sum_col_clean, week_col]
                            if pd.notna(week_orders_sum) and week_orders_sum > 0 and reklama_value > 0:
                                drr_values.append((reklama_value / week_orders_sum) * 100)  # ДРР = (Реклама / Заказали на сумму) * 100%
                        if drr_values:
                            pivot_data.loc["ДРР", col] = sum(drr_values) / len(drr_values)
                        else:
                            pivot_data.loc["ДРР", col] = 0.0
        
        # Рассчитываем среднюю цену: Заказали на сумму / Заказали шт
        if orders_col and orders_sum_col:
            orders_col_clean = clean_column_name(orders_col)
            orders_sum_col_clean = clean_column_name(orders_sum_col)
            if orders_col_clean in pivot_data.index and orders_sum_col_clean in pivot_data.index:
                for col in pivot_data.columns:
                    try:
                        orders_count = pivot_data.loc[orders_col_clean, col]
                        orders_sum = pivot_data.loc[orders_sum_col_clean, col]
                        if pd.notna(orders_count) and pd.notna(orders_sum) and orders_count != 0:
                            avg_price = orders_sum / orders_count
                            pivot_data.loc["Средняя цена", col] = avg_price
                        else:
                            pivot_data.loc["Средняя цена", col] = 0
                    except:
                        pivot_data.loc["Средняя цена", col] = 0
        
        # ДРР уже рассчитан выше при создании строки
        
        # Рассчитываем общие значения по месяцам для каждой строки
        for idx in pivot_data.index:
            if idx == "ДРР":
                # Для ДРР - среднее арифметическое по месяцам
                values = []
                for col in monthly_pivot_data.columns:
                    if col in pivot_data.columns:
                        val = pivot_data.loc[idx, col]
                        # Проверяем, что val не является Series и не равен 0
                        try:
                            # Пытаемся получить скалярное значение
                            if hasattr(val, 'iloc'):
                                # Если это Series, берем первое значение
                                val_scalar = val.iloc[0] if len(val) > 0 else 0
                            else:
                                val_scalar = val
                            
                            if pd.notna(val_scalar) and val_scalar != 0:
                                values.append(val_scalar)
                        except:
                            # Если что-то пошло не так, пропускаем
                            pass
                if values:
                    pivot_data.loc[idx, "Общие по месяцам"] = sum(values) / len(values)
            elif idx == "Реклама":
                # Для рекламы - сумма по неделям
                total = 0
                for col in pivot_data.columns:
                    if col not in ["Общие по месяцам"] and not (col.startswith(("2024.", "2023.", "2022.", "2025.")) and '(' not in col):
                        val = pivot_data.loc[idx, col]
                        if pd.notna(val):
                            total += val
                pivot_data.loc[idx, "Общие по месяцам"] = total
            elif idx in ["Заказ план", "Продажа план"]:
                # Для планов - сумма по неделям
                total = 0
                for col in pivot_data.columns:
                    if col not in ["Общие по месяцам"] and not (col.startswith(("2024.", "2023.", "2022.", "2025.")) and '(' not in col):
                        val = pivot_data.loc[idx, col]
                        if pd.notna(val):
                            total += val
                pivot_data.loc[idx, "Общие по месяцам"] = total
            elif idx == "Прибыль":
                # Для прибыли - сумма по неделям
                total = 0
                for col in pivot_data.columns:
                    if col not in ["Общие по месяцам"] and not (col.startswith(("2024.", "2023.", "2022.", "2025.")) and '(' not in col):
                        val = pivot_data.loc[idx, col]
                        if pd.notna(val):
                            total += val
                pivot_data.loc[idx, "Общие по месяцам"] = total
            elif idx in ["Средняя цена", "Процент выкупа", "Конверсия в корзину, %", "Конверсия в заказ, %", "Рентабельность факт", "Рентабельность план", "Прибыль на ед."]:
                # Для процентных показателей - среднее арифметическое по месяцам
                values = []
                for col in monthly_pivot_data.columns:
                    if col in pivot_data.columns:
                        val = pivot_data.loc[idx, col]
                        # Проверяем, что val не является Series и не равен 0
                        try:
                            # Пытаемся получить скалярное значение
                            if hasattr(val, 'iloc'):
                                # Если это Series, берем первое значение
                                val_scalar = val.iloc[0] if len(val) > 0 else 0
                            else:
                                val_scalar = val
                            
                            if pd.notna(val_scalar) and val_scalar != 0:
                                values.append(val_scalar)
                        except:
                            # Если что-то пошло не так, пропускаем
                            pass
                if values:
                    pivot_data.loc[idx, "Общие по месяцам"] = sum(values) / len(values)
            else:
                # Для количественных показателей - сумма по месяцам
                total = 0
                for col in monthly_pivot_data.columns:
                    if col in pivot_data.columns:
                        val = pivot_data.loc[idx, col]
                        if pd.notna(val):
                            total += val
                pivot_data.loc[idx, "Общие по месяцам"] = total
        
        # Форматируем числа для лучшей читабельности
        def format_number(value):
            try:
                if pd.isna(value) or value is None or value == '0' or value == '0.0':
                    return '0'
                # Преобразуем в число, если это строка
                if isinstance(value, str):
                    # Убираем форматирование (пробелы, запятые)
                    value = float(value.replace(' ', '').replace(',', ''))
                else:
                    value = float(value)
                
                if value >= 1000000:  # Миллионы
                    return f'{int(value):,}'.replace(',', ' ')
                elif value >= 1000:  # Тысячи
                    return f'{int(value):,}'.replace(',', ' ')
                elif value == int(value):  # Целое число
                    return f'{int(value):,}'.replace(',', ' ')
                else:  # Дробное число
                    return f'{value:,.2f}'.replace(',', ' ')
            except:
                return str(value)
        
        
        # Применяем форматирование к числовым данным
        # Создаем отдельный DataFrame для форматированного отображения с правильным порядком столбцов
        formatted_data = pivot_data[final_columns].copy().astype(str)
        
        for col in formatted_data.columns:
            for idx in formatted_data.index:
                if idx not in ['Реклама', 'ДРР', 'Средняя цена', 'Заказ план', 'Продажа план', 'Процент выкупа', 'Прибыль на ед.', 'Конверсия в корзину, %', 'Конверсия в заказ, %', 'Рентабельность факт', 'Рентабельность план', 'Прибыль'] and 'Заказали на сумму' not in idx and 'Выкупили на сумму' not in idx:  # Не форматируем эти строки
                    formatted_data.loc[idx, col] = format_number(formatted_data.loc[idx, col])
                elif idx == 'ДРР':  # Для ДРР используем специальное форматирование с процентами
                    # Получаем исходное значение из pivot_data
                    original_value = pivot_data.loc[idx, col]
                    if pd.notna(original_value) and original_value != 0:
                        # Проверяем, не является ли это значением рекламы (слишком большое для ДРР)
                        if original_value > 100:
                            # Исправляем: рассчитываем правильный ДРР для всех недель
                            reklama_value = st.session_state.get('reklama_values', {}).get(col, 0.0)
                            orders_sum_col_clean = clean_column_name(orders_sum_col) if orders_sum_col else None
                            if orders_sum_col_clean and orders_sum_col_clean in pivot_data.index:
                                orders_sum_value = pivot_data.loc[orders_sum_col_clean, col]
                                # Преобразуем в число, если это строка
                                try:
                                    if isinstance(orders_sum_value, str):
                                        # Убираем форматирование (пробелы, запятые)
                                        orders_sum_value = float(orders_sum_value.replace(' ', '').replace(',', ''))
                                    orders_sum_value = float(orders_sum_value)
                                except (ValueError, TypeError):
                                    orders_sum_value = 0.0
                                
                                if pd.notna(orders_sum_value) and orders_sum_value > 0 and reklama_value > 0:
                                    correct_drr = (reklama_value / orders_sum_value) * 100
                                    formatted_data.loc[idx, col] = f'{correct_drr:.2f}%'
                                else:
                                    formatted_data.loc[idx, col] = '0.00%'
                            else:
                                formatted_data.loc[idx, col] = '0.00%'
                        else:
                            formatted_data.loc[idx, col] = f'{original_value:.2f}%'
                    else:
                        formatted_data.loc[idx, col] = '0.00%'
                elif idx == 'Процент выкупа':  # Для Процента выкупа используем форматирование с процентами
                    original_value = pivot_data.loc[idx, col]
                    if pd.notna(original_value) and original_value != 0:
                        formatted_data.loc[idx, col] = f'{original_value:.1f}%'
                    else:
                        formatted_data.loc[idx, col] = '0.0%'
                elif idx == 'Средняя цена':  # Для средней цены используем форматирование с 2 знаками
                    original_value = pivot_data.loc[idx, col]
                    if pd.notna(original_value) and original_value != 0:
                        formatted_data.loc[idx, col] = f'{original_value:.2f}'
                    else:
                        formatted_data.loc[idx, col] = '0.00'
                elif idx == 'Прибыль на ед.':  # Для прибыли на единицу используем форматирование с 2 знаками
                    original_value = pivot_data.loc[idx, col]
                    try:
                        if pd.notna(original_value) and original_value != 0:
                            formatted_data.loc[idx, col] = f'{original_value:.2f} ₽'
                        else:
                            formatted_data.loc[idx, col] = '0.00 ₽'
                    except:
                        formatted_data.loc[idx, col] = '0.00 ₽'
                elif idx in ['Конверсия в корзину, %', 'Конверсия в заказ, %', 'Рентабельность факт', 'Рентабельность план']:  # Для конверсий и рентабельности используем форматирование с процентами
                    original_value = pivot_data.loc[idx, col]
                    if pd.notna(original_value) and original_value != 0:
                        formatted_data.loc[idx, col] = f'{original_value:.1f}%'
                    else:
                        formatted_data.loc[idx, col] = '0.0%'
                elif idx == 'Прибыль':  # Для прибыли используем форматирование с рублями
                    original_value = pivot_data.loc[idx, col]
                    if pd.notna(original_value) and original_value != 0:
                        formatted_data.loc[idx, col] = f'{original_value:,.0f} ₽'.replace(',', ' ')
                    else:
                        formatted_data.loc[idx, col] = '0 ₽'
                elif idx == 'Реклама':  # Для рекламы используем форматирование с пробелами
                    original_value = pivot_data.loc[idx, col]
                    if pd.notna(original_value) and original_value != 0:
                        formatted_data.loc[idx, col] = f'{int(original_value):,}'.replace(',', ' ')
                    else:
                        formatted_data.loc[idx, col] = '0'
                elif idx in ['Заказ план', 'Продажа план']:  # Для планов показываем 0 или "нет данных"
                    original_value = pivot_data.loc[idx, col]
                    if pd.notna(original_value) and original_value != 0:
                        formatted_data.loc[idx, col] = f'{int(original_value):,}'.replace(',', ' ')
                    else:
                        formatted_data.loc[idx, col] = '0'
                elif 'Заказали на сумму' in idx:  # Для сумм заказов используем читаемое форматирование
                    original_value = pivot_data.loc[idx, col]
                    if pd.notna(original_value) and original_value != 0:
                        formatted_data.loc[idx, col] = f'{int(original_value):,} ₽'.replace(',', ' ')
                    else:
                        formatted_data.loc[idx, col] = '0 ₽'
                elif 'Выкупили на сумму' in idx:  # Для сумм выкупов используем читаемое форматирование
                    original_value = pivot_data.loc[idx, col]
                    if pd.notna(original_value) and original_value != 0:
                        formatted_data.loc[idx, col] = f'{int(original_value):,} ₽'.replace(',', ' ')
                    else:
                        formatted_data.loc[idx, col] = '0 ₽'
        
        # Применяем цветовое кодирование к таблице (по строкам)
        def highlight_orders_sales(row):
            """Функция для цветового кодирования строк заказов и выкупов"""
            row_name = row.name
            styles = []
            
            # Определяем цвет в зависимости от строки
            if 'Заказали' in row_name and 'план' not in row_name.lower():
                # Для заказов - синий цвет
                # Находим максимальное числовое значение в строке для нормализации
                numeric_values = []
                for val in row:
                    try:
                        if isinstance(val, str):
                            if val.replace(' ', '').replace(',', '') == '' or val == '0':
                                continue
                            num_val = float(val.replace(' ', '').replace(',', ''))
                        else:
                            if pd.isna(val) or val == 0:
                                continue
                            num_val = float(val)
                        numeric_values.append(num_val)
                    except:
                        continue
                
                max_val = max(numeric_values) if numeric_values else 1000
                
                for val in row:
                    if pd.isna(val) or val == '' or val == '0':
                        styles.append('')
                    else:
                        try:
                            if isinstance(val, str):
                                if val.replace(' ', '').replace(',', '') == '':
                                    styles.append('')
                                    continue
                                num_val = float(val.replace(' ', '').replace(',', ''))
                            else:
                                num_val = float(val)
                            intensity = min(num_val / max_val, 1.0)
                            alpha = 0.1 + (intensity * 0.4)  # От 0.1 до 0.5
                            styles.append(f'background-color: rgba(0, 123, 255, {alpha})')
                        except:
                            styles.append('')
                return styles
            elif 'Выкупили' in row_name and 'план' not in row_name.lower():
                # Для выкупов - зеленый цвет
                # Находим максимальное числовое значение в строке для нормализации
                numeric_values = []
                for val in row:
                    try:
                        if isinstance(val, str):
                            if val.replace(' ', '').replace(',', '') == '' or val == '0':
                                continue
                            num_val = float(val.replace(' ', '').replace(',', ''))
                        else:
                            if pd.isna(val) or val == 0:
                                continue
                            num_val = float(val)
                        numeric_values.append(num_val)
                    except:
                        continue
                
                max_val = max(numeric_values) if numeric_values else 1000
                
                for val in row:
                    if pd.isna(val) or val == '' or val == '0':
                        styles.append('')
                    else:
                        try:
                            if isinstance(val, str):
                                if val.replace(' ', '').replace(',', '') == '':
                                    styles.append('')
                                    continue
                                num_val = float(val.replace(' ', '').replace(',', ''))
                            else:
                                num_val = float(val)
                            intensity = min(num_val / max_val, 1.0)
                            alpha = 0.1 + (intensity * 0.4)  # От 0.1 до 0.5
                            styles.append(f'background-color: rgba(40, 167, 69, {alpha})')
                        except:
                            styles.append('')
                return styles
            else:
                return [''] * len(row)
        
        # Убеждаемся, что индексы уникальны для стилизации
        formatted_data_unique = formatted_data.copy()
        formatted_data_unique.index = [f"{idx}_{i}" if formatted_data.index.tolist().count(idx) > 1 else idx 
                                      for i, idx in enumerate(formatted_data.index)]
        
        # Применяем стилизацию по строкам
        styled_data = formatted_data_unique.style.apply(highlight_orders_sales, axis=1)
        
        # Добавляем выделение планов заказов с отклонениями
        def highlight_plan_deviations(df):
            """Функция для выделения планов заказов в зависимости от отклонения от факта"""
            styles = pd.DataFrame('', index=df.index, columns=df.columns)
            
            # Находим строки с планами и фактами заказов
            plan_row = None
            fact_row = None
            
            for idx in df.index:
                if 'Заказ план' in idx:
                    plan_row = idx
                elif 'Заказали, шт' in idx:  # Точное название строки с фактом
                    fact_row = idx
            
            if plan_row and fact_row:
                for col in df.columns:
                    try:
                        # Получаем значения плана и факта
                        plan_val = df.loc[plan_row, col]
                        fact_val = df.loc[fact_row, col]
                        
                        # Преобразуем в числа
                        if isinstance(plan_val, str):
                            plan_num = float(plan_val.replace(' ', '').replace(',', '')) if plan_val.replace(' ', '').replace(',', '') not in ['', '0'] else 0
                        else:
                            plan_num = float(plan_val) if not pd.isna(plan_val) else 0
                            
                        if isinstance(fact_val, str):
                            fact_num = float(fact_val.replace(' ', '').replace(',', '')) if fact_val.replace(' ', '').replace(',', '') not in ['', '0'] else 0
                        else:
                            fact_num = float(fact_val) if not pd.isna(fact_val) else 0
                        
                        # Рассчитываем отклонение только если оба значения больше 0
                        if plan_num > 0 and fact_num > 0:
                            deviation = ((plan_num - fact_num) / fact_num) * 100
                            
                            # Определяем цвет в зависимости от отклонения
                            if deviation > 5:  # План больше факта на 5%+ - красный
                                intensity = min(abs(deviation) / 100, 1.0)  # Нормализуем до 100%
                                red_intensity = int(200 * intensity)
                                styles.loc[plan_row, col] = f'background-color: rgba(255, {255-red_intensity}, {255-red_intensity}, 0.8)'
                            elif deviation < -5:  # План меньше факта на 5%+ - зеленый
                                intensity = min(abs(deviation) / 100, 1.0)  # Нормализуем до 100%
                                green_intensity = int(200 * intensity)
                                styles.loc[plan_row, col] = f'background-color: rgba({255-green_intensity}, 255, {255-green_intensity}, 0.8)'
                            # Если отклонение в пределах ±5%, не красим
                    except Exception as e:
                        continue
                        
            return styles
        
        # Добавляем выделение месячных столбцов
        def highlight_monthly_columns(df):
            """Функция для выделения месячных столбцов и текущей недели цветом"""
            styles = pd.DataFrame('', index=df.index, columns=df.columns)
            current_week = get_current_week_column()
            
            for col in df.columns:
                # Проверяем, является ли столбец месячным (формат YYYY.MM без скобок)
                if (col.startswith(("2024.", "2023.", "2022.", "2025.")) and 
                    '(' not in col and 
                    col != "Общие по месяцам"):
                    styles[col] = 'background-color: rgba(255, 193, 7, 0.3)'  # Желтый цвет для месячных столбцов
                
                # Выделяем текущую неделю нейтральным цветом
                if col == current_week:
                    styles[col] = 'background-color: rgba(108, 117, 125, 0.3); font-weight: bold; border: 2px solid #6c757d'  # Серый цвет для текущей недели
                    
            return styles
        
        # Добавляем выделение планов продаж с отклонениями
        def highlight_sales_deviations(df):
            """Функция для выделения планов продаж в зависимости от отклонения от факта"""
            styles = pd.DataFrame('', index=df.index, columns=df.columns)
            
            # Находим строки с планами и фактами продаж
            plan_row = None
            fact_row = None
            
            for idx in df.index:
                if 'Продажа план' in idx:
                    plan_row = idx
                elif 'Выкупили, шт' in idx:  # Точное название строки с фактом продаж
                    fact_row = idx
            
            if plan_row and fact_row:
                for col in df.columns:
                    try:
                        # Получаем значения плана и факта
                        plan_val = df.loc[plan_row, col]
                        fact_val = df.loc[fact_row, col]
                        
                        # Преобразуем в числа
                        if isinstance(plan_val, str):
                            plan_num = float(plan_val.replace(' ', '').replace(',', '')) if plan_val.replace(' ', '').replace(',', '') not in ['', '0'] else 0
                        else:
                            plan_num = float(plan_val) if not pd.isna(plan_val) else 0
                            
                        if isinstance(fact_val, str):
                            fact_num = float(fact_val.replace(' ', '').replace(',', '')) if fact_val.replace(' ', '').replace(',', '') not in ['', '0'] else 0
                        else:
                            fact_num = float(fact_val) if not pd.isna(fact_val) else 0
                        
                        # Рассчитываем отклонение только если оба значения больше 0
                        if plan_num > 0 and fact_num > 0:
                            deviation = ((plan_num - fact_num) / fact_num) * 100
                            
                            # Определяем цвет в зависимости от отклонения
                            if deviation > 5:  # План больше факта на 5%+ - красный
                                intensity = min(abs(deviation) / 100, 1.0)  # Нормализуем до 100%
                                red_intensity = int(200 * intensity)
                                styles.loc[plan_row, col] = f'background-color: rgba(255, {255-red_intensity}, {255-red_intensity}, 0.8)'
                            elif deviation < -5:  # План меньше факта на 5%+ - зеленый
                                intensity = min(abs(deviation) / 100, 1.0)  # Нормализуем до 100%
                                green_intensity = int(200 * intensity)
                                styles.loc[plan_row, col] = f'background-color: rgba({255-green_intensity}, 255, {255-green_intensity}, 0.8)'
                    except:
                        continue
            
            return styles
        
        # Применяем выделение месячных столбцов
        styled_data = styled_data.apply(highlight_monthly_columns, axis=None)
        
        # Применяем выделение планов заказов с отклонениями
        styled_data = styled_data.apply(highlight_plan_deviations, axis=None)
        
        # Применяем выделение планов продаж с отклонениями
        styled_data = styled_data.apply(highlight_sales_deviations, axis=None)
        
        # Таблица готова к отображению
        
        # Получаем текущую неделю для скролла
        current_week = get_current_week_column()
        
        # Проверяем наличие данных для расчета прибыли
        has_sales_data = "Выкупили, шт" in pivot_data.index and any(pivot_data.loc["Выкупили, шт"] > 0) if "Выкупили, шт" in pivot_data.index else False
        has_price_data = "Средняя цена" in pivot_data.index and any(pivot_data.loc["Средняя цена"] > 0) if "Средняя цена" in pivot_data.index else False
        
        if not has_sales_data or not has_price_data:
            st.info("💡 Для расчета прибыли необходимо загрузить файл с данными о продажах и установить параметры рентабельности в боковой панели.")
        
        
        # Создаем вкладки
        tab1, tab2, tab3 = st.tabs(["📊 Основная таблица", "📈 Результаты KPI", "📅 Анализ по сезонам"])
        
        with tab1:
            # Отображаем таблицу с горизонтальной прокруткой
            st.dataframe(
                styled_data, 
                width='stretch',  # Используем всю ширину контейнера
                height=800
            )
            
            # KPI текущего состояния под таблицей
            st.markdown("---")
            st.subheader("🎯 KPI текущего состояния")
            
            # Получаем текущую дату и неделю
            current_date = datetime.now()
            current_week = current_date.isocalendar().week
            current_year = current_date.year
            
            # Получаем неделю начала плана из настроек
            start_week_for_plan = st.session_state.table_settings.get('start_week_for_plan', current_week)
            
            # Формируем название текущей недели
            week_to_month_mapping = {
                27: 7, 28: 7, 29: 7, 30: 7, 31: 7,  # Июль
                32: 8, 33: 8, 34: 8, 35: 8,          # Август  
                36: 9, 37: 9, 38: 9, 39: 9, 40: 9,   # Сентябрь
                41: 10, 42: 10, 43: 10, 44: 10,      # Октябрь
                45: 11, 46: 11, 47: 11, 48: 11,      # Ноябрь
                49: 12, 50: 12, 51: 12, 52: 12,      # Декабрь
                5: 2, 6: 2, 7: 2, 8: 2,              # Февраль
                9: 3, 10: 3, 11: 3, 12: 3, 13: 3,   # Март
                14: 4, 15: 4, 16: 4, 17: 4,          # Апрель
                18: 5, 19: 5, 20: 5, 21: 5, 22: 5,  # Май
                23: 6, 24: 6, 25: 6, 26: 6,          # Июнь
            }
            
            # Рассчитываем накопленные значения от начала периода до текущей даты
            total_orders = 0
            total_sales = 0
            total_revenue = 0
            total_orders_plan = 0
            total_sales_plan = 0
            
            # Получаем все недельные столбцы из таблицы (содержат "(" и "нед.")
            weekly_columns = [col for col in pivot_data.columns if "(" in col and "нед." in col]
            
            # Фильтруем столбцы по диапазону недель от start_week_for_plan до текущей недели
            # Учитываем настройку скрытия недель
            hide_weeks_before = st.session_state.table_settings.get('hide_weeks_before', None)
            
            filtered_columns = []
            for col in weekly_columns:
                # Извлекаем номер недели из названия столбца
                if "(нед." in col:
                    try:
                        week_part = col.split("(нед.")[1].split(")")[0].strip()
                        week_num = int(week_part)
                        
                        # Проверяем, не скрыта ли неделя
                        if hide_weeks_before and week_num < hide_weeks_before:
                            continue
                        
                        # Включаем недели от start_week_for_plan до текущей недели
                        if start_week_for_plan <= week_num <= current_week:
                            filtered_columns.append(col)
                    except (ValueError, IndexError):
                        continue
            
        # Отладочная информация - показываем доступные индексы
        st.caption(f"🔍 Доступные индексы в pivot_data: {list(pivot_data.index)}")
        st.caption(f"🔍 Всего недельных столбцов: {len(weekly_columns)}")
        st.caption(f"🔍 Отфильтрованных столбцов: {len(filtered_columns)}")
        st.caption(f"🔍 Столбцы для расчета: {filtered_columns}")
        
        # Показываем все значения продаж для диагностики
        st.caption("🔍 Все значения продаж по неделям:")
        for col in weekly_columns[:10]:  # Показываем первые 10 недель
            if "Выкупили, шт" in pivot_data.index:
                sales_val = pivot_data.loc["Выкупили, шт", col]
                st.caption(f"  {col}: {sales_val}")
        
        # Суммируем значения по отфильтрованным столбцам
        for week_col in filtered_columns:
                # Суммируем фактические значения
                if "Заказали, шт" in pivot_data.index:
                    orders = pivot_data.loc["Заказали, шт", week_col]
                    # Отладочная информация - показываем значение для каждой недели
                    st.caption(f"🔍 Неделя {week_col}: заказы = {orders} (тип: {type(orders)})")
                    if pd.notna(orders) and orders > 0:
                        total_orders += orders
                        st.caption(f"✅ Добавлено к total_orders: {orders}")
                    else:
                        st.caption(f"❌ Пропущено: orders = {orders} (NaN или <= 0)")
                
                if "Выкупили, шт" in pivot_data.index:
                    sales = pivot_data.loc["Выкупили, шт", week_col]
                    # Отладочная информация - показываем значение для каждой недели
                    st.caption(f"🔍 Неделя {week_col}: продажи = {sales} (тип: {type(sales)})")
                    if pd.notna(sales) and sales > 0:
                        total_sales += sales
                        st.caption(f"✅ Добавлено к total_sales: {sales}")
                    else:
                        st.caption(f"❌ Пропущено: sales = {sales} (NaN или <= 0)")
                else:
                    # Отладочная информация - показываем, что индекс "Выкупили, шт" не найден
                    st.caption(f"⚠️ Индекс 'Выкупили, шт' не найден в pivot_data.index")
                
                if "Заказали на сумму" in pivot_data.index:
                    revenue = pivot_data.loc["Заказали на сумму", week_col]
                    if pd.notna(revenue) and revenue > 0:
                        total_revenue += revenue
                
                # Суммируем плановые значения
                if week_col in st.session_state.orders_plan_values:
                    plan_orders = st.session_state.orders_plan_values[week_col]
                    if plan_orders > 0:
                        total_orders_plan += plan_orders
                
                # Суммируем план продаж из таблицы (строка "Продажа план")
                if "Продажа план" in pivot_data.index:
                    plan_sales = pivot_data.loc["Продажа план", week_col]
                    if pd.notna(plan_sales) and plan_sales > 0:
                        total_sales_plan += plan_sales
            
            # Показываем информацию о найденных столбцах для отладки
                if len(filtered_columns) == 0:
                        st.warning("⚠️ Не найдены столбцы с данными для расчета KPI")
                        st.info(f"📊 Доступные недельные столбцы: {len(weekly_columns)}")
                if len(weekly_columns) > 0:
                    st.info(f"📋 Примеры столбцов: {weekly_columns[:3]}")
                else:
                        st.info(f"✅ Найдено {len(filtered_columns)} столбцов для расчета KPI (недели 25-{min(39, current_week)})")
            
            # Создаем колонки для отображения KPI
                col1, col2, col3, col4 = st.columns(4)
            
                with col1:
                # Заказы (накопленные)
                        st.metric(
                            "📦 Заказы (накопленные)",
                            f"{total_orders:,.0f}",
                            delta=f"{total_orders - total_orders_plan:+.0f}" if total_orders_plan > 0 else None,
                            help=f"Заказы с недели {start_week_for_plan} по {current_week}"
                )
            
                with col2:
                # Продажи (накопленные) с опережением/отставанием от плана
                # Добавляем отладочную информацию
                        if total_sales_plan > 0:
                            sales_difference = total_sales - total_sales_plan
                            sales_percentage = (sales_difference / total_sales_plan) * 100
                    
                            st.metric(
                        "💰 Продажи (накопленные)",
                        f"{total_sales:,.0f}",
                        delta=f"{sales_difference:+.0f}",
                        help=f"Продажи с недели {start_week_for_plan} по {current_week}. План: {total_sales_plan:,.0f}"
                    )
                    
                    # Детальная отладочная информация
                            st.caption(f"🔍 Детали: Факт={total_sales:,.0f}, План={total_sales_plan:,.0f}, Разность={sales_difference:+.0f} ({sales_percentage:+.1f}%)")
                    
                    # Дополнительная диагностика
                            if sales_percentage > 100:  # Если опережение больше 100%
                                    st.info("ℹ️ Значительное опережение плана продаж:")
                                    st.caption(f"📊 Факт продаж: {total_sales:,.0f}")
                                    st.caption(f"📊 План продаж: {total_sales_plan:,.0f}")
                                    st.caption(f"📊 Опережение: +{total_sales - total_sales_plan:,.0f} ({sales_percentage:.1f}%)")
        else:
                    # Показываем отладочную информацию
                    st.metric(
                        "💰 Продажи (накопленные)",
                        f"{total_sales:,.0f}",
                        help=f"Продажи с недели {start_week_for_plan} по {current_week}. План продаж: {total_sales_plan:,.0f}"
                    )
                    # Отладочная информация
                    if len(filtered_columns) > 0:
                        st.caption(f"🔍 Отладка: найдено {len(filtered_columns)} недель, план продаж: {total_sales_plan}")
                        
                        # Проверяем, есть ли вообще данные в sales_plan_values
                        total_sales_plan_values = len(st.session_state.sales_plan_values)
                        st.caption(f"📊 Всего значений в sales_plan_values: {total_sales_plan_values}")
                        
                        # Показываем первые несколько недель и их планы из таблицы
                        sales_plan_debug = []
                        for week_col in filtered_columns[:5]:  # Показываем первые 5 недель
                            if "Продажа план" in pivot_data.index:
                                plan_val = pivot_data.loc["Продажа план", week_col]
                                if pd.notna(plan_val) and plan_val > 0:
                                    sales_plan_debug.append(f"{week_col}: {plan_val}")
                                else:
                                    sales_plan_debug.append(f"{week_col}: 0")
                            else:
                                sales_plan_debug.append(f"{week_col}: НЕТ СТРОКИ")
                        
                        if sales_plan_debug:
                            st.caption(f"📊 План продаж из таблицы: {', '.join(sales_plan_debug)}")
                        
                        # Проверяем, есть ли строка "Продажа план" в таблице
                        if "Продажа план" in pivot_data.index:
                            st.caption("✅ Строка 'Продажа план' найдена в таблице")
                        else:
                            st.caption("❌ Строка 'Продажа план' НЕ найдена в таблице")
            
            
        with col3:
                # Конверсия (общая) = (выкупы / заказы) * 100
                if total_orders > 0:
                    conversion = (total_sales / total_orders) * 100
                    st.metric(
                        "📊 Конверсия (общая)",
                        f"{conversion:.1f}%",
                        help=f"Общая конверсия с недели {start_week_for_plan} по {current_week}"
                    )
                else:
                    st.metric("📊 Конверсия (общая)", "Нет данных")
            
            
            # Подпись текущей недели внизу таблицы - УБИРАЕМ ПО ЗАПРОСУ ПОЛЬЗОВАТЕЛЯ
            # st.markdown(f"<div style='text-align: center; margin-top: 10px; padding: 10px; background-color: #f0f2f6; border-radius: 5px;'><strong>📍 Текущая неделя: {current_week}</strong></div>", unsafe_allow_html=True)
        
        with tab2:
            # Вкладка "Результаты KPI"
            st.header("📈 Результаты KPI")
            
            
            # Сравнение с планом
            st.markdown("---")
            st.subheader("📋 Сравнение с планом")
            
            # Получаем текущую неделю
            current_date = datetime.now()
            current_week = current_date.isocalendar().week
            current_year = current_date.year
            current_month = current_date.month
            
            # Формируем название текущей недели
            week_to_month_mapping = {
                27: 7, 28: 7, 29: 7, 30: 7, 31: 7,  # Июль
                32: 8, 33: 8, 34: 8, 35: 8,          # Август  
                36: 9, 37: 9, 38: 9, 39: 9, 40: 9,   # Сентябрь
                41: 10, 42: 10, 43: 10, 44: 10,      # Октябрь
                45: 11, 46: 11, 47: 11, 48: 11,      # Ноябрь
                49: 12, 50: 12, 51: 12, 52: 12,      # Декабрь
                5: 2, 6: 2, 7: 2, 8: 2,              # Февраль
                9: 3, 10: 3, 11: 3, 12: 3, 13: 3,   # Март
                14: 4, 15: 4, 16: 4, 17: 4,          # Апрель
                18: 5, 19: 5, 20: 5, 21: 5, 22: 5,  # Май
                23: 6, 24: 6, 25: 6, 26: 6,          # Июнь
            }
            
            current_month_from_week = week_to_month_mapping.get(current_week, current_month)
            current_week_col = f"{current_year}.{current_month_from_week} (нед. {current_week:02d})"
            
            # Получаем план для текущей недели
            plan_orders = st.session_state.orders_plan_values.get(current_week_col, 0)
            plan_rentability = st.session_state.rentability_plan_values.get(current_week_col, 0)
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Сравнение заказов с планом
                if current_week_col in pivot_data.columns and "Заказали, шт" in pivot_data.index:
                    actual_orders = pivot_data.loc["Заказали, шт", current_week_col]
                    if pd.notna(actual_orders) and actual_orders > 0 and plan_orders > 0:
                        orders_difference = actual_orders - plan_orders
                        orders_percentage = (orders_difference / plan_orders) * 100
                        
                        if orders_percentage > 0:
                            st.success(f"✅ Заказы опережают план на {orders_percentage:.1f}%")
                        elif orders_percentage < -10:
                            st.error(f"❌ Заказы отстают от плана на {abs(orders_percentage):.1f}%")
                        else:
                            st.warning(f"⚠️ Заказы близки к плану: {orders_percentage:.1f}%")
                        
                        st.metric(
                            "📦 Заказы vs План",
                            f"{actual_orders:,.0f}",
                            delta=f"{orders_difference:+.0f}",
                            help=f"План: {plan_orders:,.0f}"
                        )
                    else:
                        st.info("📊 Данные для сравнения заказов с планом отсутствуют")
                else:
                    st.info("📊 Данные для сравнения заказов с планом отсутствуют")
            
            with col2:
                # Сравнение рентабельности с планом
                if plan_rentability > 0:
                    # Получаем фактическую рентабельность для текущей недели
                    if current_week_col in pivot_data.columns and "Рентабельность, %" in pivot_data.index:
                        actual_rentability = pivot_data.loc["Рентабельность, %", current_week_col]
                        if pd.notna(actual_rentability) and actual_rentability > 0:
                            rentability_difference = actual_rentability - plan_rentability
                            
                            if rentability_difference > 2:
                                st.success(f"✅ Рентабельность опережает план на {rentability_difference:.1f}%")
                            elif rentability_difference < -2:
                                st.error(f"❌ Рентабельность отстает от плана на {abs(rentability_difference):.1f}%")
                            else:
                                st.warning(f"⚠️ Рентабельность близка к плану: {rentability_difference:+.1f}%")
                            
                            st.metric(
                                "💰 Рентабельность vs План",
                                f"{actual_rentability:.1f}%",
                                delta=f"{rentability_difference:+.1f}%",
                                help=f"План: {plan_rentability:.1f}%"
                            )
                        else:
                            st.info("📊 Фактическая рентабельность не рассчитана")
                    else:
                        st.info("📊 Данные для сравнения рентабельности отсутствуют")
                else:
                    st.info("📊 План рентабельности не установлен")
            
            # Рассчитываем KPI по сезонам
            st.markdown("---")
            st.subheader("📈 KPI по сезонам")
            seasonal_kpi = calculate_seasonal_kpi(pivot_data)
            
            # Определяем все возможные сезоны (последние 4 сезона)
            current_year = datetime.now().year
            current_month = datetime.now().month
            
            # Определяем текущий сезон
            if current_month >= 7:
                current_season = f"{current_year}-1"
            else:
                current_season = f"{current_year}-2"
            
            # Создаем список из 4 последних сезонов
            all_seasons = []
            for year in [current_year - 1, current_year]:
                all_seasons.extend([f"{year}-2", f"{year}-1"])  # 2 сезон, затем 1 сезон
            
            # Берем последние 4 сезона
            display_seasons = all_seasons[-4:]
            
            # Создаем колонки для отображения KPI
            cols = st.columns(4)
            
            for i, season in enumerate(display_seasons):
                with cols[i]:
                    year, season_num = season.split('-')
                    season_name = f"{year} год, {season_num} сезон"
                    
                    if season_num == '1':
                        season_period = "1 июля - 31 декабря"
                    else:
                        season_period = "1 февраля - 30 июня"
                    
                    st.subheader(f"📅 {season_name}")
                    st.caption(f"Период: {season_period}")
                    
                    if season in seasonal_kpi and seasonal_kpi[season]['has_data']:
                        kpi = seasonal_kpi[season]
                        
                        # Заказы
                        st.metric(
                            "📦 Заказы",
                            f"{kpi['orders_fact']:,.0f}",
                            delta=f"План: {kpi['orders_plan']:,.0f}" if kpi['orders_plan'] > 0 else None
                        )
                        
                        # Продажи
                        st.metric(
                            "💰 Продажи",
                            f"{kpi['sales_fact']:,.0f}",
                            delta=f"План: {kpi['sales_plan']:,.0f}" if kpi['sales_plan'] > 0 else None
                        )
                        
                        # Выручка
                        st.metric(
                            "💵 Выручка",
                            f"{kpi['revenue_fact']:,.0f} ₽",
                            delta=f"План: {kpi['revenue_plan']:,.0f} ₽" if kpi['revenue_plan'] > 0 else None
                        )
                        
                        # Конверсия
                        st.metric(
                            "📊 Конверсия",
                            f"{kpi['conversion_rate']:.1f}%"
                        )
                        
                        # Средняя цена
                        st.metric(
                            "🏷️ Средняя цена",
                            f"{kpi['avg_price']:,.0f} ₽"
                        )
                        
                        # Выполнение плана заказов
                        if kpi['orders_plan'] > 0:
                            orders_completion = (kpi['orders_fact'] / kpi['orders_plan']) * 100
                            st.metric(
                                "✅ Выполнение плана заказов",
                                f"{orders_completion:.1f}%",
                                delta=f"{orders_completion - 100:+.1f}%"
                            )
                        
                        # Выполнение плана продаж
                        if kpi['sales_plan'] > 0:
                            sales_completion = (kpi['sales_fact'] / kpi['sales_plan']) * 100
                            st.metric(
                                "✅ Выполнение плана продаж",
                                f"{sales_completion:.1f}%",
                                delta=f"{sales_completion - 100:+.1f}%"
                            )
                    else:
                        # Нет данных
                        st.info("📭 Нет данных")
                        st.metric("📦 Заказы", "Нет данных")
                        st.metric("💰 Продажи", "Нет данных")
                        st.metric("💵 Выручка", "Нет данных")
                        st.metric("📊 Конверсия", "Нет данных")
                        st.metric("🏷️ Средняя цена", "Нет данных")
                        st.metric("✅ Выполнение плана", "Нет данных")
            
            # Дополнительная информация
            st.markdown("---")
            st.markdown("### 📋 Информация о сезонах")
            st.info("""
            **Определение сезонов:**
            - **1 сезон**: 1 июля - 31 декабря
            - **2 сезон**: 1 февраля - 30 июня
            
            **Отображаются последние 4 сезона** для анализа динамики показателей.
            """)
            
            # Сводная таблица по сезонам
            if seasonal_kpi:
                st.markdown("### 📊 Сводная таблица по сезонам")
                
                # Создаем DataFrame для сводной таблицы
                summary_data = []
                for season in display_seasons:
                    if season in seasonal_kpi and seasonal_kpi[season]['has_data']:
                        kpi = seasonal_kpi[season]
                        year, season_num = season.split('-')
                        summary_data.append({
                            'Сезон': f"{year} год, {season_num} сезон",
                            'Заказы (факт)': f"{kpi['orders_fact']:,.0f}",
                            'Продажи (факт)': f"{kpi['sales_fact']:,.0f}",
                            'Выручка (факт)': f"{kpi['revenue_fact']:,.0f} ₽",
                            'Конверсия (%)': f"{kpi['conversion_rate']:.1f}%",
                            'Средняя цена (₽)': f"{kpi['avg_price']:,.0f}",
                            'Выполнение плана заказов (%)': f"{(kpi['orders_fact'] / kpi['orders_plan']) * 100:.1f}%" if kpi['orders_plan'] > 0 else "Нет плана",
                            'Выполнение плана продаж (%)': f"{(kpi['sales_fact'] / kpi['sales_plan']) * 100:.1f}%" if kpi['sales_plan'] > 0 else "Нет плана"
                        })
                    else:
                        year, season_num = season.split('-')
                        summary_data.append({
                            'Сезон': f"{year} год, {season_num} сезон",
                            'Заказы (факт)': "Нет данных",
                            'Продажи (факт)': "Нет данных",
                            'Выручка (факт)': "Нет данных",
                            'Конверсия (%)': "Нет данных",
                            'Средняя цена (₽)': "Нет данных",
                            'Выполнение плана заказов (%)': "Нет данных",
                            'Выполнение плана продаж (%)': "Нет данных"
                        })
                
                if summary_data:
                    summary_df = pd.DataFrame(summary_data)
                    st.dataframe(summary_df, use_container_width=True)
        
        with tab3:
            # Вкладка "Анализ по сезонам"
            st.header("📅 Анализ по сезонам")
            
            # Определяем сезоны согласно запросу пользователя
            season1_start = "2025-01-01"
            season1_end = "2025-06-30"
            season2_start = "2025-07-01" 
            season2_end = "2025-12-31"
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("🌱 Сезон 1")
                st.info(f"**Период:** {season1_start} - {season1_end}")
                st.write("**Месяцы:** Январь - Июнь 2025")
                
                # Анализ данных за сезон 1
                season1_columns = []
                for col in pivot_data.columns:
                    if '(' in col and 'нед.' in col:
                        # Извлекаем дату из названия столбца
                        date_part = col.split(' (')[0]  # "2025.1", "2025.2", etc.
                        if date_part.startswith("2025."):
                            month = int(date_part.split('.')[1])
                            if 1 <= month <= 6:  # Январь - Июнь
                                season1_columns.append(col)
                
                if season1_columns:
                    st.success(f"✅ Найдено {len(season1_columns)} недель в сезоне 1")
                    
                    # Рассчитываем показатели для сезона 1
                    season1_data = {}
                    if "Заказали, шт" in pivot_data.index:
                        season1_orders = sum([pivot_data.loc["Заказали, шт", col] for col in season1_columns if pd.notna(pivot_data.loc["Заказали, шт", col])])
                        season1_data["Заказы"] = season1_orders
                    
                    if "Выкупили, шт" in pivot_data.index:
                        season1_sales = sum([pivot_data.loc["Выкупили, шт", col] for col in season1_columns if pd.notna(pivot_data.loc["Выкупили, шт", col])])
                        season1_data["Продажи"] = season1_sales
                    
                    if "Заказали на сумму" in pivot_data.index:
                        season1_revenue = sum([pivot_data.loc["Заказали на сумму", col] for col in season1_columns if pd.notna(pivot_data.loc["Заказали на сумму", col])])
                        season1_data["Выручка"] = season1_revenue
                    
                    # Отображаем результаты
                    for metric, value in season1_data.items():
                        if metric == "Выручка":
                            st.metric(f"{metric} (₽)", f"{value:,.0f}")
                        else:
                            st.metric(f"{metric} (шт)", f"{value:,.0f}")
                else:
                    st.warning("⚠️ Данные за сезон 1 не найдены")
            
            with col2:
                st.subheader("🍂 Сезон 2")
                st.info(f"**Период:** {season2_start} - {season2_end}")
                st.write("**Месяцы:** Июль - Декабрь 2025")
                
                # Анализ данных за сезон 2
                season2_columns = []
                for col in pivot_data.columns:
                    if '(' in col and 'нед.' in col:
                        # Извлекаем дату из названия столбца
                        date_part = col.split(' (')[0]  # "2025.7", "2025.8", etc.
                        if date_part.startswith("2025."):
                            month = int(date_part.split('.')[1])
                            if 7 <= month <= 12:  # Июль - Декабрь
                                season2_columns.append(col)
                
                if season2_columns:
                    st.success(f"✅ Найдено {len(season2_columns)} недель в сезоне 2")
                    
                    # Рассчитываем показатели для сезона 2
                    season2_data = {}
                    if "Заказали, шт" in pivot_data.index:
                        season2_orders = sum([pivot_data.loc["Заказали, шт", col] for col in season2_columns if pd.notna(pivot_data.loc["Заказали, шт", col])])
                        season2_data["Заказы"] = season2_orders
                    
                    if "Выкупили, шт" in pivot_data.index:
                        season2_sales = sum([pivot_data.loc["Выкупили, шт", col] for col in season2_columns if pd.notna(pivot_data.loc["Выкупили, шт", col])])
                        season2_data["Продажи"] = season2_sales
                    
                    if "Заказали на сумму" in pivot_data.index:
                        season2_revenue = sum([pivot_data.loc["Заказали на сумму", col] for col in season2_columns if pd.notna(pivot_data.loc["Заказали на сумму", col])])
                        season2_data["Выручка"] = season2_revenue
                    
                    # Отображаем результаты
                    for metric, value in season2_data.items():
                        if metric == "Выручка":
                            st.metric(f"{metric} (₽)", f"{value:,.0f}")
                        else:
                            st.metric(f"{metric} (шт)", f"{value:,.0f}")
                else:
                    st.warning("⚠️ Данные за сезон 2 не найдены")
            
            # Сравнительный анализ
            st.markdown("---")
            st.subheader("📊 Сравнительный анализ сезонов")
            
            if season1_columns and season2_columns:
                # Создаем сравнительную таблицу
                comparison_data = []
                
                metrics = ["Заказы", "Продажи", "Выручка"]
                season1_values = [season1_data.get(metric, 0) for metric in metrics]
                season2_values = [season2_data.get(metric, 0) for metric in metrics]
                
                for i, metric in enumerate(metrics):
                    season1_val = season1_values[i]
                    season2_val = season2_values[i]
                    
                    if season1_val > 0 and season2_val > 0:
                        growth = ((season2_val - season1_val) / season1_val) * 100
                        comparison_data.append({
                            "Показатель": metric,
                            "Сезон 1 (Янв-Июн)": f"{season1_val:,.0f}",
                            "Сезон 2 (Июл-Дек)": f"{season2_val:,.0f}",
                            "Изменение (%)": f"{growth:+.1f}%"
                        })
                
                if comparison_data:
                    comparison_df = pd.DataFrame(comparison_data)
                    st.dataframe(comparison_df, use_container_width=True)
                else:
                    st.info("💡 Для сравнения необходимо наличие данных в обоих сезонах")
            else:
                st.info("💡 Загрузите данные для анализа сезонов")
        
            # Расширенный KPI после таблицы (перенесено в первую вкладку)
        st.subheader("📊 Расширенный KPI")
        
        # Получаем данные для KPI
        if "Заказ план" in pivot_data.index and "Заказали, шт" in pivot_data.index:
            # Рассчитываем общие показатели
            total_plan_orders = 0
            total_fact_orders = 0
            total_plan_sales = 0
            total_fact_sales = 0
            
            # Суммируем по всем недельным столбцам (исключаем месячные и общие)
            week_columns = [col for col in pivot_data.columns if col != "Общие по месяцам" and not (col.startswith(("2024.", "2023.", "2022.", "2025.")) and '(' not in col)]
            
            for col in week_columns:
                plan_orders = pivot_data.loc["Заказ план", col] if pd.notna(pivot_data.loc["Заказ план", col]) else 0
                fact_orders = pivot_data.loc["Заказали, шт", col] if pd.notna(pivot_data.loc["Заказали, шт", col]) else 0
                total_plan_orders += plan_orders
                total_fact_orders += fact_orders
                
                # Для продаж
                if "Продажа план" in pivot_data.index and "Выкупили, шт" in pivot_data.index:
                    plan_sales = pivot_data.loc["Продажа план", col] if pd.notna(pivot_data.loc["Продажа план", col]) else 0
                    fact_sales = pivot_data.loc["Выкупили, шт", col] if pd.notna(pivot_data.loc["Выкупили, шт", col]) else 0
                    total_plan_sales += plan_sales
                    total_fact_sales += fact_sales
            
            # Создаем колонки для KPI
            col1, col2, col3, col4, col5, col6 = st.columns(6)
            
            with col1:
                if total_plan_orders > 0:
                    orders_completion = (total_fact_orders / total_plan_orders) * 100
                    orders_delta = orders_completion - 100
                    st.metric(
                        "Выполнение плана\nзаказов",
                        f"{orders_completion:.1f}%",
                        delta=f"{orders_delta:+.1f}%",
                        help=f"План: {total_plan_orders:.0f} шт, Факт: {total_fact_orders:.0f} шт"
                    )
                else:
                    st.metric(
                        "Выполнение плана\nзаказов",
                        "Нет плана",
                        help="План заказов не установлен"
                    )
            
            with col2:
                if total_plan_sales > 0:
                    sales_completion = (total_fact_sales / total_plan_sales) * 100
                    sales_delta = sales_completion - 100
                    st.metric(
                        "Выполнение плана\nпродаж",
                        f"{sales_completion:.1f}%",
                        delta=f"{sales_delta:+.1f}%",
                        help=f"План: {total_plan_sales:.0f} шт, Факт: {total_fact_sales:.0f} шт"
                    )
                else:
                    st.metric(
                        "Выполнение плана\nпродаж",
                        "Нет плана",
                        help="План продаж не установлен"
                    )
            
            with col3:
                # Средняя рентабельность
                if "Рентабельность факт" in pivot_data.index:
                    rentability_values = []
                    for col in week_columns:
                        rent_val = pivot_data.loc["Рентабельность факт", col] if pd.notna(pivot_data.loc["Рентабельность факт", col]) else 0
                        if rent_val != 0:
                            rentability_values.append(rent_val)
                    
                    if rentability_values:
                        avg_rentability = sum(rentability_values) / len(rentability_values)
                        st.metric(
                            "Средняя\nрентабельность",
                            f"{avg_rentability:.1f}%",
                            help=f"Рассчитано по {len(rentability_values)} неделям"
                        )
                    else:
                        st.metric(
                            "Средняя\nрентабельность",
                            "Нет данных",
                            help="Недостаточно данных для расчета"
                        )
            
            with col4:
                # Средний ДРР
                if "ДРР" in pivot_data.index:
                    drr_values = []
                    for col in week_columns:
                        drr_val = pivot_data.loc["ДРР", col] if pd.notna(pivot_data.loc["ДРР", col]) else 0
                        if drr_val != 0:
                            drr_values.append(drr_val)
                    
                    if drr_values:
                        avg_drr = sum(drr_values) / len(drr_values)
                        st.metric(
                            "Средний\nДРР",
                            f"{avg_drr:.1f}%",
                            help=f"Доля рекламных расходов по {len(drr_values)} неделям"
                        )
                    else:
                        st.metric(
                            "Средний\nДРР",
                            "Нет данных",
                            help="Недостаточно данных для расчета"
                        )
            
            with col5:
                # Общий план продаж
                st.metric(
                    "Общий план\nпродаж",
                    f"{total_plan_sales:.0f} шт",
                    help="Суммарный план продаж по всем неделям"
                )
            
            with col6:
                # Общий факт продаж
                st.metric(
                    "Общий факт\nпродаж",
                    f"{total_fact_sales:.0f} шт",
                    help="Суммарный факт продаж по всем неделям"
                )
            
        
        # Линейный график сравнения планов и фактов
        st.subheader("📈 График сравнения планов и фактов заказов")
        
        if "Заказ план" in pivot_data.index and "Заказали, шт" in pivot_data.index:
            # Подготавливаем данные для графика
            chart_data = []
            
            for col in week_columns:
                plan_orders = pivot_data.loc["Заказ план", col] if pd.notna(pivot_data.loc["Заказ план", col]) else 0
                fact_orders = pivot_data.loc["Заказали, шт", col] if pd.notna(pivot_data.loc["Заказали, шт", col]) else 0
                
                # Извлекаем дату из названия столбца для сортировки
                try:
                    if "2025." in col and "(" in col:
                        year_month = col.split(" (")[0]  # "2025.09"
                        week_num = col.split(" (нед. ")[1].split(")")[0]  # "38"
                        # Создаем дату для сортировки (примерная)
                        year = int(year_month.split(".")[0])
                        month = int(year_month.split(".")[1])
                        # Приблизительная дата начала недели
                        week_start = f"{year}-{month:02d}-{int(week_num)*7-6:02d}"
                        chart_data.append({
                            'Неделя': col,
                            'Заказ план': plan_orders,
                            'Заказали, шт': fact_orders,
                            'Дата': week_start
                        })
                except:
                    # Если не удалось распарсить дату, используем порядковый номер
                    chart_data.append({
                        'Неделя': col,
                        'Заказ план': plan_orders,
                        'Заказали, шт': fact_orders,
                        'Дата': f"2025-01-{len(chart_data)+1:02d}"
                    })
            
            if chart_data:
                # Создаем DataFrame для графика
                import pandas as pd
                chart_df = pd.DataFrame(chart_data)
                
                # Сортируем по дате
                chart_df['Дата'] = pd.to_datetime(chart_df['Дата'], errors='coerce')
                chart_df = chart_df.sort_values('Дата')
                
                # Создаем график
                import plotly.graph_objects as go
                from plotly.subplots import make_subplots
                
                fig = go.Figure()
                
                # Добавляем линии
                fig.add_trace(go.Scatter(
                    x=chart_df['Неделя'],
                    y=chart_df['Заказ план'],
                    mode='lines+markers',
                    name='Заказ план',
                    line=dict(color='#1f77b4', width=3),
                    marker=dict(size=8)
                ))
                
                fig.add_trace(go.Scatter(
                    x=chart_df['Неделя'],
                    y=chart_df['Заказали, шт'],
                    mode='lines+markers',
                    name='Заказали, шт',
                    line=dict(color='#ff7f0e', width=3),
                    marker=dict(size=8)
                ))
                
                # Настройки графика
                fig.update_layout(
                    title='Сравнение планов и фактов заказов по неделям',
                    xaxis_title='Недели',
                    yaxis_title='Количество заказов',
                    hovermode='x unified',
                    height=600,
                    showlegend=True,
                    legend=dict(
                        orientation="h",
                        yanchor="bottom",
                        y=1.02,
                        xanchor="right",
                        x=1
                    ),
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    font=dict(size=12)
                )
                
                # Поворачиваем подписи на оси X для лучшей читаемости
                fig.update_xaxes(tickangle=45)
                
                # Отображаем график
                st.plotly_chart(fig, use_container_width=True)
                
                # Добавляем статистику под графиком
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    total_plan = chart_df['Заказ план'].sum()
                    total_fact = chart_df['Заказали, шт'].sum()
                    st.metric(
                        "Общий план заказов",
                        f"{total_plan:.0f} шт"
                    )
                
                with col2:
                    st.metric(
                        "Общий факт заказов",
                        f"{total_fact:.0f} шт"
                    )
                
                with col3:
                    if total_plan > 0:
                        overall_completion = (total_fact / total_plan) * 100
                        st.metric(
                            "Общее выполнение",
                            f"{overall_completion:.1f}%"
                        )
                    else:
                        st.metric(
                            "Общее выполнение",
                            "Нет плана"
                        )
            else:
                st.warning("⚠️ Недостаточно данных для построения графика")
        else:
            st.warning("⚠️ Отсутствуют данные о планах или фактах заказов")
        
        # Session state уже инициализирован выше
        
        # Добавляем интерфейс для ввода рекламы под таблицу
        st.subheader("💰 Настройка рекламы по неделям")
        
        # Выпадающий список для выбора недели (текущая неделя по умолчанию)
        current_week = get_current_week_column()
        week_options = list(pivot_data.columns)
        current_week_index = 0
        if current_week in week_options:
            current_week_index = week_options.index(current_week)
        else:
            # Если текущая неделя не найдена, ищем ближайшую
            for i, week in enumerate(week_options):
                if current_week in week or week in current_week:
                    current_week_index = i
                    break
        
        selected_week = st.selectbox(
            "Выберите неделю для настройки рекламы:",
            options=week_options,
            index=current_week_index,
            help="Выберите неделю для ввода суммы рекламы"
        )
        
        # Поле ввода рекламы для выбранной недели
        current_reklama_value = st.session_state.reklama_values.get(selected_week, 0.0)
        reklama_value = st.number_input(
            f"Введите сумму рекламы для {selected_week}:",
            min_value=0.0,
            value=current_reklama_value,
            step=1000.0,
            help="Сумма рекламы для расчета ДРР (Доход на Рубль Рекламы)"
        )
        
        # Обновляем session state при изменении значения
        if reklama_value != current_reklama_value:
            st.session_state.reklama_values[selected_week] = reklama_value
            save_settings_to_cache()  # Автоматически сохраняем в кеш
        
        
        # Кнопки для сохранения и загрузки настроек
        col1, col2 = st.columns(2)
        with col1:
            if st.button("💾 Сохранить настройки в кеш", help="Сохраняет текущие настройки рекламы и планов"):
                save_settings_to_cache()
                st.success("Настройки сохранены в кеш!")
        with col2:
            if st.button("🔄 Загрузить настройки из кеша", help="Загружает сохраненные настройки"):
                if load_settings_from_cache():
                    st.success("Настройки загружены из кеша!")
                    # Убираем st.rerun() чтобы избежать постоянных перезагрузок
                else:
                    st.warning("Кеш не найден или пуст")
        
        
        # Session state для планов уже инициализирован выше
        
        # Добавляем интерфейс для редактирования планов
        st.subheader("📋 Настройка планов по неделям")
        
        # Планирование заказов по месяцам в процентах
        st.markdown("**📊 Планирование заказов по месяцам в процентах:**")
        
        # Показываем текущие настройки
        if st.session_state.monthly_percentages:
            st.info(f"📋 Текущие настройки: Базовое значение = {st.session_state.base_orders_value} шт")
            # Показываем проценты по месяцам в компактном виде
            month_names = ["Янв", "Фев", "Мар", "Апр", "Май", "Июн", "Июл", "Авг", "Сен", "Окт", "Ноя", "Дек"]
            percentages_display = []
            for i in range(1, 13):
                pct = st.session_state.monthly_percentages.get(i, 100.0)
                percentages_display.append(f"{month_names[i-1]}: {pct:.0f}%")
            st.info(f"📊 Проценты по месяцам: {', '.join(percentages_display)}")
        
        # Создаем интерфейс для ввода процентов по месяцам
        # Инициализируем monthly_percentages значениями из session_state или 100.0 по умолчанию
        monthly_percentages = {i: st.session_state.monthly_percentages.get(i, 100.0) for i in range(1, 13)}
        
        # Создаем колонки для месяцев
        col1, col2, col3, col4 = st.columns(4)
        
        months = [
            (1, "Январь"), (2, "Февраль"), (3, "Март"), (4, "Апрель"),
            (5, "Май"), (6, "Июнь"), (7, "Июль"), (8, "Август"),
            (9, "Сентябрь"), (10, "Октябрь"), (11, "Ноябрь"), (12, "Декабрь")
        ]
        
        with col1:
            for i in range(0, 3):
                month_num, month_name = months[i]
                saved_value = st.session_state.monthly_percentages.get(month_num, 100.0)
                monthly_percentages[month_num] = st.number_input(
                    f"{month_name} (%)",
                    min_value=0.0,
                    max_value=1000.0,
                    value=saved_value,
                    step=1.0,
                    key=f"orders_month_{month_num}_percent"
                )
                # Сохраняем изменения в session state
                if monthly_percentages[month_num] != saved_value:
                    st.session_state.monthly_percentages[month_num] = monthly_percentages[month_num]
                    save_settings_to_cache()
        
        with col2:
            for i in range(3, 6):
                month_num, month_name = months[i]
                saved_value = st.session_state.monthly_percentages.get(month_num, 100.0)
                monthly_percentages[month_num] = st.number_input(
                    f"{month_name} (%)",
                    min_value=0.0,
                    max_value=1000.0,
                    value=saved_value,
                    step=1.0,
                    key=f"orders_month_{month_num}_percent"
                )
                # Сохраняем изменения в session state
                if monthly_percentages[month_num] != saved_value:
                    st.session_state.monthly_percentages[month_num] = monthly_percentages[month_num]
                    save_settings_to_cache()
        
        with col3:
            for i in range(6, 9):
                month_num, month_name = months[i]
                saved_value = st.session_state.monthly_percentages.get(month_num, 100.0)
                monthly_percentages[month_num] = st.number_input(
                    f"{month_name} (%)",
                    min_value=0.0,
                    max_value=1000.0,
                    value=saved_value,
                    step=1.0,
                    key=f"orders_month_{month_num}_percent"
                )
                # Сохраняем изменения в session state
                if monthly_percentages[month_num] != saved_value:
                    st.session_state.monthly_percentages[month_num] = monthly_percentages[month_num]
                    save_settings_to_cache()
        
        with col4:
            for i in range(9, 12):
                month_num, month_name = months[i]
                saved_value = st.session_state.monthly_percentages.get(month_num, 100.0)
                monthly_percentages[month_num] = st.number_input(
                    f"{month_name} (%)",
                    min_value=0.0,
                    max_value=1000.0,
                    value=saved_value,
                    step=1.0,
                    key=f"orders_month_{month_num}_percent"
                )
                # Сохраняем изменения в session state
                if monthly_percentages[month_num] != saved_value:
                    st.session_state.monthly_percentages[month_num] = monthly_percentages[month_num]
                    save_settings_to_cache()
        
        # Кнопки управления настройками
        col1, col2, col3 = st.columns([1, 1, 1])
        with col1:
            if st.button("💾 Сохранить настройки", help="Сохранить текущие настройки в кеш"):
                save_settings_to_cache()
                st.success("✅ Настройки сохранены!")
        with col2:
            if st.button("🔄 Загрузить настройки", help="Загрузить настройки из кеша"):
                if load_settings_from_cache():
                    st.success("✅ Настройки загружены!")
                    # Убираем st.rerun() чтобы избежать постоянных перезагрузок
                else:
                    st.warning("⚠️ Настройки не найдены в кеше")
        with col3:
            if st.button("🔄 Сбросить к умолчанию", help="Сбросить все настройки к значениям по умолчанию"):
                # Сбрасываем настройки к умолчанию
                st.session_state.monthly_percentages = {i: 100.0 for i in range(1, 13)}
                st.session_state.base_orders_value = 50.0
                save_settings_to_cache()
                st.success("✅ Настройки сброшены к умолчанию!")
                # Убираем st.rerun() чтобы избежать постоянных перезагрузок
        
        # Настройка базового значения заказов
        col1, col2 = st.columns([1, 1])
        with col1:
            saved_base_orders = st.session_state.base_orders_value
            base_orders = st.number_input(
                "Базовое значение заказов (шт)",
                min_value=0.0,
                value=saved_base_orders,
                step=5.0,
                key="base_orders_input",
                help="Базовое значение для расчета плана заказов"
            )
            # Сохраняем изменения в session state
            if base_orders != saved_base_orders:
                st.session_state.base_orders_value = base_orders
                save_settings_to_cache()
        
        with col2:
            st.markdown("")  # Пустое место для выравнивания
        
        # Кнопки для генерации планов
        col1, col2, col3 = st.columns([1, 1, 1])
        with col1:
            if st.button("📈 Создать план заказов по процентам", help="Генерирует план заказов на основе ваших процентов по месяцам"):
                if generate_seasonal_orders_plan(pivot_data, monthly_percentages, base_orders):
                    st.success("✅ План заказов создан!")
                    # Убираем st.rerun() чтобы избежать постоянных перезагрузок
        with col2:
            if st.button("💰 Создать план рентабельности по процентам", help="Генерирует план рентабельности на основе ваших процентов по месяцам"):
                # Получаем текущее значение базовой рентабельности из session state или используем 15.0 по умолчанию
                current_base_rentability = st.session_state.get('base_rentability_value', 15.0)
                if generate_seasonal_rentability_plan(pivot_data, st.session_state.monthly_rentability_percentages, current_base_rentability):
                    st.success("✅ План рентабельности создан!")
                    st.rerun()  # Перезагружаем для обновления таблицы
                else:
                    st.error("❌ Ошибка при создании плана рентабельности")
        
        st.markdown("---")
        
        # Выпадающий список для выбора недели (текущая неделя по умолчанию)
        current_week = get_current_week_column()
        week_options = list(pivot_data.columns)
        current_week_index = 0
        if current_week in week_options:
            current_week_index = week_options.index(current_week)
        else:
            # Если текущая неделя не найдена, ищем ближайшую
            for i, week in enumerate(week_options):
                if current_week in week or week in current_week:
                    current_week_index = i
                    break
        
        selected_plan_week = st.selectbox(
            "Выберите неделю для настройки планов:",
            options=week_options,
            index=current_week_index,
            help="Выберите неделю для ввода планов",
            key="plan_week_selector"
        )
        
        # Создаем колонки для ввода планов
        col1, col2 = st.columns(2)
        
        with col1:
            current_orders_plan = st.session_state.orders_plan_values.get(selected_plan_week, 0.0)
            orders_plan_value = st.number_input(
                f"Заказ план для {selected_plan_week}:",
                min_value=0.0,
                value=current_orders_plan,
                step=1.0,
                help="План по заказам для выбранной недели"
            )
            
            # Обновляем session state при изменении значений планов заказов
            if orders_plan_value != current_orders_plan:
                st.session_state.orders_plan_values[selected_plan_week] = orders_plan_value
                save_settings_to_cache()  # Автоматически сохраняем в кеш
            
            # Автоматическое исправление падений в неделях 39, 40, 45, 49 встроено в алгоритм генерации планов
        
        with col2:
            # Продажа план рассчитывается автоматически как Заказ план × % выкупа
            buyout_percent = st.session_state.rentability_params.get('buyout_percent', 22.0)
            current_orders_plan = st.session_state.orders_plan_values.get(selected_plan_week, 0.0)
            calculated_sales_plan = current_orders_plan * (buyout_percent / 100)
            
            st.info(f"**Продажа план для {selected_plan_week}:**")
            st.info(f"📊 {calculated_sales_plan:.1f} шт (рассчитывается автоматически)")
            st.caption(f"Формула: {current_orders_plan:.1f} заказов × {buyout_percent}% выкупа = {calculated_sales_plan:.1f} продаж")
        
        st.markdown("---")
        
        # Добавляем интерфейс для настройки Рентабельность план (аналогично планам заказов)
        st.subheader("💰 Настройка планов рентабельности")
        
        # Планирование рентабельности по месяцам в процентах (аналогично планам заказов)
        st.markdown("**📊 Планирование рентабельности по месяцам в процентах:**")
        
        # Показываем текущие настройки
        if st.session_state.monthly_rentability_percentages:
            st.info(f"📋 Текущие настройки: Базовое значение рентабельности = {st.session_state.get('base_rentability_value', 15.0)}%")
            # Показываем проценты по месяцам в компактном виде
            month_names = ["Янв", "Фев", "Мар", "Апр", "Май", "Июн", "Июл", "Авг", "Сен", "Окт", "Ноя", "Дек"]
            percentages_display = []
            for i in range(1, 13):
                pct = st.session_state.monthly_rentability_percentages.get(i, 100.0)
                percentages_display.append(f"{month_names[i-1]}: {pct:.0f}%")
            st.info("📊 " + " | ".join(percentages_display))
        
        # Создаем интерфейс для ввода процентов по месяцам для рентабельности
        # Инициализируем monthly_rentability_percentages значениями из session_state или 100.0 по умолчанию
        monthly_rentability_percentages = {i: st.session_state.monthly_rentability_percentages.get(i, 100.0) for i in range(1, 13)}
        
        # Создаем колонки для месяцев
        col1, col2, col3, col4 = st.columns(4)
        
        months = [
            (1, "Январь"), (2, "Февраль"), (3, "Март"), (4, "Апрель"),
            (5, "Май"), (6, "Июнь"), (7, "Июль"), (8, "Август"),
            (9, "Сентябрь"), (10, "Октябрь"), (11, "Ноябрь"), (12, "Декабрь")
        ]
        
        with col1:
            for i in range(0, 3):
                month_num, month_name = months[i]
                saved_value = st.session_state.monthly_rentability_percentages.get(month_num, 100.0)
                monthly_rentability_percentages[month_num] = st.number_input(
                    f"{month_name} (%)",
                    min_value=0.0,
                    max_value=1000.0,
                    value=saved_value,
                    step=1.0,
                    key=f"rentability_month_{month_num}_percent"
                )
                # Сохраняем изменения в session state
                if monthly_rentability_percentages[month_num] != saved_value:
                    st.session_state.monthly_rentability_percentages[month_num] = monthly_rentability_percentages[month_num]
                    save_settings_to_cache()
        
        with col2:
            for i in range(3, 6):
                month_num, month_name = months[i]
                saved_value = st.session_state.monthly_rentability_percentages.get(month_num, 100.0)
                monthly_rentability_percentages[month_num] = st.number_input(
                    f"{month_name} (%)",
                    min_value=0.0,
                    max_value=1000.0,
                    value=saved_value,
                    step=1.0,
                    key=f"rentability_month_{month_num}_percent"
                )
                # Сохраняем изменения в session state
                if monthly_rentability_percentages[month_num] != saved_value:
                    st.session_state.monthly_rentability_percentages[month_num] = monthly_rentability_percentages[month_num]
                    save_settings_to_cache()
        
        with col3:
            for i in range(6, 9):
                month_num, month_name = months[i]
                saved_value = st.session_state.monthly_rentability_percentages.get(month_num, 100.0)
                monthly_rentability_percentages[month_num] = st.number_input(
                    f"{month_name} (%)",
                    min_value=0.0,
                    max_value=1000.0,
                    value=saved_value,
                    step=1.0,
                    key=f"rentability_month_{month_num}_percent"
                )
                # Сохраняем изменения в session state
                if monthly_rentability_percentages[month_num] != saved_value:
                    st.session_state.monthly_rentability_percentages[month_num] = monthly_rentability_percentages[month_num]
                    save_settings_to_cache()
        
        with col4:
            for i in range(9, 12):
                month_num, month_name = months[i]
                saved_value = st.session_state.monthly_rentability_percentages.get(month_num, 100.0)
                monthly_rentability_percentages[month_num] = st.number_input(
                    f"{month_name} (%)",
                    min_value=0.0,
                    max_value=1000.0,
                    value=saved_value,
                    step=1.0,
                    key=f"rentability_month_{month_num}_percent"
                )
                # Сохраняем изменения в session state
                if monthly_rentability_percentages[month_num] != saved_value:
                    st.session_state.monthly_rentability_percentages[month_num] = monthly_rentability_percentages[month_num]
                    save_settings_to_cache()
        
        # Кнопки управления настройками рентабельности
        col1, col2, col3 = st.columns([1, 1, 1])
        with col1:
            if st.button("💾 Сохранить настройки рентабельности", help="Сохранить настройки рентабельности в кеш"):
                save_settings_to_cache()
                st.success("✅ Настройки рентабельности сохранены!")
        with col2:
            if st.button("🔄 Сбросить рентабельность к умолчанию", help="Сбросить настройки рентабельности к значениям по умолчанию"):
                # Сбрасываем настройки к умолчанию
                st.session_state.monthly_rentability_percentages = {i: 100.0 for i in range(1, 13)}
                st.session_state.base_rentability_value = 15.0
                save_settings_to_cache()
                st.success("✅ Настройки рентабельности сброшены к умолчанию!")
                st.rerun()
        
        # Базовое значение рентабельности
        current_base_rentability = st.session_state.get('base_rentability_value', 15.0)
        base_rentability = st.number_input(
            "Базовое значение рентабельности (%):",
            min_value=0.0,
            max_value=1000.0,
            value=current_base_rentability,
            step=0.1,
            format="%.1f",
            help="Базовое значение рентабельности в процентах",
            key="base_rentability_input"
        )
        
        # Сохраняем значение в session state при изменении
        if base_rentability != current_base_rentability:
            st.session_state.base_rentability_value = base_rentability
        
        # Кнопки для сохранения и применения настроек рентабельности
        st.markdown("---")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if st.button("💾 Сохранить настройки", help="Сохранить все настройки рентабельности в кеш"):
                save_settings_to_cache()
                st.success("✅ Настройки рентабельности сохранены!")
        
        with col2:
            if st.button("🔄 Применить изменения", help="Применить все изменения и обновить интерфейс"):
                st.success("✅ Изменения применены!")
                # Убираем st.rerun() чтобы отладочная информация не исчезала
        
        with col3:
            if st.button("🧪 Тест добавления", help="Добавить одно тестовое значение"):
                st.write("🔍 ТЕСТ: Добавляем одно значение...")
                test_col = "2025.9 (нед. 36)"  # Фиксированная неделя
                st.session_state.rentability_plan_values[test_col] = 25.5
                st.write(f"🔍 ТЕСТ: Добавлено значение 25.5% для {test_col}")
                st.write(f"🔍 ТЕСТ: session_state теперь содержит {len(st.session_state.rentability_plan_values)} значений")
                # Убираем st.rerun() чтобы отладочная информация не исчезала
        
        with col4:
            if st.button("💰 Создать план рентабельности", help="Создать план рентабельности на основе текущих настроек"):
                st.write(f"🔍 Кнопка нажата! base_rentability={base_rentability}")
                st.write(f"🔍 monthly_percentages: {st.session_state.monthly_percentages}")
                
                # Тестовое добавление значений напрямую
                st.write("🔍 Добавляем тестовые значения напрямую...")
                test_columns = [col for col in pivot_data.columns if "2025." in col and "(" in col][:5]  # Берем первые 5 недель
                for i, col in enumerate(test_columns):
                    test_value = 15.0 + i  # 15.0, 16.0, 17.0, 18.0, 19.0
                    st.session_state.rentability_plan_values[col] = test_value
                    st.write(f"🔍 Добавлено тестовое значение для {col}: {test_value}")
                
                st.write(f"🔍 Теперь session_state содержит {len(st.session_state.rentability_plan_values)} значений")
                
                if generate_seasonal_rentability_plan(pivot_data, st.session_state.monthly_rentability_percentages, base_rentability):
                    st.success("✅ План рентабельности создан!")
                    st.rerun()  # Перезагружаем для обновления таблицы
        
        st.markdown("---")
        
        # Интерфейс для рентабельности план уже добавлен выше в главной части
        
        # Информация о расчете рентабельности
        st.subheader("📊 Расчет рентабельности")
        
        st.info("""
        **Рентабельность факт** рассчитывается автоматически по сложной формуле из приложения "📊 Таблица товаров с детальным расчетом":
        
        **Средняя цена** из таблицы воронки продаж подставляется как **"Цена со скидкой"** в расчет себестоимости.
        
        **Формула расчета:**
        1. **Цена со скидкой** = Средняя цена из воронки
        2. **Комиссия** = Цена со скидкой × % комиссии WB
        3. **Реклама** = Цена со скидкой × % рекламы
        4. **Доставка с учетом выкупа** = (Выкуп% × Логистика + (1-Выкуп%) × (Логистика + 50)) × 100 / Выкуп%
        5. **Выручка с ед.** = Цена со скидкой - Комиссия - Доставка - Реклама - Хранение
        6. **Налог** = Цена со скидкой × 7%
        7. **Прибыль с ед.** = Выручка с ед. - Себестоимость - Налог
        8. **Рентабельность** = (Прибыль с ед. / Себестоимость) × 100%
        
        **💾 Кеширование:** Рассчитанные значения рентабельности сохраняются в кеш для ускорения работы. 
        При изменении параметров рентабельности кеш автоматически очищается.
        
        **Рентабельность план** можно настроить вручную для планирования.
        """)
        
        # Показываем текущую фактическую рентабельность для выбранной недели
        if "Средняя цена" in pivot_data.index:
            avg_price = pivot_data.loc["Средняя цена", selected_plan_week]
            if avg_price > 0:
                # Используем ДРР (долю рекламных расходов) вместо абсолютной суммы рекламы
                drr_value = 0.0
                if "ДРР" in pivot_data.index:
                    drr_value = pivot_data.loc["ДРР", selected_plan_week] if pd.notna(pivot_data.loc["ДРР", selected_plan_week]) else 0.0
                advertising_percent = drr_value  # ДРР уже в процентах
                
                current_rent_fact = calculate_complex_rentability(
                    average_price=avg_price,
                    cost_price=st.session_state.rentability_params.get('cost_price', 100.0),
                    discount_percent=st.session_state.rentability_params.get('discount_percent', 0.0),
                    commission_rate=st.session_state.rentability_params.get('commission_rate', 15.0),
                    logistics_cost=st.session_state.rentability_params.get('logistics_cost', 50.0),
                    advertising_percent=advertising_percent,
                    buyout_percent=st.session_state.rentability_params.get('buyout_percent', 22.0),
                    storage_cost=st.session_state.rentability_params.get('storage_cost', 0.0),
                    spp_discount=st.session_state.rentability_params.get('spp_discount', 25.0)
                )
                
                st.metric(
                    f"Рентабельность факт ({selected_plan_week})",
                    f"{current_rent_fact:.1f}%",
                    help=f"Рассчитано на основе средней цены {avg_price:.0f} ₽"
                )
                
                # Добавляем процент выполнения плана заказов
                if "Заказ план" in pivot_data.index and "Заказали, шт" in pivot_data.index:
                    plan_orders = pivot_data.loc["Заказ план", selected_plan_week] if pd.notna(pivot_data.loc["Заказ план", selected_plan_week]) else 0
                    fact_orders = pivot_data.loc["Заказали, шт", selected_plan_week] if pd.notna(pivot_data.loc["Заказали, шт", selected_plan_week]) else 0
                    
                    if plan_orders > 0:
                        completion_percentage = (fact_orders / plan_orders) * 100
                        delta = completion_percentage - 100
                        st.metric(
                            f"Выполнение плана заказов ({selected_plan_week})",
                            f"{completion_percentage:.1f}%",
                            delta=f"{delta:+.1f}%",
                            help=f"План: {plan_orders:.0f} шт, Факт: {fact_orders:.0f} шт"
                        )
                    else:
                        st.metric(
                            f"Выполнение плана заказов ({selected_plan_week})",
                            "Нет плана",
                            help="План заказов не установлен"
                        )
        
    else:
        st.error("❌ Не удалось определить столбцы для анализа.")

else:
    st.error("❌ Не удалось загрузить данные. Проверьте наличие файла Voronka.xlsx в корневой папке проекта.")

# Таблица для расчета рентабельности товаров
if df is not None:
    st.markdown("---")
    st.subheader("📊 Таблица расчета рентабельности товаров")
    
    # Инициализируем session state для товаров
    if 'rentability_products' not in st.session_state:
        st.session_state.rentability_products = []
    
    # Форма добавления нового товара
    with st.expander("➕ Добавить товар для расчета рентабельности", expanded=False):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            product_name = st.text_input("Название товара", key="new_product_name")
            cost_price = st.number_input("Себестоимость, ₽", min_value=0.0, value=100.0, step=10.0, key="new_cost_price")
            retail_price = st.number_input("Розничная цена, ₽", min_value=0.0, value=150.0, step=10.0, key="new_retail_price")
        
        with col2:
            discount_percent = st.number_input("Скидка, %", min_value=0.0, max_value=100.0, value=0.0, step=1.0, key="new_discount_percent")
            commission_rate = st.number_input("Комиссия WB, %", min_value=0.0, max_value=50.0, value=15.0, step=0.5, key="new_commission_rate")
            logistics_cost = st.number_input("Логистика, ₽", min_value=0.0, value=50.0, step=5.0, key="new_logistics_cost")
        
        with col3:
            advertising_percent = st.number_input("Реклама, %", min_value=0.0, max_value=100.0, value=0.0, step=1.0, key="new_advertising_percent")
            buyout_percent = st.number_input("Выкуп, %", min_value=0.0, max_value=100.0, value=22.0, step=1.0, key="new_buyout_percent")
            storage_cost = st.number_input("Хранение, ₽", min_value=0.0, value=0.0, step=1.0, key="new_storage_cost")
        
        if st.button("➕ Добавить товар", key="add_product_button"):
            if product_name:
                # Рассчитываем рентабельность
                price_with_discount = retail_price * (1 - discount_percent / 100)
                result = calculate_unit_economics(
                    cost_price=cost_price,
                    retail_price=retail_price,
                    discount_percent=discount_percent,
                    commission_rate=commission_rate,
                    logistics_cost=logistics_cost,
                    advertising_percent=advertising_percent,
                    buyout_percent=buyout_percent,
                    storage_cost=storage_cost,
                    spp_discount=25.0
                )
                
                # Добавляем товар в список
                product_data = {
                    'name': product_name,
                    'cost_price': cost_price,
                    'retail_price': retail_price,
                    'discount_percent': discount_percent,
                    'commission_rate': commission_rate,
                    'logistics_cost': logistics_cost,
                    'advertising_percent': advertising_percent,
                    'buyout_percent': buyout_percent,
                    'storage_cost': storage_cost,
                    'profit_per_unit': result['Прибыль за единицу'],
                    'profit_percent': result['Рентабельность, %'],
                    'profit_total': result['Прибыль за единицу'] * result['Продано товара']
                }
                
                st.session_state.rentability_products.append(product_data)
                st.success(f"✅ Товар '{product_name}' добавлен!")
                st.rerun()
            else:
                st.error("❌ Введите название товара")
    
    # Отображение таблицы товаров
    if st.session_state.rentability_products:
        st.markdown("### 📋 Список товаров")
        
        # Создаем DataFrame для отображения
        products_df = pd.DataFrame(st.session_state.rentability_products)
        
        # Переименовываем колонки для лучшего отображения
        display_df = products_df.copy()
        display_df.columns = [
            'Товар', 'Себестоимость, ₽', 'Розничная цена, ₽', 'Скидка, %',
            'Комиссия, %', 'Логистика, ₽', 'Реклама, %', 'Выкуп, %',
            'Хранение, ₽', 'Прибыль/ед, ₽', 'Рентабельность, %', 'Прибыль общая, ₽'
        ]
        
        # Форматируем числовые колонки
        for col in display_df.columns[1:]:
            if col.endswith('₽'):
                display_df[col] = display_df[col].round(2)
            elif col.endswith('%'):
                display_df[col] = display_df[col].round(1)
        
        # Отображаем таблицу
        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True
        )
        
        # Кнопки управления
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🗑️ Очистить все товары", key="clear_all_products"):
                st.session_state.rentability_products = []
                st.success("✅ Все товары удалены!")
                st.rerun()
        
        with col2:
            # Кнопка удаления последнего товара
            if st.button("🗑️ Удалить последний товар", key="remove_last_product"):
                if st.session_state.rentability_products:
                    removed_product = st.session_state.rentability_products.pop()
                    st.success(f"✅ Товар '{removed_product['name']}' удален!")
                    st.rerun()
                else:
                    st.warning("⚠️ Нет товаров для удаления")
        
        with col3:
            # Показать общую прибыль
            total_profit = sum([p['profit_total'] for p in st.session_state.rentability_products])
            st.metric("💰 Общая прибыль", f"{total_profit:,.0f} ₽")
        
        # Детальная информация по каждому товару
        st.markdown("### 🔍 Детальная информация")
        
        for i, product in enumerate(st.session_state.rentability_products):
            with st.expander(f"📦 {product['name']}", expanded=False):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Себестоимость", f"{product['cost_price']:.0f} ₽")
                    st.metric("Розничная цена", f"{product['retail_price']:.0f} ₽")
                    st.metric("Цена со скидкой", f"{product['retail_price'] * (1 - product['discount_percent'] / 100):.0f} ₽")
                
                with col2:
                    st.metric("Комиссия WB", f"{product['commission_rate']:.1f}%")
                    st.metric("Логистика", f"{product['logistics_cost']:.0f} ₽")
                    st.metric("Реклама", f"{product['advertising_percent']:.1f}%")
                
                with col3:
                    st.metric("Прибыль/ед", f"{product['profit_per_unit']:.2f} ₽")
                    st.metric("Рентабельность", f"{product['profit_percent']:.1f}%")
                    st.metric("Выкуп", f"{product['buyout_percent']:.0f}%")
                
                # Кнопка удаления конкретного товара
                if st.button(f"🗑️ Удалить товар", key=f"remove_product_{i}"):
                    st.session_state.rentability_products.pop(i)
                    st.success(f"✅ Товар '{product['name']}' удален!")
                    st.rerun()
    
    else:
        st.info("📝 Добавьте товары для расчета рентабельности, используя форму выше.")
