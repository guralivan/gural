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
    page_title="🔮 Прогнозирование заказов с Prophet (из кеша)",
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
</style>
""", unsafe_allow_html=True)

# Заголовок
st.markdown('<h1 class="main-header">🔮 Прогнозирование заказов с Prophet</h1>', unsafe_allow_html=True)
st.markdown("**Прогнозирование заказов на основе данных из кеша приложения с использованием модели Prophet**")

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

def aggregate_orders_by_date(df):
    """Агрегирует заказы по дате"""
    if df is None or df.empty:
        return None
    
    # Группируем по дате и суммируем заказы
    aggregated = df.groupby('Дата')['Общие заказы'].sum().reset_index()
    aggregated = aggregated.sort_values('Дата')
    
    return aggregated

# ================= ФУНКЦИИ ПРОГНОЗИРОВАНИЯ PROPHET =================

def prophet_forecast(df_prophet, periods=30, seasonality_mode='additive', changepoint_prior_scale=0.05):
    """Прогнозирование с использованием Prophet"""
    model = Prophet(
        seasonality_mode=seasonality_mode,
        changepoint_prior_scale=changepoint_prior_scale
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

# Агрегируем данные по заказам
orders_data = aggregate_orders_by_date(df)

if orders_data is None or orders_data.empty:
    st.error("❌ Не удалось агрегировать данные по заказам")
    st.stop()

# Подготавливаем данные для Prophet
df_prophet = orders_data[['Дата', 'Общие заказы']].rename(columns={'Дата': 'ds', 'Общие заказы': 'y'})

# Боковая панель
st.sidebar.header("📊 Настройки прогнозирования с Prophet")

# Показываем информацию о данных
st.sidebar.markdown("### 📋 Информация о данных")
st.sidebar.metric("Всего записей", f"{len(df):,}")
st.sidebar.metric("Дней данных", f"{len(orders_data):,}")

date_range = orders_data['Дата'].max() - orders_data['Дата'].min()
st.sidebar.metric("Период данных", f"{date_range.days} дней")

total_orders = orders_data['Общие заказы'].sum()
st.sidebar.metric("Общее количество заказов", f"{total_orders:,.0f}")

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
st.markdown("### 📈 Анализ заказов и прогнозирование с Prophet")

# Показываем данные
col1, col2 = st.columns([2, 1])

with col1:
    st.markdown("#### 📊 График заказов по дням")
    fig_data = go.Figure()
    fig_data.add_trace(go.Scatter(
        x=orders_data['Дата'], 
        y=orders_data['Общие заказы'], 
        mode='lines', 
        name='Исторические заказы',
        line=dict(color='blue', width=2)
    ))
    fig_data.update_layout(
        title="Исторические данные: Общие заказы", 
        xaxis_title='Дата', 
        yaxis_title='Количество заказов',
        hovermode='x unified'
    )
    st.plotly_chart(fig_data, use_container_width=True)

with col2:
    st.markdown("#### 📊 Статистика заказов")
    orders_metric = orders_data['Общие заказы']
    
    col2_1, col2_2 = st.columns(2)
    with col2_1:
        st.metric("Среднее в день", f"{orders_metric.mean():.1f}")
        st.metric("Медиана", f"{orders_metric.median():.1f}")
    with col2_2:
        st.metric("Максимум", f"{orders_metric.max():.0f}")
        st.metric("Минимум", f"{orders_metric.min():.0f}")

# Создание прогноза
if st.button("🔮 Создать прогноз заказов с Prophet", type="primary"):
    with st.spinner("Создаю прогноз заказов с Prophet..."):
        # Создаем модель с дополнительными настройками
        model = Prophet(
            seasonality_mode=seasonality_mode,
            changepoint_prior_scale=changepoint_prior_scale,
            weekly_seasonality=weekly_seasonality,
            yearly_seasonality=yearly_seasonality
        )
        
        model.fit(df_prophet)
        future = model.make_future_dataframe(periods=periods)
        forecast = model.predict(future)
        
        st.success("✅ Прогноз заказов с Prophet создан успешно!")
        
        # График прогноза
        st.markdown("#### 📈 График прогноза заказов")
        fig_prophet = plot_plotly(model, forecast)
        fig_prophet.update_layout(
            title=f"Прогноз заказов с Prophet на {periods} дней", 
            yaxis_title='Количество заказов'
        )
        st.plotly_chart(fig_prophet, use_container_width=True)
        
        # Компоненты прогноза
        st.markdown("#### 📉 Компоненты прогноза Prophet")
        fig_components = model.plot_components(forecast)
        st.write(fig_components)  # Streamlit может отображать Matplotlib фигуры
        
        # Статистика прогноза
        st.markdown("#### 📊 Статистика прогноза заказов")
        
        forecast_values = forecast['yhat'][-periods:].values
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Средний прогноз", f"{np.mean(forecast_values):.1f}")
        with col2:
            st.metric("Максимальный прогноз", f"{np.max(forecast_values):.0f}")
        with col3:
            st.metric("Минимальный прогноз", f"{np.min(forecast_values):.0f}")
        with col4:
            last_historical_value = orders_data['Общие заказы'].iloc[-1]
            if last_historical_value != 0:
                change = ((forecast_values[-1] - last_historical_value) / last_historical_value * 100)
                st.metric("Изменение", f"{change:.1f}%")
            else:
                st.metric("Изменение", "N/A")
        
        # Таблица прогноза
        st.markdown("#### 📋 Детальный прогноз заказов")
        
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
            label="📥 Скачать прогноз заказов (CSV)",
            data=csv,
            file_name=f"prophet_forecast_orders_cache_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )

# Информация о данных
st.markdown("---")
st.markdown("### 📋 Информация о прогнозировании заказов с Prophet")

col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    #### 📊 Что анализируется:
    - **Общие заказы** - сумма обычных и ВБ клуб заказов
    - **Агрегация по дням** - суммирование всех заказов за день
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
    
    #### 💡 Рекомендации:
    - Экспериментируйте с параметрами для лучшей подгонки модели
    - Используйте данные из кеша для более точных прогнозов
    """)

# Футер
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; padding: 1rem;'>
    🔮 <strong>Прогнозирование заказов с Prophet</strong> | Данные из кеша приложения
</div>
""", unsafe_allow_html=True)
