import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Настройка страницы
st.set_page_config(
    page_title="Калькулятор расходов по сезонам",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Функции для работы с данными
def load_data():
    """Загрузка данных из файла"""
    default_data = {
        'seasons': {
            'season1': {
                'name': 'Сезон 1',
                'months': 6,
                'invested': 0,
                'profitability': 0,
                'monthly_expenses': {},
                'one_time_expenses': {},
                'next_season_investment': 0,
                'revenue': 0,
                'profit': 0,
                'balance': 0,
                'total_monthly_expenses': 0,
                'total_one_time_expenses': 0,
                'total_expenses': 0
            },
            'season2': {
                'name': 'Сезон 2',
                'months': 6,
                'invested': 0,
                'profitability': 0,
                'monthly_expenses': {},
                'one_time_expenses': {},
                'next_season_investment': 0,
                'revenue': 0,
                'profit': 0,
                'balance': 0,
                'total_monthly_expenses': 0,
                'total_one_time_expenses': 0,
                'total_expenses': 0
            }
        },
        'carry_over': True
    }
    
    if os.path.exists('seasonal_data.json'):
        try:
            with open('seasonal_data.json', 'r', encoding='utf-8') as f:
                loaded_data = json.load(f)
                
            # Добавляем недостающие поля, если их нет
            for season_key in ['season1', 'season2']:
                if season_key in loaded_data['seasons']:
                    season = loaded_data['seasons'][season_key]
                    for field in ['total_monthly_expenses', 'total_one_time_expenses', 'total_expenses', 'next_season_investment']:
                        if field not in season:
                            season[field] = 0
                    
                    # Пересчитываем итоги
                    totals = calculate_season_totals(season)
                    season.update(totals)
                
            return loaded_data
        except Exception as e:
            st.error(f"Ошибка загрузки данных: {e}")
            return default_data
    
    return default_data

def save_data(data):
    """Сохранение данных в файл"""
    with open('seasonal_data.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def calculate_season_totals(season_data):
    """Расчет итогов по сезону"""
    # Месячные расходы умножаем на 6 (длительность сезона)
    total_monthly_expenses = sum(season_data['monthly_expenses'].values()) * 6
    total_one_time_expenses = sum(season_data['one_time_expenses'].values())
    next_season_investment = season_data.get('next_season_investment', 0)
    total_expenses = total_monthly_expenses + total_one_time_expenses + next_season_investment
    
    # Расчет выручки на основе вложений и рентабельности
    if season_data['profitability'] > 0:
        revenue = season_data['invested'] * (1 + season_data['profitability'] / 100)
    else:
        revenue = 0
    
    profit = revenue - total_expenses
    balance = profit
    
    return {
        'total_monthly_expenses': total_monthly_expenses,
        'total_one_time_expenses': total_one_time_expenses,
        'total_expenses': total_expenses,
        'revenue': revenue,
        'profit': profit,
        'balance': balance
    }

def transfer_balance_to_next_season(data):
    """Перенос вложения на следующий сезон и остатка"""
    season1_next_investment = data['seasons']['season1'].get('next_season_investment', 0)
    season1_balance = data['seasons']['season1'].get('balance', 0)
    
    transferred_amounts = []
    
    # Переносим вложение на следующий сезон
    if season1_next_investment > 0:
        data['seasons']['season2']['invested'] += season1_next_investment
        transferred_amounts.append(f"Вложение на следующий сезон: {season1_next_investment:,.0f} руб.")
        # Обнуляем вложение на следующий сезон в первом сезоне
        data['seasons']['season1']['next_season_investment'] = 0
    
    # Переносим остаток прибыли
    if season1_balance > 0:
        data['seasons']['season2']['invested'] += season1_balance
        transferred_amounts.append(f"Остаток прибыли: {season1_balance:,.0f} руб.")
        # Обнуляем остаток в первом сезоне (устанавливаем баланс в 0)
        data['seasons']['season1']['balance'] = 0
    
    # Пересчитываем оба сезона если были переносы
    if transferred_amounts:
        totals1 = calculate_season_totals(data['seasons']['season1'])
        data['seasons']['season1'].update(totals1)
        totals2 = calculate_season_totals(data['seasons']['season2'])
        data['seasons']['season2'].update(totals2)
    
    return transferred_amounts

def duplicate_expenses_to_next_season(data, source_season):
    """Дублирование расходов на следующий сезон"""
    if source_season == "Сезон 1":
        target_season = "season2"
        source_season_key = "season1"
    else:
        target_season = "season1"
        source_season_key = "season2"
    
    duplicated_items = []
    
    # Дублируем месячные расходы
    source_monthly = data['seasons'][source_season_key]['monthly_expenses']
    if source_monthly:
        data['seasons'][target_season]['monthly_expenses'].update(source_monthly)
        duplicated_items.append(f"Месячные расходы: {len(source_monthly)} позиций")
    
    # Дублируем единовременные расходы
    source_one_time = data['seasons'][source_season_key]['one_time_expenses']
    if source_one_time:
        data['seasons'][target_season]['one_time_expenses'].update(source_one_time)
        duplicated_items.append(f"Единовременные расходы: {len(source_one_time)} позиций")
    
    # Дублируем вложение на следующий сезон
    source_next_investment = data['seasons'][source_season_key].get('next_season_investment', 0)
    if source_next_investment > 0:
        data['seasons'][target_season]['next_season_investment'] = source_next_investment
        duplicated_items.append(f"Вложение на следующий сезон: {source_next_investment:,.0f} руб.")
    
    # Пересчитываем целевой сезон
    if duplicated_items:
        totals = calculate_season_totals(data['seasons'][target_season])
        data['seasons'][target_season].update(totals)
    
    return duplicated_items

# Загрузка данных
data = load_data()

# Заголовок
st.title("📊 Калькулятор расходов по сезонам")
st.markdown("---")

# Боковая панель для основных параметров
with st.sidebar:
    st.header("⚙️ Основные параметры")
    
    # Переключение между сезонами
    selected_season = st.selectbox(
        "Выберите сезон для редактирования:",
        ["Сезон 1", "Сезон 2"],
        key="season_selector"
    )
    
    season_key = 'season1' if selected_season == "Сезон 1" else 'season2'
    current_season = data['seasons'][season_key]
    
    st.subheader(f"Параметры {selected_season}")
    
    # Ввод основных параметров
    current_season['invested'] = st.number_input(
        "Вложено (руб.):",
        min_value=0.0,
        value=float(current_season['invested']),
        step=1000.0,
        format="%.0f"
    )
    
    current_season['profitability'] = st.number_input(
        "Рентабельность (%):",
        min_value=0.0,
        max_value=1000.0,
        value=float(current_season['profitability']),
        step=1.0,
        format="%.1f"
    )
    
    # Пересчет при изменении параметров
    totals = calculate_season_totals(current_season)
    current_season.update(totals)
    
    # Сохранение данных
    if st.button("💾 Сохранить изменения"):
        save_data(data)
        st.success("Данные сохранены!")
    
    st.markdown("---")
    
    # Перенос остатка
    st.subheader("🔄 Перенос остатка")
    data['carry_over'] = st.checkbox(
        "Автоматически переносить остаток на следующий сезон",
        value=data.get('carry_over', True)
    )
    
    if st.button("📤 Перенести вложение и остаток с Сезона 1 на Сезон 2"):
        # Показываем состояние до переноса
        season1_next_investment = data['seasons']['season1'].get('next_season_investment', 0)
        season1_balance = data['seasons']['season1'].get('balance', 0)
        st.info(f"**До переноса:** Вложения Сезона 2: {data['seasons']['season2']['invested']:,.0f} руб.")
        st.info(f"**Вложение на следующий сезон в Сезоне 1:** {season1_next_investment:,.0f} руб.")
        st.info(f"**Остаток прибыли в Сезоне 1:** {season1_balance:,.0f} руб.")
        
        transferred_amounts = transfer_balance_to_next_season(data)
        save_data(data)
        
        if transferred_amounts:
            st.success("✅ Перенос выполнен успешно!")
            st.info("**Перенесено:**")
            for amount in transferred_amounts:
                st.write(f"• {amount}")
            st.info(f"**После переноса:** Вложения Сезона 2: {data['seasons']['season2']['invested']:,.0f} руб.")
            
            # Принудительно обновляем страницу для отображения изменений
            st.rerun()
        else:
            st.warning("⚠️ Нечего переносить - нет вложения на следующий сезон и остатка")
    
    # Кнопка дублирования расходов
    if st.button("🔄 Дублировать расходы на следующий сезон"):
        # Определяем целевой сезон
        target_season = "Сезон 2" if selected_season == "Сезон 1" else "Сезон 1"
        
        # Показываем информацию о дублировании
        st.info(f"🔄 **Дублирование расходов с {selected_season} на {target_season}**")
        
        # Подсчитываем количество расходов для дублирования
        monthly_count = len(current_season['monthly_expenses'])
        one_time_count = len(current_season['one_time_expenses'])
        next_investment = current_season.get('next_season_investment', 0)
        
        if monthly_count > 0 or one_time_count > 0 or next_investment > 0:
            st.info(f"📊 **Будет продублировано:**")
            if monthly_count > 0:
                st.write(f"• Месячные расходы: {monthly_count} позиций")
            if one_time_count > 0:
                st.write(f"• Единовременные расходы: {one_time_count} позиций")
            if next_investment > 0:
                st.write(f"• Вложение на следующий сезон: {next_investment:,.0f} руб.")
            
            # Выполняем дублирование
            duplicated_items = duplicate_expenses_to_next_season(data, selected_season)
            save_data(data)
            
            if duplicated_items:
                st.success("✅ Дублирование выполнено успешно!")
                st.info("**Продублировано:**")
                for item in duplicated_items:
                    st.write(f"• {item}")
                
                # Принудительно обновляем страницу для отображения изменений
                st.rerun()
        else:
            st.warning("⚠️ Нечего дублировать - нет расходов в текущем сезоне")

# Основная область
col1, col2 = st.columns([2, 1])

with col1:
    st.header(f"📋 Управление расходами - {selected_season}")
    
    # Месячные расходы
    st.subheader("💰 Месячные расходы")
    
    # Показываем общую сумму месячных расходов
    total_monthly = sum(current_season['monthly_expenses'].values()) * 6
    if total_monthly > 0:
        st.info(f"📊 **Общая сумма месячных расходов за сезон:** {total_monthly:,.0f} руб.")
    
    # Добавление нового месячного расхода
    with st.expander("➕ Добавить месячный расход"):
        month_name = st.text_input("Название месяца:", key="month_name")
        month_amount = st.number_input("Сумма за месяц (руб.):", min_value=0.0, key="month_amount")
        
        # Показываем расчет за сезон
        season_total = month_amount * 6 if month_amount > 0 else 0
        st.info(f"💰 За сезон (6 месяцев): {season_total:,.0f} руб.")
        
        if st.button("Добавить месячный расход"):
            if month_name and month_amount > 0:
                # Сохраняем месячную сумму, но в расчетах умножаем на 6
                current_season['monthly_expenses'][month_name] = month_amount
                totals = calculate_season_totals(current_season)
                current_season.update(totals)
                save_data(data)
                st.success(f"Добавлен расход: {month_name} - {month_amount:,.0f} руб./мес. (за сезон: {season_total:,.0f} руб.)")
                st.rerun()
    
    # Редактирование месячных расходов
    if current_season['monthly_expenses']:
        st.write("**Текущие месячные расходы:**")
        for month, amount in current_season['monthly_expenses'].items():
            col_a, col_b, col_c, col_d, col_e = st.columns([2, 1, 1, 1, 1])
            with col_a:
                st.write(f"📅 {month}")
            with col_b:
                st.write(f"{amount:,.0f} руб./мес.")
            with col_c:
                st.write(f"{amount * 6:,.0f} руб./сезон")
            with col_d:
                if st.button("✏️", key=f"edit_month_{month}"):
                    # Сохраняем данные для редактирования
                    st.session_state['editing_month'] = month
                    st.session_state['editing_month_amount'] = amount
                    st.rerun()
            with col_e:
                if st.button("🗑️", key=f"del_month_{month}"):
                    del current_season['monthly_expenses'][month]
                    totals = calculate_season_totals(current_season)
                    current_season.update(totals)
                    save_data(data)
                    st.rerun()
        
        # Форма редактирования месячного расхода
        if 'editing_month' in st.session_state:
            st.write("**✏️ Редактирование месячного расхода:**")
            edited_month_name = st.text_input("Название месяца:", value=st.session_state['editing_month'], key="edit_month_name")
            edited_month_amount = st.number_input("Сумма за месяц (руб.):", min_value=0.0, value=float(st.session_state['editing_month_amount']), key="edit_month_amount")
            
            # Показываем расчет за сезон
            edited_season_total = edited_month_amount * 6 if edited_month_amount > 0 else 0
            st.info(f"💰 За сезон (6 месяцев): {edited_season_total:,.0f} руб.")
            
            col_save, col_cancel = st.columns(2)
            with col_save:
                if st.button("💾 Сохранить изменения"):
                    old_month = st.session_state['editing_month']
                    # Удаляем старый расход
                    if old_month in current_season['monthly_expenses']:
                        del current_season['monthly_expenses'][old_month]
                    # Добавляем обновленный
                    current_season['monthly_expenses'][edited_month_name] = edited_month_amount
                    totals = calculate_season_totals(current_season)
                    current_season.update(totals)
                    save_data(data)
                    # Очищаем сессию
                    if 'editing_month' in st.session_state:
                        del st.session_state['editing_month']
                    if 'editing_month_amount' in st.session_state:
                        del st.session_state['editing_month_amount']
                    st.success(f"Месячный расход обновлен: {edited_month_name} - {edited_month_amount:,.0f} руб./мес. (за сезон: {edited_season_total:,.0f} руб.)")
                    st.rerun()
            
            with col_cancel:
                if st.button("❌ Отменить"):
                    if 'editing_month' in st.session_state:
                        del st.session_state['editing_month']
                    if 'editing_month_amount' in st.session_state:
                        del st.session_state['editing_month_amount']
                    st.rerun()
    
    # Единовременные расходы
    st.subheader("💸 Единовременные расходы")
    
    # Показываем общую сумму единовременных расходов
    total_one_time = sum(current_season['one_time_expenses'].values())
    if total_one_time > 0:
        st.info(f"📊 **Общая сумма единовременных расходов:** {total_one_time:,.0f} руб.")
    
    # Добавление единовременного расхода
    with st.expander("➕ Добавить единовременный расход"):
        expense_name = st.text_input("Название расхода:", key="expense_name")
        expense_amount = st.number_input("Сумма (руб.):", min_value=0.0, key="expense_amount")
        
        if st.button("Добавить единовременный расход"):
            if expense_name and expense_amount > 0:
                current_season['one_time_expenses'][expense_name] = expense_amount
                totals = calculate_season_totals(current_season)
                current_season.update(totals)
                save_data(data)
                st.success(f"Добавлен расход: {expense_name} - {expense_amount:,.0f} руб.")
                st.rerun()
    
    # Редактирование единовременных расходов
    if current_season['one_time_expenses']:
        st.write("**Текущие единовременные расходы:**")
        for expense, amount in current_season['one_time_expenses'].items():
            col_a, col_b, col_c, col_d = st.columns([2, 1, 1, 1])
            with col_a:
                st.write(f"💸 {expense}")
            with col_b:
                st.write(f"{amount:,.0f} руб.")
            with col_c:
                if st.button("✏️", key=f"edit_expense_{expense}"):
                    # Сохраняем данные для редактирования
                    st.session_state['editing_expense'] = expense
                    st.session_state['editing_amount'] = amount
                    st.rerun()
            with col_d:
                if st.button("🗑️", key=f"del_expense_{expense}"):
                    del current_season['one_time_expenses'][expense]
                    totals = calculate_season_totals(current_season)
                    current_season.update(totals)
                    save_data(data)
                    st.rerun()
        
        # Форма редактирования
        if 'editing_expense' in st.session_state:
            st.write("**✏️ Редактирование расхода:**")
            edited_name = st.text_input("Название:", value=st.session_state['editing_expense'], key="edit_expense_name")
            edited_amount = st.number_input("Сумма (руб.):", min_value=0.0, value=float(st.session_state['editing_amount']), key="edit_expense_amount")
            
            col_save, col_cancel = st.columns(2)
            with col_save:
                if st.button("💾 Сохранить изменения"):
                    old_name = st.session_state['editing_expense']
                    # Удаляем старый расход
                    if old_name in current_season['one_time_expenses']:
                        del current_season['one_time_expenses'][old_name]
                    # Добавляем обновленный
                    current_season['one_time_expenses'][edited_name] = edited_amount
                    totals = calculate_season_totals(current_season)
                    current_season.update(totals)
                    save_data(data)
                    # Очищаем сессию
                    if 'editing_expense' in st.session_state:
                        del st.session_state['editing_expense']
                    if 'editing_amount' in st.session_state:
                        del st.session_state['editing_amount']
                    st.success(f"Расход обновлен: {edited_name} - {edited_amount:,.0f} руб.")
                    st.rerun()
            
            with col_cancel:
                if st.button("❌ Отменить"):
                    if 'editing_expense' in st.session_state:
                        del st.session_state['editing_expense']
                    if 'editing_amount' in st.session_state:
                        del st.session_state['editing_amount']
                    st.rerun()
    
    # Вложение на следующий сезон
    st.subheader("🔄 Вложение на следующий сезон")
    
    # Информация о том, как работает вложение на следующий сезон
    if selected_season == "Сезон 1":
        st.info("💡 **Как это работает:** Вложение на следующий сезон учитывается как расход в текущем сезоне, но при нажатии кнопки 'Перенести остаток и вложения' автоматически добавляется к вложениям Сезона 2.")
    
    # Добавление вложения на следующий сезон
    with st.expander("➕ Добавить вложение на следующий сезон"):
        next_investment_amount = st.number_input(
            "Сумма вложения на следующий сезон (руб.):", 
            min_value=0.0, 
            value=float(current_season.get('next_season_investment', 0)),
            key="next_investment_amount"
        )
        
        if st.button("Сохранить вложение на следующий сезон"):
            current_season['next_season_investment'] = next_investment_amount
            totals = calculate_season_totals(current_season)
            current_season.update(totals)
            save_data(data)
            st.success(f"Вложение на следующий сезон: {next_investment_amount:,.0f} руб.")
            if selected_season == "Сезон 1":
                st.info("✅ Это вложение будет автоматически перенесено в 'Вложено' Сезона 2 при нажатии кнопки переноса.")
            st.rerun()
    
    # Отображение текущего вложения на следующий сезон
    if current_season.get('next_season_investment', 0) > 0:
        st.write("**Текущее вложение на следующий сезон:**")
        col_a, col_b, col_c, col_d = st.columns([2, 1, 1, 1])
        with col_a:
            st.write("🔄 Вложение на следующий сезон")
        with col_b:
            st.write(f"{current_season['next_season_investment']:,.0f} руб.")
        with col_c:
            if st.button("✏️", key="edit_next_investment"):
                # Сохраняем данные для редактирования
                st.session_state['editing_next_investment'] = current_season['next_season_investment']
                st.rerun()
        with col_d:
            if st.button("🗑️", key="del_next_investment"):
                current_season['next_season_investment'] = 0
                totals = calculate_season_totals(current_season)
                current_season.update(totals)
                save_data(data)
                st.rerun()
        
        # Форма редактирования вложения на следующий сезон
        if 'editing_next_investment' in st.session_state:
            st.write("**✏️ Редактирование вложения на следующий сезон:**")
            edited_next_investment = st.number_input(
                "Сумма вложения на следующий сезон (руб.):", 
                min_value=0.0, 
                value=float(st.session_state['editing_next_investment']),
                key="edit_next_investment_amount"
            )
            
            col_save, col_cancel = st.columns(2)
            with col_save:
                if st.button("💾 Сохранить изменения"):
                    current_season['next_season_investment'] = edited_next_investment
                    totals = calculate_season_totals(current_season)
                    current_season.update(totals)
                    save_data(data)
                    # Очищаем сессию
                    if 'editing_next_investment' in st.session_state:
                        del st.session_state['editing_next_investment']
                    st.success(f"Вложение на следующий сезон обновлено: {edited_next_investment:,.0f} руб.")
                    if selected_season == "Сезон 1":
                        st.info("✅ Это вложение будет автоматически перенесено в 'Вложено' Сезона 2 при нажатии кнопки переноса.")
                    st.rerun()
            
            with col_cancel:
                if st.button("❌ Отменить"):
                    if 'editing_next_investment' in st.session_state:
                        del st.session_state['editing_next_investment']
                    st.rerun()

with col2:
    st.header("📊 Итоги")
    
    # Карточки с итогами
    st.metric(
        "Вложено",
        f"{current_season['invested']:,.0f} руб.",
        delta=None
    )
    
    st.metric(
        "Выручка",
        f"{current_season['revenue']:,.0f} руб.",
        delta=f"{current_season['revenue'] - current_season['invested']:,.0f} руб."
    )
    
    st.metric(
        "Общие расходы",
        f"{current_season['total_expenses']:,.0f} руб.",
        delta=None
    )
    
    st.metric(
        "Прибыль",
        f"{current_season['profit']:,.0f} руб.",
        delta=None,
        delta_color="normal" if current_season['profit'] >= 0 else "inverse"
    )
    
    st.metric(
        "Остаток",
        f"{current_season['balance']:,.0f} руб.",
        delta=None,
        delta_color="normal" if current_season['balance'] >= 0 else "inverse"
    )

# Детальная разбивка расходов
st.markdown("---")
st.header("📈 Детальная разбивка")

col3, col4 = st.columns(2)

with col3:
    st.subheader("Расходы по категориям")
    
    if current_season['monthly_expenses'] or current_season['one_time_expenses'] or current_season.get('next_season_investment', 0) > 0:
        # Подготовка данных для графика
        expense_data = []
        
        for month, amount in current_season['monthly_expenses'].items():
            expense_data.append({'Категория': 'Месячные расходы', 'Название': f"{month} (за сезон)", 'Сумма': amount * 6})
        
        for expense, amount in current_season['one_time_expenses'].items():
            expense_data.append({'Категория': 'Единовременные расходы', 'Название': expense, 'Сумма': amount})
        
        if current_season.get('next_season_investment', 0) > 0:
            expense_data.append({'Категория': 'Вложение на следующий сезон', 'Название': 'Вложение на следующий сезон', 'Сумма': current_season['next_season_investment']})
        
        if expense_data:
            df_expenses = pd.DataFrame(expense_data)
            
            # График расходов
            fig = px.bar(
                df_expenses,
                x='Название',
                y='Сумма',
                color='Категория',
                title=f"Расходы {selected_season}",
                labels={'Сумма': 'Сумма (руб.)', 'Название': 'Название расхода'},
                color_discrete_map={
                    'Месячные расходы': '#FF6B6B',
                    'Единовременные расходы': '#4ECDC4',
                    'Вложение на следующий сезон': '#FFD93D'
                }
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig, width='stretch')
    else:
        st.info("Расходы не добавлены")

with col4:
    st.subheader("Структура доходов и расходов")
    
    # Круговая диаграмма
    labels = ['Вложено', 'Прибыль', 'Месячные расходы', 'Единовременные расходы', 'Вложение на следующий сезон']
    values = [
        current_season['invested'],
        max(0, current_season['profit']),
        current_season['total_monthly_expenses'],
        current_season['total_one_time_expenses'],
        current_season.get('next_season_investment', 0)
    ]
    
    # Фильтруем нулевые значения
    non_zero_data = [(label, value) for label, value in zip(labels, values) if value > 0]
    
    if non_zero_data:
        labels_filtered, values_filtered = zip(*non_zero_data)
        
        fig = px.pie(
            values=values_filtered,
            names=labels_filtered,
            title=f"Структура {selected_season}",
            color_discrete_sequence=px.colors.qualitative.Set3
        )
        fig.update_layout(height=400)
        st.plotly_chart(fig, width='stretch')
    else:
        st.info("Нет данных для отображения")

# Сравнение сезонов
st.markdown("---")
st.header("🔄 Сравнение сезонов")

col5, col6 = st.columns(2)

with col5:
    st.subheader("Сезон 1")
    season1 = data['seasons']['season1']
    
    # Создаем DataFrame для отображения
    season1_data = {
        'Показатель': ['Вложено', 'Выручка', 'Общие расходы', 'Прибыль', 'Остаток'],
        'Значение': [
            season1['invested'],
            season1['revenue'],
            season1['total_expenses'],
            season1['profit'],
            season1['balance']
        ]
    }
    
    df_season1 = pd.DataFrame(season1_data)
    df_season1['Значение'] = df_season1['Значение'].apply(lambda x: f"{x:,.0f} руб.")
    
    st.dataframe(df_season1, use_container_width=True, hide_index=True)

with col6:
    st.subheader("Сезон 2")
    season2 = data['seasons']['season2']
    
    # Создаем DataFrame для отображения
    season2_data = {
        'Показатель': ['Вложено', 'Выручка', 'Общие расходы', 'Прибыль', 'Остаток'],
        'Значение': [
            season2['invested'],
            season2['revenue'],
            season2['total_expenses'],
            season2['profit'],
            season2['balance']
        ]
    }
    
    df_season2 = pd.DataFrame(season2_data)
    df_season2['Значение'] = df_season2['Значение'].apply(lambda x: f"{x:,.0f} руб.")
    
    st.dataframe(df_season2, use_container_width=True, hide_index=True)

# График сравнения сезонов
st.subheader("📊 Сравнительный анализ")
comparison_data = {
    'Сезон': ['Сезон 1', 'Сезон 1', 'Сезон 1', 'Сезон 1', 'Сезон 2', 'Сезон 2', 'Сезон 2', 'Сезон 2'],
    'Показатель': ['Вложено', 'Выручка', 'Прибыль', 'Остаток', 'Вложено', 'Выручка', 'Прибыль', 'Остаток'],
    'Значение': [
        season1['invested'], season1['revenue'], season1['profit'], season1['balance'],
        season2['invested'], season2['revenue'], season2['profit'], season2['balance']
    ]
}

df_comparison = pd.DataFrame(comparison_data)

fig = px.bar(
    df_comparison,
    x='Показатель',
    y='Значение',
    color='Сезон',
    title="Сравнение показателей по сезонам",
    barmode='group',
    color_discrete_map={'Сезон 1': '#FF6B6B', 'Сезон 2': '#4ECDC4'}
)
fig.update_layout(height=500)
st.plotly_chart(fig, width='stretch')

# Футер
st.markdown("---")
st.markdown("💡 **Советы:**")
st.markdown("- Используйте функцию переноса остатка для планирования следующего сезона")
st.markdown("- Регулярно сохраняйте изменения")
st.markdown("- Анализируйте структуру расходов для оптимизации")

