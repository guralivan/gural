# -*- coding: utf-8 -*-
"""
Модуль для форматирования чисел и дат
"""
import numpy as np
import pandas as pd


def format_thousands(x, decimals=0):
    """Форматирует число"""
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
    """Форматирует число с пробелами как разделителями тысяч"""
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
    """Форматирует число как рубли"""
    s = format_thousands(x, decimals=decimals)
    return (s + " ₽") if s != "" else ""


def fmt_units(x, unit="шт."):
    """Форматирует число с единицей измерения"""
    s = format_thousands(x, decimals=0)
    return (s + f" {unit}") if s != "" else ""


def fmt_rub_kpi(x, decimals=0):
    """Форматирует число как рубли для KPI (с пробелами)"""
    s = format_thousands_with_spaces(x, decimals=decimals)
    return (s + " ₽") if s != "" else ""


def fmt_units_kpi(x, unit="шт."):
    """Форматирует число для KPI (с пробелами)"""
    s = format_thousands_with_spaces(x, decimals=0)
    return (s + f" {unit}") if s != "" else ""


def fmt_date(d):
    """Форматирует дату на русском"""
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
    """Парсит строку с разделителями тысяч в число"""
    if s is None or str(s).strip() == "":
        return default_val
    try:
        cleaned = (str(s).replace("\\xa0"," ").replace("\\u00a0"," ").replace(" ", " "))
        cleaned = cleaned.replace(" ", "").replace(",", "").strip()
        return int(float(cleaned))
    except Exception:
        return default_val


def sort_df(df, col, asc):
    """Сортирует DataFrame по колонке"""
    if col not in df.columns:
        return df
    if pd.api.types.is_numeric_dtype(df[col]):
        return df.sort_values(by=col, ascending=asc, na_position="last", kind="mergesort")
    return df.sort_values(by=col, ascending=asc, na_position="last", kind="mergesort",
                          key=lambda s: s.astype(str).str.lower())



























