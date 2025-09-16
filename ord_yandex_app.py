import streamlit as st
import requests
import json
from datetime import datetime, date
import pandas as pd
from typing import Dict, List, Optional
import time

# Настройка страницы
st.set_page_config(
    page_title="ОРД Яндекс - Управление рекламой",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Конфигурация API
API_BASE_URL = "https://ord-prestable.yandex.net/api/v6"
API_DOCS_URL = "https://ord-prestable.yandex.net/api/docs"

class ORDAPIClient:
    """Клиент для работы с API ОРД Яндекс"""
    
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
    
    def create_organization(self, org_data: Dict) -> Dict:
        """Создать организацию"""
        return self._make_request("POST", "/organization", org_data)
    
    def get_organization(self, object_id: str) -> Dict:
        """Получить информацию об организации"""
        return self._make_request("GET", f"/organization?object_id={object_id}")
    
    def create_creative(self, creative_data: Dict) -> Dict:
        """Создать креатив"""
        return self._make_request("POST", "/creative", creative_data)
    
    def get_creative(self, object_id: str) -> Dict:
        """Получить информацию о креативе"""
        return self._make_request("GET", f"/creative?object_id={object_id}")
    
    def create_contract(self, contract_data: Dict) -> Dict:
        """Создать контракт"""
        return self._make_request("POST", "/contract", contract_data)
    
    def get_contract(self, object_id: str) -> Dict:
        """Получить информацию о контракте"""
        return self._make_request("GET", f"/contract?object_id={object_id}")
    
    def create_invoice(self, invoice_data: Dict) -> Dict:
        """Создать акт"""
        return self._make_request("POST", "/invoice", invoice_data)
    
    def get_invoice(self, object_id: str) -> Dict:
        """Получить информацию об акте"""
        return self._make_request("GET", f"/invoice?object_id={object_id}")

def main():
    st.title("📊 ОРД Яндекс - Управление рекламой")
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
                    st.json(status)
                else:
                    st.error("❌ Ошибка подключения")
        else:
            st.warning("⚠️ Введите токен для работы с API")
            st.markdown(f"[📖 Документация API]({API_DOCS_URL})")
    
    # Основной интерфейс
    if not api_token:
        st.info("👆 Введите токен API в боковой панели для начала работы")
        return
    
    client = ORDAPIClient(api_token)
    
    # Навигация по разделам
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "🏢 Организации", 
        "🎨 Креативы", 
        "📋 Контракты", 
        "📄 Акты", 
        "📊 Статистика", 
        "🔍 Статусы"
    ])
    
    # Вкладка Организации
    with tab1:
        st.header("🏢 Управление организациями")
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.subheader("Создать организацию")
            
            with st.form("create_organization"):
                org_type = st.selectbox(
                    "Тип организации",
                    ["ul", "ip", "fl", "ffl", "ful"],
                    format_func=lambda x: {
                        "ul": "Юридическое лицо (РФ)",
                        "ip": "Индивидуальный предприниматель (РФ)",
                        "fl": "Физическое лицо (РФ)",
                        "ffl": "Иностранное физическое лицо",
                        "ful": "Иностранное юридическое лицо"
                    }[x]
                )
                
                org_id = st.text_input("ID организации")
                org_name = st.text_input("Наименование/ФИО")
                inn = st.text_input("ИНН")
                kpp = st.text_input("КПП (для юр.лиц)")
                
                is_ors = st.checkbox("Является оператором рекламных систем")
                is_rr = st.checkbox("Является рекламораспространителем")
                
                if st.form_submit_button("Создать организацию"):
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
                    
                    result = client.create_organization(org_data)
                    st.json(result)
        
        with col2:
            st.subheader("Просмотр организации")
            
            org_id_view = st.text_input("ID организации для просмотра")
            if st.button("Получить данные"):
                if org_id_view:
                    result = client.get_organization(org_id_view)
                    st.json(result)
                else:
                    st.warning("Введите ID организации")
    
    # Вкладка Креативы
    with tab2:
        st.header("🎨 Управление креативами")
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.subheader("Создать креатив")
            
            with st.form("create_creative"):
                creative_id = st.text_input("ID креатива")
                creative_type = st.selectbox(
                    "Тип креатива",
                    ["banner", "video", "text", "feed_element"],
                    format_func=lambda x: {
                        "banner": "Баннер",
                        "video": "Видео",
                        "text": "Текст",
                        "feed_element": "Элемент ленты"
                    }[x]
                )
                
                description = st.text_area("Описание объекта рекламирования")
                urls = st.text_area("Целевые ссылки (по одной на строку)")
                
                # Текстовые данные
                st.subheader("Текстовые данные")
                text_data = st.text_area("Текст креатива")
                
                # Медиаданные
                st.subheader("Медиаданные")
                media_url = st.text_input("Ссылка на медиафайл")
                media_type = st.selectbox(
                    "Тип медиафайла",
                    ["image", "video", "audio"]
                )
                
                if st.form_submit_button("Создать креатив"):
                    creative_data = {
                        "id": creative_id,
                        "type": creative_type,
                        "description": description,
                        "urls": [url.strip() for url in urls.split('\n') if url.strip()]
                    }
                    
                    if text_data:
                        creative_data["textData"] = [{"text": text_data}]
                    
                    if media_url:
                        creative_data["mediaData"] = [{
                            "mediaUrl": media_url,
                            "mediaUrlFileType": media_type
                        }]
                    
                    result = client.create_creative(creative_data)
                    st.json(result)
        
        with col2:
            st.subheader("Просмотр креатива")
            
            creative_id_view = st.text_input("ID креатива для просмотра")
            if st.button("Получить данные креатива"):
                if creative_id_view:
                    result = client.get_creative(creative_id_view)
                    st.json(result)
                else:
                    st.warning("Введите ID креатива")
    
    # Вкладка Контракты
    with tab3:
        st.header("📋 Управление контрактами")
        st.info("Функционал контрактов будет добавлен в следующих версиях")
    
    # Вкладка Акты
    with tab4:
        st.header("📄 Управление актами")
        st.info("Функционал актов будет добавлен в следующих версиях")
    
    # Вкладка Статистика
    with tab5:
        st.header("📊 Статистика")
        st.info("Функционал статистики будет добавлен в следующих версиях")
    
    # Вкладка Статусы
    with tab6:
        st.header("🔍 Просмотр статусов")
        
        if st.button("Получить общий статус API"):
            status = client.get_status()
            st.json(status)
        
        st.subheader("Статус конкретного объекта")
        
        object_type = st.selectbox(
            "Тип объекта",
            ["creative", "organization", "contract", "invoice"]
        )
        
        object_id = st.text_input("ID объекта")
        
        if st.button("Получить статус объекта"):
            if object_id:
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
