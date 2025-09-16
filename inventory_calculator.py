import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# Настройка страницы
st.set_page_config(
    page_title="Калькулятор остатков товара",
    page_icon="📦",
    layout="wide"
)

# Заголовок
st.title("📦 Калькулятор остатков товара для закупки")
st.markdown("---")

@st.cache_data
def load_data(file_path):
    """Загрузка данных из Excel файла"""
    try:
        # Пытаемся прочитать все листы
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

def calculate_inventory_needs(monthly_orders, buyback_rate, return_days=7, safety_stock=0.1):
    """
    Расчет необходимых остатков товара
    
    Параметры:
    - monthly_orders: словарь с заказами по месяцам
    - buyback_rate: процент выкупа (0.0 - 1.0)
    - return_days: дни возврата товара
    - safety_stock: страховой запас (0.0 - 1.0)
    """
    
    results = {}
    cumulative_returns = 0
    
    for month, orders in monthly_orders.items():
        # Товар, который нужно заказать для этого месяца
        needed_for_month = orders
        
        # Возвраты с предыдущих месяцев (если прошло больше return_days)
        if cumulative_returns > 0:
            available_returns = cumulative_returns
            needed_for_month = max(0, needed_for_month - available_returns)
            cumulative_returns -= min(available_returns, orders)
        
        # Товар, который будет возвращен в этом месяце
        returns_this_month = orders * (1 - buyback_rate)
        
        # Добавляем страховой запас
        safety_stock_amount = needed_for_month * safety_stock
        
        # Общий объем закупки для месяца
        total_purchase = needed_for_month + safety_stock_amount
        
        # Накопление возвратов
        cumulative_returns += returns_this_month
        
        results[month] = {
            'orders': orders,
            'needed_for_month': needed_for_month,
            'returns_this_month': returns_this_month,
            'safety_stock': safety_stock_amount,
            'total_purchase': total_purchase,
            'cumulative_returns': cumulative_returns
        }
    
    return results

def create_visualizations(results, buyback_rate):
    """Создание визуализаций"""
    
    # Подготовка данных для графиков
    months = list(results.keys())
    orders = [results[m]['orders'] for m in months]
    purchases = [results[m]['total_purchase'] for m in months]
    returns = [results[m]['returns_this_month'] for m in months]
    cumulative_returns = [results[m]['cumulative_returns'] for m in months]
    
    # График 1: Заказы vs Закупки
    fig1 = go.Figure()
    fig1.add_trace(go.Bar(name='Заказы', x=months, y=orders, marker_color='blue'))
    fig1.add_trace(go.Bar(name='Закупки', x=months, y=purchases, marker_color='red'))
    fig1.update_layout(
        title=f'Заказы vs Закупки (Выкуп: {buyback_rate*100}%)',
        xaxis_title='Месяц',
        yaxis_title='Количество',
        barmode='group'
    )
    
    # График 2: Возвраты и накопленные возвраты
    fig2 = go.Figure()
    fig2.add_trace(go.Bar(name='Возвраты за месяц', x=months, y=returns, marker_color='orange'))
    fig2.add_trace(go.Scatter(name='Накопленные возвраты', x=months, y=cumulative_returns, 
                             mode='lines+markers', line=dict(color='green', width=3)))
    fig2.update_layout(
        title='Динамика возвратов',
        xaxis_title='Месяц',
        yaxis_title='Количество'
    )
    
    # График 3: Эффективность использования возвратов
    efficiency = []
    for m in months:
        if results[m]['orders'] > 0:
            eff = (results[m]['orders'] - results[m]['needed_for_month']) / results[m]['orders'] * 100
            efficiency.append(eff)
        else:
            efficiency.append(0)
    
    fig3 = go.Figure()
    fig3.add_trace(go.Bar(name='Эффективность использования возвратов (%)', 
                          x=months, y=efficiency, marker_color='purple'))
    fig3.update_layout(
        title='Эффективность использования возвратов',
        xaxis_title='Месяц',
        yaxis_title='Процент использования возвратов'
    )
    
    return fig1, fig2, fig3

def main():
    # Боковая панель с параметрами
    st.sidebar.header("⚙️ Параметры расчета")
    
    # Загрузка файла
    uploaded_file = st.sidebar.file_uploader(
        "Загрузите файл с данными (Excel)", 
        type=['xlsx', 'xls']
    )
    
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
        value=10, 
        step=5
    ) / 100
    
    # Основной контент
    if uploaded_file is not None:
        try:
            # Загружаем данные
            data, sheets = load_data(uploaded_file)
            
            if data:
                st.success(f"✅ Файл успешно загружен! Найдено листов: {len(sheets)}")
                
                # Выбор листа
                selected_sheet = st.selectbox("Выберите лист с данными:", sheets)
                
                if selected_sheet:
                    df = data[selected_sheet]
                    st.subheader(f"📊 Данные из листа: {selected_sheet}")
                    
                    # Показываем первые строки данных
                    st.dataframe(df.head(), use_container_width=True)
                    
                    # Анализ структуры данных
                    st.subheader("🔍 Анализ структуры данных")
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write("**Информация о данных:**")
                        st.write(f"- Размер: {df.shape[0]} строк, {df.shape[1]} столбцов")
                        st.write(f"- Столбцы: {list(df.columns)}")
                    
                    with col2:
                        st.write("**Типы данных:**")
                        st.write(df.dtypes)
                    
                    # Ручной ввод данных (если файл не подходит)
                    st.subheader("📝 Ввод данных о заказах")
                    st.info("Если данные в файле не подходят, введите заказы вручную:")
                    
                    # Создаем форму для ручного ввода
                    with st.form("manual_data"):
                        st.write("**Введите заказы по месяцам:**")
                        
                        col1, col2, col3, col4 = st.columns(4)
                        
                        monthly_orders = {}
                        months = ['Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь',
                                'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь']
                        
                        for i, month in enumerate(months):
                            with col1 if i < 3 else col2 if i < 6 else col3 if i < 9 else col4:
                                value = st.number_input(
                                    f"{month}:", 
                                    min_value=0, 
                                    value=100 if i < 6 else 80,
                                    key=f"month_{i}"
                                )
                                monthly_orders[month] = value
                        
                        submitted = st.form_submit_button("Рассчитать остатки")
                        
                        if submitted:
                            # Расчет остатков
                            results = calculate_inventory_needs(
                                monthly_orders, 
                                buyback_rate, 
                                return_days, 
                                safety_stock
                            )
                            
                            # Результаты
                            st.subheader("📈 Результаты расчета")
                            
                            # Таблица результатов
                            results_df = pd.DataFrame(results).T
                            results_df = results_df.round(2)
                            st.dataframe(results_df, use_container_width=True)
                            
                            # Суммарная статистика
                            total_orders = sum(monthly_orders.values())
                            total_purchases = sum(results[m]['total_purchase'] for m in results)
                            total_returns = sum(results[m]['returns_this_month'] for m in results)
                            
                            col1, col2, col3, col4 = st.columns(4)
                            with col1:
                                st.metric("Общий объем заказов", f"{total_orders:,.0f} шт.")
                            with col2:
                                st.metric("Общий объем закупок", f"{total_purchases:,.0f} шт.")
                            with col3:
                                st.metric("Общий объем возвратов", f"{total_returns:,.0f} шт.")
                            with col4:
                                efficiency = ((total_orders - (total_purchases - total_returns)) / total_orders * 100) if total_orders > 0 else 0
                                st.metric("Эффективность (%)", f"{efficiency:.1f}%")
                            
                            # Визуализации
                            st.subheader("📊 Визуализация результатов")
                            
                            fig1, fig2, fig3 = create_visualizations(results, buyback_rate)
                            
                            col1, col2 = st.columns(2)
                            with col1:
                                st.plotly_chart(fig1, use_container_width=True)
                            with col2:
                                st.plotly_chart(fig2, use_container_width=True)
                            
                            st.plotly_chart(fig3, use_container_width=True)
                            
                            # Рекомендации
                            st.subheader("💡 Рекомендации")
                            
                            if buyback_rate < 0.3:
                                st.warning("⚠️ Низкий процент выкупа может привести к большим объемам возвратов")
                            
                            if safety_stock < 0.1:
                                st.info("ℹ️ Рекомендуется увеличить страховой запас для стабильности поставок")
                            
                            # Экспорт результатов
                            st.subheader("💾 Экспорт результатов")
                            
                            # Создаем Excel файл для скачивания
                            output = pd.ExcelWriter('inventory_calculation_results.xlsx', engine='openpyxl')
                            
                            # Лист с результатами
                            results_df.to_excel(output, sheet_name='Результаты расчета')
                            
                            # Лист с параметрами
                            params_df = pd.DataFrame({
                                'Параметр': ['Процент выкупа', 'Дни возврата', 'Страховой запас'],
                                'Значение': [f"{buyback_rate*100}%", f"{return_days} дней", f"{safety_stock*100}%"]
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
                
        except Exception as e:
            st.error(f"Ошибка при обработке файла: {e}")
    else:
        st.info("👆 Загрузите файл с данными в боковой панели для начала работы")
        
        # Демонстрационные данные
        st.subheader("🎯 Пример расчета")
        st.write("""
        **Сценарий:** Товар с выкупом 20%
        - Заказы: 100 шт. в месяц
        - Выкуп: 20 шт. (20%)
        - Возврат: 80 шт. через 7 дней
        - Страховой запас: 10%
        
        **Результат:** Необходимо закупить ~110 шт. для первого месяца
        """)

if __name__ == "__main__":
    main()
















