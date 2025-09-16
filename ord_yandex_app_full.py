import streamlit as st
import requests
import json
from datetime import datetime, date
import pandas as pd
from typing import Dict, List, Optional
import time

# Настройка страницы
st.set_page_config(
    page_title="ОРД Яндекс - Полное управление рекламой",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Конфигурация API
API_BASE_URL = "https://ord-prestable.yandex.net/api/v6"
API_DOCS_URL = "https://ord-prestable.yandex.net/api/docs"

class ORDAPIClient:
    """Расширенный клиент для работы с API ОРД Яндекс"""
    
    def __init__(self, token: str):
        self.token = token
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
    
    def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Dict:
        """Выполнить запрос к API"""
        url = f"{API_BASE_URL}{endpoint}"
        
        try:
            if method.upper() == "GET":
                response = requests.get(url, headers=self.headers)
            elif method.upper() == "POST":
                response = requests.post(url, headers=self.headers, json=data)
            else:
                raise ValueError(f"Неподдерживаемый метод: {method}")
            
            response.raise_for_status()
            return response.json()
        
        except requests.exceptions.RequestException as e:
            st.error(f"Ошибка API: {e}")
            return {"error": str(e)}
    
    def get_status(self) -> Dict:
        """Получить статус API"""
        return self._make_request("GET", "/status")
    
    # Организации
    def create_organization(self, org_data: Dict) -> Dict:
        return self._make_request("POST", "/organization", org_data)
    
    def get_organization(self, object_id: str) -> Dict:
        return self._make_request("GET", f"/organization?object_id={object_id}")
    
    # Креативы
    def create_creative(self, creative_data: Dict) -> Dict:
        return self._make_request("POST", "/creative", creative_data)
    
    def get_creative(self, object_id: str) -> Dict:
        return self._make_request("GET", f"/creative?object_id={object_id}")
    
    # Контракты
    def create_contract(self, contract_data: Dict) -> Dict:
        return self._make_request("POST", "/contract", contract_data)
    
    def get_contract(self, object_id: str) -> Dict:
        return self._make_request("GET", f"/contract?object_id={object_id}")
    
    # Акты
    def create_invoice(self, invoice_data: Dict) -> Dict:
        return self._make_request("POST", "/invoice", invoice_data)
    
    def get_invoice(self, object_id: str) -> Dict:
        return self._make_request("GET", f"/invoice?object_id={object_id}")
    
    # Площадки
    def create_platforms(self, platforms_data: Dict) -> Dict:
        return self._make_request("POST", "/platforms", platforms_data)
    
    # Статистика
    def create_statistics(self, statistics_data: Dict) -> Dict:
        return self._make_request("POST", "/statistics", statistics_data)

def render_organization_form():
    """Форма создания организации"""
    st.subheader("Создать организацию")
    
    with st.form("create_organization"):
        col1, col2 = st.columns(2)
        
        with col1:
            org_id = st.text_input("ID организации*", help="Уникальный идентификатор")
            org_type = st.selectbox(
                "Тип организации*",
                ["ul", "ip", "fl", "ffl", "ful"],
                format_func=lambda x: {
                    "ul": "Юридическое лицо (РФ)",
                    "ip": "Индивидуальный предприниматель (РФ)",
                    "fl": "Физическое лицо (РФ)",
                    "ffl": "Иностранное физическое лицо",
                    "ful": "Иностранное юридическое лицо"
                }[x]
            )
            org_name = st.text_input("Наименование/ФИО*")
            inn = st.text_input("ИНН*", help="10 или 12 цифр")
        
        with col2:
            kpp = st.text_input("КПП", help="Только для российских юр.лиц")
            is_ors = st.checkbox("Оператор рекламных систем")
            is_rr = st.checkbox("Рекламораспространитель")
            
            # Дополнительные поля для иностранных лиц
            if org_type in ["ffl", "ful"]:
                oksm_number = st.text_input("Код страны (ОКСМ)*")
                if org_type == "ffl":
                    epay_number = st.text_input("Номер счета/кошелька")
                    mobile_phone = st.text_input("Мобильный телефон")
                else:
                    reg_number = st.text_input("Регистрационный номер")
                    alternative_inn = st.text_input("Номер налогоплательщика")
        
        if st.form_submit_button("Создать организацию", type="primary"):
            org_data = {
                "id": org_id,
                "type": org_type,
                "name": org_name,
                "inn": inn,
                "isOrs": is_ors,
                "isRr": is_rr
            }
            
            if kpp:
                org_data["kpp"] = kpp
            
            if org_type in ["ffl", "ful"]:
                org_data["oksmNumber"] = oksm_number
                if org_type == "ffl":
                    if epay_number:
                        org_data["epayNumber"] = epay_number
                    if mobile_phone:
                        org_data["mobilePhone"] = mobile_phone
                else:
                    if reg_number:
                        org_data["regNumber"] = reg_number
                    if alternative_inn:
                        org_data["alternativeInn"] = alternative_inn
            
            return org_data
    
    return None

def render_creative_form():
    """Форма создания креатива"""
    st.subheader("Создать креатив")
    
    with st.form("create_creative"):
        col1, col2 = st.columns(2)
        
        with col1:
            creative_id = st.text_input("ID креатива*")
            creative_type = st.selectbox(
                "Тип креатива*",
                ["banner", "video", "text", "feed_element"],
                format_func=lambda x: {
                    "banner": "Баннер",
                    "video": "Видео", 
                    "text": "Текст",
                    "feed_element": "Элемент ленты"
                }[x]
            )
            
            description = st.text_area(
                "Описание объекта рекламирования*",
                help="Бренд, вид товара/услуги, дополнительная информация"
            )
            
            urls = st.text_area(
                "Целевые ссылки",
                help="По одной ссылке на строку"
            )
        
        with col2:
            # Текстовые данные
            st.subheader("Текстовые данные")
            text_data = st.text_area(
                "Текст креатива",
                help="Максимум 65000 символов"
            )
            
            # Медиаданные
            st.subheader("Медиаданные")
            media_url = st.text_input("Ссылка на медиафайл")
            media_type = st.selectbox(
                "Тип медиафайла",
                ["image", "video", "audio"]
            )
            
            # Таргетинг
            st.subheader("Параметры таргетинга")
            target_regions = st.multiselect(
                "Регионы",
                ["77", "78", "50"],  # Примеры кодов регионов
                help="Коды регионов для таргетинга"
            )
            
            target_sexes = st.multiselect(
                "Пол",
                ["male", "female"]
            )
            
            target_ages = st.text_input(
                "Возрастные группы",
                help="Например: 25:45, 18:35"
            )
        
        if st.form_submit_button("Создать креатив", type="primary"):
            creative_data = {
                "id": creative_id,
                "type": creative_type,
                "description": description
            }
            
            if urls:
                creative_data["urls"] = [url.strip() for url in urls.split('\n') if url.strip()]
            
            if text_data:
                creative_data["textData"] = [{"text": text_data}]
            
            if media_url:
                creative_data["mediaData"] = [{
                    "mediaUrl": media_url,
                    "mediaUrlFileType": media_type
                }]
            
            # Таргетинг
            targeting = {}
            if target_regions:
                targeting["regions"] = target_regions
            if target_sexes:
                targeting["sexes"] = target_sexes
            if target_ages:
                targeting["ages"] = [target_ages]
            
            if targeting:
                creative_data["targeting"] = targeting
            
            return creative_data
    
    return None

def render_contract_form():
    """Форма создания контракта"""
    st.subheader("Создать контракт")
    
    with st.form("create_contract"):
        col1, col2 = st.columns(2)
        
        with col1:
            contract_id = st.text_input("ID контракта*")
            contract_type = st.selectbox(
                "Тип контракта*",
                ["contract", "intermediary-contract", "additional-agreement"],
                format_func=lambda x: {
                    "contract": "Договор оказания услуг",
                    "intermediary-contract": "Посреднический договор",
                    "additional-agreement": "Дополнительное соглашение"
                }[x]
            )
            
            client_id = st.text_input("ID заказчика*")
            contractor_id = st.text_input("ID исполнителя*")
            
            client_role = st.selectbox(
                "Роль заказчика*",
                ["rd", "ra", "rr", "ors", "psr"],
                format_func=lambda x: {
                    "rd": "Рекламодатель",
                    "ra": "Рекламное агентство",
                    "rr": "Рекламораспространитель",
                    "ors": "Оператор рекламной системы",
                    "psr": "Посредник"
                }[x]
            )
        
        with col2:
            contractor_role = st.selectbox(
                "Роль исполнителя*",
                ["rd", "ra", "rr", "ors", "psr"],
                format_func=lambda x: {
                    "rd": "Рекламодатель",
                    "ra": "Рекламное агентство",
                    "rr": "Рекламораспространитель",
                    "ors": "Оператор рекламной системы",
                    "psr": "Посредник"
                }[x]
            )
            
            start_date = st.date_input("Дата начала*")
            end_date = st.date_input("Дата окончания*")
            
            amount = st.number_input(
                "Сумма договора",
                min_value=0.0,
                step=0.01,
                format="%.2f"
            )
        
        if st.form_submit_button("Создать контракт", type="primary"):
            contract_data = {
                "id": contract_id,
                "type": contract_type,
                "clientId": client_id,
                "contractorId": contractor_id,
                "clientRole": client_role,
                "contractorRole": contractor_role,
                "startDate": start_date.strftime("%Y-%m-%d"),
                "endDate": end_date.strftime("%Y-%m-%d")
            }
            
            if amount > 0:
                contract_data["amount"] = {
                    "excludingVat": str(amount),
                    "vatRate": "20.00",
                    "vat": str(amount * 0.2),
                    "includingVat": str(amount * 1.2)
                }
            
            return contract_data
    
    return None

def render_invoice_form():
    """Форма создания акта"""
    st.subheader("Создать акт")
    
    with st.form("create_invoice"):
        col1, col2 = st.columns(2)
        
        with col1:
            invoice_id = st.text_input("ID акта*")
            contract_id = st.text_input("ID договора*")
            
            client_role = st.selectbox(
                "Роль заказчика*",
                ["rd", "ra", "rr", "ors", "psr"],
                format_func=lambda x: {
                    "rd": "Рекламодатель",
                    "ra": "Рекламное агентство",
                    "rr": "Рекламораспространитель",
                    "ors": "Оператор рекламной системы",
                    "psr": "Посредник"
                }[x]
            )
            
            contractor_role = st.selectbox(
                "Роль исполнителя*",
                ["rd", "ra", "rr", "ors", "psr"],
                format_func=lambda x: {
                    "rd": "Рекламодатель",
                    "ra": "Рекламное агентство",
                    "rr": "Рекламораспространитель",
                    "ors": "Оператор рекламной системы",
                    "psr": "Посредник"
                }[x]
            )
        
        with col2:
            invoice_type = st.selectbox(
                "Тип акта*",
                ["invoice", "intermediary-report"],
                format_func=lambda x: {
                    "invoice": "Акт выполненных работ",
                    "intermediary-report": "Отчет посредника"
                }[x]
            )
            
            invoice_date = st.date_input("Дата акта*")
            start_date = st.date_input("Дата начала периода*")
            end_date = st.date_input("Дата окончания периода*")
            
            amount = st.number_input(
                "Сумма акта",
                min_value=0.0,
                step=0.01,
                format="%.2f"
            )
        
        if st.form_submit_button("Создать акт", type="primary"):
            invoice_data = {
                "id": invoice_id,
                "contractId": contract_id,
                "clientRole": client_role,
                "contractorRole": contractor_role,
                "type": invoice_type,
                "date": invoice_date.strftime("%Y-%m-%d"),
                "startDate": start_date.strftime("%Y-%m-%d"),
                "endDate": end_date.strftime("%Y-%m-%d")
            }
            
            if amount > 0:
                invoice_data["amount"] = {
                    "services": {
                        "excludingVat": str(amount),
                        "vatRate": "20.00",
                        "vat": str(amount * 0.2),
                        "includingVat": str(amount * 1.2)
                    }
                }
            
            return invoice_data
    
    return None

def render_statistics_form():
    """Форма создания статистики"""
    st.subheader("Создать статистику")
    
    with st.form("create_statistics"):
        col1, col2 = st.columns(2)
        
        with col1:
            stat_id = st.text_input("ID статистики")
            creative_id = st.text_input("ID креатива*")
            platform_id = st.text_input("ID платформы*")
            
            imps_fact = st.number_input(
                "Фактическое количество показов*",
                min_value=0,
                step=1
            )
            
            imps_plan = st.number_input(
                "Плановое количество показов*",
                min_value=0,
                step=1
            )
        
        with col2:
            campaign_type = st.selectbox(
                "Тип кампании*",
                ["cpa", "cpc", "cpm", "other"],
                format_func=lambda x: {
                    "cpa": "CPA (за действие)",
                    "cpc": "CPC (за клик)",
                    "cpm": "CPM (за 1000 показов)",
                    "other": "Другое"
                }[x]
            )
            
            amount_per_unit = st.number_input(
                "Стоимость за единицу",
                min_value=0.0,
                step=0.01,
                format="%.5f"
            )
            
            date_start_fact = st.date_input("Фактическая дата начала*")
            date_end_fact = st.date_input("Фактическая дата окончания*")
            
            date_start_plan = st.date_input("Плановая дата начала*")
            date_end_plan = st.date_input("Плановая дата окончания*")
        
        if st.form_submit_button("Создать статистику", type="primary"):
            statistics_data = {
                "statistics": [{
                    "creativeId": creative_id,
                    "platformId": platform_id,
                    "impsFact": int(imps_fact),
                    "impsPlan": int(imps_plan),
                    "type": campaign_type,
                    "dateStartFact": date_start_fact.strftime("%Y-%m-%d"),
                    "dateEndFact": date_end_fact.strftime("%Y-%m-%d"),
                    "dateStartPlan": date_start_plan.strftime("%Y-%m-%d"),
                    "dateEndPlan": date_end_plan.strftime("%Y-%m-%d")
                }]
            }
            
            if stat_id:
                statistics_data["statistics"][0]["id"] = stat_id
            
            if amount_per_unit > 0:
                statistics_data["statistics"][0]["amountPerUnit"] = str(amount_per_unit)
            
            return statistics_data
    
    return None

def main():
    st.title("📊 ОРД Яндекс - Полное управление рекламой")
    st.markdown("---")
    
    # Боковая панель для настройки
    with st.sidebar:
        st.header("🔧 Настройки")
        
        # Ввод токена API
        api_token = st.text_input(
            "API Token",
            type="password",
            help="Введите токен для доступа к API ОРД Яндекс"
        )
        
        if api_token:
            st.success("✅ Токен установлен")
            
            # Проверка подключения
            if st.button("🔍 Проверить подключение"):
                client = ORDAPIClient(api_token)
                status = client.get_status()
                
                if "error" not in status:
                    st.success("✅ Подключение успешно")
                    with st.expander("Детали статуса"):
                        st.json(status)
                else:
                    st.error("❌ Ошибка подключения")
        else:
            st.warning("⚠️ Введите токен для работы с API")
            st.markdown(f"[📖 Документация API]({API_DOCS_URL})")
        
        st.markdown("---")
        st.markdown("### 📋 Быстрые действия")
        st.markdown("- Создать тестовую организацию")
        st.markdown("- Создать тестовый креатив")
        st.markdown("- Проверить статус объектов")
    
    # Основной интерфейс
    if not api_token:
        st.info("👆 Введите токен API в боковой панели для начала работы")
        
        # Показываем информацию об API
        st.markdown("## 📖 О API ОРД Яндекс")
        st.markdown("""
        **ОРД (Общий реестр данных)** - это система учета рекламной информации в России.
        
        ### Основные возможности:
        - 🏢 Управление организациями (рекламодатели, агентства, площадки)
        - 🎨 Создание и управление креативами
        - 📋 Работа с контрактами на размещение рекламы
        - 📄 Ведение актов выполненных работ
        - 📊 Учет статистики показов
        - 🔍 Мониторинг статусов объектов
        
        ### Требования:
        - Валидный токен API
        - Соответствие данных требованиям ЕРИР
        - Корректное заполнение всех обязательных полей
        """)
        return
    
    client = ORDAPIClient(api_token)
    
    # Навигация по разделам
    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
        "🏢 Организации", 
        "🎨 Креативы", 
        "📋 Контракты", 
        "📄 Акты", 
        "📊 Статистика",
        "🌐 Площадки",
        "🔍 Статусы"
    ])
    
    # Вкладка Организации
    with tab1:
        st.header("🏢 Управление организациями")
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            org_data = render_organization_form()
            if org_data:
                with st.spinner("Создание организации..."):
                    result = client.create_organization(org_data)
                    st.success("Организация создана!")
                    st.json(result)
        
        with col2:
            st.subheader("Просмотр организации")
            
            org_id_view = st.text_input("ID организации для просмотра")
            if st.button("Получить данные организации"):
                if org_id_view:
                    with st.spinner("Загрузка данных..."):
                        result = client.get_organization(org_id_view)
                        st.json(result)
                else:
                    st.warning("Введите ID организации")
    
    # Вкладка Креативы
    with tab2:
        st.header("🎨 Управление креативами")
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            creative_data = render_creative_form()
            if creative_data:
                with st.spinner("Создание креатива..."):
                    result = client.create_creative(creative_data)
                    st.success("Креатив создан!")
                    st.json(result)
        
        with col2:
            st.subheader("Просмотр креатива")
            
            creative_id_view = st.text_input("ID креатива для просмотра")
            if st.button("Получить данные креатива"):
                if creative_id_view:
                    with st.spinner("Загрузка данных..."):
                        result = client.get_creative(creative_id_view)
                        st.json(result)
                else:
                    st.warning("Введите ID креатива")
    
    # Вкладка Контракты
    with tab3:
        st.header("📋 Управление контрактами")
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            contract_data = render_contract_form()
            if contract_data:
                with st.spinner("Создание контракта..."):
                    result = client.create_contract(contract_data)
                    st.success("Контракт создан!")
                    st.json(result)
        
        with col2:
            st.subheader("Просмотр контракта")
            
            contract_id_view = st.text_input("ID контракта для просмотра")
            if st.button("Получить данные контракта"):
                if contract_id_view:
                    with st.spinner("Загрузка данных..."):
                        result = client.get_contract(contract_id_view)
                        st.json(result)
                else:
                    st.warning("Введите ID контракта")
    
    # Вкладка Акты
    with tab4:
        st.header("📄 Управление актами")
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            invoice_data = render_invoice_form()
            if invoice_data:
                with st.spinner("Создание акта..."):
                    result = client.create_invoice(invoice_data)
                    st.success("Акт создан!")
                    st.json(result)
        
        with col2:
            st.subheader("Просмотр акта")
            
            invoice_id_view = st.text_input("ID акта для просмотра")
            if st.button("Получить данные акта"):
                if invoice_id_view:
                    with st.spinner("Загрузка данных..."):
                        result = client.get_invoice(invoice_id_view)
                        st.json(result)
                else:
                    st.warning("Введите ID акта")
    
    # Вкладка Статистика
    with tab5:
        st.header("📊 Управление статистикой")
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            statistics_data = render_statistics_form()
            if statistics_data:
                with st.spinner("Создание статистики..."):
                    result = client.create_statistics(statistics_data)
                    st.success("Статистика создана!")
                    st.json(result)
        
        with col2:
            st.subheader("Информация о статистике")
            st.info("""
            **Статистика** содержит данные о:
            - Фактических и плановых показах
            - Стоимости услуг
            - Периодах размещения
            - Типах рекламных кампаний
            """)
    
    # Вкладка Площадки
    with tab6:
        st.header("🌐 Управление площадками")
        st.info("Функционал площадок будет добавлен в следующих версиях")
    
    # Вкладка Статусы
    with tab7:
        st.header("🔍 Просмотр статусов")
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.subheader("Общий статус API")
            if st.button("Получить статус API"):
                with st.spinner("Проверка статуса..."):
                    status = client.get_status()
                    st.json(status)
        
        with col2:
            st.subheader("Статус конкретного объекта")
            
            object_type = st.selectbox(
                "Тип объекта",
                ["creative", "organization", "contract", "invoice"]
            )
            
            object_id = st.text_input("ID объекта")
            
            if st.button("Получить статус объекта"):
                if object_id:
                    with st.spinner("Загрузка статуса..."):
                        if object_type == "creative":
                            result = client.get_creative(object_id)
                        elif object_type == "organization":
                            result = client.get_organization(object_id)
                        elif object_type == "contract":
                            result = client.get_contract(object_id)
                        elif object_type == "invoice":
                            result = client.get_invoice(object_id)
                        
                        st.json(result)
                else:
                    st.warning("Введите ID объекта")

if __name__ == "__main__":
    main()
