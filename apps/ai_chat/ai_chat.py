# -*- coding: utf-8 -*-
"""
ИИчат - Автоматический анализ товаров с чат-интерфейсом
Автоматически загружает данные, выполняет весь анализ и предоставляет чат для обсуждения результатов
"""
import os
import sys
from pathlib import Path

# Добавляем корневую директорию проекта в sys.path
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import json
import pandas as pd
import numpy as np
import streamlit as st
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# Импорт из локальных модулей utils
from utils.calculations import calculate_unit_economics, calculate_daily_profit
from utils.data_processing import (
    read_table as read_table_base, get_file_statistics, get_analysis_period
)
from utils.reports import find_and_load_reports_from_tovar
from utils.ai_analysis import (
    analyze_combination_products_with_ai_core,
    analyze_wgsn_trends_with_ai_core
)

# Импорт OpenAI
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

# Импорт httpx для прокси (опционально)
try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False

# Настройка страницы
st.set_page_config(
    page_title="ИИчат — Анализ товаров",
    page_icon="💬",
    layout="wide"
)

# ==================== ФУНКЦИИ АВТОМАТИЧЕСКОЙ ИНИЦИАЛИЗАЦИИ ====================

def auto_load_file(file_path):
    """Автоматически загружает файл Excel"""
    if not os.path.exists(file_path):
        return None, None, None
    
    with open(file_path, "rb") as f:
        file_data = f.read()
    
    df, df_raw, metadata = read_table_base(file_data, file_path)
    return df, df_raw, metadata


def run_auto_analytics_analysis(df, report_end_date=None):
    """
    Автоматически запускает анализ параметров (код из вкладки "Аналитика по параметрам")
    Создает топ комбинации товаров
    """
    if df is None or df.empty:
        return []
    
    # Получаем параметры из session_state или используем значения по умолчанию
    spp = st.session_state.get("spp", 25)
    buyout_pct = st.session_state.get("buyout_pct", 25)
    
    # Получаем все параметры из колонок (кроме основных)
    main_cols = ["Артикул", "URL", "Статус", "Параметры", "Выручка", "Заказы", 
                 "Средняя цена", "Позиция в выдаче", "Дата создания", "Упущенная выручка",
                 "Изображение", "Ссылка", "Выкупы", "Продажи", "Средняя цена без СПП",
                 "Цена (с СПП)", "Прибыль", "Стоимость за 1000 показов"]
    
    param_cols = [col for col in df.columns if col not in main_cols]
    
    if not param_cols:
        return []
    
    # Группируем товары по комбинациям параметров
    all_combinations_dict = {}
    
    for _, row in df.iterrows():
        combo_parts = []
        for param in param_cols:
            value = row.get(param)
            if pd.notna(value) and str(value).strip():
                combo_parts.append(f"{param}:{str(value).strip()}")
        
        if combo_parts:
            combo_str = " | ".join(sorted(combo_parts))  # Сортируем для единообразия
            sku = str(row.get("Артикул", "")).replace(".0", "")
            
            if combo_str not in all_combinations_dict:
                all_combinations_dict[combo_str] = []
            all_combinations_dict[combo_str].append(sku)
    
    # Группируем по комбинациям (уже отсортированы)
    from collections import defaultdict
    regrouped_combinations = defaultdict(lambda: {"skus": [], "original_combos": []})
    
    for combo_str, skus in all_combinations_dict.items():
        regrouped_combinations[combo_str]["skus"].extend(skus)
    
    # Пересчитываем метрики
    regrouped_analytics = []
    cleaned_combo_to_skus = {}
    
    for cleaned_combo_str, combo_data in regrouped_combinations.items():
        skus = list(set(combo_data["skus"]))  # Убираем дубликаты
        if not skus:
            continue
        
        cleaned_combo_to_skus[cleaned_combo_str] = skus
        
        mask = df["Артикул"].astype(str).str.replace(".0", "").isin(skus)
        filtered_df = df[mask]
        
        if not filtered_df.empty:
            total_revenue = filtered_df["Выручка"].sum() if "Выручка" in filtered_df.columns else 0
            total_orders = filtered_df["Заказы"].sum() if "Заказы" in filtered_df.columns else 0
            avg_price = filtered_df["Средняя цена"].mean() if "Средняя цена" in filtered_df.columns else 0
            lost_revenue = filtered_df["Упущенная выручка"].sum() if "Упущенная выручка" in filtered_df.columns else 0
            avg_position = filtered_df["Позиция в выдаче"].mean() if "Позиция в выдаче" in filtered_df.columns else 0
            avg_cpm = filtered_df["Стоимость за 1000 показов"].mean() if "Стоимость за 1000 показов" in filtered_df.columns else 0
            
            revenue_per_product = total_revenue / len(filtered_df) if len(filtered_df) > 0 else 0
            lost_revenue_per_product = lost_revenue / len(filtered_df) if len(filtered_df) > 0 else 0
            cpm_per_product = avg_cpm / len(filtered_df) if len(filtered_df) > 0 else 0
            
            # Применяем СПП
            avg_price_without_spp = avg_price / (1 - float(spp) / 100.0) if float(spp) < 100 else avg_price
            
            regrouped_analytics.append({
                "Комбинация": cleaned_combo_str,
                "Количество артикулов": len(filtered_df),
                "Общая выручка": total_revenue,
                "Выручка на 1 артикул": revenue_per_product,
                "Средняя цена без СПП": avg_price_without_spp,
                "Упущенная выручка": lost_revenue,
                "Упущенная выручка на 1 артикул": lost_revenue_per_product,
                "Позиция в выдаче (средняя)": avg_position,
                "Стоимость за 1000 показов на 1 артикул": cpm_per_product
            })
    
    # Рассчитываем рейтинг
    if regrouped_analytics:
        all_revenues = [c["Выручка на 1 артикул"] for c in regrouped_analytics]
        all_prices = [c["Средняя цена без СПП"] for c in regrouped_analytics]
        all_lost = [c["Упущенная выручка на 1 артикул"] for c in regrouped_analytics]
        
        def calculate_score(combo):
            revenue = combo["Выручка на 1 артикул"]
            price = combo["Средняя цена без СПП"]
            lost = combo["Упущенная выручка на 1 артикул"]
            
            if max(all_revenues) > min(all_revenues):
                norm_revenue = (revenue - min(all_revenues)) / (max(all_revenues) - min(all_revenues))
            else:
                norm_revenue = 0.5
            
            if max(all_prices) > min(all_prices):
                norm_price = (price - min(all_prices)) / (max(all_prices) - min(all_prices))
            else:
                norm_price = 0.5
            
            if max(all_lost) > min(all_lost):
                norm_lost = 1 - (lost - min(all_lost)) / (max(all_lost) - min(all_lost))
            else:
                norm_lost = 0.5
            
            score = (norm_revenue * 0.9) + (norm_price * 0.09) + (norm_lost * 0.01)
            return score
        
        for combo in regrouped_analytics:
            combo["Рейтинг"] = calculate_score(combo)
        
        regrouped_analytics.sort(key=lambda x: x["Рейтинг"], reverse=True)
    
    # Сохраняем результаты
    top_10_combinations = regrouped_analytics[:10]
    
    st.session_state['top_10_combinations'] = top_10_combinations
    st.session_state['top_10_novelty_combinations'] = []  # Для совместимости
    st.session_state['top_10_regular_combinations'] = top_10_combinations  # Для совместимости
    st.session_state['cleaned_combo_to_skus'] = cleaned_combo_to_skus
    st.session_state['all_combinations'] = all_combinations_dict
    
    return top_10_combinations


def run_auto_sales_plan(combo_key, combo_skus):
    """Автоматически создает план продаж для комбинации"""
    if not combo_skus:
        return
    
    combo_report_key = f"report_{combo_key}"
    
    # Инициализация
    if 'combination_reports' not in st.session_state:
        st.session_state['combination_reports'] = {}
    
    # Автоматически загружаем отчеты из папки Tovar
    combo_skus_list = [str(sku).replace(".0", "") for sku in combo_skus]
    found_reports = find_and_load_reports_from_tovar(tuple(combo_skus_list), "Tovar")
    
    if found_reports:
        all_reports_data = []
        loaded_skus = []
        
        for sku, report_info in found_reports.items():
            data = report_info['data'].copy()
            data['Артикул'] = sku
            all_reports_data.append(data)
            loaded_skus.append(sku)
        
        if all_reports_data:
            combined_data = pd.concat(all_reports_data, ignore_index=True)
            
            # Группируем по дате
            aggregated_data = combined_data.groupby('Дата').agg({
                'Заказы': 'sum',
                'Продажи': 'sum',
                'Средняя цена': 'mean'
            }).reset_index()
            
            # Сохраняем
            st.session_state['combination_reports'][combo_report_key] = {
                'data': aggregated_data,
                'combination': combo_key,
                'filename': f"Автоматически загружено из Tovar ({len(found_reports)} отчетов)",
                'source': 'auto_tovar',
                'loaded_skus': loaded_skus
            }


def find_data_file():
    """Ищет файл данных в разных возможных местах"""
    file_name = "Рашгард мужской с 1 января по 16 сентября.xlsx"
    
    # Получаем project_root из глобальной переменной
    project_root = Path(__file__).parent.parent.parent
    
    possible_paths = [
        file_name,  # Текущая директория
        os.path.join(str(project_root), file_name),  # Корень проекта
        os.path.join(str(project_root), "data", file_name),  # Папка data
        os.path.join(str(project_root.parent), file_name),  # Родительская директория
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            return path
    
    return None


def auto_initialize_all_data(file_path=None):
    """
    Автоматически выполняет весь анализ:
    1. Загружает файл
    2. Обрабатывает данные
    3. Формирует топ комбинации
    4. Создает планы продаж для топ комбинаций
    """
    
    if 'auto_init_complete' in st.session_state:
        return True
    
    # Ищем файл, если путь не указан
    if file_path is None:
        file_path = find_data_file()
    
    if file_path is None or not os.path.exists(file_path):
        return False
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    # Шаг 1: Загрузка файла
    status_text.text("📂 Загрузка файла...")
    progress_bar.progress(10)
    
    df, df_raw, metadata = auto_load_file(file_path)
    
    if df is None:
        st.error(f"❌ Не удалось загрузить файл: {file_path}")
        return False
    
    st.session_state['df'] = df
    st.session_state['df_raw'] = df_raw
    st.session_state['file_name'] = os.path.basename(file_path)
    st.session_state['spp'] = 25
    st.session_state['buyout_pct'] = 25
    
    # Шаг 2: Анализ параметров
    status_text.text("📊 Анализ параметров и формирование комбинаций...")
    progress_bar.progress(30)
    
    top_combos = run_auto_analytics_analysis(df)
    
    if not top_combos:
        st.warning("⚠️ Не удалось сформировать комбинации")
        return False
    
    # Шаг 3: Создание планов продаж для топ-3
    status_text.text("📈 Создание планов продаж...")
    progress_bar.progress(60)
    
    cleaned_combo_to_skus = st.session_state.get('cleaned_combo_to_skus', {})
    
    for i, combo in enumerate(top_combos[:3], 1):
        combo_key = combo.get('Комбинация', '')
        combo_skus = cleaned_combo_to_skus.get(combo_key, [])
        run_auto_sales_plan(combo_key, combo_skus)
        progress_bar.progress(60 + (i * 10))
    
    # Шаг 4: Завершение
    status_text.text("✅ Инициализация завершена!")
    progress_bar.progress(100)
    
    st.session_state['auto_init_complete'] = True
    
    # Очищаем прогресс-бар
    progress_bar.empty()
    status_text.empty()
    
    return True


# ==================== ФУНКЦИИ ДЛЯ ЧАТА ====================

def collect_all_data_context():
    """Собирает все обработанные данные для контекста ИИ"""
    context = {
        'df': st.session_state.get('df'),
        'file_name': st.session_state.get('file_name', ''),
        'total_products': len(st.session_state.get('df', [])) if st.session_state.get('df') is not None else 0,
        'top_combinations': st.session_state.get('top_10_combinations', []),
        'combo_to_skus': st.session_state.get('cleaned_combo_to_skus', {}),
        'sales_plans': {},
        'plan_details': {},
        'settings': {
            'spp': st.session_state.get('spp', 25),
            'buyout_pct': st.session_state.get('buyout_pct', 25),
        }
    }
    
    # Собираем данные о планах продаж
    combination_reports = st.session_state.get('combination_reports', {})
    for combo_key, report_data in combination_reports.items():
        context['sales_plans'][combo_key] = {
            'data': report_data.get('data'),
            'filename': report_data.get('filename', ''),
            'source': report_data.get('source', '')
        }
        
        plan_details_key = f'plan_details_table_{combo_key.replace("report_", "")}'
        if plan_details_key in st.session_state:
            context['plan_details'][combo_key] = st.session_state[plan_details_key]
    
    return context


def generate_welcome_message(context):
    """Генерирует приветственное сообщение с полной статистикой"""
    msg = "👋 **Добро пожаловать в ИИчат! Все данные проанализированы.**\n\n"
    
    msg += f"📊 **Общая статистика:**\n"
    msg += f"- Товаров в базе: **{context['total_products']}**\n"
    msg += f"- Топ комбинаций найдено: **{len(context['top_combinations'])}**\n"
    msg += f"- Файл данных: {context['file_name']}\n\n"
    
    if context['top_combinations']:
        msg += "🏆 **Топ-3 комбинации товаров:**\n\n"
        for i, combo in enumerate(context['top_combinations'][:3], 1):
            msg += f"**{i}. {combo.get('Комбинация', '')[:60]}...**\n"
            msg += f"   💰 Выручка: {combo.get('Выручка на 1 артикул', 0):,.0f} ₽/артикул\n"
            msg += f"   📦 Товаров: {combo.get('Количество артикулов', 0)}\n"
            msg += f"   ⭐ Рейтинг: {combo.get('Рейтинг', 0):.3f}\n\n"
    
    msg += "💬 **Что вы можете спросить:**\n"
    msg += "- Где лучше продавать товары из топ-комбинации?\n"
    msg += "- Какие перспективы у конкретной комбинации?\n"
    msg += "- Какой план продаж для лучшей комбинации?\n"
    msg += "- Какие рекомендации по улучшению продаж?\n"
    msg += "- Сравни комбинации между собой\n"
    msg += "- Рассчитай заказ для комбинации\n"
    
    return msg


def generate_comprehensive_ai_response(user_question, context, chat_history):
    """Генерирует ответ ИИ на основе ВСЕХ обработанных данных"""
    
    if not OPENAI_AVAILABLE:
        return "⚠️ OpenAI не установлен. Установите: `pip install openai`"
    
    api_key = st.session_state.get('openai_api_key', '')
    if not api_key:
        # Пробуем получить из secrets
        try:
            api_key = st.secrets.get('openai_api_key', '')
        except:
            pass
    
    if not api_key:
        return "⚠️ OpenAI API ключ не настроен. Укажите ключ в боковой панели."
    
    # Формируем промпт с полным контекстом
    system_prompt = """Ты эксперт-аналитик по товарам Wildberries. У тебя есть полный анализ данных:
- Топ комбинации товаров с рейтингами
- Планы продаж (низкий, средний, высокий)
- Расчеты заказов
- ИИ-анализ комбинаций

Отвечай на русском языке, давай конкретные рекомендации с цифрами и фактами из данных."""
    
    # Формируем контекст данных
    data_context = f"""
ДАННЫЕ ДЛЯ АНАЛИЗА:

1. ОБЩАЯ СТАТИСТИКА:
- Всего товаров: {context['total_products']}
- Файл: {context['file_name']}
- Топ комбинаций найдено: {len(context['top_combinations'])}

2. ТОП-5 КОМБИНАЦИЙ ТОВАРОВ:
"""
    
    for i, combo in enumerate(context['top_combinations'][:5], 1):
        data_context += f"""
{i}. {combo.get('Комбинация', '')}
   - Выручка на артикул: {combo.get('Выручка на 1 артикул', 0):,.0f} ₽
   - Количество товаров: {combo.get('Количество артикулов', 0)}
   - Рейтинг: {combo.get('Рейтинг', 0):.3f}
   - Средняя цена без СПП: {combo.get('Средняя цена без СПП', 0):,.0f} ₽
   - Упущенная выручка на артикул: {combo.get('Упущенная выручка на 1 артикул', 0):,.0f} ₽
"""
        
        # Добавляем информацию о плане продаж, если есть
        combo_key = combo.get('Комбинация', '')
        plan_key = f"report_{combo_key}"
        if plan_key in context['sales_plans']:
            plan_data = context['sales_plans'][plan_key]
            plan_df = plan_data.get('data')
            if plan_df is not None and not plan_df.empty:
                total_orders = plan_df['Заказы'].sum() if 'Заказы' in plan_df.columns else 0
                total_sales = plan_df['Продажи'].sum() if 'Продажи' in plan_df.columns else 0
                avg_price_plan = plan_df['Средняя цена'].mean() if 'Средняя цена' in plan_df.columns else 0
                data_context += f"   - План продаж: загружен ({plan_data.get('filename', 'N/A')})\n"
                data_context += f"     * Заказов в отчете: {total_orders:,.0f} шт\n"
                data_context += f"     * Продаж в отчете: {total_sales:,.0f} шт\n"
                if avg_price_plan > 0:
                    data_context += f"     * Средняя цена: {avg_price_plan:,.0f} ₽\n"
        
        # Добавляем артикулы комбинации
        if combo_key in context['combo_to_skus']:
            skus = context['combo_to_skus'][combo_key]
            data_context += f"   - Артикулов в комбинации: {len(skus)}\n"
            if len(skus) <= 10:
                data_context += f"     * Артикулы: {', '.join(skus[:10])}\n"
    
    user_prompt = f"{data_context}\n\nВОПРОС ПОЛЬЗОВАТЕЛЯ: {user_question}\n\nДай детальный ответ с конкретными рекомендациями на основе предоставленных данных."
    
    # Получаем настройки прокси
    proxy_url = st.session_state.get('openai_proxy_url', '')
    if not proxy_url:
        try:
            proxy_url = st.secrets.get('openai_proxy_url', '')
        except:
            pass
    
    # Вызываем ИИ
    try:
        # Создаем клиент OpenAI с прокси, если указан
        client_kwargs = {"api_key": api_key}
        if proxy_url:
            # Поддержка прокси через http_client
            if not HTTPX_AVAILABLE:
                return "❌ Для использования прокси необходимо установить httpx: `pip install httpx`"
            
            client_kwargs["http_client"] = httpx.Client(
                proxies=proxy_url,
                timeout=60.0
            )
        
        client = openai.OpenAI(**client_kwargs)
        
        # Формируем историю сообщений (последние 10 для контекста)
        messages = [
            {"role": "system", "content": system_prompt}
        ]
        
        # Добавляем последние сообщения из истории
        for msg in chat_history[-10:]:
            messages.append({
                "role": msg["role"],
                "content": msg["content"]
            })
        
        messages.append({"role": "user", "content": user_prompt})
        
        response = client.chat.completions.create(
            model="gpt-4",
            messages=messages,
            temperature=0.7,
            max_tokens=2000
        )
        
        return response.choices[0].message.content
        
    except openai.APIError as e:
        error_code = getattr(e, 'status_code', None)
        error_body = getattr(e, 'body', {})
        
        # Обработка ошибки 403 (недоступен регион)
        if error_code == 403:
            error_msg = error_body.get('error', {}).get('message', '') if isinstance(error_body, dict) else str(e)
            if 'country' in error_msg.lower() or 'region' in error_msg.lower() or 'territory' in error_msg.lower():
                return f"""❌ **Ошибка доступа к OpenAI API (403)**

OpenAI API недоступен в вашем регионе.

**Решения:**
1. **Использовать прокси**: Укажите прокси-сервер в настройках (боковая панель → Прокси для OpenAI)
   - Формат: `http://user:pass@proxy.example.com:port` или `socks5://user:pass@proxy.example.com:port`
   - Или просто `http://proxy.example.com:port` если без авторизации

2. **Альтернативные варианты:**
   - Использовать VPN с поддержкой OpenAI
   - Использовать прокси-сервисы, которые поддерживают OpenAI API
   - Использовать альтернативные LLM API (YandexGPT, DeepSeek и т.д.)

**Текущая ошибка:** {error_msg}"""
        
        # Общая обработка ошибок API
        return f"❌ **Ошибка OpenAI API ({error_code or 'unknown'})**: {str(e)}"
    
    except Exception as e:
        error_str = str(e)
        # Проверяем, есть ли в ошибке упоминание о регионе
        if '403' in error_str and ('country' in error_str.lower() or 'region' in error_str.lower()):
            return f"""❌ **Ошибка доступа к OpenAI API (403)**

OpenAI API недоступен в вашем регионе.

**Решения:**
1. **Использовать прокси**: Укажите прокси-сервер в настройках (боковая панель → Прокси для OpenAI)
   - Формат: `http://user:pass@proxy.example.com:port` или `socks5://user:pass@proxy.example.com:port`

2. **Альтернативные варианты:**
   - Использовать VPN с поддержкой OpenAI
   - Использовать прокси-сервисы для OpenAI API

**Детали ошибки:** {error_str}"""
        
        return f"❌ Ошибка при обращении к ИИ: {error_str}"


# ==================== ГЛАВНЫЙ ИНТЕРФЕЙС ====================

def main():
    st.title("💬 ИИчат — Анализ товаров Wildberries")
    st.markdown("Автоматический анализ данных и интеллектуальный чат для обсуждения результатов")
    
    # Боковая панель с настройками
    with st.sidebar:
        st.header("⚙️ Настройки")
        
        # Настройка API ключа OpenAI
        st.subheader("🔑 OpenAI API")
        api_key = st.text_input(
            "API ключ OpenAI:",
            value=st.session_state.get('openai_api_key', ''),
            type="password",
            help="Введите ваш API ключ OpenAI для работы чата"
        )
        
        if api_key:
            st.session_state['openai_api_key'] = api_key
            st.success("✅ API ключ сохранен")
        else:
            # Пробуем получить из secrets
            try:
                default_key = st.secrets.get('openai_api_key', '')
                if default_key:
                    st.session_state['openai_api_key'] = default_key
                    st.info("✅ API ключ загружен из настроек")
            except:
                pass
        
        # Настройка прокси (если OpenAI недоступен в регионе)
        st.subheader("🌐 Прокси для OpenAI")
        st.caption("Требуется, если OpenAI API недоступен в вашем регионе")
        
        proxy_url = st.text_input(
            "URL прокси-сервера:",
            value=st.session_state.get('openai_proxy_url', ''),
            help="Формат: http://user:pass@proxy.example.com:port или socks5://user:pass@proxy.example.com:port"
        )
        
        if proxy_url:
            st.session_state['openai_proxy_url'] = proxy_url
            st.success("✅ Прокси сохранен")
        else:
            # Пробуем получить из secrets
            try:
                default_proxy = st.secrets.get('openai_proxy_url', '')
                if default_proxy:
                    st.session_state['openai_proxy_url'] = default_proxy
                    st.info("✅ Прокси загружен из настроек")
            except:
                pass
        
        # Кнопка очистки прокси
        if proxy_url and st.button("🗑️ Очистить прокси", use_container_width=True):
            st.session_state['openai_proxy_url'] = ''
            st.rerun()
        
        st.divider()
        
        # Информация о данных
        st.subheader("📊 Данные")
        if st.session_state.get('auto_init_complete'):
            st.success("✅ Данные загружены и проанализированы")
            st.caption(f"Файл: {st.session_state.get('file_name', 'N/A')}")
            st.caption(f"Товаров: {len(st.session_state.get('df', []))}")
            st.caption(f"Комбинаций: {len(st.session_state.get('top_10_combinations', []))}")
        else:
            st.info("⏳ Данные не загружены")
        
        st.divider()
        
        # Кнопка перезагрузки данных
        if st.button("🔄 Перезагрузить данные", use_container_width=True):
            if 'auto_init_complete' in st.session_state:
                del st.session_state['auto_init_complete']
            st.rerun()
    
    # Автоматическая инициализация
    if not st.session_state.get('auto_init_complete', False):
        st.info("🔄 Автоматическая инициализация данных...")
        
        init_result = auto_initialize_all_data()
        
        if init_result:
            st.success("✅ Инициализация завершена!")
            st.balloons()
            st.rerun()
        else:
            st.error("❌ Ошибка при инициализации")
            st.markdown("""
            **💡 Инструкция:**
            1. Поместите файл `Рашгард мужской с 1 января по 16 сентября.xlsx` в одну из следующих папок:
               - Корневая директория проекта
               - Папка `data/` в корне проекта
            2. Нажмите кнопку "🔄 Перезагрузить данные" в боковой панели
            """)
            return
    
    # Чат-интерфейс
    if st.session_state.get('auto_init_complete', False):
        # Инициализация истории чата
        if 'main_chat_history' not in st.session_state:
            st.session_state['main_chat_history'] = []
        
        # Собираем контекст данных
        context = collect_all_data_context()
        
        # Отображаем историю чата
        chat_container = st.container()
        with chat_container:
            # Приветственное сообщение (если чат пустой)
            if not st.session_state['main_chat_history']:
                welcome = generate_welcome_message(context)
                st.session_state['main_chat_history'].append({
                    "role": "assistant",
                    "content": welcome
                })
            
            # Показываем все сообщения
            for message in st.session_state['main_chat_history']:
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])
        
        # Поле ввода
        user_input = st.chat_input("Задайте вопрос о товарах, комбинациях, планах продаж...")
        
        if user_input:
            # Добавляем вопрос пользователя
            st.session_state['main_chat_history'].append({
                "role": "user",
                "content": user_input
            })
            
            # Генерируем ответ на основе ВСЕХ данных
            with st.spinner("🤔 Анализирую данные и готовлю ответ..."):
                response = generate_comprehensive_ai_response(
                    user_input,
                    context,
                    st.session_state['main_chat_history']
                )
            
            # Добавляем ответ
            st.session_state['main_chat_history'].append({
                "role": "assistant",
                "content": response
            })
            
            st.rerun()
        
        # Кнопка очистки чата
        col1, col2 = st.columns([1, 4])
        with col1:
            if st.button("🗑️ Очистить чат", use_container_width=True):
                st.session_state['main_chat_history'] = []
                st.rerun()


if __name__ == "__main__":
    main()

