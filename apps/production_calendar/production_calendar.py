import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json
import os
import locale

# Настройка локали для русского языка
try:
    locale.setlocale(locale.LC_TIME, 'ru_RU.UTF-8')
except:
    try:
        locale.setlocale(locale.LC_TIME, 'Russian_Russia.1251')
    except:
        pass

# Функция для форматирования дат на русском языке
def format_date_russian(date_str):
    """Форматирует дату в строку с месяцем на русском языке"""
    try:
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        months_ru = {
            1: "января", 2: "февраля", 3: "марта", 4: "апреля",
            5: "мая", 6: "июня", 7: "июля", 8: "августа",
            9: "сентября", 10: "октября", 11: "ноября", 12: "декабря"
        }
        return f"{date_obj.day} {months_ru[date_obj.month]} {date_obj.year}"
    except:
        return date_str

# Настройка страницы
st.set_page_config(
    page_title="Календарь производства и логистики",
    page_icon="📅",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Заголовок приложения
st.title("📅 Календарь производства и логистики")
st.markdown("Планирование производства товаров из Китая с учетом сезонности")

# Боковая панель для настроек
with st.sidebar:
    st.header("⚙️ Настройки по умолчанию")
    
    # Настройки сроков по умолчанию
    default_development_days = st.number_input(
        "Сроки разработки (дни)", 
        min_value=1, 
        max_value=365, 
        value=90,
        help="Стандартное время разработки товара (3 месяца = 90 дней)"
    )
    
    default_production_days = st.number_input(
        "Сроки производства (дни)", 
        min_value=1, 
        max_value=365, 
        value=30,
        help="Стандартное время производства товара"
    )
    
    default_shipping_days = st.number_input(
        "Сроки доставки (дни)", 
        min_value=1, 
        max_value=365, 
        value=15,
        help="Время доставки из Китая в Россию"
    )
    
    default_processing_days = st.number_input(
        "Обработка (дни)", 
        min_value=1, 
        max_value=30, 
        value=3,
        help="Время обработки и подготовки к продаже"
    )
    
    default_wb_days = st.number_input(
        "Поставка на WB (дни)", 
        min_value=1, 
        max_value=30, 
        value=2,
        help="Время доставки на склад Wildberries"
    )
    
    st.divider()
    
    # Сезонные рекомендации
    st.header("🌱 Сезонные рекомендации")
    
    current_month = datetime.now().month
    
    if current_month in [12, 1, 2]:
        season = "Зима"
        recommended_start = "август-сентябрь"
        recommended_dev_start = "май-июнь"
        st.info(f"Текущий сезон: {season}\nРекомендуется начать разработку: {recommended_dev_start}\nРекомендуется начать производство: {recommended_start}")
    elif current_month in [3, 4, 5]:
        season = "Весна"
        recommended_start = "декабрь-январь"
        recommended_dev_start = "сентябрь-октябрь"
        st.info(f"Текущий сезон: {season}\nРекомендуется начать разработку: {recommended_dev_start}\nРекомендуется начать производство: {recommended_start}")
    elif current_month in [6, 7, 8]:
        season = "Лето"
        recommended_start = "март-апрель"
        recommended_dev_start = "декабрь-январь"
        st.info(f"Текущий сезон: {season}\nРекомендуется начать разработку: {recommended_dev_start}\nРекомендуется начать производство: {recommended_start}")
    else:
        season = "Осень"
        recommended_start = "июнь-июль"
        recommended_dev_start = "март-апрель"
        st.info(f"Текущий сезон: {season}\nРекомендуется начать разработку: {recommended_dev_start}\nРекомендуется начать производство: {recommended_start}")

# Основная область приложения
col1, col2 = st.columns([2, 1])

# Функция для загрузки сохраненных данных
def load_saved_data():
    if os.path.exists('production_calendar_data.json'):
        with open('production_calendar_data.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

# Функция для сохранения данных
def save_data(data):
    with open('production_calendar_data.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# Функция миграции для добавления поля разработки и расходов
def migrate_projects(projects):
    """Добавляет поле разработки и расходов к существующим проектам"""
    for project in projects:
        if 'development_start' not in project:
            # Рассчитываем дату начала разработки как 90 дней до начала производства
            production_start = datetime.strptime(project['production_start'], "%Y-%m-%d")
            development_start = production_start - timedelta(days=90)
            development_end = production_start
            
            project['development_start'] = development_start.strftime("%Y-%m-%d")
            project['development_end'] = development_end.strftime("%Y-%m-%d")
            project['development_days'] = 90
        
        # Добавляем поля расходов на разработку
        if 'total_development_cost' not in project:
            project['sample_russia_fabric'] = 0
            project['sample_russia_ready'] = 0
            project['sample_china'] = 0
            project['delivery_china'] = 0
            project['delivery_russia'] = 0
            project['patterns'] = 0
            project['model_3d'] = 0
            project['taxi'] = 0
            project['other_expenses'] = 0
            project['total_development_cost'] = 0
    
    return projects

# Загрузка сохраненных данных
saved_projects = load_saved_data()

# Миграция существующих проектов
if saved_projects:
    saved_projects = migrate_projects(saved_projects)
    save_data(saved_projects) 

with col1:
    st.header("📋 Новый проект")
    
    # Форма для создания нового проекта
    with st.form("new_project_form"):
        project_name = st.text_input("Название проекта/товара", placeholder="Например: Пиджак весенняя коллекция")
        
        col1_1, col1_2 = st.columns(2)
        
        with col1_1:
            development_start = st.date_input(
                "Дата начала разработки",
                value=datetime.now().date(),
                help="Дата начала разработки товара"
            )
            
            development_days = st.number_input(
                "Сроки разработки (дни)",
                min_value=0,
                max_value=365,
                value=default_development_days
            )
            
            # Автоматический расчет даты готовности к продаже
            if development_days > 0:
                development_end_calc = development_start + timedelta(days=development_days)
                production_start_calc = development_end_calc + timedelta(days=1)
                production_end_calc = production_start_calc + timedelta(days=default_production_days)
                shipping_start_calc = production_end_calc + timedelta(days=1)
                arrival_russia_calc = shipping_start_calc + timedelta(days=default_shipping_days)
                processing_start_calc = arrival_russia_calc + timedelta(days=1)
                processing_end_calc = processing_start_calc + timedelta(days=default_processing_days)
                wb_delivery_calc = processing_end_calc + timedelta(days=1)
                ready_for_sale_calc = wb_delivery_calc + timedelta(days=default_wb_days)
            else:
                # Если разработки нет, считаем от текущей даты
                production_start_calc = datetime.now().date() + timedelta(days=1)
                production_end_calc = production_start_calc + timedelta(days=default_production_days)
                shipping_start_calc = production_end_calc + timedelta(days=1)
                arrival_russia_calc = shipping_start_calc + timedelta(days=default_shipping_days)
                processing_start_calc = arrival_russia_calc + timedelta(days=1)
                processing_end_calc = processing_start_calc + timedelta(days=default_processing_days)
                wb_delivery_calc = processing_end_calc + timedelta(days=1)
                ready_for_sale_calc = wb_delivery_calc + timedelta(days=default_wb_days)
            
            # Показываем рассчитанную дату готовности к продаже
            st.info(f"📊 **Автоматический расчет**: Товар будет готов к продаже **{ready_for_sale_calc.strftime('%d.%m.%Y')}**")
            
            # Детальная временная шкала проекта
            with st.expander("📅 Детальная временная шкала проекта", expanded=False):
                if development_days > 0:
                    st.write(f"**📅 Разработка**: {development_start.strftime('%d.%m.%Y')} → {(development_start + timedelta(days=development_days)).strftime('%d.%m.%Y')} ({development_days} дн.)")
                st.write(f"**🏭 Производство**: {production_start_calc.strftime('%d.%m.%Y')} → {(production_start_calc + timedelta(days=default_production_days)).strftime('%d.%m.%Y')} ({default_production_days} дн.)")
                st.write(f"**🚢 Доставка**: {(production_start_calc + timedelta(days=default_production_days + 1)).strftime('%d.%m.%Y')} → {(production_start_calc + timedelta(days=default_production_days + default_shipping_days)).strftime('%d.%m.%Y')} ({default_shipping_days} дн.)")
                st.write(f"**⚙️ Обработка**: {(production_start_calc + timedelta(days=default_production_days + default_shipping_days + 1)).strftime('%d.%m.%Y')} → {(production_start_calc + timedelta(days=default_production_days + default_shipping_days + default_processing_days)).strftime('%d.%m.%Y')} ({default_processing_days} дн.)")
                st.write(f"**📦 Поставка на WB**: {(production_start_calc + timedelta(days=default_production_days + default_shipping_days + default_processing_days + 1)).strftime('%d.%m.%Y')} → {ready_for_sale_calc.strftime('%d.%m.%Y')} ({default_wb_days} дн.)")
                st.write(f"**✅ Готов к продаже**: {ready_for_sale_calc.strftime('%d.%m.%Y')}")
            
            production_start = st.date_input(
                "Дата начала производства",
                value=production_start_calc,
                help="Дата начала производства после разработки"
            )
            
            production_days = st.number_input(
                "Сроки производства (дни)",
                min_value=1,
                max_value=365,
                value=default_production_days
            )
            
            shipping_days = st.number_input(
                "Сроки доставки (дни)",
                min_value=1,
                max_value=365,
                value=default_shipping_days
            )
        
        with col1_2:
            processing_days = st.number_input(
                "Обработка (дни)",
                min_value=1,
                max_value=30,
                value=default_processing_days
            )
            
            wb_days = st.number_input(
                "Поставка на WB (дни)",
                min_value=1,
                max_value=30,
                value=default_wb_days
            )
            
            target_launch = st.date_input(
                "Целевая дата запуска",
                value=ready_for_sale_calc + timedelta(days=7),  # По умолчанию +7 дней после готовности
                help="Желаемая дата поступления товара в продажу"
            ) 
        
        # Расходы на разработку (сворачиваемый раздел)
        with st.expander("💰 Расходы на разработку", expanded=False):
            col_exp1, col_exp2 = st.columns(2)
            
            with col_exp1:
                st.write("**Образцы и материалы:**")
                sample_russia_fabric = st.number_input("Ткань, пуговицы (₽)", min_value=0, value=0, help="Стоимость материалов для образца в России")
                sample_russia_ready = st.number_input("Образец в России готовый (₽)", min_value=0, value=0, help="Стоимость готового образца в России")
                sample_china = st.number_input("Образец в Китае (₽)", min_value=0, value=0, help="Стоимость образца в Китае")
                
                st.write("**Доставка:**")
                delivery_china = st.number_input("Доставка из Китая (₽)", min_value=0, value=0, help="Стоимость доставки образцов из Китая")
                delivery_russia = st.number_input("Доставка по России (₽)", min_value=0, value=0, help="Стоимость доставки по России")
            
            with col_exp2:
                st.write("**Техническая документация:**")
                patterns = st.number_input("Лекала (₽)", min_value=0, value=0, help="Стоимость создания лекал")
                model_3d = st.number_input("3D модель (₽)", min_value=0, value=0, help="Стоимость создания 3D модели")
                
                st.write("**Прочие расходы:**")
                taxi = st.number_input("Такси (₽)", min_value=0, value=0, help="Стоимость поездок на такси")
                other_expenses = st.number_input("Прочие расходы (₽)", min_value=0, value=0, help="Другие расходы на разработку")
            
            # Расчет общих расходов на разработку
            total_development_cost = (
                sample_russia_fabric + sample_russia_ready + sample_china +
                delivery_china + delivery_russia + patterns + model_3d + taxi + other_expenses
            )
            
            st.info(f"**💰 Общие расходы на разработку: {total_development_cost:,} ₽**")
        
        notes = st.text_area("Дополнительные заметки", placeholder="Особенности производства, логистики и т.д.")
        
        submitted = st.form_submit_button("📅 Создать проект", type="primary")
        
        if submitted and project_name:
            # Расчет дат с учетом возможности отсутствия разработки
            if development_days > 0:
                development_end = development_start + timedelta(days=development_days)
                production_end = production_start + timedelta(days=production_days)
            else:
                # Если разработка 0 дней, то производство начинается сразу
                development_end = development_start
                production_end = production_start + timedelta(days=production_days)
            
            shipping_start = production_end
            shipping_end = shipping_start + timedelta(days=shipping_days)
            processing_start = shipping_end
            processing_end = processing_start + timedelta(days=processing_days)
            wb_start = processing_end
            wb_end = wb_start + timedelta(days=wb_days)
            
            # Создание проекта
            new_project = {
                "id": len(saved_projects) + 1,
                "name": project_name,
                "development_start": development_start.strftime("%Y-%m-%d"),
                "development_end": development_end.strftime("%Y-%m-%d"),
                "development_days": development_days,
                "production_start": production_start.strftime("%Y-%m-%d"),
                "production_end": production_end.strftime("%Y-%m-%d"),
                "production_days": production_days,
                "shipping_start": shipping_start.strftime("%Y-%m-%d"),
                "shipping_end": shipping_end.strftime("%Y-%m-%d"),
                "shipping_days": shipping_days,
                "processing_start": processing_start.strftime("%Y-%m-%d"),
                "processing_end": processing_end.strftime("%Y-%m-%d"),
                "processing_days": processing_days,
                "wb_start": wb_start.strftime("%Y-%m-%d"),
                "wb_end": wb_end.strftime("%Y-%m-%d"),
                "wb_days": wb_days,
                "target_launch": target_launch.strftime("%Y-%m-%d"),
                "notes": notes,
                "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                # Расходы на разработку
                "sample_russia_fabric": sample_russia_fabric,
                "sample_russia_ready": sample_russia_ready,
                "sample_china": sample_china,
                "delivery_china": delivery_china,
                "delivery_russia": delivery_russia,
                "patterns": patterns,
                "model_3d": model_3d,
                "taxi": taxi,
                "other_expenses": other_expenses,
                "total_development_cost": total_development_cost
            }
            
            saved_projects.append(new_project)
            save_data(saved_projects)
            st.success(f"Проект '{project_name}' успешно создан!")
            st.rerun() 

# Отображение существующих проектов (перемещено вверх)
if saved_projects:
    st.header("📋 Существующие проекты")
    
    # Проверяем, есть ли проект для редактирования
    editing_project_id = st.session_state.get('editing_project', None)
    editing_project = None
    
    if editing_project_id:
        editing_project = next((p for p in saved_projects if p['id'] == editing_project_id), None)
    
    # Если есть проект для редактирования, показываем форму редактирования
    if editing_project:
        st.subheader(f"✏️ Редактирование проекта: {editing_project['name']}")
        
        with st.form(f"edit_project_form_main_{editing_project['id']}", clear_on_submit=False):
            # Основная информация
            edited_name = st.text_input("Название проекта/товара", value=editing_project['name'])
            
            # Информация о проекте
            st.info(f"📋 **ID проекта**: {editing_project['id']} | 📅 **Создан**: {editing_project.get('created_at', 'Не указано')}")
            
            col_edit1, col_edit2 = st.columns(2)
            
            with col_edit1:
                edited_dev_start = st.date_input(
                    "Дата начала разработки",
                    value=datetime.strptime(editing_project['development_start'], "%Y-%m-%d").date(),
                    key="edit_dev_start"
                )
                
                edited_dev_days = st.number_input(
                    "Сроки разработки (дни)",
                    min_value=0,
                    max_value=365,
                    value=editing_project['development_days'],
                    key="edit_dev_days"
                )
                
                edited_prod_start = st.date_input(
                    "Дата начала производства",
                    value=datetime.strptime(editing_project['production_start'], "%Y-%m-%d").date(),
                    key="edit_prod_start"
                )
                
                edited_prod_days = st.number_input(
                    "Сроки производства (дни)",
                    min_value=1,
                    max_value=365,
                    value=editing_project['production_days'],
                    key="edit_prod_days"
                )
                
                edited_shipping_days = st.number_input(
                    "Сроки доставки (дни)",
                    min_value=1,
                    max_value=365,
                    value=editing_project['shipping_days'],
                    key="edit_shipping_days"
                )
            
            with col_edit2:
                edited_processing_days = st.number_input(
                    "Обработка (дни)",
                    min_value=1,
                    max_value=30,
                    value=editing_project['processing_days'],
                    key="edit_processing_days"
                )
                
                edited_wb_days = st.number_input(
                    "Поставка на WB (дни)",
                    min_value=1,
                    max_value=30,
                    value=editing_project['wb_days'],
                    key="edit_wb_days"
                )
                
                edited_target_launch = st.date_input(
                    "Целевая дата запуска",
                    value=datetime.strptime(editing_project['target_launch'], "%Y-%m-%d").date(),
                    key="edit_target_launch"
                )
            
            # Расходы на разработку
            with st.expander("💰 Расходы на разработку", expanded=False):
                col_edit_exp1, col_edit_exp2 = st.columns(2)
                
                with col_edit_exp1:
                    st.write("**Образцы и материалы:**")
                    edited_sample_russia_fabric = st.number_input(
                        "Ткань, пуговицы (₽)", 
                        min_value=0, 
                        value=editing_project.get('sample_russia_fabric', 0),
                        key="edit_sample_russia_fabric"
                    )
                    edited_sample_russia_ready = st.number_input(
                        "Образец в России готовый (₽)", 
                        min_value=0, 
                        value=editing_project.get('sample_russia_ready', 0),
                        key="edit_sample_russia_ready"
                    )
                    edited_sample_china = st.number_input(
                        "Образец в Китае (₽)", 
                        min_value=0, 
                        value=editing_project.get('sample_china', 0),
                        key="edit_sample_china"
                    )
                    
                    st.write("**Доставка:**")
                    edited_delivery_china = st.number_input(
                        "Доставка из Китая (₽)", 
                        min_value=0, 
                        value=editing_project.get('delivery_china', 0),
                        key="edit_delivery_china"
                    )
                    edited_delivery_russia = st.number_input(
                        "Доставка по России (₽)", 
                        min_value=0, 
                        value=editing_project.get('delivery_russia', 0),
                        key="edit_delivery_russia"
                    )
                
                with col_edit_exp2:
                    st.write("**Техническая документация:**")
                    edited_patterns = st.number_input(
                        "Лекала (₽)", 
                        min_value=0, 
                        value=editing_project.get('patterns', 0),
                        key="edit_patterns"
                    )
                    edited_model_3d = st.number_input(
                        "3D модель (₽)", 
                        min_value=0, 
                        value=editing_project.get('model_3d', 0),
                        key="edit_model_3d"
                    )
                    
                    st.write("**Прочие расходы:**")
                    edited_taxi = st.number_input(
                        "Такси (₽)", 
                        min_value=0, 
                        value=editing_project.get('taxi', 0),
                        key="edit_taxi"
                    )
                    edited_other_expenses = st.number_input(
                        "Прочие расходы (₽)", 
                        min_value=0, 
                        value=editing_project.get('other_expenses', 0),
                        key="edit_other_expenses"
                    )
                
                # Расчет общих расходов на разработку
                edited_total_development_cost = (
                    edited_sample_russia_fabric + edited_sample_russia_ready + edited_sample_china +
                    edited_delivery_china + edited_delivery_russia + edited_patterns + 
                    edited_model_3d + edited_taxi + edited_other_expenses
                )
                
                st.info(f"**💰 Общие расходы на разработку: {edited_total_development_cost:,} ₽**")
            
            edited_notes = st.text_area(
                "Дополнительные заметки", 
                value=editing_project.get('notes', ''),
                key="edit_notes"
            )
            
            # Автоматический расчет и отображение дат в реальном времени
            st.markdown("---")
            st.subheader("📅 Предварительный просмотр дат")
            
            # Расчет дат на основе текущих значений (правильный расчет: день начала считается, поэтому -1)
            if edited_dev_days > 0:
                calc_dev_end = edited_dev_start + timedelta(days=edited_dev_days - 1)
                calc_prod_start = calc_dev_end + timedelta(days=1)
            else:
                calc_dev_end = edited_dev_start
                calc_prod_start = edited_prod_start if edited_prod_start > edited_dev_start else edited_dev_start + timedelta(days=1)
            
            calc_prod_end = edited_prod_start + timedelta(days=edited_prod_days - 1)
            calc_shipping_start = calc_prod_end + timedelta(days=1)
            calc_shipping_end = calc_shipping_start + timedelta(days=edited_shipping_days - 1)
            calc_processing_start = calc_shipping_end + timedelta(days=1)
            calc_processing_end = calc_processing_start + timedelta(days=edited_processing_days - 1)
            calc_wb_start = calc_processing_end + timedelta(days=1)
            calc_wb_end = calc_wb_start + timedelta(days=edited_wb_days - 1)
            
            # Отображение предварительного просмотра
            col_preview1, col_preview2 = st.columns(2)
            with col_preview1:
                if edited_dev_days > 0:
                    st.write(f"**🔬 Разработка**: {edited_dev_start.strftime('%d.%m.%Y')} → {calc_dev_end.strftime('%d.%m.%Y')} ({edited_dev_days} дн.)")
                st.write(f"**🏭 Производство**: {edited_prod_start.strftime('%d.%m.%Y')} → {calc_prod_end.strftime('%d.%m.%Y')} ({edited_prod_days} дн.)")
                st.write(f"**🚢 Доставка**: {calc_shipping_start.strftime('%d.%m.%Y')} → {calc_shipping_end.strftime('%d.%m.%Y')} ({edited_shipping_days} дн.)")
            with col_preview2:
                st.write(f"**📦 Обработка**: {calc_processing_start.strftime('%d.%m.%Y')} → {calc_processing_end.strftime('%d.%m.%Y')} ({edited_processing_days} дн.)")
                st.write(f"**🛍️ Поставка на WB**: {calc_wb_start.strftime('%d.%m.%Y')} → {calc_wb_end.strftime('%d.%m.%Y')} ({edited_wb_days} дн.)")
                st.success(f"**✅ Готов к продаже**: {calc_wb_end.strftime('%d.%m.%Y')}")
            
            # Кнопки управления формой редактирования
            col_edit_btn1, col_edit_btn2, col_edit_btn3 = st.columns([1, 1, 1])
            
            with col_edit_btn1:
                if st.form_submit_button("💾 Сохранить изменения", type="primary"):
                    # Расчет обновленных дат (правильный расчет: день начала считается, поэтому -1)
                    if edited_dev_days > 0:
                        edited_dev_end = edited_dev_start + timedelta(days=edited_dev_days - 1)
                        # Если дата производства указана раньше окончания разработки, пересчитываем
                        if edited_prod_start <= calc_dev_end:
                            edited_prod_start = calc_dev_end + timedelta(days=1)
                        edited_prod_end = edited_prod_start + timedelta(days=edited_prod_days - 1)
                    else:
                        edited_dev_end = edited_dev_start
                        edited_prod_end = edited_prod_start + timedelta(days=edited_prod_days - 1)
                    
                    # Каждый следующий этап начинается на следующий день после окончания предыдущего
                    edited_shipping_start = edited_prod_end + timedelta(days=1)
                    edited_shipping_end = edited_shipping_start + timedelta(days=edited_shipping_days - 1)
                    edited_processing_start = edited_shipping_end + timedelta(days=1)
                    edited_processing_end = edited_processing_start + timedelta(days=edited_processing_days - 1)
                    edited_wb_start = edited_processing_end + timedelta(days=1)
                    edited_wb_end = edited_wb_start + timedelta(days=edited_wb_days - 1)
                    
                    # Обновление проекта
                    editing_project.update({
                        "name": edited_name,
                        "development_start": edited_dev_start.strftime("%Y-%m-%d"),
                        "development_end": edited_dev_end.strftime("%Y-%m-%d"),
                        "development_days": edited_dev_days,
                        "production_start": edited_prod_start.strftime("%Y-%m-%d"),
                        "production_end": edited_prod_end.strftime("%Y-%m-%d"),
                        "production_days": edited_prod_days,
                        "shipping_start": edited_shipping_start.strftime("%Y-%m-%d"),
                        "shipping_end": edited_shipping_end.strftime("%Y-%m-%d"),
                        "shipping_days": edited_shipping_days,
                        "processing_start": edited_processing_start.strftime("%Y-%m-%d"),
                        "processing_end": edited_processing_end.strftime("%Y-%m-%d"),
                        "processing_days": edited_processing_days,
                        "wb_start": edited_wb_start.strftime("%Y-%m-%d"),
                        "wb_end": edited_wb_end.strftime("%Y-%m-%d"),
                        "wb_days": edited_wb_days,
                        "target_launch": edited_target_launch.strftime("%Y-%m-%d"),
                        "notes": edited_notes,
                        "sample_russia_fabric": edited_sample_russia_fabric,
                        "sample_russia_ready": edited_sample_russia_ready,
                        "sample_china": edited_sample_china,
                        "delivery_china": edited_delivery_china,
                        "delivery_russia": edited_delivery_russia,
                        "patterns": edited_patterns,
                        "model_3d": edited_model_3d,
                        "taxi": edited_taxi,
                        "other_expenses": edited_other_expenses,
                        "total_development_cost": edited_total_development_cost
                    })
                    
                    save_data(saved_projects)
                    st.success(f"Проект '{edited_name}' успешно обновлен!")
                    st.session_state.editing_project = None
                    st.rerun()
            
            with col_edit_btn2:
                if st.form_submit_button("❌ Отменить"):
                    st.session_state.editing_project = None
                    st.rerun()
            
            with col_edit_btn3:
                if st.form_submit_button("🔄 Автопересчет дат"):
                    # Автоматический пересчет всех дат на основе начальной даты и длительностей
                    # (правильный расчет: день начала считается, поэтому -1)
                    if edited_dev_days > 0:
                        edited_dev_end = edited_dev_start + timedelta(days=edited_dev_days - 1)
                        edited_prod_start = edited_dev_end + timedelta(days=1)
                    else:
                        edited_dev_end = edited_dev_start
                        edited_prod_start = edited_dev_start + timedelta(days=1)
                    
                    edited_prod_end = edited_prod_start + timedelta(days=edited_prod_days - 1)
                    edited_shipping_start = edited_prod_end + timedelta(days=1)
                    edited_shipping_end = edited_shipping_start + timedelta(days=edited_shipping_days - 1)
                    edited_processing_start = edited_shipping_end + timedelta(days=1)
                    edited_processing_end = edited_processing_start + timedelta(days=edited_processing_days - 1)
                    edited_wb_start = edited_processing_end + timedelta(days=1)
                    edited_wb_end = edited_wb_start + timedelta(days=edited_wb_days - 1)
                    
                    st.info(f"📊 **Пересчитанные даты**: Товар будет готов к продаже **{edited_wb_end.strftime('%d.%m.%Y')}**")
                    st.rerun()
        
        st.divider()
    
    # Фильтры
    col_filter1, col_filter2, col_filter3 = st.columns(3)
    
    with col_filter1:
        status_filter = st.selectbox(
            "Статус",
            ["Все", "Активные", "Завершенные", "Просроченные"]
        )
    
    with col_filter2:
        search_term = st.text_input("Поиск по названию", placeholder="Введите название проекта")
    
    with col_filter3:
        sort_by = st.selectbox(
            "Сортировка",
            ["По дате создания", "По дате запуска", "По названию"]
        )
    
    # Фильтрация проектов
    filtered_projects = saved_projects.copy()
    
    if status_filter == "Активные":
        filtered_projects = [p for p in filtered_projects if datetime.strptime(p['wb_end'], "%Y-%m-%d").date() >= datetime.now().date()]
    elif status_filter == "Завершенные":
        filtered_projects = [p for p in filtered_projects if datetime.strptime(p['wb_end'], "%Y-%m-%d").date() < datetime.now().date()]
    elif status_filter == "Просроченные":
        filtered_projects = [p for p in filtered_projects if datetime.strptime(p['target_launch'], "%Y-%m-%d").date() < datetime.now().date()]
    
    if search_term:
        filtered_projects = [p for p in filtered_projects if search_term.lower() in p['name'].lower()]
    
    # Сортировка
    if sort_by == "По дате создания":
        filtered_projects.sort(key=lambda x: x['created_at'], reverse=True)
    elif sort_by == "По дате запуска":
        filtered_projects.sort(key=lambda x: x['target_launch'])
    elif sort_by == "По названию":
        filtered_projects.sort(key=lambda x: x['name'])
    
    # Отображение проектов (свернуты по умолчанию, показывают только краткие KPI)
    for project_idx, project in enumerate(filtered_projects):
        # Краткие KPI в заголовке проекта
        wb_end_date = datetime.strptime(project['wb_end'], "%Y-%m-%d").date()
        target_launch_date = datetime.strptime(project['target_launch'], "%Y-%m-%d").date()
        current_date = datetime.now().date()
        days_after_wb = (target_launch_date - wb_end_date).days
        
        # Расчет дней до производства
        if project.get('development_days', 0) > 0:
            production_start_date = datetime.strptime(project['production_start'], "%Y-%m-%d").date()
            days_to_production = (production_start_date - current_date).days
        else:
            production_start_date = datetime.strptime(project['production_start'], "%Y-%m-%d").date()
            days_to_production = (production_start_date - current_date).days
        
        # Статус проекта
        if wb_end_date >= current_date:
            if target_launch_date >= current_date:
                status = "🟢 В планах"
            else:
                status = "🟡 В процессе"
        else:
            if target_launch_date < current_date:
                status = "🔴 Просрочен"
            else:
                status = "✅ Завершен"
        
        # Краткие KPI в заголовке
        # Форматируем дату начала в русском формате
        start_date = datetime.strptime(project['development_start'] if project.get('development_days', 0) > 0 else project['production_start'], "%Y-%m-%d")
        months_ru = {
            1: "января", 2: "февраля", 3: "марта", 4: "апреля",
            5: "мая", 6: "июня", 7: "июля", 8: "августа",
            9: "сентября", 10: "октября", 11: "ноября", 12: "декабря"
        }
        start_date_formatted = f"{start_date.day} {months_ru[start_date.month]} {start_date.year}"
        
        st.subheader(f"📦 {project['name']} (ID: {project['id']}) - {status}")
        st.markdown(f"**📅 Дата начала: {start_date_formatted}**")
        
        # Краткие метрики в одной строке
        col_kpi_brief1, col_kpi_brief2, col_kpi_brief3, col_kpi_brief4 = st.columns(4)
        
        with col_kpi_brief1:
            st.metric("🏭 Дней до производства", f"{days_to_production} дн.", 
                     delta=f"{'+' if days_to_production > 0 else ''}{days_to_production} дн.")
        
        with col_kpi_brief2:
            st.metric("⏰ Дней до запуска", f"{days_after_wb} дн.", 
                     delta=f"{'+' if days_after_wb > 0 else ''}{days_after_wb} дн.")
        
        with col_kpi_brief3:
            if project.get('development_days', 0) > 0:
                st.metric("🔬 Разработка", f"{project['development_days']} дн.")
            else:
                st.metric("🏭 Производство", f"{project['production_days']} дн.")
        
        with col_kpi_brief4:
            if project.get('total_development_cost', 0) > 0:
                st.metric("💰 Расходы", f"{project['total_development_cost']:,} ₽")
            else:
                st.metric("🚢 Доставка", f"{project['shipping_days']} дн.")
        
        # Сворачиваемый блок с деталями проекта
        with st.expander("📊 Детали проекта", expanded=False):
            st.divider()
            
            # Временная шкала на всю ширину
            st.subheader("📅 Временная шкала проекта")
            
            # Создание временной шкалы (адаптивная)
            if project.get('development_days', 0) > 0:
                # Если есть этап разработки
                timeline_data = {
                    'Этап': ['Разработка', 'Производство', 'Доставка', 'Обработка', 'Поставка на WB'],
                    'Начало': [
                        project['development_start'],
                        project['production_start'],
                        project['shipping_start'],
                        project['processing_start'],
                        project['wb_start']
                    ],
                    'Конец': [
                        project['development_end'],
                        project['production_end'],
                        project['shipping_end'],
                        project['processing_end'],
                        project['wb_end']
                    ],
                    'Длительность': [
                        project['development_days'],
                        project['production_days'],
                        project['shipping_days'],
                        project['processing_days'],
                        project['wb_days']
                    ]
                }
            else:
                # Если нет этапа разработки
                timeline_data = {
                    'Этап': ['Производство', 'Доставка', 'Обработка', 'Поставка на WB'],
                    'Начало': [
                        project['production_start'],
                        project['shipping_start'],
                        project['processing_start'],
                        project['wb_start']
                    ],
                    'Конец': [
                        project['production_end'],
                        project['shipping_end'],
                        project['processing_end'],
                        project['wb_end']
                    ],
                    'Длительность': [
                        project['production_days'],
                        project['shipping_days'],
                        project['processing_days'],
                        project['wb_days']
                    ]
                }
            
            df_timeline = pd.DataFrame(timeline_data)
            df_timeline['Начало'] = pd.to_datetime(df_timeline['Начало'])
            df_timeline['Конец'] = pd.to_datetime(df_timeline['Конец'])
            
            # Временная шкала
            fig_timeline = px.timeline(
                timeline_data,
                x_start='Начало',
                x_end='Конец',
                y='Этап',
                title="Временная шкала проекта",
                color='Длительность',
                color_continuous_scale='viridis'
            )
            
            fig_timeline.update_layout(
                height=400,
                xaxis_title="Дата",
                yaxis_title="Этап"
            )
            
            st.plotly_chart(fig_timeline, use_container_width=True, key=f"timeline_{project_idx}_{project['id']}_main")
            
            # Детали проекта на всю ширину
            st.subheader("📊 Детали проекта")
            
            # Статус в красивом блоке на всю ширину
            col_status1, col_status2, col_status3 = st.columns([1, 2, 1])
            with col_status2:
                st.info(f"**Статус проекта**: {status}")
            
            # Ключевые даты в виде KPI
            st.subheader("📅 Ключевые даты")
            
            # Отображение KPI на всю ширину (адаптивное количество колонок)
            if project.get('development_days', 0) > 0:
                # Если есть этап разработки - 5 колонок
                col_kpi1, col_kpi2, col_kpi3, col_kpi4, col_kpi5 = st.columns(5)
                
                with col_kpi1:
                    st.metric("🔬 Начало разработки", format_date_russian(project['development_start']))
                    st.metric("✅ Окончание разработки", format_date_russian(project['development_end']))
                
                with col_kpi2:
                    st.metric("🏭 Начало производства", format_date_russian(project['production_start']))
                    st.metric("✅ Окончание производства", format_date_russian(project['production_end']))
                
                with col_kpi3:
                    st.metric("🚢 Начало доставки", format_date_russian(project['shipping_start']))
                    st.metric("🇷🇺 Прибытие в Россию", format_date_russian(project['shipping_end']))
                
                with col_kpi4:
                    st.metric("📦 Начало обработки", format_date_russian(project['processing_start']))
                    st.metric("🏁 Окончание обработки", format_date_russian(project['processing_end']))
                
                with col_kpi5:
                    st.metric("📦 Поставка на WB", format_date_russian(project['wb_start']))
                    st.metric("🛍️ Готов к продаже", format_date_russian(project['wb_end']))
                    st.metric("🎯 Целевая дата запуска", format_date_russian(project['target_launch']))
            else:
                # Если нет этапа разработки - 4 колонки
                col_kpi1, col_kpi2, col_kpi3, col_kpi4 = st.columns(4)
                
                with col_kpi1:
                    st.metric("🏭 Начало производства", format_date_russian(project['production_start']))
                    st.metric("✅ Окончание производства", format_date_russian(project['production_end']))
                
                with col_kpi2:
                    st.metric("🚢 Начало доставки", format_date_russian(project['shipping_start']))
                    st.metric("🇷🇺 Прибытие в Россию", format_date_russian(project['shipping_end']))
                
                with col_kpi3:
                    st.metric("📦 Начало обработки", format_date_russian(project['processing_start']))
                    st.metric("🏁 Окончание обработки", format_date_russian(project['processing_end']))
                
                with col_kpi4:
                    st.metric("📦 Поставка на WB", format_date_russian(project['wb_start']))
                    st.metric("🛍️ Готов к продаже", format_date_russian(project['wb_end']))
                    st.metric("🎯 Целевая дата запуска", format_date_russian(project['target_launch']))
            
            # Дополнительная информация о временном запасе на всю ширину
            st.divider()
            
            # Информация о днях до производства
            if days_to_production > 0:
                st.info(f"📅 **Планирование**: До начала производства осталось {days_to_production} дней")
            elif days_to_production == 0:
                st.warning("⚠️ **Внимание**: Производство начинается сегодня")
            else:
                st.error(f"🔴 **Производство началось**: Производство началось {abs(days_to_production)} дней назад")
            
            # Информация о временном запасе до запуска
            if days_after_wb > 0:
                st.success(f"✅ **Временной запас**: У вас есть {days_after_wb} дней между готовностью товара и целевой датой запуска")
            elif days_after_wb == 0:
                st.warning("⚠️ **Внимание**: Товар готов к продаже точно в целевую дату")
            else:
                st.error(f"🔴 **Просрочено**: Товар готов к продаже на {abs(days_after_wb)} дней позже целевой даты")
            
            # Длительности на всю ширину
            st.divider()
            st.subheader("⏱️ Длительности этапов")
            
            if project.get('development_days', 0) > 0:
                # Если есть этап разработки - 5 колонок
                col_dur1, col_dur2, col_dur3, col_dur4, col_dur5 = st.columns(5)
                
                with col_dur1:
                    st.metric("🔬 Разработка", f"{project['development_days']} дн.")
                
                with col_dur2:
                    st.metric("🏭 Производство", f"{project['production_days']} дн.")
                
                with col_dur3:
                    st.metric("🚢 Доставка", f"{project['shipping_days']} дн.")
                
                with col_dur4:
                    st.metric("📦 Обработка", f"{project['processing_days']} дн.")
                
                with col_dur5:
                    st.metric("🛍️ Поставка на WB", f"{project['wb_days']} дн.")
            else:
                # Если нет этапа разработки - 4 колонки
                col_dur1, col_dur2, col_dur3, col_dur4 = st.columns(4)
                
                with col_dur1:
                    st.metric("🏭 Производство", f"{project['production_days']} дн.")
                
                with col_dur2:
                    st.metric("🚢 Доставка", f"{project['shipping_days']} дн.")
                
                with col_dur3:
                    st.metric("📦 Обработка", f"{project['processing_days']} дн.")
                
                with col_dur4:
                    st.metric("🛍️ Поставка на WB", f"{project['wb_days']} дн.")
            
            # Расходы на разработку (показываются только если есть расходы)
            if 'total_development_cost' in project and project['total_development_cost'] > 0:
                st.divider()
                st.subheader("💰 Расходы на разработку")
                
                col_cost1, col_cost2, col_cost3 = st.columns(3)
                
                with col_cost1:
                    st.write("**Образцы и материалы:**")
                    if project.get('sample_russia_fabric', 0) > 0:
                        st.metric("Ткань, пуговицы", f"{project['sample_russia_fabric']:,} ₽")
                    if project.get('sample_russia_ready', 0) > 0:
                        st.metric("Образец в России", f"{project['sample_russia_ready']:,} ₽")
                    if project.get('sample_china', 0) > 0:
                        st.metric("Образец в Китае", f"{project['sample_china']:,} ₽")
                
                with col_cost2:
                    st.write("**Доставка и документация:**")
                    if project.get('delivery_china', 0) > 0:
                        st.metric("Доставка из Китая", f"{project['delivery_china']:,} ₽")
                    if project.get('delivery_russia', 0) > 0:
                        st.metric("Доставка по России", f"{project['delivery_russia']:,} ₽")
                    if project.get('patterns', 0) > 0:
                        st.metric("Лекала", f"{project['patterns']:,} ₽")
                    if project.get('model_3d', 0) > 0:
                        st.metric("3D модель", f"{project['model_3d']:,} ₽")
                
                with col_cost3:
                    st.write("**Прочие расходы:**")
                    if project.get('taxi', 0) > 0:
                        st.metric("Такси", f"{project['taxi']:,} ₽")
                    if project.get('other_expenses', 0) > 0:
                        st.metric("Прочие расходы", f"{project['other_expenses']:,} ₽")
                    
                    st.divider()
                    st.metric("**Общие расходы**", f"{project['total_development_cost']:,} ₽", delta="Разработка")
            
            if project['notes']:
                st.divider()
                st.subheader("📝 Заметки")
                st.info(project['notes'])
            
            # Кнопки управления на всю ширину
            st.divider()
            st.subheader("⚙️ Управление проектом")
            
            col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 1])
            
            with col_btn1:
                if st.button("✏️ Редактировать", key=f"edit_{project_idx}_{project['id']}"):
                    st.session_state.editing_project = project['id']
                    st.rerun()
                    
            with col_btn2:
                if st.button("🗑️ Удалить", key=f"delete_{project_idx}_{project['id']}"):
                    saved_projects.remove(project)
                    save_data(saved_projects)
                    st.success(f"Проект '{project['name']}' удален!")
                    st.rerun()
            
            with col_btn3:
                if st.button("📊 Экспорт", key=f"export_{project_idx}_{project['id']}"):
                    st.info("Функция экспорта будет добавлена в следующем обновлении")
        
        # Разделитель между проектами
        st.markdown("---")
        st.markdown("")

with col2:
    st.header("📊 Статистика")
    
    if saved_projects:
        total_projects = len(saved_projects)
        active_projects = len([p for p in saved_projects if datetime.strptime(p['wb_end'], "%Y-%m-%d").date() >= datetime.now().date()])
        completed_projects = total_projects - active_projects
        
        st.metric("Всего проектов", total_projects)
        st.metric("Активных проектов", active_projects)
        st.metric("Завершенных", completed_projects)
        
        # Средние сроки (адаптивные)
        avg_production = sum(p['production_days'] for p in saved_projects) / total_projects
        avg_shipping = sum(p['shipping_days'] for p in saved_projects) / total_projects
        
        # Проверяем, есть ли проекты с этапом разработки
        projects_with_development = [p for p in saved_projects if p.get('development_days', 0) > 0]
        if projects_with_development:
            avg_development = sum(p['development_days'] for p in projects_with_development) / len(projects_with_development)
        else:
            avg_development = 0
        
        # Расчет среднего временного запаса
        time_buffers = []
        for p in saved_projects:
            wb_end = datetime.strptime(p['wb_end'], "%Y-%m-%d").date()
            target_launch = datetime.strptime(p['target_launch'], "%Y-%m-%d").date()
            buffer = (target_launch - wb_end).days
            if buffer >= 0:  # Только положительные запасы
                time_buffers.append(buffer)
        
        avg_buffer = sum(time_buffers) / len(time_buffers) if time_buffers else 0
        
        if avg_development > 0:
            st.metric("Средний срок разработки", f"{avg_development:.1f} дн.")
        st.metric("Средний срок производства", f"{avg_production:.1f} дн.")
        st.metric("Средний срок доставки", f"{avg_shipping:.1f} дн.")
        st.metric("Средний временной запас", f"{avg_buffer:.1f} дн.")
        
        # Статистика по расходам на разработку
        if saved_projects:
            development_costs = [p.get('total_development_cost', 0) for p in saved_projects if p.get('total_development_cost', 0) > 0]
            if development_costs:
                avg_development_cost = sum(development_costs) / len(development_costs)
                total_development_cost = sum(development_costs)
                max_development_cost = max(development_costs)
                
                st.metric("💰 Средние расходы на разработку", f"{avg_development_cost:,.0f} ₽")
                st.metric("💰 Общие расходы на разработку", f"{total_development_cost:,.0f} ₽")
                st.metric("💰 Максимальные расходы на разработку", f"{max_development_cost:,.0f} ₽")
        
        # Дополнительные KPI
        if saved_projects:
            # Проекты с критичными временными запасами
            critical_projects = []
            for p in saved_projects:
                wb_end = datetime.strptime(p['wb_end'], "%Y-%m-%d").date()
                target_launch = datetime.strptime(p['target_launch'], "%Y-%m-%d").date()
                if (target_launch - wb_end).days < 0:
                    critical_projects.append(p['name'])
            
            if critical_projects:
                st.metric("🚨 Критичные проекты", len(critical_projects), delta="Требуют внимания")
            else:
                st.metric("✅ Критичные проекты", 0, delta="Все в порядке")
    else:
        st.info("Нет созданных проектов")
    editing_project = None
    
    if editing_project_id:
        editing_project = next((p for p in saved_projects if p['id'] == editing_project_id), None)
    
    # Если есть проект для редактирования, показываем форму редактирования
    if editing_project:
        st.subheader(f"✏️ Редактирование проекта: {editing_project['name']}")
        
        with st.form(f"edit_project_form_{editing_project['id']}", clear_on_submit=False):
            # Основная информация
            edited_name = st.text_input("Название проекта/товара", value=editing_project['name'])
            
            # Информация о проекте
            st.info(f"📋 **ID проекта**: {editing_project['id']} | 📅 **Создан**: {editing_project.get('created_at', 'Не указано')}")
            
            col_edit1, col_edit2 = st.columns(2)
            
            with col_edit1:
                edited_dev_start = st.date_input(
                    "Дата начала разработки",
                    value=datetime.strptime(editing_project['development_start'], "%Y-%m-%d").date(),
                    key="edit_dev_start"
                )
                
                edited_dev_days = st.number_input(
                    "Сроки разработки (дни)",
                    min_value=0,
                    max_value=365,
                    value=editing_project['development_days'],
                    key="edit_dev_days"
                )
                
                edited_prod_start = st.date_input(
                    "Дата начала производства",
                    value=datetime.strptime(editing_project['production_start'], "%Y-%m-%d").date(),
                    key="edit_prod_start"
                )
                
                edited_prod_days = st.number_input(
                    "Сроки производства (дни)",
                    min_value=1,
                    max_value=365,
                    value=editing_project['production_days'],
                    key="edit_prod_days"
                )
                
                edited_shipping_days = st.number_input(
                    "Сроки доставки (дни)",
                    min_value=1,
                    max_value=365,
                    value=editing_project['shipping_days'],
                    key="edit_shipping_days"
                )
            
            with col_edit2:
                edited_processing_days = st.number_input(
                    "Обработка (дни)",
                    min_value=1,
                    max_value=30,
                    value=editing_project['processing_days'],
                    key="edit_processing_days"
                )
                
                edited_wb_days = st.number_input(
                    "Поставка на WB (дни)",
                    min_value=1,
                    max_value=30,
                    value=editing_project['wb_days'],
                    key="edit_wb_days"
                )
                
                edited_target_launch = st.date_input(
                    "Целевая дата запуска",
                    value=datetime.strptime(editing_project['target_launch'], "%Y-%m-%d").date(),
                    key="edit_target_launch"
                )
            
            # Расходы на разработку
            with st.expander("💰 Расходы на разработку", expanded=False):
                col_edit_exp1, col_edit_exp2 = st.columns(2)
                
                with col_edit_exp1:
                    st.write("**Образцы и материалы:**")
                    edited_sample_russia_fabric = st.number_input(
                        "Ткань, пуговицы (₽)", 
                        min_value=0, 
                        value=editing_project.get('sample_russia_fabric', 0),
                        key="edit_sample_russia_fabric"
                    )
                    edited_sample_russia_ready = st.number_input(
                        "Образец в России готовый (₽)", 
                        min_value=0, 
                        value=editing_project.get('sample_russia_ready', 0),
                        key="edit_sample_russia_ready"
                    )
                    edited_sample_china = st.number_input(
                        "Образец в Китае (₽)", 
                        min_value=0, 
                        value=editing_project.get('sample_china', 0),
                        key="edit_sample_china"
                    )
                    
                    st.write("**Доставка:**")
                    edited_delivery_china = st.number_input(
                        "Доставка из Китая (₽)", 
                        min_value=0, 
                        value=editing_project.get('delivery_china', 0),
                        key="edit_delivery_china"
                    )
                    edited_delivery_russia = st.number_input(
                        "Доставка по России (₽)", 
                        min_value=0, 
                        value=editing_project.get('delivery_russia', 0),
                        key="edit_delivery_russia"
                    )
                
                with col_edit_exp2:
                    st.write("**Техническая документация:**")
                    edited_patterns = st.number_input(
                        "Лекала (₽)", 
                        min_value=0, 
                        value=editing_project.get('patterns', 0),
                        key="edit_patterns"
                    )
                    edited_model_3d = st.number_input(
                        "3D модель (₽)", 
                        min_value=0, 
                        value=editing_project.get('model_3d', 0),
                        key="edit_model_3d"
                    )
                    
                    st.write("**Прочие расходы:**")
                    edited_taxi = st.number_input(
                        "Такси (₽)", 
                        min_value=0, 
                        value=editing_project.get('taxi', 0),
                        key="edit_taxi"
                    )
                    edited_other_expenses = st.number_input(
                        "Прочие расходы (₽)", 
                        min_value=0, 
                        value=editing_project.get('other_expenses', 0),
                        key="edit_other_expenses"
                    )
                
                # Расчет общих расходов на разработку
                edited_total_development_cost = (
                    edited_sample_russia_fabric + edited_sample_russia_ready + edited_sample_china +
                    edited_delivery_china + edited_delivery_russia + edited_patterns + 
                    edited_model_3d + edited_taxi + edited_other_expenses
                )
                
                st.info(f"**💰 Общие расходы на разработку: {edited_total_development_cost:,} ₽**")
            
            edited_notes = st.text_area(
                "Дополнительные заметки", 
                value=editing_project.get('notes', ''),
                key="edit_notes"
            )
            
            # Автоматический расчет и отображение дат в реальном времени
            st.markdown("---")
            st.subheader("📅 Предварительный просмотр дат")
            
            # Расчет дат на основе текущих значений (правильный расчет: день начала считается, поэтому -1)
            if edited_dev_days > 0:
                calc_dev_end = edited_dev_start + timedelta(days=edited_dev_days - 1)
                calc_prod_start = calc_dev_end + timedelta(days=1)
            else:
                calc_dev_end = edited_dev_start
                calc_prod_start = edited_prod_start if edited_prod_start > edited_dev_start else edited_dev_start + timedelta(days=1)
            
            calc_prod_end = edited_prod_start + timedelta(days=edited_prod_days - 1)
            calc_shipping_start = calc_prod_end + timedelta(days=1)
            calc_shipping_end = calc_shipping_start + timedelta(days=edited_shipping_days - 1)
            calc_processing_start = calc_shipping_end + timedelta(days=1)
            calc_processing_end = calc_processing_start + timedelta(days=edited_processing_days - 1)
            calc_wb_start = calc_processing_end + timedelta(days=1)
            calc_wb_end = calc_wb_start + timedelta(days=edited_wb_days - 1)
            
            # Отображение предварительного просмотра
            col_preview1, col_preview2 = st.columns(2)
            with col_preview1:
                if edited_dev_days > 0:
                    st.write(f"**🔬 Разработка**: {edited_dev_start.strftime('%d.%m.%Y')} → {calc_dev_end.strftime('%d.%m.%Y')} ({edited_dev_days} дн.)")
                st.write(f"**🏭 Производство**: {edited_prod_start.strftime('%d.%m.%Y')} → {calc_prod_end.strftime('%d.%m.%Y')} ({edited_prod_days} дн.)")
                st.write(f"**🚢 Доставка**: {calc_shipping_start.strftime('%d.%m.%Y')} → {calc_shipping_end.strftime('%d.%m.%Y')} ({edited_shipping_days} дн.)")
            with col_preview2:
                st.write(f"**📦 Обработка**: {calc_processing_start.strftime('%d.%m.%Y')} → {calc_processing_end.strftime('%d.%m.%Y')} ({edited_processing_days} дн.)")
                st.write(f"**🛍️ Поставка на WB**: {calc_wb_start.strftime('%d.%m.%Y')} → {calc_wb_end.strftime('%d.%m.%Y')} ({edited_wb_days} дн.)")
                st.success(f"**✅ Готов к продаже**: {calc_wb_end.strftime('%d.%m.%Y')}")
            
            # Кнопки управления формой редактирования
            col_edit_btn1, col_edit_btn2, col_edit_btn3 = st.columns([1, 1, 1])
            
            with col_edit_btn1:
                if st.form_submit_button("💾 Сохранить изменения", type="primary"):
                    # Расчет обновленных дат (правильный расчет: день начала считается, поэтому -1)
                    if edited_dev_days > 0:
                        edited_dev_end = edited_dev_start + timedelta(days=edited_dev_days - 1)
                        # Если дата производства указана раньше окончания разработки, пересчитываем
                        if edited_prod_start <= calc_dev_end:
                            edited_prod_start = calc_dev_end + timedelta(days=1)
                        edited_prod_end = edited_prod_start + timedelta(days=edited_prod_days - 1)
                    else:
                        edited_dev_end = edited_dev_start
                        edited_prod_end = edited_prod_start + timedelta(days=edited_prod_days - 1)
                    
                    # Каждый следующий этап начинается на следующий день после окончания предыдущего
                    edited_shipping_start = edited_prod_end + timedelta(days=1)
                    edited_shipping_end = edited_shipping_start + timedelta(days=edited_shipping_days - 1)
                    edited_processing_start = edited_shipping_end + timedelta(days=1)
                    edited_processing_end = edited_processing_start + timedelta(days=edited_processing_days - 1)
                    edited_wb_start = edited_processing_end + timedelta(days=1)
                    edited_wb_end = edited_wb_start + timedelta(days=edited_wb_days - 1)
                    
                    # Обновление проекта
                    editing_project.update({
                        "name": edited_name,
                        "development_start": edited_dev_start.strftime("%Y-%m-%d"),
                        "development_end": edited_dev_end.strftime("%Y-%m-%d"),
                        "development_days": edited_dev_days,
                        "production_start": edited_prod_start.strftime("%Y-%m-%d"),
                        "production_end": edited_prod_end.strftime("%Y-%m-%d"),
                        "production_days": edited_prod_days,
                        "shipping_start": edited_shipping_start.strftime("%Y-%m-%d"),
                        "shipping_end": edited_shipping_end.strftime("%Y-%m-%d"),
                        "shipping_days": edited_shipping_days,
                        "processing_start": edited_processing_start.strftime("%Y-%m-%d"),
                        "processing_end": edited_processing_end.strftime("%Y-%m-%d"),
                        "processing_days": edited_processing_days,
                        "wb_start": edited_wb_start.strftime("%Y-%m-%d"),
                        "wb_end": edited_wb_end.strftime("%Y-%m-%d"),
                        "wb_days": edited_wb_days,
                        "target_launch": edited_target_launch.strftime("%Y-%m-%d"),
                        "notes": edited_notes,
                        "sample_russia_fabric": edited_sample_russia_fabric,
                        "sample_russia_ready": edited_sample_russia_ready,
                        "sample_china": edited_sample_china,
                        "delivery_china": edited_delivery_china,
                        "delivery_russia": edited_delivery_russia,
                        "patterns": edited_patterns,
                        "model_3d": edited_model_3d,
                        "taxi": edited_taxi,
                        "other_expenses": edited_other_expenses,
                        "total_development_cost": edited_total_development_cost
                    })
                    
                    save_data(saved_projects)
                    st.success(f"Проект '{edited_name}' успешно обновлен!")
                    st.session_state.editing_project = None
                    st.rerun()
            
            with col_edit_btn2:
                if st.form_submit_button("❌ Отменить"):
                    st.session_state.editing_project = None
                    st.rerun()
            
            with col_edit_btn3:
                if st.form_submit_button("🔄 Автопересчет дат"):
                    # Автоматический пересчет всех дат на основе начальной даты и длительностей
                    # (правильный расчет: день начала считается, поэтому -1)
                    if edited_dev_days > 0:
                        edited_dev_end = edited_dev_start + timedelta(days=edited_dev_days - 1)
                        edited_prod_start = edited_dev_end + timedelta(days=1)
                    else:
                        edited_dev_end = edited_dev_start
                        edited_prod_start = edited_dev_start + timedelta(days=1)
                    
                    edited_prod_end = edited_prod_start + timedelta(days=edited_prod_days - 1)
                    edited_shipping_start = edited_prod_end + timedelta(days=1)
                    edited_shipping_end = edited_shipping_start + timedelta(days=edited_shipping_days - 1)
                    edited_processing_start = edited_shipping_end + timedelta(days=1)
                    edited_processing_end = edited_processing_start + timedelta(days=edited_processing_days - 1)
                    edited_wb_start = edited_processing_end + timedelta(days=1)
                    edited_wb_end = edited_wb_start + timedelta(days=edited_wb_days - 1)
                    
                    st.info(f"📊 **Пересчитанные даты**: Товар будет готов к продаже **{edited_wb_end.strftime('%d.%m.%Y')}**")
                    st.rerun()
        
        st.divider()