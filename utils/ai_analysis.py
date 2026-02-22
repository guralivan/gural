# -*- coding: utf-8 -*-
"""
Модуль для AI-анализа с использованием OpenAI API.
Содержит функции для анализа комбинаций товаров и трендов WGSN.
"""

import os
import json
import base64
import re
import time

# Проверка наличия библиотеки OpenAI
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    openai = None

from utils.image_cache import get_cached_image_path
from utils.wb_api_images import get_product_name_from_wb


def analyze_combination_products_with_ai_core(
    combo_products_df, 
    combination_key: str, 
    category: str, 
    api_key: str,
    max_products: int = 5
) -> dict:
    """
    Анализирует товары в комбинации с помощью ИИ для получения рекомендаций по улучшению.
    
    Args:
        combo_products_df: DataFrame с товарами комбинации
        combination_key: Ключ комбинации (параметры)
        category: Категория товаров
        api_key: API ключ OpenAI
        max_products: Максимальное количество товаров для анализа
        
    Returns:
        Словарь с анализом и рекомендациями
    """
    if not OPENAI_AVAILABLE:
        return {
            "error": "OpenAI не доступен. Установите библиотеку openai для использования этой функции."
        }
    
    if not api_key:
        return {
            "error": "API ключ OpenAI не указан."
        }
    
    try:
        client = openai.OpenAI(api_key=api_key)
        
        # Собираем изображения товаров (максимум max_products товаров для анализа)
        image_paths = []
        product_info = []
        
        for idx, row in combo_products_df.head(max_products).iterrows():
            sku = str(row.get("Артикул", "")).replace(".0", "")
            if not sku:
                continue
            
            # Получаем путь к изображению
            image_path = get_cached_image_path(sku)
            if image_path and os.path.exists(image_path):
                image_paths.append(image_path)
                
                # Собираем информацию о товаре
                product_data = {
                    "sku": sku,
                    "revenue": row.get("Выручка", 0),
                    "orders": row.get("Заказы", 0),
                    "price": row.get("Средняя цена", 0),
                    "position": row.get("Позиция в выдаче", 0)
                }
                product_info.append(product_data)
        
        if not image_paths:
            return {
                "error": "Не найдено изображений товаров для анализа. Убедитесь, что изображения скачаны."
            }
        
        # Подготавливаем изображения для отправки в API
        image_contents = []
        for img_path in image_paths:
            try:
                with open(img_path, 'rb') as image_file:
                    image_bytes = image_file.read()
                    image_data = base64.b64encode(image_bytes).decode('utf-8')
                    ext = os.path.splitext(img_path)[1].lower()
                    mime_type = {
                        '.jpg': 'image/jpeg',
                        '.jpeg': 'image/jpeg',
                        '.png': 'image/png',
                        '.webp': 'image/webp'
                    }.get(ext, 'image/jpeg')
                    image_contents.append({
                        "type": "input_image",
                        "image_url": f"data:{mime_type};base64,{image_data}"
                    })
            except Exception:
                continue
        
        if not image_contents:
            return {
                "error": "Не удалось подготовить изображения для анализа."
            }
        
        # Формируем промпт для анализа
        avg_revenue = combo_products_df["Выручка"].mean() if "Выручка" in combo_products_df.columns else 0
        avg_position = combo_products_df["Позиция в выдаче"].mean() if "Позиция в выдаче" in combo_products_df.columns else 0
        total_products = len(combo_products_df)
        
        prompt = f"""Ты эксперт по анализу товаров и маркетингу. Проанализируй товары в комбинации параметров и дай рекомендации по улучшению.

КОНТЕКСТ:
- Категория: {category}
- Комбинация параметров: {combination_key}
- Количество товаров в комбинации: {total_products}
- Средняя выручка на товар: {avg_revenue:,.0f} руб
- Средняя позиция в выдаче: {avg_position:.1f}

ЗАДАЧА:
1. Проанализируй изображения товаров в этой комбинации
2. Определи общие характеристики и паттерны
3. Выяви слабые места и возможности для улучшения
4. Дай конкретные рекомендации по изменению товаров для получения конкурентного преимущества

ФОРМАТ ОТВЕТА (JSON):
{{
    "common_characteristics": "Общие характеристики товаров в комбинации",
    "strengths": ["Сильная сторона 1", "Сильная сторона 2", ...],
    "weaknesses": ["Слабая сторона 1", "Слабая сторона 2", ...],
    "recommendations": [
        {{
            "priority": "high|medium|low",
            "category": "Дизайн|Материал|Цвет|Принт|Детали",
            "recommendation": "Конкретная рекомендация по улучшению",
            "expected_impact": "Ожидаемый эффект от изменения"
        }},
        ...
    ],
    "competitive_advantages": ["Преимущество 1", "Преимущество 2", ...],
    "market_insights": "Анализ рыночной ситуации и трендов для этой категории"
}}

ВАЖНО:
- Будь конкретным и практичным в рекомендациях
- Учитывай специфику категории "{category}"
- Фокусируйся на изменениях, которые дадут реальное конкурентное преимущество
- Учитывай текущие показатели (выручка, позиция) при рекомендациях"""

        # Отправляем запрос в OpenAI
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt}
                ] + image_contents
            }
        ]
        
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            max_tokens=2000,
            temperature=0.7
        )
        
        response_text = response.choices[0].message.content
        
        # Парсим JSON из ответа
        json_start = response_text.find('{')
        json_end = response_text.rfind('}') + 1
        
        if json_start >= 0 and json_end > json_start:
            json_str = response_text[json_start:json_end]
            try:
                analysis_result = json.loads(json_str)
                analysis_result["raw_response"] = response_text
                return analysis_result
            except json.JSONDecodeError:
                return {
                    "error": "Не удалось распарсить ответ ИИ",
                    "raw_response": response_text
                }
        else:
            return {
                "error": "ИИ не вернул JSON формат",
                "raw_response": response_text
            }
            
    except openai.RateLimitError:
        return {
            "error": "Превышен лимит запросов к OpenAI API. Попробуйте позже."
        }
    except openai.APITimeoutError:
        return {
            "error": "Превышено время ожидания ответа от OpenAI API. Попробуйте позже."
        }
    except Exception as e:
        return {
            "error": f"Ошибка при анализе: {str(e)}"
        }


def analyze_wgsn_trends_with_ai_core(
    wgsn_content: dict, 
    category: str, 
    combination_key: str,
    api_key: str
) -> dict:
    """
    Анализирует содержимое файлов WGSN с помощью ИИ для получения трендов и рекомендаций.
    
    Args:
        wgsn_content: Словарь с содержимым файлов WGSN
        category: Категория товаров
        combination_key: Ключ комбинации параметров
        api_key: API ключ OpenAI
        
    Returns:
        Словарь с анализом трендов WGSN
    """
    if not OPENAI_AVAILABLE:
        return {
            "error": "OpenAI не доступен. Установите библиотеку openai для использования этой функции."
        }
    
    if "error" in wgsn_content:
        return wgsn_content
    
    if not api_key:
        return {
            "error": "API ключ OpenAI не указан."
        }
    
    try:
        client = openai.OpenAI(api_key=api_key)
        
        # Объединяем содержимое всех файлов WGSN
        combined_content = ""
        file_names = []
        for filename, content in wgsn_content.items():
            # Увеличиваем размер для более детального анализа
            combined_content += f"\n\n=== Файл: {filename} ===\n{content[:10000]}"
            file_names.append(filename)
        
        # Если содержимое слишком большое, берем больше контента из каждого файла
        if len(combined_content) > 50000:
            combined_content = ""
            for filename, content in wgsn_content.items():
                combined_content += f"\n\n=== Файл: {filename} ===\n{content[:15000]}"
        
        # Парсим параметры комбинации для детального анализа
        combination_params = {}
        if combination_key:
            parts = [p.strip() for p in combination_key.split("|")]
            for part in parts:
                if ":" in part:
                    param_name, param_value = part.split(":", 1)
                    combination_params[param_name.strip()] = param_value.strip()
        
        # Определяем специфику категории
        category_specifics = ""
        if "рашград" in category.lower() or "компрессион" in category.lower() or "футболка" in category.lower():
            category_specifics = """
СПЕЦИФИКА КАТЕГОРИИ:
- Это мужская компрессионная/спортивная одежда (рашград)
- Товары предназначены для спорта, фитнеса, активного образа жизни
- Важны: функциональность, комфорт, технологичность материалов
- Целевая аудитория: мужчины, занимающиеся спортом, фитнесом, ведущие активный образ жизни
- Ключевые требования: влагоотведение, воздухопроницаемость, эластичность, долговечность
- Конкурентная среда: высокая конкуренция, важно выделяться через дизайн, технологии, качество
"""
        
        # Формируем детальный промпт для анализа
        prompt = f"""Ты эксперт по анализу модных трендов WGSN (Worth Global Style Network) и специалист по спортивной/компрессионной одежде. 
Проведи глубокий и детальный анализ файлов WGSN и дай конкретные, развернутые рекомендации для товаров в указанной комбинации параметров.

КОНТЕКСТ АНАЛИЗА:
- Категория товаров: {category}
{category_specifics}
- Текущая комбинация параметров: {combination_key}
- Детали комбинации: {json.dumps(combination_params, ensure_ascii=False, indent=2) if combination_params else "Параметры не указаны"}
- Файлы WGSN для анализа: {', '.join(file_names)}

СОДЕРЖИМОЕ ФАЙЛОВ WGSN:
{combined_content}

ДЕТАЛЬНАЯ ЗАДАЧА АНАЛИЗА:

1. ГЛУБОКИЙ АНАЛИЗ ТРЕНДОВ WGSN:
   - Выдели ВСЕ релевантные тренды из файлов WGSN для категории "{category}"
   - Определи приоритетность трендов (что актуально сейчас, что будет актуально в ближайшем будущем)
   - Найди тренды, которые напрямую связаны с компрессионной/спортивной одеждой, футболками, мужской спортивной одеждой
   - Выяви тренды по цветам, материалам, технологиям, дизайну, которые применимы к данной категории

2. КОНКРЕТНОЕ СОПОСТАВЛЕНИЕ С КОМБИНАЦИЕЙ:
   - Проанализируй КАЖДЫЙ параметр из комбинации: {combination_key}
   - Для каждого параметра найди соответствующие тренды из WGSN
   - Определи, какие параметры соответствуют актуальным трендам, а какие устарели
   - Выяви параметры, которые можно улучшить на основе трендов WGSN

3. РАЗВЕРНУТЫЕ РЕКОМЕНДАЦИИ:
   - Дай КОНКРЕТНЫЕ рекомендации по изменению КАЖДОГО параметра комбинации на основе трендов WGSN
   - Укажи, какие конкретные значения параметров будут актуальны согласно WGSN
   - Объясни, ПОЧЕМУ эти изменения дадут конкурентное преимущество
   - Предложи новые комбинации параметров, которые будут соответствовать трендам WGSN

4. АНАЛИЗ ПО КАТЕГОРИЯМ:
   - ЦВЕТА: какие цвета актуальны для спортивной/компрессионной одежды по WGSN, какие устарели
   - МАТЕРИАЛЫ: какие материалы и технологии рекомендуются WGSN для данной категории
   - ДИЗАЙН: какие дизайнерские решения, принты, детали актуальны
   - ТЕХНОЛОГИИ: какие технологические решения (влагозащита, терморегуляция и т.д.) актуальны

5. КОНКУРЕНТНОЕ ПРЕИМУЩЕСТВО:
   - Определи, какие тренды WGSN еще не широко используются в категории "{category}"
   - Предложи, как можно выделиться на рынке, применяя эти тренды
   - Укажи конкретные шаги для получения конкурентного преимущества

ФОРМАТ ОТВЕТА (JSON):
{{
    "wgsn_trends_summary": "Развернутое резюме ключевых трендов из WGSN, применимых к категории {category}. Минимум 200 слов.",
    "category_analysis": {{
        "current_trends": "Актуальные тренды для {category} на основе WGSN",
        "emerging_trends": "Появляющиеся тренды, которые станут актуальными",
        "declining_trends": "Устаревающие тренды, от которых стоит отойти"
    }},
    "combination_parameter_analysis": [
        {{
            "parameter": "Название параметра из комбинации",
            "current_value": "Текущее значение",
            "wgsn_trend_status": "Соответствует|Частично соответствует|Не соответствует трендам WGSN",
            "wgsn_recommendation": "Конкретная рекомендация WGSN для этого параметра",
            "suggested_values": ["Рекомендуемое значение 1", "Рекомендуемое значение 2", ...],
            "rationale": "Обоснование рекомендации на основе WGSN"
        }},
        ...
    ],
    "relevant_trends": [
        {{
            "trend_name": "Название тренда",
            "source_file": "Имя файла WGSN",
            "trend_type": "Цвет|Материал|Дизайн|Технология|Стиль|Функциональность",
            "description": "Детальное описание тренда (минимум 100 слов)",
            "relevance_to_category": "Почему тренд критически важен для {category}",
            "application_to_combination": "Конкретное применение тренда к комбинации {combination_key}",
            "implementation_steps": ["Шаг 1", "Шаг 2", "Шаг 3"],
            "expected_market_impact": "Ожидаемое влияние на рынок и продажи"
        }},
        ...
    ],
    "trend_recommendations": [
        {{
            "priority": "high|medium|low",
            "trend_category": "Цвет|Дизайн|Материал|Технология|Стиль|Функциональность",
            "recommendation": "Детальная рекомендация на основе трендов WGSN (минимум 150 слов)",
            "specific_changes": "Конкретные изменения в параметрах комбинации",
            "expected_impact": "Детальное описание ожидаемого эффекта от применения тренда",
            "wgsn_source": "Конкретная цитата или ссылка на источник из файлов WGSN",
            "timeline": "Когда лучше внедрить (сейчас|ближайшие 3 месяца|6 месяцев|год)"
        }},
        ...
    ],
    "new_combination_suggestions": [
        {{
            "combination": "Новая комбинация параметров на основе трендов WGSN",
            "rationale": "Обоснование новой комбинации",
            "wgsn_trends_used": ["Тренд 1", "Тренд 2", ...],
            "competitive_advantage": "Какое конкурентное преимущество даст эта комбинация"
        }},
        ...
    ],
    "future_trends": [
        {{
            "trend_name": "Название будущего тренда",
            "timeframe": "Когда станет актуальным",
            "description": "Описание тренда",
            "preparation_steps": ["Шаг подготовки 1", "Шаг подготовки 2", ...]
        }},
        ...
    ],
    "competitive_advantages_from_trends": [
        {{
            "advantage": "Конкретное конкурентное преимущество",
            "wgsn_trend_basis": "На каком тренде WGSN основано",
            "implementation": "Как реализовать",
            "market_positioning": "Как позиционировать на рынке"
        }},
        ...
    ],
    "market_insights": "Развернутый анализ рыночной ситуации на основе трендов WGSN для категории {category}. Минимум 300 слов.",
    "action_plan": {{
        "immediate_actions": ["Действие 1", "Действие 2", ...],
        "short_term_actions": ["Действие 1 (3 месяца)", "Действие 2 (3 месяца)", ...],
        "long_term_actions": ["Действие 1 (6-12 месяцев)", "Действие 2 (6-12 месяцев)", ...]
    }}
}}

КРИТИЧЕСКИ ВАЖНО:
- Будь МАКСИМАЛЬНО конкретным и детальным в рекомендациях
- Ссылайся на КОНКРЕТНЫЕ тренды из файлов WGSN с указанием источника
- Анализируй КАЖДЫЙ параметр комбинации отдельно
- Давай РАЗВЕРНУТЫЕ объяснения (минимум 100-150 слов для каждого важного пункта)
- Учитывай специфику категории "{category}" - это спортивная/компрессионная одежда для мужчин
- Фокусируйся на трендах, которые дадут РЕАЛЬНОЕ конкурентное преимущество
- Предлагай КОНКРЕТНЫЕ значения параметров, а не общие рекомендации
- Объясняй ПОЧЕМУ каждое изменение важно с точки зрения трендов WGSN

ОБЯЗАТЕЛЬНО:
- Твой ответ должен быть ВАЛИДНЫМ JSON объектом
- Начинай ответ с символа {{ и заканчивай символом }}
- НЕ добавляй никакого текста до или после JSON объекта
- НЕ используй markdown код-блоки (```json или ```)
- Ответ должен начинаться сразу с {{ и заканчиваться }}
- Все строки должны быть правильно экранированы для JSON
- Используй двойные кавычки для всех ключей и строковых значений"""

        # Пытаемся отправить запрос, используя несколько стратегий
        response = None
        response_text = None
        last_error = None
        
        # Попытка 1: Без response_format (более гибкий подход)
        try:
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system",
                        "content": "Ты эксперт по анализу модных трендов WGSN (Worth Global Style Network). Твоя задача - проанализировать тренды моды для коммерческих целей. Отвечай ТОЛЬКО валидным JSON объектом без дополнительных объяснений. Начинай ответ сразу с { и заканчивай }."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=4000,
                temperature=0.7
            )
            response_text = response.choices[0].message.content if response.choices[0].message.content else None
            # Проверяем, не является ли ответ отказом
            if response_text and response_text.strip().startswith('{'):
                # Успешно получили JSON
                pass
            elif response_text and ("sorry" in response_text.lower() or "can't assist" in response_text.lower()):
                # Модель отказалась, пробуем следующую стратегию
                response_text = None
                raise Exception("Model refused")
        except Exception as e1:
            last_error = str(e1)
            # Попытка 2: С response_format для гарантированного JSON
            try:
                response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {
                            "role": "system",
                            "content": "Ты эксперт по анализу модных трендов WGSN. Отвечай ТОЛЬКО в формате JSON, без дополнительных объяснений. Начинай ответ сразу с { и заканчивай }."
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    max_tokens=4000,
                    temperature=0.7,
                    response_format={"type": "json_object"}
                )
                response_text = response.choices[0].message.content if response.choices[0].message.content else None
            except Exception as e2:
                # Если первая попытка с response_format не сработала, пробуем без него
                try:
                    response = client.chat.completions.create(
                        model="gpt-4o",
                        messages=[
                            {
                                "role": "system",
                                "content": "Ты эксперт по анализу модных трендов WGSN. Твой ответ должен быть валидным JSON объектом. Начинай сразу с { и заканчивай }. НЕ добавляй никаких объяснений до или после JSON."
                            },
                            {
                                "role": "user",
                                "content": prompt + "\n\nКРИТИЧЕСКИ ВАЖНО: Отвечай ТОЛЬКО валидным JSON объектом. Начинай ответ сразу с символа { и заканчивай символом }. Не добавляй никакого текста до или после JSON."
                            }
                        ],
                        max_tokens=4000,
                        temperature=0.7
                    )
                    response_text = response.choices[0].message.content if response.choices[0].message.content else None
                except Exception as e3:
                    return {
                        "error": f"Ошибка при запросе к OpenAI API. Попробуйте позже.",
                        "raw_response": f"Первая попытка: {str(e2)[:200]}. Вторая попытка: {str(e3)[:200]}",
                        "source_files": file_names
                    }
        
        # Проверяем, что получили ответ
        if not response_text:
            return {
                "error": "ИИ не вернул ответ. Попробуйте позже.",
                "raw_response": "",
                "source_files": file_names
            }
        
        # Проверяем, не вернул ли ИИ отказ (только если ответ не начинается с JSON)
        response_text_stripped = response_text.strip()
        is_likely_refusal = (
            not response_text_stripped.startswith('{') 
            and ("sorry" in response_text.lower() 
                 or "can't assist" in response_text.lower() 
                 or "cannot" in response_text.lower()
                 or "unable to" in response_text.lower()
                 or "i'm sorry" in response_text.lower())
        )
        
        if is_likely_refusal:
            # Если ИИ отказался, пытаемся еще раз с более простым промптом
            try:
                # Упрощаем промпт - убираем часть контента файлов, оставляем только структуру запроса
                simplified_prompt = f"""Ты эксперт по анализу модных трендов WGSN.

Категория товаров: {category}
Комбинация параметров: {combination_key}

Проанализируй тренды WGSN для этой категории и верни рекомендации в формате JSON.

ФОРМАТ ОТВЕТА (JSON):
{{
    "wgsn_trends_summary": "Резюме трендов WGSN для категории {category}",
    "category_analysis": {{
        "current_trends": "Актуальные тренды",
        "emerging_trends": "Появляющиеся тренды",
        "declining_trends": "Устаревающие тренды"
    }},
    "combination_parameter_analysis": [],
    "relevant_trends": [],
    "trend_recommendations": [],
    "market_insights": "Анализ рыночной ситуации",
    "action_plan": {{
        "immediate_actions": [],
        "short_term_actions": [],
        "long_term_actions": []
    }}
}}

Отвечай ТОЛЬКО валидным JSON объектом. Начинай сразу с {{ и заканчивай }}."""
                
                response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {
                            "role": "user",
                            "content": simplified_prompt
                        }
                    ],
                    max_tokens=4000,
                    temperature=0.7
                )
                response_text = response.choices[0].message.content if response.choices[0].message.content else response_text
            except Exception as retry_e:
                # Если и это не помогло, возвращаем ошибку
                pass
        
        # Парсим JSON из ответа
        json_start = response_text.find('{')
        json_end = response_text.rfind('}') + 1
        
        if json_start >= 0 and json_end > json_start:
            json_str = response_text[json_start:json_end]
            try:
                analysis_result = json.loads(json_str)
                analysis_result["raw_response"] = response_text
                analysis_result["source_files"] = file_names
                return analysis_result
            except json.JSONDecodeError as e:
                # Пытаемся исправить JSON (удаляем markdown код-блоки если есть)
                json_str_clean = json_str.strip()
                if json_str_clean.startswith('```'):
                    # Удаляем markdown код-блоки
                    lines = json_str_clean.split('\n')
                    lines = [line for line in lines if not line.strip().startswith('```')]
                    json_str_clean = '\n'.join(lines)
                
                try:
                    analysis_result = json.loads(json_str_clean)
                    analysis_result["raw_response"] = response_text
                    analysis_result["source_files"] = file_names
                    return analysis_result
                except json.JSONDecodeError:
                    return {
                        "error": "Не удалось распарсить ответ ИИ как JSON",
                        "raw_response": response_text,
                        "source_files": file_names,
                        "json_error": str(e)
                    }
        else:
            return {
                "error": "ИИ не вернул JSON формат",
                "raw_response": response_text,
                "source_files": file_names
            }
            
    except openai.RateLimitError:
        return {
            "error": "Превышен лимит запросов к OpenAI API. Попробуйте позже."
        }
    except openai.APITimeoutError:
        return {
            "error": "Превышено время ожидания ответа от OpenAI API. Попробуйте позже."
        }
    except Exception as e:
        return {
            "error": f"Ошибка при анализе WGSN: {str(e)}"
        }


def analyze_image_with_ai_core(
    image_path_or_url: str,
    api_key: str,
    param_options: dict,
    hierarchy_params: list,
    subtype_params: list,
    visual_params: list,
    selected_params: list = None,
    product_name: str = None,
    sku: str = None,
    debug_mode: bool = False
) -> dict:
    """
    Анализирует изображение товара через нейросеть (OpenAI Vision API).
    Core-функция без UI-логики.
    
    Args:
        image_path_or_url: Путь к локальному файлу изображения или URL
        api_key: API ключ OpenAI
        param_options: Словарь с параметрами и их вариантами
        hierarchy_params: Список иерархических параметров
        subtype_params: Список параметров подтипа
        visual_params: Список визуальных параметров
        selected_params: Список параметров для анализа (если None, используются все)
        product_name: Название товара (если доступно)
        sku: Артикул товара (для получения названия, если product_name не указан)
        debug_mode: Режим отладки
        
    Returns:
        Словарь с полями:
        - "params": dict - найденные параметры
        - "_debug_response": str - сырой ответ API (для debug)
        - "_warning": str или None - предупреждение (например, файл слишком большой)
    """
    result = {
        "params": {},
        "_debug_response": None,
        "_warning": None
    }
    
    if not OPENAI_AVAILABLE:
        return result
    
    if not api_key:
        return result
    
    try:
        client = openai.OpenAI(api_key=api_key, timeout=120.0)
        
        # Если указаны выбранные параметры, фильтруем только их
        if selected_params and len(selected_params) > 0:
            param_options = {k: v for k, v in param_options.items() if k in selected_params}
        
        # Разделяем параметры на иерархические и визуальные
        hierarchical_params_dict = {}
        visual_params_dict = {}
        other_params_dict = {}
        
        for param_name, options in param_options.items():
            if param_name in hierarchy_params:
                hierarchical_params_dict[param_name] = options
            elif param_name in visual_params or any(vp in param_name for vp in visual_params):
                visual_params_dict[param_name] = options
            else:
                other_params_dict[param_name] = options
        
        # Получаем название товара из API WB (если доступно)
        if not product_name and sku:
            try:
                product_name = get_product_name_from_wb(sku)
            except:
                pass
        
        # Если название все еще не получено, пытаемся извлечь SKU из пути
        if not product_name:
            try:
                filename = os.path.basename(image_path_or_url)
                if "_screenshotapi_" in filename:
                    sku_from_path = filename.split("_screenshotapi_")[0]
                    if sku_from_path and sku_from_path.isdigit():
                        product_name = get_product_name_from_wb(sku_from_path)
            except:
                pass
        
        # Формируем промпт с учетом иерархии сегментов
        prompt_parts = ["""Ты - помощник для анализа товаров электронной коммерции. Проанализируй это изображение товара (одежды или аксессуара) с Wildberries.

ВАЖНО: 
- Это изображение товара для продажи в интернет-магазине
- Ты анализируешь ТОВАР (одежду, предмет), а не людей
- Игнорируй людей на изображении полностью - они просто демонстрируют товар
- Это коммерческий анализ товара для каталога, не анализ людей
- На скриншоте может быть видно НАЗВАНИЕ ТОВАРА - обязательно учитывай его при анализе!
- Если на скриншоте видно название товара, используй его для более точного определения параметров

АНАЛИЗ ДОЛЖЕН ПРОХОДИТЬ ПО ИЕРАРХИИ СЕГМЕНТОВ:

ШАГ 1: Определи ТИП товара (верхний уровень сегментации)
ШАГ 2: Внутри определенного типа определи КОМПЛЕКТ
ШАГ 3: Внутри определенного комплекта определи ПОДТИП (через параметры РУКАВ и ВОРОТ)
ШАГ 4: Внутри определенного подтипа определи РУКАВ
ШАГ 5: Внутри определенного рукава определи ВОРОТ
ШАГ 6: ТОЛЬКО после определения всех иерархических параметров (Тип → Комплект → Подтип (Рукав, Ворот)) анализируй ВИЗУАЛЬНЫЕ параметры (Цвет, Принт, Логотип, Строчка шов и т.д.)

Визуальные параметры анализируются только в контексте определенной иерархии сегментов!"""]
        
        if product_name:
            prompt_parts.append(f"\nВАЖНО: Название товара из каталога: {product_name}")
            prompt_parts.append("Используй это название для более точного определения параметров товара!")
            prompt_parts.append("Если на скриншоте видно название товара, сравни его с указанным выше и учитывай при анализе.")
        
        if param_options:
            prompt_parts.append("\nКРИТИЧЕСКИ ВАЖНО: Используй ТОЛЬКО параметры из списка ниже! НЕ добавляй параметры, которых нет в списке!")
            
            if hierarchical_params_dict:
                prompt_parts.append("\n=== ИЕРАРХИЧЕСКИЕ ПАРАМЕТРЫ (определяй в указанном порядке) ===")
                for param_name in hierarchy_params:
                    if param_name in hierarchical_params_dict:
                        options = hierarchical_params_dict[param_name]
                        if isinstance(options, list) and options:
                            prompt_parts.append(f"\n{param_name} (варианты): {', '.join(options)}")
                        else:
                            prompt_parts.append(f"\n{param_name}: (определи значение самостоятельно на основе изображения)")
            
            if visual_params_dict:
                prompt_parts.append("\n=== ВИЗУАЛЬНЫЕ ПАРАМЕТРЫ (анализируй ТОЛЬКО после определения иерархии) ===")
                for param_name, options in visual_params_dict.items():
                    if isinstance(options, list):
                        if options:
                            if param_name == "Цвет":
                                single_colors = [opt for opt in options if "-" not in opt]
                                combined_colors = [opt for opt in options if "-" in opt]
                                
                                prompt_parts.append(f"\n- {param_name}:")
                                prompt_parts.append(f"  * Основные цвета (используй когда товар одного цвета): {', '.join(single_colors)}")
                                if combined_colors:
                                    prompt_parts.append(f"  * Сочетания двух цветов (используй ТОЛЬКО когда видно два разных цвета на товаре): {', '.join(combined_colors)}")
                                    prompt_parts.append(f"  ВАЖНО: Сочетания типа 'Черно-белый' используй ТОЛЬКО если товар действительно имеет два разных цвета!")
                            else:
                                prompt_parts.append(f"- {param_name}: {', '.join(options)}")
                        else:
                            prompt_parts.append(f"- {param_name}: (определи значение самостоятельно на основе изображения)")
                    elif options:
                        prompt_parts.append(f"- {param_name}: {options}")
                    else:
                        prompt_parts.append(f"- {param_name}: (определи значение самостоятельно на основе изображения)")
            
            if other_params_dict:
                prompt_parts.append("\n=== ДОПОЛНИТЕЛЬНЫЕ ПАРАМЕТРЫ ===")
                for param_name, options in other_params_dict.items():
                    if isinstance(options, list) and options:
                        prompt_parts.append(f"- {param_name}: {', '.join(options)}")
                    else:
                        prompt_parts.append(f"- {param_name}: (определи значение самостоятельно на основе изображения)")
            
            json_keys = []
            for param_name in param_options.keys():
                json_keys.append(f'  "{param_name}": "значение из вариантов выше или пустая строка"')
            
            prompt_parts.append(f"""
Ответь в формате JSON, используя ТОЛЬКО параметры из списка выше:
{{
{chr(10).join(json_keys)}
}}

КРИТИЧЕСКИ ВАЖНО - СТРОГО СЛЕДУЙ ИЕРАРХИИ: 
1. СНАЧАЛА определи иерархические параметры в строгом порядке:
   - Сначала ТИП товара (футболка, лонгслив, комплект, худи, свитшот и т.д.)
   - Затем КОМПЛЕКТ (внутри определенного типа)
   - Затем ПОДТИП (определяется через параметры РУКАВ и ВОРОТ внутри определенного комплекта)
   - Затем РУКАВ (внутри определенного подтипа)
   - Затем ВОРОТ (внутри определенного рукава)

2. ТОЛЬКО ПОСЛЕ определения всех иерархических параметров анализируй ВИЗУАЛЬНЫЕ параметры:
   - Цвет (анализируй цвет товара в контексте определенной иерархии)
   - Принт (есть ли принт на товаре)
   - Логотип (есть ли логотип)
   - Строчка/Шов (цветная строчка, особенности швов)
   - И другие визуальные параметры

3. ОБЯЗАТЕЛЬНО включи ВСЕ параметры из списка выше в ответ JSON
4. Используй ТОЛЬКО параметры из списка выше
5. НЕ добавляй параметры, которых нет в списке
6. Для параметра "Цвет": если товар имеет ОДИН цвет - используй основной цвет (Белый, Черный, Синий и т.д.)
7. Для параметра "Цвет": если товар имеет ДВА разных цвета - используй сочетание (Черно-белый, Сине-белый и т.д.)
8. НЕ используй сочетания цветов если товар однотонный!
9. Если параметр определить невозможно после тщательного анализа, укажи пустую строку ""
10. Если есть существующие варианты для параметра, ОБЯЗАТЕЛЬНО выбери один из них
11. Будь внимателен и строго следуй иерархии: Тип → Комплект → Подтип (Рукав, Ворот) → Визуальные параметры""")
        else:
            prompt_parts.append("""
Определи следующие параметры товара:
1. Цвет товара - укажи цвет из доступных вариантов
2. Другие видимые характеристики товара

Ответь в формате JSON с параметрами, которые ты видишь на изображении.""")
        
        prompt_parts.append("""

ВАЖНО: 
- Анализируй только характеристики ТОВАРА (цвет, фасон, детали товара)
- Не анализируй людей на изображении
- Фокусируйся на визуальных характеристиках самого товара""")
        
        prompt = "\n".join(prompt_parts)
        
        # Определяем, это локальный файл или URL
        is_local_file = False
        if image_path_or_url:
            is_local_file = os.path.exists(image_path_or_url) and os.path.isfile(image_path_or_url)
        
        if is_local_file:
            # Проверяем размер файла
            file_size = os.path.getsize(image_path_or_url)
            max_size = 20 * 1024 * 1024  # 20 MB
            
            if file_size > max_size:
                result["_warning"] = f"⚠️ Изображение слишком большое ({file_size / 1024 / 1024:.1f} MB). Максимальный размер: 20 MB"
                return result
            
            # Локальный файл - конвертируем в base64
            try:
                with open(image_path_or_url, 'rb') as image_file:
                    image_bytes = image_file.read()
                    image_data = base64.b64encode(image_bytes).decode('utf-8')
                    ext = os.path.splitext(image_path_or_url)[1].lower()
                    mime_type = {
                        '.jpg': 'image/jpeg',
                        '.jpeg': 'image/jpeg',
                        '.png': 'image/png',
                        '.webp': 'image/webp'
                    }.get(ext, 'image/jpeg')
                    image_content = f"data:{mime_type};base64,{image_data}"
            except Exception as e:
                result["_warning"] = f"❌ Не удалось прочитать файл изображения: {str(e)[:100]}"
                return result
        else:
            image_content = image_path_or_url
        
        # Отправляем запрос в OpenAI Vision API с retry логикой
        max_retries = 3
        retry_count = 0
        response = None
        
        while retry_count < max_retries:
            try:
                response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": prompt},
                                {
                                    "type": "image_url",
                                    "image_url": {"url": image_content}
                                }
                            ]
                        }
                    ],
                    max_tokens=300
                )
                break
            except openai.APITimeoutError as timeout_err:
                retry_count += 1
                if retry_count < max_retries:
                    wait_time = (2 ** (retry_count - 1)) * 5
                    time.sleep(wait_time)
                    continue
                else:
                    raise Exception(f"APITimeoutError: Превышено время ожидания после {max_retries} попыток: {str(timeout_err)}")
            except openai.RateLimitError as e:
                raise Exception(f"Rate limit error: {str(e)}")
            except openai.APIError as e:
                error_str = str(e)
                if "429" in error_str or "rate limit" in error_str.lower() or "too many requests" in error_str.lower():
                    raise Exception(f"Rate limit error: {error_str}")
                # Пробуем альтернативную модель
                try:
                    response = client.chat.completions.create(
                        model="gpt-4-turbo",
                        messages=[
                            {
                                "role": "user",
                                "content": [
                                    {"type": "text", "text": prompt},
                                    {
                                        "type": "image_url",
                                        "image_url": {"url": image_content}
                                    }
                                ]
                            }
                        ],
                        max_tokens=300
                    )
                    break
                except openai.APITimeoutError as timeout_err:
                    retry_count += 1
                    if retry_count < max_retries:
                        wait_time = (2 ** (retry_count - 1)) * 5
                        time.sleep(wait_time)
                        continue
                    else:
                        raise Exception(f"APITimeoutError: Превышено время ожидания после {max_retries} попыток: {str(timeout_err)}")
                except openai.RateLimitError as rate_err:
                    raise Exception(f"Rate limit error: {str(rate_err)}")
                except openai.APIError as api_err:
                    error_str = str(api_err)
                    if "429" in error_str or "rate limit" in error_str.lower() or "too many requests" in error_str.lower():
                        raise Exception(f"Rate limit error: {error_str}")
                    raise e
                except Exception:
                    raise e
        
        if response is None:
            raise Exception("Не удалось получить ответ от API после всех попыток")
        
        response_text = response.choices[0].message.content
        result["_debug_response"] = response_text
        
        # Парсим JSON из ответа
        json_start = response_text.find('{')
        json_end = response_text.rfind('}') + 1
        
        if json_start >= 0 and json_end > json_start:
            json_str = response_text[json_start:json_end]
            try:
                parsed_params = json.loads(json_str)
                
                if param_options:
                    for param_name in param_options.keys():
                        if param_name not in parsed_params:
                            parsed_params[param_name] = ""
                
                for key, value in parsed_params.items():
                    if param_options and len(param_options) > 0 and key not in param_options:
                        continue
                    
                    if value is not None:
                        value_clean = str(value).strip()
                    else:
                        value_clean = ""
                    
                    if value_clean:
                        if param_options and key in param_options and param_options[key]:
                            exact_match = None
                            for option in param_options[key]:
                                if option.lower() == value_clean.lower():
                                    exact_match = option
                                    break
                            
                            if exact_match:
                                result["params"][key] = exact_match
                            else:
                                partial_match = None
                                value_lower = value_clean.lower()
                                for option in param_options[key]:
                                    option_lower = option.lower()
                                    if value_lower in option_lower or option_lower in value_lower:
                                        partial_match = option
                                        break
                                
                                if partial_match:
                                    result["params"][key] = partial_match
                                else:
                                    result["params"][key] = value_clean
                        else:
                            result["params"][key] = value_clean
            except json.JSONDecodeError:
                # Пытаемся извлечь параметры вручную через регулярные выражения
                param_names_to_extract = list(param_options.keys()) if param_options else ["Цвет", "Стиль", "Материал", "Длина"]
                for param_name in param_names_to_extract:
                    pattern = f'"{param_name}"\\s*:\\s*"([^"]+)"'
                    match = re.search(pattern, response_text, re.IGNORECASE)
                    if match:
                        value = match.group(1).strip()
                        if value:
                            if param_name in param_options and param_options[param_name]:
                                for option in param_options[param_name]:
                                    if option.lower() == value.lower():
                                        result["params"][param_name] = option
                                        break
                            else:
                                result["params"][param_name] = value
        else:
            # Если не нашли JSON, пытаемся извлечь параметры другим способом
            param_names_to_extract = list(param_options.keys()) if param_options else ["Цвет", "Стиль", "Материал", "Длина"]
            for param_name in param_names_to_extract:
                patterns = [
                    f'{param_name}\\s*[:=]\\s*"([^"]+)"',
                    f'{param_name}\\s*[:=]\\s*([А-Яа-яA-Za-z\\-]+)',
                ]
                for pattern in patterns:
                    match = re.search(pattern, response_text, re.IGNORECASE)
                    if match:
                        value = match.group(1).strip()
                        if value and len(value) < 50:
                            if param_name in param_options and param_options[param_name]:
                                for option in param_options[param_name]:
                                    if option.lower() == value.lower() or value.lower() in option.lower():
                                        result["params"][param_name] = option
                                        break
                            else:
                                result["params"][param_name] = value
                        break
        
    except Exception as e:
        # Пробрасываем исключение с информацией для обёртки
        raise e
    
    return result


def analyze_reviews_with_ai_core(
    comments: list,
    advantages: list,
    disadvantages: list,
    api_key: str,
    max_items: int = 200
) -> dict:
    """
    Анализирует отзывы (комментарии/достоинства/недостатки) и возвращает проценты по темам.
    """
    if not OPENAI_AVAILABLE:
        return {"error": "OpenAI не доступен. Установите библиотеку openai для использования этой функции."}
    if not api_key:
        return {"error": "API ключ OpenAI не указан."}

    try:
        client = openai.OpenAI(api_key=api_key)
        def _clean(items):
            out = []
            for it in items:
                if it is None:
                    continue
                txt = str(it).strip()
                if not txt or txt.lower() in ["nan", "none", "-"]:
                    continue
                out.append(txt)
            return out[:max_items]

        comments = _clean(comments)
        advantages = _clean(advantages)
        disadvantages = _clean(disadvantages)

        prompt = (
            "Ты аналитик отзывов маркетплейса. Проанализируй текст отзывов и выдели "
            "основные положительные и отрицательные стороны, а также их долю в процентах.\n"
            "Верни строго JSON вида:\n"
            "{"
            "\"positive\":[{\"topic\":\"...\",\"percent\":12.3}],"
            "\"negative\":[{\"topic\":\"...\",\"percent\":9.1}],"
            "\"improvements\":[\"...\",\"...\"],"
            "\"summary\":\"краткий вывод\""
            "}\n"
            "Правила:\n"
            "- Проценты должны быть от 0 до 100.\n"
            "- Сумма positive может быть меньше 100, так же для negative.\n"
            "- Не упоминай оценки, анализируй только тексты.\n"
            "- В improvements дай 3-5 конкретных улучшений, что исправить, чтобы стать конкурентнее.\n"
            "- Пиши по-русски.\n\n"
            "Тексты:\n"
            f"Комментарии:\n{chr(10).join(comments)}\n\n"
            f"Достоинства:\n{chr(10).join(advantages)}\n\n"
            f"Недостатки:\n{chr(10).join(disadvantages)}\n"
        )

        response = client.responses.create(
            model="gpt-4.1-mini",
            input=prompt,
            temperature=0.2
        )
        raw_text = response.output_text if hasattr(response, "output_text") else ""
        try:
            return json.loads(raw_text)
        except Exception:
            # пробуем извлечь JSON из текста
            try:
                match = re.search(r"\{.*\}", raw_text, re.DOTALL)
                if match:
                    return json.loads(match.group(0))
            except Exception:
                pass
            return {"error": "Не удалось разобрать ответ ИИ", "raw_response": raw_text}
    except Exception as e:
        return {"error": f"Ошибка анализа отзывов: {e}"}


def analyze_marketing_images_with_ai_core(
    image_paths: list,
    api_key: str,
    product_name: str = None
) -> dict:
    """
    Анализирует главные фото конкурентов и дает рекомендации по маркетингу.
    """
    if not OPENAI_AVAILABLE:
        return {"error": "OpenAI не доступен. Установите библиотеку openai для использования этой функции."}
    if not api_key:
        return {"error": "API ключ OpenAI не указан."}
    if not image_paths:
        return {"error": "Нет изображений для анализа."}

    try:
        client = openai.OpenAI(api_key=api_key)
        image_contents = []
        for img_path in image_paths:
            try:
                with open(img_path, 'rb') as image_file:
                    image_bytes = image_file.read()
                    image_data = base64.b64encode(image_bytes).decode('utf-8')
                    ext = os.path.splitext(img_path)[1].lower()
                    mime_type = {
                        '.jpg': 'image/jpeg',
                        '.jpeg': 'image/jpeg',
                        '.png': 'image/png',
                        '.webp': 'image/webp'
                    }.get(ext, 'image/jpeg')
                    image_contents.append({
                        "type": "input_image",
                        "image_url": f"data:{mime_type};base64,{image_data}"
                    })
            except Exception:
                continue

        if not image_contents:
            return {"error": "Не удалось подготовить изображения."}

        prompt = (
            "Ты профессиональный маркетолог для маркетплейса. Проанализируй главные фото конкурентов "
            "и дай рекомендации как конкурировать. Скажи, как бы ты выделялся среди конкурентов.\n"
            "Ответ верни строго JSON:\n"
            "{"
            "\"insights\":[\"...\"],"
            "\"color_scheme\":[\"...\"],"
            "\"positioning\":[\"...\"],"
            "\"expert_opinion\":\"...\","
            "\"designer_opinion\":\"...\","
            "\"summary\":\"краткий вывод\""
            "}\n"
            "Правила:\n"
            "- Опиши, что улучшить в визуале карточки.\n"
            "- Дай рекомендации по цветовой схеме для продукта: как отличаться от конкурентов, но оставаться в тематике продукта.\n"
            "- Поле expert_opinion должно быть минимум 1000 символов.\n"
            "- Поле designer_opinion должно быть минимум 500 символов.\n"
            "- Пиши по-русски.\n"
        )
        if product_name:
            prompt += f"\nПродукт: {product_name}\n"

        response = client.responses.create(
            model="gpt-4.1-mini",
            input=[
                {"role": "user", "content": [{"type": "input_text", "text": prompt}, *image_contents]}
            ],
            temperature=0.2
        )
        raw_text = response.output_text if hasattr(response, "output_text") else ""
        try:
            return json.loads(raw_text)
        except Exception:
            try:
                match = re.search(r"\{.*\}", raw_text, re.DOTALL)
                if match:
                    return json.loads(match.group(0))
            except Exception:
                pass
            return {"error": "Не удалось разобрать ответ ИИ", "raw_response": raw_text}
    except Exception as e:
        return {"error": f"Ошибка анализа изображений: {e}"}

















