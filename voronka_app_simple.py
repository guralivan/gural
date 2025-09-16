# -*- coding: utf-8 -*-
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import os
import json
import pickle

# Настройка страницы
st.set_page_config(page_title="Анализ воронки продаж", layout="wide")

st.title("📊 Анализ воронки продаж (Voronka.xlsx)")

# Функции для кеширования данных
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
    """Сохраняет настройки рекламы и планов в кеш"""
    settings = {
        'reklama_values': st.session_state.get('reklama_values', {}),
        'orders_plan_values': st.session_state.get('orders_plan_values', {}),
        'sales_plan_values': st.session_state.get('sales_plan_values', {}),
        'timestamp': datetime.now().isoformat()
    }
    save_cache_data(settings, 'settings_cache.pkl')

def load_settings_from_cache():
    """Загружает настройки рекламы и планов из кеша"""
    settings = load_cache_data('settings_cache.pkl')
    if settings:
        st.session_state.reklama_values = settings.get('reklama_values', {})
        st.session_state.orders_plan_values = settings.get('orders_plan_values', {})
        st.session_state.sales_plan_values = settings.get('sales_plan_values', {})
        return True
    return False

def load_additional_data(uploaded_file):
    """Загружает дополнительные данные из загруженного файла"""
    try:
        # Определяем тип файла
        if uploaded_file.name.endswith('.xlsx') or uploaded_file.name.endswith('.xls'):
            # Загружаем Excel файл
            try:
                df = pd.read_excel(uploaded_file, sheet_name="Товары", header=[0, 1])
                if isinstance(df.columns, pd.MultiIndex):
                    df.columns = [' '.join(str(col).strip() for col in multi_col if str(col) != 'nan').strip() 
                                 for multi_col in df.columns]
            except:
                df = pd.read_excel(uploaded_file, sheet_name="Товары", header=0)
            
            # Очищаем данные
            for col in df.columns:
                if df[col].dtype == 'object':
                    mask = df[col].astype(str).str.contains('Детальный отчет воронки продаж по карточкам товаров', na=False)
                    if mask.any():
                        df = df[~mask]
                        break
            
            if len(df.columns) > 0:
                first_col = df.columns[0]
                if df[first_col].dtype == 'object':
                    df[first_col] = df[first_col].astype(str).str.replace('Детальный отчет воронки продаж по карточкам товаров', '', regex=False)
            
            return df
        else:
            st.error("Поддерживаются только файлы Excel (.xlsx, .xls)")
            return None
    except Exception as e:
        st.error(f"Ошибка загрузки файла: {e}")
        return None

def merge_dataframes(df1, df2):
    """Объединяет два DataFrame, дополняя данные"""
    try:
        # Находим общие столбцы
        common_cols = list(set(df1.columns) & set(df2.columns))
        
        if not common_cols:
            st.warning("Нет общих столбцов для объединения")
            return df1
        
        # Объединяем по общим столбцам
        merged_df = pd.concat([df1, df2], ignore_index=True)
        
        # Удаляем дубликаты если есть
        if 'Дата' in merged_df.columns:
            merged_df = merged_df.drop_duplicates(subset=['Дата'], keep='last')
        
        return merged_df
    except Exception as e:
        st.error(f"Ошибка объединения данных: {e}")
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
        # Пробуем загрузить с многоуровневыми заголовками
        try:
            df = pd.read_excel(voronka_path, sheet_name="Товары", header=[0, 1])
            
            # Объединяем многоуровневые заголовки
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = [' '.join(str(col).strip() for col in multi_col if str(col) != 'nan').strip() 
                             for multi_col in df.columns]
        except Exception as e:
            # Загружаем с обычными заголовками
            df = pd.read_excel(voronka_path, sheet_name="Товары", header=0)
        
        # Удаляем строки с текстом "Детальный отчет воронки продаж по карточкам товаров"
        for col in df.columns:
            if df[col].dtype == 'object':  # Только для текстовых столбцов
                mask = df[col].astype(str).str.contains('Детальный отчет воронки продаж по карточкам товаров', na=False)
                if mask.any():
                    df = df[~mask]
                    break
        
        # Также очищаем первый столбец от этого текста
        if len(df.columns) > 0:
            first_col = df.columns[0]
            if df[first_col].dtype == 'object':
                # Заменяем текст на пустую строку в первом столбце
                df[first_col] = df[first_col].astype(str).str.replace('Детальный отчет воронки продаж по карточкам товаров', '', regex=False)
        
        return df
        
    except Exception as e:
        st.error(f"❌ Ошибка загрузки файла: {e}")
        return None

# Секция для загрузки дополнительных файлов
st.sidebar.header("📁 Загрузка дополнительных данных")

uploaded_file = st.sidebar.file_uploader(
    "Загрузите дополнительный Excel файл:",
    type=['xlsx', 'xls'],
    help="Файл будет объединен с основными данными (не заменяя их)"
)

# Загружаем основные данные
df = load_voronka_data()

# Если загружен дополнительный файл, объединяем данные
if uploaded_file is not None and df is not None:
    additional_df = load_additional_data(uploaded_file)
    if additional_df is not None:
        df = merge_dataframes(df, additional_df)
        st.sidebar.success(f"✅ Файл {uploaded_file.name} успешно объединен с основными данными!")
        st.sidebar.info(f"📊 Общее количество строк: {len(df)}")
elif uploaded_file is not None and df is None:
    st.sidebar.error("❌ Сначала загрузите основной файл Voronka.xlsx")

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
                    # Создаем более понятный формат дат для недель
                    df.loc[valid_dates, 'Неделя_Год'] = (
                        df.loc[valid_dates, 'Год'].astype(int).astype(str) + '.' + 
                        df.loc[valid_dates, 'Месяц'].astype(int).astype(str) + 
                        ' (нед. ' + df.loc[valid_dates, 'Неделя'].astype(int).astype(str) + ')'
                    )
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
        
        # Группируем по неделям
        agg_dict = {
            orders_col: 'sum',
            sales_col: 'sum'
        }
        
        # Добавляем все найденные столбцы
        if prodazha_col and pd.api.types.is_numeric_dtype(df[prodazha_col]):
            agg_dict[prodazha_col] = 'sum'
        if orders_sum_col and pd.api.types.is_numeric_dtype(df[orders_sum_col]):
            agg_dict[orders_sum_col] = 'sum'
        if sales_sum_col and pd.api.types.is_numeric_dtype(df[sales_sum_col]):
            agg_dict[sales_sum_col] = 'sum'
        if conversion_col and pd.api.types.is_numeric_dtype(df[conversion_col]):
            agg_dict[conversion_col] = 'mean'  # Для процентов используем среднее
        if cart_conversion_col and pd.api.types.is_numeric_dtype(df[cart_conversion_col]):
            agg_dict[cart_conversion_col] = 'mean'  # Для процентов используем среднее
        if cancelled_col and pd.api.types.is_numeric_dtype(df[cancelled_col]):
            agg_dict[cancelled_col] = 'sum'
        if order_conversion_col and pd.api.types.is_numeric_dtype(df[order_conversion_col]):
            agg_dict[order_conversion_col] = 'mean'  # Для процентов используем среднее
        if card_views_col and pd.api.types.is_numeric_dtype(df[card_views_col]):
            agg_dict[card_views_col] = 'sum'
        # Убираем агрегацию для "Отменили" по запросу пользователя
        # if cancelled_wb_col and pd.api.types.is_numeric_dtype(df[cancelled_wb_col]):
        #     agg_dict[cancelled_wb_col] = 'sum'
        
        weekly_data = df.groupby('Неделя_Год').agg(agg_dict).reset_index()
        
        # Сортируем недели по дате (от новых к старым - справа налево)
        # Создаем временную колонку для сортировки по году, месяцу и неделе
        weekly_data['year'] = weekly_data['Неделя_Год'].str.extract(r'(\d{4})').astype(int)
        weekly_data['month'] = weekly_data['Неделя_Год'].str.extract(r'(\d{4})\.(\d+)')[1].astype(int)
        weekly_data['week'] = weekly_data['Неделя_Год'].str.extract(r'нед\. (\d+)').astype(int)
        weekly_data = weekly_data.sort_values(['year', 'month', 'week'], ascending=False).drop(['year', 'month', 'week'], axis=1)
        
        # Создаем сводную таблицу по неделям
        weekly_pivot_data = weekly_data.set_index('Неделя_Год').T
        
        # Создаем сводную таблицу по месяцам
        monthly_data = df.groupby('Месяц_Год').agg(agg_dict).reset_index()
        # Сортируем месяцы
        monthly_data['year'] = monthly_data['Месяц_Год'].str.extract(r'(\d{4})').astype(int)
        monthly_data['month'] = monthly_data['Месяц_Год'].str.extract(r'(\d{4})\.(\d+)')[1].astype(int)
        monthly_data = monthly_data.sort_values(['year', 'month'], ascending=False).drop(['year', 'month'], axis=1)
        monthly_pivot_data = monthly_data.set_index('Месяц_Год').T
        
        # Создаем итоговую таблицу, начиная с недельных данных
        pivot_data = weekly_pivot_data.copy()
        
        # Добавляем месячные столбцы с правильными значениями
        for col in monthly_pivot_data.columns:
            pivot_data[col] = monthly_pivot_data[col]
            
            # Для строк "Реклама", "Заказ план", "Продажа план" - рассчитываем сумму по неделям
            month_weeks = [c for c in pivot_data.columns if c.startswith(col + ' (')]
            
            # Реклама - сумма по неделям
            if "Реклама" in pivot_data.index:
                reklama_total = sum(st.session_state.get('reklama_values', {}).get(week, 0.0) for week in month_weeks)
                pivot_data.loc["Реклама", col] = reklama_total
            
            # Заказ план - сумма по неделям
            if "Заказ план" in pivot_data.index:
                orders_plan_total = sum(st.session_state.get('orders_plan_values', {}).get(week, 0.0) for week in month_weeks)
                pivot_data.loc["Заказ план", col] = orders_plan_total
            
            # Продажа план - сумма по неделям
            if "Продажа план" in pivot_data.index:
                sales_plan_total = sum(st.session_state.get('sales_plan_values', {}).get(week, 0.0) for week in month_weeks)
                pivot_data.loc["Продажа план", col] = sales_plan_total
        
        # Добавляем столбец "Общие по месяцам"
        pivot_data["Общие по месяцам"] = 0.0
        
        # Создаем правильный порядок столбцов: месячный столбец перед недельными того же месяца
        final_columns = []
        
        # Получаем уникальные месяцы из недельных данных
        weekly_months = set()
        for col in weekly_pivot_data.columns:
            if '(' in col and 'нед.' in col:
                # Извлекаем месяц из формата "2024.01 (нед. 01)"
                month_part = col.split(' (')[0]  # "2024.01"
                weekly_months.add(month_part)
        
        # Добавляем месяцы из monthly_pivot_data, которых может не быть в недельных данных
        for col in monthly_pivot_data.columns:
            if col not in weekly_months:
                weekly_months.add(col)
        
        # Сортируем месяцы по убыванию
        sorted_months = sorted(weekly_months, key=lambda x: (int(x.split('.')[0]), int(x.split('.')[1])), reverse=True)
        
        # Создаем правильный порядок столбцов: недели месяца, затем месячный столбец
        for month in sorted_months:
            # Добавляем недельные столбцы этого месяца
            month_weeks = [col for col in pivot_data.columns if col.startswith(month + ' (')]
            # Сортируем недели по убыванию
            month_weeks.sort(key=lambda x: int(x.split('нед. ')[1].split(')')[0]), reverse=True)
            final_columns.extend(month_weeks)
            
            # Добавляем месячный столбец после недель
            if month in pivot_data.columns:
                final_columns.append(month)
        
        # Добавляем столбец "Общие по месяцам" в конец
        final_columns.append("Общие по месяцам")
        
        # Убеждаемся, что все столбцы из pivot_data включены в final_columns
        for col in pivot_data.columns:
            if col not in final_columns:
                final_columns.append(col)
        
        # Переупорядочиваем DataFrame
        pivot_data = pivot_data[final_columns]
        
        # Обновляем индексы для отображения и очищаем от лишнего текста
        index_names = []
        
        # Функция для очистки названий от лишнего текста
        def clean_column_name(name):
            if name:
                # Убираем "Детальный отчет воронки продаж по карточкам товаров" из начала
                cleaned = str(name).replace('Детальный отчет воронки продаж по карточкам товаров', '').strip()
                # Убираем лишние пробелы и переносы строк
                cleaned = ' '.join(cleaned.split())
                return cleaned if cleaned else name
            return name
        
        # Создаем список названий индексов в правильном порядке
        index_names = []
        
        if orders_col:
            index_names.append(clean_column_name(orders_col))
        
        if sales_col:
            index_names.append(clean_column_name(sales_col))
        
        if prodazha_col and pd.api.types.is_numeric_dtype(df[prodazha_col]):
            index_names.append(clean_column_name(prodazha_col))
        if orders_sum_col and pd.api.types.is_numeric_dtype(df[orders_sum_col]):
            index_names.append(clean_column_name(orders_sum_col))
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
        # Убираем строку "Отменили" по запросу пользователя
        # if cancelled_wb_col and pd.api.types.is_numeric_dtype(df[cancelled_wb_col]):
        #     index_names.append("Отменили, шт")
        
        # Добавляем названия для новых строк
        index_names.extend(["Средняя цена", "Реклама", "ДРР", "Заказ план", "Продажа план"])
        
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
        
        # Создаем строки в правильном порядке согласно index_names
        for idx_name in index_names:
            if idx_name == "Средняя цена":
                row = pd.Series([0.0] * len(pivot_data.columns), index=pivot_data.columns)
                row.name = "Средняя цена"
                additional_rows.append(row.to_frame().T)
            elif idx_name == "Реклама":
                # Загружаем значения из session state
                values = []
                for col in pivot_data.columns:
                    if col == "Общие по месяцам":
                        values.append(0.0)  # Будет рассчитано позже
                    elif col.startswith(("2024.", "2023.", "2022.", "2025.")) and '(' not in col:
                        # Месячные столбцы уже рассчитаны выше
                        values.append(0.0)  # Будет перезаписано позже
                    else:
                        values.append(st.session_state.reklama_values.get(col, 0.0))
                row = pd.Series(values, index=pivot_data.columns)
                row.name = "Реклама"
                additional_rows.append(row.to_frame().T)
            elif idx_name == "ДРР":
                row = pd.Series([0.0] * len(pivot_data.columns), index=pivot_data.columns)
                row.name = "ДРР"
                additional_rows.append(row.to_frame().T)
            elif idx_name == "Заказ план":
                # Загружаем значения из session state
                values = []
                for col in pivot_data.columns:
                    if col == "Общие по месяцам":
                        values.append(0.0)  # Будет рассчитано позже
                    elif col.startswith(("2024.", "2023.", "2022.", "2025.")) and '(' not in col:
                        # Месячные столбцы уже рассчитаны выше
                        values.append(0.0)  # Будет перезаписано позже
                    else:
                        values.append(st.session_state.orders_plan_values.get(col, 0.0))
                row = pd.Series(values, index=pivot_data.columns)
                row.name = "Заказ план"
                additional_rows.append(row.to_frame().T)
            elif idx_name == "Продажа план":
                # Загружаем значения из session state
                values = []
                for col in pivot_data.columns:
                    if col == "Общие по месяцам":
                        values.append(0.0)  # Будет рассчитано позже
                    elif col.startswith(("2024.", "2023.", "2022.", "2025.")) and '(' not in col:
                        # Месячные столбцы уже рассчитаны выше
                        values.append(0.0)  # Будет перезаписано позже
                    else:
                        values.append(st.session_state.sales_plan_values.get(col, 0.0))
                row = pd.Series(values, index=pivot_data.columns)
                row.name = "Продажа план"
                additional_rows.append(row.to_frame().T)
        
        # Добавляем строки в таблицу в правильном порядке
        if additional_rows:
            pivot_data = pd.concat([pivot_data] + additional_rows)
        
        # Теперь устанавливаем правильные названия индексов
        pivot_data.index = index_names
        
        # Перезаписываем месячные значения для строк "Реклама", "Заказ план", "Продажа план"
        for col in pivot_data.columns:
            if col.startswith(("2024.", "2023.", "2022.", "2025.")) and '(' not in col:
                month_weeks = [c for c in pivot_data.columns if c.startswith(col + ' (')]
                
                # Реклама - сумма по неделям
                if "Реклама" in pivot_data.index:
                    reklama_total = sum(st.session_state.get('reklama_values', {}).get(week, 0.0) for week in month_weeks)
                    pivot_data.loc["Реклама", col] = reklama_total
                
                # Заказ план - сумма по неделям
                if "Заказ план" in pivot_data.index:
                    orders_plan_total = sum(st.session_state.get('orders_plan_values', {}).get(week, 0.0) for week in month_weeks)
                    pivot_data.loc["Заказ план", col] = orders_plan_total
                
                # Продажа план - сумма по неделям
                if "Продажа план" in pivot_data.index:
                    sales_plan_total = sum(st.session_state.get('sales_plan_values', {}).get(week, 0.0) for week in month_weeks)
                    pivot_data.loc["Продажа план", col] = sales_plan_total
        
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
                    except:
                        pivot_data.loc["Средняя цена", col] = 0
        
        # Рассчитываем ДРР: Реклама / Заказали на сумму
        if orders_sum_col:
            orders_sum_col_clean = clean_column_name(orders_sum_col)
            if orders_sum_col_clean in pivot_data.index:
                for col in pivot_data.columns:
                    try:
                        orders_sum_value = pivot_data.loc[orders_sum_col_clean, col]
                        # Для недельных столбцов используем session state, для месячных - среднее
                        if col.startswith(("2024.", "2023.", "2022.", "2025.")) and '(' not in col:
                            # Месячные столбцы - среднее ДРР по неделям этого месяца
                            month_weeks = [c for c in pivot_data.columns if c.startswith(col + ' (')]
                            drr_values = []
                            for week_col in month_weeks:
                                reklama_value = st.session_state.reklama_values.get(week_col, 0.0)
                                week_orders_sum = pivot_data.loc[orders_sum_col_clean, week_col]
                                if pd.notna(week_orders_sum) and week_orders_sum > 0 and reklama_value > 0:
                                    drr_values.append(reklama_value / week_orders_sum)
                            if drr_values:
                                pivot_data.loc["ДРР", col] = sum(drr_values) / len(drr_values)
                            else:
                                pivot_data.loc["ДРР", col] = 0.0
                        else:
                            # Недельные столбцы
                            reklama_value = st.session_state.reklama_values.get(col, 0.0)
                            if pd.notna(orders_sum_value) and orders_sum_value > 0 and reklama_value > 0:
                                pivot_data.loc["ДРР", col] = reklama_value / orders_sum_value
                            else:
                                pivot_data.loc["ДРР", col] = 0.0
                    except:
                        pivot_data.loc["ДРР", col] = 0.0
        
        # Рассчитываем общие значения по месяцам для каждой строки
        for idx in pivot_data.index:
            if idx == "ДРР":
                # Для ДРР - среднее арифметическое по месяцам
                values = []
                for col in monthly_pivot_data.columns:
                    if col in pivot_data.columns:
                        val = pivot_data.loc[idx, col]
                        if pd.notna(val) and val != 0:
                            values.append(val)
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
            elif idx in ["Средняя цена", "Процент выкупа", "Конверсия в корзину, %", "Конверсия в заказ, %"]:
                # Для процентных показателей - среднее арифметическое по месяцам
                values = []
                for col in monthly_pivot_data.columns:
                    if col in pivot_data.columns:
                        val = pivot_data.loc[idx, col]
                        if pd.notna(val) and val != 0:
                            values.append(val)
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
                if pd.isna(value) or value is None:
                    return ''
                if isinstance(value, (int, float)):
                    if value % 1 == 0:  # Целое число
                        return f'{int(value):,}'.replace(',', ' ')
                    else:  # Дробное число
                        return f'{value:,.2f}'.replace(',', ' ')
                return str(value)
            except:
                return str(value)
        
        # Применяем форматирование к числовым данным
        formatted_data = pivot_data.copy()
        for col in formatted_data.columns:
            for idx in formatted_data.index:
                if idx not in ['Реклама', 'ДРР', 'Средняя цена', 'Заказ план', 'Продажа план']:  # Не форматируем эти строки
                    formatted_data.loc[idx, col] = format_number(formatted_data.loc[idx, col])
                elif idx == 'ДРР':  # Для ДРР используем специальное форматирование
                    if pd.notna(formatted_data.loc[idx, col]) and formatted_data.loc[idx, col] != 0:
                        formatted_data.loc[idx, col] = f'{formatted_data.loc[idx, col]:.2f}'
                    else:
                        formatted_data.loc[idx, col] = '0.00'
                elif idx == 'Средняя цена':  # Для средней цены используем форматирование с 2 знаками
                    if pd.notna(formatted_data.loc[idx, col]) and formatted_data.loc[idx, col] != 0:
                        formatted_data.loc[idx, col] = f'{formatted_data.loc[idx, col]:.2f}'
                    else:
                        formatted_data.loc[idx, col] = '0.00'
                elif idx == 'Реклама':  # Для рекламы используем форматирование с пробелами
                    if pd.notna(formatted_data.loc[idx, col]) and formatted_data.loc[idx, col] != 0:
                        formatted_data.loc[idx, col] = f'{int(formatted_data.loc[idx, col]):,}'.replace(',', ' ')
                    else:
                        formatted_data.loc[idx, col] = '0'
                elif idx in ['Заказ план', 'Продажа план']:  # Для планов показываем 0 или "нет данных"
                    if pd.notna(formatted_data.loc[idx, col]) and formatted_data.loc[idx, col] != 0:
                        formatted_data.loc[idx, col] = f'{int(formatted_data.loc[idx, col]):,}'.replace(',', ' ')
                    else:
                        formatted_data.loc[idx, col] = '0'
        
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
        
        # Добавляем выделение месячных столбцов
        def highlight_monthly_columns(df):
            """Функция для выделения месячных столбцов цветом"""
            styles = pd.DataFrame('', index=df.index, columns=df.columns)
            for col in df.columns:
                # Проверяем, является ли столбец месячным (формат YYYY.MM без скобок)
                if (col.startswith(("2024.", "2023.", "2022.", "2025.")) and 
                    '(' not in col and 
                    col != "Общие по месяцам"):
                    styles[col] = 'background-color: rgba(255, 193, 7, 0.3)'  # Желтый цвет для месячных столбцов
            return styles
        
        # Применяем выделение месячных столбцов
        styled_data = styled_data.apply(highlight_monthly_columns, axis=None)
        
        st.dataframe(styled_data, width='stretch', height=600)
        
        # Session state уже инициализирован выше
        
        # Добавляем интерфейс для ввода рекламы под таблицу
        st.subheader("💰 Настройка рекламы по неделям")
        
        # Выпадающий список для выбора недели (текущая неделя по умолчанию)
        current_week = list(pivot_data.columns)[0] if len(pivot_data.columns) > 0 else None
        selected_week = st.selectbox(
            "Выберите неделю для настройки рекламы:",
            options=list(pivot_data.columns),
            index=0 if current_week else 0,
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
            st.rerun()
        
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
                    st.rerun()
                else:
                    st.warning("Кеш не найден или пуст")
        
        # Session state для планов уже инициализирован выше
        
        # Добавляем интерфейс для редактирования планов
        st.subheader("📋 Настройка планов по неделям")
        
        # Выпадающий список для выбора недели (текущая неделя по умолчанию)
        selected_plan_week = st.selectbox(
            "Выберите неделю для настройки планов:",
            options=list(pivot_data.columns),
            index=0,
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
        
        with col2:
            current_sales_plan = st.session_state.sales_plan_values.get(selected_plan_week, 0.0)
            sales_plan_value = st.number_input(
                f"Продажа план для {selected_plan_week}:",
                min_value=0.0,
                value=current_sales_plan,
                step=1.0,
                help="План по продажам для выбранной недели"
            )
        
        # Обновляем session state при изменении значений
        if orders_plan_value != current_orders_plan:
            st.session_state.orders_plan_values[selected_plan_week] = orders_plan_value
            save_settings_to_cache()  # Автоматически сохраняем в кеш
            st.rerun()
            
        if sales_plan_value != current_sales_plan:
            st.session_state.sales_plan_values[selected_plan_week] = sales_plan_value
            save_settings_to_cache()  # Автоматически сохраняем в кеш
            st.rerun()
        
    else:
        st.error("❌ Не удалось определить столбцы для анализа.")

else:
    st.error("❌ Не удалось загрузить данные. Проверьте наличие файла Voronka.xlsx в корневой папке проекта.")
