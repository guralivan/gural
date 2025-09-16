import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import io

# Попытка импорта Prophet
try:
    from prophet import Prophet
    PROPHET_AVAILABLE = True
except ImportError:
    PROPHET_AVAILABLE = False

# Настройки страницы
st.set_page_config(
    page_title="🔮 Прогнозирование Prophet",
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
    .source-card {
        background-color: #e8f4fd;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
        border-left: 4px solid #1f77b4;
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
</style>
""", unsafe_allow_html=True)

# Заголовок
st.markdown('<h1 class="main-header">🔮 Прогнозирование Prophet</h1>', unsafe_allow_html=True)
st.markdown("**Прогнозирование временных рядов на основе данных из различных источников**")

# Проверка доступности Prophet
if not PROPHET_AVAILABLE:
    st.error("⚠️ Prophet не установлен. Установите: pip install prophet")
    st.stop()

# ================= ФУНКЦИИ ДЛЯ ЗАГРУЗКИ ДАННЫХ =================

def process_uploaded_file(uploaded_file):
    """Обрабатывает загруженный файл"""
    try:
        # Определяем тип файла
        if uploaded_file.name.lower().endswith(('.xlsx', '.xls')):
            # Читаем Excel файл
            df = pd.read_excel(uploaded_file)
        elif uploaded_file.name.lower().endswith('.csv'):
            # Читаем CSV файл
            df = pd.read_csv(uploaded_file)
        else:
            st.error("❌ Поддерживаются только файлы Excel (.xlsx, .xls) и CSV (.csv)")
            return None
        
        # Проверяем, что файл не пустой
        if df.empty:
            st.error("❌ Загруженный файл пустой")
            return None
        
        # Ищем столбцы с датами
        date_columns = []
        for col in df.columns:
            if 'дата' in col.lower() or 'date' in col.lower():
                date_columns.append(col)
        
        if not date_columns:
            # Если нет явных столбцов с датами, создаем искусственные даты
            df['Дата'] = pd.date_range(start='2024-01-01', periods=len(df), freq='D')
        else:
            # Используем первый найденный столбец с датой
            df['Дата'] = pd.to_datetime(df[date_columns[0]], errors='coerce', utc=False)
            # Проверяем, что столбец действительно стал datetime
            if pd.api.types.is_datetime64_any_dtype(df['Дата']):
                if df['Дата'].dt.tz is not None:
                    df['Дата'] = df['Дата'].dt.tz_localize(None)
            else:
                # Если не удалось преобразовать в datetime, создаем искусственные даты
                df['Дата'] = pd.date_range(start='2024-01-01', periods=len(df), freq='D')
        
        # Преобразуем числовые столбцы (автоматически определяем)
        for col in df.columns:
            if col != 'Дата' and df[col].dtype == 'object':
                # Пытаемся преобразовать в числовой формат
                df[col] = pd.to_numeric(df[col], errors='ignore')
        
        return df
    except Exception as e:
        st.error(f"Ошибка обработки файла: {e}")
        return None

@st.cache_data
def load_sales_report_data():
    """Загружает данные из файла полный_отчет_wb_20250912_152351.xlsx (отчет продаж)"""
    try:
        # Загружаем данные из листа "📋 Исходные данные"
        df = pd.read_excel('полный_отчет_wb_20250912_152351.xlsx', sheet_name='📋 Исходные данные')
        
        # Преобразуем дату и убираем timezone
        if 'Дата' in df.columns:
            df['Дата'] = pd.to_datetime(df['Дата'], utc=False)
            # Проверяем, что столбец действительно стал datetime
            if pd.api.types.is_datetime64_any_dtype(df['Дата']):
                if df['Дата'].dt.tz is not None:
                    df['Дата'] = df['Дата'].dt.tz_localize(None)
        
        # Преобразуем числовые столбцы
        numeric_cols = ['Заказали, шт', 'Выкупили, шт', 'Выкупили на сумму, ₽', 
                       'Переходы в карточку', 'Положили в корзину', 'Процент выкупа',
                       'Заказали на сумму, ₽']
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        return df
    except Exception as e:
        st.error(f"Ошибка загрузки данных полный_отчет_wb_20250912_152351.xlsx: {e}")
        return None

@st.cache_data
def load_weekly_reports_data():
    """Загружает данные из файла Еженедельные отчёты (12).xlsx"""
    try:
        df = pd.read_excel('Еженедельные отчёты (12).xlsx', sheet_name='Sheet1')
        
        # Используем столбец "Дата начала" как основную дату
        if 'Дата начала' in df.columns:
            df['Дата'] = pd.to_datetime(df['Дата начала'], utc=False)
            # Проверяем, что столбец действительно стал datetime
            if pd.api.types.is_datetime64_any_dtype(df['Дата']):
                if df['Дата'].dt.tz is not None:
                    df['Дата'] = df['Дата'].dt.tz_localize(None)
        else:
            # Если нет столбца с датой, создаем искусственные даты
            df['Дата'] = pd.date_range(start='2024-01-01', periods=len(df), freq='W')
        
        # Преобразуем числовые столбцы
        numeric_cols = ['Итого к оплате', 'Стоимость логистики', 'Стоимость хранения', 
                       'Общая сумма штрафов', 'Прочие удержания', 'К перечислению за товар']
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        return df
    except Exception as e:
        st.error(f"Ошибка загрузки данных Еженедельные отчёты (12).xlsx: {e}")
        return None

# ================= ФУНКЦИИ PROPHET =================

def prepare_data_for_prophet(df, metric_column, date_column='Дата'):
    """Подготавливает данные для Prophet"""
    try:
        if date_column not in df.columns:
            st.error(f"❌ Столбец '{date_column}' не найден в данных")
            return None
        
        if metric_column not in df.columns:
            st.error(f"❌ Столбец '{metric_column}' не найден в данных")
            return None
        
        # Создаем DataFrame для Prophet
        prophet_df = df[[date_column, metric_column]].copy()
        
        # Удаляем строки с пустыми значениями
        prophet_df = prophet_df.dropna()
        
        # Переименовываем столбцы для Prophet
        prophet_df.columns = ['ds', 'y']
        
        # Убираем информацию о часовом поясе из дат
        if pd.api.types.is_datetime64_any_dtype(prophet_df['ds']):
            if prophet_df['ds'].dt.tz is not None:
                prophet_df['ds'] = prophet_df['ds'].dt.tz_localize(None)
        
        # Преобразуем в datetime64[ns] без timezone
        prophet_df['ds'] = pd.to_datetime(prophet_df['ds'], utc=False)
        
        # Сортируем по дате
        prophet_df = prophet_df.sort_values('ds')
        
        return prophet_df
    except Exception as e:
        st.error(f"Ошибка подготовки данных: {e}")
        return None

def create_prophet_forecast(df_prophet, periods=30, seasonality_mode='additive'):
    """Создает прогноз с помощью Prophet"""
    try:
        if df_prophet is None or len(df_prophet) < 2:
            st.error("Недостаточно данных для прогнозирования")
            return None, None
        
        # Дополнительная проверка дат
        if pd.api.types.is_datetime64_any_dtype(df_prophet['ds']):
            if df_prophet['ds'].dt.tz is not None:
                df_prophet['ds'] = df_prophet['ds'].dt.tz_localize(None)
        
        # Убеждаемся, что даты в правильном формате
        df_prophet['ds'] = pd.to_datetime(df_prophet['ds'], utc=False)
        
        # Создаем модель Prophet
        model = Prophet(
            seasonality_mode=seasonality_mode,
            daily_seasonality=False,
            weekly_seasonality=True,
            yearly_seasonality=True
        )
        
        # Обучаем модель
        model.fit(df_prophet)
        
        # Создаем будущие даты
        future = model.make_future_dataframe(periods=periods)
        
        # Делаем прогноз
        forecast = model.predict(future)
        
        # Предотвращаем отрицательные значения
        forecast['yhat'] = forecast['yhat'].clip(lower=0)
        forecast['yhat_lower'] = forecast['yhat_lower'].clip(lower=0)
        forecast['yhat_upper'] = forecast['yhat_upper'].clip(lower=0)
        
        return model, forecast
    except Exception as e:
        st.error(f"Ошибка создания прогноза: {e}")
        return None, None

def plot_prophet_forecast(model, forecast, title="Прогноз Prophet"):
    """Создает график прогноза Prophet"""
    try:
        fig = go.Figure()
        
        # Добавляем исторические данные (черные точки)
        fig.add_trace(go.Scatter(
            x=forecast['ds'][:-len(forecast)//4],  # Исторические данные
            y=forecast['yhat'][:-len(forecast)//4],
            mode='markers',
            name='Исторические данные',
            marker=dict(color='black', size=4),
            hovertemplate='<b>Дата:</b> %{x}<br><b>Значение:</b> %{y:.2f}<extra></extra>'
        ))
        
        # Добавляем прогноз (синяя линия)
        fig.add_trace(go.Scatter(
            x=forecast['ds'],
            y=forecast['yhat'],
            mode='lines',
            name='Прогноз',
            line=dict(color='blue', width=2),
            hovertemplate='<b>Дата:</b> %{x}<br><b>Прогноз:</b> %{y:.2f}<extra></extra>'
        ))
        
        # Добавляем доверительный интервал
        fig.add_trace(go.Scatter(
            x=forecast['ds'],
            y=forecast['yhat_upper'],
            mode='lines',
            line=dict(width=0),
            showlegend=False,
            hoverinfo='skip'
        ))
        
        fig.add_trace(go.Scatter(
            x=forecast['ds'],
            y=forecast['yhat_lower'],
            mode='lines',
            line=dict(width=0),
            fill='tonexty',
            fillcolor='rgba(0,100,80,0.2)',
            name='Доверительный интервал',
            hovertemplate='<b>Дата:</b> %{x}<br><b>Верхняя граница:</b> %{y:.2f}<extra></extra>'
        ))
        
        fig.update_layout(
            title=title,
            xaxis_title='Дата',
            yaxis_title='Значение',
            hovermode='x unified',
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )
        
        return fig
    except Exception as e:
        st.error(f"Ошибка создания графика: {e}")
        return None

def plot_prophet_components(model, forecast, title="Компоненты прогноза Prophet"):
    """Создает график компонентов прогноза"""
    try:
        # Создаем график компонентов
        fig = model.plot_components(forecast)
        
        # Обновляем заголовок
        fig.suptitle(title, fontsize=16)
        
        return fig
    except Exception as e:
        st.error(f"Ошибка создания графика компонентов: {e}")
        return None

# ================= ОСНОВНОЙ ИНТЕРФЕЙС =================

# Боковая панель - выбор источника данных
st.sidebar.header("📊 Выбор источника данных")

data_source = st.sidebar.selectbox(
    "Выберите источник данных:",
    ["📊 Полный отчет продаж", "📋 Еженедельные отчеты (12)", "📁 Загрузить файл"],
    help="Выберите источник данных для прогнозирования"
)

# Загружаем данные в зависимости от выбора
if data_source == "📊 Полный отчет продаж":
    df = load_sales_report_data()
    data_type = "sales_report"
    st.sidebar.markdown('<div class="source-card">', unsafe_allow_html=True)
    st.sidebar.write("**📊 Источник:** Полный отчет продаж")
    st.sidebar.write("**📁 Файл:** полный_отчет_wb_20250912_152351.xlsx")
    st.sidebar.write("**📊 Содержит:** Детальные данные продаж")
    st.sidebar.markdown('</div>', unsafe_allow_html=True)
elif data_source == "📋 Еженедельные отчеты (12)":
    df = load_weekly_reports_data()
    data_type = "weekly_reports"
    st.sidebar.markdown('<div class="source-card">', unsafe_allow_html=True)
    st.sidebar.write("**📋 Источник:** Еженедельные отчеты")
    st.sidebar.write("**📁 Файл:** Еженедельные отчёты (12).xlsx")
    st.sidebar.write("**📊 Содержит:** Расходы, логистика, штрафы")
    st.sidebar.markdown('</div>', unsafe_allow_html=True)
elif data_source == "📁 Загрузить файл":
    st.sidebar.markdown('<div class="source-card">', unsafe_allow_html=True)
    st.sidebar.write("**📁 Источник:** Загруженный файл")
    st.sidebar.write("**📊 Поддерживает:** Excel, CSV")
    st.sidebar.write("**📅 Автоопределение:** Дат и числовых столбцов")
    st.sidebar.markdown('</div>', unsafe_allow_html=True)
    
    # Загрузка файла
    uploaded_file = st.sidebar.file_uploader(
        "Выберите файл для прогнозирования:",
        type=['xlsx', 'xls', 'csv'],
        help="Поддерживаются файлы Excel (.xlsx, .xls) и CSV (.csv)"
    )
    
    if uploaded_file is not None:
        df = process_uploaded_file(uploaded_file)
        data_type = "uploaded"
        st.sidebar.success(f"✅ Файл загружен: {uploaded_file.name}")
    else:
        df = None
        data_type = "uploaded"

if df is None:
    if data_type == "uploaded":
        st.info("👆 Загрузите файл для начала работы")
    else:
        st.error("❌ Не удалось загрузить данные. Проверьте наличие файлов:")
        st.error("• полный_отчет_wb_20250912_152351.xlsx")
        st.error("• Еженедельные отчёты (12).xlsx")
    st.stop()

# Информация о данных
if df is not None:
    st.sidebar.markdown("### 📋 Информация о данных")
    st.sidebar.write(f"**Записей:** {len(df):,}")
    st.sidebar.write(f"**Столбцов:** {len(df.columns)}")
    if 'Дата' in df.columns:
        st.sidebar.write(f"**Период:** {df['Дата'].min().strftime('%d.%m.%Y')} - {df['Дата'].max().strftime('%d.%m.%Y')}")

# Основной интерфейс с вкладками
if data_type == "sales_report":
    # Определяем метрики для полного отчета продаж
    metric_options = {
        'Выкупили, шт': 'Количество выкупов',
        'Выкупили на сумму, ₽': 'Выручка',
        'Заказали, шт': 'Количество заказов',
        'Заказали на сумму, ₽': 'Сумма заказов',
        'Переходы в карточку': 'Переходы в карточку',
        'Положили в корзину': 'Добавления в корзину',
        'Процент выкупа': 'Процент выкупа'
    }
    available_metrics = [col for col in metric_options.keys() if col in df.columns]
    title = "📊 Полный отчет продаж"
    
elif data_type == "weekly_reports":
    # Определяем метрики для еженедельных отчетов
    metric_options = {
        'Итого к оплате': 'Общая сумма к оплате',
        'Стоимость логистики': 'Стоимость логистики',
        'Стоимость хранения': 'Стоимость хранения',
        'Общая сумма штрафов': 'Общая сумма штрафов',
        'Прочие удержания': 'Прочие удержания',
        'К перечислению за товар': 'К перечислению за товар'
    }
    available_metrics = [col for col in metric_options.keys() if col in df.columns]
    title = "📋 Еженедельные отчеты"
    
elif data_type == "uploaded":
    # Для загруженных файлов определяем числовые столбцы
    numeric_columns = []
    for col in df.columns:
        if col != 'Дата' and pd.api.types.is_numeric_dtype(df[col]):
            numeric_columns.append(col)
    
    if not numeric_columns:
        st.error("❌ Не найдены числовые столбцы для прогнозирования")
        st.stop()
    
    metric_options = {col: col for col in numeric_columns}
    available_metrics = numeric_columns
    title = "📁 Загруженный файл"

if not available_metrics:
    st.error("❌ Не найдены подходящие столбцы для прогнозирования")
    st.stop()

# Создаем вкладки
tab1, tab2, tab3 = st.tabs(["🔮 Прогнозирование", "📊 Анализ данных", "📋 Информация"])

with tab1:
    st.markdown(f"### {title}")
    
    # Выбор метрики
    selected_metric = st.selectbox(
        "Выберите метрику для прогнозирования:",
        available_metrics,
        format_func=lambda x: metric_options[x] if data_type != "uploaded" else x
    )
    
    # Настройки прогнозирования
    col1, col2 = st.columns(2)
    
    with col1:
        periods = st.number_input(
            "Период прогнозирования (дни):",
            min_value=7,
            max_value=365,
            value=30,
            help="Количество дней для прогнозирования"
        )
    
    with col2:
        seasonality_mode = st.selectbox(
            "Режим сезонности:",
            ["additive", "multiplicative"],
            help="Additive: сезонность добавляется к тренду, Multiplicative: сезонность умножается на тренд"
        )
    
    # Кнопка создания прогноза
    if st.button("🔮 Создать прогноз", type="primary"):
        with st.spinner("Создаю прогноз..."):
            # Подготавливаем данные
            prophet_df = prepare_data_for_prophet(df, selected_metric)
            
            if prophet_df is not None and len(prophet_df) > 0:
                # Создаем прогноз
                model, forecast = create_prophet_forecast(prophet_df, periods, seasonality_mode)
                
                if model is not None and forecast is not None:
                    st.success("✅ Прогноз создан успешно!")
                    
                    # Отображаем график прогноза
                    forecast_fig = plot_prophet_forecast(model, forecast, f"Прогноз: {metric_options.get(selected_metric, selected_metric)}")
                    if forecast_fig:
                        st.plotly_chart(forecast_fig, use_container_width=True)
                    
                    # Отображаем компоненты
                    components_fig = plot_prophet_components(model, forecast, f"Компоненты прогноза: {metric_options.get(selected_metric, selected_metric)}")
                    if components_fig:
                        st.plotly_chart(components_fig, use_container_width=True)
                    
                    # Подробная статистика прогноза
                    st.markdown("### 📊 Подробная статистика прогноза")
                    
                    # Основные метрики
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        st.metric(
                            "Среднее значение",
                            f"{forecast['yhat'].mean():.2f}",
                            help="Среднее прогнозируемое значение"
                        )
                    
                    with col2:
                        st.metric(
                            "Максимальное значение",
                            f"{forecast['yhat'].max():.2f}",
                            help="Максимальное прогнозируемое значение"
                        )
                    
                    with col3:
                        st.metric(
                            "Минимальное значение",
                            f"{forecast['yhat'].min():.2f}",
                            help="Минимальное прогнозируемое значение"
                        )
                    
                    with col4:
                        st.metric(
                            "Стандартное отклонение",
                            f"{forecast['yhat'].std():.2f}",
                            help="Разброс прогнозируемых значений"
                        )
                    
                    # Дополнительные метрики
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        st.metric(
                            "Медиана",
                            f"{forecast['yhat'].median():.2f}",
                            help="Медианное значение прогноза"
                        )
                    
                    with col2:
                        st.metric(
                            "25-й процентиль",
                            f"{forecast['yhat'].quantile(0.25):.2f}",
                            help="Нижний квартиль"
                        )
                    
                    with col3:
                        st.metric(
                            "75-й процентиль",
                            f"{forecast['yhat'].quantile(0.75):.2f}",
                            help="Верхний квартиль"
                        )
                    
                    with col4:
                        st.metric(
                            "Коэффициент вариации",
                            f"{(forecast['yhat'].std() / forecast['yhat'].mean() * 100):.1f}%",
                            help="Относительная изменчивость"
                        )
                    
                    # Таблица прогноза
                    st.markdown("### 📋 Детальный прогноз")
                    
                    # Создаем таблицу с прогнозом
                    forecast_table = forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']].copy()
                    forecast_table.columns = ['Дата', 'Прогноз', 'Нижняя граница', 'Верхняя граница']
                    forecast_table['Дата'] = forecast_table['Дата'].dt.strftime('%d.%m.%Y')
                    
                    st.dataframe(forecast_table, use_container_width=True)
                    
                    # Кнопка скачивания
                    csv = forecast_table.to_csv(index=False)
                    st.download_button(
                        label="📥 Скачать прогноз (CSV)",
                        data=csv,
                        file_name=f"prophet_forecast_{selected_metric}_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv"
                    )
                else:
                    st.error("❌ Ошибка при создании прогноза")
            else:
                st.error("❌ Не удалось подготовить данные для прогнозирования")

with tab2:
    st.markdown("### 📊 Анализ данных")
    
    # Показываем предварительный просмотр данных
    st.markdown("#### 📋 Предварительный просмотр данных")
    st.dataframe(df.head(10), use_container_width=True)
    
    # Показываем информацию о столбцах
    st.markdown("#### 📊 Информация о столбцах")
    col_info = []
    for col in df.columns:
        col_info.append({
            'Столбец': col,
            'Тип': str(df[col].dtype),
            'Уникальных значений': df[col].nunique(),
            'Пустых значений': df[col].isnull().sum()
        })
    
    col_df = pd.DataFrame(col_info)
    st.dataframe(col_df, use_container_width=True)
    
    # Статистика по выбранной метрике
    if selected_metric in df.columns:
        st.markdown(f"#### 📈 Статистика по метрике: {metric_options.get(selected_metric, selected_metric)}")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Среднее", f"{df[selected_metric].mean():.2f}")
        with col2:
            st.metric("Медиана", f"{df[selected_metric].median():.2f}")
        with col3:
            st.metric("Максимум", f"{df[selected_metric].max():.2f}")
        with col4:
            st.metric("Минимум", f"{df[selected_metric].min():.2f}")

with tab3:
    st.markdown("### 📋 Информация о данных")
    
    # Общая информация
    st.markdown("#### 📊 Общая информация")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Всего записей", f"{len(df):,}")
    with col2:
        st.metric("Всего столбцов", len(df.columns))
    with col3:
        if 'Дата' in df.columns:
            st.metric("Период данных", f"{(df['Дата'].max() - df['Дата'].min()).days} дней")
    
    # Информация о файле
    if data_type == "uploaded":
        st.markdown("#### 📁 Информация о файле")
        st.info(f"**Имя файла:** {uploaded_file.name}")
        st.info(f"**Размер файла:** {uploaded_file.size:,} байт")
    
    # Доступные метрики
    st.markdown("#### 🎯 Доступные метрики для прогнозирования")
    for metric in available_metrics:
        st.write(f"• **{metric}** - {metric_options.get(metric, metric)}")

# Информация о Prophet
st.markdown("---")
st.markdown("### ℹ️ О методе Prophet")
st.markdown("""
**Prophet** — это инструмент прогнозирования временных рядов, разработанный Facebook. 
Он особенно хорошо подходит для бизнес-данных с сильными сезонными эффектами.

**Особенности:**
- 📈 Автоматическое обнаружение трендов
- 🔄 Учет сезонности (недельной, месячной, годовой)
- 🎯 Устойчивость к выбросам
- 📊 Доверительные интервалы
- ⚡ Быстрое обучение модели

**Источники данных:**
- **📊 Полный отчет продаж** - детальные данные продаж
- **📋 Еженедельные отчеты (12)** - расширенные еженедельные данные
- **📁 Загруженные файлы** - любые Excel/CSV файлы

**Применение:**
- Прогнозирование продаж
- Планирование расходов
- Анализ сезонности
- Бизнес-планирование

**✅ Исправления:**
- Устранена ошибка с часовыми поясами
- Улучшена обработка дат
- Исправлена ошибка ".dt accessor with datetimelike values"
- Добавлена проверка типов данных перед использованием .dt
- Упрощен интерфейс - только два источника данных
- Добавлены подробные KPI и обозначения к графикам
- Предотвращены отрицательные значения в прогнозе
""")

# Футер
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; padding: 1rem;'>
    🔮 <strong>Prophet Forecasting</strong> | Создано для анализа данных Wildberries
</div>
""", unsafe_allow_html=True)





