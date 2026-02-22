# -*- coding: utf-8 -*-
"""
Модуль для обработки таблиц и данных
"""
import pandas as pd
from io import BytesIO


def read_table(file_bytes: bytes, filename: str, error_callback=None):
    """
    Читает таблицу из байтов файла (Excel или CSV).
    
    Args:
        file_bytes: Байты файла
        filename: Имя файла (для определения формата)
        error_callback: Функция для обработки ошибок (опционально)
    
    Returns:
        tuple: (df, df_raw, metadata)
    """
    try:
        if filename.lower().endswith((".xlsx", ".xls")):
            df_raw = pd.read_excel(BytesIO(file_bytes), sheet_name=0, header=None)
        else:
            df_raw = pd.read_csv(BytesIO(file_bytes), header=None, sep=None, engine="python")
    except Exception as e:
        if error_callback:
            error_callback(f"Ошибка чтения файла: {e}")
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


def get_file_statistics(df):
    """Получает статистику по загруженному файлу"""
    try:
        stats = {
            "total_rows": len(df),
            "total_products": df["Артикул"].nunique() if "Артикул" in df.columns else len(df),
            "total_revenue": df["Выручка"].sum() if "Выручка" in df.columns else 0,
            "total_orders": df["Заказы"].sum() if "Заказы" in df.columns else 0,
            "avg_price": df["Средняя цена"].mean() if "Средняя цена" in df.columns else 0,
            "columns_count": len(df.columns)
        }
        
        # Добавляем информацию о колонках
        stats["available_columns"] = list(df.columns)
        
        return stats
    except Exception as e:
        return None


def get_analysis_period(df, df_raw=None, header_row=None, error_callback=None):
    """Извлекает анализируемый период из заголовка таблицы"""
    try:
        # Сначала пытаемся найти период в заголовке таблицы
        if df_raw is not None and header_row is not None:
            # Ищем строку с "Анализируемый период" в заголовке
            for i in range(max(0, header_row - 5), min(len(df_raw), header_row + 1)):
                row_values = df_raw.iloc[i].astype(str).str.strip().tolist()
                
                # Ищем "Анализируемый период" в строке
                for j, cell_value in enumerate(row_values):
                    if "анализируемый период" in cell_value.lower():
                        # Ищем даты в соседних ячейках
                        for k in range(j + 1, min(len(row_values), j + 5)):
                            period_value = row_values[k]
                            if period_value and period_value != "nan":
                                # Пытаемся извлечь даты из строки вида "01.01.2025 - 30.04.2025"
                                import re
                                date_pattern = r'(\d{2}\.\d{2}\.\d{4})\s*-\s*(\d{2}\.\d{2}\.\d{4})'
                                match = re.search(date_pattern, period_value)
                                
                                if match:
                                    start_date_str = match.group(1)
                                    end_date_str = match.group(2)
                                    
                                    try:
                                        # Парсим даты
                                        start_date = pd.to_datetime(start_date_str, format='%d.%m.%Y')
                                        end_date = pd.to_datetime(end_date_str, format='%d.%m.%Y')
                                        
                                        # Форматируем даты для отображения
                                        months = {
                                            1: "января", 2: "февраля", 3: "марта", 4: "апреля", 5: "мая", 6: "июня",
                                            7: "июля", 8: "августа", 9: "сентября", 10: "октября", 11: "ноября", 12: "декабря"
                                        }
                                        
                                        start_date_formatted = f"{start_date.day} {months[start_date.month]} {start_date.year}"
                                        end_date_formatted = f"{end_date.day} {months[end_date.month]} {end_date.year}"
                                        
                                        # Вычисляем количество дней
                                        days_diff = (end_date - start_date).days
                                        
                                        return {
                                            "start_date": start_date,
                                            "end_date": end_date,
                                            "start_date_str": start_date_formatted,
                                            "end_date_str": end_date_formatted,
                                            "days_count": days_diff + 1,
                                            "period_str": f"{start_date_formatted} - {end_date_formatted} ({days_diff + 1} дней)",
                                            "source": "header"
                                        }
                                    except Exception as e:
                                        if error_callback:
                                            error_callback(f"Не удалось распарсить даты из заголовка: {e}")
                                        break
                                break
                        break
        
        # Если не нашли в заголовке, пытаемся извлечь из колонки "Дата создания"
        if "Дата создания" in df.columns and not df["Дата создания"].isna().all():
            # Получаем минимальную и максимальную даты
            min_date = df["Дата создания"].dropna().min()
            max_date = df["Дата создания"].dropna().max()
            
            if pd.notna(min_date) and pd.notna(max_date):
                # Форматируем даты для отображения
                months = {
                    1: "января", 2: "февраля", 3: "марта", 4: "апреля", 5: "мая", 6: "июня",
                    7: "июля", 8: "августа", 9: "сентября", 10: "октября", 11: "ноября", 12: "декабря"
                }
                
                min_date_str = f"{min_date.day} {months[min_date.month]} {min_date.year}"
                max_date_str = f"{max_date.day} {months[max_date.month]} {max_date.year}"
                
                # Вычисляем количество дней
                days_diff = (max_date - min_date).days
                
                return {
                    "start_date": min_date,
                    "end_date": max_date,
                    "start_date_str": min_date_str,
                    "end_date_str": max_date_str,
                    "days_count": days_diff + 1,
                    "period_str": f"{min_date_str} - {max_date_str} ({days_diff + 1} дней)",
                    "source": "date_column"
                }
        
        return None
    except Exception as e:
        if error_callback:
            error_callback(f"Ошибка при определении периода анализа: {e}")
        return None



























