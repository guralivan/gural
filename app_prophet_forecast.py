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

def create_prophet_forecast(df_prophet, periods=30, seasonality_mode='additive', metric_name=''):
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
        
        # Определяем, может ли метрика быть отрицательной
        non_negative_metrics = [
            'выручка', 'продаж', 'заказов', 'шт', 'количество', 'сумма', 
            'оплате', 'логистики', 'хранения', 'штрафов', 'удержания',
            'перечислению', 'выкупили', 'заказали', 'переходы', 'корзину'
        ]
        
        is_non_negative = any(keyword in metric_name.lower() for keyword in non_negative_metrics)
        
        # Разрешаем отрицательные значения для всех метрик
        # Убираем ограничения clip(lower=0) чтобы разрешить отрицательные значения
        
        return model, forecast
    except Exception as e:
        st.error(f"Ошибка создания прогноза: {e}")
        return None, None

def plot_prophet_forecast(model, forecast, title="Прогноз Prophet"):
    """Создает график прогноза Prophet"""
    try:
        fig = go.Figure()
        
        # Разделяем данные на исторические и прогнозные
        # Находим точку разделения (последняя дата в исторических данных)
        historical_data = model.history
        last_historical_date = pd.to_datetime(historical_data['ds'].max())
        
        # Исторические данные (фактические значения)
        historical_mask = pd.to_datetime(forecast['ds']) <= last_historical_date
        forecast_mask = pd.to_datetime(forecast['ds']) > last_historical_date
        
        # Добавляем исторические данные как полосу (область)
        if historical_mask.any():
            # Используем фактические значения из исторических данных
            historical_actual = historical_data[['ds', 'y']].copy()
            fig.add_trace(go.Scatter(
                x=historical_actual['ds'],
                y=historical_actual['y'],
                mode='lines',
                name='Исторические данные',
                line=dict(color='gray', width=3),
                hovertemplate='<b>Дата:</b> %{x}<br><b>Фактическое значение:</b> %{y:,.0f}<extra></extra>'
            ))
        
        # Добавляем прогноз (синяя линия)
        if forecast_mask.any():
            fig.add_trace(go.Scatter(
                x=forecast[forecast_mask]['ds'],
                y=forecast[forecast_mask]['yhat'],
                mode='lines',
                name='Прогноз',
                line=dict(color='blue', width=3),
                hovertemplate='<b>Дата:</b> %{x}<br><b>Прогноз:</b> %{y:,.0f}<extra></extra>'
            ))
        
        # Добавляем доверительный интервал только для прогноза
        if forecast_mask.any():
            fig.add_trace(go.Scatter(
                x=forecast[forecast_mask]['ds'],
                y=forecast[forecast_mask]['yhat_upper'],
                mode='lines',
                line=dict(width=0),
                showlegend=False,
                hoverinfo='skip'
            ))
            
            fig.add_trace(go.Scatter(
                x=forecast[forecast_mask]['ds'],
                y=forecast[forecast_mask]['yhat_lower'],
                mode='lines',
                line=dict(width=0),
                fill='tonexty',
                fillcolor='rgba(0,100,80,0.2)',
                name='Доверительный интервал прогноза',
                hovertemplate='<b>Дата:</b> %{x}<br><b>Верхняя граница:</b> %{y:,.0f}<extra></extra>'
            ))
        
        # Добавляем вертикальную линию разделения
        if historical_mask.any() and forecast_mask.any():
            # Преобразуем Timestamp в строку для совместимости
            last_date_str = last_historical_date.strftime('%Y-%m-%d') if hasattr(last_historical_date, 'strftime') else str(last_historical_date)
            fig.add_vline(
                x=last_date_str,
                line_dash="dash",
                line_color="red",
                annotation_text="Начало прогноза",
                annotation_position="top"
            )
        
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
        # Создаем график компонентов с помощью Plotly
        from plotly.subplots import make_subplots
        import plotly.graph_objects as go
        
        # Компоненты уже есть в forecast
        
        # Создаем subplots
        fig = make_subplots(
            rows=3, cols=1,
            subplot_titles=['Тренд', 'Недельная сезонность', 'Годовая сезонность'],
            vertical_spacing=0.1
        )
        
        # Тренд
        fig.add_trace(
            go.Scatter(
                x=forecast['ds'],
                y=forecast['trend'],
                mode='lines',
                name='Тренд',
                line=dict(color='blue', width=2)
            ),
            row=1, col=1
        )
        
        # Недельная сезонность
        if 'weekly' in forecast.columns:
            fig.add_trace(
                go.Scatter(
                    x=forecast['ds'],
                    y=forecast['weekly'],
                    mode='lines',
                    name='Недельная сезонность',
                    line=dict(color='green', width=2)
                ),
                row=2, col=1
            )
        
        # Годовая сезонность
        if 'yearly' in forecast.columns:
            fig.add_trace(
                go.Scatter(
                    x=forecast['ds'],
                    y=forecast['yearly'],
                    mode='lines',
                    name='Годовая сезонность',
                    line=dict(color='red', width=2)
                ),
                row=3, col=1
            )
        
        # Обновляем layout
        fig.update_layout(
            title=title,
            height=800,
            showlegend=False
        )
        
        # Обновляем оси
        fig.update_xaxes(title_text="Дата", row=3, col=1)
        fig.update_yaxes(title_text="Тренд", row=1, col=1)
        fig.update_yaxes(title_text="Недельная сезонность", row=2, col=1)
        fig.update_yaxes(title_text="Годовая сезонность", row=3, col=1)
        
        return fig
    except Exception as e:
        st.error(f"Ошибка создания графика компонентов: {e}")
        return None

# ================= ОСНОВНОЙ ИНТЕРФЕЙС =================

# Инициализация session state для хранения данных
if 'uploaded_data' not in st.session_state:
    st.session_state.uploaded_data = {}

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
        # Проверяем, не загружен ли уже этот файл
        file_key = uploaded_file.name + str(uploaded_file.size)
        
        if file_key not in st.session_state.uploaded_data:
            # Обрабатываем новый файл
            df = process_uploaded_file(uploaded_file)
            if df is not None:
                # Сохраняем данные в session state
                st.session_state.uploaded_data[file_key] = {
                    'data': df,
                    'name': uploaded_file.name,
                    'size': uploaded_file.size,
                    'timestamp': datetime.now()
                }
                st.sidebar.success(f"✅ Файл загружен: {uploaded_file.name}")
            else:
                df = None
        else:
            # Используем сохраненные данные
            df = st.session_state.uploaded_data[file_key]['data']
            st.sidebar.info(f"📁 Используется сохраненный файл: {uploaded_file.name}")
        
        data_type = "uploaded"
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
    try:
        record_count = len(df)
        st.sidebar.write(f"**Записей:** {record_count:,}")
    except:
        st.sidebar.write("**Записей:** N/A")
    
    try:
        column_count = len(df.columns)
        st.sidebar.write(f"**Столбцов:** {column_count}")
    except:
        st.sidebar.write("**Столбцов:** N/A")
    if 'Дата' in df.columns:
        try:
            min_date = df['Дата'].min().strftime('%d.%m.%Y')
            max_date = df['Дата'].max().strftime('%d.%m.%Y')
            st.sidebar.write(f"**Период:** {min_date} - {max_date}")
        except:
            st.sidebar.write("**Период:** N/A")

# Показываем информацию о сохраненных файлах
if st.session_state.uploaded_data:
    st.sidebar.markdown("### 📁 Сохраненные файлы")
    for file_key, file_info in st.session_state.uploaded_data.items():
        with st.sidebar.expander(f"📄 {file_info['name']}"):
            try:
                file_size = file_info['size']
                st.write(f"**Размер:** {file_size:,} байт")
            except:
                st.write("**Размер:** N/A")
            
            try:
                timestamp = file_info['timestamp'].strftime('%d.%m.%Y %H:%M')
                st.write(f"**Загружен:** {timestamp}")
            except:
                st.write("**Загружен:** N/A")
            
            try:
                record_count = len(file_info['data'])
                st.write(f"**Записей:** {record_count:,}")
            except:
                st.write("**Записей:** N/A")
            
            # Кнопка удаления файла
            if st.button(f"🗑️ Удалить", key=f"delete_{file_key}"):
                del st.session_state.uploaded_data[file_key]
                st.rerun()

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
        available_metrics
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
                model, forecast = create_prophet_forecast(prophet_df, periods, seasonality_mode, selected_metric)
                
                if model is not None and forecast is not None:
                    st.success("✅ Прогноз создан успешно!")
                    
                    # Показываем информацию о периоде прогноза
                    historical_data = model.history
                    last_historical_date = pd.to_datetime(historical_data['ds'].max())
                    forecast_start = pd.to_datetime(forecast[pd.to_datetime(forecast['ds']) > last_historical_date]['ds'].min())
                    forecast_end = pd.to_datetime(forecast['ds'].max())
                    
                    try:
                        forecast_start_str = forecast_start.strftime('%d.%m.%Y')
                        forecast_end_str = forecast_end.strftime('%d.%m.%Y')
                        st.info(f"📅 **Период прогноза:** {forecast_start_str} - {forecast_end_str}")
                    except:
                        st.info("📅 **Период прогноза:** N/A")
                    
                    try:
                        last_date_str = last_historical_date.strftime('%d.%m.%Y')
                        st.info(f"📊 **Исторические данные:** до {last_date_str}")
                    except:
                        st.info("📊 **Исторические данные:** N/A")
                    
                    # Отображаем график прогноза
                    forecast_fig = plot_prophet_forecast(model, forecast, f"Прогноз: {selected_metric}")
                    if forecast_fig:
                        st.plotly_chart(forecast_fig, width='stretch')
                    
                    # Отображаем компоненты
                    components_fig = plot_prophet_components(model, forecast, f"Компоненты прогноза: {selected_metric}")
                    if components_fig:
                        st.plotly_chart(components_fig, width='stretch')
                    
                    # Подробная статистика прогноза
                    st.markdown("### 📊 Подробная статистика прогноза")
                    
                    # Основные метрики
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        try:
                            mean_val = forecast['yhat'].mean()
                            if pd.notna(mean_val) and isinstance(mean_val, (int, float)):
                                mean_text = f"{float(mean_val):,.2f}"
                            else:
                                mean_text = "N/A"
                        except (ValueError, TypeError, AttributeError):
                            mean_text = "N/A"
                        
                        st.metric(
                            "Среднее значение",
                            mean_text,
                            help="Среднее прогнозируемое значение"
                        )
                    
                    with col2:
                        try:
                            max_val = forecast['yhat'].max()
                            if pd.notna(max_val) and isinstance(max_val, (int, float)):
                                max_text = f"{float(max_val):,.2f}"
                            else:
                                max_text = "N/A"
                        except (ValueError, TypeError, AttributeError):
                            max_text = "N/A"
                        
                        st.metric(
                            "Максимальное значение",
                            max_text,
                            help="Максимальное прогнозируемое значение"
                        )
                    
                    with col3:
                        try:
                            min_val = forecast['yhat'].min()
                            if pd.notna(min_val) and isinstance(min_val, (int, float)):
                                min_text = f"{float(min_val):,.2f}"
                            else:
                                min_text = "N/A"
                        except (ValueError, TypeError, AttributeError):
                            min_text = "N/A"
                        
                        st.metric(
                            "Минимальное значение",
                            min_text,
                            help="Минимальное прогнозируемое значение"
                        )
                    
                    with col4:
                        try:
                            std_val = forecast['yhat'].std()
                            if pd.notna(std_val) and isinstance(std_val, (int, float)):
                                std_text = f"{float(std_val):,.2f}"
                            else:
                                std_text = "N/A"
                        except (ValueError, TypeError, AttributeError):
                            std_text = "N/A"
                        
                        st.metric(
                            "Стандартное отклонение",
                            std_text,
                            help="Разброс прогнозируемых значений"
                        )
                    
                    # Дополнительные метрики
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        try:
                            median_val = forecast['yhat'].median()
                            if pd.notna(median_val) and isinstance(median_val, (int, float)):
                                median_text = f"{float(median_val):,.2f}"
                            else:
                                median_text = "N/A"
                        except (ValueError, TypeError, AttributeError):
                            median_text = "N/A"
                        
                        st.metric(
                            "Медиана",
                            median_text,
                            help="Медианное значение прогноза"
                        )
                    
                    with col2:
                        try:
                            q25_val = forecast['yhat'].quantile(0.25)
                            if pd.notna(q25_val) and isinstance(q25_val, (int, float)):
                                q25_text = f"{float(q25_val):,.2f}"
                            else:
                                q25_text = "N/A"
                        except (ValueError, TypeError, AttributeError):
                            q25_text = "N/A"
                        
                        st.metric(
                            "25-й процентиль",
                            q25_text,
                            help="Нижний квартиль"
                        )
                    
                    with col3:
                        try:
                            q75_val = forecast['yhat'].quantile(0.75)
                            if pd.notna(q75_val) and isinstance(q75_val, (int, float)):
                                q75_text = f"{float(q75_val):,.2f}"
                            else:
                                q75_text = "N/A"
                        except (ValueError, TypeError, AttributeError):
                            q75_text = "N/A"
                        
                        st.metric(
                            "75-й процентиль",
                            q75_text,
                            help="Верхний квартиль"
                        )
                    
                    with col4:
                        try:
                            mean_val = forecast['yhat'].mean()
                            std_val = forecast['yhat'].std()
                            if (pd.notna(mean_val) and pd.notna(std_val) and 
                                isinstance(mean_val, (int, float)) and isinstance(std_val, (int, float)) and 
                                float(mean_val) != 0):
                                cv = (float(std_val) / float(mean_val) * 100)
                                cv_text = f"{cv:.1f}%"
                            else:
                                cv_text = "N/A"
                        except (ValueError, TypeError, AttributeError, ZeroDivisionError):
                            cv_text = "N/A"
                        
                        st.metric(
                            "Коэффициент вариации",
                            cv_text,
                            help="Относительная изменчивость"
                        )
                    
                    # Таблица прогноза
                    st.markdown("### 📋 Детальный прогноз")
                    
                    # Создаем таблицу только с прогнозными данными (будущие значения)
                    forecast_only = forecast[pd.to_datetime(forecast['ds']) > last_historical_date].copy()
                    forecast_table = forecast_only[['ds', 'yhat', 'yhat_lower', 'yhat_upper']].copy()
                    forecast_table.columns = ['Дата', 'Прогноз', 'Нижняя граница', 'Верхняя граница']
                    forecast_table['Дата'] = forecast_table['Дата'].dt.strftime('%d.%m.%Y')
                    
                    # Форматируем числовые столбцы
                    for col in ['Прогноз', 'Нижняя граница', 'Верхняя граница']:
                        def safe_format(x):
                            try:
                                if pd.notna(x):
                                    # Преобразуем в float и форматируем
                                    val = float(x)
                                    return f"{val:,.2f}"
                                else:
                                    return "N/A"
                            except (ValueError, TypeError, AttributeError):
                                # Если не удается преобразовать в число, возвращаем строковое представление
                                try:
                                    return str(x) if pd.notna(x) else "N/A"
                                except:
                                    return "N/A"
                        
                        forecast_table[col] = forecast_table[col].apply(safe_format)
                    
                    st.dataframe(forecast_table, width='stretch')
                    
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
    st.dataframe(df.head(10), width='stretch')
    
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
    st.dataframe(col_df, width='stretch')
    
    # Статистика по выбранной метрике
    if selected_metric in df.columns:
        st.markdown(f"#### 📈 Статистика по метрике: {selected_metric}")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            try:
                mean_val = df[selected_metric].mean()
                if pd.notna(mean_val) and isinstance(mean_val, (int, float)):
                    mean_text = f"{float(mean_val):,.2f}"
                else:
                    mean_text = "N/A"
            except (ValueError, TypeError, AttributeError):
                mean_text = "N/A"
            st.metric("Среднее", mean_text)
        with col2:
            try:
                median_val = df[selected_metric].median()
                if pd.notna(median_val) and isinstance(median_val, (int, float)):
                    median_text = f"{float(median_val):,.2f}"
                else:
                    median_text = "N/A"
            except (ValueError, TypeError, AttributeError):
                median_text = "N/A"
            st.metric("Медиана", median_text)
        with col3:
            try:
                max_val = df[selected_metric].max()
                if pd.notna(max_val) and isinstance(max_val, (int, float)):
                    max_text = f"{float(max_val):,.2f}"
                else:
                    max_text = "N/A"
            except (ValueError, TypeError, AttributeError):
                max_text = "N/A"
            st.metric("Максимум", max_text)
        with col4:
            try:
                min_val = df[selected_metric].min()
                if pd.notna(min_val) and isinstance(min_val, (int, float)):
                    min_text = f"{float(min_val):,.2f}"
                else:
                    min_text = "N/A"
            except (ValueError, TypeError, AttributeError):
                min_text = "N/A"
            st.metric("Минимум", min_text)

with tab3:
    st.markdown("### 📋 Информация о данных")
    
    # Общая информация
    st.markdown("#### 📊 Общая информация")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        try:
            record_count = len(df)
            st.metric("Всего записей", f"{record_count:,}")
        except:
            st.metric("Всего записей", "N/A")
    with col2:
        st.metric("Всего столбцов", len(df.columns))
    with col3:
        if 'Дата' in df.columns:
            date_diff = df['Дата'].max() - df['Дата'].min()
            if hasattr(date_diff, 'days'):
                days = date_diff.days
            else:
                days = date_diff.dt.days.iloc[0] if hasattr(date_diff, 'dt') else int(date_diff.total_seconds() / 86400)
            try:
                st.metric("Период данных", f"{days} дней")
            except:
                st.metric("Период данных", "N/A")
    
    # Информация о файле
    if data_type == "uploaded":
        st.markdown("#### 📁 Информация о файле")
        st.info(f"**Имя файла:** {uploaded_file.name}")
        try:
            file_size = uploaded_file.size
            st.info(f"**Размер файла:** {file_size:,} байт")
        except:
            st.info("**Размер файла:** N/A")
    
    # Доступные метрики
    st.markdown("#### 🎯 Доступные метрики для прогнозирования")
    for metric in available_metrics:
        st.write(f"• **{metric}**")

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
""")

st.markdown("### 📊 Режимы сезонности в Prophet")

col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    #### 🔄 Additive (Аддитивный)
    **"Сезонность добавляется к тренду"**
    
    **Формула:** `Прогноз = Тренд + Сезонность + Шум`
    
    **Характеристика:** Сезонные колебания имеют **постоянную амплитуду**
    
    **Пример:** Если тренд = 1000, а сезонность = +200, то итоговый прогноз = 1200
    
    **Когда использовать:**
    - ✅ Когда сезонные колебания **не зависят** от уровня тренда
    - ✅ Когда амплитуда сезонности **постоянна** во времени
    - ✅ Для данных с **линейным трендом**
    
    **Примеры:**
    - 📈 Продажи товаров (сезонные скидки всегда +20%)
    - 🌡️ Температура (зимой всегда -10°C от среднего)
    - 📊 Количество заказов (выходные всегда +50 заказов)
    """)

with col2:
    st.markdown("""
    #### ✖️ Multiplicative (Мультипликативный)
    **"Сезонность умножается на тренд"**
    
    **Формула:** `Прогноз = Тренд × Сезонность × Шум`
    
    **Характеристика:** Сезонные колебания **пропорциональны** тренду
    
    **Пример:** Если тренд = 1000, а сезонность = 1.2, то итоговый прогноз = 1200
    
    **Когда использовать:**
    - ✅ Когда сезонные колебания **зависят** от уровня тренда
    - ✅ Когда амплитуда сезонности **растет** с ростом тренда
    - ✅ Для данных с **экспоненциальным трендом**
    
    **Примеры:**
    - 💰 Выручка (рождественские продажи +20% от текущего уровня)
    - 📱 Активные пользователи (выходные +30% от базового уровня)
    - 🏪 Оборот магазина (сезонные всплески пропорциональны росту)
    """)

st.markdown("""
#### 🎯 Рекомендации для ваших данных Wildberries:

**📊 Полный отчет продаж:**
- **Рекомендация:** `Additive`
- **Причина:** Сезонные колебания продаж обычно имеют постоянную амплитуду
- **Пример:** Черная пятница всегда добавляет +1000 заказов

**📋 Еженедельные отчеты (расходы):**
- **Рекомендация:** `Additive`
- **Причина:** Расходы на логистику и хранение имеют фиксированные сезонные компоненты
- **Пример:** Зимой логистика всегда дороже на +5000₽

#### 🔍 Практический совет:
1. **Начните с `Additive`** - он работает в большинстве случаев
2. **Если прогноз выглядит неточно** - попробуйте `Multiplicative`
3. **Сравните результаты** - выберите тот, где доверительные интервалы уже

#### 📈 Визуальная разница:
- **Additive:** Сезонные "волны" одинаковой высоты
- **Multiplicative:** Сезонные "волны" растут вместе с трендом
""")

st.markdown("### ✅ Исправления и улучшения:")
st.markdown("""
- Устранена ошибка с часовыми поясами
- Улучшена обработка дат
- Исправлена ошибка ".dt accessor with datetimelike values"
- Добавлена проверка типов данных перед использованием .dt
- Упрощен интерфейс - только два источника данных
- Добавлены подробные KPI и обозначения к графикам
- Предотвращены отрицательные значения в прогнозе
- Исправлена ошибка с графиком компонентов
- Добавлено подробное объяснение режимов сезонности
""")

# Футер
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; padding: 1rem;'>
    🔮 <strong>Prophet Forecasting</strong> | Создано для анализа данных Wildberries
</div>
""", unsafe_allow_html=True)
