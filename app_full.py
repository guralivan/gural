# -*- coding: utf-8 -*-
import os
import json
import base64
from io import BytesIO
import urllib.parse as _urlparse

import pandas as pd
import numpy as np
import streamlit as st
import requests

try:
    from PIL import Image
except Exception:
    Image = None

st.set_page_config(page_title="WB Dashboard — Анализ товаров", layout="wide")

# ================= ФУНКЦИИ ДЛЯ РАБОТЫ С ПАРАМЕТРАМИ =================

def save_param_value(sku: str, param: str, value: str):
    """Сохраняет значение параметра для товара"""
    if "param_values" not in st.session_state:
        st.session_state["param_values"] = {}
    if sku not in st.session_state["param_values"]:
        st.session_state["param_values"][sku] = {}
    st.session_state["param_values"][sku][param] = value

def get_param_values():
    """Получает все сохраненные значения параметров"""
    return st.session_state.get("param_values", {})

def save_param_values_to_file():
    """Сохраняет параметры в файл"""
    param_values = get_param_values()
    if param_values:
        try:
            with open("param_values.json", "w", encoding="utf-8") as f:
                json.dump(param_values, f, ensure_ascii=False, indent=2)
            return True
        except Exception:
            return False
    return False

def load_param_values_from_file():
    """Загружает параметры из файла"""
    try:
        if os.path.exists("param_values.json"):
            with open("param_values.json", "r", encoding="utf-8") as f:
                data = json.load(f)
                st.session_state["param_values"] = data
                return True
    except Exception:
        pass
    return False

# ================= ФУНКЦИИ ДЛЯ РАБОТЫ С ИЗОБРАЖЕНИЯМИ =================

def _cache_root():
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "wb_cache")

def _cache_dir():
    d = _cache_root()
    os.makedirs(d, exist_ok=True)
    os.makedirs(os.path.join(d, "imgs"), exist_ok=True)
    return d

def _url_cache_path():
    return os.path.join(_cache_dir(), "image_cache.json")

def load_url_cache():
    p = _url_cache_path()
    if os.path.exists(p):
        try:
            with open(p, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_url_cache(m: dict):
    try:
        with open(_url_cache_path(), "w", encoding="utf-8") as f:
            json.dump(m, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

def get_url_cache():
    if "img_url_cache" not in st.session_state:
        st.session_state["img_url_cache"] = load_url_cache()
    return st.session_state["img_url_cache"]

def img_path_for(nm: str, fmt: str = "JPEG"):
    nm = str(nm).replace(".0", "")
    ext = "jpg" if fmt.upper() == "JPEG" else "png"
    return os.path.join(_cache_dir(), "imgs", f"{nm}.{ext}")

def get_cached_image_path(nm: str):
    nm = str(nm).replace(".0", "")
    for ext in ("jpg", "png", "jpeg", "webp"):
        p = os.path.join(_cache_dir(), "imgs", f"{nm}.{ext}")
        if os.path.exists(p):
            return p
    return ""

def ensure_image_cached(nm: str, url: str, fmt: str = "JPEG", timeout: int = 25) -> str:
    try:
        p_exist = get_cached_image_path(nm)
        if p_exist:
            return p_exist
        if not url:
            return ""
        path = img_path_for(nm, fmt)
        headers = {"User-Agent": "WB-Dashboard/1.0"}
        with requests.get(url, headers=headers, timeout=timeout, stream=True) as r:
            if r.status_code != 200:
                return ""
            with open(path, "wb") as f:
                for chunk in r.iter_content(8192):
                    if chunk:
                        f.write(chunk)
        return path
    except Exception:
        return ""

def load_image_bytes(path: str, max_w: int | None = None) -> bytes:
    if not path or not os.path.exists(path):
        return b""
    if Image is None or max_w is None:
        try:
            with open(path, "rb") as f:
                return f.read()
        except Exception:
            return b""
    try:
        im = Image.open(path)
        if im.mode not in ("RGB", "RGBA"):
            im = im.convert("RGB")
        if max_w and im.width > max_w:
            ratio = max_w / float(im.width)
            im = im.resize((int(im.width * ratio), int(im.height * ratio)))
        bio = BytesIO()
        im.save(bio, format="JPEG", quality=85)
        return bio.getvalue()
    except Exception:
        try:
            with open(path, "rb") as f:
                return f.read()
        except Exception:
            return b""

def img_data_uri(nm: str, max_w: int | None = None) -> str:
    """Создает data URI для изображения"""
    try:
        cached_path = get_cached_image_path(nm)
        if not cached_path:
            return ""
        img_bytes = load_image_bytes(cached_path, max_w)
        if not img_bytes:
            return ""
        b64 = base64.b64encode(img_bytes).decode('utf-8')
        return f"data:image/jpeg;base64,{b64}"
    except Exception:
        return ""

# ================= ФУНКЦИИ ДЛЯ РАБОТЫ С СКРИНШОТАМИ =================

def build_wb_product_url(nm, host="https://global.wildberries.ru"):
    return f"{host.rstrip('/')}/catalog/{str(nm).replace('.0','')}/detail.aspx"

def build_screenshot_url(page_url: str, key: str, w: int = 400, h: int = 600, fmt: str = "JPEG", profile: str = "D4", base: str = "https://api.s-shot.ru"):
    q = _urlparse.quote(page_url, safe="")
    return f"{base.rstrip('/')}/{int(w)}x{int(h)}/{fmt}/{key}/{profile}/?{q}"

def screenshot_for_article(nm, conf):
    if not conf.get("key"): 
        return ""
    page = build_wb_product_url(nm, conf.get("wb_host","https://global.wildberries.ru"))
    return build_screenshot_url(page, conf.get("key",""), conf.get("w",400), conf.get("h",600), conf.get("fmt","JPEG"), conf.get("profile","D4"), conf.get("base","https://api.s-shot.ru"))

# ================= ФУНКЦИИ ДЛЯ РАБОТЫ С ТАБЛИЦАМИ =================

def read_table(file_bytes, filename):
    """Читает Excel или CSV файл"""
    try:
        if filename.lower().endswith((".xlsx", ".xls")):
            df_raw = pd.read_excel(BytesIO(file_bytes), sheet_name=0, header=None)
        else:
            df_raw = pd.read_csv(BytesIO(file_bytes), header=None, sep=None, engine="python")
    except Exception as e:
        st.error(f"Ошибка чтения файла: {e}")
        return None, None, None

    # Поиск заголовков
    header_row = None
    for i, row in df_raw.iterrows():
        if row.astype(str).str.contains("Артикул|артикул|Артикул|Артикул").any():
            header_row = i
            break
    
    if header_row is None:
        st.error("Не найден столбец 'Артикул' в файле")
        return None, None, None

    # Чтение с заголовками
    if filename.lower().endswith((".xlsx",".xls")):
        df = pd.read_excel(BytesIO(file_bytes), sheet_name=0, header=header_row)
    else:
        df = pd.read_csv(BytesIO(file_bytes), header=header_row, sep=None, engine="python")
    
    df = df.loc[:, ~df.columns.astype(str).str.startswith("Unnamed")]
    
    # Переименование столбцов
    column_mapping = {
        "Средняя цена": "Цена (без СПП)",
        "Цена": "Цена (без СПП)",
        "Цена до СПП": "Цена (без СПП)",
        "Цена с СПП": "Цена (с СПП)",
        "Цена после СПП": "Цена (с СПП)",
        "Количество заказов": "Заказы",
        "Заказы": "Заказы",
        "Выручка": "Выручка",
        "Доход": "Выручка",
        "Прибыль": "Прибыль",
        "Маржа": "Прибыль"
    }
    
    df = df.rename(columns=column_mapping)
    
    # Конвертация типов
    if "Артикул" in df.columns:
        df["Артикул"] = df["Артикул"].astype(str)
    
    numeric_columns = ["Выручка", "Заказы", "Цена (без СПП)", "Цена (с СПП)", "Прибыль"]
    for col in numeric_columns:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    return df, df_raw, {"header_row": header_row, "filename": filename}

# ================= ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ =================

def fmt_rub(x):
    """Форматирует число как рубли"""
    if pd.isna(x):
        return ""
    try:
        return f"{int(x):,} ₽".replace(",", " ")
    except:
        return str(x)

def fmt_units(x, unit=""):
    """Форматирует число с единицами измерения"""
    if pd.isna(x):
        return ""
    try:
        return f"{int(x):,} {unit}".replace(",", " ")
    except:
        return str(x)

def fmt_date(x):
    """Форматирует дату"""
    if pd.isna(x):
        return ""
    try:
        return pd.to_datetime(x).strftime("%d.%m.%Y")
    except:
        return str(x)

def parse_thousands_input(input_str, default_value):
    """Парсит строку с тысячами разделителями"""
    if not input_str or input_str.strip() == "":
        return default_value
    try:
        # Убираем пробелы и заменяем запятые на точки
        cleaned = input_str.replace(" ", "").replace(",", ".")
        return float(cleaned)
    except:
        return default_value

# ================= ОСНОВНОЕ ПРИЛОЖЕНИЕ =================

# Загружаем сохраненные параметры
load_param_values_from_file()

# Инициализация session_state
if "schemas" not in st.session_state:
    st.session_state["schemas"] = {}

# Сайдбар
with st.sidebar:
    st.title("⚙️ Настройки")
    
    # API ключ для скриншотов
    sc_key = st.text_input("🔑 API ключ s-shot.ru", type="password", help="Ключ для генерации скриншотов товаров")
    
    # Настройки скриншотов
    sc_w = st.number_input("📐 Ширина скриншота", min_value=100, max_value=1200, value=400, step=50)
    sc_h = st.number_input("📐 Высота скриншота", min_value=100, max_value=1200, value=600, step=50)
    sc_fmt = st.selectbox("📷 Формат скриншота", ["JPEG", "PNG"], index=0)
    sc_host = st.text_input("🌐 Хост Wildberries", value="https://global.wildberries.ru")
    
    # Конфигурация скриншотов
    sc_conf = {
        "key": sc_key,
        "w": sc_w,
        "h": sc_h,
        "fmt": sc_fmt,
        "wb_host": sc_host,
        "base": "https://api.s-shot.ru"
    }
    
    # Загрузка файла
    uploaded = st.file_uploader("📁 Загрузить файл", type=["xlsx", "csv"], help="Загрузите Excel или CSV файл с данными товаров")
    
    # Кнопка сохранения параметров
    if st.button("💾 Сохранить параметры"):
        if save_param_values_to_file():
            st.success("✅ Параметры сохранены!")
        else:
            st.error("❌ Ошибка сохранения параметров")

# Основной контент
if uploaded is not None:
    file_bytes = uploaded.read()
    df, raw, meta = read_table(file_bytes, uploaded.name)
    
    if df is not None and not df.empty:
        st.success(f"✅ Файл загружен: {uploaded.name}")
        
        # Создаем вкладки
        tab1, tab2, tab3 = st.tabs(["📊 Дашборд", "⚙️ Параметры", "📈 Аналитика"])
        
        with tab1:
            st.header("📊 Дашборд товаров")
            
            # Фильтры
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                search = st.text_input("🔍 Поиск", placeholder="Поиск по артикулу или названию")
            
            with col2:
                if "Предмет" in df.columns:
                    subject_filter = st.multiselect("📦 Предмет", options=df["Предмет"].dropna().unique())
                else:
                    subject_filter = []
            
            with col3:
                if "Поставщик" in df.columns:
                    supplier_filter = st.multiselect("🏢 Поставщик", options=df["Поставщик"].dropna().unique())
                else:
                    supplier_filter = []
            
            with col4:
                if "Бренд" in df.columns:
                    brand_filter = st.multiselect("🏷️ Бренд", options=df["Бренд"].dropna().unique())
                else:
                    brand_filter = []
            
            # Применяем фильтры
            filtered_df = df.copy()
            
            if search:
                mask = (
                    filtered_df["Артикул"].astype(str).str.contains(search, case=False, na=False) |
                    (filtered_df["Название"].astype(str).str.contains(search, case=False, na=False) if "Название" in filtered_df.columns else False)
                )
                filtered_df = filtered_df[mask]
            
            if subject_filter:
                filtered_df = filtered_df[filtered_df["Предмет"].isin(subject_filter)]
            
            if supplier_filter:
                filtered_df = filtered_df[filtered_df["Поставщик"].isin(supplier_filter)]
            
            if brand_filter:
                filtered_df = filtered_df[filtered_df["Бренд"].isin(brand_filter)]
            
            # KPI
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                total_revenue = filtered_df["Выручка"].sum() if "Выручка" in filtered_df.columns else 0
                st.metric("💰 Общая выручка", fmt_rub(total_revenue))
            
            with col2:
                total_orders = filtered_df["Заказы"].sum() if "Заказы" in filtered_df.columns else 0
                st.metric("📦 Общие заказы", fmt_units(total_orders, "шт."))
            
            with col3:
                avg_price = filtered_df["Цена (без СПП)"].mean() if "Цена (без СПП)" in filtered_df.columns else 0
                st.metric("💵 Средняя цена", fmt_rub(avg_price))
            
            with col4:
                total_items = len(filtered_df)
                st.metric("📋 Товаров", total_items)
            
            # Таблица с данными
            st.subheader("📋 Данные товаров")
            
            # Добавляем столбцы с параметрами
            display_df = filtered_df.copy()
            
            # Добавляем столбец с изображениями
            if sc_key and "Артикул" in display_df.columns:
                st.info("🖼️ Загружаем изображения...")
                
                image_column = []
                for idx, row in display_df.iterrows():
                    nm = str(row["Артикул"]).replace(".0", "")
                    
                    # Проверяем кэш
                    cached_path = get_cached_image_path(nm)
                    if cached_path:
                        img_bytes = load_image_bytes(cached_path, max_w=200)
                        if img_bytes:
                            image_column.append(img_bytes)
                        else:
                            image_column.append("")
                    else:
                        # Загружаем через API
                        screenshot_url = screenshot_for_article(nm, sc_conf)
                        if screenshot_url:
                            try:
                                headers = {"User-Agent": "WB-Dashboard/1.0"}
                                response = requests.get(screenshot_url, headers=headers, timeout=10)
                                if response.status_code == 200:
                                    # Сохраняем в кэш
                                    ensure_image_cached(nm, screenshot_url, sc_fmt)
                                    img_bytes = load_image_bytes(get_cached_image_path(nm), max_w=200)
                                    image_column.append(img_bytes)
                                else:
                                    image_column.append("")
                            except Exception:
                                image_column.append("")
                        else:
                            image_column.append("")
                else:
                    image_column = [""] * len(display_df)
                
                if image_column:
                    display_df.insert(1, "Изображение", image_column)
            
            # Добавляем столбец со ссылками
            if "Артикул" in display_df.columns:
                display_df.insert(2, "Ссылка", display_df["Артикул"].astype(str).map(lambda s: build_wb_product_url(s.replace(".0",""), sc_host)))
            
            # Настройка отображения столбцов
            from streamlit import column_config as cc
            
            col_cfg = {}
            if "Изображение" in display_df.columns:
                col_cfg["Изображение"] = cc.ImageColumn(width=200)
            if "Ссылка" in display_df.columns:
                col_cfg["Ссылка"] = cc.LinkColumn(display_text="Открыть", help="Открыть карточку на Wildberries")
            
            # Отображаем таблицу
            st.dataframe(display_df, use_container_width=True, hide_index=True, column_config=col_cfg)
        
        with tab2:
            st.header("⚙️ Управление параметрами")
            
            # Создание параметров
            st.subheader("➕ Создать новый параметр")
            
            col1, col2 = st.columns(2)
            
            with col1:
                param_name = st.text_input("Название параметра", placeholder="Например: Цвет, Размер, Крой")
            
            with col2:
                param_values = st.text_area("Значения (через /)", placeholder="Красный/Синий/Зеленый")
            
            if st.button("➕ Добавить параметр"):
                if param_name and param_values:
                    values_list = [v.strip() for v in param_values.split("/") if v.strip()]
                    if values_list:
                        st.session_state["schemas"][param_name] = values_list
                        st.success(f"✅ Параметр '{param_name}' создан с {len(values_list)} значениями!")
                        st.rerun()
                    else:
                        st.error("❌ Введите хотя бы одно значение")
                else:
                    st.error("❌ Заполните название и значения параметра")
            
            # Список параметров
            st.subheader("📋 Существующие параметры")
            
            if st.session_state["schemas"]:
                for param_name, values in st.session_state["schemas"].items():
                    with st.expander(f"📋 {param_name} ({len(values)} значений)"):
                        st.write("Значения:", ", ".join(values))
                        
                        if st.button(f"🗑️ Удалить {param_name}", key=f"del_{param_name}"):
                            del st.session_state["schemas"][param_name]
                            st.rerun()
            else:
                st.info("📝 Параметры не созданы. Создайте первый параметр выше.")
            
            # Назначение параметров товарам
            if st.session_state["schemas"]:
                st.subheader("🎯 Назначение параметров товарам")
                
                # Выбор параметра для назначения
                selected_param = st.selectbox("Выберите параметр", list(st.session_state["schemas"].keys()))
                
                if selected_param:
                    param_values = st.session_state["schemas"][selected_param]
                    
                    # Создаем таблицу для назначения
                    assign_df = filtered_df[["Артикул"]].copy()
                    assign_df["Значение"] = ""
                    
                    # Добавляем столбец с выпадающим списком
                    assign_df["Значение"] = st.selectbox(
                        f"Значение параметра '{selected_param}'",
                        [""] + param_values,
                        key="param_assignment"
                    )
                    
                    if st.button("💾 Сохранить назначения"):
                        if assign_df["Значение"].iloc[0]:  # Если выбрано значение
                            sku = str(assign_df["Артикул"].iloc[0]).replace(".0", "")
                            value = assign_df["Значение"].iloc[0]
                            save_param_value(sku, selected_param, value)
                            st.success(f"✅ Параметр '{selected_param}' = '{value}' назначен товару {sku}")
                        else:
                            st.warning("⚠️ Выберите значение параметра")
        
        with tab3:
            st.header("📈 Аналитика по параметрам")
            
            param_values = get_param_values()
            
            if param_values:
                st.subheader("📊 Статистика по параметрам")
                
                # Создаем аналитическую таблицу
                analytics_data = []
                
                for sku, params in param_values.items():
                    if sku in filtered_df["Артикул"].astype(str).values:
                        row_data = {"Артикул": sku}
                        
                        # Добавляем параметры
                        for param, value in params.items():
                            row_data[param] = value
                        
                        # Добавляем данные из основного DataFrame
                        sku_row = filtered_df[filtered_df["Артикул"].astype(str) == sku].iloc[0]
                        for col in ["Выручка", "Заказы", "Цена (без СПП)", "Цена (с СПП)"]:
                            if col in sku_row:
                                row_data[col] = sku_row[col]
                        
                        analytics_data.append(row_data)
                
                if analytics_data:
                    analytics_df = pd.DataFrame(analytics_data)
                    
                    # Добавляем анализ лучших комбинаций параметров
                    st.subheader("🏆 Лучшие комбинации параметров")
                    
                    # Отладочная информация
                    st.write(f"**Доступные параметры**: {available_params}")
                    st.write(f"**Количество параметров**: {len(available_params) if available_params else 0}")
                    
                    # Функция для расчета рейтинга параметров
                    def calculate_parameter_rating(df, param_name):
                        """Рассчитывает рейтинг параметра на основе выручки и заказов"""
                        if param_name not in df.columns:
                            return pd.DataFrame()
                        
                        # Группируем по значению параметра
                        grouped = df.groupby(param_name).agg({
                            "Выручка": ["sum", "mean", "count"],
                            "Заказы": ["sum", "mean"]
                        }).round(2)
                        
                        grouped.columns = ["Общая выручка", "Средняя выручка", "Количество товаров", "Общие заказы", "Средние заказы"]
                        
                        # Нормализуем показатели (0-100)
                        if grouped["Общая выручка"].max() > 0:
                            grouped["Рейтинг выручки"] = (grouped["Общая выручка"] / grouped["Общая выручка"].max() * 100).round(1)
                        else:
                            grouped["Рейтинг выручки"] = 0
                            
                        if grouped["Общие заказы"].max() > 0:
                            grouped["Рейтинг заказов"] = (grouped["Общие заказы"] / grouped["Общие заказы"].max() * 100).round(1)
                        else:
                            grouped["Рейтинг заказов"] = 0
                        
                        # Общий рейтинг (среднее арифметическое)
                        grouped["Общий рейтинг"] = ((grouped["Рейтинг выручки"] + grouped["Рейтинг заказов"]) / 2).round(1)
                        
                        return grouped.sort_values("Общий рейтинг", ascending=False)
                    
                    # Получаем все параметры
                    available_params = [col for col in analytics_df.columns if col not in ["Артикул", "Выручка", "Заказы", "Цена (без СПП)", "Цена (с СПП)"]]
                    
                    if available_params:
                        # Анализируем каждый параметр отдельно
                        param_ratings = {}
                        
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.write("**Рейтинг значений параметров:**")
                            
                            for param in available_params:
                                rating_df = calculate_parameter_rating(analytics_df, param)
                                if not rating_df.empty:
                                    param_ratings[param] = rating_df
                                    
                                    with st.expander(f"📊 {param}"):
                                        st.dataframe(rating_df[["Общий рейтинг", "Рейтинг выручки", "Рейтинг заказов", "Общая выручка", "Общие заказы"]], use_container_width=True)
                        
                        with col2:
                            st.write("**Лучшие комбинации:**")
                            
                            # Выбор алгоритма анализа комбинаций
                            algorithm_choice = st.radio(
                                "Алгоритм:",
                                ["🏆 По рейтингу параметров", "📊 По эффективности"],
                                help="'По рейтингу параметров' - комбинации формируются из значений с рейтингом 1. 'По эффективности' - по фактическим показателям выручки и заказов.",
                                key="algorithm_choice_app_full"
                            )
                            
                            # Создает идеальную комбинацию на основе рейтингов параметров
                            def create_ideal_combination_from_ratings(param_ratings):
                                """Создает идеальную комбинацию из значений с рейтингом 1"""
                                ideal_combination = {}
                                
                                for param_name, ratings in param_ratings.items():
                                    # Ищем значение с рейтингом 1
                                    value_with_rating_1 = None
                                    for value, rating in ratings.items():
                                        if rating == 1:
                                            value_with_rating_1 = value
                                            break
                                    
                                    if value_with_rating_1:
                                        ideal_combination[param_name] = value_with_rating_1
                                
                                return ideal_combination
                            
                            # Находим лучшие комбинации параметров (старый алгоритм)
                            def find_best_combinations(df, params, top_n=5):
                                """Находит лучшие комбинации параметров по эффективности"""
                                if len(params) < 2:
                                    return pd.DataFrame()
                                
                                param1, param2 = params[0], params[1]
                                
                                # Группируем по комбинациям параметров
                                grouped = df.groupby([param1, param2]).agg({
                                    "Выручка": ["sum", "mean"],
                                    "Заказы": ["sum", "mean"],
                                    "Артикул": "count"
                                }).round(2)
                                
                                grouped.columns = ["Общая выручка", "Средняя выручка", "Общие заказы", "Средние заказы", "Количество товаров"]
                                
                                # Рассчитываем рейтинг комбинации
                                if grouped["Общая выручка"].max() > 0:
                                    grouped["Рейтинг выручки"] = (grouped["Общая выручка"] / grouped["Общая выручка"].max() * 100).round(1)
                                else:
                                    grouped["Рейтинг выручки"] = 0
                                    
                                if grouped["Общие заказы"].max() > 0:
                                    grouped["Рейтинг заказов"] = (grouped["Общие заказы"] / grouped["Общие заказы"].max() * 100).round(1)
                                else:
                                    grouped["Рейтинг заказов"] = 0
                                
                                grouped["Общий рейтинг"] = ((grouped["Рейтинг выручки"] + grouped["Рейтинг заказов"]) / 2).round(1)
                                
                                # Добавляем название комбинации
                                grouped["Комбинация"] = grouped.index.map(lambda x: f"{x[0]} + {x[1]}" if isinstance(x, tuple) else str(x))
                                
                                return grouped.sort_values("Общий рейтинг", ascending=False).head(top_n)
                            
                            # Показываем лучшие комбинации
                            if len(available_params) >= 2:
                                if algorithm_choice == "🏆 По рейтингу параметров":
                                    # Создаем идеальную комбинацию
                                    ideal_combination = create_ideal_combination_from_ratings(param_ratings)
                                    
                                    if ideal_combination:
                                        # Создаем DataFrame с идеальной комбинацией
                                        combination_data = []
                                        param1, param2 = available_params[0], available_params[1]
                                        combo_name = " + ".join([ideal_combination[param] for param in [param1, param2]])
                                        
                                        # Находим фактические данные для этой комбинации (если есть)
                                        actual_data = analytics_df[
                                            (analytics_df[param1] == ideal_combination[param1]) & 
                                            (analytics_df[param2] == ideal_combination[param2])
                                        ]
                                        
                                        if not actual_data.empty:
                                            total_revenue = actual_data["Выручка"].sum()
                                            total_orders = actual_data["Заказы"].sum()
                                            count = len(actual_data)
                                        else:
                                            total_revenue = 0
                                            total_orders = 0
                                            count = 0
                                        
                                        combination_data.append({
                                            "Комбинация": combo_name,
                                            "Рейтинг_параметра_1": ideal_combination[param1],
                                            "Рейтинг_параметра_2": ideal_combination[param2],
                                            "Суммарный_рейтинг_параметров": 2,  # 1 + 1
                                            "Общая выручка": total_revenue,
                                            "Общие заказы": total_orders,
                                            "Количество товаров": count,
                                            "Статус": "✅ Идеальная комбинация" if count > 0 else "⚠️ Теоретическая комбинация"
                                        })
                                        
                                        best_combinations = pd.DataFrame(combination_data)
                                    else:
                                        st.warning("⚠️ Не удалось создать идеальную комбинацию. Проверьте рейтинги параметров.")
                                        best_combinations = pd.DataFrame()
                                else:
                                    # Используем старый алгоритм по эффективности
                                    best_combinations = find_best_combinations(analytics_df, available_params)
                                
                                if not best_combinations.empty:
                                    if algorithm_choice == "🏆 По рейтингу параметров":
                                        # Показываем идеальную комбинацию
                                        display_cols = ["Комбинация", "Рейтинг_параметра_1", "Рейтинг_параметра_2", "Суммарный_рейтинг_параметров", "Статус", "Общая выручка", "Общие заказы", "Количество товаров"]
                                        available_cols = [col for col in display_cols if col in best_combinations.columns]
                                        st.dataframe(
                                            best_combinations[available_cols], 
                                            use_container_width=True
                                        )
                                        st.caption("🏆 Идеальная комбинация из значений с рейтингом 1")
                                    else:
                                        # Показываем по эффективности
                                        st.dataframe(
                                            best_combinations[["Комбинация", "Общий рейтинг", "Рейтинг выручки", "Рейтинг заказов", "Общая выручка", "Общие заказы"]], 
                                            use_container_width=True
                                        )
                                        st.caption("📊 Комбинации ранжированы по эффективности (выручка + заказы)")
                                    
                                    # График только для алгоритма по эффективности
                                    if algorithm_choice != "🏆 По рейтингу параметров":
                                        st.write("**График лучших комбинаций:**")
                                        chart_data = best_combinations[["Комбинация", "Общий рейтинг"]].set_index("Комбинация")
                                        st.bar_chart(chart_data)
                                else:
                                    st.info("Недостаточно данных для анализа комбинаций")
                            else:
                                st.info("Нужно минимум 2 параметра для анализа комбинаций")
                    else:
                        if not available_params:
                            st.warning("⚠️ Нет доступных параметров. Создайте параметры на вкладке 'Параметры'.")
                        elif len(available_params) < 2:
                            st.warning(f"⚠️ Недостаточно параметров для анализа комбинаций. Доступно: {len(available_params)}, нужно: минимум 2.")
                            st.info("💡 Создайте еще параметры на вкладке 'Параметры', чтобы увидеть анализ комбинаций.")
                        
                        # Общие рекомендации
                        st.subheader("💡 Рекомендации")
                        
                        if param_ratings:
                            # Находим параметры с лучшими значениями
                            recommendations = []
                            
                            for param, rating_df in param_ratings.items():
                                if not rating_df.empty:
                                    best_value = rating_df.index[0]
                                    best_rating = rating_df.iloc[0]["Общий рейтинг"]
                                    recommendations.append(f"**{param}**: {best_value} (рейтинг: {best_rating})")
                            
                            if recommendations:
                                st.write("**Лучшие значения по параметрам:**")
                                for rec in recommendations:
                                    st.write(f"• {rec}")
                                
                                # Показываем идеальную комбинацию
                                if len(recommendations) >= 2 and algorithm_choice == "🏆 По рейтингу параметров":
                                    param1_best = recommendations[0].split(": ")[1].split(" (")[0]
                                    param2_best = recommendations[1].split(": ")[1].split(" (")[0]
                                    st.success(f"⭐ **Идеальная комбинация**: {param1_best} + {param2_best} (оба параметра с рейтингом 1)")
                                    
                                    # Проверяем, есть ли товары с такой комбинацией
                                    if not best_combinations.empty:
                                        ideal_combo = best_combinations.iloc[0]
                                        if ideal_combo['Количество товаров'] > 0:
                                            st.info("✅ В каталоге уже есть товары с такими параметрами")
                                        else:
                                            st.info("💡 **Рекомендация**: Создайте товары с такими параметрами для максимальной эффективности")
                    
                    # Оригинальная аналитика по параметрам
                    st.subheader("📊 Детальная аналитика по параметрам")
                    
                    # Группировка по параметрам
                    for param in st.session_state["schemas"].keys():
                        if param in analytics_df.columns:
                            st.subheader(f"📊 Аналитика по параметру: {param}")
                            
                            # Группировка
                            grouped = analytics_df.groupby(param).agg({
                                "Выручка": ["sum", "mean", "count"],
                                "Заказы": ["sum", "mean"],
                                "Цена (без СПП)": ["mean"],
                                "Цена (с СПП)": ["mean"]
                            }).round(2)
                            
                            # Переименование столбцов
                            grouped.columns = [
                                "Общая выручка", "Средняя выручка", "Количество товаров",
                                "Общие заказы", "Средние заказы",
                                "Средняя цена (без СПП)", "Средняя цена (с СПП)"
                            ]
                            
                            st.dataframe(grouped, use_container_width=True)
                            
                            # График
                            if "Выручка" in analytics_df.columns:
                                chart_data = analytics_df.groupby(param)["Выручка"].sum().reset_index()
                                st.bar_chart(chart_data.set_index(param))
                else:
                    st.info("📝 Нет данных для анализа. Назначьте параметры товарам на вкладке 'Параметры'.")
            else:
                st.info("📝 Нет назначенных параметров. Перейдите на вкладку 'Параметры' для создания и назначения параметров.")
    
    else:
        st.error("❌ Не удалось загрузить данные из файла")
else:
    st.info("📁 Загрузите файл с данными товаров в сайдбаре для начала работы")






