# -*- coding: utf-8 -*-
"""
Модуль для работы с Wildberries URL и базовыми операциями
"""
import re


def build_wb_product_url(nm, host="https://global.wildberries.ru"):
    """Строит URL товара Wildberries по артикулу"""
    return f"{host.rstrip('/')}/catalog/{str(nm).replace('.0','')}/detail.aspx"


def extract_sku_from_url(url: str) -> str | None:
    """
    Извлекает артикул (SKU) из URL товара Wildberries.
    
    Поддерживаемые форматы:
    - https://www.wildberries.ru/catalog/{sku}/detail.aspx
    - https://wildberries.ru/catalog/{sku}/detail.aspx
    - https://global.wildberries.ru/catalog/{sku}/detail.aspx
    - https://www.wildberries.ru/catalog/{sku}/detail
    - https://www.wildberries.ru/catalog/{sku}/
    
    Args:
        url: URL товара Wildberries
        
    Returns:
        Артикул товара или None, если не удалось извлечь
    """
    if not url or not isinstance(url, str):
        return None
    
    try:
        # Убираем пробелы и лишние символы
        url = url.strip()
        
        # Паттерны для поиска артикула в URL
        # Паттерн 1: /catalog/{sku}/detail
        pattern1 = r'/catalog/(\d+)/detail'
        match = re.search(pattern1, url)
        if match:
            return match.group(1)
        
        # Паттерн 2: /catalog/{sku}/
        pattern2 = r'/catalog/(\d+)/?'
        match = re.search(pattern2, url)
        if match:
            return match.group(1)
        
        # Паттерн 3: /catalog/{sku} (без слеша в конце)
        pattern3 = r'/catalog/(\d+)(?:\?|$)'
        match = re.search(pattern3, url)
        if match:
            return match.group(1)
        
        return None
    except Exception:
        return None


def extract_sku_from_filename(filename: str) -> str:
    """
    Извлекает артикул из названия файла.
    Формат: "Wildberries - 159482033 - Данные по дням..."
    
    Примеры:
    - "Wildberries - 159482033 - Данные по дням.xlsx" -> "159482033"
    - "report_123456789_data.csv" -> "123456789"
    """
    if not filename:
        return ""
    
    try:
        # Ищем паттерн "Wildberries - <артикул> -"
        match = re.search(r'Wildberries\s*-\s*(\d+)\s*-', filename)
        if match:
            return match.group(1)

        # Альтернативный паттерн: просто число после дефиса
        match = re.search(r'-\s*(\d{6,})\s*-', filename)
        if match:
            return match.group(1)
        
        # Ищем последовательность из 6+ цифр
        match = re.search(r'(\d{6,})', filename)
        if match:
            return match.group(1)

        return ""
    except Exception:
        return ""



























