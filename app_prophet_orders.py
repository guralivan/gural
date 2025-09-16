import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
from prophet import Prophet
import warnings
warnings.filterwarnings('ignore')

# Настройки страницы
st.set_page_config(
    page_title="🔮 Prophet: Прогнозирование заказов",
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
    .prophet-card {
        background-color: #e3f2fd;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
        border-left: 4px solid #2196f3;
    }
</style>
""", unsafe_allow_html=True)

# Заголовок
st.markdown('<h1 class="main-header">🔮 Prophet: Прогнозирование заказов</h1>', unsafe_allow_html=True)
st.markdown("**Мощное прогнозирование заказов с использованием Facebook Prophet**")

# ================= ФУНКЦИИ ДЛЯ ЗАГРУЗКИ ДАННЫХ =================

@st.cache_data
def load_45_data():
    """Загружает данные из файла 45.xlsx"""
    try:
        df = pd.read_excel('45.xlsx', sheet_name='Товары', header=1)
        
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
        st.error(f"Ошибка загрузки данных из 45.xlsx: {e}")
        return None

def aggregate_orders_by_date(df):
    """Агрегирует заказы по дате"""
    if df is None or df.empty:
        return None
    
    # Группируем по дате и суммируем заказы
    aggregated = df.groupby('Дата')['Общие заказы'].sum().reset_index()
    aggregated = aggregated.sort_values('Дата')
    
    return aggregated

def prepare_prophet_data(df):
    """Подготавливает данные для Prophet"""
    if df is None or df.empty:
        return None
    
    # Prophet требует столбцы 'ds' (дата) и 'y' (значение)
    prophet_df = df[['Дата', 'Общие заказы']].copy()
    prophet_df.columns = ['ds', 'y']
    
    # Убираем нулевые и отрицательные значения
    prophet_df = prophet_df[prophet_df['y'] > 0]
    
    return prophet_df

# ================= ФУНКЦИИ ПРОГНОЗИРОВАНИЯ PROPHET =================

@st.cache_data
def create_prophet_forecast(df, periods=30, seasonality_mode='additive', 
                          yearly_seasonality=True, weekly_seasonality=True, 
                          daily_seasonality=False, changepoint_prior_scale=0.05):
    """Создает прогноз с помощью Prophet"""
    try:
        # Создаем модель Prophet
        model = Prophet(
            seasonality_mode=seasonality_mode,
            yearly_seasonality=yearly_seasonality,
            weekly_seasonality=weekly_seasonality,
            daily_seasonality=daily_seasonality,
            changepoint_prior_scale=changepoint_prior_scale
        )
        
        # Обучаем модель
        model.fit(df)
        
        # Создаем будущие даты
        future = model.make_future_dataframe(periods=periods)
        
        # Делаем прогноз
        forecast = model.predict(future)
        
        return model, forecast
        
    except Exception as e:
        st.error(f"Ошибка создания прогноза Prophet: {e}")
        return None, None

# ================= ФУНКЦИИ ВИЗУАЛИЗАЦИИ =================

def plot_prophet_forecast(model, forecast, title="Prophet Прогноз заказов"):
    """Создает график прогноза Prophet"""
    fig = go.Figure()
    
    # Исторические данные
    fig.add_trace(go.Scatter(
        x=forecast['ds'][:-len(forecast)//4],  # Исторические данные (первые 3/4)
        y=forecast['yhat'][:-len(forecast)//4],
        mode='lines',
        name='Исторические заказы',
        line=dict(color='blue', width=3)
    ))
    
    # Прогноз
    forecast_period = forecast.tail(len(forecast)//4)  # Последняя четверть - прогноз
    fig.add_trace(go.Scatter(
        x=forecast_period['ds'],
        y=forecast_period['yhat'],
        mode='lines',
        name='Прогноз заказов',
        line=dict(color='red', width=3, dash='dash')
    ))
    
    # Доверительный интервал
    fig.add_trace(go.Scatter(
        x=forecast_period['ds'],
        y=forecast_period['yhat_upper'],
        mode='lines',
        line=dict(width=0),
        showlegend=False,
        hoverinfo='skip'
    ))
    
    fig.add_trace(go.Scatter(
        x=forecast_period['ds'],
        y=forecast_period['yhat_lower'],
        mode='lines',
        line=dict(width=0),
        fill='tonexty',
        fillcolor='rgba(255,0,0,0.2)',
        name='Доверительный интервал',
        hoverinfo='skip'
    ))
    
    fig.update_layout(
        title=title,
        xaxis_title='Дата',
        yaxis_title='Количество заказов',
        hovermode='x unified',
        height=500
    )
    
    return fig

def plot_prophet_components(model, forecast):
    """Создает графики компонентов Prophet"""
    # Тренд
    fig_trend = go.Figure()
    fig_trend.add_trace(go.Scatter(
        x=forecast['ds'],
        y=forecast['trend'],
        mode='lines',
        name='Тренд',
        line=dict(color='blue', width=2)
    ))
    fig_trend.update_layout(
        title='Тренд заказов',
        xaxis_title='Дата',
        yaxis_title='Тренд',
        height=300
    )
    
    # Сезонность (если есть)
    components_figs = [fig_trend]
    
    if 'weekly' in forecast.columns:
        fig_weekly = go.Figure()
        fig_weekly.add_trace(go.Scatter(
            x=forecast['ds'],
            y=forecast['weekly'],
            mode='lines',
            name='Недельная сезонность',
            line=dict(color='green', width=2)
        ))
        fig_weekly.update_layout(
            title='Недельная сезонность',
            xaxis_title='Дата',
            yaxis_title='Сезонность',
            height=300
        )
        components_figs.append(fig_weekly)
    
    if 'yearly' in forecast.columns:
        fig_yearly = go.Figure()
        fig_yearly.add_trace(go.Scatter(
            x=forecast['ds'],
            y=forecast['yearly'],
            mode='lines',
            name='Годовая сезонность',
            line=dict(color='orange', width=2)
        ))
        fig_yearly.update_layout(
            title='Годовая сезонность',
            xaxis_title='Дата',
            yaxis_title='Сезонность',
            height=300
        )
        components_figs.append(fig_yearly)
    
    return components_figs

# ================= ОСНОВНОЙ ИНТЕРФЕЙС =================

# Загружаем данные
df = load_45_data()

if df is None:
    st.error("❌ Не удалось загрузить данные из файла 45.xlsx")
    st.info("Убедитесь, что файл 45.xlsx находится в той же папке, что и приложение")
    st.stop()

# Агрегируем данные по заказам
orders_data = aggregate_orders_by_date(df)

if orders_data is None or orders_data.empty:
    st.error("❌ Не удалось агрегировать данные по заказам")
    st.stop()

# Подготавливаем данные для Prophet
prophet_data = prepare_prophet_data(orders_data)

if prophet_data is None or prophet_data.empty:
    st.error("❌ Не удалось подготовить данные для Prophet")
    st.stop()

# Боковая панель
st.sidebar.header("🔮 Настройки Prophet")

# Показываем информацию о данных
st.sidebar.markdown("### 📋 Информация о данных")
st.sidebar.metric("Всего записей", f"{len(df):,}")
st.sidebar.metric("Дней данных", f"{len(orders_data):,}")
st.sidebar.metric("Дней для Prophet", f"{len(prophet_data):,}")

date_range = orders_data['Дата'].max() - orders_data['Дата'].min()
st.sidebar.metric("Период данных", f"{date_range.days} дней")

total_orders = orders_data['Общие заказы'].sum()
st.sidebar.metric("Общее количество заказов", f"{total_orders:,.0f}")

# Настройки Prophet
st.sidebar.markdown("### ⚙️ Настройки Prophet")

periods = st.sidebar.slider(
    "Период прогнозирования (дни):",
    min_value=7,
    max_value=90,
    value=30
)

seasonality_mode = st.sidebar.selectbox(
    "Режим сезонности:",
    ["additive", "multiplicative"],
    help="Additive: сезонность добавляется к тренду. Multiplicative: сезонность умножается на тренд"
)

yearly_seasonality = st.sidebar.checkbox("Годовая сезонность", value=True)
weekly_seasonality = st.sidebar.checkbox("Недельная сезонность", value=True)
daily_seasonality = st.sidebar.checkbox("Дневная сезонность", value=False)

changepoint_prior_scale = st.sidebar.slider(
    "Гибкость тренда:",
    min_value=0.001,
    max_value=0.5,
    value=0.05,
    step=0.001,
    help="Больше значение = более гибкий тренд"
)

# Основной контент
st.markdown("### 📈 Анализ заказов")

# Показываем данные
col1, col2 = st.columns([2, 1])

with col1:
    st.markdown("#### 📊 График заказов по дням")
    fig_data = px.line(orders_data, x='Дата', y='Общие заказы', 
                      title="Исторические данные: Общие заказы")
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

# Создание прогноза Prophet
if st.button("🔮 Создать Prophet прогноз", type="primary"):
    with st.spinner("Prophet создает прогноз заказов..."):
        # Создаем прогноз
        model, forecast = create_prophet_forecast(
            prophet_data, 
            periods=periods,
            seasonality_mode=seasonality_mode,
            yearly_seasonality=yearly_seasonality,
            weekly_seasonality=weekly_seasonality,
            daily_seasonality=daily_seasonality,
            changepoint_prior_scale=changepoint_prior_scale
        )
        
        if model is not None and forecast is not None:
            st.success("✅ Prophet прогноз заказов создан успешно!")
            
            # Основной график прогноза
            st.markdown("#### 🔮 Prophet Прогноз заказов")
            fig_forecast = plot_prophet_forecast(model, forecast)
            st.plotly_chart(fig_forecast, use_container_width=True)
            
            # Компоненты Prophet
            st.markdown("#### 📊 Компоненты Prophet")
            components_figs = plot_prophet_components(model, forecast)
            
            for i, fig in enumerate(components_figs):
                st.plotly_chart(fig, use_container_width=True)
            
            # Статистика прогноза
            st.markdown("#### 📊 Статистика Prophet прогноза")
            
            # Получаем только прогнозную часть
            forecast_period = forecast.tail(periods)
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Средний прогноз", f"{forecast_period['yhat'].mean():.1f}")
            with col2:
                st.metric("Максимальный прогноз", f"{forecast_period['yhat'].max():.0f}")
            with col3:
                st.metric("Минимальный прогноз", f"{forecast_period['yhat'].min():.0f}")
            with col4:
                last_historical = prophet_data['y'].iloc[-1]
                last_forecast = forecast_period['yhat'].iloc[-1]
                if last_historical != 0:
                    change = ((last_forecast - last_historical) / last_historical * 100)
                    st.metric("Изменение", f"{change:.1f}%")
                else:
                    st.metric("Изменение", "N/A")
            
            # Таблица прогноза
            st.markdown("#### 📋 Детальный Prophet прогноз")
            
            forecast_table = forecast_period[['ds', 'yhat', 'yhat_lower', 'yhat_upper']].copy()
            forecast_table.columns = ['Дата', 'Прогноз', 'Нижняя граница', 'Верхняя граница']
            forecast_table['Дата'] = forecast_table['Дата'].dt.strftime('%d.%m.%Y')
            forecast_table = forecast_table.round(1)
            
            st.dataframe(forecast_table, use_container_width=True)
            
            # Кнопка скачивания
            csv = forecast_table.to_csv(index=False)
            st.download_button(
                label="📥 Скачать Prophet прогноз (CSV)",
                data=csv,
                file_name=f"prophet_forecast_orders_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
            
            # Информация о модели
            st.markdown("#### 🔧 Информация о модели Prophet")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("""
                **Параметры модели:**
                - Режим сезонности: `{seasonality_mode}`
                - Годовая сезонность: `{yearly_seasonality}`
                - Недельная сезонность: `{weekly_seasonality}`
                - Дневная сезонность: `{daily_seasonality}`
                - Гибкость тренда: `{changepoint_prior_scale}`
                """.format(
                    seasonality_mode=seasonality_mode,
                    yearly_seasonality=yearly_seasonality,
                    weekly_seasonality=weekly_seasonality,
                    daily_seasonality=daily_seasonality,
                    changepoint_prior_scale=changepoint_prior_scale
                ))
            
            with col2:
                st.markdown("""
                **Качество модели:**
                - Период прогноза: `{periods}` дней
                - Исторических данных: `{historical_days}` дней
                - Доверительный интервал: 80%
                """.format(
                    periods=periods,
                    historical_days=len(prophet_data)
                ))
        else:
            st.error("❌ Не удалось создать Prophet прогноз. Проверьте данные.")

# Информация о Prophet
st.markdown("---")
st.markdown("### 📋 Информация о Prophet")

col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    #### 🔮 Что такое Prophet:
    - **Автоматическое обнаружение трендов** - Prophet находит изменения в тренде
    - **Сезонность** - учитывает недельные, месячные и годовые паттерны
    - **Праздники** - может учитывать влияние праздников
    - **Доверительные интервалы** - показывает неопределенность прогноза
    - **Устойчивость к выбросам** - не ломается от аномальных значений
    """)

with col2:
    st.markdown("""
    #### ⚙️ Настройки Prophet:
    - **Режим сезонности** - additive или multiplicative
    - **Гибкость тренда** - насколько быстро может меняться тренд
    - **Сезонности** - какие паттерны учитывать
    - **Период прогноза** - на сколько дней вперед прогнозировать
    
    #### 💡 Рекомендации:
    - Используйте **additive** для стабильных данных
    - Используйте **multiplicative** для данных с растущей волатильностью
    """)

# Футер
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; padding: 1rem;'>
    🔮 <strong>Prophet Прогнозирование заказов</strong> | Facebook Prophet + Streamlit
</div>
""", unsafe_allow_html=True)
