import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Настройка страницы
st.set_page_config(
    page_title="Анализ сезонности товаров",
    page_icon="📊",
    layout="wide"
)

# Заголовок
st.title("📊 Анализ сезонности товаров")

@st.cache_data
def load_data():
    """Загрузка данных из CSV файла"""
    # Пробуем разные варианты чтения файла
    encodings = ['utf-8', 'cp1251', 'latin1', 'utf-8-sig']
    separators = [',', ';', '\t']
    
    for encoding in encodings:
        for sep in separators:
            try:
                df = pd.read_csv('sezon.csv', encoding=encoding, sep=sep)
                # Проверяем, что файл загрузился корректно
                if len(df.columns) > 10 and len(df) > 10:
                    return df
            except Exception as e:
                continue
    
    # Если ничего не сработало, используем значения по умолчанию
    return pd.read_csv('sezon.csv', encoding='utf-8')

def clean_data(df):
    """Очистка и подготовка данных"""
    # Находим строку с заголовками (строка, содержащая 'наименование товара')
    header_row = None
    for i, row in df.iterrows():
        if 'наименование товара' in str(row.values):
            header_row = i
            break

    if header_row is not None:
        # Используем эту строку как заголовки
        df.columns = df.iloc[header_row]
        # Удаляем все строки до заголовков включительно
        df = df.iloc[header_row + 1:].reset_index(drop=True)

    # Удаляем пустые строки
    if 'наименование товара' in df.columns:
        df = df.dropna(subset=['наименование товара'])
        # Удаляем строки с заголовками (если они повторяются)
        df = df[df['наименование товара'] != 'наименование товара']

    # Очищаем числовые столбцы
    month_columns = ['январь', 'февраль', 'март', 'апрель', 'май', 'июнь',
                     'июль', 'август', 'сентябрь', 'октябрь', 'ноябрь', 'декабрь']

    for col in month_columns:
        if col in df.columns:
            # Более детальная очистка числовых данных
            # Сначала заменяем все возможные варианты пустых значений
            df[col] = df[col].astype(str)
            # Удаляем все виды пробелов (включая неразрывные \xa0)
            df[col] = df[col].str.replace(' ', '', regex=False)  # обычный пробел
            df[col] = df[col].str.replace('\xa0', '', regex=False)  # неразрывный пробел
            df[col] = df[col].str.replace('\u00a0', '', regex=False)  # еще один вариант неразрывного пробела
            # Удаляем запятые (десятичные разделители)
            df[col] = df[col].str.replace(',', '', regex=False)
            # Заменяем различные варианты NaN
            df[col] = df[col].str.replace('nan', '', regex=False, case=False)
            df[col] = df[col].str.replace('NaN', '', regex=False)
            df[col] = df[col].str.replace('None', '', regex=False)
            # Заменяем пустые строки на 0
            df[col] = df[col].replace('', '0')
            # Преобразуем в числовой формат
            df[col] = pd.to_numeric(df[col], errors='coerce')
            # Заменяем NaN на 0
            df[col] = df[col].fillna(0)

    return df

# Загрузка данных (один раз для всего приложения)
with st.spinner("Загружаем данные..."):
    df = load_data()
    df = clean_data(df)

# Создаем вкладки для разных режимов
tab1, tab2 = st.tabs(["🔍 Анализ запроса", "📅 Анализ по месяцам"])

with tab1:
    st.markdown("---")

    # Выбор товара на основной странице
    st.subheader("🔍 Выбор товара для анализа")

# Устанавливаем поиск только по запросу
search_type = "По запросу"

# Создаем две колонки для выбора
col1, col2 = st.columns([2, 3])

# Выбор категории
with col1:
    if 'категория' in df.columns:
        categories = sorted(df['категория'].dropna().unique())
        selected_category = st.selectbox(
            "Выберите категорию:",
            categories,
            help="Сначала выберите категорию товаров"
        )
    else:
        st.error("Столбец 'категория' не найден")
        selected_category = None

# Выбор запроса в зависимости от категории
with col2:
    if selected_category:
        # Фильтруем данные по выбранной категории
        category_df = df[df['категория'] == selected_category]
        
        # Поиск только по запросу
        if 'запрос' in category_df.columns:
            # Создаем список запросов из выбранной категории
            queries_in_category = sorted(category_df['запрос'].dropna().unique())
            
            if queries_in_category:
                selected_item = st.selectbox(
                    "Выберите запрос:",
                    queries_in_category,
                    help="Выберите поисковый запрос для анализа сезонности"
                )
                
                # Фильтруем данные по запросу и категории
                if selected_item:
                    filtered_df = category_df[category_df['запрос'] == selected_item]
                else:
                    filtered_df = pd.DataFrame()
            else:
                st.warning("В этой категории нет поисковых запросов")
                filtered_df = pd.DataFrame()
        else:
            st.error("Столбец 'запрос' не найден")
            filtered_df = pd.DataFrame()
    else:
        st.info("Выберите категорию для продолжения")
        filtered_df = pd.DataFrame()

st.markdown("---")

# Основная область
if not filtered_df.empty:

    
    # Информация о выбранном товаре/запросе
    product_info = filtered_df.iloc[0]
    

    
    # Подготовка данных для графика
    month_columns = ['январь', 'февраль', 'март', 'апрель', 'май', 'июнь', 
                    'июль', 'август', 'сентябрь', 'октябрь', 'ноябрь', 'декабрь']
    
    # Создаем данные для графика - правильно обрабатываем nan значения
    chart_data = []
    for month in month_columns:
        if month in product_info:
            value = product_info[month]
            # Проверяем на nan и пустые значения
            if pd.notna(value) and value != '' and str(value).strip() != '':
                try:
                    numeric_value = float(value)
                    chart_data.append({
                        'Месяц': month,
                        'Частота': numeric_value
                    })
                except (ValueError, TypeError):
                    # Если не удается преобразовать, ставим 0
                    chart_data.append({
                        'Месяц': month,
                        'Частота': 0
                    })
            else:
                # Добавляем 0 для nan и пустых значений
                chart_data.append({
                    'Месяц': month,
                    'Частота': 0
                })
        else:
            # Если столбца нет вообще, ставим 0
            chart_data.append({
                'Месяц': month,
                'Частота': 0
            })
    
    if chart_data:
        chart_df = pd.DataFrame(chart_data)
        
        # Создаем график
        display_name = product_info['наименование товара'] if search_type == "По товару" else product_info['запрос']
        
        fig = px.line(
            chart_df, 
            x='Месяц', 
            y='Частота',
            title=f"Частотность запросов за год: {display_name}",
            labels={'Частота': 'Частота запросов', 'Месяц': 'Месяц'},
            markers=True
        )
        
        # Улучшаем внешний вид графика
        fig.update_traces(
            line=dict(width=4, color='#1f77b4'),
            marker=dict(size=10, color='#ff7f0e')
        )
        
        fig.update_layout(
            xaxis_title="Месяц",
            yaxis_title="Частота запросов",
            hovermode='x unified',
            height=500,  # Увеличиваем высоту
            plot_bgcolor='rgba(0,0,0,0)',
            xaxis=dict(showgrid=True, gridcolor='lightgray'),
            yaxis=dict(showgrid=True, gridcolor='lightgray'),
            title_font_size=16,
            font=dict(size=12)
        )
        
        # Устанавливаем правильный порядок месяцев
        month_order = ['январь', 'февраль', 'март', 'апрель', 'май', 'июнь', 
                      'июль', 'август', 'сентябрь', 'октябрь', 'ноябрь', 'декабрь']
        fig.update_xaxes(categoryorder='array', categoryarray=month_order)
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Статистика под графиком
        col1, col2, col3, col4, col5 = st.columns(5)
        
        # Вычисляем статистику только для ненулевых значений
        non_zero_values = [item['Частота'] for item in chart_data if item['Частота'] > 0]
        zero_count = len([item['Частота'] for item in chart_data if item['Частота'] == 0])
        
        if non_zero_values:
            max_value = max(chart_data, key=lambda x: x['Частота'])
            min_value = min([item for item in chart_data if item['Частота'] > 0], key=lambda x: x['Частота'])
            avg_frequency = sum(non_zero_values) / len(non_zero_values)
            total_frequency = sum(item['Частота'] for item in chart_data)
            
            with col1:
                st.metric("Пиковый месяц", max_value['Месяц'])
            with col2:
                st.metric("Максимум", f"{max_value['Частота']:,.0f}")
            with col3:
                st.metric("Среднее", f"{avg_frequency:,.0f}")
            with col4:
                st.metric("Месяцев с данными", f"{len(non_zero_values)}/12")
            with col5:
                seasonality_coef = max_value['Частота'] / avg_frequency if avg_frequency > 0 else 0
                st.metric("Коэф. сезонности", f"{seasonality_coef:.2f}")
                
            # Дополнительная информация
            if zero_count > 0:
                st.info(f"ℹ️ У {zero_count} месяцев нет данных (показаны как 0)")
        else:
            st.warning("⚠️ Все месяцы имеют нулевые значения - возможно, данные отсутствуют")
    else:
        st.error("Не удалось создать данные для графика")
else:
    st.info("Выберите товар или поисковый запрос для анализа выше")
    
    # Показываем небольшую подсказку
    st.markdown("""
    ### 💡 Как использовать приложение:
    
    1. **Выберите тип поиска:** по товару или по поисковому запросу
    2. **Выберите категорию:** из списка доступных категорий
    3. **Выберите конкретный товар или запрос** из выбранной категории
    
    Данные показывают частоту поисковых запросов по месяцам, что поможет понять:
    - В какие месяцы товар наиболее популярен
    - Сезонные тренды и пики спроса
    - Планирование закупок и рекламных кампаний
    """)

# Дополнительная информация
if not filtered_df.empty:
    st.markdown("---")
    st.subheader("📋 Детальные данные по месяцам")
    
    # Таблица с данными по месяцам
    month_columns = ['январь', 'февраль', 'март', 'апрель', 'май', 'июнь', 
                    'июль', 'август', 'сентябрь', 'октябрь', 'ноябрь', 'декабрь']
    
    month_data = []
    for month in month_columns:
        if month in product_info and pd.notna(product_info[month]):
            month_data.append({
                'Месяц': month,
                'Частота запросов': f"{product_info[month]:,.0f}"
            })
    
    if month_data:
        month_df = pd.DataFrame(month_data)
        st.dataframe(month_df, use_container_width=True)



    # Футер
    st.markdown("---")
    st.markdown("*Приложение для анализа сезонности товаров на основе данных о частоте запросов*")

# Вторая вкладка - Анализ по месяцам
with tab2:
    st.markdown("---")
    st.subheader("📅 Анализ запросов по месяцам")
    
    # Выбор месяца
    month_columns = ['январь', 'февраль', 'март', 'апрель', 'май', 'июнь', 
                    'июль', 'август', 'сентябрь', 'октябрь', 'ноябрь', 'декабрь']
    
    selected_month = st.selectbox(
        "Выберите месяц для анализа:",
        month_columns,
        help="Выберите месяц, чтобы увидеть все запросы с их частотностью"
    )
    
    if selected_month and selected_month in df.columns:
        # Определяем столбцы месяцев
        month_columns = ['январь', 'февраль', 'март', 'апрель', 'май', 'июнь', 
                        'июль', 'август', 'сентябрь', 'октябрь', 'ноябрь', 'декабрь']
        
        # Получаем данные для выбранного месяца со всеми месяцами для расчета
        columns_to_select = ['запрос', 'категория', 'наименование товара'] + month_columns
        month_data = df[columns_to_select].copy()
        month_data = month_data[month_data[selected_month] > 0]  # Только ненулевые значения для выбранного месяца
        
        if not month_data.empty:
            # Находим максимальную частоту для каждого запроса за все 12 месяцев
            month_data['Макс_частота_за_год'] = month_data[month_columns].max(axis=1)
            
            # Сортируем по максимальной частоте за год
            month_data = month_data.sort_values(by='Макс_частота_за_год', ascending=False)
            
            total_queries = len(month_data)
            
            # Определяем статусы с двумя пиками и падением
            month_data['Статус'] = 'Низкий рост'  # по умолчанию
            
            # Для каждого запроса находим два максимальных значения за год
            for idx, row in month_data.iterrows():
                # Получаем все значения месяцев для этого запроса
                month_values = row[month_columns].values
                # Сортируем по убыванию и берем два максимальных
                sorted_values = sorted(month_values, reverse=True)
                max_value = sorted_values[0]  # самый высокий
                second_max_value = sorted_values[1] if len(sorted_values) > 1 else max_value  # второй по высоте
                
                current_month_value = row[selected_month]
                
                # Определяем статус
                if current_month_value == max_value:
                    month_data.loc[idx, 'Статус'] = 'Пик max'
                elif current_month_value == second_max_value:
                    month_data.loc[idx, 'Статус'] = 'Пик min'
                elif current_month_value >= max_value * 0.5:
                    month_data.loc[idx, 'Статус'] = 'Рост'
                elif current_month_value <= max_value * 0.3:  # Большое падение (более 70% от максимума)
                    month_data.loc[idx, 'Статус'] = 'Большое падение'
                elif current_month_value <= max_value * 0.7:  # Падение (30-70% от максимума)
                    month_data.loc[idx, 'Статус'] = 'Падение'
            
            # Теперь показываем все данные, включая "Падение"
            filtered_month_data = month_data.copy()
            
            # KPI метрики
            total_queries = len(month_data)
            peak_max_queries = len(month_data[month_data['Статус'] == 'Пик max'])
            peak_min_queries = len(month_data[month_data['Статус'] == 'Пик min'])
            growth_queries = len(month_data[month_data['Статус'] == 'Рост'])
            decline_queries = len(month_data[month_data['Статус'] == 'Падение'])
            big_decline_queries = len(month_data[month_data['Статус'] == 'Большое падение'])
            
            # Отображаем KPI
            col1, col2, col3, col4, col5, col6 = st.columns(6)
            with col1:
                st.metric("Всего", total_queries)
            with col2:
                st.metric("Пик max", peak_max_queries)
            with col3:
                st.metric("Пик min", peak_min_queries)
            with col4:
                st.metric("Рост", growth_queries)
            with col5:
                st.metric("Падение", decline_queries)
            with col6:
                st.metric("Большое падение", big_decline_queries)
            
            st.write(f"**Найдено {len(month_data)} запросов с данными в {selected_month}**")
            
            # Фильтрация и сортировка
            col1, col2 = st.columns(2)
            
            with col1:
                status_options = ['Все', 'Пик max', 'Пик min', 'Рост', 'Падение', 'Большое падение']
                selected_status = st.selectbox(
                    "Фильтр по статусу:",
                    status_options,
                    help="Выберите статус для фильтрации запросов"
                )
            
            with col2:
                sort_options = ['По цвету (зеленый → красный)', 'По частотности (высокая → низкая)', 'По алфавиту']
                selected_sort = st.selectbox(
                    "Сортировка:",
                    sort_options,
                    help="Выберите способ сортировки запросов"
                )
            
            # Применяем фильтр по статусу
            if selected_status != 'Все':
                filtered_month_data = filtered_month_data[filtered_month_data['Статус'] == selected_status]
            
            # Применяем сортировку в зависимости от выбора пользователя
            if selected_sort == 'По цвету (зеленый → красный)':
                # Сортировка по цвету (интенсивности)
                def get_color_priority(row):
                    current_month_value = row[selected_month]
                    month_values = [row[month] for month in month_columns]
                    max_val = max(month_values) if month_values else 1
                    if max_val == 0:
                        return 5  # Нулевые значения в конце
                    
                    intensity = current_month_value / max_val
                    
                    if intensity >= 0.9:
                        return 1  # Зеленый - высший приоритет
                    elif intensity >= 0.5:
                        return 2  # Желтый
                    elif intensity >= 0.3:
                        return 3  # Бледно-желтый
                    else:
                        return 4  # Красный - низший приоритет
                
                filtered_month_data['sort_key'] = filtered_month_data.apply(get_color_priority, axis=1)
                filtered_month_data = filtered_month_data.sort_values('sort_key')
                filtered_month_data = filtered_month_data.drop('sort_key', axis=1)
                
            elif selected_sort == 'По частотности (высокая → низкая)':
                # Сортировка по частотности в выбранном месяце
                filtered_month_data = filtered_month_data.sort_values(selected_month, ascending=False)
                
            else:  # По алфавиту
                # Сортировка по названию запроса
                filtered_month_data = filtered_month_data.sort_values('запрос')
            
            # Показываем топ запросы
            st.subheader(f"🔥 Топ запросы в {selected_month}")
            
            # Легенда цветов
            st.markdown(f"""
            **Цветовая схема по частотности:**
            - 🟢 **90%+ от максимума** - зеленый цвет (высокая частотность)
            - 🟡 **50-90% от максимума** - желтый цвет (средняя частотность)
            - 💛 **30-50% от максимума** - бледно-желтый цвет (низкая частотность)
            - 🔴 **Менее 30% от максимума** - красный цвет (очень низкая частотность)
            - 🔵 **{selected_month}** - выделен синим в заголовке (выбранный месяц)
            """)
            
            # Таблица с данными - показываем все месяцы
            display_columns = ['запрос', 'категория'] + month_columns + ['Статус']
            display_data = filtered_month_data[display_columns].copy()
            
            # Переименовываем столбцы для отображения
            display_data.columns = ['Запрос', 'Категория'] + month_columns + ['Статус']
            
            # Форматируем числовые значения
            for month in month_columns:
                display_data[month] = display_data[month].apply(lambda x: f"{x:,.0f}")
            
            # Функция для стилизации таблицы
            def style_dataframe(df):
                # Создаем стилизованный DataFrame без цветового выделения статуса
                styled_df = df.style
                
                # Применяем градацию цвета к столбцам месяцев
                def apply_color_gradient(df_row):
                    styles = [''] * len(df_row)
                    
                    # Получаем статус строки
                    status = df_row.get('Статус', '')
                    
                    # Собираем значения месяцев
                    month_values = []
                    for month in month_columns:
                        try:
                            val = float(str(df_row[month]).replace(',', ''))
                            month_values.append(val)
                        except:
                            month_values.append(0)
                    
                    max_val = max(month_values) if month_values else 1
                    if max_val == 0:
                        return styles
                    
                    # Применяем цвета к каждому месяцу
                    for i, month in enumerate(month_columns):
                        col_idx = list(df_row.index).index(month)
                        val = month_values[i]
                        
                        if val == 0:
                            styles[col_idx] = 'background-color: #f5f5f5'
                            continue
                        
                        intensity = val / max_val
                        
                        # Определяем цвет в зависимости от интенсивности частотности
                        if intensity >= 0.9:
                            # Высокая частотность - зеленый (пики)
                            styles[col_idx] = 'background-color: #4caf50; color: white; font-weight: bold'
                        elif intensity >= 0.5:
                            # Средняя частотность - желтый (рост)
                            styles[col_idx] = 'background-color: #ffeb3b; color: black; font-weight: bold'
                        elif intensity >= 0.3:
                            # Низкая частотность - бледно-желтый (падение)
                            styles[col_idx] = 'background-color: #fff9c4; color: black'
                        else:
                            # Очень низкая частотность - красный (большое падение)
                            styles[col_idx] = 'background-color: #f44336; color: white; font-weight: bold'
                    
                    return styles
                
                # Применяем градацию по строкам
                styled_df = styled_df.apply(apply_color_gradient, axis=1)
                
                # Подсвечиваем заголовок выбранного месяца
                def highlight_selected_month_header(s):
                    styles = [''] * len(s)
                    if selected_month in s.index:
                        month_idx = list(s.index).index(selected_month)
                        styles[month_idx] = 'background-color: #1976d2; color: white; font-weight: bold; border: 2px solid #0d47a1'
                    return styles
                
                styled_df = styled_df.apply(highlight_selected_month_header, axis=0)
                
                return styled_df
            
            # Применяем стилизацию и отображаем таблицу
            styled_df = style_dataframe(display_data)
            st.dataframe(
                styled_df,
                use_container_width=True,
                height=400
            )
            
        else:
            st.warning(f"В {selected_month} нет данных о запросах")
    else:
        st.error("Не удалось загрузить данные для выбранного месяца")
