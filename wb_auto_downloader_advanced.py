# -*- coding: utf-8 -*-
"""
Улучшенная версия автоматического скачивания отчетов с сайта Wildberries
Включает более надежный поиск элементов и обработку различных форматов страниц
"""

import os
import time
import logging
from datetime import datetime, timedelta
from pathlib import Path
import pandas as pd
from typing import Optional, List, Dict
import streamlit as st
import json

try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.common.action_chains import ActionChains
    from selenium.webdriver.common.keys import Keys
    from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
    from webdriver_manager.chrome import ChromeDriverManager
except ImportError:
    st.error("❌ Необходимо установить зависимости: pip install selenium webdriver-manager")
    st.stop()

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('wb_downloader_advanced.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class WBAdvancedDownloader:
    """Улучшенный класс для автоматического скачивания отчетов с Wildberries"""
    
    def __init__(self, download_dir: str = "downloaded_reports", headless: bool = True):
        """
        Инициализация загрузчика
        
        Args:
            download_dir: Папка для сохранения скачанных файлов
            headless: Запуск браузера в фоновом режиме
        """
        self.download_dir = Path(download_dir)
        self.download_dir.mkdir(exist_ok=True)
        self.headless = headless
        self.driver = None
        self.wait = None
        
        # URL для входа в личный кабинет
        self.base_url = "https://seller.wildberries.ru"
        self.reports_url = "https://seller.wildberries.ru/suppliers-mutual-settlements/reports-implementations/reports-weekly-new"
        
        # Селекторы для различных элементов (могут изменяться)
        self.selectors = {
            'login_button': [
                "//button[contains(text(), 'Войти')]",
                "//button[contains(text(), 'Вход')]",
                "//a[contains(text(), 'Войти')]",
                "//button[@data-testid='login-button']"
            ],
            'phone_input': [
                "//input[@type='tel']",
                "//input[@name='phone']",
                "//input[contains(@placeholder, 'телефон')]",
                "//input[contains(@placeholder, 'Телефон')]"
            ],
            'get_code_button': [
                "//button[contains(text(), 'Получить код')]",
                "//button[contains(text(), 'Отправить код')]",
                "//button[contains(text(), 'Получить')]"
            ],
            'reports_table': [
                "//table[contains(@class, 'table')]",
                "//div[contains(@class, 'reports-table')]",
                "//div[contains(@class, 'table-container')]",
                "//div[contains(@class, 'reports-list')]"
            ],
            'download_button': [
                "//button[contains(text(), 'Скачать')]",
                "//a[contains(text(), 'Скачать')]",
                "//button[contains(text(), 'Excel')]",
                "//a[contains(text(), 'Excel')]",
                "//button[contains(@class, 'download')]",
                "//a[contains(@class, 'download')]"
            ]
        }
        
    def setup_driver(self) -> bool:
        """Настройка веб-драйвера Chrome с улучшенными параметрами"""
        try:
            chrome_options = Options()
            
            if self.headless:
                chrome_options.add_argument("--headless")
            
            # Настройки для скачивания файлов
            prefs = {
                "download.default_directory": str(self.download_dir.absolute()),
                "download.prompt_for_download": False,
                "download.directory_upgrade": True,
                "safebrowsing.enabled": True,
                "profile.default_content_settings.popups": 0,
                "profile.default_content_setting_values.automatic_downloads": 1
            }
            chrome_options.add_experimental_option("prefs", prefs)
            
            # Дополнительные настройки для стабильности
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--disable-web-security")
            chrome_options.add_argument("--disable-features=VizDisplayCompositor")
            chrome_options.add_argument("--window-size=1920,1080")
            chrome_options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
            
            # Автоматическая установка ChromeDriver
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.wait = WebDriverWait(self.driver, 30)
            
            # Установка таймаутов
            self.driver.implicitly_wait(10)
            self.driver.set_page_load_timeout(60)
            
            logger.info("✅ Веб-драйвер успешно настроен")
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка настройки веб-драйвера: {e}")
            return False
    
    def find_element_by_selectors(self, selectors: List[str], timeout: int = 10) -> Optional[object]:
        """Поиск элемента по списку селекторов"""
        for selector in selectors:
            try:
                element = WebDriverWait(self.driver, timeout).until(
                    EC.presence_of_element_located((By.XPATH, selector))
                )
                return element
            except TimeoutException:
                continue
        return None
    
    def find_clickable_element_by_selectors(self, selectors: List[str], timeout: int = 10) -> Optional[object]:
        """Поиск кликабельного элемента по списку селекторов"""
        for selector in selectors:
            try:
                element = WebDriverWait(self.driver, timeout).until(
                    EC.element_to_be_clickable((By.XPATH, selector))
                )
                return element
            except TimeoutException:
                continue
        return None
    
    def login(self, phone: str, password: str) -> bool:
        """
        Улучшенный вход в личный кабинет Wildberries
        
        Args:
            phone: Номер телефона
            password: Пароль (не используется, так как нужен SMS код)
            
        Returns:
            bool: True если вход успешен
        """
        try:
            logger.info("🔐 Начинаем процесс входа в личный кабинет...")
            
            # Переходим на главную страницу
            self.driver.get(self.base_url)
            time.sleep(3)
            
            # Ищем кнопку входа
            login_button = self.find_clickable_element_by_selectors(self.selectors['login_button'])
            
            if login_button:
                try:
                    login_button.click()
                    time.sleep(2)
                except Exception as e:
                    logger.warning(f"⚠️ Ошибка клика по кнопке входа: {e}")
                    # Пробуем JavaScript клик
                    self.driver.execute_script("arguments[0].click();", login_button)
                    time.sleep(2)
            else:
                logger.warning("⚠️ Кнопка входа не найдена, возможно уже авторизованы")
            
            # Вводим номер телефона
            phone_input = self.find_element_by_selectors(self.selectors['phone_input'])
            
            if phone_input:
                try:
                    phone_input.clear()
                    phone_input.send_keys(phone)
                    time.sleep(1)
                    
                    # Ищем кнопку "Получить код"
                    get_code_button = self.find_clickable_element_by_selectors(self.selectors['get_code_button'])
                    
                    if get_code_button:
                        get_code_button.click()
                        time.sleep(2)
                        
                        logger.info("📱 Код отправлен на телефон. Ожидаем ввода кода...")
                        
                        # Ждем ввода кода (пользователь должен ввести вручную)
                        st.info("📱 Введите код подтверждения, который пришел на ваш телефон")
                        
                        # Ждем перехода на главную страницу или появления элементов личного кабинета
                        try:
                            # Ждем появления элементов, указывающих на успешный вход
                            success_indicators = [
                                "//a[contains(@href, 'seller.wildberries.ru')]",
                                "//div[contains(@class, 'user-menu')]",
                                "//button[contains(@class, 'user')]",
                                "//div[contains(@class, 'profile')]"
                            ]
                            
                            success_element = self.find_element_by_selectors(success_indicators, timeout=60)
                            
                            if success_element:
                                logger.info("✅ Успешный вход в личный кабинет")
                                return True
                            else:
                                logger.error("❌ Не удалось войти в личный кабинет")
                                return False
                                
                        except TimeoutException:
                            logger.error("❌ Таймаут при ожидании входа")
                            return False
                    else:
                        logger.error("❌ Не найдена кнопка 'Получить код'")
                        return False
                        
                except Exception as e:
                    logger.error(f"❌ Ошибка при вводе телефона: {e}")
                    return False
            else:
                logger.error("❌ Не найден элемент для ввода телефона")
                return False
                
        except Exception as e:
            logger.error(f"❌ Ошибка при входе: {e}")
            return False
    
    def navigate_to_reports(self) -> bool:
        """Переход к странице отчетов с проверкой"""
        try:
            logger.info("📊 Переходим к странице отчетов...")
            
            # Переходим на страницу отчетов
            self.driver.get(self.reports_url)
            time.sleep(5)
            
            # Проверяем, что мы на правильной странице
            if "reports-weekly-new" in self.driver.current_url:
                logger.info("✅ Успешно перешли на страницу отчетов")
                
                # Ждем загрузки контента
                time.sleep(3)
                return True
            else:
                logger.error("❌ Не удалось перейти на страницу отчетов")
                return False
                
        except Exception as e:
            logger.error(f"❌ Ошибка при переходе к отчетам: {e}")
            return False
    
    def find_and_download_reports(self, date_from: datetime, date_to: datetime) -> List[str]:
        """
        Улучшенный поиск и скачивание отчетов за указанный период
        
        Args:
            date_from: Начальная дата
            date_to: Конечная дата
            
        Returns:
            List[str]: Список скачанных файлов
        """
        downloaded_files = []
        
        try:
            logger.info(f"🔍 Ищем отчеты с {date_from.strftime('%d.%m.%Y')} по {date_to.strftime('%d.%m.%Y')}")
            
            # Ждем загрузки страницы
            time.sleep(3)
            
            # Ищем таблицу или контейнер с отчетами
            reports_container = self.find_element_by_selectors(self.selectors['reports_table'])
            
            if not reports_container:
                logger.warning("⚠️ Таблица отчетов не найдена, пробуем альтернативные методы")
                
                # Пробуем найти отчеты в другом формате
                page_source = self.driver.page_source
                if "отчет" in page_source.lower() or "report" in page_source.lower():
                    logger.info("📋 Найдены упоминания отчетов на странице")
                else:
                    logger.error("❌ Отчеты не найдены на странице")
                    return []
            
            # Ищем все возможные элементы с отчетами
            report_elements = []
            
            # Различные селекторы для поиска отчетов
            report_selectors = [
                "//tr[td[contains(text(), '2024') or contains(text(), '2025')]]",
                "//div[contains(@class, 'report')]",
                "//div[contains(@class, 'row')]",
                "//li[contains(@class, 'report')]",
                "//div[contains(text(), '2024') or contains(text(), '2025')]"
            ]
            
            for selector in report_selectors:
                try:
                    elements = self.driver.find_elements(By.XPATH, selector)
                    if elements:
                        report_elements.extend(elements)
                        logger.info(f"📋 Найдено {len(elements)} элементов по селектору: {selector}")
                except Exception as e:
                    logger.warning(f"⚠️ Ошибка поиска по селектору {selector}: {e}")
            
            if not report_elements:
                logger.warning("⚠️ Элементы отчетов не найдены, пробуем поиск по тексту")
                
                # Поиск по тексту на странице
                all_elements = self.driver.find_elements(By.XPATH, "//*[contains(text(), '2024') or contains(text(), '2025')]")
                report_elements = [el for el in all_elements if any(date in el.text for date in ['2024', '2025'])]
            
            logger.info(f"📋 Всего найдено {len(report_elements)} потенциальных отчетов")
            
            # Обрабатываем найденные элементы
            for element in report_elements:
                try:
                    element_text = element.text.strip()
                    
                    # Ищем дату в тексте элемента
                    date_found = None
                    for year in ['2024', '2025']:
                        if year in element_text:
                            # Пробуем извлечь дату
                            import re
                            date_patterns = [
                                r'(\d{1,2}\.\d{1,2}\.\d{4})',
                                r'(\d{1,2}/\d{1,2}/\d{4})',
                                r'(\d{4}-\d{1,2}-\d{1,2})'
                            ]
                            
                            for pattern in date_patterns:
                                match = re.search(pattern, element_text)
                                if match:
                                    try:
                                        date_str = match.group(1)
                                        if '.' in date_str:
                                            date_found = datetime.strptime(date_str, '%d.%m.%Y')
                                        elif '/' in date_str:
                                            date_found = datetime.strptime(date_str, '%d/%m/%Y')
                                        elif '-' in date_str:
                                            date_found = datetime.strptime(date_str, '%Y-%m-%d')
                                        break
                                    except ValueError:
                                        continue
                            
                            if date_found:
                                break
                    
                    if date_found and date_from <= date_found <= date_to:
                        logger.info(f"📅 Найден отчет за {date_found.strftime('%d.%m.%Y')}")
                        
                        # Ищем кнопку скачивания в этом элементе или рядом
                        download_button = None
                        
                        # Поиск кнопки скачивания в элементе
                        try:
                            download_buttons = element.find_elements(By.XPATH, ".//button | .//a")
                            for btn in download_buttons:
                                btn_text = btn.text.lower()
                                if any(word in btn_text for word in ['скачать', 'download', 'excel']):
                                    download_button = btn
                                    break
                        except Exception:
                            pass
                        
                        # Если не найдена в элементе, ищем рядом
                        if not download_button:
                            try:
                                parent = element.find_element(By.XPATH, "./..")
                                download_buttons = parent.find_elements(By.XPATH, ".//button | .//a")
                                for btn in download_buttons:
                                    btn_text = btn.text.lower()
                                    if any(word in btn_text for word in ['скачать', 'download', 'excel']):
                                        download_button = btn
                                        break
                            except Exception:
                                pass
                        
                        if download_button:
                            try:
                                # Прокручиваем к элементу
                                self.driver.execute_script("arguments[0].scrollIntoView(true);", download_button)
                                time.sleep(1)
                                
                                # Кликаем на кнопку скачивания
                                download_button.click()
                                time.sleep(3)
                                
                                # Проверяем, что файл скачался
                                downloaded_file = self._check_downloaded_file()
                                if downloaded_file:
                                    downloaded_files.append(downloaded_file)
                                    logger.info(f"✅ Скачан файл: {downloaded_file}")
                                
                            except Exception as e:
                                logger.warning(f"⚠️ Ошибка при скачивании отчета за {date_found.strftime('%d.%m.%Y')}: {e}")
                        else:
                            logger.warning(f"⚠️ Не найдена кнопка скачивания для отчета за {date_found.strftime('%d.%m.%Y')}")
                    
                except Exception as e:
                    logger.warning(f"⚠️ Ошибка при обработке элемента отчета: {e}")
                    continue
            
            return downloaded_files
            
        except Exception as e:
            logger.error(f"❌ Ошибка при поиске отчетов: {e}")
            return []
    
    def _check_downloaded_file(self) -> Optional[str]:
        """Проверяет, что файл скачался"""
        try:
            # Ждем появления нового файла в папке загрузки
            time.sleep(3)
            
            # Получаем список файлов в папке загрузки
            files = list(self.download_dir.glob("*.xlsx"))
            files.extend(list(self.download_dir.glob("*.xls")))
            
            if files:
                # Возвращаем самый новый файл
                latest_file = max(files, key=os.path.getctime)
                return str(latest_file)
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Ошибка при проверке скачанного файла: {e}")
            return None
    
    def close(self):
        """Закрытие браузера"""
        if self.driver:
            self.driver.quit()
            logger.info("🔒 Браузер закрыт")

def download_wb_reports_advanced(phone: str, password: str, date_from: datetime, date_to: datetime, headless: bool = True) -> List[str]:
    """
    Улучшенная функция для скачивания отчетов
    
    Args:
        phone: Номер телефона для входа
        password: Пароль (не используется, так как нужен SMS код)
        date_from: Начальная дата
        date_to: Конечная дата
        headless: Запуск в фоновом режиме
        
    Returns:
        List[str]: Список скачанных файлов
    """
    downloader = WBAdvancedDownloader(headless=headless)
    
    try:
        # Настройка драйвера
        if not downloader.setup_driver():
            return []
        
        # Вход в систему
        if not downloader.login(phone, password):
            return []
        
        # Переход к отчетам
        if not downloader.navigate_to_reports():
            return []
        
        # Скачивание отчетов
        downloaded_files = downloader.find_and_download_reports(date_from, date_to)
        
        return downloaded_files
        
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}")
        return []
        
    finally:
        downloader.close()

# Streamlit интерфейс
def create_advanced_download_interface():
    """Создание улучшенного интерфейса для скачивания отчетов"""
    
    st.markdown("## 🤖 Автоматическое скачивание отчетов Wildberries (Улучшенная версия)")
    
    st.info("""
    **Улучшенная версия с:**
    - 🔍 Более надежным поиском элементов
    - 🛡️ Лучшей обработкой ошибок
    - 📊 Поддержкой различных форматов страниц
    - ⚡ Автоматической установкой ChromeDriver
    """)
    
    # Форма ввода данных
    with st.form("advanced_download_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            phone = st.text_input("📱 Номер телефона", placeholder="+7XXXXXXXXXX")
            password = st.text_input("🔐 Пароль", type="password", placeholder="Введите пароль")
        
        with col2:
            date_from = st.date_input("📅 Дата начала", value=datetime.now() - timedelta(days=30))
            date_to = st.date_input("📅 Дата окончания", value=datetime.now())
        
        headless = st.checkbox("🖥️ Запуск в фоновом режиме", value=True)
        
        submitted = st.form_submit_button("🚀 Скачать отчеты", type="primary")
    
    if submitted:
        if not phone or not password:
            st.error("❌ Пожалуйста, заполните все поля")
            return
        
        # Конвертируем даты
        date_from_dt = datetime.combine(date_from, datetime.min.time())
        date_to_dt = datetime.combine(date_to, datetime.max.time())
        
        # Показываем прогресс
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        try:
            status_text.text("🔧 Настройка браузера...")
            progress_bar.progress(10)
            
            status_text.text("🔐 Вход в личный кабинет...")
            progress_bar.progress(30)
            
            status_text.text("📊 Поиск отчетов...")
            progress_bar.progress(60)
            
            # Скачивание отчетов
            downloaded_files = download_wb_reports_advanced(
                phone=phone,
                password=password,
                date_from=date_from_dt,
                date_to=date_to_dt,
                headless=headless
            )
            
            progress_bar.progress(100)
            
            if downloaded_files:
                status_text.text("✅ Скачивание завершено!")
                st.success(f"🎉 Успешно скачано {len(downloaded_files)} отчетов:")
                
                for file_path in downloaded_files:
                    file_name = Path(file_path).name
                    st.write(f"📄 {file_name}")
                    
                    # Кнопка для просмотра файла
                    if st.button(f"👁️ Просмотреть {file_name}", key=f"view_{file_name}"):
                        try:
                            df = pd.read_excel(file_path)
                            st.dataframe(df.head(10))
                        except Exception as e:
                            st.error(f"Ошибка при чтении файла: {e}")
            else:
                status_text.text("❌ Отчеты не найдены")
                st.warning("⚠️ Не удалось скачать отчеты. Проверьте:")
                st.write("- Правильность ввода данных")
                st.write("- Наличие отчетов за выбранный период")
                st.write("- Стабильность интернет-соединения")
                
        except Exception as e:
            st.error(f"❌ Ошибка при скачивании: {e}")
            logger.error(f"Ошибка в интерфейсе: {e}")

if __name__ == "__main__":
    # Настройка страницы Streamlit
    st.set_page_config(
        page_title="WB Advanced Auto Downloader",
        page_icon="🤖",
        layout="wide"
    )
    
    create_advanced_download_interface()
