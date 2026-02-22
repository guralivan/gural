# -*- coding: utf-8 -*-
"""
Модуль для работы с отчетами отзывов (папка Otziv).
"""
import os
import re
from typing import Optional

import pandas as pd

from utils.wb_utils import extract_sku_from_filename


def _detect_header_row(raw_df: pd.DataFrame) -> Optional[int]:
    keywords = ["дата", "артикул", "оценка", "комментарий", "достоинства", "недостатки"]
    for i in range(min(len(raw_df), 60)):
        row_values = raw_df.iloc[i].astype(str).str.strip().str.lower()
        hits = 0
        for val in row_values:
            if any(kw in val for kw in keywords):
                hits += 1
        if hits >= 3:
            return i
    return None


def _find_col(columns, key: str) -> Optional[str]:
    for c in columns:
        if key in str(c).lower():
            return c
    return None


def _read_otziv_report(filepath: str) -> Optional[pd.DataFrame]:
    try:
        if filepath.endswith(".csv"):
            df = pd.read_csv(filepath)
        else:
            df = pd.read_excel(filepath)
    except Exception:
        return None

    cols = df.columns.astype(str).str.strip()
    df.columns = cols

    if _find_col(cols, "оценк") is None or _find_col(cols, "артикул") is None:
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
                df.columns = df.columns.astype(str).str.strip()
        except Exception:
            return None

    return df


def find_and_load_otziv_reports(skus: tuple, otziv_folder: str = "Otziv") -> tuple[dict, dict]:
    """
    Возвращает отчеты отзывов и причины отсутствия.
    """
    reports = {}
    missing = {}

    if not os.path.exists(otziv_folder):
        for sku in skus:
            missing[str(sku).replace(".0", "")] = "Папка Otziv не найдена"
        return reports, missing

    files = os.listdir(otziv_folder)
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

        filepath = os.path.join(otziv_folder, matched)
        df = _read_otziv_report(filepath)
        if df is None or df.empty:
            missing[sku] = f"Не удалось прочитать файл: {matched}"
            continue

        reports[sku] = {
            "data": df,
            "filename": matched,
            "filepath": filepath
        }

    return reports, missing
