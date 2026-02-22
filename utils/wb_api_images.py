# -*- coding: utf-8 -*-
"""
Модуль для работы с Wildberries API для получения изображений товаров
"""
import requests


def get_product_image_urls_from_wb_api(sku: str, max_images: int = 3) -> list:
    """
    Получает URL изображений товара из API Wildberries.
    
    Args:
        sku: Артикул товара
        max_images: Максимальное количество изображений
        
    Returns:
        Список URL изображений
    """
    image_urls = []
    
    try:
        # API Wildberries для получения данных о товаре
        api_url = f"https://card.wb.ru/cards/v1/detail?appType=1&curr=rub&dest=-1257786&spp=30&nm={sku}"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json',
            'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
        }
        
        response = requests.get(api_url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            if 'data' in data and 'products' in data['data'] and len(data['data']['products']) > 0:
                product = data['data']['products'][0]
                
                # Получаем изображения из поля 'pics'
                if 'pics' in product and product['pics']:
                    # Определяем параметры для формирования URL
                    # Формат: https://basket-{basket_id}.wbbasket.ru/vol{vol_id}/part{part_id}/{sku}/images/big/{pic_id}.jpg
                    sku_int = int(sku) if sku.isdigit() else 0
                    
                    if sku_int > 0:
                        # Определяем корзину (basket_id) на основе диапазонов артикулов
                        # WB использует разные корзины для разных диапазонов артикулов
                        basket_id = 1  # По умолчанию
                        if sku_int >= 14300000 and sku_int < 28800000:
                            basket_id = 2
                        elif sku_int >= 28800000 and sku_int < 43500000:
                            basket_id = 3
                        elif sku_int >= 43500000 and sku_int < 58000000:
                            basket_id = 4
                        elif sku_int >= 58000000 and sku_int < 72500000:
                            basket_id = 5
                        elif sku_int >= 72500000 and sku_int < 87000000:
                            basket_id = 6
                        elif sku_int >= 87000000 and sku_int < 101500000:
                            basket_id = 7
                        elif sku_int >= 101500000 and sku_int < 116000000:
                            basket_id = 8
                        elif sku_int >= 116000000 and sku_int < 130500000:
                            basket_id = 9
                        elif sku_int >= 130500000 and sku_int < 145000000:
                            basket_id = 10
                        elif sku_int >= 145000000 and sku_int < 159500000:
                            basket_id = 11
                        elif sku_int >= 159500000 and sku_int < 174000000:
                            basket_id = 12
                        elif sku_int >= 174000000 and sku_int < 188500000:
                            basket_id = 13
                        elif sku_int >= 188500000 and sku_int < 203000000:
                            basket_id = 14
                        elif sku_int >= 203000000 and sku_int < 217500000:
                            basket_id = 15
                        elif sku_int >= 217500000 and sku_int < 232000000:
                            basket_id = 16
                        elif sku_int >= 232000000:
                            basket_id = 17
                        
                        # Определяем vol и part из артикула
                        # vol = первые 3 цифры (или первые 2 для старых артикулов)
                        # part = первые 4 цифры
                        vol_id = sku_int // 100000 if sku_int >= 100000 else sku_int // 10000
                        part_id = sku_int // 1000 if sku_int >= 1000 else sku_int // 100
                        
                        # Формируем URL для каждого изображения
                        for pic_id in product['pics'][:max_images]:
                            image_url = f"https://basket-{basket_id:02d}.wbbasket.ru/vol{vol_id}/part{part_id}/{sku}/images/big/{pic_id}.jpg"
                            image_urls.append(image_url)
                
                # Альтернативный способ: если есть поле 'photos' или 'images'
                elif 'photos' in product and product['photos'] and not image_urls:
                    for photo_url in product['photos'][:max_images]:
                        if isinstance(photo_url, str) and photo_url.startswith('http'):
                            image_urls.append(photo_url)
        
    except Exception as e:
        # В случае ошибки возвращаем пустой список
        pass
    
    return image_urls[:max_images]


def get_product_name_from_wb(sku: str) -> str:
    """
    Получает название товара из API Wildberries.
    
    Args:
        sku: Артикул товара
        
    Returns:
        Название товара или пустая строка
    """
    try:
        api_url = f"https://card.wb.ru/cards/v1/detail?appType=1&curr=rub&dest=-1257786&spp=30&nm={sku}"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json',
            'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
        }
        
        response = requests.get(api_url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            if 'data' in data and 'products' in data['data'] and len(data['data']['products']) > 0:
                product = data['data']['products'][0]
                if 'name' in product:
                    return product['name']
    except Exception as e:
        pass
    
    return ""


def build_screenshot_url(page_url: str, key: str, width: int = 400, height: int = 600, format: str = "JPEG", profile: str = "D4", base_url: str = "https://api.s-shot.ru") -> str:
    """
    Строит URL для получения скриншота через screenshotapi.net
    
    Args:
        page_url: URL страницы для скриншота
        key: API ключ screenshotapi.net
        width: Ширина скриншота
        height: Высота скриншота
        format: Формат изображения (JPEG, PNG)
        profile: Профиль браузера
        base_url: Базовый URL API
        
    Returns:
        URL скриншота
    """
    if not key:
        return ""
    
    params = {
        "url": page_url,
        "key": key,
        "dimension": f"{width}x{height}",
        "format": format.lower(),
        "image": "1"
    }
    
    if profile:
        params["profile"] = profile
    
    query_string = "&".join([f"{k}={v}" for k, v in params.items()])
    return f"{base_url}?{query_string}"



























