# -*- coding: utf-8 -*-
"""
Автоматическое скачивание отчетов с сайта Wildberries
Использует Selenium для веб-автоматизации
"""

import os
import time
import logging
from datetime import datetime, timedelta
from pathlib import Path
import pandas as pd
from typing import Optional, List, Dict
import streamlit as st

try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.common.action_chains import ActionChains
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
        logging.FileHandler('wb_downloader.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class WBReportDownloader:
    """Класс для автоматического скачивания отчетов с Wildberries"""
    
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
        self.login_url = "https://seller.wildberries.ru/suppliers-mutual-settlements/reports-implementations/reports-weekly-new"
        
    def setup_driver(self) -> bool:
        """Настройка веб-драйвера Chrome"""
        try:
            chrome_options = Options()
            
            if self.headless:
                chrome_options.add_argument("--headless")
            
            # Настройки для скачивания файлов
            prefs = {
                "download.default_directory": str(self.download_dir.absolute()),
                "download.prompt_for_download": False,
                "download.directory_upgrade": True,
                "safebrowsing.enabled": True
            }
            chrome_options.add_experimental_option("prefs", prefs)
            
            # Дополнительные настройки
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")
            chrome_options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
            
            # Автоматическая установка ChromeDriver
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.wait = WebDriverWait(self.driver, 20)
            
            logger.info("✅ Веб-драйвер успешно настроен")
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка настройки веб-драйвера: {e}")
            return False
    
    def login(self, phone: str, password: str) -> bool:
        """
        Вход в личный кабинет Wildberries
        
        Args:
            phone: Номер телефона
            password: Пароль
            
        Returns:
            bool: True если вход успешен
        """
        try:
            logger.info("🔐 Начинаем процесс входа в личный кабинет...")
            
            # Переходим на страницу входа
            self.driver.get("https://seller.wildberries.ru/")
            time.sleep(3)
            
            # Ищем кнопку входа
            try:
                login_button = self.wait.until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Войти') or contains(text(), 'Вход')]"))
                )
                login_button.click()
                time.sleep(2)
            except TimeoutException:
                logger.warning("⚠️ Кнопка входа не найдена, возможно уже авторизованы")
            
            # Вводим номер телефона
            try:
                phone_input = self.wait.until(
                    EC.presence_of_element_located((By.XPATH, "//input[@type='tel' or @name='phone' or contains(@placeholder, 'телефон')]"))
                )
                phone_input.clear()
                phone_input.send_keys(phone)
                time.sleep(1)
                
                # Нажимаем "Получить код"
                get_code_button = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Получить код') or contains(text(), 'Отправить код')]")
                get_code_button.click()
                time.sleep(2)
                
                logger.info("📱 Код отправлен на телефон. Ожидаем ввода кода...")
                
                # Ждем ввода кода (пользователь должен ввести вручную)
                st.info("📱 Введите код подтверждения, который пришел на ваш телефон")
                
                # Ждем перехода на главную страницу (признак успешного входа)
                try:
                    self.wait.until(
                        EC.presence_of_element_located((By.XPATH, "//a[contains(@href, 'seller.wildberries.ru')]"))
                    )
                    logger.info("✅ Успешный вход в личный кабинет")
                    return True
                except TimeoutException:
                    logger.error("❌ Не удалось войти в личный кабинет")
                    return False
                    
            except TimeoutException:
                logger.error("❌ Не найден элемент для ввода телефона")
                return False
                
        except Exception as e:
            logger.error(f"❌ Ошибка при входе: {e}")
            return False
    
    def navigate_to_reports(self) -> bool:
        """Переход к странице отчетов"""
        try:
            logger.info("📊 Переходим к странице отчетов...")
            
            # Переходим на страницу отчетов
            self.driver.get(self.login_url)
            time.sleep(3)
            
            # Проверяем, что мы на правильной странице
            if "reports-weekly-new" in self.driver.current_url:
                logger.info("✅ Успешно перешли на страницу отчетов")
                return True
            else:
                logger.error("❌ Не удалось перейти на страницу отчетов")
                return False
                
        except Exception as e:
            logger.error(f"❌ Ошибка при переходе к отчетам: {e}")
            return False
    
    def find_and_download_reports(self, date_from: datetime, date_to: datetime) -> List[str]:
        """
        Поиск и скачивание отчетов за указанный период
        
        Args:
            date_from: Начальная дата
            date_to: Конечная дата
            
        Returns:
            List[str]: Список скачанных файлов
        """
        downloaded_files = []
        
        try:
            logger.info(f"🔍 Ищем отчеты с {date_from.strftime('%d.%m.%Y')} по {date_to.strftime('%d.%m.%Y')}")
            
            # Ждем загрузки таблицы отчетов
            try:
                reports_table = self.wait.until(
                    EC.presence_of_element_located((By.XPATH, "//table[contains(@class, 'table') or contains(@class, 'reports')]"))
                )
            except TimeoutException:
                # Пробуем найти отчеты в другом формате
                reports_table = self.driver.find_element(By.XPATH, "//div[contains(@class, 'reports') or contains(@class, 'table')]")
            
            # Ищем строки с отчетами
            report_rows = self.driver.find_elements(By.XPATH, "//tr[contains(@class, 'report') or td[contains(text(), '2024') or contains(text(), '2025')]]")
            
            if not report_rows:
                # Альтернативный поиск
                report_rows = self.driver.find_elements(By.XPATH, "//div[contains(@class, 'report-item') or contains(@class, 'report-row')]")
            
            logger.info(f"📋 Найдено {len(report_rows)} отчетов")
            
            for row in report_rows:
                try:
                    # Ищем дату в строке
                    date_elements = row.find_elements(By.XPATH, ".//td[contains(text(), '2024') or contains(text(), '2025')] | .//span[contains(text(), '2024') or contains(text(), '2025')]")
                    
                    if date_elements:
                        date_text = date_elements[0].text.strip()
                        
                        # Парсим дату
                        try:
                            report_date = datetime.strptime(date_text.split()[0], '%d.%m.%Y')
                            
                            # Проверяем, попадает ли дата в нужный диапазон
                            if date_from <= report_date <= date_to:
                                logger.info(f"📅 Найден отчет за {report_date.strftime('%d.%m.%Y')}")
                                
                                # Ищем кнопку скачивания
                                download_buttons = row.find_elements(By.XPATH, ".//button[contains(text(), 'Скачать') or contains(text(), 'Excel') or contains(@class, 'download')] | .//a[contains(text(), 'Скачать') or contains(text(), 'Excel')]")
                                
                                if download_buttons:
                                    download_button = download_buttons[0]
                                    
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
                                    
                                else:
                                    logger.warning(f"⚠️ Не найдена кнопка скачивания для отчета за {report_date.strftime('%d.%m.%Y')}")
                                    
                        except ValueError:
                            logger.warning(f"⚠️ Не удалось распарсить дату: {date_text}")
                            continue
                            
                except Exception as e:
                    logger.warning(f"⚠️ Ошибка при обработке строки отчета: {e}")
                    continue
            
            return downloaded_files
            
        except Exception as e:
            logger.error(f"❌ Ошибка при поиске отчетов: {e}")
            return []
    
    def _check_downloaded_file(self) -> Optional[str]:
        """Проверяет, что файл скачался"""
        try:
            # Ждем появления нового файла в папке загрузки
            time.sleep(2)
            
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

def download_wb_reports(phone: str, password: str, date_from: datetime, date_to: datetime, headless: bool = True) -> List[str]:
    """
    Основная функция для скачивания отчетов
    
    Args:
        phone: Номер телефона для входа
        password: Пароль (не используется, так как нужен SMS код)
        date_from: Начальная дата
        date_to: Конечная дата
        headless: Запуск в фоновом режиме
        
    Returns:
        List[str]: Список скачанных файлов
    """
    downloader = WBReportDownloader(headless=headless)
    
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
def create_download_interface():
    """Создание интерфейса для скачивания отчетов"""
    
    st.markdown("## 🤖 Автоматическое скачивание отчетов Wildberries")
    
    st.info("""
    **Инструкция по использованию:**
    1. Введите номер телефона и пароль от личного кабинета WB
    2. Выберите период для скачивания отчетов
    3. Нажмите "Скачать отчеты"
    4. Введите SMS код, который придет на телефон
    5. Дождитесь завершения скачивания
    """)
    
    # Форма ввода данных
    with st.form("download_form"):
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
            downloaded_files = download_wb_reports(
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
        page_title="WB Auto Downloader",
        page_icon="🤖",
        layout="wide"
    )
    
    create_download_interface()
