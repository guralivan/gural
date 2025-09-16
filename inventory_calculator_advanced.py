import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import warnings
import os
import json
from pathlib import Path
warnings.filterwarnings('ignore')

# Создаем папку для сохранения данных
SAVE_DIR = Path("saved_products")
SAVE_DIR.mkdir(exist_ok=True)

@st.cache_data
def load_saved_products():
    """Загрузка сохраненных товаров"""
    products = {}
    if SAVE_DIR.exists():
        for file_path in SAVE_DIR.glob("*.json"):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    product_data = json.load(f)
                    products[file_path.stem] = product_data
            except Exception as e:
                st.error(f"Ошибка загрузки файла {file_path}: {e}")
    return products

def save_product(product_name, data):
    """Сохранение товара"""
    try:
        file_path = SAVE_DIR / f"{product_name}.json"
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        st.error(f"Ошибка сохранения: {e}")
        return False

def delete_product(product_name):
    """Удаление товара"""
    try:
        file_path = SAVE_DIR / f"{product_name}.json"
        if file_path.exists():
            file_path.unlink()
            return True
    except Exception as e:
        st.error(f"Ошибка удаления: {e}")
    return False

# Настройка страницы
st.set_page_config(
    page_title="Расширенный калькулятор остатков",
    page_icon="📦",
    layout="wide"
)

# Заголовок
st.title("📦 Расширенный калькулятор остатков товара - максимальная распродажа")
st.markdown("---")

@st.cache_data
def load_data(file_path):
    """Загрузка данных из Excel файла"""
    try:
        excel_file = pd.ExcelFile(file_path)
        sheets = excel_file.sheet_names
        
        data = {}
        for sheet in sheets:
            df = pd.read_excel(file_path, sheet_name=sheet)
            data[sheet] = df
            
        return data, sheets
    except Exception as e:
        st.error(f"Ошибка при загрузке файла: {e}")
        return None, []

def analyze_data_structure(df):
    """Анализ структуры данных для автоматического определения колонок"""
    
    # Ищем колонки с месяцами
    month_columns = []
    numeric_columns = []
    
    for col in df.columns:
        col_str = str(col).lower()
        
        # Проверяем на месяцы
        months = ['январь', 'февраль', 'март', 'апрель', 'май', 'июнь',
                 'июль', 'август', 'сентябрь', 'октябрь', 'ноябрь', 'декабрь',
                 'jan', 'feb', 'mar', 'apr', 'may', 'jun',
                 'jul', 'aug', 'sep', 'oct', 'nov', 'dec']
        
        if any(month in col_str for month in months):
            month_columns.append(col)
        
        # Проверяем на числовые данные
        if df[col].dtype in ['int64', 'float64']:
            numeric_columns.append(col)
    
    return month_columns, numeric_columns

def extract_monthly_data(df, selected_columns):
    """Извлечение месячных данных из выбранных колонок"""
    
    monthly_data = {}
    
    for col in selected_columns:
        # Пытаемся определить месяц из названия колонки
        col_str = str(col).lower()
        
        month_mapping = {
            'январь': 'Январь', 'jan': 'Январь', 'january': 'Январь',
            'февраль': 'Февраль', 'feb': 'Февраль', 'february': 'Февраль',
            'март': 'Март', 'mar': 'Март', 'march': 'Март',
            'апрель': 'Апрель', 'apr': 'Апрель', 'april': 'Апрель',
            'май': 'Май', 'may': 'Май',
            'июнь': 'Июнь', 'jun': 'Июнь', 'june': 'Июнь',
            'июль': 'Июль', 'jul': 'Июль', 'july': 'Июль',
            'август': 'Август', 'aug': 'Август', 'august': 'Август',
            'сентябрь': 'Сентябрь', 'sep': 'Сентябрь', 'september': 'Сентябрь',
            'октябрь': 'Октябрь', 'oct': 'Октябрь', 'october': 'Октябрь',
            'ноябрь': 'Ноябрь', 'nov': 'Ноябрь', 'november': 'Ноябрь',
            'декабрь': 'Декабрь', 'dec': 'Декабрь', 'december': 'Декабрь'
        }
        
        month_name = None
        for key, value in month_mapping.items():
            if key in col_str:
                month_name = value
                break
        
        if month_name:
            # Берем среднее значение по колонке (если несколько строк)
            value = df[col].mean()
            if not pd.isna(value):
                monthly_data[month_name] = int(value)
    
    return monthly_data

def calculate_inventory_needs(monthly_orders, buyback_rate, initial_stock=0, return_days=7, safety_stock=0.1, monthly_undelivered=None):
    """Расчет единовременной закупки товара для максимальной распродажи с минимальным остатком"""
    
    results = {}
    total_orders = sum(monthly_orders.values())
    
    # НОВАЯ ЛОГИКА: Недоставка создает контролируемый недостаток, а не влияет на общий объем заказов
    total_actual_orders = total_orders  # Используем полные заказы
    
    # НОВАЯ ЛОГИКА: Рассчитываем закупку для максимальной распродажи
    
    # Анализируем месяцы по порядку и рассчитываем минимально необходимый запас
    months_list = list(monthly_orders.keys())
    
    # Рассчитываем общий объем заказов и возвратов
    total_returns = total_actual_orders * (1 - buyback_rate)
    
    # Закупка = общий объем заказов - общий объем возвратов - начальный остаток + минимальный страховой запас
    # Цель: распродать максимально товар и оставить минимальный остаток
    net_required = total_actual_orders - total_returns - initial_stock
    
    if safety_stock == 0:
        # При нулевом страховом запасе закупаем точно по чистой потребности
        total_initial_purchase = max(0, net_required)
    else:
        # При наличии страхового запаса добавляем минимальную долю
        total_initial_purchase = max(0, net_required) + (max(0, net_required) * safety_stock * 0.05)
    
    # Теперь моделируем продажи с рассчитанной закупкой + начальный остаток
    warehouse_stock = total_initial_purchase + initial_stock
    
    for month, orders in monthly_orders.items():
        # НОВАЯ ЛОГИКА: Лимит недостатка товара в процентах от заказов
        shortage_limit_percent = monthly_undelivered.get(month, 0) if monthly_undelivered else 0
        max_allowed_shortage = orders * shortage_limit_percent  # Максимально допустимый недостаток в штуках
        
        # Продаем товар с учетом лимита недостатка
        if warehouse_stock >= orders:
            # Товара достаточно - продаем полные заказы
            sold_from_warehouse = orders
            stock_shortage = 0
        else:
            # Товара недостаточно - продаем доступный товар
            sold_from_warehouse = warehouse_stock
            stock_shortage = orders - warehouse_stock
        
        # Применяем лимит недостатка товара
        if stock_shortage > max_allowed_shortage:
            # Если недостаток превышает лимит, ограничиваем его
            stock_shortage = max_allowed_shortage
        
        # Общий недостаток = недостаток из-за отсутствия товара (ограниченный лимитом)
        total_shortage = stock_shortage
        
        # Товар, который будет возвращен в этом месяце
        returns_this_month = sold_from_warehouse * (1 - buyback_rate)
        
        # Товар, который выкупается (не возвращается)
        buyback_quantity = sold_from_warehouse * buyback_rate
        
        # Возвращается на склад
        returns_to_warehouse = returns_this_month
        
        # Обновляем остаток на складе
        warehouse_stock = warehouse_stock - sold_from_warehouse + returns_to_warehouse
        
        # Расчет KPI
        utilization_rate = (buyback_quantity / sold_from_warehouse * 100) if sold_from_warehouse > 0 else 0
        return_rate = (returns_this_month / sold_from_warehouse * 100) if sold_from_warehouse > 0 else 0
        
        results[month] = {
            'orders': orders,
            'sold_from_warehouse': sold_from_warehouse,
            'shortage': total_shortage,  # Недостаток товара (ограниченный лимитом)
            'returns_this_month': returns_this_month,
            'returns_to_warehouse': returns_to_warehouse,
            'buyback_quantity': buyback_quantity,
            'warehouse_stock': warehouse_stock,
            'utilization_rate': utilization_rate,
            'return_rate': return_rate,
            'total_initial_purchase': total_initial_purchase if month == list(monthly_orders.keys())[0] else 0
        }
    
    return results

def create_advanced_visualizations(results, buyback_rate, monthly_orders):
    """Создание расширенных визуализаций с новыми KPI"""
    
    months = list(results.keys())
    orders = [results[m]['orders'] for m in months]
    sold_from_warehouse = [results[m]['sold_from_warehouse'] for m in months]
    shortage = [results[m]['shortage'] for m in months]
    returns = [results[m]['returns_this_month'] for m in months]
    returns_to_warehouse = [results[m]['returns_to_warehouse'] for m in months]
    warehouse_stock = [results[m]['warehouse_stock'] for m in months]
    buyback_quantity = [results[m]['buyback_quantity'] for m in months]
    utilization_rate = [results[m]['utilization_rate'] for m in months]
    
    # График 1: Сравнение заказов и продаж (максимальная распродажа)
    fig1 = go.Figure()
    fig1.add_trace(go.Bar(name='Заказы', x=months, y=orders, marker_color='blue', opacity=0.8))
    fig1.add_trace(go.Bar(name='Продано со склада', x=months, y=sold_from_warehouse, marker_color='green', opacity=0.8))
    fig1.add_trace(go.Bar(name='Недостаток товара', x=months, y=shortage, marker_color='red', opacity=0.8))
    fig1.update_layout(
        title=f'Сравнение заказов и продаж - максимальная распродажа (Выкуп: {buyback_rate*100}%)',
        xaxis_title='Месяц',
        yaxis_title='Количество',
        barmode='group',
        height=500
    )
    
    # График 2: Динамика возвратов и остатков на складе
    fig2 = go.Figure()
    fig2.add_trace(go.Bar(name='Возвраты за месяц', x=months, y=returns, marker_color='orange'))
    fig2.add_trace(go.Bar(name='Возвращается на склад', x=months, y=returns_to_warehouse, marker_color='lightgreen'))
    fig2.add_trace(go.Scatter(name='Остаток на складе', x=months, y=warehouse_stock, 
                             mode='lines+markers', line=dict(color='purple', width=3)))
    fig2.update_layout(
        title='Динамика возвратов и остатков на складе',
        xaxis_title='Месяц',
        yaxis_title='Количество',
        height=500
    )
    
    # График 3: Эффективность использования возвратов
    efficiency = []
    for m in months:
        if results[m]['orders'] > 0:
            # Эффективность = (выкупленный товар / проданный товар) * 100
            eff = (results[m]['buyback_quantity'] / results[m]['sold_from_warehouse']) * 100 if results[m]['sold_from_warehouse'] > 0 else 0
            efficiency.append(eff)
        else:
            efficiency.append(0)
    
    fig3 = go.Figure()
    fig3.add_trace(go.Bar(name='Эффективность использования возвратов (%)', 
                          x=months, y=efficiency, marker_color='purple'))
    fig3.update_layout(
        title='Эффективность выкупа товара',
        xaxis_title='Месяц',
        yaxis_title='Процент выкупа',
        height=500
    )
    
    # График 4: Остатки на складе и выкуп
    fig4 = go.Figure()
    fig4.add_trace(go.Bar(name='Остаток на складе', x=months, y=warehouse_stock, marker_color='green'))
    fig4.add_trace(go.Scatter(name='Выкуплено товара', x=months, y=buyback_quantity, 
                             mode='lines+markers', line=dict(color='purple', width=3)))
    fig4.update_layout(
        title='Остатки на складе и выкуп товара',
        xaxis_title='Месяц',
        yaxis_title='Количество',
        height=500
    )
    
    # График 5: KPI показатели
    fig5 = go.Figure()
    fig5.add_trace(go.Bar(name='Процент использования', x=months, y=utilization_rate, marker_color='blue'))
    fig5.add_trace(go.Bar(name='Процент возвратов', x=months, y=[results[m]['return_rate'] for m in months], marker_color='red'))
    fig5.update_layout(
        title='KPI показатели по месяцам',
        xaxis_title='Месяц',
        yaxis_title='Процент',
        barmode='group',
        height=500
    )
    
    # График 6: Сезонность спроса
    fig6 = go.Figure()
    fig6.add_trace(go.Scatter(name='Заказы', x=months, y=orders, 
                             mode='lines+markers', line=dict(color='blue', width=3)))
    fig6.update_layout(
        title='Сезонность спроса',
        xaxis_title='Месяц',
        yaxis_title='Количество заказов',
        height=500
    )
    
    return fig1, fig2, fig3, fig4, fig5, fig6

def calculate_weekly_inventory(monthly_orders, buyback_rate, return_days=7, safety_stock=0.1):
    """Расчет еженедельного инвентаря на основе месячных заказов"""
    
    weekly_results = {}
    
    # Преобразуем месячные заказы в еженедельные (примерно 4.33 недели в месяце)
    weeks_per_month = 4.33
    
    for month, orders in monthly_orders.items():
        weekly_orders = orders / weeks_per_month
        
        for week in range(1, 5):  # 4 недели в месяце
            week_key = f"{month} - Неделя {week}"
            
            # Распределяем заказы по неделям (можно настроить неравномерно)
            if week == 1:
                week_orders = weekly_orders * 1.2  # Первая неделя - больше заказов
            elif week == 4:
                week_orders = weekly_orders * 0.8  # Последняя неделя - меньше заказов
            else:
                week_orders = weekly_orders
            
            # Расчет для недели
            sold_from_warehouse = week_orders
            returns_this_week = sold_from_warehouse * (1 - buyback_rate)
            buyback_quantity = sold_from_warehouse * buyback_rate
            returns_to_warehouse = returns_this_week
            
            weekly_results[week_key] = {
                'orders': week_orders,
                'sold_from_warehouse': sold_from_warehouse,
                'returns_this_week': returns_this_week,
                'returns_to_warehouse': returns_to_warehouse,
                'buyback_quantity': buyback_quantity,
                'utilization_rate': (buyback_quantity / sold_from_warehouse * 100) if sold_from_warehouse > 0 else 0,
                'return_rate': (returns_this_week / sold_from_warehouse * 100) if sold_from_warehouse > 0 else 0
            }
    
    return weekly_results

def calculate_seasonal_kpi(monthly_orders, season_months):
    """Расчет KPI для конкретного сезона"""
    
    season_orders = {month: monthly_orders.get(month, 0) for month in season_months}
    total_orders = sum(season_orders.values())
    
    if total_orders == 0:
        return {
            'total_orders': 0,
            'avg_orders_per_month': 0,
            'peak_month': None,
            'low_month': None,
            'seasonal_variance': 0
        }
    
    # Средние заказы в месяц
    avg_orders_per_month = total_orders / len(season_months)
    
    # Пиковый и минимальный месяцы
    peak_month = max(season_orders, key=season_orders.get)
    low_month = min(season_orders, key=season_orders.get)
    
    # Дисперсия сезонности
    variance = sum((orders - avg_orders_per_month) ** 2 for orders in season_orders.values()) / len(season_months)
    seasonal_variance = (variance ** 0.5) / avg_orders_per_month * 100 if avg_orders_per_month > 0 else 0
    
    return {
        'total_orders': total_orders,
        'avg_orders_per_month': avg_orders_per_month,
        'peak_month': peak_month,
        'low_month': low_month,
        'seasonal_variance': seasonal_variance
    }

def main():
    # Боковая панель
    st.sidebar.header("⚙️ Параметры расчета")
    
    # Загрузка сохраненных товаров
    saved_products = load_saved_products()
    
    # Управление сохраненными товарами
    st.sidebar.subheader("💾 Сохраненные товары")
    
    if saved_products:
        selected_product = st.sidebar.selectbox(
            "Выберите сохраненный товар:",
            ["Новый товар"] + list(saved_products.keys())
        )
        
        if selected_product != "Новый товар":
            product_data = saved_products[selected_product]
            st.sidebar.success(f"Загружен товар: {selected_product}")
            
            # Кнопка удаления
            if st.sidebar.button("🗑️ Удалить товар"):
                if delete_product(selected_product):
                    st.sidebar.success("Товар удален!")
                    st.rerun()
    else:
        selected_product = "Новый товар"
        st.sidebar.info("Нет сохраненных товаров")
    
    # Параметры
    buyback_rate = st.sidebar.slider(
        "Процент выкупа товара (%)", 
        min_value=0, 
        max_value=100, 
        value=20, 
        step=5
    ) / 100
    
    return_days = st.sidebar.number_input(
        "Дни возврата товара", 
        min_value=1, 
        max_value=30, 
        value=7
    )
    
    safety_stock = st.sidebar.slider(
        "Страховой запас (%)", 
        min_value=0, 
        max_value=50, 
        value=0, 
        step=1
    ) / 100
    
    # Дополнительная опция для минимального остатка
    zero_safety_stock = st.sidebar.checkbox(
        "Нулевой страховой запас (минимальный остаток)",
        value=False,
        help="Если включено, страховой запас будет установлен в 0%"
    )
    
    if zero_safety_stock:
        safety_stock = 0
    
    # Основной контент
    st.subheader("📝 Ввод данных о заказах")
    st.info("Введите количество заказов по месяцам для расчета необходимых остатков товара")
    
    # Загрузка данных из сохраненного товара
    if selected_product != "Новый товар" and selected_product in saved_products:
        product_data = saved_products[selected_product]
        st.success(f"📦 Загружены данные товара: {selected_product}")
        
        # Автоматически заполняем параметры
        if 'buyback_rate' in product_data:
            buyback_rate = product_data['buyback_rate']
        if 'return_days' in product_data:
            return_days = product_data['return_days']
        if 'safety_stock' in product_data:
            safety_stock = product_data['safety_stock']
        if 'initial_stock' in product_data:
            initial_stock = product_data['initial_stock']
        if 'monthly_undelivered' in product_data:
            monthly_undelivered = product_data['monthly_undelivered']
    
    st.write("**Введите данные:**")
    
    # Поле для остатка на начало
    initial_stock = st.number_input(
        "Остаток на начало (шт.):",
        min_value=0,
        value=0,
        help="Начальный остаток товара на складе"
    )
    
    st.write("**Введите заказы по месяцам:**")
    
    col1, col2, col3, col4 = st.columns(4)
    
    monthly_orders = {}
    monthly_undelivered = {}
    months = ['Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь',
            'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь']
    
    for i, month in enumerate(months):
        with col1 if i < 3 else col2 if i < 6 else col3 if i < 9 else col4:
            # Загружаем сохраненные значения или используем 0 по умолчанию
            saved_order = monthly_orders.get(month, 0) if 'monthly_orders' in locals() else 0
            saved_undelivered = monthly_undelivered.get(month, 0) * 100 if 'monthly_undelivered' in locals() else 0.0
            
            value = st.number_input(
                f"{month} (заказы):", 
                min_value=0, 
                value=saved_order,
                key=f"month_{i}"
            )
            monthly_orders[month] = value
            
            shortage_limit = st.number_input(
                f"{month} (% лимит недостатка):", 
                min_value=0.0, 
                max_value=100.0,
                value=float(saved_undelivered),
                step=0.1,
                key=f"shortage_limit_{i}",
                help="Максимально допустимый недостаток товара в процентах от заказов"
            )
            monthly_undelivered[month] = shortage_limit / 100.0  # Сохраняем как дробь
    
    # Автоматический расчет при изменении любого параметра
    if sum(monthly_orders.values()) > 0:  # Только если есть заказы
        # Расчет остатков
        results = calculate_inventory_needs(
            monthly_orders, 
            buyback_rate, 
            initial_stock,
            return_days, 
            safety_stock,
            monthly_undelivered
        )
        
        # Результаты
        st.subheader("📈 Результаты расчета")
        
        # Таблица результатов с русскими заголовками
        results_df = pd.DataFrame(results).T
        results_df = results_df.round(0)  # Округляем до целых чисел
        
        # Переименовываем колонки на русский язык
        results_df.columns = [
            'Заказы',
            'Продано со склада',
            'Недостаток товара',
            'Возвраты за месяц',
            'Возвращается на склад',
            'Выкуплено товара',
            'Товар на складе',
            'Процент использования',
            'Процент возвратов',
            'Единовременная закупка'
        ]
        
        # Исправляем отображение данных
        st.dataframe(results_df, width='stretch')
        
        # Суммарная статистика
        total_orders = sum(monthly_orders.values())
        total_sold = sum(results[m]['sold_from_warehouse'] for m in results)
        total_shortage = sum(results[m]['shortage'] for m in results)
        total_returns = sum(results[m]['returns_this_month'] for m in results)
        total_buyback = sum(results[m]['buyback_quantity'] for m in results)
        total_initial_purchase = results[list(results.keys())[0]]['total_initial_purchase']
        final_warehouse_stock = results[list(results.keys())[-1]]['warehouse_stock']
        
        # Расчет расширенных KPI
        overall_utilization = (total_buyback / total_sold * 100) if total_sold > 0 else 0
        overall_return_rate = (total_returns / total_sold * 100) if total_sold > 0 else 0
        efficiency = (total_buyback / total_initial_purchase * 100) if total_initial_purchase > 0 else 0
        avg_monthly_orders = total_orders / len(monthly_orders) if monthly_orders else 0
        avg_monthly_sold = total_sold / len(monthly_orders) if monthly_orders else 0
        
        # Основные метрики
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Общий объем заказов", f"{total_orders:,.0f} шт.")
        with col2:
            st.metric("Единовременная закупка", f"{total_initial_purchase:,.0f} шт.")
        with col3:
            st.metric("Общий объем продаж", f"{total_sold:,.0f} шт.")
        with col4:
            st.metric("Недостаток товара", f"{total_shortage:,.0f} шт.")
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Остаток на складе", f"{final_warehouse_stock:,.0f} шт.")
        with col2:
            st.metric("Общий объем возвратов", f"{total_returns:,.0f} шт.")
        with col3:
            st.metric("Процент покрытия", f"{(initial_stock/total_initial_purchase*100):.1f}%" if total_initial_purchase > 0 else "0%")
        with col4:
            st.metric("Эффективность закупки", f"{(total_buyback/total_initial_purchase*100):.1f}%" if total_initial_purchase > 0 else "0%")
        
        # Расширенные KPI
        st.subheader("📊 Расширенные KPI")
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            st.metric("Процент использования", f"{overall_utilization:.1f}%")
        with col2:
            st.metric("Процент возвратов", f"{overall_return_rate:.1f}%")
        with col3:
            st.metric("Эффективность (%)", f"{efficiency:.1f}%")
        with col4:
            st.metric("Средний заказ/мес", f"{avg_monthly_orders:.0f} шт.")
        with col5:
            st.metric("Средняя продажа/мес", f"{avg_monthly_sold:.0f} шт.")
        

        
        # Визуализации
        st.subheader("📊 Визуализация результатов")
        
        fig1, fig2, fig3, fig4, fig5, fig6 = create_advanced_visualizations(results, buyback_rate, monthly_orders)
        
        col1, col2 = st.columns(2)
        with col1:
            st.plotly_chart(fig1, width='stretch')
        with col2:
            st.plotly_chart(fig2, width='stretch')
        
        col1, col2 = st.columns(2)
        with col1:
            st.plotly_chart(fig3, width='stretch')
        with col2:
            st.plotly_chart(fig4, width='stretch')
        
        col1, col2 = st.columns(2)
        with col1:
            st.plotly_chart(fig5, width='stretch')
        with col2:
            st.plotly_chart(fig6, width='stretch')
        
        # Еженедельная таблица
        st.subheader("📅 Подробный еженедельный расчет")
        
        # Рассчитываем еженедельные данные
        weekly_results = calculate_weekly_inventory(monthly_orders, buyback_rate, return_days, safety_stock)
        
        # Создаем DataFrame для еженедельных данных
        weekly_df = pd.DataFrame(weekly_results).T
        
        # Переименовываем колонки
        weekly_df.columns = [
            'Заказы',
            'Продано со склада',
            'Возвраты за неделю',
            'Возвращается на склад',
            'Выкуплено товара',
            'Процент использования',
            'Процент возвратов'
        ]
        
        # Округляем числовые значения
        weekly_df = weekly_df.round(1)
        
        # Отображаем еженедельную таблицу
        st.dataframe(weekly_df, width='stretch')
        
        # Сводка по еженедельным данным
        st.write("**📊 Сводка по еженедельным данным:**")
        col1, col2, col3, col4 = st.columns(4)
        
        total_weekly_orders = sum(weekly_results[week]['orders'] for week in weekly_results)
        total_weekly_sold = sum(weekly_results[week]['sold_from_warehouse'] for week in weekly_results)
        total_weekly_returns = sum(weekly_results[week]['returns_this_week'] for week in weekly_results)
        total_weekly_buyback = sum(weekly_results[week]['buyback_quantity'] for week in weekly_results)
        
        with col1:
            st.metric("Общий объем заказов (недели)", f"{total_weekly_orders:.0f} шт.")
        with col2:
            st.metric("Общий объем продаж (недели)", f"{total_weekly_sold:.0f} шт.")
        with col3:
            st.metric("Общий объем возвратов (недели)", f"{total_weekly_returns:.0f} шт.")
        with col4:
            st.metric("Общий объем выкупа (недели)", f"{total_weekly_buyback:.0f} шт.")
        
        # Рекомендации
        st.subheader("💡 Рекомендации и анализ")
        
        # Анализ эффективности
        if efficiency > 80:
            st.success("✅ Отличная эффективность использования товара!")
        elif efficiency > 60:
            st.warning("⚠️ Хорошая эффективность, но есть возможности для улучшения")
        else:
            st.error("❌ Низкая эффективность, требуется оптимизация")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**📈 Анализ использования товара:**")
            if overall_utilization > 70:
                st.success(f"✅ Высокий процент использования: {overall_utilization:.1f}%")
            elif overall_utilization > 50:
                st.warning(f"⚠️ Средний процент использования: {overall_utilization:.1f}%")
            else:
                st.error(f"❌ Низкий процент использования: {overall_utilization:.1f}%")
            
            if overall_return_rate < 30:
                st.success(f"✅ Низкий процент возвратов: {overall_return_rate:.1f}%")
            elif overall_return_rate < 50:
                st.warning(f"⚠️ Средний процент возвратов: {overall_return_rate:.1f}%")
            else:
                st.error(f"❌ Высокий процент возвратов: {overall_return_rate:.1f}%")
        
        with col2:
            st.write("**📊 Дополнительные метрики:**")
            st.metric("Средний остаток/мес", f"{sum([results[m]['warehouse_stock'] for m in results])/len(monthly_orders):.0f} шт.")
            st.metric("Коэффициент оборачиваемости", f"{total_sold/total_initial_purchase:.2f}")
            st.metric("Эффективность запасов", f"{(total_buyback/total_initial_purchase)*100:.1f}%")
            
            st.write("**⚙️ Параметры:**")
            if buyback_rate < 0.3:
                st.warning("⚠️ Низкий процент выкупа может привести к большим объемам возвратов")
            else:
                st.success("✅ Хороший процент выкупа")
            
            if safety_stock < 0.1:
                st.info("ℹ️ Рекомендуется увеличить страховой запас")
            else:
                st.success("✅ Страховой запас достаточный")
        
        # Сохранение товара
        st.subheader("💾 Сохранение и экспорт")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Сохранить товар:**")
            product_name = st.text_input(
                "Название товара:",
                value=f"Товар_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                key="product_name"
            )
            
            # Автоматическое сохранение при изменении данных
            product_data = {
                'name': product_name,
                'buyback_rate': buyback_rate,
                'return_days': return_days,
                'safety_stock': safety_stock,
                'initial_stock': initial_stock,
                'monthly_orders': monthly_orders,
                'monthly_undelivered': monthly_undelivered,
                'results': results,
                'total_orders': total_orders,
                'total_returns': total_returns,
                'created_at': datetime.now().isoformat()
            }
            
            # Автоматически сохраняем при изменении данных
            if save_product(product_name, product_data):
                st.success(f"✅ Данные автоматически сохранены в '{product_name}'")
        
        # Экспорт в Excel
        st.subheader("📊 Экспорт результатов")
        
        # Создаем Excel файл
        output = pd.ExcelWriter('inventory_calculation_results.xlsx', engine='openpyxl')
        
        # Лист с результатами
        results_df.to_excel(output, sheet_name='Результаты расчета')
        
        # Лист с исходными данными
        monthly_df = pd.DataFrame(list(monthly_orders.items()), 
                                columns=['Месяц', 'Заказы'])
        monthly_df['Заказы'] = monthly_df['Заказы'].round(0)  # Округляем до целых
        monthly_df.to_excel(output, sheet_name='Исходные данные', index=False)
        
        # Лист с параметрами
        params_df = pd.DataFrame({
            'Параметр': [
                'Процент выкупа', 'Дни возврата', 'Страховой запас', 
                'Остаток на начало', 'Единовременная закупка', 'Общий объем заказов', 
                'Общий объем продаж', 'Общий недостаток товара', 'Общий объем возвратов', 
                'Остаток на складе', 'Процент использования', 'Процент возвратов', 
                'Эффективность (%)', 'Средний заказ/мес', 'Средняя продажа/мес', 
                'Разница закупок', 'Процент покрытия'
            ],
            'Значение': [
                f"{buyback_rate*100}%", f"{return_days} дней", f"{safety_stock*100}%", 
                f"{initial_stock} шт.", f"{total_initial_purchase} шт.", f"{total_orders} шт.", 
                f"{total_sold} шт.", f"{total_shortage} шт.", f"{total_returns} шт.", 
                f"{final_warehouse_stock} шт.", f"{overall_utilization:.1f}%", f"{overall_return_rate:.1f}%", 
                f"{efficiency:.1f}%", f"{avg_monthly_orders:.0f} шт.", f"{avg_monthly_sold:.0f} шт.", 
                f"{total_initial_purchase - initial_stock} шт.",
                f"{(initial_stock/total_initial_purchase*100):.1f}%" if total_initial_purchase > 0 else "0%"
            ]
        })
        params_df.to_excel(output, sheet_name='Параметры', index=False)
        
        output.close()
        
        with open('inventory_calculation_results.xlsx', 'rb') as f:
            st.download_button(
                label="📥 Скачать результаты (Excel)",
                data=f.read(),
                file_name=f"inventory_calculation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
    
    # Если нет заказов, показываем сообщение
    else:
        st.info("ℹ️ Введите заказы по месяцам для начала расчета")
    
    # Дополнительная информация
    st.subheader("ℹ️ Информация о расчете")
    st.write("""
    **Алгоритм расчета остатков:**
    
    1. **Для каждого месяца:**
       - Определяем необходимый объем заказов
       - Учитываем доступные возвраты с предыдущих месяцев
       - Рассчитываем новые возвраты (заказы × (1 - процент выкупа))
       - Добавляем страховой запас
       - Накопление возвратов для следующих месяцев
    
    2. **Пример расчета:**
       - Заказы: 100 шт. в месяц
       - Выкуп: 20% (20 шт.)
       - Возврат: 80 шт. через 7 дней
       - Страховой запас: 10%
       
       **Результат:** 
       - Месяц 1: Закупка 110 шт. (100 + 10% страховой запас)
       - Месяц 2: Закупка 22 шт. (100 - 80 возвратов + 10% страховой запас)
    """)

if __name__ == "__main__":
    main()
