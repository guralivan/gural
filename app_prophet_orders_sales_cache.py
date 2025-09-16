import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta
from prophet import Prophet
from prophet.plot import plot_plotly
import os

# Настройки страницы
st.set_page_config(
    page_title="🔮 Прогнозирование заказов и продаж с Prophet",
    page_icon="🔮",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Стили
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
        margin: 0.5rem 0;
    }
    .success-card {
        background-color: #d4edda;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
        border-left: 4px solid #28a745;
    }
    .cache-info {
        background-color: #e3f2fd;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
        border-left: 4px solid #2196f3;
    }
    .analysis-tabs {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Заголовок
st.markdown('<h1 class="main-header">🔮 Прогнозирование заказов и продаж с Prophet</h1>', unsafe_allow_html=True)
st.markdown("**Комплексный анализ заказов и продаж на основе данных из кеша приложения с использованием модели Prophet**")

# ================= ФУНКЦИИ ДЛЯ ЗАГРУЗКИ ДАННЫХ =================

@st.cache_data
def load_data_from_cache(cache_file="data_cache.csv"):
    """Загружает данные из кеша приложения"""
    try:
        if not os.path.exists(cache_file):
            st.error(f"❌ Файл кеша {cache_file} не найден!")
            return None
        
        df = pd.read_csv(cache_file)
        
        # Преобразуем дату
        df['Дата'] = pd.to_datetime(df['Дата'])
        
        # Преобразуем числовые столбцы
        numeric_columns = [
            'Заказали, шт', 'Заказали ВБ клуб, шт', 'Выкупили, шт', 'Выкупили ВБ клуб, шт',
            'Заказали на сумму, ₽', 'Заказали на сумму ВБ клуб, ₽',
            'Выкупили на сумму, ₽', 'Выкупили на сумму ВБ клуб, ₽'
        ]
        
        for col in numeric_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Добавляем общие показатели
        df['Общие заказы'] = df['Заказали, шт'].fillna(0) + df['Заказали ВБ клуб, шт'].fillna(0)
        df['Общие выкупы'] = df['Выкупили, шт'].fillna(0) + df['Выкупили ВБ клуб, шт'].fillna(0)
        df['Общая выручка'] = df['Выкупили на сумму, ₽'].fillna(0) + df['Выкупили на сумму ВБ клуб, ₽'].fillna(0)
        df['Общая сумма заказов'] = df['Заказали на сумму, ₽'].fillna(0) + df['Заказали на сумму ВБ клуб, ₽'].fillna(0)
        
        return df
    except Exception as e:
        st.error(f"Ошибка загрузки данных из кеша: {e}")
        return None

def get_cache_info(cache_file="data_cache.csv"):
    """Получает информацию о кеше"""
    if os.path.exists(cache_file):
        try:
            df = pd.read_csv(cache_file)
            df['Дата'] = pd.to_datetime(df['Дата'])
            return {
                'exists': True,
                'records': len(df),
                'start_date': df['Дата'].min(),
                'end_date': df['Дата'].max(),
                'years': sorted(df['Дата'].dt.year.unique()),
                'file_size': os.path.getsize(cache_file) / 1024 / 1024  # MB
            }
        except:
            return {'exists': False}
    return {'exists': False}

def aggregate_data_by_date(df, metric):
    """Агрегирует данные по дате для выбранной метрики"""
    if df is None or df.empty:
        return None
    
    # Группируем по дате и суммируем выбранную метрику
    aggregated = df.groupby('Дата')[metric].sum().reset_index()
    aggregated = aggregated.sort_values('Дата')
    
    return aggregated

# ================= ФУНКЦИИ ПРОГНОЗИРОВАНИЯ PROPHET =================

def prophet_forecast(df_prophet, periods=30, seasonality_mode='additive', changepoint_prior_scale=0.05, weekly_seasonality=True, yearly_seasonality=True):
    """Прогнозирование с использованием Prophet"""
    model = Prophet(
        seasonality_mode=seasonality_mode,
        changepoint_prior_scale=changepoint_prior_scale,
        weekly_seasonality=weekly_seasonality,
        yearly_seasonality=yearly_seasonality
    )
    model.fit(df_prophet)
    
    future = model.make_future_dataframe(periods=periods)
    forecast = model.predict(future)
    
    return model, forecast

# ================= ОСНОВНОЙ ИНТЕРФЕЙС =================

# Показываем информацию о кеше
cache_info = get_cache_info()

if cache_info['exists']:
    st.markdown(f"""
    <div class="cache-info">
        <h4>📁 Информация о кеше данных</h4>
        <p><strong>Файл:</strong> data_cache.csv</p>
        <p><strong>Записей:</strong> {cache_info['records']:,}</p>
        <p><strong>Период:</strong> {cache_info['start_date'].strftime('%d.%m.%Y')} - {cache_info['end_date'].strftime('%d.%m.%Y')}</p>
        <p><strong>Годы:</strong> {', '.join(map(str, cache_info['years']))}</p>
        <p><strong>Размер файла:</strong> {cache_info['file_size']:.2f} MB</p>
    </div>
    """, unsafe_allow_html=True)
else:
    st.error("❌ Кеш данных не найден! Убедитесь, что файл data_cache.csv существует.")
    st.stop()

# Загружаем данные
df = load_data_from_cache()

if df is None:
    st.error("❌ Не удалось загрузить данные из кеша")
    st.stop()

# Боковая панель
st.sidebar.header("📊 Настройки анализа")

# Выбор метрики для анализа
st.sidebar.markdown("### 📈 Выберите метрику для анализа")
metric_options = {
    'Общие заказы': 'Общие заказы',
    'Общие выкупы (продажи)': 'Общие выкупы',
    'Общая выручка': 'Общая выручка',
    'Общая сумма заказов': 'Общая сумма заказов'
}

selected_metric = st.sidebar.selectbox(
    "Метрика:",
    list(metric_options.keys()),
    help="Выберите показатель для прогнозирования"
)

# Агрегируем данные по выбранной метрике
data = aggregate_data_by_date(df, metric_options[selected_metric])

if data is None or data.empty:
    st.error("❌ Не удалось агрегировать данные")
    st.stop()

# Подготавливаем данные для Prophet
df_prophet = data[['Дата', metric_options[selected_metric]]].rename(columns={'Дата': 'ds', metric_options[selected_metric]: 'y'})

# Показываем информацию о данных
st.sidebar.markdown("### 📋 Информация о данных")
st.sidebar.metric("Всего записей", f"{len(df):,}")
st.sidebar.metric("Дней данных", f"{len(data):,}")

date_range = data['Дата'].max() - data['Дата'].min()
st.sidebar.metric("Период данных", f"{date_range.days} дней")

total_value = data[metric_options[selected_metric]].sum()
st.sidebar.metric(f"Общее значение {selected_metric.lower()}", f"{total_value:,.0f}")

# Настройки прогнозирования Prophet
st.sidebar.markdown("### ⚙️ Настройки Prophet")

periods = st.sidebar.slider(
    "Период прогнозирования (дни):",
    min_value=7,
    max_value=365,
    value=30
)

seasonality_mode = st.sidebar.selectbox(
    "Режим сезонности:",
    ['additive', 'multiplicative'],
    help="Additive: сезонность добавляется к тренду. Multiplicative: сезонность умножается на тренд."
)

changepoint_prior_scale = st.sidebar.slider(
    "Чувствительность к изменениям тренда (changepoint_prior_scale):",
    min_value=0.001,
    max_value=0.5,
    value=0.05,
    step=0.001,
    help="Чем выше значение, тем более гибкой будет модель к изменениям тренда."
)

# Дополнительные настройки Prophet
st.sidebar.markdown("### 🔧 Дополнительные настройки")

weekly_seasonality = st.sidebar.checkbox("Недельная сезонность", value=True)
yearly_seasonality = st.sidebar.checkbox("Годовая сезонность", value=True)

# Основной контент
st.markdown(f"### 📈 Анализ {selected_metric.lower()} и прогнозирование с Prophet")

# Создаем вкладки для разных видов анализа
tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 Обзор данных", "🔮 Прогнозирование", "📈 Сравнение метрик", "📋 Детальная статистика", "🎯 KPI по прогнозу"])

with tab1:
    st.markdown("#### 📊 Обзор данных")
    
    # Показываем данные
    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown(f"#### 📊 График {selected_metric.lower()} по дням")
        fig_data = go.Figure()
        fig_data.add_trace(go.Scatter(
            x=data['Дата'], 
            y=data[metric_options[selected_metric]], 
            mode='lines', 
            name=f'Исторические {selected_metric.lower()}',
            line=dict(color='blue', width=2)
        ))
        fig_data.update_layout(
            title=f"Исторические данные: {selected_metric}", 
            xaxis_title='Дата', 
            yaxis_title=selected_metric,
            hovermode='x unified'
        )
        st.plotly_chart(fig_data, use_container_width=True)

    with col2:
        st.markdown(f"#### 📊 Статистика {selected_metric.lower()}")
        metric_values = data[metric_options[selected_metric]]
        
        col2_1, col2_2 = st.columns(2)
        with col2_1:
            st.metric("Среднее в день", f"{metric_values.mean():.1f}")
            st.metric("Медиана", f"{metric_values.median():.1f}")
        with col2_2:
            st.metric("Максимум", f"{metric_values.max():.0f}")
            st.metric("Минимум", f"{metric_values.min():.0f}")

with tab2:
    st.markdown("#### 🔮 Прогнозирование с Prophet")
    
    # Создание прогноза
    if st.button("🔮 Создать прогноз с Prophet", type="primary"):
        with st.spinner("Создаю прогноз с Prophet..."):
            model, forecast = prophet_forecast(
                df_prophet, 
                periods, 
                seasonality_mode, 
                changepoint_prior_scale,
                weekly_seasonality,
                yearly_seasonality
            )
            
            st.success("✅ Прогноз создан успешно!")
            
            # Сохраняем модель и прогноз в session state для использования в других вкладках
            st.session_state['model'] = model
            st.session_state['forecast'] = forecast
            
            # График прогноза
            st.markdown(f"#### 📈 График прогноза {selected_metric.lower()}")
            fig_prophet = plot_plotly(model, forecast)
            fig_prophet.update_layout(
                title=f"Прогноз {selected_metric.lower()} с Prophet на {periods} дней", 
                yaxis_title=selected_metric
            )
            st.plotly_chart(fig_prophet, use_container_width=True)
            
            # Компоненты прогноза
            st.markdown("#### 📉 Компоненты прогноза Prophet")
            fig_components = model.plot_components(forecast)
            st.write(fig_components)
            
            # Статистика прогноза
            st.markdown("#### 📊 Статистика прогноза")
            
            forecast_values = forecast['yhat'][-periods:].values
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Средний прогноз", f"{np.mean(forecast_values):.1f}")
            with col2:
                st.metric("Максимальный прогноз", f"{np.max(forecast_values):.0f}")
            with col3:
                st.metric("Минимальный прогноз", f"{np.min(forecast_values):.0f}")
            with col4:
                last_historical_value = data[metric_options[selected_metric]].iloc[-1]
                if last_historical_value != 0:
                    change = ((forecast_values[-1] - last_historical_value) / last_historical_value * 100)
                    st.metric("Изменение", f"{change:.1f}%")
                else:
                    st.metric("Изменение", "N/A")
            
            # Таблица прогноза
            st.markdown("#### 📋 Детальный прогноз")
            
            forecast_df_display = forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']][-periods:]
            forecast_df_display.columns = ['Дата', 'Прогноз', 'Нижняя граница', 'Верхняя граница']
            forecast_df_display['Дата'] = forecast_df_display['Дата'].dt.strftime('%d.%m.%Y')
            forecast_df_display['Прогноз'] = forecast_df_display['Прогноз'].round(1)
            forecast_df_display['Нижняя граница'] = forecast_df_display['Нижняя граница'].round(1)
            forecast_df_display['Верхняя граница'] = forecast_df_display['Верхняя граница'].round(1)
            
            st.dataframe(forecast_df_display, use_container_width=True)
            
            # Кнопка скачивания
            csv = forecast_df_display.to_csv(index=False)
            st.download_button(
                label="📥 Скачать прогноз (CSV)",
                data=csv,
                file_name=f"prophet_forecast_{selected_metric.lower().replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )

with tab3:
    st.markdown("#### 📈 Сравнение всех метрик")
    
    # Агрегируем все метрики
    orders_data = aggregate_data_by_date(df, 'Общие заказы')
    sales_data = aggregate_data_by_date(df, 'Общие выкупы')
    revenue_data = aggregate_data_by_date(df, 'Общая выручка')
    orders_sum_data = aggregate_data_by_date(df, 'Общая сумма заказов')
    
    # Создаем сравнительный график
    fig_comparison = go.Figure()
    
    fig_comparison.add_trace(go.Scatter(
        x=orders_data['Дата'], 
        y=orders_data['Общие заказы'], 
        mode='lines', 
        name='Заказы',
        line=dict(color='blue', width=2)
    ))
    
    fig_comparison.add_trace(go.Scatter(
        x=sales_data['Дата'], 
        y=sales_data['Общие выкупы'], 
        mode='lines', 
        name='Продажи (выкупы)',
        line=dict(color='green', width=2)
    ))
    
    fig_comparison.update_layout(
        title="Сравнение заказов и продаж по дням", 
        xaxis_title='Дата', 
        yaxis_title='Количество',
        hovermode='x unified'
    )
    st.plotly_chart(fig_comparison, use_container_width=True)
    
    # График выручки
    fig_revenue = go.Figure()
    
    fig_revenue.add_trace(go.Scatter(
        x=revenue_data['Дата'], 
        y=revenue_data['Общая выручка'], 
        mode='lines', 
        name='Выручка от продаж',
        line=dict(color='orange', width=2)
    ))
    
    fig_revenue.add_trace(go.Scatter(
        x=orders_sum_data['Дата'], 
        y=orders_sum_data['Общая сумма заказов'], 
        mode='lines', 
        name='Сумма заказов',
        line=dict(color='red', width=2)
    ))
    
    fig_revenue.update_layout(
        title="Сравнение выручки и суммы заказов", 
        xaxis_title='Дата', 
        yaxis_title='Сумма (₽)',
        hovermode='x unified'
    )
    st.plotly_chart(fig_revenue, use_container_width=True)
    
    # Метрики конверсии
    st.markdown("#### 📊 Ключевые метрики")
    
    total_orders = orders_data['Общие заказы'].sum()
    total_sales = sales_data['Общие выкупы'].sum()
    total_revenue = revenue_data['Общая выручка'].sum()
    total_orders_sum = orders_sum_data['Общая сумма заказов'].sum()
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        conversion_rate = (total_sales / total_orders * 100) if total_orders > 0 else 0
        st.metric("Конверсия заказов в продажи", f"{conversion_rate:.1f}%")
    
    with col2:
        avg_order_value = (total_orders_sum / total_orders) if total_orders > 0 else 0
        st.metric("Средний чек заказа", f"{avg_order_value:,.0f} ₽")
    
    with col3:
        avg_sale_value = (total_revenue / total_sales) if total_sales > 0 else 0
        st.metric("Средний чек продажи", f"{avg_sale_value:,.0f} ₽")
    
    with col4:
        revenue_per_order = (total_revenue / total_orders) if total_orders > 0 else 0
        st.metric("Выручка на заказ", f"{revenue_per_order:,.0f} ₽")

with tab4:
    st.markdown("#### 📋 Детальная статистика по всем метрикам")
    
    # Создаем таблицу со статистикой
    metrics_stats = []
    
    for metric_name, metric_col in metric_options.items():
        metric_data = aggregate_data_by_date(df, metric_col)
        if metric_data is not None and not metric_data.empty:
            values = metric_data[metric_col]
            stats = {
                'Метрика': metric_name,
                'Общее значение': f"{values.sum():,.0f}",
                'Среднее в день': f"{values.mean():.1f}",
                'Медиана': f"{values.median():.1f}",
                'Максимум': f"{values.max():.0f}",
                'Минимум': f"{values.min():.0f}",
                'Стандартное отклонение': f"{values.std():.1f}"
            }
            metrics_stats.append(stats)
    
    if metrics_stats:
        stats_df = pd.DataFrame(metrics_stats)
        st.dataframe(stats_df, use_container_width=True)
    
    # Корреляционная матрица
    st.markdown("#### 🔗 Корреляция между метриками")
    
    # Подготавливаем данные для корреляции
    correlation_data = []
    for metric_name, metric_col in metric_options.items():
        metric_data = aggregate_data_by_date(df, metric_col)
        if metric_data is not None and not metric_data.empty:
            correlation_data.append(metric_data.set_index('Дата')[metric_col])
    
    if len(correlation_data) > 1:
        correlation_df = pd.concat(correlation_data, axis=1)
        correlation_df.columns = list(metric_options.keys())
        correlation_matrix = correlation_df.corr()
        
        fig_corr = go.Figure(data=go.Heatmap(
            z=correlation_matrix.values,
            x=correlation_matrix.columns,
            y=correlation_matrix.columns,
            colorscale='RdBu',
            zmid=0
        ))
        
        fig_corr.update_layout(
            title="Корреляционная матрица метрик",
            xaxis_title="Метрики",
            yaxis_title="Метрики"
        )
        
        st.plotly_chart(fig_corr, use_container_width=True)

with tab5:
    st.markdown("#### 🎯 KPI по прогнозу")
    
    # Проверяем, есть ли данные для расчета KPI
    if 'model' in st.session_state and 'forecast' in st.session_state:
        st.success("✅ Данные прогноза доступны для расчета KPI")
        
        # Основные KPI прогноза
        st.markdown("##### 📊 Основные KPI прогноза")
        
        # Получаем данные прогноза
        forecast = st.session_state['forecast']
        forecast_values = forecast['yhat'][-periods:].values
        forecast_lower = forecast['yhat_lower'][-periods:].values
        forecast_upper = forecast['yhat_upper'][-periods:].values
        
        # Исторические данные для сравнения
        historical_values = data[metric_options[selected_metric]].values
        last_30_days = historical_values[-30:] if len(historical_values) >= 30 else historical_values
        
        # Расчет KPI
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            # Средний прогноз
            avg_forecast = np.mean(forecast_values)
            avg_historical = np.mean(last_30_days)
            growth_rate = ((avg_forecast - avg_historical) / avg_historical * 100) if avg_historical > 0 else 0
            
            st.metric(
                "Средний прогноз", 
                f"{avg_forecast:.1f}",
                f"{growth_rate:+.1f}%"
            )
        
        with col2:
            # Максимальный прогноз
            max_forecast = np.max(forecast_values)
            max_historical = np.max(last_30_days)
            max_growth = ((max_forecast - max_historical) / max_historical * 100) if max_historical > 0 else 0
            
            st.metric(
                "Максимальный прогноз", 
                f"{max_forecast:.0f}",
                f"{max_growth:+.1f}%"
            )
        
        with col3:
            # Минимальный прогноз
            min_forecast = np.min(forecast_values)
            min_historical = np.min(last_30_days)
            min_growth = ((min_forecast - min_historical) / min_historical * 100) if min_historical > 0 else 0
            
            st.metric(
                "Минимальный прогноз", 
                f"{min_forecast:.0f}",
                f"{min_growth:+.1f}%"
            )
        
        with col4:
            # Общий прогноз на период
            total_forecast = np.sum(forecast_values)
            total_historical = np.sum(last_30_days)
            total_growth = ((total_forecast - total_historical) / total_historical * 100) if total_historical > 0 else 0
            
            st.metric(
                "Общий прогноз", 
                f"{total_forecast:.0f}",
                f"{total_growth:+.1f}%"
            )
        
        # Дополнительные KPI
        st.markdown("##### 📈 Дополнительные KPI")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            # Коэффициент вариации (стабильность прогноза)
            cv_forecast = (np.std(forecast_values) / np.mean(forecast_values) * 100) if np.mean(forecast_values) > 0 else 0
            cv_historical = (np.std(last_30_days) / np.mean(last_30_days) * 100) if np.mean(last_30_days) > 0 else 0
            
            st.metric(
                "Коэффициент вариации прогноза", 
                f"{cv_forecast:.1f}%",
                f"Исторический: {cv_historical:.1f}%"
            )
        
        with col2:
            # Средняя неопределенность
            uncertainty = np.mean(forecast_upper - forecast_lower)
            uncertainty_pct = (uncertainty / np.mean(forecast_values) * 100) if np.mean(forecast_values) > 0 else 0
            
            st.metric(
                "Средняя неопределенность", 
                f"{uncertainty:.1f}",
                f"{uncertainty_pct:.1f}% от прогноза"
            )
        
        with col3:
            # Тренд прогноза (наклон)
            x = np.arange(len(forecast_values))
            trend_slope = np.polyfit(x, forecast_values, 1)[0]
            trend_direction = "📈 Рост" if trend_slope > 0 else "📉 Спад" if trend_slope < 0 else "➡️ Стабильно"
            
            st.metric(
                "Тренд прогноза", 
                f"{trend_slope:.2f}/день",
                trend_direction
            )
        
        with col4:
            # Доверительный интервал
            confidence_interval = np.mean(forecast_upper - forecast_lower) / 2
            confidence_pct = (confidence_interval / np.mean(forecast_values) * 100) if np.mean(forecast_values) > 0 else 0
            
            st.metric(
                "Доверительный интервал", 
                f"±{confidence_interval:.1f}",
                f"±{confidence_pct:.1f}%"
            )
        
        # График KPI
        st.markdown("##### 📊 Визуализация KPI")
        
        # Создаем график сравнения прогноза с историческими данными
        fig_kpi = go.Figure()
        
        # Исторические данные (последние 30 дней)
        hist_dates = data['Дата'].iloc[-30:] if len(data) >= 30 else data['Дата']
        hist_values = data[metric_options[selected_metric]].iloc[-30:] if len(data) >= 30 else data[metric_options[selected_metric]]
        
        fig_kpi.add_trace(go.Scatter(
            x=hist_dates,
            y=hist_values,
            mode='lines',
            name='Исторические данные (30 дней)',
            line=dict(color='blue', width=2)
        ))
        
        # Прогноз
        forecast_dates = pd.date_range(
            start=data['Дата'].iloc[-1] + timedelta(days=1),
            periods=periods,
            freq='D'
        )
        
        fig_kpi.add_trace(go.Scatter(
            x=forecast_dates,
            y=forecast_values,
            mode='lines',
            name='Прогноз',
            line=dict(color='red', width=2)
        ))
        
        # Доверительный интервал
        fig_kpi.add_trace(go.Scatter(
            x=forecast_dates,
            y=forecast_upper,
            mode='lines',
            line=dict(width=0),
            showlegend=False
        ))
        
        fig_kpi.add_trace(go.Scatter(
            x=forecast_dates,
            y=forecast_lower,
            mode='lines',
            line=dict(width=0),
            fill='tonexty',
            fillcolor='rgba(255,0,0,0.2)',
            name='Доверительный интервал'
        ))
        
        fig_kpi.update_layout(
            title=f"KPI: Сравнение прогноза с историческими данными ({selected_metric})",
            xaxis_title='Дата',
            yaxis_title=selected_metric,
            hovermode='x unified'
        )
        
        st.plotly_chart(fig_kpi, use_container_width=True)
        
        # Таблица KPI
        st.markdown("##### 📋 Детальная таблица KPI")
        
        kpi_data = {
            'Показатель': [
                'Средний прогноз',
                'Максимальный прогноз', 
                'Минимальный прогноз',
                'Общий прогноз на период',
                'Коэффициент вариации',
                'Средняя неопределенность',
                'Тренд (наклон)',
                'Доверительный интервал'
            ],
            'Значение': [
                f"{avg_forecast:.1f}",
                f"{max_forecast:.0f}",
                f"{min_forecast:.0f}",
                f"{total_forecast:.0f}",
                f"{cv_forecast:.1f}%",
                f"{uncertainty:.1f}",
                f"{trend_slope:.2f}/день",
                f"±{confidence_interval:.1f}"
            ],
            'Изменение к историческому': [
                f"{growth_rate:+.1f}%",
                f"{max_growth:+.1f}%",
                f"{min_growth:+.1f}%",
                f"{total_growth:+.1f}%",
                f"Исторический: {cv_historical:.1f}%",
                f"{uncertainty_pct:.1f}% от прогноза",
                trend_direction,
                f"±{confidence_pct:.1f}%"
            ]
        }
        
        kpi_df = pd.DataFrame(kpi_data)
        st.dataframe(kpi_df, use_container_width=True)
        
        # Рекомендации на основе KPI
        st.markdown("##### 💡 Рекомендации на основе KPI")
        
        recommendations = []
        
        if growth_rate > 10:
            recommendations.append("🟢 **Положительный тренд**: Прогноз показывает значительный рост. Рекомендуется увеличить запасы и подготовиться к росту спроса.")
        elif growth_rate < -10:
            recommendations.append("🔴 **Отрицательный тренд**: Прогноз показывает снижение. Рекомендуется пересмотреть стратегию и найти способы стимулирования спроса.")
        else:
            recommendations.append("🟡 **Стабильный тренд**: Прогноз показывает умеренные изменения. Рекомендуется поддерживать текущую стратегию.")
        
        if cv_forecast > 50:
            recommendations.append("⚠️ **Высокая волатильность**: Прогноз нестабилен. Рекомендуется увеличить буферные запасы.")
        elif cv_forecast < 20:
            recommendations.append("✅ **Низкая волатильность**: Прогноз стабилен. Можно оптимизировать запасы.")
        
        if uncertainty_pct > 30:
            recommendations.append("❓ **Высокая неопределенность**: Доверительный интервал широкий. Рекомендуется дополнительный анализ факторов влияния.")
        elif uncertainty_pct < 15:
            recommendations.append("🎯 **Низкая неопределенность**: Прогноз надежен. Можно принимать уверенные решения.")
        
        if trend_slope > 0:
            recommendations.append("📈 **Восходящий тренд**: Прогноз растет. Рекомендуется подготовиться к увеличению объемов.")
        elif trend_slope < 0:
            recommendations.append("📉 **Нисходящий тренд**: Прогноз снижается. Рекомендуется найти способы стимулирования роста.")
        
        for rec in recommendations:
            st.markdown(rec)
        
        # Экспорт KPI
        st.markdown("##### 📥 Экспорт KPI")
        
        kpi_csv = kpi_df.to_csv(index=False)
        st.download_button(
            label="📥 Скачать KPI (CSV)",
            data=kpi_csv,
            file_name=f"kpi_forecast_{selected_metric.lower().replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )
        
    else:
        st.info("ℹ️ Для расчета KPI по прогнозу сначала создайте прогноз на вкладке '🔮 Прогнозирование'")
        
        # Показываем примеры KPI, которые будут рассчитаны
        st.markdown("##### 📊 KPI, которые будут рассчитаны после создания прогноза:")
        
        kpi_examples = [
            "**Средний прогноз** - среднее значение прогнозируемых показателей",
            "**Максимальный/минимальный прогноз** - экстремальные значения",
            "**Общий прогноз на период** - суммарное значение за весь период",
            "**Коэффициент вариации** - показатель стабильности прогноза",
            "**Средняя неопределенность** - ширина доверительного интервала",
            "**Тренд прогноза** - направление изменения (рост/спад/стабильно)",
            "**Доверительный интервал** - диапазон возможных значений",
            "**Рекомендации** - автоматические советы на основе анализа KPI"
        ]
        
        for example in kpi_examples:
            st.markdown(f"• {example}")

# Информация о данных
st.markdown("---")
st.markdown("### 📋 Информация о комплексном анализе")

col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    #### 📊 Что анализируется:
    - **Общие заказы** - сумма обычных и ВБ клуб заказов
    - **Общие выкупы (продажи)** - сумма обычных и ВБ клуб продаж
    - **Общая выручка** - сумма выручки от продаж
    - **Общая сумма заказов** - сумма всех заказов
    - **Агрегация по дням** - суммирование всех показателей за день
    - **Исторические данные** - из кеша приложения (data_cache.csv)
    - **Прогноз** - на выбранный период с учетом тренда и сезонности
    """)

with col2:
    st.markdown("""
    #### 🎯 Особенности Prophet:
    - **Автоматическое обнаружение трендов и сезонности**
    - **Гибкость** - позволяет настраивать чувствительность к изменениям
    - **Интервалы неопределенности** - показывает диапазон возможных значений
    - **Настраиваемые сезонности** - недельная и годовая
    - **Сравнительный анализ** - возможность сравнения всех метрик
    
    #### 💡 Рекомендации:
    - Используйте разные метрики для полного понимания бизнеса
    - Анализируйте конверсию заказов в продажи
    - Следите за трендами выручки и среднего чека
    """)

# Футер
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; padding: 1rem;'>
    🔮 <strong>Комплексный анализ заказов и продаж с Prophet</strong> | Данные из кеша приложения
</div>
""", unsafe_allow_html=True)
