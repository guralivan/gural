# -*- coding: utf-8 -*-
"""
Модуль для автоматической авторизации и загрузки отчетов с сайта service-analytic.com
"""
import os
import time
import streamlit as st
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import tempfile


def setup_driver(headless=True):
    """Настройка Chrome драйвера"""
    chrome_options = Options()
    if headless:
        chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    try:
        # Пробуем использовать webdriver-manager для автоматической установки ChromeDriver
        try:
            from selenium.webdriver.chrome.service import Service
            from webdriver_manager.chrome import ChromeDriverManager
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=chrome_options)
            st.info("✅ ChromeDriver установлен автоматически через webdriver-manager")
        except ImportError:
            # Если webdriver-manager не установлен, используем стандартный способ
            st.info("ℹ️ webdriver-manager не найден, используем стандартный ChromeDriver")
            driver = webdriver.Chrome(options=chrome_options)
        except Exception as e:
            # Если webdriver-manager не сработал, пробуем стандартный способ
            st.warning(f"⚠️ webdriver-manager не сработал: {e}. Пробуем стандартный способ...")
            driver = webdriver.Chrome(options=chrome_options)
        
        return driver
    except Exception as e:
        error_msg = str(e)
        st.error(f"❌ Ошибка инициализации браузера: {error_msg}")
        
        # Более детальные сообщения об ошибках
        if "chromedriver" in error_msg.lower() or "executable" in error_msg.lower():
            st.info("💡 Проблема с ChromeDriver:")
            st.info("   1. Установите: pip install webdriver-manager")
            st.info("   2. Или скачайте ChromeDriver вручную с https://chromedriver.chromium.org/")
            st.info("   3. Убедитесь, что ChromeDriver в PATH")
        elif "chrome" in error_msg.lower() and "not found" in error_msg.lower():
            st.info("💡 Google Chrome не найден:")
            st.info("   1. Установите Google Chrome браузер")
            st.info("   2. Убедитесь, что Chrome доступен в системе")
        else:
            st.info("💡 Установите зависимости: pip install selenium webdriver-manager")
        
        return None


def test_authorization(
    login_url="https://service-analytic.com/login",
    username=None,
    password=None,
    headless=True,
    wait_timeout=30
):
    """
    Тестовая функция для проверки авторизации на сайте
    
    Parameters:
    -----------
    login_url : str
        URL страницы авторизации
    username : str
        Логин для авторизации
    password : str
        Пароль для авторизации
    headless : bool
        Запуск браузера в фоновом режиме
    wait_timeout : int
        Таймаут ожидания элементов (секунды)
    
    Returns:
    --------
    dict
        Словарь с результатами: {'success': bool, 'message': str, 'current_url': str}
    """
    
    driver = None
    try:
        # Настройка драйвера
        st.info("🔧 Инициализация браузера...")
        driver = setup_driver(headless)
        if driver is None:
            return {
                'success': False,
                'message': 'Не удалось инициализировать браузер. Проверьте установку Chrome и ChromeDriver.',
                'current_url': None
            }
        st.success("✅ Браузер инициализирован")
        
        wait = WebDriverWait(driver, wait_timeout)
        
        # Шаг 1: Переход на страницу авторизации
        st.info("🔐 Переход на страницу авторизации...")
        driver.get(login_url)
        time.sleep(3)  # Даем время на загрузку страницы
        
        # Шаг 2: Поиск и заполнение поля логина
        try:
            username_selector = "#root > div.MuiContainer-root.MuiContainer-maxWidthXs.SignIn_container__OyMm-.css-hltdia > form > div:nth-child(1) > div > input"
            username_field = wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, username_selector))
            )
            
            username_field.clear()
            username_field.send_keys(username)
            time.sleep(1)
            
            st.success("✅ Логин введен")
            
        except TimeoutException:
            return {
                'success': False,
                'message': 'Не удалось найти поле логина',
                'current_url': driver.current_url
            }
        
        # Шаг 3: Поиск и заполнение поля пароля
        try:
            password_field = wait.until(
                EC.presence_of_element_located((By.ID, "mui-181"))
            )
            
            password_field.clear()
            password_field.send_keys(password)
            time.sleep(1)
            
            st.success("✅ Пароль введен")
            
        except TimeoutException:
            return {
                'success': False,
                'message': 'Не удалось найти поле пароля',
                'current_url': driver.current_url
            }
        
        # Шаг 4: Поиск и нажатие кнопки входа
        try:
            login_button_selector = "#root > div.MuiContainer-root.MuiContainer-maxWidthXs.SignIn_container__OyMm-.css-hltdia > form > div:nth-child(4) > button"
            login_button = wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, login_button_selector))
            )
            
            # Прокручиваем к кнопке, если нужно
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", login_button)
            time.sleep(0.5)
            
            # Нажимаем кнопку
            login_button.click()
            st.info("🔄 Выполняется вход...")
            time.sleep(5)  # Ожидание перехода после авторизации
            
            # Получаем текущий URL после авторизации
            current_url = driver.current_url
            
            # Проверяем успешность авторизации
            if "login" not in current_url.lower():
                # Проверяем наличие сообщений об ошибке
                try:
                    error_elements = driver.find_elements(By.CSS_SELECTOR, ".error, .MuiAlert-root, [role='alert'], .MuiSnackbar-root")
                    if error_elements:
                        error_text = error_elements[0].text
                        if error_text:
                            return {
                                'success': False,
                                'message': f'Ошибка авторизации: {error_text}',
                                'current_url': current_url
                            }
                except:
                    pass
                
                # Если нет ошибок и URL изменился, считаем авторизацию успешной
                return {
                    'success': True,
                    'message': 'Авторизация успешна!',
                    'current_url': current_url
                }
            else:
                # Все еще на странице логина - проверяем наличие ошибок
                try:
                    error_elements = driver.find_elements(By.CSS_SELECTOR, ".error, .MuiAlert-root, [role='alert'], .MuiSnackbar-root, .MuiFormHelperText-root")
                    if error_elements:
                        error_text = error_elements[0].text
                        if error_text and len(error_text) > 0:
                            return {
                                'success': False,
                                'message': f'Ошибка авторизации: {error_text}',
                                'current_url': current_url
                            }
                except:
                    pass
                
                return {
                    'success': False,
                    'message': 'Авторизация не удалась. Проверьте учетные данные.',
                    'current_url': current_url
                }
                
        except TimeoutException:
            return {
                'success': False,
                'message': 'Не удалось найти кнопку входа',
                'current_url': driver.current_url
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'Ошибка при нажатии кнопки входа: {str(e)}',
                'current_url': driver.current_url if driver else None
            }
        
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        return {
            'success': False,
            'message': f'Ошибка при авторизации: {str(e)}',
            'current_url': driver.current_url if driver else None,
            'trace': error_trace
        }
        
    finally:
        if driver:
            # Сохраняем скриншот перед закрытием (для отладки)
            try:
                screenshot_dir = tempfile.gettempdir()
                screenshot_path = os.path.join(screenshot_dir, f"auth_test_{int(time.time())}.png")
                driver.save_screenshot(screenshot_path)
                st.info(f"📸 Скриншот сохранен: {screenshot_path}")
            except:
                pass
            
            driver.quit()

