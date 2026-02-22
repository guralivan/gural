# -*- coding: utf-8 -*-
"""
Модуль для работы с отчётами из папки Tovar
"""
import os
import re
from typing import Optional, Union

import pandas as pd
from utils.wb_utils import extract_sku_from_filename

_LAST_REPORT_LOAD_ERROR: Optional[str] = None


def _set_last_report_load_error(error: Optional[Union[Exception, str]]) -> None:
    global _LAST_REPORT_LOAD_ERROR
    if error is None:
        _LAST_REPORT_LOAD_ERROR = None
    else:
        if isinstance(error, Exception):
            msg = str(error).strip()
            if msg:
                _LAST_REPORT_LOAD_ERROR = f"{type(error).__name__}: {msg}"
            else:
                _LAST_REPORT_LOAD_ERROR = type(error).__name__
        else:
            _LAST_REPORT_LOAD_ERROR = str(error)


def get_last_report_load_error() -> Optional[str]:
    return _LAST_REPORT_LOAD_ERROR


def load_report_from_tovar_folder(filepath: str) -> pd.DataFrame:
    """
    Загружает и обрабатывает отчет из папки Tovar.
    """
    try:
        _set_last_report_load_error(None)
        # Определяем формат файла
        if filepath.endswith('.csv'):
            # Пробуем разные разделители и кодировки
            df = None
            for sep in [';', ',', '\t']:
                for encoding in ['utf-8', 'utf-8-sig', 'cp1251', 'windows-1251']:
                    try:
                        df = pd.read_csv(filepath, sep=sep, encoding=encoding)
                        if len(df.columns) > 1:  # Успешно распарсили
                            break
                    except:
                        continue
                if df is not None and len(df.columns) > 1:
                    break
            
            if df is None:
                # Последняя попытка без указания разделителя
                try:
                    df = pd.read_csv(filepath, encoding='utf-8')
                except:
                    try:
                        df = pd.read_csv(filepath, encoding='cp1251')
                    except:
                        _set_last_report_load_error("Не удалось прочитать CSV файл")
                        return None
        else:
            df = None
            last_error = None
            for engine in [None, "openpyxl", "calamine", "pyxlsb"]:
                try:
                    if engine is None:
                        df = pd.read_excel(filepath)
                    else:
                        df = pd.read_excel(filepath, engine=engine)
                    break
                except Exception as e:
                    last_error = e
                    df = None
                    continue
            if df is None:
                _set_last_report_load_error(last_error or "Не удалось прочитать Excel файл")
                # Пробуем открыть как CSV (на случай неверного расширения)
                try:
                    df = pd.read_csv(filepath, sep=';', encoding='utf-8')
                except Exception:
                    return None
        
        def detect_header_row(raw_df: pd.DataFrame) -> Optional[int]:
            keywords = ['дата', 'артикул', 'заказ', 'продаж', 'выручк', 'средн']
            for i in range(min(len(raw_df), 60)):
                row_values = raw_df.iloc[i].astype(str).str.strip().str.lower()
                if not any(('дата' in val or val == 'date') for val in row_values):
                    continue
                hits = 0
                for val in row_values:
                    for kw in keywords:
                        if kw in val:
                            hits += 1
                            break
                if hits >= 2:
                    return i
            return None

        def set_header_from_row(raw_df: pd.DataFrame, header_idx: int) -> pd.DataFrame:
            data_df = raw_df.iloc[header_idx + 1:].copy()
            data_df.columns = raw_df.iloc[header_idx].astype(str).str.strip()
            return data_df

        def find_date_col(columns) -> Optional[str]:
            # Сначала ищем точное совпадение "Дата"
            for col in columns:
                col_lower = str(col).strip().lower()
                if col_lower == 'дата' or col_lower == 'date':
                    return col
            # Затем ищем любые колонки с датой
            for col in columns:
                col_lower = str(col).lower()
                if 'дата' in col_lower or 'date' in col_lower:
                    return col
            return None

        # Нормализуем названия колонок
        df.columns = df.columns.astype(str).str.strip()
        
        # Ищем колонку с датой
        date_col = find_date_col(df.columns)
        
        if date_col is None:
            # Пробуем найти строку заголовков в середине файла
            try:
                if filepath.endswith('.csv'):
                    raw_df = pd.read_csv(filepath, header=None, encoding='utf-8')
                else:
                    raw_df = pd.read_excel(filepath, header=None)
                header_idx = detect_header_row(raw_df)
                if header_idx is not None:
                    # Переоткрываем файл с найденным заголовком (более надежно)
                    if filepath.endswith('.csv'):
                        df = pd.read_csv(filepath, header=header_idx, encoding='utf-8')
                    else:
                        df = pd.read_excel(filepath, header=header_idx)
                    df.columns = df.columns.astype(str).str.strip()
                    date_col = find_date_col(df.columns)
            except Exception:
                pass
        
        if date_col is None:
            col_list = [str(c) for c in list(df.columns)[:12]]
            _set_last_report_load_error(
                f"Не найдена колонка с датой. Колонки: {', '.join(col_list)}"
            )
            return None
        
        # Преобразуем дату, если получилось слишком много NaT — пробуем альтернативный заголовок
        df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
        if df[date_col].notna().sum() == 0:
            try:
                if filepath.endswith('.csv'):
                    raw_df = pd.read_csv(filepath, header=None, encoding='utf-8')
                else:
                    raw_df = pd.read_excel(filepath, header=None)
                header_idx = detect_header_row(raw_df)
                if header_idx is not None:
                    if filepath.endswith('.csv'):
                        df = pd.read_csv(filepath, header=header_idx, encoding='utf-8')
                    else:
                        df = pd.read_excel(filepath, header=header_idx)
                    df.columns = df.columns.astype(str).str.strip()
                    date_col = find_date_col(df.columns)
                    if date_col is None:
                        col_list = [str(c) for c in list(df.columns)[:12]]
                        _set_last_report_load_error(
                            f"Не найдена колонка с датой. Колонки: {', '.join(col_list)}"
                        )
                        return None
                    df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
            except Exception:
                pass
        
        if df[date_col].notna().sum() == 0:
            sample_vals = df[date_col].astype(str).head(5).tolist()
            _set_last_report_load_error(
                f"Не удалось распознать даты в колонке '{date_col}'. Примеры: {', '.join(sample_vals)}"
            )
            return None
        
        df = df.dropna(subset=[date_col])
        if df.empty:
            _set_last_report_load_error("Нет данных с корректной датой")
            return None
        
        # Создаем нормализованный DataFrame
        normalized_data = pd.DataFrame()
        normalized_data['Дата'] = df[date_col]
        
        # Обрабатываем колонку с продажами
        sales_col = None
        for col in df.columns:
            col_lower = col.lower()
            if 'продаж' in col_lower or 'выкуп' in col_lower or 'sale' in col_lower:
                sales_col = col
                break
        
        # Обрабатываем колонку с заказами (может отсутствовать)
        orders_col = None
        for col in df.columns:
            col_lower = col.lower()
            if 'заказ' in col_lower or 'order' in col_lower:
                orders_col = col
                break
        
        orders_values = None
        if orders_col:
            orders_values = []
            for val in df[orders_col]:
                if pd.isna(val):
                    orders_values.append(0)
                elif isinstance(val, str):
                    match = re.search(r'(\d+)', str(val))
                    if match:
                        orders_values.append(float(match.group(1)))
                    else:
                        orders_values.append(0)
                else:
                    orders_values.append(float(val) if pd.notna(val) else 0)
            normalized_data['Заказы'] = orders_values
        else:
            orders_values = None
        
        if sales_col:
            # Парсим значения вида "41 шт" или просто числа
            sales_values = []
            for val in df[sales_col]:
                if pd.isna(val):
                    sales_values.append(0)
                elif isinstance(val, str):
                    # Извлекаем число из строки "41 шт"
                    match = re.search(r'(\d+)', str(val))
                    if match:
                        sales_values.append(float(match.group(1)))
                    else:
                        sales_values.append(0)
                else:
                    sales_values.append(float(val) if pd.notna(val) else 0)
            normalized_data['Продажи'] = sales_values
        elif orders_values is not None:
            # В новом формате продажи представлены как "Заказы"
            normalized_data['Продажи'] = orders_values
        else:
            normalized_data['Продажи'] = 0
        
        if orders_values is not None:
            normalized_data['Заказы'] = orders_values
        else:
            # Если нет заказов, используем продажи как заказы (приблизительно)
            normalized_data['Заказы'] = normalized_data['Продажи'] * 1.2  # Примерный коэффициент
        
        # Обрабатываем колонку "Цена с СПП, ₽" (приоритет)
        spp_price_col = None
        for col in df.columns:
            if "спп" in col.lower() and "цена" in col.lower():
                spp_price_col = col
                break
        
        if spp_price_col:
            spp_price_values = []
            for val in df[spp_price_col]:
                if pd.isna(val):
                    spp_price_values.append(0)
                elif isinstance(val, str):
                    clean_val = re.sub(r'[^\d,.]', '', str(val).replace(',', '.'))
                    try:
                        spp_price_values.append(float(clean_val))
                    except:
                        spp_price_values.append(0)
                else:
                    spp_price_values.append(float(val) if pd.notna(val) else 0)
            normalized_data['Цена с СПП, ₽'] = spp_price_values
        
        # Обрабатываем колонку с базовой ценой (fallback)
        base_price_col = None
        for col in df.columns:
            col_lower = col.lower()
            if col == "Базовая цена, ₽" or col == "Базовая цена":
                base_price_col = col
                break
            if "цена" in col_lower and "без спп" in col_lower:
                base_price_col = col
                break
        
        if base_price_col:
            # Парсим значения вида "615 ₽" или просто числа
            base_price_values = []
            for val in df[base_price_col]:
                if pd.isna(val):
                    base_price_values.append(0)
                elif isinstance(val, str):
                    clean_val = re.sub(r'[^\d,.]', '', str(val).replace(',', '.'))
                    try:
                        base_price_values.append(float(clean_val))
                    except:
                        base_price_values.append(0)
                else:
                    base_price_values.append(float(val) if pd.notna(val) else 0)
            normalized_data['Базовая цена, ₽'] = base_price_values
        
        # Обрабатываем колонку с ценой (для совместимости)
        price_col = None
        for col in df.columns:
            col_lower = col.lower()
            if ('цена' in col_lower or 'price' in col_lower) and 'спп' in col_lower:
                price_col = col
                break
        
        if price_col is None:
            # Ищем любую колонку с ценой
            for col in df.columns:
                col_lower = col.lower()
                if 'цена' in col_lower or 'price' in col_lower:
                    price_col = col
                    break
        
        if price_col:
            # Парсим значения вида "615 ₽" или просто числа
            price_values = []
            for val in df[price_col]:
                if pd.isna(val):
                    price_values.append(0)
                elif isinstance(val, str):
                    # Удаляем все нечисловые символы кроме точки и запятой
                    clean_val = re.sub(r'[^\d,.]', '', str(val).replace(',', '.'))
                    try:
                        price_values.append(float(clean_val))
                    except:
                        price_values.append(0)
                else:
                    price_values.append(float(val) if pd.notna(val) else 0)
            normalized_data['Средняя цена'] = price_values
        else:
            normalized_data['Средняя цена'] = 0
        
        if normalized_data.empty:
            _set_last_report_load_error("Нормализованные данные пусты")
            return None
        return normalized_data
    
    except Exception as e:
        _set_last_report_load_error(e)
        return None


def find_and_load_reports_from_tovar(
    skus: tuple,
    tovar_folder: str = "Tovar",
    return_missing: bool = False
) -> dict:
    """
    Находит и загружает отчеты из папки Tovar для указанных артикулов.
    
    Args:
        skus: Кортеж артикулов (строки) - tuple для кеширования
        tovar_folder: Путь к папке Tovar
    
    Returns:
        Словарь {артикул: DataFrame с данными}
    """
    reports = {}
    missing_reports = {}
    
    try:
        # Проверяем существование папки
        if not os.path.exists(tovar_folder):
            for sku in skus:
                missing_reports[str(sku).replace(".0", "")] = "Папка Tovar не найдена"
            return (reports, missing_reports) if return_missing else reports
        
        # Получаем список файлов в папке
        files = os.listdir(tovar_folder)
        
        # Преобразуем артикулы в строки для сравнения
        skus_str = [str(sku).replace(".0", "") for sku in skus]
        
        # Ищем файлы для каждого артикула
        missing_reports = {sku: "Отчет не найден в папке Tovar" for sku in skus_str}
        for filename in files:
            # Извлекаем артикул из названия файла
            file_sku = extract_sku_from_filename(filename)
            
            if file_sku and file_sku in skus_str:
                filepath = os.path.join(tovar_folder, filename)
                # Загружаем отчет
                report_data = load_report_from_tovar_folder(filepath)
                
                if report_data is not None and not report_data.empty:
                    reports[file_sku] = {
                        'data': report_data,
                        'filename': filename,
                        'filepath': filepath
                    }
                    if file_sku in missing_reports:
                        del missing_reports[file_sku]
                elif report_data is None:
                    if file_sku in missing_reports:
                        last_error = get_last_report_load_error()
                        if last_error:
                            missing_reports[file_sku] = f"Не удалось прочитать файл: {filename} ({last_error})"
                        else:
                            missing_reports[file_sku] = f"Не удалось прочитать файл: {filename}"
                else:
                    if file_sku in missing_reports:
                        missing_reports[file_sku] = f"Файл пустой или без данных: {filename}"
    
    except Exception as e:
        pass
    
    return (reports, missing_reports) if return_missing else reports



























