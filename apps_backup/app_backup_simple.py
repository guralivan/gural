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

st.set_page_config(page_title="Дашборд товаров — скриншоты", layout="wide")

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
        return f"{int(round(xf)):,}".replace(",", " ")
    return f"{xf:,.{decimals}f}".replace(",", " ").replace(".", ",")
def fmt_rub(x, decimals=0):
    s = format_thousands(x, decimals=decimals)
    return (s + " ₽") if s != "" else ""
def fmt_units(x, unit="шт."):
    s = format_thousands(x, decimals=0)
    return (s + f" {unit}") if s != "" else ""
def fmt_date(d):
    if d is None or (isinstance(d, float) and np.isnan(d)):
        return ""
    try:
        return pd.to_datetime(d).strftime("%d/%m/%y")
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
    k1, k2, k3, k4, k5 = st.columns(5)
    k1.metric("Выручка (в выборке)", fmt_rub(total_rev))
    k2.metric("Заказы (в выборке)", fmt_units(total_orders, "шт."))
    k3.metric("Средний чек", fmt_rub(avg_check))
    k4.metric("Упущенная выручка", fmt_rub(lost_rev))
    k5.metric("Выручка / Кол-во товаров", fmt_rub(rev_per_sku))

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

if uploaded is None:
    st.info("Загрузите файл с данными.")
else:
    df, raw, meta = read_table(uploaded.read(), uploaded.name)
    if df is None or df.empty:
        st.error("Не удалось прочитать таблицу.")
    else:
        st.title("📊 Дашборд (упрощённый пример)")
        cols = st.columns([1,1,1,1,1,1])
        search = cols[0].text_input("Поиск")
        spp = cols[2].number_input("СПП, %", 0, 100, 25, 1)
        buyout_pct = cols[3].number_input("Процент выкупа, %", 1, 100, 25, 1)
        show_images = cols[4].checkbox("Показывать «Изображение»", value=False)
        html_mode = cols[5].checkbox("HTML-таблица", value=False)
        fdf = df.copy()
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
        kpi_row(fdf)
        st.divider()
        # Миниатюры кэш
        url_cache = get_url_cache()
        if show_images and "Артикул" in fdf.columns:
            imgs = []
            for a in fdf["Артикул"].astype(str):
                k = a.replace(".0","")
                url = url_cache.get(k, "")
                if not url and sc_key:
                    url = screenshot_for_article(k, {"key": sc_key,"w": sc_w,"h": sc_h,"fmt": sc_fmt,"profile": sc_profile,"base": sc_base,"wb_host": sc_host})
                    if url:
                        url_cache[k] = url
                        save_url_cache(url_cache)
                path = get_cached_image_path(k) or (ensure_image_cached(k, url, sc_fmt) if url else "")
                imgs.append(load_image_bytes(path, 140) if path else b"")
            fdf.insert(1, "Изображение", imgs)

        money_cols = ["Выручка","Прибыль","Упущенная выручка","Цена (до СПП)","Цена (с СПП)"]
        for col in money_cols:
            if col in fdf.columns:
                fdf[col] = fdf[col].apply(fmt_rub)
        if "Заказы" in fdf.columns:
            fdf["Заказы"] = fdf["Заказы"].apply(lambda x: fmt_units(x, "шт."))
        if "Выкупы" in fdf.columns:
            fdf["Выкупы"] = fdf["Выкупы"].apply(lambda x: fmt_units(x, "шт."))

        from streamlit import column_config as cc
        col_cfg = {}
        if "Изображение" in fdf.columns:
            col_cfg["Изображение"] = cc.ImageColumn(width=140)
        st.dataframe(fdf, use_container_width=True, hide_index=True, column_config=col_cfg)

# end of file
