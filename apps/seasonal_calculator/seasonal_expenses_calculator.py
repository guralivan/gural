import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime, date
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import calendar

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
    current_year = datetime.now().year
    
    # Создаем структуру для нескольких лет с двумя сезонами в каждом
    default_data = {
        'years': {}
    }
    
    # Добавляем годы с 2024 по 2027
    for year in range(2024, 2028):
        default_data['years'][str(year)] = {
            'season1': {
                'name': f'{year} - Сезон 1',
                'months': 6,
                'invested': 0,
                'profitability': 0,
                'monthly_expenses': {},
                'one_time_expenses': {},
                'next_season_investment': 0,
                'loans': {},
                'revenue': 0,
                'profit': 0,
                'balance': 0,
                'total_monthly_expenses': 0,
                'total_one_time_expenses': 0,
                'total_expenses': 0,
                'total_loans': 0
            },
            'season2': {
                'name': f'{year} - Сезон 2',
                'months': 6,
                'invested': 0,
                'profitability': 0,
                'monthly_expenses': {},
                'one_time_expenses': {},
                'next_season_investment': 0,
                'loans': {},
                'revenue': 0,
                'profit': 0,
                'balance': 0,
                'total_monthly_expenses': 0,
                'total_one_time_expenses': 0,
                'total_expenses': 0,
                'total_loans': 0
            }
        }
    
    default_data['carry_over'] = True
    
    if os.path.exists('seasonal_data.json'):
        try:
            with open('seasonal_data.json', 'r', encoding='utf-8') as f:
                loaded_data = json.load(f)
            
            # Проверяем, есть ли уже новая структура
            if 'years' in loaded_data:
                # Добавляем недостающие поля для всех сезонов
                for year in loaded_data['years']:
                    for season_key in ['season1', 'season2']:
                        if season_key in loaded_data['years'][year]:
                            season = loaded_data['years'][year][season_key]
                            for field in ['total_monthly_expenses', 'total_one_time_expenses', 'total_expenses', 'next_season_investment', 'total_loans']:
                                if field not in season:
                                    season[field] = 0
                            
                            # Добавляем поле loans, если его нет
                            if 'loans' not in season:
                                season['loans'] = {}
                            
                            # Пересчитываем итоги
                            totals = calculate_season_totals(season)
                            season.update(totals)
                
                return loaded_data
            else:
                # Миграция со старой структуры на новую
                st.info("🔄 Обновление структуры данных...")
                migrated_data = default_data.copy()
                
                # Переносим данные из старой структуры в 2024 год
                if 'seasons' in loaded_data:
                    if 'season1' in loaded_data['seasons']:
                        migrated_data['years']['2024']['season1'].update(loaded_data['seasons']['season1'])
                    if 'season2' in loaded_data['seasons']:
                        migrated_data['years']['2024']['season2'].update(loaded_data['seasons']['season2'])
                
                # Пересчитываем итоги для мигрированных данных
                for season_key in ['season1', 'season2']:
                    # Добавляем поле loans, если его нет
                    if 'loans' not in migrated_data['years']['2024'][season_key]:
                        migrated_data['years']['2024'][season_key]['loans'] = {}
                    
                    totals = calculate_season_totals(migrated_data['years']['2024'][season_key])
                    migrated_data['years']['2024'][season_key].update(totals)
                
                return migrated_data
                
        except Exception as e:
            st.error(f"Ошибка загрузки данных: {e}")
            return default_data
    
    return default_data

def save_data(data):
    """Сохранение данных в файл"""
    with open('seasonal_data.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def get_season_months(season_key, year):
    """Получить месяцы для сезона"""
    if season_key == "season1":
        # Сезон 1: январь-июнь
        return [1, 2, 3, 4, 5, 6]
    else:
        # Сезон 2: июль-декабрь
        return [7, 8, 9, 10, 11, 12]

def get_current_season():
    """Определить текущий сезон на основе текущей даты"""
    current_date = date.today()
    current_month = current_date.month
    
    # Сезон 1: январь-июнь (1-6)
    # Сезон 2: июль-декабрь (7-12)
    if 1 <= current_month <= 6:
        return "season1"
    else:
        return "season2"

def calculate_remaining_monthly_expenses(season_data, season_key, year):
    """Расчет остатка месячных расходов на основе текущего дня"""
    current_date = date.today()
    current_year = current_date.year
    current_month = current_date.month
    current_day = current_date.day
    
    # Получаем месяцы для текущего сезона
    season_months = get_season_months(season_key, year)
    
    # Проверяем, относится ли текущий год и месяц к выбранному сезону
    if current_year != int(year) or current_month not in season_months:
        # Если текущий месяц не относится к выбранному сезону, показываем полную сумму
        return sum(season_data['monthly_expenses'].values()) * 6, "Сезон не активен"
    
    # Сначала рассчитываем общую сумму месячных расходов за месяц
    monthly_total = sum(season_data['monthly_expenses'].values())
    
    remaining_expenses = 0
    total_spent = 0
    details = []
    
    # Проходим по месяцам сезона
    for month_num in season_months:
        month_name = calendar.month_name[month_num]
        
        if month_num < current_month:
            # Месяц уже прошел - расход полностью потрачен
            month_spent = monthly_total
            month_remaining = 0
            total_spent += month_spent
        elif month_num == current_month:
            # Текущий месяц - рассчитываем пропорционально дню
            days_in_month = calendar.monthrange(current_year, month_num)[1]
            spent_ratio = current_day / days_in_month
            month_spent = monthly_total * spent_ratio
            month_remaining = monthly_total - month_spent
            total_spent += month_spent
            remaining_expenses += month_remaining
        else:
            # Будущий месяц - расход еще не потрачен
            month_spent = 0
            month_remaining = monthly_total
            remaining_expenses += month_remaining
        
        # Добавляем детали для месяца
        if month_spent > 0 and month_remaining > 0:
            details.append(f"{month_name}: {month_spent:,.0f} руб. (потрачено) + {month_remaining:,.0f} руб. (остаток)")
        elif month_spent > 0:
            details.append(f"{month_name}: {month_spent:,.0f} руб. (потрачено)")
        elif month_remaining > 0:
            details.append(f"{month_name}: {month_remaining:,.0f} руб. (остаток)")
    
    return remaining_expenses, details

def calculate_spent_monthly_expenses(season_data, season_key, year):
    """Расчет фактически потраченных месячных расходов на основе текущего дня"""
    current_date = date.today()
    current_year = current_date.year
    current_month = current_date.month
    current_day = current_date.day
    
    # Получаем месяцы для текущего сезона
    season_months = get_season_months(season_key, year)
    
    # Проверяем, относится ли текущий год и месяц к выбранному сезону
    if current_year != int(year) or current_month not in season_months:
        # Если текущий месяц не относится к выбранному сезону, показываем 0 (сезон не активен)
        return 0, "Сезон не активен"
    
    # Рассчитываем общую сумму месячных расходов за месяц
    monthly_total = sum(season_data['monthly_expenses'].values())
    
    spent_expenses = 0
    
    # Проходим по месяцам сезона
    for month_num in season_months:
        if month_num < current_month:
            # Месяц уже прошел - расход полностью потрачен
            spent_expenses += monthly_total
        elif month_num == current_month:
            # Текущий месяц - рассчитываем пропорционально дню
            days_in_month = calendar.monthrange(current_year, month_num)[1]
            spent_ratio = current_day / days_in_month
            month_spent = monthly_total * spent_ratio
            spent_expenses += month_spent
        # Будущие месяцы не учитываем (еще не потрачены)
    
    return spent_expenses, f"Потрачено за {len([m for m in season_months if m <= current_month])} месяцев"

def calculate_revenue_balance_after_monthly_expenses(season_data, season_key, year):
    """Расчет остатка выручки после вычета всех расходов"""
    # Получаем общую выручку
    total_invested = season_data['invested'] + sum(season_data.get('loans', {}).values())
    if season_data['profitability'] > 0:
        total_revenue = total_invested * (1 + season_data['profitability'] / 100)
    else:
        total_revenue = 0
    
    # Получаем фактически потраченные месячные расходы
    spent_monthly_expenses, _ = calculate_spent_monthly_expenses(season_data, season_key, year)
    
    # Получаем остаток месячных расходов для отображения
    remaining_monthly_expenses, _ = calculate_remaining_monthly_expenses(season_data, season_key, year)
    
    # Вычитаем единовременные расходы и вложение на следующий сезон
    one_time_expenses = sum(season_data['one_time_expenses'].values())
    next_season_investment = season_data.get('next_season_investment', 0)
    
    # Остаток выручки после вычета всех расходов
    # Вычитаем только фактически потраченные месячные расходы (без единовременных расходов)
    revenue_balance = total_revenue - spent_monthly_expenses - next_season_investment
    
    return revenue_balance, total_revenue, spent_monthly_expenses, one_time_expenses, next_season_investment

def calculate_season_totals(season_data):
    """Расчет итогов по сезону"""
    # Месячные расходы умножаем на 6 (длительность сезона)
    total_monthly_expenses = sum(season_data['monthly_expenses'].values()) * 6
    total_one_time_expenses = sum(season_data['one_time_expenses'].values())
    next_season_investment = season_data.get('next_season_investment', 0)
    total_loans = sum(season_data.get('loans', {}).values())
    total_expenses = total_monthly_expenses + total_one_time_expenses + next_season_investment
    
    # Общие вложения = первоначальные вложения + займы
    total_invested = season_data['invested'] + total_loans
    
    # Расчет выручки на основе общих вложений (включая займы) и рентабельности
    if season_data['profitability'] > 0:
        revenue = total_invested * (1 + season_data['profitability'] / 100)
    else:
        revenue = 0
    
    profit = revenue - total_expenses
    balance = profit  # Займы уже учтены в расчете выручки
    
    return {
        'total_monthly_expenses': total_monthly_expenses,
        'total_one_time_expenses': total_one_time_expenses,
        'total_expenses': total_expenses,
        'total_loans': total_loans,
        'total_invested': total_invested,
        'revenue': revenue,
        'profit': profit,
        'balance': balance
    }

def transfer_balance_to_next_season(data, source_year, source_season, target_year, target_season):
    """Перенос вложения на следующий сезон и остатка"""
    source_data = data['years'][source_year][source_season]
    target_data = data['years'][target_year][target_season]
    
    source_next_investment = source_data.get('next_season_investment', 0)
    source_balance = source_data.get('balance', 0)
    
    transferred_amounts = []
    
    # Переносим вложение на следующий сезон
    if source_next_investment > 0:
        target_data['invested'] += source_next_investment
        transferred_amounts.append(f"Вложение на следующий сезон: {source_next_investment:,.0f} руб.")
        # Обнуляем вложение на следующий сезон в исходном сезоне
        source_data['next_season_investment'] = 0
    
    # Переносим остаток баланса (включая займы)
    if source_balance > 0:
        target_data['invested'] += source_balance
        transferred_amounts.append(f"Остаток прибыли: {source_balance:,.0f} руб.")
        # Обнуляем остаток баланса в исходном сезоне
        source_data['balance'] = 0
    
    # Пересчитываем оба сезона
    totals_source = calculate_season_totals(source_data)
    source_data.update(totals_source)
    totals_target = calculate_season_totals(target_data)
    target_data.update(totals_target)
    
    return transferred_amounts

def duplicate_expenses_to_next_season(data, source_year, source_season, target_year, target_season):
    """Дублирование расходов на следующий сезон"""
    source_data = data['years'][source_year][source_season]
    target_data = data['years'][target_year][target_season]
    
    duplicated_items = []
    
    # Дублируем месячные расходы
    source_monthly = source_data['monthly_expenses']
    if source_monthly:
        target_data['monthly_expenses'].update(source_monthly)
        duplicated_items.append(f"Месячные расходы: {len(source_monthly)} позиций")
    
    # Дублируем единовременные расходы
    source_one_time = source_data['one_time_expenses']
    if source_one_time:
        target_data['one_time_expenses'].update(source_one_time)
        duplicated_items.append(f"Единовременные расходы: {len(source_one_time)} позиций")
    
    # Дублируем вложение на следующий сезон
    source_next_investment = source_data.get('next_season_investment', 0)
    if source_next_investment > 0:
        target_data['next_season_investment'] = source_next_investment
        duplicated_items.append(f"Вложение на следующий сезон: {source_next_investment:,.0f} руб.")
    
    # Дублируем займы
    source_loans = source_data.get('loans', {})
    if source_loans:
        target_data['loans'].update(source_loans)
        duplicated_items.append(f"Займы: {len(source_loans)} позиций")
    
    # Пересчитываем целевой сезон
    if duplicated_items:
        totals = calculate_season_totals(target_data)
        target_data.update(totals)
    
    return duplicated_items

# Загрузка данных
data = load_data()

# Заголовок
st.title("📊 Калькулятор расходов по сезонам")
st.markdown("---")

# Боковая панель для основных параметров
with st.sidebar:
    st.header("⚙️ Основные параметры")
    
    # Получаем доступные годы
    available_years = list(data['years'].keys())
    available_years.sort()
    
    # Определяем текущий год
    current_year = str(date.today().year)
    
    # Если текущий год есть в доступных годах, выбираем его по умолчанию
    if current_year in available_years:
        default_year_index = available_years.index(current_year)
    else:
        # Если текущего года нет, выбираем последний доступный год
        default_year_index = len(available_years) - 1
    
    # Переключение между годами (по умолчанию текущий год)
    selected_year = st.selectbox(
        "Выберите год:",
        available_years,
        index=default_year_index,
        key="year_selector"
    )
    
    # Показываем индикатор текущего года
    if selected_year == current_year:
        st.info(f"📅 **Текущий год** (автоматически выбран)")
    
    # Переключение между сезонами (по умолчанию текущий сезон)
    current_season_key = get_current_season()
    season_options = ["season1", "season2"]
    default_index = season_options.index(current_season_key)
    
    selected_season = st.selectbox(
        "Выберите сезон:",
        season_options,
        index=default_index,
        format_func=lambda x: "Сезон 1" if x == "season1" else "Сезон 2",
        key="season_selector"
    )
    
    # Показываем индикатор текущего сезона
    if selected_season == current_season_key:
        st.info(f"📅 **Текущий сезон** (автоматически выбран на основе текущей даты)")
    
    current_season = data['years'][selected_year][selected_season]
    
    st.subheader(f"Параметры {selected_year} - {selected_season.replace('season', 'Сезон ')}")
    
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
    
    # Определяем целевой сезон для переноса
    if selected_season == "season1":
        target_season = "season2"
        target_year = selected_year
    else:
        target_season = "season1"
        target_year = str(int(selected_year) + 1) if int(selected_year) < 2027 else selected_year
    
    if st.button(f"📤 Перенести вложение и остаток в {target_year} - {target_season.replace('season', 'Сезон ')}"):
        # Показываем состояние до переноса
        source_next_investment = current_season.get('next_season_investment', 0)
        source_balance = current_season.get('balance', 0)
        target_data = data['years'][target_year][target_season]
        st.info(f"**До переноса:** Вложения {target_year} - {target_season.replace('season', 'Сезон ')}: {target_data['invested']:,.0f} руб.")
        st.info(f"**Вложение на следующий сезон:** {source_next_investment:,.0f} руб.")
        st.info(f"**Остаток прибыли:** {source_balance:,.0f} руб.")
        
        transferred_amounts = transfer_balance_to_next_season(data, selected_year, selected_season, target_year, target_season)
        save_data(data)
        
        if transferred_amounts:
            st.success("✅ Перенос выполнен успешно!")
            st.info("**Перенесено:**")
            for amount in transferred_amounts:
                st.write(f"• {amount}")
            st.info(f"**После переноса:** Вложения {target_year} - {target_season.replace('season', 'Сезон ')}: {target_data['invested']:,.0f} руб.")
            
            # Принудительно обновляем страницу для отображения изменений
            st.rerun()
        else:
            st.warning("⚠️ Нечего переносить - нет вложения на следующий сезон и остатка")
    
    # Кнопка дублирования расходов
    if st.button("🔄 Дублировать расходы на следующий сезон"):
        # Определяем целевой сезон для дублирования
        if selected_season == "season1":
            target_season = "season2"
            target_year = selected_year
        else:
            target_season = "season1"
            target_year = str(int(selected_year) + 1) if int(selected_year) < 2027 else selected_year
        
        # Показываем информацию о дублировании
        st.info(f"🔄 **Дублирование расходов с {selected_year} - {selected_season.replace('season', 'Сезон ')} на {target_year} - {target_season.replace('season', 'Сезон ')}**")
        
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
            duplicated_items = duplicate_expenses_to_next_season(data, selected_year, selected_season, target_year, target_season)
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
    st.header(f"📋 Управление расходами - {selected_year} - {selected_season.replace('season', 'Сезон ')}")
    
    # Месячные расходы
    st.subheader("💰 Месячные расходы")
    
    # Показываем общую сумму месячных расходов
    total_monthly = sum(current_season['monthly_expenses'].values()) * 6
    if total_monthly > 0:
        st.info(f"📊 **Общая сумма месячных расходов за сезон:** {total_monthly:,.0f} руб.")
        
        # Показываем остаток расходов на основе текущего дня
        remaining_expenses, details = calculate_remaining_monthly_expenses(current_season, selected_season, selected_year)
        
        if isinstance(details, list):
            # Создаем expander для детального просмотра
            with st.expander("📅 Детализация расходов по месяцам (на основе текущего дня)", expanded=False):
                for detail in details:
                    st.write(f"• {detail}")
            
            # Показываем остаток расходов
            spent_expenses = total_monthly - remaining_expenses
            st.success(f"💡 **Остаток месячных расходов на сегодня:** {remaining_expenses:,.0f} руб.")
            st.info(f"📈 **Потрачено на сегодня:** {spent_expenses:,.0f} руб.")
            
            # Прогресс-бар для визуализации
            if total_monthly > 0:
                progress_ratio = spent_expenses / total_monthly
                st.progress(progress_ratio)
                st.caption(f"Прогресс: {progress_ratio:.1%} от общего бюджета сезона")
            
            # Показываем остаток выручки после вычета остатка месячных расходов
            revenue_balance, total_revenue, spent_monthly_expenses, one_time_exp, next_investment = calculate_revenue_balance_after_monthly_expenses(current_season, selected_season, selected_year)
            
            if total_revenue > 0:
                st.markdown("---")
                st.subheader("💰 Остаток выручки после расходов")
                
                # Создаем expander с детальным расчетом
                with st.expander("📊 Детальный расчет остатка выручки", expanded=True):
                    st.write(f"**Общая выручка:** {total_revenue:,.0f} руб.")
                    st.write(f"**Текущие месячные траты:** -{spent_monthly_expenses:,.0f} руб.")
                    st.write(f"**Вложение на следующий сезон:** -{next_investment:,.0f} руб.")
                    st.markdown("---")
                    st.write(f"**Остаток выручки:** {revenue_balance:,.0f} руб.")
                    st.info("ℹ️ Единовременные расходы не учитываются в расчете остатка выручки")
                
                # Показываем результат с цветовой индикацией
                if revenue_balance > 0:
                    st.success(f"✅ **Остаток выручки после всех расходов:** {revenue_balance:,.0f} руб.")
                elif revenue_balance == 0:
                    st.info(f"⚖️ **Выручка полностью покрывает расходы:** {revenue_balance:,.0f} руб.")
                else:
                    st.error(f"⚠️ **Недостаток средств:** {abs(revenue_balance):,.0f} руб.")
        else:
            st.info(f"ℹ️ {details}")
    
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
    st.info("ℹ️ Единовременные расходы не учитываются в расчете остатка выручки")
    
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
    
    # Займы
    st.subheader("💰 Займы")
    
    # Показываем общую сумму займов
    total_loans = sum(current_season.get('loans', {}).values())
    if total_loans > 0:
        st.info(f"📊 **Общая сумма займов:** {total_loans:,.0f} руб.")
    
    # Добавление нового займа
    with st.expander("➕ Добавить займ"):
        loan_name = st.text_input("Название займа:", key="loan_name")
        loan_amount = st.number_input("Сумма займа (руб.):", min_value=0.0, key="loan_amount")
        
        if st.button("Добавить займ"):
            if loan_name and loan_amount > 0:
                current_season['loans'][loan_name] = loan_amount
                totals = calculate_season_totals(current_season)
                current_season.update(totals)
                save_data(data)
                st.success(f"Добавлен займ: {loan_name} - {loan_amount:,.0f} руб.")
                st.rerun()
    
    # Редактирование займов
    if current_season.get('loans', {}):
        st.write("**Текущие займы:**")
        for loan_name, loan_amount in current_season['loans'].items():
            col_a, col_b, col_c, col_d = st.columns([2, 1, 1, 1])
            with col_a:
                st.write(f"💰 {loan_name}")
            with col_b:
                st.write(f"{loan_amount:,.0f} руб.")
            with col_c:
                if st.button("✏️", key=f"edit_loan_{loan_name}"):
                    # Сохраняем данные для редактирования
                    st.session_state['editing_loan'] = loan_name
                    st.session_state['editing_loan_amount'] = loan_amount
                    st.rerun()
            with col_d:
                if st.button("🗑️", key=f"del_loan_{loan_name}"):
                    del current_season['loans'][loan_name]
                    totals = calculate_season_totals(current_season)
                    current_season.update(totals)
                    save_data(data)
                    st.rerun()
        
        # Форма редактирования займа
        if 'editing_loan' in st.session_state:
            st.write("**✏️ Редактирование займа:**")
            edited_loan_name = st.text_input("Название займа:", value=st.session_state['editing_loan'], key="edit_loan_name")
            edited_loan_amount = st.number_input("Сумма займа (руб.):", min_value=0.0, value=float(st.session_state['editing_loan_amount']), key="edit_loan_amount")
            
            col_save, col_cancel = st.columns(2)
            with col_save:
                if st.button("💾 Сохранить изменения"):
                    old_loan = st.session_state['editing_loan']
                    # Удаляем старый займ
                    if old_loan in current_season['loans']:
                        del current_season['loans'][old_loan]
                    # Добавляем обновленный
                    current_season['loans'][edited_loan_name] = edited_loan_amount
                    totals = calculate_season_totals(current_season)
                    current_season.update(totals)
                    save_data(data)
                    # Очищаем сессию
                    if 'editing_loan' in st.session_state:
                        del st.session_state['editing_loan']
                    if 'editing_loan_amount' in st.session_state:
                        del st.session_state['editing_loan_amount']
                    st.success(f"Займ обновлен: {edited_loan_name} - {edited_loan_amount:,.0f} руб.")
                    st.rerun()
            
            with col_cancel:
                if st.button("❌ Отменить"):
                    if 'editing_loan' in st.session_state:
                        del st.session_state['editing_loan']
                    if 'editing_loan_amount' in st.session_state:
                        del st.session_state['editing_loan_amount']
                    st.rerun()

with col2:
    st.header("📊 Итоги")
    
    # Показываем информацию о текущей дате
    current_date = date.today()
    st.info(f"📅 **Текущая дата:** {current_date.strftime('%d.%m.%Y')}")
    
    # Карточки с итогами
    st.metric(
        "Собственные вложения",
        f"{current_season['invested']:,.0f} руб.",
        delta=None
    )
    
    st.metric(
        "Общие вложения (+ займы)",
        f"{current_season.get('total_invested', current_season['invested']):,.0f} руб.",
        delta=f"{current_season.get('total_loans', 0):,.0f} руб. займов"
    )
    
    st.metric(
        "Выручка",
        f"{current_season['revenue']:,.0f} руб.",
        delta=f"{current_season['revenue'] - current_season.get('total_invested', current_season['invested']):,.0f} руб."
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
        "Займы",
        f"{current_season.get('total_loans', 0):,.0f} руб.",
        delta=None
    )
    
    st.metric(
        "Остаток",
        f"{current_season['balance']:,.0f} руб.",
        delta=None,
        delta_color="normal" if current_season['balance'] >= 0 else "inverse"
    )
    
    # Показываем остаток месячных расходов на основе текущего дня
    if current_season['monthly_expenses']:
        remaining_expenses, details = calculate_remaining_monthly_expenses(current_season, selected_season, selected_year)
        if isinstance(details, list):
            total_monthly = sum(current_season['monthly_expenses'].values()) * 6
            spent_expenses = total_monthly - remaining_expenses
            st.metric(
                "Остаток месячных расходов",
                f"{remaining_expenses:,.0f} руб.",
                delta=f"-{spent_expenses:,.0f} руб. потрачено",
                delta_color="inverse"
            )
    
    # Показываем остаток выручки после вычета остатка месячных расходов
    if current_season['profitability'] > 0:
        revenue_balance, total_revenue, spent_monthly_expenses, one_time_exp, next_investment = calculate_revenue_balance_after_monthly_expenses(current_season, selected_season, selected_year)
        
        if revenue_balance > 0:
            st.metric(
                "Остаток выручки после расходов",
                f"{revenue_balance:,.0f} руб.",
                delta=f"из {total_revenue:,.0f} руб. выручки",
                delta_color="normal"
            )
        elif revenue_balance == 0:
            st.metric(
                "Остаток выручки после расходов",
                f"{revenue_balance:,.0f} руб.",
                delta="Выручка = Расходы",
                delta_color="off"
            )
        else:
            st.metric(
                "Недостаток средств",
                f"{abs(revenue_balance):,.0f} руб.",
                delta=f"из {total_revenue:,.0f} руб. выручки",
                delta_color="inverse"
            )

# Детальная разбивка расходов
st.markdown("---")
st.header("📈 Детальная разбивка")

col3, col4 = st.columns(2)

with col3:
    st.subheader("Расходы по категориям")
    
    if current_season['monthly_expenses'] or current_season['one_time_expenses'] or current_season.get('next_season_investment', 0) > 0 or current_season.get('loans', {}):
        # Подготовка данных для графика
        expense_data = []
        
        for month, amount in current_season['monthly_expenses'].items():
            expense_data.append({'Категория': 'Месячные расходы', 'Название': f"{month} (за сезон)", 'Сумма': amount * 6})
        
        for expense, amount in current_season['one_time_expenses'].items():
            expense_data.append({'Категория': 'Единовременные расходы', 'Название': expense, 'Сумма': amount})
        
        if current_season.get('next_season_investment', 0) > 0:
            expense_data.append({'Категория': 'Вложение на следующий сезон', 'Название': 'Вложение на следующий сезон', 'Сумма': current_season['next_season_investment']})
        
        # Добавляем займы
        for loan_name, loan_amount in current_season.get('loans', {}).items():
            expense_data.append({'Категория': 'Займы', 'Название': loan_name, 'Сумма': loan_amount})
        
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
                    'Вложение на следующий сезон': '#FFD93D',
                    'Займы': '#95E1D3'
                }
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig, width='stretch')
    else:
        st.info("Расходы не добавлены")

with col4:
    st.subheader("Структура доходов и расходов")
    
    # Круговая диаграмма
    labels = ['Вложено', 'Прибыль', 'Месячные расходы', 'Единовременные расходы', 'Вложение на следующий сезон', 'Займы']
    values = [
        current_season['invested'],
        max(0, current_season['profit']),
        current_season['total_monthly_expenses'],
        current_season['total_one_time_expenses'],
        current_season.get('next_season_investment', 0),
        current_season.get('total_loans', 0)
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
    st.subheader(f"{selected_year} - Сезон 1")
    season1 = data['years'][selected_year]['season1']
    
    # Создаем DataFrame для отображения
    season1_data = {
        'Показатель': ['Вложено', 'Выручка', 'Общие расходы', 'Прибыль', 'Займы', 'Остаток'],
        'Значение': [
            season1['invested'],
            season1['revenue'],
            season1['total_expenses'],
            season1['profit'],
            season1.get('total_loans', 0),
            season1['balance']
        ]
    }
    
    df_season1 = pd.DataFrame(season1_data)
    df_season1['Значение'] = df_season1['Значение'].apply(lambda x: f"{x:,.0f} руб.")
    
    st.dataframe(df_season1, use_container_width=True, hide_index=True)

with col6:
    st.subheader(f"{selected_year} - Сезон 2")
    season2 = data['years'][selected_year]['season2']
    
    # Создаем DataFrame для отображения
    season2_data = {
        'Показатель': ['Вложено', 'Выручка', 'Общие расходы', 'Прибыль', 'Займы', 'Остаток'],
        'Значение': [
            season2['invested'],
            season2['revenue'],
            season2['total_expenses'],
            season2['profit'],
            season2.get('total_loans', 0),
            season2['balance']
        ]
    }
    
    df_season2 = pd.DataFrame(season2_data)
    df_season2['Значение'] = df_season2['Значение'].apply(lambda x: f"{x:,.0f} руб.")
    
    st.dataframe(df_season2, use_container_width=True, hide_index=True)

# График сравнения сезонов
st.subheader("📊 Сравнительный анализ")
comparison_data = {
    'Сезон': [f'{selected_year} Сезон 1', f'{selected_year} Сезон 1', f'{selected_year} Сезон 1', f'{selected_year} Сезон 1', f'{selected_year} Сезон 1', 
              f'{selected_year} Сезон 2', f'{selected_year} Сезон 2', f'{selected_year} Сезон 2', f'{selected_year} Сезон 2', f'{selected_year} Сезон 2'],
    'Показатель': ['Вложено', 'Выручка', 'Прибыль', 'Займы', 'Остаток', 'Вложено', 'Выручка', 'Прибыль', 'Займы', 'Остаток'],
    'Значение': [
        season1['invested'], season1['revenue'], season1['profit'], season1.get('total_loans', 0), season1['balance'],
        season2['invested'], season2['revenue'], season2['profit'], season2.get('total_loans', 0), season2['balance']
    ]
}

df_comparison = pd.DataFrame(comparison_data)

fig = px.bar(
    df_comparison,
    x='Показатель',
    y='Значение',
    color='Сезон',
    title=f"Сравнение показателей по сезонам {selected_year}",
    barmode='group',
    color_discrete_map={f'{selected_year} Сезон 1': '#FF6B6B', f'{selected_year} Сезон 2': '#4ECDC4'}
)
fig.update_layout(height=500)
st.plotly_chart(fig, width='stretch')

# Футер
st.markdown("---")
st.markdown("💡 **Советы:**")
st.markdown("- Используйте функцию переноса остатка для планирования следующего сезона")
st.markdown("- Регулярно сохраняйте изменения")
st.markdown("- Анализируйте структуру расходов для оптимизации")

