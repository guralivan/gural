# -*- coding: utf-8 -*-
"""
Модуль для чата с ИИ на основе всех данных анализа
"""
import os
import json

# Проверка наличия библиотеки OpenAI
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    openai = None

from .mc_reader import read_mc_files
from .wgsn_reader import read_wgsn_files


def collect_all_analysis_data(session_state: dict) -> str:
    """
    Собирает все данные анализа из session_state для использования в чате.
    
    Args:
        session_state: Словарь session_state Streamlit
        
    Returns:
        Строка с форматированными данными для контекста чата
    """
    context_parts = []
    
    # 1. Анализ комбинаций (топ-3)
    combinations_analysis = session_state.get("combinations_ai_analysis", {})
    if combinations_analysis and "error" not in combinations_analysis:
        context_parts.append("=== АНАЛИЗ КОМБИНАЦИЙ ПАРАМЕТРОВ ===\n")
        
        if "economic_conclusions" in combinations_analysis:
            context_parts.append(f"Экономические выводы: {combinations_analysis['economic_conclusions']}\n")
        
        if "expert_analysis" in combinations_analysis:
            context_parts.append(f"Экспертный анализ: {combinations_analysis['expert_analysis']}\n")
        
        if "best_combinations" in combinations_analysis:
            context_parts.append("\nТоп-3 лучшие комбинации:\n")
            for combo in combinations_analysis["best_combinations"][:3]:
                rank = combo.get("rank", 0)
                combination = combo.get("combination", "N/A")
                why_best = combo.get("why_best", "")
                context_parts.append(f"{rank}. {combination}\n")
                if why_best:
                    context_parts.append(f"   Обоснование: {why_best[:300]}...\n")
        
        if "recommendations" in combinations_analysis:
            rec = combinations_analysis["recommendations"]
            if rec.get("best_to_sell"):
                context_parts.append(f"\nГлавный вывод: {rec['best_to_sell']}\n")
    
    # 2. Анализ WGSN
    wgsn_analysis = session_state.get("wgsn_analysis", {})
    if wgsn_analysis and "error" not in wgsn_analysis:
        context_parts.append("\n=== АНАЛИЗ ТРЕНДОВ WGSN ===\n")
        
        if "wgsn_trends_summary" in wgsn_analysis:
            context_parts.append(f"Резюме трендов: {wgsn_analysis['wgsn_trends_summary']}\n")
        
        if "category_analysis" in wgsn_analysis:
            cat_analysis = wgsn_analysis["category_analysis"]
            if cat_analysis.get("current_trends"):
                context_parts.append(f"Актуальные тренды: {cat_analysis['current_trends']}\n")
    
    # 3. Данные из папки MC
    mc_content = read_mc_files()
    if mc_content and "error" not in mc_content:
        context_parts.append("\n=== ДОПОЛНИТЕЛЬНЫЕ ИССЛЕДОВАНИЯ (MC) ===\n")
        for filename, content in mc_content.items():
            # Ограничиваем размер для контекста
            content_limited = content[:2000] if len(content) > 2000 else content
            context_parts.append(f"Файл {filename}: {content_limited}...\n")
    
    # 4. Данные из папки WGSN (если есть)
    wgsn_content = session_state.get("wgsn_content", {})
    if wgsn_content and "error" not in wgsn_content:
        context_parts.append("\n=== СОДЕРЖИМОЕ ФАЙЛОВ WGSN ===\n")
        for filename, content in list(wgsn_content.items())[:2]:  # Берем первые 2 файла
            content_limited = content[:2000] if len(content) > 2000 else content
            context_parts.append(f"Файл {filename}: {content_limited}...\n")
    
    return "\n".join(context_parts)


def chat_with_ai_core(
    user_message: str,
    chat_history: list,
    context_data: str,
    api_key: str,
    category: str = "Рашрашд мужской (компрессионная одежда)"
) -> dict:
    """
    Отправляет сообщение пользователя в ИИ с контекстом всех данных анализа.
    
    Args:
        user_message: Сообщение пользователя
        chat_history: История чата (список словарей с "role" и "content")
        context_data: Строка с контекстными данными (выводы анализа, WGSN, MC)
        api_key: API ключ OpenAI
        category: Категория товаров
        
    Returns:
        Словарь с ответом ИИ:
            - "response": текст ответа
            - "error": ошибка (если есть)
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
        
        # Формируем системный промпт с контекстом
        system_prompt = f"""Ты эксперт-консультант по анализу товаров и комбинаций параметров в электронной коммерции.
Ты помогаешь пользователю принимать решения на основе данных анализа комбинаций параметров, трендов WGSN и дополнительных исследований.

КОНТЕКСТНЫЕ ДАННЫЕ:
{context_data}

ТВОЯ РОЛЬ:
- Отвечай на вопросы пользователя, основываясь ТОЛЬКО на предоставленных контекстных данных
- Помогай интерпретировать результаты анализа комбинаций
- Давай рекомендации на основе экономического анализа
- Объясняй связи между трендами WGSN и комбинациями параметров
- Используй данные из папок MC и WGSN для более полных ответов
- Будь конкретным и ссылайся на конкретные данные из контекста

ВАЖНО:
- Если в контексте нет информации для ответа, скажи об этом честно
- Не выдумывай данные, которых нет в контексте
- Отвечай на русском языке
- Будь профессиональным и полезным"""
        
        # Формируем историю сообщений
        messages = [
            {"role": "system", "content": system_prompt}
        ]
        
        # Добавляем историю чата (если есть)
        if chat_history:
            messages.extend(chat_history[-10:])  # Берем последние 10 сообщений для контекста
        
        # Добавляем текущее сообщение пользователя
        messages.append({"role": "user", "content": user_message})
        
        # Отправляем запрос в OpenAI
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            max_tokens=2000,
            temperature=0.7
        )
        
        ai_response = response.choices[0].message.content
        
        return {
            "response": ai_response
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
            "error": f"Ошибка при отправке сообщения: {str(e)}"
        }











