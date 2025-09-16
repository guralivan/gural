import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import calendar

# Настройка страницы
st.set_page_config(
    page_title="Калькулятор заказов и баланса",
    page_icon="📦",
    layout="wide"
)

# Заголовок приложения
st.title("📦 Калькулятор заказов и баланса товаров")
st.markdown("---")

# Определение месяцев
months = [
    "Январь", "Февраль", "Март", "Апрель", "Май", "Июнь",
    "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь"
]

# Инициализация сессии
if 'orders_data' not in st.session_state:
    st.session_state.orders_data = {}
if 'return_percentage' not in st.session_state:
    st.session_state.return_percentage = 0.0
if 'initial_balance' not in st.session_state:
    st.session_state.initial_balance = 0

# Основная область
st.header("⚙️ Настройки и анализ")

# Создаем колонки для настроек
col_settings1, col_settings2, col_settings3 = st.columns(3)

with col_settings1:
    # Процент выкупа
    return_percentage = st.number_input(
        "Процент выкупа (%)",
        min_value=0.0,
        max_value=100.0,
        value=st.session_state.return_percentage,
        step=0.1,
        help="Процент товаров, которые будут выкуплены"
    )
    st.session_state.return_percentage = return_percentage

with col_settings2:
    # Начальный баланс
    initial_balance = st.number_input(
        "Начальный баланс товаров",
        min_value=0,
        value=st.session_state.initial_balance,
        step=1,
        help="Количество товаров на складе в начале периода"
    )
    st.session_state.initial_balance = initial_balance

with col_settings3:
    st.write("")
    st.write("")
    # Кнопка для очистки данных
    if st.button("🗑️ Очистить все данные", type="secondary"):
        st.session_state.orders_data = {}
        st.rerun()

# Расчет минимального необходимого баланса
def calculate_min_balance():
    if not st.session_state.orders_data:
        return {
            'simple': 0,
            'optimal': 0,
            'with_returns': 0
        }
    
    # Простой расчет - общее количество заказов
    total_orders = sum(st.session_state.orders_data.values())
    
    # Продвинутый расчет с учетом возвратов
    def calculate_optimal_balance():
        if not st.session_state.orders_data:
            return 0
        
        max_deficit = 0
        current_balance = 0
        returned_from_previous = 0
        total_orders = 0
        
        for month in months:
            for week in range(1, 6):
                orders_key = f"{month}_{week}"
                orders = st.session_state.orders_data.get(orders_key, 0)
                
                if orders > 0:
                    total_orders += orders
                    # Списываем заказы
                    current_balance = current_balance - orders + returned_from_previous
                    
                    # Если баланс отрицательный, это дефицит
                    if current_balance < 0:
                        deficit = abs(current_balance)
                        if deficit > max_deficit:
                            max_deficit = deficit
                    
                    # Возвращенные товары придут на следующую неделю
                    returned = orders * (1 - return_percentage / 100)
                    returned_from_previous = returned
        
        # Если нет дефицита, возвращаем минимальный баланс (первый заказ)
        if max_deficit == 0 and total_orders > 0:
            # Находим первый заказ
            for month in months:
                for week in range(1, 6):
                    orders_key = f"{month}_{week}"
                    orders = st.session_state.orders_data.get(orders_key, 0)
                    if orders > 0:
                        return orders  # Возвращаем размер первого заказа как минимальный баланс
        
        return max_deficit
    
    optimal_balance = calculate_optimal_balance()
    
    return {
        'simple': total_orders,
        'optimal': optimal_balance,
        'with_returns': total_orders - (total_orders * (return_percentage / 100))
    }

min_required_balance = calculate_min_balance()

# Подсказка о минимальном балансе
if min_required_balance['simple'] > 0:
    st.markdown("---")
    st.subheader("💡 Анализ необходимого баланса")
    
    # Создаем колонки для разных типов расчетов
    col_analysis1, col_analysis2, col_analysis3, col_analysis4 = st.columns(4)
    
    with col_analysis1:
        st.metric(
            "📊 Простой расчет", 
            f"{min_required_balance['simple']:,}",
            help="Общее количество всех заказов"
        )
    
    with col_analysis2:
        st.metric(
            "🔄 С учетом возвратов", 
            f"{round(min_required_balance['with_returns']):,}",
            help="Заказы минус выкупленные товары"
        )
    
    with col_analysis3:
        st.metric(
            "⚡ Оптимальный баланс", 
            f"{min_required_balance['optimal']:,}",
            help="Минимальный баланс для избежания дефицита"
        )
    
    with col_analysis4:
        if min_required_balance['optimal'] > 0:
            st.metric(
                "💰 Экономия", 
                f"{min_required_balance['simple'] - min_required_balance['optimal']:,}",
                help="Разница между простым и оптимальным расчетом"
            )
        else:
            st.metric(
                "💰 Экономия", 
                "0",
                help="Нет экономии"
            )
    
    # Рекомендация
    if min_required_balance['optimal'] > 0:
        recommended_balance = min_required_balance['optimal']
        recommendation_type = "оптимальный"
    else:
        recommended_balance = min_required_balance['simple']
        recommendation_type = "минимальный"
    
    col_recommendation1, col_recommendation2 = st.columns(2)
    
    with col_recommendation1:
        if initial_balance >= recommended_balance:
            st.success(f"✅ Баланс достаточен! {recommendation_type.capitalize()}: {recommended_balance:,}")
        else:
            st.warning(f"⚠️ {recommendation_type.capitalize()} баланс: **{recommended_balance:,}** товаров")
    
    with col_recommendation2:
        if initial_balance < recommended_balance:
            st.info(f"📊 Текущий: {initial_balance:,} | Необходимо добавить: {recommended_balance - initial_balance:,}")
        else:
            st.info(f"📊 Текущий баланс: {initial_balance:,} товаров")
    
    # Детализация по неделям
    with st.expander("📋 Детализация по неделям"):
        weekly_analysis = []
        cumulative_orders = 0
        
        for month in months:
            for week in range(1, 6):
                orders_key = f"{month}_{week}"
                orders = st.session_state.orders_data.get(orders_key, 0)
                if orders > 0:
                    cumulative_orders += orders
                    weekly_analysis.append({
                        "Месяц": month,
                        "Неделя": week,
                        "Заказы на неделю": orders,
                        "Накопительные заказы": cumulative_orders,
                        "Необходимый баланс": cumulative_orders
                    })
        
        if weekly_analysis:
            df_analysis = pd.DataFrame(weekly_analysis)
            st.dataframe(df_analysis, width='stretch')
            
            # График потребности в товарах
            if len(weekly_analysis) > 1:
                st.line_chart(df_analysis.set_index("Неделя")["Накопительные заказы"])
        else:
            st.info("Нет данных для анализа. Добавьте заказы в форму ниже.")
else:
    st.info("💡 Введите заказы ниже, чтобы увидеть анализ необходимого баланса")

# Основная область
st.header("📊 Ввод данных по месяцам")

# Выбор месяца
selected_month = st.selectbox("Выберите месяц:", months)

# Ввод заказов по неделям
st.subheader(f"Заказы для {selected_month}")

# Получаем количество недель в выбранном месяце
current_year = datetime.now().year
month_num = months.index(selected_month) + 1
_, num_weeks = calendar.monthrange(current_year, month_num)

# Создаем форму для ввода заказов
with st.form(key=f"form_{selected_month}"):
    orders_input = {}
    
    for week in range(1, 6):  # Максимум 5 недель
        col1, col2 = st.columns([1, 2])
        with col1:
            st.write(f"Неделя {week}:")
        with col2:
            orders_input[week] = st.number_input(
                f"Количество заказов",
                min_value=0,
                value=st.session_state.orders_data.get(f"{selected_month}_{week}", 0),
                key=f"orders_{selected_month}_{week}"
            )
    
    submitted = st.form_submit_button("💾 Сохранить заказы")
    
    if submitted:
        for week, orders in orders_input.items():
            st.session_state.orders_data[f"{selected_month}_{week}"] = orders
        st.success(f"Данные для {selected_month} сохранены!")
        st.rerun()

# Общая статистика
if st.session_state.orders_data:
    st.markdown("---")
    st.subheader("📈 Общая статистика")
    
    col_stats1, col_stats2, col_stats3, col_stats4 = st.columns(4)
    
    # Подсчет общей статистики
    total_orders = sum(st.session_state.orders_data.values())
    total_purchased = total_orders * (return_percentage / 100)
    total_returned = total_orders - total_purchased
    
    with col_stats1:
        st.metric("Всего заказов", f"{total_orders:,}")
    
    with col_stats2:
        st.metric("Выкуплено", f"{round(total_purchased):,}")
    
    with col_stats3:
        st.metric("Возвращено", f"{round(total_returned):,}")
    
    with col_stats4:
        st.metric("Процент выкупа", f"{return_percentage:.1f}%")

# Создание таблицы с данными
st.header("📋 Таблица заказов и баланса")

def create_orders_table():
    data = []
    current_balance = st.session_state.initial_balance
    returned_from_previous_week = 0  # Возвращенные товары с предыдущей недели
    
    for month in months:
        for week in range(1, 6):
            orders_key = f"{month}_{week}"
            orders = st.session_state.orders_data.get(orders_key, 0)
            
            if orders > 0:  # Показываем только строки с заказами
                # Расчет выкупленных товаров
                purchased = orders * (return_percentage / 100)
                returned = orders - purchased
                
                # Обновление баланса: списываем заказы, добавляем возвращенные с предыдущей недели
                balance_before = current_balance
                current_balance = current_balance - orders + returned_from_previous_week
                
                # Формируем отображение баланса
                if returned_from_previous_week > 0:
                    balance_display = f"{balance_before}-{orders}+{returned_from_previous_week:.0f}={current_balance:.0f}"
                else:
                    balance_display = f"{balance_before}-{orders}={current_balance:.0f}"
                
                data.append({
                    "Месяц": month,
                    "Неделя": week,
                    "Заказано товаров": orders,
                    "Выкуплено": f"{round(purchased)}",
                    "Возвращено с прошлой недели": f"{round(returned_from_previous_week)}",
                    "Баланс": balance_display
                })
                
                # Возвращенные товары придут на следующую неделю
                returned_from_previous_week = returned
    
    return pd.DataFrame(data)

# Отображение таблицы
if st.session_state.orders_data:
    df = create_orders_table()
    if not df.empty:
        st.dataframe(df, width='stretch')
        
        # Экспорт данных
        csv = df.to_csv(index=False, encoding='utf-8-sig')
        st.download_button(
            label="📥 Скачать таблицу (CSV)",
            data=csv,
            file_name=f"заказы_и_баланс_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )
    else:
        st.info("Нет данных для отображения. Добавьте заказы в форму выше.")
else:
    st.info("Данные отсутствуют. Начните с ввода заказов в форме выше.")

# Дополнительная информация
st.markdown("---")
st.header("ℹ️ Как использовать приложение")

with st.expander("Инструкция по использованию"):
    st.markdown("""
    ### Пошаговая инструкция:
    
    1. **Настройте параметры** в боковой панели:
       - Установите процент выкупа (например, 70%)
       - Введите начальный баланс товаров
    
    2. **Введите заказы по месяцам**:
       - Выберите месяц из выпадающего списка
       - Введите количество заказов для каждой недели
       - Нажмите "Сохранить заказы"
    
    3. **Просматривайте результаты**:
       - Таблица автоматически обновляется
       - Показывает месяцы, недели, заказы, выкупленные товары и баланс
       - Баланс отображается в формате: текущий+возвращенные=новый
    
    ### Логика расчетов:
    - **Выкуплено** = Заказано × (Процент выкупа / 100)
    - **Возвращено** = Заказано - Выкуплено
    - **Новый баланс** = Текущий баланс + Возвращенные товары
    """)

# Футер
st.markdown("---")
st.markdown("*Приложение для расчета заказов и баланса товаров*")
