# -*- coding: utf-8 -*-
"""
Модуль для работы с отчетами по размерам (папка size).
"""
import os
import re
from typing import Optional

import pandas as pd

from utils.wb_utils import extract_sku_from_filename


def _detect_header_row(raw_df: pd.DataFrame) -> Optional[int]:
    for i in range(min(len(raw_df), 60)):
        row_values = raw_df.iloc[i].astype(str).str.strip().str.lower()
        has_size = any("размер" in v for v in row_values)
        has_orders = any(("заказ" in v) or ("кол-во" in v) or ("количество" in v) for v in row_values)
        if has_size and has_orders:
            return i
    return None


def _find_size_col(columns) -> Optional[str]:
    for c in columns:
        if "размер" in str(c).lower():
            return c
    return None


def _find_orders_col(columns) -> Optional[str]:
    for c in columns:
        cl = str(c).lower()
        if "заказ" in cl or "кол-во" in cl or "количество" in cl:
            return c
    return None


def _find_sku_col(columns) -> Optional[str]:
    for c in columns:
        if "артикул" in str(c).lower():
            return c
    return None


def normalize_size(val: str) -> Optional[str]:
    """
    Оставляем только буквенные размеры (XS, S, M, L, XL, XXL, XXXL, XXXXL).
    """
    if val is None:
        return None
    s = str(val).strip().upper()
    if not s or s == "NAN":
        return None
    # Пробуем извлечь буквенный размер после разделителя (например "50-52 | XL")
    for sep in ["|", "｜", "/", "\\"]:
        if sep in s:
            parts = [p.strip() for p in s.split(sep) if p.strip()]
            if parts:
                s = parts[-1]

    # Ищем буквенные размеры напрямую
    # Нормализуем форматы вида 2XL/3XL/4XL
    s = s.replace("1XL", "XL").replace("2XL", "XXL").replace("3XL", "XXXL").replace("4XL", "XXXXL")
    match = re.search(r"\b(ONE SIZE|XXXXL|XXXL|XXL|XL|XS|S|M|L|OS)\b", s)
    if match:
        size = match.group(1)
        if size == "ONE SIZE":
            return "OS"
        return size

    # Если остались только цифры/диапазоны — игнорируем
    return None


def _to_number(val) -> float:
    if pd.isna(val):
        return 0.0
    if isinstance(val, str):
        m = re.search(r"[\d.,]+", val.replace(" ", ""))
        if not m:
            return 0.0
        return float(m.group(0).replace(",", "."))
    try:
        return float(val)
    except Exception:
        return 0.0


def _read_size_report(filepath: str) -> Optional[pd.DataFrame]:
    try:
        if filepath.endswith(".csv"):
            df = pd.read_csv(filepath)
        else:
            df = pd.read_excel(filepath)
    except Exception:
        return None

    size_col = _find_size_col(df.columns)
    orders_col = _find_orders_col(df.columns)
    if size_col is None or orders_col is None:
        try:
            if filepath.endswith(".csv"):
                raw_df = pd.read_csv(filepath, header=None)
            else:
                raw_df = pd.read_excel(filepath, header=None)
            header_idx = _detect_header_row(raw_df)
            if header_idx is not None:
                if filepath.endswith(".csv"):
                    df = pd.read_csv(filepath, header=header_idx)
                else:
                    df = pd.read_excel(filepath, header=header_idx)
        except Exception:
            return None

    size_col = _find_size_col(df.columns)
    orders_col = _find_orders_col(df.columns)
    if size_col is None or orders_col is None:
        return None

    sku_col = _find_sku_col(df.columns)

    out = pd.DataFrame()
    out["Размер"] = df[size_col].apply(normalize_size)
    out["Заказы"] = df[orders_col].apply(_to_number)
    if sku_col:
        out["Артикул"] = df[sku_col].astype(str).str.replace(".0", "")
    # Оставляем только буквенные размеры
    out = out[out["Размер"].notna()]
    return out


def find_and_load_size_reports(skus: tuple, size_folder: str = "size") -> tuple[dict, dict]:
    """
    Возвращает отчеты по размерам и список причин отсутствия.
    """
    reports = {}
    missing = {}

    if not os.path.exists(size_folder):
        for sku in skus:
            missing[str(sku).replace(".0", "")] = "Папка size не найдена"
        return reports, missing

    files = os.listdir(size_folder)
    skus_str = [str(sku).replace(".0", "") for sku in skus]

    for sku in skus_str:
        matched = None
        for filename in files:
            file_sku = extract_sku_from_filename(filename)
            if file_sku == sku:
                matched = filename
                break
        if not matched:
            missing[sku] = "Файл по артикулу не найден"
            continue

        filepath = os.path.join(size_folder, matched)
        df = _read_size_report(filepath)
        if df is None or df.empty:
            missing[sku] = f"Не удалось прочитать файл: {matched}"
            continue

        if "Артикул" in df.columns:
            df = df[df["Артикул"].astype(str) == sku]

        if df.empty:
            missing[sku] = f"Нет строк по артикулу в файле: {matched}"
            continue

        reports[sku] = {
            "data": df,
            "filename": matched,
            "filepath": filepath
        }

    return reports, missing
