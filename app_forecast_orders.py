import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta

# Настройки страницы
st.set_page_config(
    page_title="🔮 Прогнозирование заказов",
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
</style>
""", unsafe_allow_html=True)

# Заголовок
st.markdown('<h1 class="main-header">🔮 Прогнозирование заказов</h1>', unsafe_allow_html=True)
st.markdown("**Прогнозирование заказов на основе данных из файла 45.xlsx**")

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

# ================= ФУНКЦИИ ПРОГНОЗИРОВАНИЯ =================

def simple_linear_forecast(data, periods=30):
    """Простое линейное прогнозирование"""
    if len(data) < 2:
        return None, None
    
    # Создаем временной ряд
    x = np.arange(len(data))
    y = np.array(data)
    
    # Удаляем NaN значения
    mask = ~np.isnan(y)
    x_clean = x[mask]
    y_clean = y[mask]
    
    if len(x_clean) < 2:
        return None, None
    
    # Линейная регрессия
    coeffs = np.polyfit(x_clean, y_clean, 1)
    trend_line = np.polyval(coeffs, x_clean)
    
    # Прогнозируем будущие значения
    future_x = np.arange(len(data), len(data) + periods)
    future_y = np.polyval(coeffs, future_x)
    
    return trend_line, future_y

def moving_average_forecast(data, window=7, periods=30):
    """Прогнозирование на основе скользящего среднего"""
    if len(data) < window:
        return None, None
    
    # Вычисляем скользящее среднее
    ma = pd.Series(data).rolling(window=window, min_periods=1).mean()
    
    # Тренд на основе последних значений
    recent_trend = ma.iloc[-window:].diff().mean()
    
    # Прогнозируем
    last_value = ma.iloc[-1]
    forecast = []
    for i in range(periods):
        next_value = last_value + recent_trend * (i + 1)
        forecast.append(next_value)
    
    return ma.values, np.array(forecast)

# ================= ФУНКЦИИ ВИЗУАЛИЗАЦИИ =================

def plot_orders_forecast(historical_data, forecast_data, dates, title="Прогноз заказов"):
    """Создает график прогноза заказов"""
    fig = go.Figure()
    
    # Исторические данные
    fig.add_trace(go.Scatter(
        x=dates[:len(historical_data)],
        y=historical_data,
        mode='lines',
        name='Исторические заказы',
        line=dict(color='blue', width=3)
    ))
    
    # Прогноз
    if forecast_data is not None:
        # Убеждаемся, что dates[-1] это datetime объект
        last_date = dates[-1]
        if not isinstance(last_date, (pd.Timestamp, datetime)):
            last_date = pd.to_datetime(last_date)
        
        forecast_dates = pd.date_range(
            start=last_date + timedelta(days=1),
            periods=len(forecast_data),
            freq='D'
        )
        
        fig.add_trace(go.Scatter(
            x=forecast_dates,
            y=forecast_data,
            mode='lines',
            name='Прогноз заказов',
            line=dict(color='red', width=3, dash='dash')
        ))
        
        # Добавляем аннотацию для разделения исторических данных и прогноза
        fig.add_annotation(
            x=last_date,
            y=max(max(historical_data), max(forecast_data)) * 0.9,
            text="Начало прогноза",
            showarrow=True,
            arrowhead=2,
            arrowcolor="gray",
            font=dict(color="gray", size=12)
        )
    
    fig.update_layout(
        title=title,
        xaxis_title='Дата',
        yaxis_title='Количество заказов',
        hovermode='x unified',
        height=500
    )
    
    return fig

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

# Боковая панель
st.sidebar.header("📊 Настройки прогнозирования заказов")

# Показываем информацию о данных
st.sidebar.markdown("### 📋 Информация о данных")
st.sidebar.metric("Всего записей", f"{len(df):,}")
st.sidebar.metric("Дней данных", f"{len(orders_data):,}")

date_range = orders_data['Дата'].max() - orders_data['Дата'].min()
st.sidebar.metric("Период данных", f"{date_range.days} дней")

total_orders = orders_data['Общие заказы'].sum()
st.sidebar.metric("Общее количество заказов", f"{total_orders:,.0f}")

# Настройки прогнозирования
st.sidebar.markdown("### ⚙️ Настройки прогноза")

periods = st.sidebar.slider(
    "Период прогнозирования (дни):",
    min_value=7,
    max_value=60,
    value=30
)

method = st.sidebar.selectbox(
    "Метод прогнозирования:",
    ["📈 Линейный тренд", "📊 Скользящее среднее"]
)

# Дополнительные параметры
if method == "📊 Скользящее среднее":
    window = st.sidebar.slider("Окно скользящего среднего:", 3, 14, 7)

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

# Создание прогноза
if st.button("🔮 Создать прогноз заказов", type="primary"):
    with st.spinner("Создаю прогноз заказов..."):
        # Получаем данные
        data = orders_data['Общие заказы'].values
        
        # Выбираем метод прогнозирования
        if method == "📈 Линейный тренд":
            trend, forecast = simple_linear_forecast(data, periods)
        elif method == "📊 Скользящее среднее":
            trend, forecast = moving_average_forecast(data, window, periods)
        
        if forecast is not None:
            st.success("✅ Прогноз заказов создан успешно!")
            
            # График прогноза
            fig_forecast = plot_orders_forecast(
                data, 
                forecast, 
                orders_data['Дата'].values, 
                f"Прогноз заказов ({method})"
            )
            st.plotly_chart(fig_forecast, use_container_width=True)
            
            # Статистика прогноза
            st.markdown("#### 📊 Статистика прогноза заказов")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Средний прогноз", f"{np.mean(forecast):.1f}")
            with col2:
                st.metric("Максимальный прогноз", f"{np.max(forecast):.0f}")
            with col3:
                st.metric("Минимальный прогноз", f"{np.min(forecast):.0f}")
            with col4:
                if data[-1] != 0:
                    change = ((forecast[-1] - data[-1]) / data[-1] * 100)
                    st.metric("Изменение", f"{change:.1f}%")
                else:
                    st.metric("Изменение", "N/A")
            
            # Таблица прогноза
            st.markdown("#### 📋 Детальный прогноз заказов")
            
            # Убеждаемся, что последняя дата это datetime объект
            last_date = orders_data['Дата'].iloc[-1]
            if not isinstance(last_date, (pd.Timestamp, datetime)):
                last_date = pd.to_datetime(last_date)
            
            forecast_dates = pd.date_range(
                start=last_date + timedelta(days=1),
                periods=len(forecast),
                freq='D'
            )
            
            forecast_df = pd.DataFrame({
                'Дата': forecast_dates.strftime('%d.%m.%Y'),
                'Прогноз заказов': forecast.round(1)
            })
            
            st.dataframe(forecast_df, use_container_width=True)
            
            # Кнопка скачивания
            csv = forecast_df.to_csv(index=False)
            st.download_button(
                label="📥 Скачать прогноз заказов (CSV)",
                data=csv,
                file_name=f"forecast_orders_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
        else:
            st.error("❌ Не удалось создать прогноз заказов. Проверьте данные.")

# Информация о данных
st.markdown("---")
st.markdown("### 📋 Информация о прогнозировании заказов")

col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    #### 📊 Что анализируется:
    - **Общие заказы** - сумма обычных и ВБ клуб заказов
    - **Агрегация по дням** - суммирование всех заказов за день
    - **Исторические данные** - для построения тренда
    - **Прогноз** - на выбранный период
    """)

with col2:
    st.markdown("""
    #### 🎯 Методы прогнозирования:
    - **📈 Линейный тренд** - для данных с четким трендом
    - **📊 Скользящее среднее** - для сглаживания шума и выбросов
    
    #### 💡 Рекомендации:
    - Используйте **линейный тренд** для стабильных данных
    - Используйте **скользящее среднее** для данных с шумом
    """)

# Футер
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; padding: 1rem;'>
    🔮 <strong>Прогнозирование заказов</strong> | Анализ продаж Wildberries
</div>
""", unsafe_allow_html=True)
