# -*- coding: utf-8 -*-
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

@st.cache_data
def load_seasonality_data():
    """Загрузка данных из CSV файла"""
    encodings = ['utf-8', 'cp1251', 'latin1', 'utf-8-sig']
    separators = [',', ';', '\t']
    for encoding in encodings:
        for sep in separators:
            try:
                df = pd.read_csv('sezon.csv', encoding=encoding, sep=sep)
                if len(df.columns) > 10 and len(df) > 10:
                    return df
            except Exception as e:
                continue
    return pd.read_csv('sezon.csv', encoding='utf-8')

def load_custom_data(uploaded_file):
    """Загрузка пользовательских данных из файла"""
    try:
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file, encoding='utf-8')
        elif uploaded_file.name.endswith('.xlsx'):
            df = pd.read_excel(uploaded_file)
        else:
            return None, "Неподдерживаемый формат файла. Используйте CSV или Excel."
        
        # Проверяем наличие необходимых столбцов
        month_columns = ['январь', 'февраль', 'март', 'апрель', 'май', 'июнь',
                          'июль', 'август', 'сентябрь', 'октябрь', 'ноябрь', 'декабрь']
        
        required_columns = ['запрос', 'категория'] + month_columns
        
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            return None, f"Отсутствуют обязательные столбцы: {', '.join(missing_columns)}"
        
        return df, "Данные успешно загружены"
    except Exception as e:
        return None, f"Ошибка при загрузке файла: {str(e)}"

def create_manual_entry_data(query, category, frequencies):
    """Создание данных для ручного ввода"""
    month_columns = ['январь', 'февраль', 'март', 'апрель', 'май', 'июнь',
                      'июль', 'август', 'сентябрь', 'октябрь', 'ноябрь', 'декабрь']
    
    data = {
        'запрос': [query],
        'категория': [category],
        'наименование товара': [query]
    }
    
    for i, month in enumerate(month_columns):
        data[month] = [frequencies[i] if i < len(frequencies) else 0]
    
    return pd.DataFrame(data)

def clean_seasonality_data(df):
    """Очистка и подготовка данных"""
    header_row = None
    for i, row in df.iterrows():
        if 'наименование товара' in str(row.values):
            header_row = i
            break
    if header_row is not None:
        df.columns = df.iloc[header_row]
        df = df.iloc[header_row + 1:].reset_index(drop=True)
    if 'наименование товара' in df.columns:
        df = df.dropna(subset=['наименование товара'])
        df = df[df['наименование товара'] != 'наименование товара']
    month_columns = ['январь', 'февраль', 'март', 'апрель', 'май', 'июнь',
                      'июль', 'август', 'сентябрь', 'октябрь', 'ноябрь', 'декабрь']
    for col in month_columns:
        if col in df.columns:
            df[col] = df[col].astype(str)
            df[col] = df[col].str.replace(' ', '', regex=False)
            df[col] = df[col].str.replace('\xa0', '', regex=False)
            df[col] = df[col].str.replace('\u00a0', '', regex=False)
            df[col] = df[col].str.replace(',', '', regex=False)
            df[col] = df[col].str.replace('nan', '', regex=False, case=False)
            df[col] = df[col].str.replace('NaN', '', regex=False)
            df[col] = df[col].str.replace('None', '', regex=False)
            df[col] = df[col].replace('', '0')
            df[col] = pd.to_numeric(df[col], errors='coerce')
            df[col] = df[col].fillna(0)
    return df

def create_seasonality_graph(filtered_df, selected_item):
    """Создание графика сезонности"""
    if filtered_df.empty:
        return None
    
    month_columns = ['январь', 'февраль', 'март', 'апрель', 'май', 'июнь',
                      'июль', 'август', 'сентябрь', 'октябрь', 'ноябрь', 'декабрь']
    
    # Получаем данные для графика
    row = filtered_df.iloc[0]
    months = []
    frequencies = []
    
    for month in month_columns:
        if month in row.index:
            months.append(month.capitalize())
            frequencies.append(row[month])
    
    # Создаем график
    fig = px.line(
        x=months, 
        y=frequencies,
        title=f"Сезонность запроса: {selected_item}",
        labels={'x': 'Месяц', 'y': 'Частота'},
        markers=True
    )
    
    fig.update_layout(
        xaxis_title="Месяц",
        yaxis_title="Частота",
        height=400,
        showlegend=False
    )
    
    return fig

def get_status_stats(month_data, selected_month):
    """Получение статистики по статусам"""
    if month_data.empty:
        return {}
    
    month_columns = ['январь', 'февраль', 'март', 'апрель', 'май', 'июнь',
                      'июль', 'август', 'сентябрь', 'октябрь', 'ноябрь', 'декабрь']
    
    month_data['Макс_частота_за_год'] = month_data[month_columns].max(axis=1)
    month_data['Статус'] = 'Низкий рост'
    
    for idx, row in month_data.iterrows():
        month_values = row[month_columns].values
        sorted_values = sorted(month_values, reverse=True)
        max_value = sorted_values[0]
        second_max_value = sorted_values[1] if len(sorted_values) > 1 else max_value
        current_month_value = row[selected_month]
        
        if current_month_value == max_value:
            month_data.loc[idx, 'Статус'] = 'Пик max'
        elif current_month_value == second_max_value:
            month_data.loc[idx, 'Статус'] = 'Пик min'
        elif current_month_value >= max_value * 0.5:
            month_data.loc[idx, 'Статус'] = 'Рост'
        elif current_month_value <= max_value * 0.3:
            month_data.loc[idx, 'Статус'] = 'Большое падение'
        elif current_month_value <= max_value * 0.7:
            month_data.loc[idx, 'Статус'] = 'Падение'
    
    # Подсчитываем статистику
    status_counts = month_data['Статус'].value_counts()
    stats = {
        'Всего': len(month_data),
        'Пик max': status_counts.get('Пик max', 0),
        'Пик min': status_counts.get('Пик min', 0),
        'Рост': status_counts.get('Рост', 0),
        'Падение': status_counts.get('Падение', 0),
        'Большое падение': status_counts.get('Большое падение', 0)
    }
    
    return stats, month_data

def style_dataframe(df, selected_month):
    """Стилизация таблицы с цветовой градацией"""
    def highlight_selected_month_header(val):
        if val == selected_month:
            return 'background-color: #2196F3; color: white; font-weight: bold'
        return ''
    
    def apply_color_gradient(val, max_val):
        if pd.isna(val) or val == 0:
            return 'background-color: #f5f5f5; color: #666'
        
        if max_val == 0:
            return ''
        
        intensity = val / max_val
        
        if intensity >= 0.9:
            return 'background-color: #4caf50; color: white; font-weight: bold'
        elif intensity >= 0.5:
            return 'background-color: #ffeb3b; color: black; font-weight: bold'
        elif intensity >= 0.3:
            return 'background-color: #fff9c4; color: black'
        else:
            return 'background-color: #f44336; color: white; font-weight: bold'
    
    # Форматируем числовые значения
    month_columns = ['январь', 'февраль', 'март', 'апрель', 'май', 'июнь',
                      'июль', 'август', 'сентябрь', 'октябрь', 'ноябрь', 'декабрь']
    
    styled_df = df.copy()
    
    for col in month_columns:
        if col in styled_df.columns:
            styled_df[col] = styled_df[col].apply(lambda x: f"{x:,.0f}" if pd.notna(x) else "0")
    
    # Применяем стили
    def style_row(row):
        styles = [''] * len(row)
        month_values = [row[month] for month in month_columns if month in row.index]
        max_val = max([float(str(val).replace(',', '')) for val in month_values if str(val).replace(',', '').replace('.', '').isdigit()]) if month_values else 1
        
        for col_idx, (col_name, val) in enumerate(row.items()):
            if col_name in month_columns:
                try:
                    val_num = float(str(val).replace(',', ''))
                    styles[col_idx] = apply_color_gradient(val_num, max_val)
                except:
                    styles[col_idx] = ''
            elif col_name == 'Статус':
                styles[col_idx] = 'background-color: white; color: black'
        
        return styles
    
    return styled_df.style.apply(style_row, axis=1)
