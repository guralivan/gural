import streamlit as st
import pandas as pd
import numpy as np
import locale
from datetime import datetime, timedelta
import streamlit.components.v1 as components
import streamlit as st
from streamlit import column_config as cc

# Настройка локали для русского языка
try:
    locale.setlocale(locale.LC_ALL, 'ru_RU.UTF-8')
except:
    try:
        locale.setlocale(locale.LC_ALL, 'Russian_Russia.1251')
    except:
        pass

# Функции форматирования
def format_thousands(x, decimals=0):
    if x is None or (isinstance(x, float) and np.isnan(x)):
        return ""
    try:
        xf = float(x)
    except Exception:
        return str(x) if x is not None else ""
    if decimals == 0:
        return f"{int(round(xf))}"
    return f"{xf:.{decimals}f}"

def format_thousands_with_spaces(x, decimals=0):
    if x is None or (isinstance(x, float) and np.isnan(x)):
        return ""
    try:
        xf = float(x)
    except Exception:
        return str(x) if x is not None else ""
    if decimals == 0:
        return f"{int(round(xf)):,}".replace(",", " ")
    return f"{xf:,.{decimals}f}".replace(",", " ").replace(".", ",")

def fmt_rub_kpi(x, decimals=0):
    s = format_thousands_with_spaces(x, decimals=decimals)
    return (s + " ₽") if s != "" else ""

def fmt_units_kpi(x, unit="шт."):
    s = format_thousands_with_spaces(x, decimals=0)
    return (s + f" {unit}") if s != "" else ""

def fmt_rub(x, decimals=0):
    s = format_thousands(x, decimals=decimals)
    return (s + " ₽") if s != "" else ""

def fmt_units(x, unit="шт."):
    s = format_thousands(x, decimals=decimals)
    return (s + f" {unit}") if s != "" else ""

def fmt_date(x):
    if pd.isna(x):
        return ""
    try:
        if isinstance(x, str):
            x = pd.to_datetime(x)
        return x.strftime("%d.%m.%Y")
    except:
        return str(x)

# Функция для отображения KPI
def kpi_row(df):
    if df.empty:
        st.warning("Нет данных для отображения")
        return
    
    # Расчеты
    total_rev = df["Выручка"].sum() if "Выручка" in df.columns else 0
    total_orders = df["Заказы"].sum() if "Заказы" in df.columns else 0
    avg_check = total_rev / total_orders if total_orders > 0 else 0
    lost_rev = df["Упущенная выручка"].sum() if "Упущенная выручка" in df.columns else 0
    rev_per_sku = total_rev / len(df) if len(df) > 0 else 0
    sku_count = len(df)
    
    # Отображение метрик
    k1, k2, k3, k4, k5, k6 = st.columns(6)
    k1.metric("Выручка (в выборке)", fmt_rub_kpi(total_rev))
    k2.metric("Заказы (в выборке)", fmt_units_kpi(total_orders, "шт."))
    k3.metric("Средний чек", fmt_rub_kpi(avg_check))
    k4.metric("Упущенная выручка", fmt_rub_kpi(lost_rev))
    k5.metric("Выручка / Кол-во товаров", fmt_rub_kpi(rev_per_sku))
    k6.metric("Количество артикулов", fmt_units_kpi(sku_count, "шт."))

# Основное приложение
def main():
    st.set_page_config(page_title="WB Dashboard", layout="wide")
    
    st.title("📊 WB Dashboard")
    
    # Загрузка данных
    @st.cache_data
    def load_data():
        try:
            df = pd.read_csv("wb_data.csv")
            return df
        except:
            # Создаем тестовые данные
            np.random.seed(42)
            n = 100
            data = {
                "Артикул": [f"WB{i:06d}" for i in range(1, n+1)],
                "Предмет": np.random.choice(["Футболка", "Джинсы", "Платье", "Куртка"], n),
                "Выручка": np.random.randint(10000, 1000000, n),
                "Заказы": np.random.randint(1, 100, n),
                "Выкупы": np.random.randint(1, 50, n),
                "Средняя цена": np.random.randint(1000, 10000, n),
                "Цена (с СПП)": np.random.randint(800, 8000, n),
                "Прибыль": np.random.randint(1000, 50000, n),
                "Упущенная выручка": np.random.randint(0, 100000, n),
                "Дата создания": pd.date_range("2024-01-01", periods=n, freq="D")
            }
            return pd.DataFrame(data)
    
    df = load_data()
    
    # Фильтры
    st.subheader("🔍 Фильтры")
    
    col1, col2, col3, col4 = st.columns(4)
    
    search = col1.text_input("🔍 Поиск")
    spp = col2.number_input("💰 СПП, %", 0, 100, 25, 1)
    buyout_pct = col3.number_input("📈 Процент выкупа, %", 1, 100, 25, 1)
    
    # Кнопка обновления данных
    col4.markdown("🔄 Обновить данные")
    if col4.button("Обновить", type="primary"):
        st.rerun()
    
    # Фильтр по предмету на отдельной строчке
    if "Предмет" in df.columns:
        subjects = sorted(df["Предмет"].dropna().unique())
        selected_subjects = st.multiselect("📦 Предмет", subjects, default=subjects)
    else:
        selected_subjects = []
    
    # Настройки отображения
    col5, col6 = st.columns(2)
    show_html = col5.checkbox("📋 Показать HTML таблицу", value=False)
    show_images = col6.checkbox("🖼️ Показать изображения", value=False)
    
    # Фильтры по выручке и цене
    col7, col8 = st.columns(2)
    
    if "Выручка" in df.columns:
        revenue_min = col7.number_input("Выручка от", min_value=0, value=0, step=1000)
        revenue_max = col8.number_input("Выручка до", min_value=0, value=int(df["Выручка"].max()) if not df["Выручка"].isna().all() else 1000000, step=1000)
    else:
        revenue_min = 0
        revenue_max = 1000000
    
    col9, col10 = st.columns(2)
    
    if "Цена (с СПП)" in df.columns:
        price_min = col9.number_input("Цена (до СПП) от", min_value=0, value=0, step=100)
        price_max = col10.number_input("Цена (до СПП) до", min_value=0, value=int(df["Цена (с СПП)"].max()) if not df["Цена (с СПП)"].isna().all() else 10000, step=100)
    else:
        price_min = 0
        price_max = 10000
    
    # Фильтр по дате
    if "Дата создания" in df.columns:
        date_col = "Дата создания"
        df[date_col] = pd.to_datetime(df[date_col])
        min_date = df[date_col].min()
        max_date = df[date_col].max()
        
        date_range = st.slider(
            "📅 Выберите диапазон дат",
            min_value=min_date,
            max_value=max_date,
            value=(min_date, max_date),
            format="DD.MM.YYYY"
        )
        
        # Показываем выбранный диапазон в русском формате
        start_date = date_range[0].strftime("%d %B %Y")
        end_date = date_range[1].strftime("%d %B %Y")
        st.info(f"Выбранный диапазон: {start_date} - {end_date}")
    
    # Применение фильтров
    filtered_df = df.copy()
    
    if search:
        mask = filtered_df.astype(str).apply(lambda x: x.str.contains(search, case=False, na=False)).any(axis=1)
        filtered_df = filtered_df[mask]
    
    if selected_subjects:
        filtered_df = filtered_df[filtered_df["Предмет"].isin(selected_subjects)]
    
    if "Выручка" in filtered_df.columns:
        filtered_df = filtered_df[(filtered_df["Выручка"] >= revenue_min) & (filtered_df["Выручка"] <= revenue_max)]
    
    if "Цена (с СПП)" in filtered_df.columns:
        filtered_df = filtered_df[(filtered_df["Цена (с СПП)"] >= price_min) & (filtered_df["Цена (с СПП)"] <= price_max)]
    
    if "Дата создания" in filtered_df.columns:
        filtered_df = filtered_df[(filtered_df[date_col] >= date_range[0]) & (filtered_df[date_col] <= date_range[1])]
    
    # Отображение KPI
    st.subheader("📈 Ключевые показатели")
    kpi_row(filtered_df)
    
    # Отображение данных
    if not filtered_df.empty:
        st.subheader("📊 Данные")
        
        # Подготовка данных для отображения
        display_df = filtered_df.copy()
        
        # Форматирование даты
        if "Дата создания" in display_df.columns:
            display_df["Дата создания"] = display_df["Дата создания"].apply(fmt_date)
        
        # Оставляем числовые данные как есть для корректной сортировки в Streamlit таблице
        
        # Изменение порядка столбцов
        if "Артикул" in display_df.columns:
            cols = ["Артикул"] + [col for col in display_df.columns if col != "Артикул"]
            display_df = display_df[cols]
        
        if show_html:
            # HTML режим
            html_df = display_df.copy()
            
            # Добавляем ссылки для HTML таблицы
            if "Артикул" in html_df.columns:
                links = []
                for sku in html_df["Артикул"].astype(str):
                    sku_clean = sku.replace(".0", "")
                    link_html = f'<a href="https://global.wildberries.ru/catalog/{sku_clean}/detail.aspx" target="_blank" style="color: #0066cc; text-decoration: none; font-weight: bold;">Открыть</a>'
                    links.append(link_html)
                html_df["Ссылка"] = links
            
            # Создаем HTML таблицу вручную
            html_parts = []
            html_parts.append('<table class="wb-table">')
            
            # Заголовки
            html_parts.append('<thead>')
            html_parts.append('<tr>')
            for col in html_df.columns:
                html_parts.append(f'<th>{col}</th>')
            html_parts.append('</tr>')
            html_parts.append('</thead>')
            
            # Данные
            html_parts.append('<tbody>')
            for _, row in html_df.iterrows():
                html_parts.append('<tr>')
                for col in html_df.columns:
                    value = row[col]
                    if pd.isna(value):
                        value = ""
                    html_parts.append(f'<td>{value}</td>')
                html_parts.append('</tr>')
            html_parts.append('</tbody>')
            html_parts.append('</table>')
            
            html_table = '\n'.join(html_parts)
            
            # CSS стили
            css_styles = """
            <style>
            .wb-table {
                width: 100%;
                border-collapse: collapse;
                margin: 20px 0;
                font-family: Arial, sans-serif;
                font-size: 12px;
                border: 1px solid #ddd;
            }
            .wb-table th {
                background: #4CAF50;
                color: white;
                padding: 8px;
                text-align: left;
                font-weight: bold;
                border: 1px solid #ddd;
            }
            .wb-table td {
                padding: 8px;
                border: 1px solid #ddd;
                vertical-align: top;
            }
            .wb-table tr:nth-child(even) {
                background-color: #f2f2f2;
            }
            .wb-table tr:hover {
                background-color: #ddd;
            }
            .wb-table a {
                color: #0066cc;
                text-decoration: none;
                font-weight: bold;
            }
            .wb-table a:hover {
                text-decoration: underline;
            }
            </style>
            """
            
            # Отображаем таблицу
            st.markdown(css_styles + html_table, unsafe_allow_html=True)
            
        else:
            # Обычный режим Streamlit
            
            # Настройка конфигурации столбцов для лучшего отображения
            col_cfg = {}
            
            # Конфигурация для артикула (обычный текст)
            if "Артикул" in display_df.columns:
                col_cfg["Артикул"] = cc.TextColumn("Артикул", width=120)
            
            # Конфигурация для ссылки на товар с динамическими URL
            if "Артикул" in display_df.columns:
                # Создаем ссылки на основе артикулов
                links_data = []
                for sku in display_df["Артикул"].astype(str):
                    sku_clean = sku.replace(".0", "")
                    links_data.append(f"https://global.wildberries.ru/catalog/{sku_clean}/detail.aspx")
                display_df["Ссылка"] = links_data
                col_cfg["Ссылка"] = cc.LinkColumn("Ссылка", display_text="Открыть", width=120)
            
            # Конфигурация для числовых столбцов (NumberColumn для корректной сортировки)
            money_columns = ["Выручка", "Средняя цена", "Цена (с СПП)", "Упущенная выручка", "Прибыль"]
            for col in money_columns:
                if col in display_df.columns:
                    col_cfg[col] = cc.NumberColumn(col, format="%.0f ₽", width=120)
            
            # Конфигурация для числовых столбцов с единицами
            if "Заказы" in display_df.columns:
                col_cfg["Заказы"] = cc.NumberColumn("Заказы", format="%.0f шт.", width=120)
            if "Выкупы" in display_df.columns:
                col_cfg["Выкупы"] = cc.NumberColumn("Выкупы", format="%.0f шт.", width=120)
            
            # Конфигурация для даты
            if "Дата создания" in display_df.columns:
                col_cfg["Дата создания"] = cc.TextColumn("Дата создания", width=120)
            
            # Конфигурация для предмета
            if "Предмет" in display_df.columns:
                col_cfg["Предмет"] = cc.TextColumn("Предмет", width=120)
            
            # Отображение таблицы с сортировкой по умолчанию
            st.dataframe(
                display_df,
                column_config=col_cfg,
                hide_index=True,
                use_container_width=True,
                column_order=["Артикул", "Ссылка", "Предмет", "Выручка", "Заказы", "Выкупы", "Средняя цена", "Цена (с СПП)", "Прибыль", "Упущенная выручка", "Дата создания"]
            )
    else:
        st.warning("Нет данных, соответствующих выбранным фильтрам")

if __name__ == "__main__":
    main()




