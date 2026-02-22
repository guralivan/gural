# -*- coding: utf-8 -*-
"""
Модуль для простого анализа изображений (цвет, стиль и т.д.)
"""
import numpy as np
from collections import Counter


def extract_dominant_colors_from_image(image, num_colors: int = 5) -> list:
    """
    Извлекает доминирующие цвета из изображения.
    Упрощенная версия без sklearn для совместимости.
    """
    try:
        # Преобразуем изображение в массив
        img_array = np.array(image)
        
        # Изменяем форму для анализа
        pixels = img_array.reshape(-1, 3)
        
        # Упрощенный алгоритм: берем случайную выборку пикселей
        # и находим наиболее частые цвета
        sample_size = min(10000, len(pixels))
        if len(pixels) > sample_size:
            sample_indices = np.random.choice(len(pixels), sample_size, replace=False)
            sample_pixels = pixels[sample_indices]
        else:
            sample_pixels = pixels
        
        # Квантуем цвета (округление до ближайших значений)
        quantized = (sample_pixels / 32).astype(int) * 32
        quantized = np.clip(quantized, 0, 255)
        
        # Подсчитываем частоту цветов
        color_counts = Counter(tuple(c) for c in quantized)
        
        # Берем топ-N цветов
        top_colors = color_counts.most_common(num_colors)
        
        # Возвращаем RGB значения
        return [list(color[0]) for color in top_colors]
        
    except Exception:
        # Fallback: просто берем средний цвет
        try:
            img_array = np.array(image)
            avg_color = img_array.mean(axis=(0, 1)).astype(int)
            return [list(avg_color)]
        except:
            return []


def get_color_name_russian(rgb: list) -> str:
    """
    Преобразует RGB в русское название цвета.
    """
    try:
        r, g, b = rgb[0], rgb[1], rgb[2]
        
        # Простая эвристика для определения цвета
        # Определяем доминирующий канал
        max_val = max(r, g, b)
        min_val = min(r, g, b)
        diff = max_val - min_val
        
        # Серый/белый/черный
        if diff < 30:
            if max_val > 200:
                return "Белый"
            elif max_val < 50:
                return "Черный"
            else:
                return "Серый"
        
        # Определяем цвет по доминирующему каналу
        if r > g and r > b:
            if r > 200 and g < 100 and b < 100:
                return "Красный"
            elif r > 150 and g > 100:
                return "Оранжевый"
            elif r > 150 and b > 100:
                return "Розовый"
            else:
                return "Красный"
        elif g > r and g > b:
            if g > 200 and r < 100 and b < 100:
                return "Зеленый"
            elif g > 150 and b > 100:
                return "Бирюзовый"
            else:
                return "Зеленый"
        elif b > r and b > g:
            if b > 200 and r < 100 and g < 100:
                return "Синий"
            elif b > 150 and r > 100:
                return "Фиолетовый"
            else:
                return "Синий"
        elif r > 200 and g > 200:
            return "Желтый"
        elif r > 150 and g > 150 and b > 150:
            return "Бежевый"
        else:
            return "Разноцветный"
            
    except Exception:
        return None


def analyze_style_from_image(image) -> dict:
    """
    Анализирует изображение для определения стиля товара.
    Базовая эвристика на основе цветов и контраста.
    """
    params = {}
    
    try:
        img_array = np.array(image)
        
        # Вычисляем среднюю яркость
        brightness = img_array.mean()
        
        # Вычисляем контраст (стандартное отклонение)
        contrast = img_array.std()
        
        # Определяем стиль на основе характеристик
        if brightness > 200:
            params['Стиль'] = 'Светлый'
        elif brightness < 80:
            params['Стиль'] = 'Темный'
        else:
            params['Стиль'] = 'Средний'
        
        # Определяем тип по контрасту
        if contrast > 60:
            if 'Стиль' in params:
                params['Стиль'] += ', Контрастный'
        
    except Exception:
        pass
    
    return params



























