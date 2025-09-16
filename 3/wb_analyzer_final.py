# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# Настройка страницы
st.set_page_config(
    page_title="Анализатор отчетов WB",
    page_icon="📊",
    layout="wide"
)

st.title("📊 Анализатор отчетов Wildberries")

# Функция для безопасной обработки данных
def safe_process_data(df):
    """Безопасная обработка данных с проверками"""
    try:
        df_clean = df.copy()
        
        # Обрабатываем даты
        df_clean['Дата начала'] = pd.to_datetime(df_clean['Дата начала'], errors='coerce', utc=True).dt.tz_convert(None)
        df_clean['Дата конца'] = pd.to_datetime(df_clean['Дата конца'], errors='coerce', utc=True).dt.tz_convert(None)
        
        # Удаляем строки с пустыми датами
        df_clean = df_clean.dropna(subset=['Дата начала', 'Дата конца'])
        
        # Обрабатываем числовые столбцы
        numeric_cols = ['Итого к оплате', 'Прочие удержания', 'Стоимость логистики', 'Стоимость хранения']
        for col in numeric_cols:
            if col in df_clean.columns:
                # Заменяем NaN на 0
                df_clean[col] = df_clean[col].fillna(0)
                # Убеждаемся, что это числовой тип
                df_clean[col] = pd.to_numeric(df_clean[col], errors='coerce').fillna(0)
        
        # Сортируем по дате
        df_clean = df_clean.sort_values('Дата начала')
        
        return df_clean
    except Exception as e:
        st.error(f"Ошибка при обработке данных: {str(e)}")
        return None

# Функция для расчета метрик
def calculate_safe_metrics(df):
    """Безопасный расчет метрик"""
    try:
        metrics = {}
        
        numeric_cols = ['Итого к оплате', 'Прочие удержания', 'Стоимость логистики', 'Стоимость хранения']
        
        for col in numeric_cols:
            if col in df.columns:
                metrics[col] = {
                    'total': float(df[col].sum()),
                    'average': float(df[col].mean()),
                    'max': float(df[col].max()),
                    'min': float(df[col].min())
                }
        
        # Общая сумма
        total_sum = sum(metrics[col]['total'] for col in metrics.keys())
        metrics['total_all'] = total_sum
        
        # Период
        if 'Дата начала' in df.columns and 'Дата конца' in df.columns:
            start_date = df['Дата начала'].min()
            end_date = df['Дата конца'].max()
            metrics['period'] = f"{start_date.strftime('%d.%m.%Y')} - {end_date.strftime('%d.%m.%Y')}"
            metrics['total_periods'] = len(df)
        
        return metrics
    except Exception as e:
        st.error(f"Ошибка при расчете метрик: {str(e)}")
        return {}

# Функция для создания графиков
def create_safe_charts(df):
    """Безопасное создание графиков"""
    try:
        df_charts = df.copy()
        
        # Группировка по месяцам
        df_charts['Месяц'] = df_charts['Дата начала'].dt.to_period('M')
        monthly_data = df_charts.groupby('Месяц').agg({
            'Итого к оплате': 'sum',
            'Прочие удержания': 'sum',
            'Стоимость логистики': 'sum',
            'Стоимость хранения': 'sum'
        }).reset_index()
        monthly_data['Месяц'] = monthly_data['Месяц'].astype(str)
        
        # Группировка по неделям
        df_charts['Неделя'] = df_charts['Дата начала'].dt.to_period('W')
        weekly_data = df_charts.groupby('Неделя').agg({
            'Итого к оплате': 'sum',
            'Прочие удержания': 'sum',
            'Стоимость логистики': 'sum',
            'Стоимость хранения': 'sum'
        }).reset_index()
        weekly_data['Неделя'] = weekly_data['Неделя'].astype(str)
        
        return monthly_data, weekly_data
    except Exception as e:
        st.error(f"Ошибка при создании графиков: {str(e)}")
        return None, None

# Основной интерфейс
st.sidebar.markdown("## ⚙️ Настройки")

# Загрузка файла
uploaded_file = st.sidebar.file_uploader(
    "Выберите Excel файл с отчетами WB",
    type=['xlsx', 'xls']
)

# Фильтр по датам
st.sidebar.markdown("### 📅 Фильтр по датам")
use_date_filter = st.sidebar.checkbox("Использовать фильтр по датам", value=False)

start_date = None
end_date = None

if use_date_filter:
    st.sidebar.markdown("**Выберите период для анализа:**")
    col1, col2 = st.sidebar.columns(2)
    with col1:
        start_date = st.date_input("Дата от", value=None, help="Начало периода")
    with col2:
        end_date = st.date_input("Дата до", value=None, help="Конец периода")
    
    if start_date and end_date:
        if start_date > end_date:
            st.sidebar.error("❌ Дата начала не может быть позже даты окончания")
            start_date = None
            end_date = None
        else:
            st.sidebar.success(f"✅ Период: {start_date.strftime('%d.%m.%Y')} - {end_date.strftime('%d.%m.%Y')}")

if uploaded_file is None:
    st.info("👆 Загрузите Excel файл с отчетами Wildberries в боковой панели")
    
    st.markdown("### 📋 Требования к файлу:")
    st.markdown("""
    - Столбцы: **Дата начала**, **Дата конца**
    - Финансовые столбцы: **Итого к оплате**, **Прочие удержания**, **Стоимость логистики**, **Стоимость хранения**
    - Каждая строка - отдельный отчет за период
    """)
    
else:
    try:
        with st.spinner("Загружаем данные..."):
            # Загружаем Excel файл
            excel_file = pd.ExcelFile(uploaded_file)
            
            # Выбираем лист
            if len(excel_file.sheet_names) > 1:
                selected_sheet = st.sidebar.selectbox(
                    "Выберите лист:",
                    excel_file.sheet_names,
                    index=0
                )
            else:
                selected_sheet = excel_file.sheet_names[0]
            
            # Загружаем данные
            df = pd.read_excel(uploaded_file, sheet_name=selected_sheet)
            
        st.success(f"✅ Файл загружен: {df.shape[0]} строк, {df.shape[1]} столбцов")
        
        # Показываем информацию о фильтре
        if use_date_filter and (start_date or end_date):
            filter_info = "Фильтр: "
            if start_date:
                filter_info += f"от {start_date.strftime('%d.%m.%Y')} "
            if end_date:
                filter_info += f"до {end_date.strftime('%d.%m.%Y')}"
            st.info(f"📅 {filter_info}")
        
        # Показываем информацию о данных
        st.sidebar.markdown("### 📊 Информация о данных")
        st.sidebar.write(f"**Размер:** {df.shape[0]} отчетов")
        st.sidebar.write(f"**Лист:** {selected_sheet}")
        
        # Проверяем столбцы
        required_columns = ['Дата начала', 'Дата конца', 'Итого к оплате', 'Прочие удержания', 'Стоимость логистики', 'Стоимость хранения']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            st.error(f"❌ Отсутствуют столбцы: {', '.join(missing_columns)}")
            st.markdown("### 📋 Найденные столбцы:")
            for i, col in enumerate(df.columns):
                st.write(f"{i+1}. {col}")
        else:
            st.success("✅ Все необходимые столбцы найдены")
            
            # Обрабатываем данные
            df_clean = safe_process_data(df)
            
            # Применяем фильтр по датам
            if df_clean is not None and use_date_filter and (start_date or end_date):
                if start_date:
                    start_date_dt = pd.to_datetime(start_date)
                    df_clean = df_clean[df_clean['Дата начала'] >= start_date_dt]
                    
                if end_date:
                    end_date_dt = pd.to_datetime(end_date)
                    df_clean = df_clean[df_clean['Дата начала'] <= end_date_dt]
            
            if df_clean is not None and not df_clean.empty:
                # Показываем информацию о количестве записей
                if use_date_filter and (start_date or end_date):
                    st.success(f"✅ Отфильтровано записей: {len(df_clean)} из {len(df)}")
                else:
                    st.success(f"✅ Обработано записей: {len(df_clean)}")
                
                # Рассчитываем метрики
                metrics = calculate_safe_metrics(df_clean)
                
                if metrics:
                    # Отображаем основные метрики
                    st.markdown("### 📈 Основные показатели")
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        st.metric(
                            "Итого к оплате",
                            f"{metrics.get('Итого к оплате', {}).get('total', 0):,.0f} ₽"
                        )
                    
                    with col2:
                        st.metric(
                            "Прочие удержания",
                            f"{metrics.get('Прочие удержания', {}).get('total', 0):,.0f} ₽"
                        )
                    
                    with col3:
                        st.metric(
                            "Стоимость логистики",
                            f"{metrics.get('Стоимость логистики', {}).get('total', 0):,.0f} ₽"
                        )
                    
                    with col4:
                        st.metric(
                            "Стоимость хранения",
                            f"{metrics.get('Стоимость хранения', {}).get('total', 0):,.0f} ₽"
                        )
                    
                    # Общая сумма
                    st.markdown("### 💰 Общая сумма всех показателей")
                    st.markdown(f"""
                    <div style='background-color: #f0f2f6; padding: 1rem; border-radius: 0.5rem; border-left: 4px solid #1f77b4;'>
                        <h3>💰 {metrics.get('total_all', 0):,.0f} ₽</h3>
                        <p>Сумма всех финансовых показателей за период</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Информация о периоде
                    if 'period' in metrics:
                        st.info(f"📅 Период анализа: {metrics['period']} ({metrics.get('total_periods', 0)} отчетов)")
                    
                    # Сводка по периодам
                    st.markdown("### 📋 Сводка по периодам")
                    
                    # Создаем сводку
                    summary = df_clean[['Дата начала', 'Дата конца', '№ отчета', 'Итого к оплате', 
                                      'Прочие удержания', 'Стоимость логистики', 'Стоимость хранения']].copy()
                    
                    # Форматируем даты
                    summary['Дата начала'] = summary['Дата начала'].dt.strftime('%d.%m.%Y')
                    summary['Дата конца'] = summary['Дата конца'].dt.strftime('%d.%m.%Y')
                    
                    # Добавляем общую сумму
                    summary['Общая сумма'] = (summary['Итого к оплате'] + summary['Прочие удержания'] + 
                                            summary['Стоимость логистики'] + summary['Стоимость хранения'])
                    
                    st.dataframe(summary, use_container_width=True)
                    
                    # Графики
                    st.markdown("### 📊 Графики анализа")
                    
                    # Создаем данные для графиков
                    monthly_data, weekly_data = create_safe_charts(df_clean)
                    
                    if monthly_data is not None and weekly_data is not None:
                        # Выбор типа графика
                        chart_type = st.selectbox(
                            "Выберите тип группировки:",
                            ["По месяцам", "По неделям"],
                            index=0
                        )
                        
                        if chart_type == "По месяцам":
                            chart_data = monthly_data
                            x_col = 'Месяц'
                            title = "Динамика показателей по месяцам"
                        else:
                            chart_data = weekly_data
                            x_col = 'Неделя'
                            title = "Динамика показателей по неделям"
                        
                        # Создаем график
                        fig = go.Figure()
                        
                        colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728']
                        columns = ['Итого к оплате', 'Прочие удержания', 'Стоимость логистики', 'Стоимость хранения']
                        
                        for i, col in enumerate(columns):
                            if col in chart_data.columns:
                                fig.add_trace(go.Scatter(
                                    x=chart_data[x_col],
                                    y=chart_data[col],
                                    mode='lines+markers',
                                    name=col,
                                    line=dict(color=colors[i % len(colors)]),
                                    hovertemplate=f'{col}: %{{y:,.0f}} ₽<extra></extra>'
                                ))
                        
                        fig.update_layout(
                            title=title,
                            xaxis_title="Период",
                            yaxis_title="Сумма (₽)",
                            height=500,
                            hovermode='x unified'
                        )
                        
                        st.plotly_chart(fig, use_container_width=True)
                        
                        # Показываем данные графика
                        st.markdown(f"#### Данные {chart_type.lower()}:")
                        st.dataframe(chart_data, use_container_width=True)
                    
                    # Детальная статистика
                    st.markdown("### 📊 Детальная статистика")
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown("#### Итого к оплате:")
                        payment_metrics = metrics.get('Итого к оплате', {})
                        st.write(f"- **Общая сумма:** {payment_metrics.get('total', 0):,.0f} ₽")
                        st.write(f"- **Среднее значение:** {payment_metrics.get('average', 0):,.0f} ₽")
                        st.write(f"- **Максимум:** {payment_metrics.get('max', 0):,.0f} ₽")
                        st.write(f"- **Минимум:** {payment_metrics.get('min', 0):,.0f} ₽")
                    
                    with col2:
                        st.markdown("#### Прочие удержания:")
                        deduction_metrics = metrics.get('Прочие удержания', {})
                        st.write(f"- **Общая сумма:** {deduction_metrics.get('total', 0):,.0f} ₽")
                        st.write(f"- **Среднее значение:** {deduction_metrics.get('average', 0):,.0f} ₽")
                        st.write(f"- **Максимум:** {deduction_metrics.get('max', 0):,.0f} ₽")
                        st.write(f"- **Минимум:** {deduction_metrics.get('min', 0):,.0f} ₽")
                    
                    col3, col4 = st.columns(2)
                    
                    with col3:
                        st.markdown("#### Стоимость логистики:")
                        logistics_metrics = metrics.get('Стоимость логистики', {})
                        st.write(f"- **Общая сумма:** {logistics_metrics.get('total', 0):,.0f} ₽")
                        st.write(f"- **Среднее значение:** {logistics_metrics.get('average', 0):,.0f} ₽")
                        st.write(f"- **Максимум:** {logistics_metrics.get('max', 0):,.0f} ₽")
                        st.write(f"- **Минимум:** {logistics_metrics.get('min', 0):,.0f} ₽")
                    
                    with col4:
                        st.markdown("#### Стоимость хранения:")
                        storage_metrics = metrics.get('Стоимость хранения', {})
                        st.write(f"- **Общая сумма:** {storage_metrics.get('total', 0):,.0f} ₽")
                        st.write(f"- **Среднее значение:** {storage_metrics.get('average', 0):,.0f} ₽")
                        st.write(f"- **Максимум:** {storage_metrics.get('max', 0):,.0f} ₽")
                        st.write(f"- **Минимум:** {storage_metrics.get('min', 0):,.0f} ₽")
                    
                    # Экспорт данных
                    st.markdown("### 💾 Экспорт данных")
                    
                    # CSV экспорт
                    csv_data = summary.to_csv(index=False, encoding='utf-8-sig')
                    st.download_button(
                        label="📥 Скачать сводку в CSV",
                        data=csv_data,
                        file_name=f"wb_reports_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv"
                    )
                    
            else:
                st.error("После обработки данных не осталось записей для анализа.")
                
    except Exception as e:
        st.error(f"❌ Ошибка при загрузке файла: {str(e)}")
        import traceback
        st.code(traceback.format_exc())

# Футер
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666;'>
    📊 Анализатор отчетов Wildberries | Финальная версия
</div>
""", unsafe_allow_html=True)



















