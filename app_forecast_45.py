import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import io

# Настройки страницы
st.set_page_config(
    page_title="🔮 Прогнозирование данных 45.xlsx",
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
    .error-card {
        background-color: #f8d7da;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
        border-left: 4px solid #dc3545;
    }
    .info-card {
        background-color: #e8f4fd;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
        border-left: 4px solid #1f77b4;
    }
</style>
""", unsafe_allow_html=True)

# Заголовок
st.markdown('<h1 class="main-header">🔮 Прогнозирование данных 45.xlsx</h1>', unsafe_allow_html=True)
st.markdown("**Прогнозирование заказов, продаж и выручки на основе данных Wildberries**")

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
            'Переходы в карточку', 'Положили в корзину', 'Добавили в отложенные',
            'Заказали, шт', 'Заказали ВБ клуб, шт', 'Выкупили, шт', 'Выкупили ВБ клуб, шт',
            'Отменили, шт', 'Отменили ВБ клуб, шт', 'Конверсия в корзину, %',
            'Конверсия в заказ, %', 'Процент выкупа', 'Процент выкупа ВБ клуб',
            'Заказали на сумму, ₽', 'Заказали на сумму ВБ клуб, ₽',
            'Выкупили на сумму, ₽', 'Выкупили на сумму ВБ клуб, ₽',
            'Отменили на сумму, ₽', 'Отменили на сумму ВБ клуб, ₽'
        ]
        
        for col in numeric_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Добавляем дополнительные расчеты
        df['Общие заказы'] = df['Заказали, шт'].fillna(0) + df['Заказали ВБ клуб, шт'].fillna(0)
        df['Общие выкупы'] = df['Выкупили, шт'].fillna(0) + df['Выкупили ВБ клуб, шт'].fillna(0)
        df['Общая выручка'] = df['Выкупили на сумму, ₽'].fillna(0) + df['Выкупили на сумму ВБ клуб, ₽'].fillna(0)
        df['Общие переходы'] = df['Переходы в карточку'].fillna(0)
        df['Общие в корзину'] = df['Положили в корзину'].fillna(0)
        
        return df
    except Exception as e:
        st.error(f"Ошибка загрузки данных из 45.xlsx: {e}")
        return None

def aggregate_data_by_date(df, metric_column, aggregation='sum'):
    """Агрегирует данные по дате"""
    if df is None or df.empty:
        return None
    
    # Группируем по дате и агрегируем
    if aggregation == 'sum':
        aggregated = df.groupby('Дата')[metric_column].sum().reset_index()
    elif aggregation == 'mean':
        aggregated = df.groupby('Дата')[metric_column].mean().reset_index()
    elif aggregation == 'count':
        aggregated = df.groupby('Дата')[metric_column].count().reset_index()
    else:
        aggregated = df.groupby('Дата')[metric_column].sum().reset_index()
    
    # Сортируем по дате
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

def exponential_smoothing_forecast(data, alpha=0.3, periods=30):
    """Экспоненциальное сглаживание"""
    if len(data) < 2:
        return None, None
    
    # Экспоненциальное сглаживание
    smoothed = [data[0]]
    for i in range(1, len(data)):
        if not np.isnan(data[i]):
            smoothed.append(alpha * data[i] + (1 - alpha) * smoothed[-1])
        else:
            smoothed.append(smoothed[-1])
    
    # Прогнозируем
    last_value = smoothed[-1]
    trend = smoothed[-1] - smoothed[-2] if len(smoothed) > 1 else 0
    
    forecast = []
    for i in range(periods):
        next_value = last_value + trend * (i + 1)
        forecast.append(next_value)
    
    return np.array(smoothed), np.array(forecast)

def seasonal_forecast(data, season_length=7, periods=30):
    """Простое сезонное прогнозирование"""
    if len(data) < season_length * 2:
        return None, None
    
    # Вычисляем сезонные индексы
    seasonal_indices = []
    for i in range(season_length):
        values = []
        for j in range(i, len(data), season_length):
            if not np.isnan(data[j]):
                values.append(data[j])
        
        if values:
            seasonal_indices.append(np.mean(values))
        else:
            seasonal_indices.append(0)
    
    # Нормализуем индексы
    avg_value = np.mean([v for v in data if not np.isnan(v)])
    if avg_value != 0:
        seasonal_indices = [idx / avg_value for idx in seasonal_indices]
    
    # Тренд
    x = np.arange(len(data))
    y = np.array(data)
    mask = ~np.isnan(y)
    if np.sum(mask) > 1:
        coeffs = np.polyfit(x[mask], y[mask], 1)
        trend = coeffs[0]
    else:
        trend = 0
    
    # Прогнозируем
    forecast = []
    for i in range(periods):
        future_period = len(data) + i
        seasonal_idx = future_period % season_length
        seasonal_factor = seasonal_indices[seasonal_idx]
        trend_value = np.polyval(coeffs, future_period) if np.sum(mask) > 1 else data[-1]
        forecast_value = trend_value * seasonal_factor
        forecast.append(forecast_value)
    
    return None, np.array(forecast)

# ================= ФУНКЦИИ ВИЗУАЛИЗАЦИИ =================

def plot_forecast(historical_data, forecast_data, dates, title="Прогноз"):
    """Создает график прогноза"""
    fig = go.Figure()
    
    # Исторические данные
    fig.add_trace(go.Scatter(
        x=dates[:len(historical_data)],
        y=historical_data,
        mode='lines',
        name='Исторические данные',
        line=dict(color='blue', width=2)
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
            name='Прогноз',
            line=dict(color='red', width=2, dash='dash')
        ))
        
        # Добавляем вертикальную линию разделения
        # Преобразуем Timestamp в строку для совместимости с Plotly
        last_date_str = last_date.strftime('%Y-%m-%d') if hasattr(last_date, 'strftime') else str(last_date)
        fig.add_vline(
            x=last_date_str,
            line_dash="dash",
            line_color="gray",
            annotation_text="Начало прогноза"
        )
    
    fig.update_layout(
        title=title,
        xaxis_title='Дата',
        yaxis_title='Значение',
        hovermode='x unified'
    )
    
    return fig

# ================= ОСНОВНОЙ ИНТЕРФЕЙС =================

# Загружаем данные
df = load_45_data()

if df is None:
    st.error("❌ Не удалось загрузить данные из файла 45.xlsx")
    st.info("Убедитесь, что файл 45.xlsx находится в той же папке, что и приложение")
    st.stop()

# Боковая панель
st.sidebar.header("📊 Настройки прогнозирования")

# Выбор метрики
metric_options = {
    'Общие заказы': 'Общее количество заказов',
    'Общие выкупы': 'Общее количество выкупов',
    'Общая выручка': 'Общая выручка (₽)',
    'Общие переходы': 'Общее количество переходов в карточку',
    'Общие в корзину': 'Общее количество добавлений в корзину',
    'Заказали, шт': 'Заказы (обычные)',
    'Выкупили, шт': 'Выкупы (обычные)',
    'Выкупили на сумму, ₽': 'Выручка (обычная)',
    'Переходы в карточку': 'Переходы в карточку',
    'Положили в корзину': 'Добавления в корзину',
    'Процент выкупа': 'Процент выкупа (%)'
}

# Фильтруем доступные метрики
available_metrics = [col for col in metric_options.keys() if col in df.columns]

if not available_metrics:
    st.error("❌ Не найдены подходящие столбцы для прогнозирования")
    st.stop()

selected_metric = st.sidebar.selectbox(
    "Метрика для прогнозирования:",
    available_metrics,
    format_func=lambda x: metric_options[x]
)

# Выбор агрегации
aggregation = st.sidebar.selectbox(
    "Агрегация данных:",
    ["sum", "mean", "count"],
    format_func=lambda x: {
        "sum": "Сумма по дням",
        "mean": "Среднее по дням", 
        "count": "Количество записей по дням"
    }[x]
)

# Настройки прогнозирования
st.sidebar.markdown("### ⚙️ Настройки прогноза")

periods = st.sidebar.slider(
    "Период прогнозирования (дни):",
    min_value=7,
    max_value=90,
    value=30
)

method = st.sidebar.selectbox(
    "Метод прогнозирования:",
    ["📈 Линейный тренд", "📊 Скользящее среднее", "🔄 Экспоненциальное сглаживание", "📅 Сезонный"]
)

# Дополнительные параметры
if method == "📊 Скользящее среднее":
    window = st.sidebar.slider("Окно скользящего среднего:", 3, 14, 7)
elif method == "🔄 Экспоненциальное сглаживание":
    alpha = st.sidebar.slider("Коэффициент сглаживания:", 0.1, 0.9, 0.3)
elif method == "📅 Сезонный":
    season_length = st.sidebar.slider("Длина сезона (дни):", 3, 30, 7)

# Основной контент
st.markdown(f"### 📊 Прогнозирование: {metric_options[selected_metric]}")

# Агрегируем данные
aggregated_data = aggregate_data_by_date(df, selected_metric, aggregation)

if aggregated_data is None or aggregated_data.empty:
    st.error("❌ Не удалось агрегировать данные")
    st.stop()

# Показываем информацию о данных
col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Всего записей", f"{len(df):,}")
with col2:
    st.metric("Дней данных", f"{len(aggregated_data):,}")
with col3:
    date_range = aggregated_data['Дата'].max() - aggregated_data['Дата'].min()
    st.metric("Период данных", f"{date_range.days} дней")

# Показываем данные
col1, col2 = st.columns([2, 1])

with col1:
    st.markdown("#### 📈 График данных")
    fig_data = px.line(aggregated_data, x='Дата', y=selected_metric, 
                      title=f"Исторические данные: {metric_options[selected_metric]}")
    st.plotly_chart(fig_data, use_container_width=True)

with col2:
    st.markdown("#### 📊 Статистика")
    metric_data = aggregated_data[selected_metric].dropna()
    
    col2_1, col2_2 = st.columns(2)
    with col2_1:
        st.metric("Среднее", f"{metric_data.mean():.2f}")
        st.metric("Медиана", f"{metric_data.median():.2f}")
    with col2_2:
        st.metric("Максимум", f"{metric_data.max():.2f}")
        st.metric("Минимум", f"{metric_data.min():.2f}")

# Создание прогноза
if st.button("🔮 Создать прогноз", type="primary"):
    with st.spinner("Создаю прогноз..."):
        # Получаем данные
        data = aggregated_data[selected_metric].values
        
        # Выбираем метод прогнозирования
        if method == "📈 Линейный тренд":
            trend, forecast = simple_linear_forecast(data, periods)
        elif method == "📊 Скользящее среднее":
            trend, forecast = moving_average_forecast(data, window, periods)
        elif method == "🔄 Экспоненциальное сглаживание":
            trend, forecast = exponential_smoothing_forecast(data, alpha, periods)
        elif method == "📅 Сезонный":
            trend, forecast = seasonal_forecast(data, season_length, periods)
        
        if forecast is not None:
            st.success("✅ Прогноз создан успешно!")
            
            # График прогноза
            fig_forecast = plot_forecast(
                data, 
                forecast, 
                aggregated_data['Дата'].values, 
                f"Прогноз: {metric_options[selected_metric]} ({method})"
            )
            st.plotly_chart(fig_forecast, use_container_width=True)
            
            # Статистика прогноза
            st.markdown("#### 📊 Статистика прогноза")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Средний прогноз", f"{np.mean(forecast):.2f}")
            with col2:
                st.metric("Максимальный прогноз", f"{np.max(forecast):.2f}")
            with col3:
                st.metric("Минимальный прогноз", f"{np.min(forecast):.2f}")
            with col4:
                if data[-1] != 0:
                    change = ((forecast[-1] - data[-1]) / data[-1] * 100)
                    st.metric("Изменение", f"{change:.1f}%")
                else:
                    st.metric("Изменение", "N/A")
            
            # Таблица прогноза
            st.markdown("#### 📋 Детальный прогноз")
            
            # Убеждаемся, что последняя дата это datetime объект
            last_date = aggregated_data['Дата'].iloc[-1]
            if not isinstance(last_date, (pd.Timestamp, datetime)):
                last_date = pd.to_datetime(last_date)
            
            forecast_dates = pd.date_range(
                start=last_date + timedelta(days=1),
                periods=len(forecast),
                freq='D'
            )
            
            forecast_df = pd.DataFrame({
                'Дата': forecast_dates.strftime('%d.%m.%Y'),
                'Прогноз': forecast.round(2)
            })
            
            st.dataframe(forecast_df, use_container_width=True)
            
            # Кнопка скачивания
            csv = forecast_df.to_csv(index=False)
            st.download_button(
                label="📥 Скачать прогноз (CSV)",
                data=csv,
                file_name=f"forecast_45_{selected_metric}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
        else:
            st.error("❌ Не удалось создать прогноз. Проверьте данные.")

# Информация о данных
st.markdown("---")
st.markdown("### 📋 Информация о данных")

col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    #### 📊 Доступные метрики:
    - **Общие заказы** - сумма обычных и ВБ клуб заказов
    - **Общие выкупы** - сумма обычных и ВБ клуб выкупов  
    - **Общая выручка** - сумма обычной и ВБ клуб выручки
    - **Общие переходы** - переходы в карточку товара
    - **Общие в корзину** - добавления в корзину
    - **Процент выкупа** - эффективность продаж
    """)

with col2:
    st.markdown("""
    #### 🎯 Методы прогнозирования:
    - **📈 Линейный тренд** - для данных с четким трендом
    - **📊 Скользящее среднее** - для сглаживания шума
    - **🔄 Экспоненциальное сглаживание** - для адаптивных прогнозов
    - **📅 Сезонный** - для данных с повторяющимися паттернами
    """)

# Футер
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; padding: 1rem;'>
    🔮 <strong>Прогнозирование данных 45.xlsx</strong> | Анализ продаж Wildberries
</div>
""", unsafe_allow_html=True)
