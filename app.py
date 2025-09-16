# -*- coding: utf-8 -*-
import os
import json
import base64
from io import BytesIO
import urllib.parse as _urlparse
import locale

import pandas as pd
import numpy as np
import streamlit as st
import requests

# Настройка локали для правильного отображения чисел с пробелами
try:
    locale.setlocale(locale.LC_ALL, 'ru_RU.UTF-8')
except:
    try:
        locale.setlocale(locale.LC_ALL, 'Russian_Russia.1251')
    except:
        pass

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
    p = get_cached_image_path(nm)
    if not p:
        return ""
    try:
        data = load_image_bytes(p, max_w=max_w)
        if not data:
            return ""
        b64 = base64.b64encode(data).decode("ascii")
        return f"data:image/jpeg;base64,{b64}"
    except Exception:
        return ""

def build_wb_product_url(nm, host="https://global.wildberries.ru"):
    return f"{host.rstrip('/')}/catalog/{str(nm).replace('.0','')}/detail.aspx"
def build_screenshot_url(page_url: str, key: str,
                         w: int = 400, h: int = 600,
                         fmt: str = "JPEG", profile: str = "D4",
                         base: str = "https://api.s-shot.ru"):
    q = _urlparse.quote(page_url, safe="")
    return f"{base.rstrip('/')}/{int(w)}x{int(h)}/{fmt}/{key}/{profile}/?{q}"
def screenshot_for_article(nm, conf):
    if not conf.get("key"):
        return ""
    page = build_wb_product_url(nm, conf.get("wb_host", "https://global.wildberries.ru"))
    return build_screenshot_url(
        page, conf.get("key", ""), conf.get("w", 400), conf.get("h", 600),
        conf.get("fmt", "JPEG"), conf.get("profile", "D4"), conf.get("base", "https://api.s-shot.ru")
    )

@st.cache_data(show_spinner=False)
def read_table(file_bytes: bytes, filename: str):
    try:
        if filename.lower().endswith((".xlsx", ".xls")):
            df_raw = pd.read_excel(BytesIO(file_bytes), sheet_name=0, header=None)
        else:
            df_raw = pd.read_csv(BytesIO(file_bytes), header=None, sep=None, engine="python")
    except Exception as e:
        st.error(f"Ошибка чтения файла: {e}")
        return None, None, {}
    key_candidates = ["Артикул", "Выручка", "Заказы", "Название"]
    header_row = None
    for i in range(min(30, len(df_raw))):
        vals = df_raw.iloc[i].astype(str).str.strip().tolist()
        if any(k in vals for k in key_candidates):
            header_row = i
            break
    if header_row is None:
        header_row = 0
    if filename.lower().endswith((".xlsx", ".xls")):
        df = pd.read_excel(BytesIO(file_bytes), sheet_name=0, header=header_row)
    else:
        df = pd.read_csv(BytesIO(file_bytes), header=header_row, sep=None, engine="python")
    df = df.loc[:, ~df.columns.astype(str).str.startswith("Unnamed")]
    df = df.loc[:, df.columns.notna()]
    df.columns = [str(c).strip() for c in df.columns]
    rename_map = {
        "Средняя цена без СПП": "Средняя цена",
        "Средняя цена без СПП, ₽": "Средняя цена",
        "Цена": "Средняя цена",
        "Выручка, ₽": "Выручка",
        "Orders": "Заказы",
        "Brand": "Бренд",
        "Supplier": "Поставщик",
        "Subject": "Предмет",
        "Creation date": "Дата создания",
        "Дата": "Дата создания",
        "Позиция": "Позиция в выдаче",
        "CPM": "Стоимость за 1000 показов",
        "Упущенная выручка, ₽": "Упущенная выручка",
    }
    df = df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns})
    num_cols = ["Выручка","Заказы","Средняя цена","Упущенная выручка",
                "Позиция в выдаче","Стоимость за 1000 показов","Буст на позицию","Буст с позиции"]
    for c in num_cols:
        if c in df.columns:
            df[c] = pd.to_numeric(
                df[c].astype(str).str.replace(r"[^\d,.-]", "", regex=True).str.replace(",", ".", regex=False),
                errors="coerce",
            )
    if "Дата создания" in df.columns:
        df["Дата создания"] = pd.to_datetime(df["Дата создания"], errors="coerce")
    if "Тип рекламы" in df.columns:
        df["Тип рекламы"] = df["Тип рекламы"].replace({"b": "Поиск", "c": "Автомат"})
    if ("Буст на позицию" in df.columns) and ("Буст с позиции" in df.columns) and ("Дельта" not in df.columns):
        df["Дельта"] = df["Буст с позиции"] - df["Буст на позицию"]
    return df, df_raw, {"header_row": header_row, "columns": list(df.columns)}

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
def fmt_rub(x, decimals=0):
    s = format_thousands(x, decimals=decimals)
    return (s + " ₽") if s != "" else ""
def fmt_units(x, unit="шт."):
    s = format_thousands(x, decimals=0)
    return (s + f" {unit}") if s != "" else ""

def fmt_rub_kpi(x, decimals=0):
    s = format_thousands_with_spaces(x, decimals=decimals)
    return (s + " ₽") if s != "" else ""
def fmt_units_kpi(x, unit="шт."):
    s = format_thousands_with_spaces(x, decimals=0)
    return (s + f" {unit}") if s != "" else ""
def fmt_date(d):
    if d is None or (isinstance(d, float) and np.isnan(d)):
        return ""
    try:
        dt = pd.to_datetime(d)
        # Русские названия месяцев
        months = {
            1: "января", 2: "февраля", 3: "марта", 4: "апреля", 5: "мая", 6: "июня",
            7: "июля", 8: "августа", 9: "сентября", 10: "октября", 11: "ноября", 12: "декабря"
        }
        return f"{dt.day} {months[dt.month]} {dt.year}"
    except Exception:
        return str(d) if d is not None else ""
def parse_thousands_input(s, default_val):
    if s is None or str(s).strip() == "":
        return default_val
    try:
        cleaned = (str(s).replace("\\xa0"," ").replace("\\u00a0"," ").replace(" ", " "))
        cleaned = cleaned.replace(" ", "").replace(",", "").strip()
        return int(float(cleaned))
    except Exception:
        return default_val
def sort_df(df, col, asc):
    if col not in df.columns:
        return df
    if pd.api.types.is_numeric_dtype(df[col]):
        return df.sort_values(by=col, ascending=asc, na_position="last", kind="mergesort")
    return df.sort_values(by=col, ascending=asc, na_position="last", kind="mergesort",
                          key=lambda s: s.astype(str).str.lower())

def get_param_schemas():
    if "param_schemas" not in st.session_state:
        st.session_state["param_schemas"] = {}
    return st.session_state["param_schemas"]
def get_param_values():
    if "param_values" not in st.session_state:
        st.session_state["param_values"] = {}
    return st.session_state["param_values"]

def kpi_row(df):
    total_rev = float(df["Выручка"].sum()) if "Выручка" in df.columns else float('nan')
    total_orders = df["Заказы"].sum() if "Заказы" in df.columns else np.nan
    avg_check = (df["Выручка"].sum() / df["Заказы"].sum()) if ("Выручка" in df.columns and "Заказы" in df.columns and df["Заказы"].sum() > 0) else np.nan
    lost_rev = df["Упущенная выручка"].sum() if "Упущенная выручка" in df.columns else np.nan
    sku_count = (df["Артикул"].nunique() if "Артикул" in df.columns else len(df)) if len(df) > 0 else 0
    rev_per_sku = (total_rev / sku_count) if (isinstance(total_rev, (int,float,np.floating)) and not pd.isna(total_rev) and sku_count > 0) else np.nan
    k1, k2, k3, k4, k5, k6 = st.columns(6)
    k1.metric("Выручка (в выборке)", fmt_rub_kpi(total_rev))
    k2.metric("Заказы (в выборке)", fmt_units_kpi(total_orders, "шт."))
    k3.metric("Средний чек", fmt_rub_kpi(avg_check))
    k4.metric("Упущенная выручка", fmt_rub_kpi(lost_rev))
    k5.metric("Выручка / Кол-во товаров", fmt_rub_kpi(rev_per_sku))
    k6.metric("Количество артикулов", fmt_units_kpi(sku_count, "шт."))

# Загружаем сохраненные параметры
load_param_values_from_file()

# Инициализация session_state
if "schemas" not in st.session_state:
    st.session_state["schemas"] = {}

# --- UI (урезанный пример, ключевые места с прибыль и миниатюрами) ---
with st.sidebar.expander("Загрузка файла", expanded=True):
    uploaded = st.file_uploader("Excel/CSV с товарами", type=["xlsx","xls","csv"])
with st.sidebar.expander("Скриншоты страниц (s-shot.ru)", expanded=True):
    sc_key = st.text_input("Ключ s-shot", value="")
    sc_base = st.text_input("Базовый URL", value="https://api.s-shot.ru")
    sc_host = st.text_input("Домен карточки WB", value="https://global.wildberries.ru")
    sc_w = st.number_input("Ширина", 100, 2000, 400, 10)
    sc_h = st.number_input("Высота", 100, 2000, 600, 10)
    sc_fmt = st.selectbox("Формат", ["JPEG","PNG"], 0)
    sc_profile = st.text_input("Профиль", value="D4")
    
    # Информация о кеше
    url_cache = get_url_cache()
    cached_count = len(url_cache)
    st.info(f"📦 В кеше: {cached_count} изображений")
    
    # Кнопки управления кешем
    col_cache1, col_cache2 = st.columns(2)
    if col_cache1.button("🗑️ Очистить кеш"):
        st.session_state["img_url_cache"] = {}
        save_url_cache({})
        st.rerun()
    
    if col_cache2.button("💾 Сохранить параметры"):
        if save_param_values_to_file():
            st.success("✅ Параметры сохранены!")
        else:
            st.error("❌ Ошибка сохранения параметров")

if uploaded is None:
    st.info("Загрузите файл с данными.")
else:
    df, raw, meta = read_table(uploaded.read(), uploaded.name)
    if df is None or df.empty:
        st.error("Не удалось прочитать таблицу.")
    else:
        st.title("📊 Дашборд WB")
        
        # Основные фильтры
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
        col_img1, col_img2, col_img3 = st.columns(3)
        show_images = col_img1.checkbox("🖼️ Показывать изображения", value=False)
        if show_images:
            img_size = col_img2.number_input("📏 Размер миниатюр (px)", min_value=50, max_value=300, value=200, step=10)
            if col_img3.button("🔄 Обновить кеш изображений", type="secondary"):
                # Очищаем кеш URL
                st.session_state["img_url_cache"] = {}
                save_url_cache({})
                st.rerun()
            if not sc_key:
                st.info("💡 Для отображения изображений товаров введите API ключ s-shot.ru в боковой панели")
        else:
            img_size = 200
        
        # Фильтр сортировки
        col_sort1, col_sort2 = st.columns(2)
        
        # Определяем доступные колонки для сортировки
        sortable_columns = []
        if "Выручка" in df.columns:
            sortable_columns.append("Выручка")
        if "Средняя цена" in df.columns:
            sortable_columns.append("Средняя цена")
        if "Заказы" in df.columns:
            sortable_columns.append("Заказы")
        if "Дата создания" in df.columns:
            sortable_columns.append("Дата создания")
        if "Прибыль" in df.columns:
            sortable_columns.append("Прибыль")
        if "Упущенная выручка" in df.columns:
            sortable_columns.append("Упущенная выручка")
        if "Позиция в выдаче" in df.columns:
            sortable_columns.append("Позиция в выдаче")
        
        # Добавляем опцию "Без сортировки"
        sortable_columns.insert(0, "Без сортировки")
        
        # Находим индекс "Выручка" для установки по умолчанию
        default_index = 0  # По умолчанию "Без сортировки"
        if "Выручка" in sortable_columns:
            default_index = sortable_columns.index("Выручка")
        
        sort_column = col_sort1.selectbox("📊 Сортировка по", sortable_columns, index=default_index)
        sort_ascending = col_sort2.selectbox("🔽 Направление", ["По убыванию", "По возрастанию"], index=0) == "По возрастанию"
        
        st.divider()
        
        # Выручка
        col7, col8 = st.columns(2)
        
        if "Выручка" in df.columns:
            revenue_min = col7.number_input("Выручка от", min_value=0, value=0, step=1000)
            revenue_max = col8.number_input("Выручка до", min_value=0, value=int(df["Выручка"].max()) if not df["Выручка"].isna().all() else 1000000, step=1000)
        else:
            revenue_min = 0
            revenue_max = 1000000
        
        # Цена
        col9, col10 = st.columns(2)
        
        if "Средняя цена" in df.columns:
            price_min = col9.number_input("Цена (до СПП) от", min_value=0, value=0, step=100)
            price_max = col10.number_input("Цена (до СПП) до", min_value=0, value=int(df["Средняя цена"].max()) if not df["Средняя цена"].isna().all() else 10000, step=100)
        else:
            price_min = 0
            price_max = 10000
        
        # Дата создания
        
        if "Дата создания" in df.columns:
            # Получаем диапазон дат
            date_range = df["Дата создания"].dropna()
            if not date_range.empty:
                min_date = date_range.min().date()
                max_date = date_range.max().date()
                
                # Создаем ползунок для выбора диапазона дат
                date_range_days = (max_date - min_date).days
                if date_range_days > 0:
                    date_slider = st.slider(
                        "Выберите диапазон дат",
                        min_value=min_date,
                        max_value=max_date,
                        value=(min_date, max_date)
                    )
                    date_min, date_max = date_slider
                    
                    # Показываем выбранный диапазон в русском формате
                    months = {
                        1: "января", 2: "февраля", 3: "марта", 4: "апреля", 5: "мая", 6: "июня",
                        7: "июля", 8: "августа", 9: "сентября", 10: "октября", 11: "ноября", 12: "декабря"
                    }
                    date_min_str = f"{date_min.day} {months[date_min.month]} {date_min.year}"
                    date_max_str = f"{date_max.day} {months[date_max.month]} {date_max.year}"
                    st.info(f"📅 Выбранный период: {date_min_str} - {date_max_str}")
                else:
                    date_min = min_date
                    date_max = max_date
            else:
                date_min = pd.Timestamp.now().date()
                date_max = pd.Timestamp.now().date()
        else:
            date_min = pd.Timestamp.now().date()
            date_max = pd.Timestamp.now().date()
        fdf = df.copy()
        
        # Применяем фильтры
        if search:
            mask = fdf.apply(lambda x: x.astype(str).str.contains(search, case=False, na=False)).any(axis=1)
            fdf = fdf[mask]
        
        if selected_subjects and "Предмет" in fdf.columns:
            fdf = fdf[fdf["Предмет"].isin(selected_subjects)]
        
        # Фильтр по выручке
        if "Выручка" in fdf.columns:
            fdf = fdf[(fdf["Выручка"] >= revenue_min) & (fdf["Выручка"] <= revenue_max)]
        
        # Фильтр по цене
        if "Средняя цена" in fdf.columns:
            fdf = fdf[(fdf["Средняя цена"] >= price_min) & (fdf["Средняя цена"] <= price_max)]
        
        # Фильтр по дате создания
        if "Дата создания" in fdf.columns:
            fdf = fdf[(fdf["Дата создания"].dt.date >= date_min) & (fdf["Дата создания"].dt.date <= date_max)]
        
        if "Средняя цена" in fdf.columns:
            fdf["Цена (с СПП)"] = fdf["Средняя цена"] * (1 - float(spp)/100.0)
        buyout_k = float(buyout_pct)/100.0 if buyout_pct else 0.0
        if "Заказы" in fdf.columns:
            fdf["Выкупы"] = pd.to_numeric(fdf["Заказы"], errors="coerce") * buyout_k
        else:
            fdf["Выкупы"] = np.nan
        # === FIX: Прибыль = Выручка * (процент выкупа) ===
        if "Выручка" in fdf.columns and buyout_k > 0:
            fdf["Прибыль"] = pd.to_numeric(fdf["Выручка"], errors="coerce") * buyout_k
        else:
            fdf["Прибыль"] = np.nan
        
        # Применяем сортировку
        if sort_column and sort_column != "Без сортировки" and sort_column in fdf.columns:
            fdf = sort_df(fdf, sort_column, sort_ascending)
        
            kpi_row(fdf)
            st.divider()

        # Миниатюры кэш
        url_cache = get_url_cache()
        
        # Создаем копию для отображения
        display_df = fdf.copy()
        
        # Добавляем изображения
        if show_images and "Артикул" in display_df.columns:
            imgs = []
            loaded_count = 0
            total_items = len(display_df)
            
            # Создаем прогресс-бар если много товаров
            if total_items > 10:
                progress_bar = st.progress(0)
                status_text = st.empty()
                
            for i, a in enumerate(display_df["Артикул"].astype(str)):
                k = a.replace(".0","")
                url = url_cache.get(k, "")
                if not url and sc_key:
                    url = screenshot_for_article(k, {"key": sc_key,"w": sc_w,"h": sc_h,"fmt": sc_fmt,"profile": sc_profile,"base": sc_base,"wb_host": sc_host})
                    if url:
                        url_cache[k] = url
                        save_url_cache(url_cache)
                
                # Проверяем кеш изображений
                cached_path = get_cached_image_path(k)
                if cached_path and os.path.exists(cached_path):
                    path = cached_path
                elif url:
                    path = ensure_image_cached(k, url, sc_fmt)
                else:
                    path = ""
                
                if path and os.path.exists(path):
                    # Создаем data URI для Streamlit
                    img_bytes = load_image_bytes(path, img_size)
                    if img_bytes:
                        b64_data = base64.b64encode(img_bytes).decode()
                        data_uri = f"data:image/jpeg;base64,{b64_data}"
                        imgs.append(data_uri)
                        loaded_count += 1
                    else:
                        imgs.append("")
                else:
                    imgs.append("")
                
                # Обновляем прогресс
                if total_items > 10:
                    progress = (i + 1) / total_items
                    progress_bar.progress(progress)
                    status_text.text(f"Загружаем изображения: {i + 1}/{total_items}")
            
            # Очищаем прогресс-бар
            if total_items > 10:
                progress_bar.empty()
                status_text.empty()
                
            display_df.insert(1, "Изображение", imgs)
            
            # Показываем статистику загрузки
            st.success(f"📊 Загружено изображений: {loaded_count} из {len(display_df)} товаров")
        
        # Добавляем отдельный столбец со ссылками на артикулы
        if "Артикул" in display_df.columns:
            # Создаем специальный формат для отображения "Открыть" в Streamlit
            display_df["Ссылка"] = "Открыть"
            # Но фактические ссылки будут настроены через column_config
        
        # Форматирование даты для Streamlit таблицы
        if "Дата создания" in display_df.columns:
            display_df["Дата создания"] = display_df["Дата создания"].apply(fmt_date)
        
        # Оставляем числовые данные как есть для корректной сортировки в Streamlit таблице
        
        # Изменение порядка столбцов
        desired_order = [
            "Артикул", "Ссылка", "Дата создания", "Выручка", "Заказы", "Выкупы", 
            "Средняя цена", "Цена (с СПП)", "Упущенная выручка", "Прибыль",
            "Предмет", "Позиция в выдаче", "Стоимость за 1000 показов", 
            "Тип рекламы", "Буст на позицию", "Буст с позиции", "Дельта",
            "Название", "Поставщик", "Бренд"
        ]
        
        # Добавляем изображения в начало если нужно
        if show_images and "Изображение" in display_df.columns:
            desired_order.insert(1, "Изображение")
        
        # Переупорядочиваем столбцы
        existing_cols = [col for col in desired_order if col in display_df.columns]
        other_cols = [col for col in display_df.columns if col not in desired_order]
        final_order = existing_cols + other_cols
        
        display_df = display_df[final_order]

        from streamlit import column_config as cc
        
        # Настройка конфигурации столбцов для лучшего отображения
        col_cfg = {}
        
        # Конфигурация для изображений
        if "Изображение" in display_df.columns:
            col_cfg["Изображение"] = cc.ImageColumn("Изображение", width=img_size + 20)
        
        # Конфигурация для артикула (обычный текст)
        if "Артикул" in display_df.columns:
            col_cfg["Артикул"] = cc.TextColumn("Артикул", width=120)
        
        # Конфигурация для ссылки на товар с динамическими URL
        if "Ссылка" in display_df.columns and "Артикул" in display_df.columns:
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
            col_cfg["Дата создания"] = cc.TextColumn("Дата создания", width=150)
        
        # Отображаем таблицу с возможностью сортировки
        st.dataframe(
            display_df, 
            use_container_width=True, 
            hide_index=True, 
            column_config=col_cfg,
            column_order=None  # Позволяет пользователю переупорядочивать столбцы
        )

# end of file
