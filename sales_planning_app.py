import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json
import os

# Настройка страницы
st.set_page_config(
    page_title="Планирование продаж",
    page_icon="��",
    layout="wide"
)

# Заголовок приложения
st.title("📊 Планирование продаж и предварительных продаж")
st.markdown("---")

# Функция для создания календаря недель
def create_weekly_calendar(year=2025):
    weeks = []
    start_date = datetime(year, 1, 1)
    
    # Находим первую неделю года (понедельник)
    while start_date.weekday() != 0:
        start_date += timedelta(days=1)
    
    current_date = start_date
    week_num = 1
    
    while current_date.year == year:
        end_date = current_date + timedelta(days=6)
        week_info = {
            'week_num': week_num,
            'start_date': current_date.strftime('%d.%m.%Y'),
            'end_date': end_date.strftime('%d.%m.%Y'),
            'period': f"{current_date.strftime('%d.%m')} - {end_date.strftime('%d.%m.%Y')}"
        }
        weeks.append(week_info)
        current_date += timedelta(days=7)
        week_num += 1
    
    return weeks

# Функция для расчета ДРР
def calculate_drr(advertising, fact_orders_rub):
    if fact_orders_rub > 0:
        return round((advertising / fact_orders_rub) * 100, 2)
    return 0

# Основная логика приложения
def main():
    # Боковая панель для ввода данных по неделям
    with st.sidebar:
        st.header("📝 Ввод данных по неделям")
        
        # Выбор недели - все недели года
        selected_week = st.selectbox(
            "Выберите неделю:",
            [f"Неделя {i}" for i in range(1, 53)],
            index=0
        )
        
        st.markdown("---")
        st.subheader(f"📊 Данные для {selected_week}")
        
        # Поля для ввода данных
        fact_orders_qty = st.number_input("Факт заказы (шт)", min_value=0, value=0, step=1)
        fact_orders_rub = st.number_input("Факт заказы (руб)", min_value=0.0, value=0.0, step=1000.0)
        plan_orders_qty = st.number_input("План заказов (шт)", min_value=0, value=0, step=1)
        redeemed_qty = st.number_input("Выкуп (шт)", min_value=0, value=0, step=1)
        redeemed_rub = st.number_input("Выкуп (руб)", min_value=0.0, value=0.0, step=1000.0)
        plan_redeemed_qty = st.number_input("План выкуп (шт)", min_value=0, value=0, step=1)
        advertising_rub = st.number_input("Реклама (руб)", min_value=0.0, value=0.0, step=100.0)
        
        # Кнопка для применения данных
        if st.button("💾 Применить данные", type="primary"):
            # Применяем данные к выбранной неделе
            if 'sales_data' in st.session_state:
                # Находим индексы строк с нужными метриками
                fact_orders_qty_row = st.session_state.sales_data[st.session_state.sales_data['Метрика'] == 'Факт заказы (шт)'].index
                fact_orders_rub_row = st.session_state.sales_data[st.session_state.sales_data['Метрика'] == 'Факт заказы (руб)'].index
                plan_orders_qty_row = st.session_state.sales_data[st.session_state.sales_data['Метрика'] == 'План заказов (шт)'].index
                redeemed_qty_row = st.session_state.sales_data[st.session_state.sales_data['Метрика'] == 'Выкуп (шт)'].index
                redeemed_rub_row = st.session_state.sales_data[st.session_state.sales_data['Метрика'] == 'Выкуп (руб)'].index
                plan_redeemed_qty_row = st.session_state.sales_data[st.session_state.sales_data['Метрика'] == 'План выкуп (шт)'].index
                advertising_rub_row = st.session_state.sales_data[st.session_state.sales_data['Метрика'] == 'Реклама (руб)'].index
                
                # Обновляем данные для выбранной недели
                # Нужно найти правильный ключ столбца с месяцем
                week_num = int(selected_week.split()[1])  # Извлекаем номер недели
                months = ['январь', 'февраль', 'март', 'апрель', 'май', 'июнь', 
                          'июль', 'август', 'сентябрь', 'октябрь', 'ноябрь', 'декабрь']
                month_idx = (week_num - 1) // 4
                month = months[month_idx] if month_idx < 12 else months[11]
                week_key = f"Неделя {week_num}\n({month})"
                
                if len(fact_orders_qty_row) > 0:
                    st.session_state.sales_data.at[fact_orders_qty_row[0], week_key] = fact_orders_qty
                if len(fact_orders_rub_row) > 0:
                    st.session_state.sales_data.at[fact_orders_rub_row[0], week_key] = fact_orders_rub
                if len(plan_orders_qty_row) > 0:
                    st.session_state.sales_data.at[plan_orders_qty_row[0], week_key] = plan_orders_qty
                if len(redeemed_qty_row) > 0:
                    st.session_state.sales_data.at[redeemed_qty_row[0], week_key] = redeemed_qty
                if len(redeemed_rub_row) > 0:
                    st.session_state.sales_data.at[redeemed_rub_row[0], week_key] = redeemed_rub
                if len(plan_redeemed_qty_row) > 0:
                    st.session_state.sales_data.at[plan_redeemed_qty_row[0], week_key] = plan_redeemed_qty
                if len(advertising_rub_row) > 0:
                    st.session_state.sales_data.at[advertising_rub_row[0], week_key] = advertising_rub
                
                st.success(f"Данные для {selected_week} обновлены!")
                st.rerun()
        
        st.markdown("---")
        st.markdown("### 📋 Инструкция")
        st.markdown("""
        1. Выберите неделю в выпадающем списке
        2. Заполните данные для выбранной недели
        3. Нажмите 'Применить данные'
        4. ДРР рассчитывается автоматически
        """)
    
    # Основной контент
    st.subheader("📅 Календарь планирования продаж")
    
    # Создание данных для примера - метрики как строки, недели как столбцы
    metrics_data = []
    
    # Определяем метрики как строки
    metrics = [
        'Факт заказы (шт)',
        'План заказов (шт)',
        'Отклонение заказов (шт)',
        'Факт заказы (руб)',
        'Цена за единицу (руб)',
        'Выкуп (шт)',
        'План выкуп (шт)',
        'Отклонение выкупа (шт)',
        'Выкуп (руб)',
        'Реклама (руб)',
        'ДРР %',
        'ДРР выкуп %',
        'Процент выкупа %'
    ]
    
    # Создаем данные для каждой метрики
    for metric in metrics:
        row_data = {'Метрика': metric}
        
        # Добавляем столбцы для всех недель года
        months = ['январь', 'февраль', 'март', 'апрель', 'май', 'июнь', 
                  'июль', 'август', 'сентябрь', 'октябрь', 'ноябрь', 'декабрь']
        
        for week in range(1, 53):
            month_idx = (week - 1) // 4
            month = months[month_idx] if month_idx < 12 else months[11]
            
            # Определяем текущий месяц для выделения
            current_date = datetime.now()
            current_month = current_date.month
            current_month_name = months[current_month - 1]
            
            # Выделяем текущий месяц
            if month == current_month_name:
                week_key = f"Неделя {week}\n({month}) 🔥"  # Добавляем эмодзи для выделения
            else:
                week_key = f"Неделя {week}\n({month})"
            
            if metric == 'ДРР %' or metric == 'ДРР выкуп %':
                row_data[week_key] = 0.0  # ДРР как float
            elif 'руб' in metric:
                row_data[week_key] = 0.0  # Деньги как float
            else:
                row_data[week_key] = 0    # Количество как int
        
        metrics_data.append(row_data)
    
    df = pd.DataFrame(metrics_data)
    
    # Создаем сессионное состояние для хранения данных
    if 'sales_data' not in st.session_state:
        st.session_state.sales_data = df.copy()
    
    # Редактируемая таблица с закрепленным столбцом
    edited_df = st.data_editor(
        st.session_state.sales_data,
        num_rows="dynamic",
        width='stretch',
        height=400,
        column_config={
            "Метрика": st.column_config.Column(
                "Метрика",
                width="medium",
                help="Название метрики"
            )
        }
    )
    
    # Обновляем данные в сессии
    st.session_state.sales_data = edited_df
    

    
    # Пересчет ДРР после редактирования
    for i, row in edited_df.iterrows():
        metric = row['Метрика']
        
        # Находим индексы строк с нужными метриками
        fact_orders_qty_row = edited_df[edited_df['Метрика'] == 'Факт заказы (шт)'].index
        fact_orders_rub_row = edited_df[edited_df['Метрика'] == 'Факт заказы (руб)'].index
        advertising_row = edited_df[edited_df['Метрика'] == 'Реклама (руб)'].index
        redeemed_rub_row = edited_df[edited_df['Метрика'] == 'Выкуп (руб)'].index
        
        if len(fact_orders_qty_row) > 0 and len(fact_orders_rub_row) > 0 and len(advertising_row) > 0 and len(redeemed_rub_row) > 0:
            fact_orders_qty_idx = fact_orders_qty_row[0]
            fact_orders_rub_idx = fact_orders_rub_row[0]
            advertising_idx = advertising_row[0]
            redeemed_rub_idx = redeemed_rub_row[0]
            
            # Пересчитываем ДРР для каждой недели
            months = ['январь', 'февраль', 'март', 'апрель', 'май', 'июнь', 
                      'июль', 'август', 'сентябрь', 'октябрь', 'ноябрь', 'декабрь']
            
            for week in range(1, 53):
                month_idx = (week - 1) // 4
                month = months[month_idx] if month_idx < 12 else months[11]
                
                # Определяем текущий месяц для выделения
                current_date = datetime.now()
                current_month = current_date.month
                current_month_name = months[current_month - 1]
                
                # Выделяем текущий месяц
                if month == current_month_name:
                    week_key = f"Неделя {week}\n({month}) 🔥"
                else:
                    week_key = f"Неделя {week}\n({month})"
                
                # Получаем значения для текущей недели
                fact_orders_qty_val = float(edited_df.at[fact_orders_qty_idx, week_key]) if pd.notna(edited_df.at[fact_orders_qty_idx, week_key]) else 0
                fact_orders_rub_val = float(edited_df.at[fact_orders_rub_idx, week_key]) if pd.notna(edited_df.at[fact_orders_rub_idx, week_key]) else 0
                advertising_val = float(edited_df.at[advertising_idx, week_key]) if pd.notna(edited_df.at[advertising_idx, week_key]) else 0
                redeemed_rub_val = float(edited_df.at[redeemed_rub_idx, week_key]) if pd.notna(edited_df.at[redeemed_rub_idx, week_key]) else 0
                
                # Находим индексы строк ДРР
                drr_row = edited_df[edited_df['Метрика'] == 'ДРР %'].index
                drr_redeemed_row = edited_df[edited_df['Метрика'] == 'ДРР выкуп %'].index
                
                if len(drr_row) > 0 and len(drr_redeemed_row) > 0:
                    drr_idx = drr_row[0]
                    drr_redeemed_idx = drr_redeemed_row[0]
                    
                    # ДРР = Реклама / Фактические заказы в руб
                    drr = calculate_drr(advertising_val, fact_orders_rub_val)
                    edited_df.at[drr_idx, week_key] = drr
                    
                    # ДРР выкуп = Реклама / Выкупленные товары руб
                    drr_redeemed = calculate_drr(advertising_val, redeemed_rub_val)
                    edited_df.at[drr_redeemed_idx, week_key] = drr_redeemed
                
                # Автоматический расчет цены за единицу
                price_row = edited_df[edited_df['Метрика'] == 'Цена за единицу (руб)'].index
                if len(price_row) > 0 and fact_orders_qty_val > 0:
                    price_idx = price_row[0]
                    price = fact_orders_rub_val / fact_orders_qty_val
                    edited_df.at[price_idx, week_key] = round(price, 2)
                
                # Получаем значение выкупа для текущей недели (нужно для всех расчетов)
                redeemed_qty_row = edited_df[edited_df['Метрика'] == 'Выкуп (шт)'].index
                redeemed_qty_val = 0
                if len(redeemed_qty_row) > 0:
                    redeemed_qty_val = float(edited_df.at[redeemed_qty_row[0], week_key]) if pd.notna(edited_df.at[redeemed_qty_row[0], week_key]) else 0
                
                # Автоматический расчет процента выкупа
                redemption_percent_row = edited_df[edited_df['Метрика'] == 'Процент выкупа %'].index
                if len(redemption_percent_row) > 0 and fact_orders_qty_val > 0:
                    redemption_percent_idx = redemption_percent_row[0]
                    redemption_percent = (redeemed_qty_val / fact_orders_qty_val) * 100 if fact_orders_qty_val > 0 else 0
                    edited_df.at[redemption_percent_idx, week_key] = round(redemption_percent, 2)
                
                # Автоматический расчет отклонений
                # Отклонение заказов = Факт - План
                deviation_orders_row = edited_df[edited_df['Метрика'] == 'Отклонение заказов (шт)'].index
                if len(deviation_orders_row) > 0:
                    deviation_orders_idx = deviation_orders_row[0]
                    plan_orders_qty_row = edited_df[edited_df['Метрика'] == 'План заказов (шт)'].index
                    if len(plan_orders_qty_row) > 0:
                        plan_orders_qty_val = float(edited_df.at[plan_orders_qty_row[0], week_key]) if pd.notna(edited_df.at[plan_orders_qty_row[0], week_key]) else 0
                        deviation_orders = fact_orders_qty_val - plan_orders_qty_val
                        edited_df.at[deviation_orders_idx, week_key] = int(deviation_orders)
                
                # Отклонение выкупа = Факт выкупа - План выкупа
                deviation_redeemed_row = edited_df[edited_df['Метрика'] == 'Отклонение выкупа (шт)'].index
                if len(deviation_redeemed_row) > 0:
                    deviation_redeemed_idx = deviation_redeemed_row[0]
                    plan_redeemed_qty_row = edited_df[edited_df['Метрика'] == 'План выкуп (шт)'].index
                    if len(plan_redeemed_qty_row) > 0:
                        plan_redeemed_qty_val = float(edited_df.at[plan_redeemed_qty_row[0], week_key]) if pd.notna(edited_df.at[plan_redeemed_qty_row[0], week_key]) else 0
                        deviation_redeemed = redeemed_qty_val - plan_redeemed_qty_val
                        edited_df.at[deviation_redeemed_idx, week_key] = int(deviation_redeemed)
    
    # Убираем дублирующую таблицу - данные уже отображаются в редакторе выше
    
    # Сводка по месяцам (будет отображаться в правой колонке)
    
    monthly_summary = {}
    months = ['январь', 'февраль', 'март', 'апрель', 'май', 'июнь', 
              'июль', 'август', 'сентябрь', 'октябрь', 'ноябрь', 'декабрь']
    
    # Инициализируем сводку по всем месяцам
    for month in months:
        monthly_summary[month] = {
            'fact_orders_qty': 0,
            'fact_orders_rub': 0,
            'plan_orders_qty': 0,
            'redeemed_qty': 0,
            'redeemed_rub': 0,
            'plan_redeemed_qty': 0,
            'advertising_rub': 0
        }
    
    # Собираем данные по месяцам (каждые 4 недели = 1 месяц)
    for week in range(1, 53):
        month_idx = (week - 1) // 4
        month = months[month_idx] if month_idx < 12 else months[11]
        
        # Определяем текущий месяц для выделения
        current_date = datetime.now()
        current_month = current_date.month
        current_month_name = months[current_month - 1]
        
        # Выделяем текущий месяц
        if month == current_month_name:
            week_key = f"Неделя {week}\n({month}) 🔥"
        else:
            week_key = f"Неделя {week}\n({month})"
        
        # Получаем значения для текущей недели
        fact_orders_qty_row = edited_df[edited_df['Метрика'] == 'Факт заказы (шт)'].index
        fact_orders_rub_row = edited_df[edited_df['Метрика'] == 'Факт заказы (руб)'].index
        plan_orders_qty_row = edited_df[edited_df['Метрика'] == 'План заказов (шт)'].index
        redeemed_qty_row = edited_df[edited_df['Метрика'] == 'Выкуп (шт)'].index
        redeemed_rub_row = edited_df[edited_df['Метрика'] == 'Выкуп (руб)'].index
        plan_redeemed_qty_row = edited_df[edited_df['Метрика'] == 'План выкуп (шт)'].index
        advertising_rub_row = edited_df[edited_df['Метрика'] == 'Реклама (руб)'].index
        
        if len(fact_orders_qty_row) > 0:
            monthly_summary[month]['fact_orders_qty'] += int(edited_df.at[fact_orders_qty_row[0], week_key]) if pd.notna(edited_df.at[fact_orders_qty_row[0], week_key]) else 0
        if len(fact_orders_rub_row) > 0:
            monthly_summary[month]['fact_orders_rub'] += float(edited_df.at[fact_orders_rub_row[0], week_key]) if pd.notna(edited_df.at[fact_orders_rub_row[0], week_key]) else 0
        if len(plan_orders_qty_row) > 0:
            monthly_summary[month]['plan_orders_qty'] += int(edited_df.at[plan_orders_qty_row[0], week_key]) if pd.notna(edited_df.at[plan_orders_qty_row[0], week_key]) else 0
        if len(redeemed_qty_row) > 0:
            monthly_summary[month]['redeemed_qty'] += int(edited_df.at[redeemed_qty_row[0], week_key]) if pd.notna(edited_df.at[redeemed_qty_row[0], week_key]) else 0
        if len(redeemed_rub_row) > 0:
            monthly_summary[month]['redeemed_rub'] += float(edited_df.at[redeemed_rub_row[0], week_key]) if pd.notna(edited_df.at[redeemed_rub_row[0], week_key]) else 0
        if len(plan_redeemed_qty_row) > 0:
            monthly_summary[month]['plan_redeemed_qty'] += int(edited_df.at[plan_redeemed_qty_row[0], week_key]) if pd.notna(edited_df.at[plan_redeemed_qty_row[0], week_key]) else 0
        if len(advertising_rub_row) > 0:
            monthly_summary[month]['advertising_rub'] += float(edited_df.at[advertising_rub_row[0], week_key]) if pd.notna(edited_df.at[advertising_rub_row[0], week_key]) else 0
    
    # Отображение сводки по месяцам
    st.markdown("---")
    st.subheader("📅 Сводка по месяцам")
    
    # Определяем текущий месяц
    current_date = datetime.now()
    current_month = current_date.month
    months_list = ['январь', 'февраль', 'март', 'апрель', 'май', 'июнь', 
                   'июль', 'август', 'сентябрь', 'октябрь', 'ноябрь', 'декабрь']
    current_month_name = months_list[current_month - 1]
    
    # Создаем колонки для сводки
    col1, col2, col3, col4 = st.columns(4)
    
    for i, (month, summary) in enumerate(monthly_summary.items()):
        # Текущий месяц развернут по умолчанию
        expanded = (month == current_month_name)
        
        # Выбираем колонку для отображения
        if i % 4 == 0:
            current_col = col1
        elif i % 4 == 1:
            current_col = current_col = col2
        elif i % 4 == 2:
            current_col = col3
        else:
            current_col = col4
        
        with current_col:
            with st.expander(f"📅 {month.capitalize()}", expanded=expanded):
                st.metric("Факт заказы (шт)", summary['fact_orders_qty'])
                st.metric("План заказов (шт)", summary['plan_orders_qty'])
                st.metric("Выкуп (шт)", summary['redeemed_qty'])
                st.metric("План выкуп (шт)", summary['plan_redeemed_qty'])
                st.metric("Факт заказы (руб)", f"{summary['fact_orders_rub']:,.0f}")
                st.metric("Выкуп (руб)", f"{summary['redeemed_rub']:,.0f}")
                st.metric("Реклама (руб)", f"{summary['advertising_rub']:,.0f}")
                
                # ДРР для месяца
                if summary['fact_orders_rub'] > 0:
                    monthly_drr = (summary['advertising_rub'] / summary['fact_orders_rub']) * 100
                    st.metric("ДРР %", f"{monthly_drr:.2f}%")
                else:
                    st.metric("ДРР %", "0%")
    
    # Общая аналитика
    st.markdown("---")
    st.subheader("🔍 Общая аналитика")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Получаем строки с нужными метриками
        fact_orders_qty_row = edited_df[edited_df['Метрика'] == 'Факт заказы (шт)'].index
        plan_orders_qty_row = edited_df[edited_df['Метрика'] == 'План заказов (шт)'].index
        
        total_fact_orders = 0
        total_plan_orders = 0
        
        if len(fact_orders_qty_row) > 0:
            total_fact_orders = edited_df.iloc[fact_orders_qty_row[0], 1:].sum()  # Суммируем все недели
        if len(plan_orders_qty_row) > 0:
            total_plan_orders = edited_df.iloc[plan_orders_qty_row[0], 1:].sum()  # Суммируем все недели
        
        st.metric("Общий факт заказов", int(total_fact_orders))
        st.metric("Общий план заказов", int(total_plan_orders))
        
        if total_plan_orders > 0:
            accuracy = (total_fact_orders / total_plan_orders) * 100
            st.metric("Точность планирования", f"{accuracy:.1f}%")
    
    with col2:
        # Получаем строки с нужными метриками
        fact_orders_rub_row = edited_df[edited_df['Метрика'] == 'Факт заказы (руб)'].index
        redeemed_rub_row = edited_df[edited_df['Метрика'] == 'Выкуп (руб)'].index
        advertising_rub_row = edited_df[edited_df['Метрика'] == 'Реклама (руб)'].index
        
        total_revenue = 0
        total_redeemed = 0
        total_advertising = 0
        
        if len(fact_orders_rub_row) > 0:
            total_revenue = edited_df.iloc[fact_orders_rub_row[0], 1:].sum()  # Суммируем все недели
        if len(redeemed_rub_row) > 0:
            total_redeemed = edited_df.iloc[redeemed_rub_row[0], 1:].sum()  # Суммируем все недели
        if len(advertising_rub_row) > 0:
            total_advertising = edited_df.iloc[advertising_rub_row[0], 1:].sum()  # Суммируем все недели
        
        st.metric("Общая выручка", f"{total_revenue:,.0f} ₽")
        st.metric("Выручка с выкупа", f"{total_redeemed:,.0f} ₽")
        st.metric("Общие расходы на рекламу", f"{total_advertising:,.0f} ₽")
    
    with col3:
        if total_revenue > 0:
            overall_drr = (total_advertising / total_revenue) * 100
            st.metric("Общий ДРР", f"{overall_drr:.2f}%")
        else:
            st.metric("Общий ДРР", "0%")
        
        if total_fact_orders > 0:
            # Получаем строку с выкупом
            redeemed_qty_row = edited_df[edited_df['Метрика'] == 'Выкуп (шт)'].index
            total_redeemed_qty = 0
            if len(redeemed_qty_row) > 0:
                total_redeemed_qty = edited_df.iloc[redeemed_qty_row[0], 1:].sum()
            conversion = (total_redeemed_qty / total_fact_orders) * 100
            st.metric("Конверсия выкупа", f"{conversion:.1f}%")
        else:
            st.metric("Конверсия выкупа", "0%")
        
        if total_advertising > 0:
            roas = total_revenue / total_advertising
            st.metric("ROAS", f"{roas:.2f}")
        
        # Общий KPI процент выкупа
        if total_fact_orders > 0:
            total_redeemed_qty = 0
            redeemed_qty_row = edited_df[edited_df['Метрика'] == 'Выкуп (шт)'].index
            if len(redeemed_qty_row) > 0:
                total_redeemed_qty = edited_df.iloc[redeemed_qty_row[0], 1:].sum()
            overall_redemption_percent = (total_redeemed_qty / total_fact_orders) * 100
            st.metric("Общий % выкупа", f"{overall_redemption_percent:.1f}%")
        else:
            st.metric("Общий % выкупа", "0%")

if __name__ == "__main__":
    main()
