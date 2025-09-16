# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date
import locale
from io import BytesIO
import json
import os

# Настройка локали для правильного отображения чисел
try:
    locale.setlocale(locale.LC_ALL, 'ru_RU.UTF-8')
except:
    try:
        locale.setlocale(locale.LC_ALL, 'Russian_Russia.1251')
    except:
        pass

# Настройка страницы
st.set_page_config(
    page_title="Таблица товаров с детальным расчетом",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS стили для увеличения высоты заголовков таблиц
st.markdown("""
<style>
    .stDataFrame > div > div > div > div > div > table > thead > tr > th {
        height: 60px !important;
        padding: 12px !important;
        vertical-align: middle !important;
        font-size: 14px !important;
        font-weight: bold !important;
    }
    
    .stDataFrame > div > div > div > div > div > table > tbody > tr > td {
        padding: 8px !important;
        vertical-align: middle !important;
    }
</style>
""", unsafe_allow_html=True)

# Функции форматирования
def format_currency(value, decimals=0):
    """Форматирование валюты с разделителями тысяч"""
    if pd.isna(value) or value == 0:
        return "0 ₽"
    return f"{value:,.{decimals}f}".replace(",", " ").replace(".", ",") + " ₽"

def format_usd(value, decimals=1):
    """Форматирование USD с разделителями тысяч"""
    if pd.isna(value) or value == 0:
        return "0,0 $"
    return f"{value:,.{decimals}f}".replace(",", " ").replace(".", ",") + " $"

def format_percent(value, decimals=1):
    """Форматирование процентов"""
    if pd.isna(value) or value == 0:
        return "0%"
    return f"{value:.{decimals}f}%"

def format_number(value, decimals=0):
    """Форматирование чисел с разделителями тысяч"""
    if pd.isna(value) or value == 0:
        return "0"
    return f"{value:,.{decimals}f}".replace(",", " ").replace(".", ",")

# Функции загрузки сохраненных товаров
def load_saved_products():
    """Загружает список сохраненных товаров"""
    try:
        if not os.path.exists('saved_products'):
            return []
        
        products = []
        for filename in os.listdir('saved_products'):
            if filename.endswith('.json'):
                filepath = os.path.join('saved_products', filename)
                with open(filepath, 'r', encoding='utf-8') as f:
                    product_data = json.load(f)
                    product_data['filename'] = filename
                    products.append(product_data)
        
        # Сортируем по дате создания (новые сначала)
        products.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        return products
    except Exception as e:
        st.error(f"Ошибка загрузки товаров: {e}")
        return []

def save_product(product_data):
    """Сохраняет товар в файл"""
    try:
        if not os.path.exists('saved_products'):
            os.makedirs('saved_products')
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"saved_products/{product_data['product_name']}_{timestamp}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(product_data, f, ensure_ascii=False, indent=2)
        return filename
    except Exception as e:
        st.error(f"Ошибка сохранения: {e}")
        return None

def update_product(filename, product_data):
    """Обновляет существующий товар"""
    try:
        filepath = os.path.join('saved_products', filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(product_data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        st.error(f"Ошибка обновления: {e}")
        return False

def delete_product(filename):
    """Удаляет товар"""
    try:
        filepath = os.path.join('saved_products', filename)
        if os.path.exists(filepath):
            os.remove(filepath)
            return True
    except Exception as e:
        st.error(f"Ошибка удаления: {e}")
    return False

# Функции для тестовых товаров
def load_test_products():
    """Загружает список сохраненных тестовых товаров"""
    try:
        if not os.path.exists('test_products'):
            return []
        
        products = []
        for filename in os.listdir('test_products'):
            if filename.endswith('.json'):
                filepath = os.path.join('test_products', filename)
                with open(filepath, 'r', encoding='utf-8') as f:
                    product_data = json.load(f)
                    product_data['filename'] = filename
                    products.append(product_data)
        
        # Сортируем по дате создания (новые сначала)
        products.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        return products
    except Exception as e:
        st.error(f"Ошибка загрузки тестовых товаров: {e}")
        return []

def save_test_product(product_data):
    """Сохраняет тестовый товар в файл"""
    try:
        if not os.path.exists('test_products'):
            os.makedirs('test_products')
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"test_products/{product_data['product_name']}_{timestamp}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(product_data, f, ensure_ascii=False, indent=2)
        return filename
    except Exception as e:
        st.error(f"Ошибка сохранения тестового товара: {e}")
        return None

def update_test_product(filename, product_data):
    """Обновляет существующий тестовый товар"""
    try:
        filepath = os.path.join('test_products', filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(product_data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        st.error(f"Ошибка обновления тестового товара: {e}")
        return False

def delete_test_product(filename):
    """Удаляет тестовый товар"""
    try:
        filepath = os.path.join('test_products', filename)
        if os.path.exists(filepath):
            os.remove(filepath)
            return True
    except Exception as e:
        st.error(f"Ошибка удаления тестового товара: {e}")
    return False

# Функции для работы с себестоимостью
def load_cost_products():
    """Загружает список сохраненных расчетов себестоимости"""
    try:
        if not os.path.exists('cost_products'):
            return []
        
        products = []
        for filename in os.listdir('cost_products'):
            if filename.endswith('.json'):
                filepath = os.path.join('cost_products', filename)
                with open(filepath, 'r', encoding='utf-8') as f:
                    product_data = json.load(f)
                    product_data['filename'] = filename
                    products.append(product_data)
        
        # Сортируем по дате создания (новые сначала)
        products.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        return products
    except Exception as e:
        st.error(f"Ошибка загрузки расчетов себестоимости: {e}")
        return []

def save_cost_product(product_data):
    """Сохраняет расчет себестоимости в файл"""
    try:
        if not os.path.exists('cost_products'):
            os.makedirs('cost_products')
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"cost_products/{product_data['product_name']}_{timestamp}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(product_data, f, ensure_ascii=False, indent=2)
        return filename
    except Exception as e:
        st.error(f"Ошибка сохранения расчета себестоимости: {e}")
        return None

def update_cost_product(filename, product_data):
    """Обновляет существующий расчет себестоимости"""
    try:
        filepath = os.path.join('cost_products', filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(product_data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        st.error(f"Ошибка обновления расчета себестоимости: {e}")
        return False

def delete_cost_product(filename):
    """Удаляет расчет себестоимости"""
    try:
        filepath = os.path.join('cost_products', filename)
        if os.path.exists(filepath):
            os.remove(filepath)
            return True
        return False
    except Exception as e:
        st.error(f"Ошибка удаления расчета себестоимости: {e}")
        return False

def update_products_cost_price(product_name, new_cost_price):
    """Обновляет себестоимость в основных и тестовых товарах"""
    updated_count = 0
    
    # Обновляем основные товары
    main_products = load_saved_products()
    st.write(f"🔍 Ищем товар '{product_name}' в {len(main_products)} основных товарах")
    for product in main_products:
        if product['product_name'] == product_name:
            st.write(f"✅ Найден основной товар: {product['product_name']}, старая себестоимость: {product.get('cost_price', 'не задана')}")
            product['cost_price'] = new_cost_price
            if update_product(product['filename'], product):
                st.write(f"✅ Обновлен основной товар: {product['product_name']}, новая себестоимость: {new_cost_price}")
                updated_count += 1
            else:
                st.write(f"❌ Ошибка обновления основного товара: {product['product_name']}")
    
    # Обновляем тестовые товары
    test_products = load_test_products()
    st.write(f"🔍 Ищем товар '{product_name}' в {len(test_products)} тестовых товарах")
    for product in test_products:
        if product['product_name'] == product_name:
            st.write(f"✅ Найден тестовый товар: {product['product_name']}, старая себестоимость: {product.get('cost_price', 'не задана')}")
            product['cost_price'] = new_cost_price
            if update_test_product(product['filename'], product):
                st.write(f"✅ Обновлен тестовый товар: {product['product_name']}, новая себестоимость: {new_cost_price}")
                updated_count += 1
            else:
                st.write(f"❌ Ошибка обновления тестового товара: {product['product_name']}")
    
    st.write(f"📊 Всего обновлено товаров: {updated_count}")
    return updated_count

def calculate_cost_price(
    price_yuan,
    delivery_russia_usd,
    logistics_china,
    weight,
    quantity,
    ff,
    development,
    other_expenses,
    yuan_rate, 
    usd_rate
):
    """Рассчитывает себестоимость товара"""
    # Стоимость товара в рублях в Китае (за единицу)
    price_rub_china_per_unit = price_yuan * yuan_rate
    
    # Общая стоимость товара в рублях в Китае (на всю партию)
    price_rub_china_total = price_rub_china_per_unit * quantity
    
    # Автоматический расчет логистики из Китая (вес в граммах, переводим в кг для расчета)
    logistics_china_per_unit = (weight / 1000) * delivery_russia_usd * usd_rate  # Логистика на единицу в рублях
    logistics_china_total = logistics_china_per_unit * quantity  # Общая логистика в рублях
    
    # Если логистика указана вручную, используем её
    if logistics_china > 0:
        logistics_china_total = logistics_china
        logistics_china_per_unit = logistics_china / quantity if quantity > 0 else 0
    
    # ФФ на единицу товара
    ff_per_unit = ff / quantity if quantity > 0 else 0
    
    # Разработка на единицу товара (общая сумма делится на количество)
    development_per_unit = development / quantity if quantity > 0 else 0
    
    # Прочие расходы на единицу товара (общая сумма делится на количество)
    other_expenses_per_unit = other_expenses / quantity if quantity > 0 else 0
    
    # Себестоимость на единицу товара (включает все затраты на единицу)
    # Стоимость в Китае на единицу + логистика из Китая на единицу + ФФ на единицу + разработка на единицу + прочие расходы на единицу
    cost_per_unit = price_rub_china_per_unit + logistics_china_per_unit + ff_per_unit + development_per_unit + other_expenses_per_unit
    
    # Общая себестоимость всей партии
    # Общая стоимость в Китае (в рублях) + логистика из Китая + ФФ + разработка + прочие расходы
    total_cost = price_rub_china_total + logistics_china_total + ff + development + other_expenses
    
    return {
        'price_rub_china': price_rub_china_total,  # Общая стоимость в Китае в рублях
        'price_rub_china_per_unit': price_rub_china_per_unit,  # Стоимость за единицу в Китае в рублях
        'cost_per_unit': cost_per_unit,
        'total_cost': total_cost,
        'logistics_china_per_unit': logistics_china_per_unit,
        'logistics_china_total': logistics_china_total,
        'ff_per_unit': ff_per_unit,
        'ff_total': ff,
        'development_per_unit': development_per_unit,
        'development_total': development,
        'other_expenses_per_unit': other_expenses_per_unit,
        'other_expenses_total': other_expenses
    }

# Функции расчета
def calculate_unit_economics(
    cost_price,           # Себестоимость
    retail_price,         # Текущая розн. цена (до скидки)
    discount_percent,     # Текущая скидка на сайте, %
    commission_rate,      # Комиссия, тариф базовый
    logistics_cost,       # Логистика тариф, руб
    advertising_percent,  # Реклама как доля от цены продажи, %
    buyout_percent,       # % выкупа
    storage_cost=0,       # Хранение (опционально)
    stock_quantity=0,     # Остаток товара
    purchased_quantity=0, # Закуплено товара
    spp_discount=25.0     # СПП скидка
):
    """Расчет юнит-экономики по формулам из таблицы"""
    
    # 1. Цена со скидкой
    price_with_discount = retail_price * (1 - discount_percent / 100)
    
    # 2. Цена с учетом СПП (не участвует в расчетах)
    price_with_spp = price_with_discount * (1 - spp_discount / 100)
    
    # 3. Комиссия в рублях
    commission_amount = price_with_discount * (commission_rate / 100)
    
    # 4. Реклама как доля от цены продажи
    advertising_cost = price_with_discount * (advertising_percent / 100)
    
    # 5. Доставка с учетом выкупа
    delivery_with_buyout = (buyout_percent/100 * logistics_cost + (1 - buyout_percent/100) * (logistics_cost + 50)) * 100 / buyout_percent
    
    # 6. Выручка с единицы (после комиссии, логистики с учетом выкупа, рекламы и хранения)
    revenue_per_unit = price_with_discount - commission_amount - delivery_with_buyout - advertising_cost - storage_cost
    
    # 7. Налог с единицы (7%)
    tax_per_unit = price_with_discount * 0.07
    
    # 8. Прибыль с единицы (после всех затрат)
    profit_per_unit = revenue_per_unit - cost_price - tax_per_unit
    
    # 9. Маржинальность (%)
    margin_percent = (profit_per_unit / price_with_discount) * 100 if price_with_discount > 0 else 0
    
    # 10. Рентабельность (%)
    profitability_percent = (profit_per_unit / cost_price) * 100 if cost_price > 0 else 0
    
    # 11. Прибыль с учетом выкупа
    profit_with_buyout = profit_per_unit * (buyout_percent / 100)
    
    # 12. Расчеты с остатками
    revenue_from_stock_no_tax = revenue_per_unit * stock_quantity
    revenue_from_stock_with_tax = revenue_from_stock_no_tax * 0.93
    stock_cost = cost_price * stock_quantity
    profit_from_stock = profit_per_unit * stock_quantity
    
    # 13. Расчет проданного товара
    sold_quantity = purchased_quantity - stock_quantity
    
    return {
        'Цена со скидкой': price_with_discount,
        'Цена с учетом СПП': price_with_spp,
        'Комиссия, руб': commission_amount,
        'Выручка с ед.': revenue_per_unit,
        'Реклама, руб': advertising_cost,
        'Налог с ед., руб': tax_per_unit,
        'Доставка с учетом выкупа': delivery_with_buyout,
        'Прибыль с ед.': profit_per_unit,
        'Прибыль с учетом выкупа': profit_with_buyout,
        'Маржинальность, %': margin_percent,
        'Рентабельность, %': profitability_percent,
        'Выручка с остатков без налога': revenue_from_stock_no_tax,
        'Выручка с остатков с налогом 7%': revenue_from_stock_with_tax,
        'Себестоимость остатков': stock_cost,
        'Прибыль с остатков': profit_from_stock,
        'Продано товара': sold_quantity
    }



# Основное приложение
def main():
    st.title("📊 Таблица товаров с детальным расчетом")
    st.markdown("---")
    
    # Загружаем сохраненные товары
    saved_products = load_saved_products()
    
    # Сайдбар для управления товарами
    with st.sidebar:
        st.header("🔧 Управление товарами")
        
        # Форма создания нового товара
        with st.expander("➕ Добавить новый товар", expanded=False):
            st.subheader("📝 Создание нового товара")
            
            product_name = st.text_input("Название товара", key="new_product_name")
            product_type = st.text_input("Тип товара", key="new_product_type")
            cost_price = st.number_input("Себестоимость, ₽", min_value=0.0, value=1000.0, step=10.0, key="new_cost_price")
            retail_price = st.number_input("Розничная цена (до скидки), ₽", min_value=0.0, value=1500.0, step=10.0, key="new_retail_price")
            discount_percent = st.number_input("Скидка на сайте, %", min_value=0.0, max_value=100.0, value=10.0, step=1.0, key="new_discount_percent")
            commission_rate = st.number_input("Комиссия, %", min_value=0.0, max_value=100.0, value=5.0, step=0.1, key="new_commission_rate")
            logistics_cost = st.number_input("Логистика, ₽", min_value=0.0, value=100.0, step=10.0, key="new_logistics_cost")
            advertising_percent = st.number_input("Реклама, % от цены", min_value=0.0, max_value=100.0, value=5.0, step=0.1, key="new_advertising_percent")
            buyout_percent = st.number_input("% выкупа", min_value=0.0, max_value=100.0, value=80.0, step=1.0, key="new_buyout_percent")
            storage_cost = st.number_input("Хранение, ₽", min_value=0.0, value=0.0, step=10.0, key="new_storage_cost")
            purchased_quantity = st.number_input("Закуплено товара, шт", min_value=0, value=200, step=1, key="new_purchased_quantity")
            stock_quantity = st.number_input("Остаток товара, шт", min_value=0, value=100, step=1, key="create_stock_quantity")
            spp_discount = st.number_input("СПП скидка, %", min_value=0.0, max_value=100.0, value=25.0, step=1.0, key="new_spp_discount")
            
            if st.button("💾 Сохранить товар", type="primary", use_container_width=True, key="save_main_product"):
                if product_name:
                    # Создаем данные товара
                    product_data = {
                        'product_name': product_name,
                        'product_type': product_type,
                        'cost_price': cost_price,
                        'retail_price': retail_price,
                        'discount_percent': discount_percent,
                        'commission_rate': commission_rate,
                        'logistics_cost': logistics_cost,
                        'advertising_percent': advertising_percent,
                        'buyout_percent': buyout_percent,
                        'storage_cost': storage_cost,
                        'purchased_quantity': purchased_quantity,
                        'stock_quantity': stock_quantity,
                        'spp_discount': spp_discount,
                        'timestamp': datetime.now().isoformat(),
                        'created_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    }
                    
                    # Сохраняем товар
                    filename = save_product(product_data)
                    if filename:
                        st.success(f"✅ Товар '{product_name}' успешно сохранен!")
                        st.rerun()
                else:
                    st.error("❌ Введите название товара!")
        
        # Форма редактирования товаров
        if saved_products:
            with st.expander("✏️ Редактировать товар", expanded=False):
                st.subheader("📝 Редактирование товара")
                
                # Выбор товара для редактирования
                edit_product_names = [p['product_name'] for p in saved_products]
                selected_edit_product = st.selectbox(
                    "Выберите товар для редактирования:",
                    options=edit_product_names,
                    key="edit_product_select"
                )
                
                if selected_edit_product:
                    # Находим выбранный товар
                    edit_product = None
                    for product in saved_products:
                        if product['product_name'] == selected_edit_product:
                            edit_product = product
                            break
                    
                    if edit_product:
                        edit_product_name = st.text_input("Название товара", value=edit_product['product_name'], key="edit_product_name")
                        edit_product_type = st.text_input("Тип товара", value=edit_product.get('product_type', ''), key="edit_product_type")
                        edit_cost_price = st.number_input("Себестоимость, ₽", min_value=0.0, value=float(edit_product['cost_price']), step=10.0, key="edit_cost_price")
                        edit_retail_price = st.number_input("Розничная цена (до скидки), ₽", min_value=0.0, value=float(edit_product['retail_price']), step=10.0, key="edit_retail_price")
                        edit_discount_percent = st.number_input("Скидка на сайте, %", min_value=0.0, max_value=100.0, value=float(edit_product['discount_percent']), step=1.0, key="edit_discount_percent")
                        edit_commission_rate = st.number_input("Комиссия, %", min_value=0.0, max_value=100.0, value=float(edit_product['commission_rate']), step=0.1, key="edit_commission_rate")
                        edit_logistics_cost = st.number_input("Логистика, ₽", min_value=0.0, value=float(edit_product['logistics_cost']), step=10.0, key="edit_logistics_cost")
                        edit_advertising_percent = st.number_input("Реклама, % от цены", min_value=0.0, max_value=100.0, value=float(edit_product['advertising_percent']), step=0.1, key="edit_advertising_percent")
                        edit_buyout_percent = st.number_input("% выкупа", min_value=0.0, max_value=100.0, value=float(edit_product['buyout_percent']), step=1.0, key="edit_buyout_percent")
                        edit_storage_cost = st.number_input("Хранение, ₽", min_value=0.0, value=float(edit_product['storage_cost']), step=10.0, key="edit_storage_cost")
                        edit_purchased_quantity = st.number_input("Закуплено товара, шт", min_value=0, value=int(edit_product.get('purchased_quantity', 200)), step=1, key="edit_purchased_quantity")
                        edit_stock_quantity = st.number_input("Остаток товара, шт", min_value=0, value=int(edit_product['stock_quantity']), step=1, key="edit_stock_quantity")
                        edit_spp_discount = st.number_input("СПП скидка, %", min_value=0.0, max_value=100.0, value=float(edit_product['spp_discount']), step=1.0, key="edit_spp_discount")
                        
                        if st.button("💾 Сохранить изменения", type="primary", use_container_width=True, key="update_main_product"):
                            if edit_product_name:
                                # Обновляем данные товара
                                edit_product.update({
                                    'product_name': edit_product_name,
                                    'product_type': edit_product_type,
                                    'cost_price': edit_cost_price,
                                    'retail_price': edit_retail_price,
                                    'discount_percent': edit_discount_percent,
                                    'commission_rate': edit_commission_rate,
                                    'logistics_cost': edit_logistics_cost,
                                    'advertising_percent': edit_advertising_percent,
                                    'buyout_percent': edit_buyout_percent,
                                    'storage_cost': edit_storage_cost,
                                    'purchased_quantity': edit_purchased_quantity,
                                    'stock_quantity': edit_stock_quantity,
                                    'spp_discount': edit_spp_discount,
                                    'updated_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                                })
                                
                                # Сохраняем изменения
                                if update_product(edit_product['filename'], edit_product):
                                    st.success(f"✅ Товар '{edit_product_name}' успешно обновлен!")
                                    st.rerun()
                            else:
                                st.error("❌ Введите название товара!")
        
        # Форма удаления товаров
        if saved_products:
            with st.expander("🗑️ Удалить товар", expanded=False):
                st.subheader("🗑️ Удаление товара")
                
                # Выбор товара для удаления
                delete_product_names = [p['product_name'] for p in saved_products]
                selected_delete_product = st.selectbox(
                    "Выберите товар для удаления:",
                    options=delete_product_names,
                    key="delete_product_select"
                )
                
                if selected_delete_product:
                    # Находим выбранный товар
                    delete_product_data = None
                    for product in saved_products:
                        if product['product_name'] == selected_delete_product:
                            delete_product_data = product
                            break
                    
                    if delete_product_data:
                        st.warning(f"⚠️ Вы собираетесь удалить товар: **{selected_delete_product}**")
                        st.info(f"Тип: {delete_product_data.get('product_type', 'Не указан')}")
                        
                        if st.button("🗑️ Удалить товар", type="secondary", use_container_width=True, key="delete_main_product"):
                            if delete_product(delete_product_data['filename']):
                                st.success(f"✅ Товар '{selected_delete_product}' успешно удален!")
                                st.rerun()
                        if st.button("❌ Отмена", use_container_width=True, key="cancel_delete_main"):
                            st.info("Удаление отменено")
        

    
    # Создаем вкладки
    tab1, tab2, tab3 = st.tabs(["📊 Основные товары", "🧪 Тестовые товары", "💰 Себестоимость"])
    
    with tab1:
        # Основные товары
        if not saved_products:
            st.warning("📝 Сохраненных товаров нет.")
            return
        
        # Показываем ВСЕ товары без фильтрации
        # Рассчитываем показатели для всех товаров
        filtered_products = []
        for product in saved_products:
            # Рассчитываем показатели для каждого товара
            results = calculate_unit_economics(
                cost_price=product['cost_price'],
                retail_price=product['retail_price'],
                discount_percent=product['discount_percent'],
                commission_rate=product['commission_rate'],
                logistics_cost=product['logistics_cost'],
                advertising_percent=product['advertising_percent'],
                buyout_percent=product['buyout_percent'],
                storage_cost=product['storage_cost'],
                stock_quantity=product['stock_quantity'],
                purchased_quantity=product.get('purchased_quantity', 0),
                spp_discount=product['spp_discount']
            )
            
            # Добавляем результаты к товару
            product['results'] = results
            filtered_products.append(product)
        
        if not filtered_products:
            st.warning("🔍 Нет товаров для отображения.")
            return
        
        # Устанавливаем сортировку по умолчанию (по типу товара)
        sort_by = "Тип товара"
        
        # Сортируем товары
        if sort_by == "Тип товара":
            filtered_products.sort(key=lambda x: (x.get('product_type', 'Другое'), x['product_name']))
        elif sort_by == "Название товара":
            filtered_products.sort(key=lambda x: x['product_name'])
        elif sort_by == "Рентабельность (по убыванию)":
            filtered_products.sort(key=lambda x: x['results']['Рентабельность, %'], reverse=True)
        elif sort_by == "Прибыль с ед. (по убыванию)":
            filtered_products.sort(key=lambda x: x['results']['Прибыль с ед.'], reverse=True)
        elif sort_by == "Выручка с ед. (по убыванию)":
            filtered_products.sort(key=lambda x: x['results']['Выручка с ед.'], reverse=True)
        elif sort_by == "Дата создания (новые сначала)":
            filtered_products.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        
        # Раздел для быстрого редактирования остатков
        with st.expander("📊 Быстрое редактирование остатков", expanded=False):
            st.subheader("📝 Изменение остатков товаров")
            
            # Создаем колонки для выбора товара и ввода нового остатка
            col1, col2, col3 = st.columns([2, 1, 1])
            
            with col1:
                # Выбор товара для редактирования остатка
                stock_edit_product_names = [p['product_name'] for p in filtered_products]
                selected_stock_edit_product = st.selectbox(
                    "Выберите товар для изменения остатка:",
                    options=stock_edit_product_names,
                    key="stock_edit_product_select"
                )
            
            if selected_stock_edit_product:
                # Находим выбранный товар
                stock_edit_product = None
                for product in filtered_products:
                    if product['product_name'] == selected_stock_edit_product:
                        stock_edit_product = product
                        break
                
                if stock_edit_product:
                    with col2:
                        st.write(f"**Текущий остаток:**")
                        st.write(f"**{stock_edit_product['stock_quantity']} шт.**")
                    
                    with col3:
                        st.write(f"**Закуплено:**")
                        st.write(f"**{stock_edit_product.get('purchased_quantity', 0)} шт.**")
                    
                    # Показываем информацию о товаре
                    st.write(f"**Товар:** {selected_stock_edit_product}")
                    st.write(f"**Продано:** {stock_edit_product.get('purchased_quantity', 0) - stock_edit_product['stock_quantity']} шт.")
                    
                    # Создаем колонки для ввода нового остатка и кнопки
                    col_input, col_button = st.columns([1, 2])
                    
                    with col_input:
                        new_stock_quantity = st.number_input(
                            "Новый остаток, шт", 
                            min_value=0, 
                            value=int(stock_edit_product['stock_quantity']), 
                            step=1, 
                            key="new_stock_quantity"
                        )
                    
                    with col_button:
                        if st.button("💾 Обновить остаток", type="primary", use_container_width=True, key="update_stock_quantity"):
                            if new_stock_quantity != stock_edit_product['stock_quantity']:
                                old_stock = stock_edit_product['stock_quantity']
                                
                                # Обновляем остаток
                                stock_edit_product['stock_quantity'] = new_stock_quantity
                                
                                # Пересчитываем результаты
                                stock_edit_product['results'] = calculate_unit_economics(
                                    cost_price=stock_edit_product['cost_price'],
                                    retail_price=stock_edit_product['retail_price'],
                                    discount_percent=stock_edit_product['discount_percent'],
                                    commission_rate=stock_edit_product['commission_rate'],
                                    logistics_cost=stock_edit_product['logistics_cost'],
                                    advertising_percent=stock_edit_product['advertising_percent'],
                                    storage_cost=stock_edit_product['storage_cost'],
                                    buyout_percent=stock_edit_product['buyout_percent'],
                                    stock_quantity=new_stock_quantity,
                                    purchased_quantity=stock_edit_product.get('purchased_quantity', 0),
                                    spp_discount=stock_edit_product['spp_discount']
                                )
                                
                                # Сохраняем обновленный товар
                                save_product(stock_edit_product['filename'], stock_edit_product)
                                
                                st.success(f"✅ Остаток товара '{selected_stock_edit_product}' обновлен: {old_stock} → {new_stock_quantity}")
                                st.rerun()
                            else:
                                st.info("Остаток не изменился")
        
        # Создаем общую таблицу
        st.subheader(f"📋 Общая таблица товаров ({len(filtered_products)} из {len(saved_products)})")
        
        # Подготавливаем данные для таблицы с промежуточными итогами
        table_data = []
        
        # Группируем товары по типам
        products_by_type = {}
        for product in filtered_products:
            product_type = product.get('product_type', 'Другое')
            if product_type not in products_by_type:
                products_by_type[product_type] = []
            products_by_type[product_type].append(product)
    
        # Сортируем типы товаров
        sorted_types = sorted(products_by_type.keys())
        
        # Создаем данные для таблицы с промежуточными итогами
        for product_type in sorted_types:
            products = products_by_type[product_type]
            
            # Добавляем товары данного типа
            for product in products:
                results = product['results']
                table_data.append({
                    'Тип': product_type,
                    'Товар': product['product_name'],
                    'Себестоимость': format_currency(product['cost_price']),
                    'Розничная цена': format_currency(product['retail_price']),
                    'Скидка': format_percent(product['discount_percent']),
                    'Цена со скидкой': format_currency(results['Цена со скидкой']),
                    'Комиссия': format_percent(product['commission_rate']),
                    'Логистика': format_currency(product['logistics_cost']),
                    'Реклама': format_percent(product['advertising_percent']),
                    '% выкупа': format_percent(product['buyout_percent']),
                    'Закуплено': format_number(product.get('purchased_quantity', 0)),
                    'Остаток': format_number(product['stock_quantity']),
                    'Продано': format_number(results['Продано товара']),
                    'Выручка с ед.': format_currency(results['Выручка с ед.']),
                    'Прибыль с ед.': format_currency(results['Прибыль с ед.']),
                    'Маржинальность': format_percent(results['Маржинальность, %']),
                    'Рентабельность': format_percent(results['Рентабельность, %']),
                    'Выручка с остатков (без налога)': format_currency(results['Выручка с остатков без налога']),
                    'Выручка с остатков (с налогом)': format_currency(results['Выручка с остатков с налогом 7%']),
                    'Себестоимость остатков': format_currency(results['Себестоимость остатков']),
                    'Прибыль с остатков': format_currency(results['Прибыль с остатков']),
                    'Дата создания': product.get('created_date', 'Неизвестно')
                })
            
            # Добавляем промежуточный итог по типу
            if len(products) > 1:
                type_total_row = {
                    'Тип': f"ИТОГО по {product_type}",
                    'Товар': f"({len(products)} товаров)",
                    'Себестоимость': '-',
                    'Розничная цена': '-',
                    'Скидка': '-',
                    'Цена со скидкой': '-',
                    'Комиссия': '-',
                    'Логистика': '-',
                    'Реклама': '-',
                    '% выкупа': '-',
                    'Закуплено': format_number(sum(p.get('purchased_quantity', 0) for p in products)),
                    'Остаток': format_number(sum(p['stock_quantity'] for p in products)),
                    'Продано': format_number(sum(p['results']['Продано товара'] for p in products)),
                    'Выручка с ед.': '-',
                    'Прибыль с ед.': '-',
                    'Маржинальность': format_percent(sum(p['results']['Маржинальность, %'] for p in products) / len(products)),
                    'Рентабельность': format_percent(sum(p['results']['Рентабельность, %'] for p in products) / len(products)),
                    'Выручка с остатков (без налога)': format_currency(sum(p['results']['Выручка с остатков без налога'] for p in products)),
                    'Выручка с остатков (с налогом)': format_currency(sum(p['results']['Выручка с остатков с налогом 7%'] for p in products)),
                    'Себестоимость остатков': format_currency(sum(p['results']['Себестоимость остатков'] for p in products)),
                    'Прибыль с остатков': format_currency(sum(p['results']['Прибыль с остатков'] for p in products)),
                    'Дата создания': '-'
                }
                table_data.append(type_total_row)
        
        # Отображаем таблицу с цветовым выделением
        df_table = pd.DataFrame(table_data)
    
        # Функция для стилизации строк
        def highlight_rows(row):
            """Выделяет цветом промежуточные итоги и общий итог"""
            if 'ИТОГО по' in str(row['Тип']):
                return ['background-color: #e6f3ff'] * len(row)  # Голубой для промежуточных итогов
            elif row['Тип'] == 'ИТОГО':
                return ['background-color: #ffe6e6'] * len(row)  # Красный для общего итога
            else:
                return [''] * len(row)
        
        # Добавляем строку итого
        if len(table_data) > 0:
            # Создаем данные для строки итого
            total_row = {
                'Тип': 'ИТОГО',
                'Товар': f"({len(filtered_products)} товаров)",
                'Себестоимость': '-',
            'Розничная цена': '-',
            'Скидка': '-',
            'Цена со скидкой': '-',
            'Комиссия': '-',
            'Логистика': '-',
            'Реклама': '-',
            '% выкупа': '-',
            'Закуплено': format_number(sum(product.get('purchased_quantity', 0) for product in filtered_products)),
            'Остаток': format_number(sum(product['stock_quantity'] for product in filtered_products)),
            'Продано': format_number(sum(product['results']['Продано товара'] for product in filtered_products)),
            'Выручка с ед.': '-',
            'Прибыль с ед.': '-',
            'Маржинальность': format_percent(sum(product['results']['Маржинальность, %'] for product in filtered_products) / len(filtered_products)),
            'Рентабельность': format_percent(sum(product['results']['Рентабельность, %'] for product in filtered_products) / len(filtered_products)),
            'Выручка с остатков (без налога)': format_currency(sum(product['results']['Выручка с остатков без налога'] for product in filtered_products)),
            'Выручка с остатков (с налогом)': format_currency(sum(product['results']['Выручка с остатков с налогом 7%'] for product in filtered_products)),
            'Себестоимость остатков': format_currency(sum(product['results']['Себестоимость остатков'] for product in filtered_products)),
            'Прибыль с остатков': format_currency(sum(product['results']['Прибыль с остатков'] for product in filtered_products)),
            'Дата создания': '-'
        }
        
        # Добавляем строку итого в DataFrame
        df_table = pd.concat([df_table, pd.DataFrame([total_row])], ignore_index=True)
    
    # Применяем стили к таблице
    styled_df = df_table.style.apply(highlight_rows, axis=1)
    
    # Отображаем таблицу основных товаров (только для просмотра)
    st.dataframe(
        styled_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Тип": st.column_config.TextColumn("Тип", width="medium"),
            "Товар": st.column_config.TextColumn("Товар", width="medium"),
            "Себестоимость": st.column_config.TextColumn("Себестоимость", width="medium"),
            "Розничная цена": st.column_config.TextColumn("Розничная цена", width="medium"),
            "Скидка": st.column_config.TextColumn("Скидка", width="medium"),
            "Цена со скидкой": st.column_config.TextColumn("Цена со скидкой", width="medium"),
            "Комиссия": st.column_config.TextColumn("Комиссия", width="medium"),
            "Логистика": st.column_config.TextColumn("Логистика", width="medium"),
            "Реклама": st.column_config.TextColumn("Реклама", width="medium"),
            "% выкупа": st.column_config.TextColumn("% выкупа", width="medium"),
            "Закуплено": st.column_config.TextColumn("Закуплено", width="medium"),
            "Остаток": st.column_config.TextColumn("Остаток", width="medium"),
            "Продано": st.column_config.TextColumn("Продано", width="medium"),
            "Выручка с ед.": st.column_config.TextColumn("Выручка с ед.", width="medium"),
            "Прибыль с ед.": st.column_config.TextColumn("Прибыль с ед.", width="medium"),
            "Маржинальность": st.column_config.TextColumn("Маржинальность", width="medium"),
            "Рентабельность": st.column_config.TextColumn("Рентабельность", width="medium"),
            "Выручка с остатков (без налога)": st.column_config.TextColumn("Выручка с остатков (без налога)", width="medium"),
            "Выручка с остатков (с налогом)": st.column_config.TextColumn("Выручка с остатков (с налогом)", width="medium"),
            "Себестоимость остатков": st.column_config.TextColumn("Себестоимость остатков", width="medium"),
            "Прибыль с остатков": st.column_config.TextColumn("Прибыль с остатков", width="medium"),
            "Дата создания": st.column_config.TextColumn("Дата создания", width="medium")
        }
    )
    
    # Общий расчет по всем товарам
    st.subheader("📊 Общий расчет по всем товарам")
            
    # Рассчитываем общие показатели
    total_purchased = sum(product.get('purchased_quantity', 0) for product in filtered_products)
    total_stock = sum(product['stock_quantity'] for product in filtered_products)
    total_sold = sum(product['results']['Продано товара'] for product in filtered_products)
    total_revenue_no_tax = sum(product['results']['Выручка с остатков без налога'] for product in filtered_products)
    total_revenue_with_tax = sum(product['results']['Выручка с остатков с налогом 7%'] for product in filtered_products)
    total_stock_cost = sum(product['results']['Себестоимость остатков'] for product in filtered_products)
    total_profit_from_stock = sum(product['results']['Прибыль с остатков'] for product in filtered_products)
    
    # Средние показатели
    avg_margin = sum(product['results']['Маржинальность, %'] for product in filtered_products) / len(filtered_products) if filtered_products else 0
    avg_profitability = sum(product['results']['Рентабельность, %'] for product in filtered_products) / len(filtered_products) if filtered_products else 0
    avg_profit_per_unit = sum(product['results']['Прибыль с ед.'] for product in filtered_products) / len(filtered_products) if filtered_products else 0
    avg_revenue_per_unit = sum(product['results']['Выручка с ед.'] for product in filtered_products) / len(filtered_products) if filtered_products else 0
    
    # Общий расчет в 4 колонках
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("### 📦 Общие показатели товаров")
        st.metric("Всего товаров", len(filtered_products))
        st.metric("Закуплено товаров", format_number(total_purchased))
        st.metric("Остаток товаров", format_number(total_stock))
        st.metric("Продано товаров", format_number(total_sold))
    
    with col2:
        st.markdown("### 💰 Общая выручка")
        st.metric("Выручка (без налога)", format_currency(total_revenue_no_tax))
        st.metric("Выручка (с налогом 7%)", format_currency(total_revenue_with_tax))
        st.metric("Себестоимость остатков", format_currency(total_stock_cost))
        st.metric("Прибыль с остатков", format_currency(total_profit_from_stock))
    
    with col3:
        st.markdown("### 📊 Средние показатели")
        st.metric("Средняя маржинальность", format_percent(avg_margin))
        st.metric("Средняя рентабельность", format_percent(avg_profitability))
        st.metric("Средняя прибыль с ед.", format_currency(avg_profit_per_unit))
        st.metric("Средняя выручка с ед.", format_currency(avg_revenue_per_unit))
    
    with col4:
        st.markdown("### 🎯 Ключевые метрики")
        if total_purchased > 0:
            sell_through_rate = (total_sold / total_purchased) * 100
            st.metric("Процент продаж", format_percent(sell_through_rate))
        else:
            st.metric("Процент продаж", "0%")
        
        if total_revenue_no_tax > 0:
            profit_margin = (total_profit_from_stock / total_revenue_no_tax) * 100
            st.metric("Общая рентабельность", format_percent(profit_margin))
        else:
            st.metric("Общая рентабельность", "0%")
        
        if total_stock_cost > 0:
            roi = (total_profit_from_stock / total_stock_cost) * 100
            st.metric("ROI остатков", format_percent(roi))
        else:
            st.metric("ROI остатков", "0%")
        
        if len(filtered_products) > 0:
            avg_price = sum(product['retail_price'] for product in filtered_products) / len(filtered_products)
            st.metric("Средняя цена", format_currency(avg_price))
        else:
            st.metric("Средняя цена", "0 ₽")
        
    # Детальный расчет для каждого товара
    st.markdown("---")
    st.subheader("🔍 Детальный расчет по товарам")
    
    # Выбор товара для детального просмотра
    selected_for_detail = st.selectbox(
        "Выберите товар для детального просмотра:",
        options=[p['product_name'] for p in filtered_products],
        help="Выберите товар, чтобы увидеть полный детальный расчет"
    )
    
    # Находим выбранный товар
    selected_product = None
    for product in filtered_products:
        if product['product_name'] == selected_for_detail:
            selected_product = product
            break
    
    if selected_product:
        results = selected_product['results']
        
        # Детальный расчет
        col1, col2, col3, col4 = st.columns(4)
    
        with col1:
                st.markdown(f"### 💰 Цены - {selected_product['product_name']}")
                st.metric("Розничная цена", format_currency(selected_product['retail_price']))
                st.metric("Скидка", format_percent(selected_product['discount_percent']))
                st.metric("Цена со скидкой", format_currency(results['Цена со скидкой']))
                st.metric("СПП скидка", format_percent(selected_product['spp_discount']))
                st.metric("Цена с учетом СПП", format_currency(results['Цена с учетом СПП']))
            
        with col2:
            st.markdown("### 📊 Результаты")
            st.metric("Выручка с ед.", format_currency(results['Выручка с ед.']))
            st.metric("Прибыль с ед.", format_currency(results['Прибыль с ед.']))
            st.metric("Маржинальность", format_percent(results['Маржинальность, %']))
            st.metric("Рентабельность", format_percent(results['Рентабельность, %']))
        
        with col3:
            st.markdown("### 📦 Расчеты с остатками")
            st.metric("Закуплено товара", format_number(selected_product.get('purchased_quantity', 0)))
            st.metric("Остаток товара", format_number(selected_product['stock_quantity']))
            st.metric("Продано товара", format_number(results['Продано товара']))
            st.metric("Выручка с остатков (без налога)", format_currency(results['Выручка с остатков без налога']))
            st.metric("Выручка с остатков (с налогом 7%)", format_currency(results['Выручка с остатков с налогом 7%']))
            st.metric("Себестоимость остатков", format_currency(results['Себестоимость остатков']))
            st.metric("Прибыль с остатков", format_currency(results['Прибыль с остатков']))
        
        with col4:
            st.markdown("### 💸 Затраты")
            st.metric("Комиссия (%)", format_percent(selected_product['commission_rate']))
            st.metric("Комиссия (₽)", format_currency(results['Комиссия, руб']))
            st.metric("Логистика", format_currency(selected_product['logistics_cost']))
            st.metric("Реклама (%)", format_percent(selected_product['advertising_percent']))
            st.metric("Реклама (₽)", format_currency(results['Реклама, руб']))
            st.metric("Налог с ед. (7%)", format_currency(results['Налог с ед., руб']))
            st.metric("Хранение", format_currency(selected_product['storage_cost']))
            st.metric("Себестоимость", format_currency(selected_product['cost_price']))
            st.metric("Доставка с учетом выкупа", format_currency(results['Доставка с учетом выкупа']))
            
        # Структура затрат
        st.markdown("---")
        st.subheader("📊 Структура затрат - доли в товаре")
        
        price_with_discount = results['Цена со скидкой']
        cost_structure = {
            'Себестоимость': selected_product['cost_price'],
            'Логистика': selected_product['logistics_cost'],
            'Прибыль': results['Прибыль с ед.'],
            'Реклама': results['Реклама, руб'],
            'Хранение': selected_product['storage_cost'],
            'Налог': results['Налог с ед., руб'],
            'Комиссия': results['Комиссия, руб']
        }
        
        cost_shares = {}
        for key, value in cost_structure.items():
            if price_with_discount > 0:
                cost_shares[key] = (value / price_with_discount) * 100
            else:
                cost_shares[key] = 0
        
        col1, col2 = st.columns(2)
        
        with col1:
            fig_pie = px.pie(
                values=list(cost_shares.values()),
                names=list(cost_shares.keys()),
                title=f"Доли в цене товара: {selected_product['product_name']}",
                labels={'value': 'Доля, %', 'name': 'Компонент'}
            )
            fig_pie.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig_pie, use_container_width=True)
        
        with col2:
            fig_bar = px.bar(
                x=list(cost_shares.keys()),
                y=list(cost_shares.values()),
                title="Доли компонентов в цене товара",
                labels={'x': 'Компонент', 'y': 'Доля, %'},
                text=[f"{value:.1f}%" for value in cost_shares.values()]
            )
            fig_bar.update_traces(textposition='outside')
            st.plotly_chart(fig_bar, use_container_width=True)
        
    # Экспорт данных
    st.markdown("---")
    st.subheader("💾 Экспорт данных")
    
    col1, col2 = st.columns(2)

    with col1:
        if st.button("📥 Экспорт таблицы в Excel", type="primary", key="export_excel_main"):
            # Создаем Excel файл с общей таблицей и детальными данными
            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                # Общая таблица
                df_table.to_excel(writer, sheet_name='Общая таблица', index=False)
                
                # Детальные данные
                detailed_data = []
                for product in filtered_products:
                    results = product['results']
                    detailed_data.append({
                        'Тип': product.get('product_type', 'Другое'),
                        'Товар': product['product_name'],
                        'Себестоимость': product['cost_price'],
                        'Розничная цена': product['retail_price'],
                        'Скидка, %': product['discount_percent'],
                        'Комиссия, %': product['commission_rate'],
                        'Логистика': product['logistics_cost'],
                        'Реклама, %': product['advertising_percent'],
                        '% выкупа': product['buyout_percent'],
                        'Хранение': product['storage_cost'],
                        'Закуплено': product.get('purchased_quantity', 0),
                        'Остаток': product['stock_quantity'],
                        'Продано': results['Продано товара'],
                        'СПП скидка, %': product['spp_discount'],
                        'Цена со скидкой': results['Цена со скидкой'],
                        'Комиссия, руб': results['Комиссия, руб'],
                        'Выручка с ед.': results['Выручка с ед.'],
                        'Прибыль с ед.': results['Прибыль с ед.'],
                        'Маржинальность, %': results['Маржинальность, %'],
                        'Рентабельность, %': results['Рентабельность, %'],
                        'Выручка с остатков (без налога)': results['Выручка с остатков без налога'],
                        'Выручка с остатков (с налогом)': results['Выручка с остатков с налогом 7%'],
                        'Себестоимость остатков': results['Себестоимость остатков'],
                        'Прибыль с остатков': results['Прибыль с остатков'],
                        'Дата создания': product.get('created_date', 'Неизвестно')
                    })
                
                pd.DataFrame(detailed_data).to_excel(writer, sheet_name='Детальные данные', index=False)
                
                # Формулы
                formulas_data = {
                    'Формула': [
                        'Цена со скидкой = Розничная цена × (1 - Скидка%)',
                        'Цена с учетом СПП = Цена со скидкой × (1 - СПП%)',
                        'Комиссия = Цена со скидкой × Комиссия%',
                        'Выручка с ед. = Цена со скидкой - Комиссия - Логистика с учетом выкупа - Реклама - Хранение',
                        'Реклама = Цена со скидкой × Реклама%',
                        'Налог с ед. = Цена со скидкой × 7%',
                        'Доставка с учетом выкупа = (Выкуп% × Логистика + (1-Выкуп%) × (Логистика+50)) × 100 / Выкуп%',
                        'Прибыль с ед. = Выручка с ед. - Себестоимость - Налог',
                        'Маржинальность = (Прибыль с ед. / Цена со скидкой) × 100%',
                        'Рентабельность = (Прибыль с ед. / Себестоимость) × 100%',
                        'Прибыль с выкупом = Прибыль с ед. × % выкупа',
                        'Выручка с остатков без налога = Выручка с ед. × Остаток',
                        'Выручка с остатков с налогом 7% = Выручка с остатков без налога × 0.93',
                        'Себестоимость остатков = Себестоимость × Остаток',
                        'Прибыль с остатков = Прибыль с ед. × Остаток',
                        'Продано товара = Закуплено товара - Остаток товара'
                    ]
                }
                pd.DataFrame(formulas_data).to_excel(writer, sheet_name='Формулы', index=False)
            
            output.seek(0)
            st.download_button(
                label="Скачать Excel файл",
                data=output.getvalue(),
                file_name=f"products_table_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

            with col2:
                if st.button("📊 Экспорт в CSV", key="export_csv_main"):
                    csv = df_table.to_csv(index=False, encoding='utf-8-sig')
                    st.download_button(
                        label="Скачать CSV файл",
                        data=csv,
                        file_name=f"products_table_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv"
                    )
    
    with tab2:
        # Тестовые товары
        # Загружаем сохраненные тестовые товары
        test_saved_products = load_test_products()
        
        # Сайдбар для управления тестовыми товарами
        with st.sidebar:
            st.header("🧪 Управление тестовыми товарами")
            
            # Форма создания нового тестового товара
            with st.expander("➕ Создать тестовый товар", expanded=False):
                st.subheader("📝 Создание тестового товара")
                
                test_new_product_name = st.text_input("Название тестового товара", key="test_new_product_name")
                test_new_product_type = st.text_input("Тип товара", value="Тест", key="test_new_product_type")
                test_new_cost_price = st.number_input("Себестоимость, ₽", min_value=0.0, value=500.0, step=10.0, key="test_new_cost_price")
                test_new_retail_price = st.number_input("Розничная цена (до скидки), ₽", min_value=0.0, value=800.0, step=10.0, key="test_new_retail_price")
                test_new_discount_percent = st.number_input("Скидка на сайте, %", min_value=0.0, max_value=100.0, value=15.0, step=1.0, key="test_new_discount_percent")
                test_new_commission_rate = st.number_input("Комиссия, %", min_value=0.0, max_value=100.0, value=5.0, step=0.1, key="test_new_commission_rate")
                test_new_logistics_cost = st.number_input("Логистика, ₽", min_value=0.0, value=80.0, step=10.0, key="test_new_logistics_cost")
                test_new_advertising_percent = st.number_input("Реклама, % от цены", min_value=0.0, max_value=100.0, value=3.0, step=0.1, key="test_new_advertising_percent")
                test_new_buyout_percent = st.number_input("% выкупа", min_value=0.0, max_value=100.0, value=85.0, step=1.0, key="test_new_buyout_percent")
                test_new_storage_cost = st.number_input("Хранение, ₽", min_value=0.0, value=20.0, step=5.0, key="test_new_storage_cost")
                test_new_purchased_quantity = st.number_input("Закуплено товара, шт", min_value=0, value=150, step=1, key="test_new_purchased_quantity")
                test_new_stock_quantity = st.number_input("Остаток товара, шт", min_value=0, value=50, step=1, key="test_new_stock_quantity")
                test_new_spp_discount = st.number_input("СПП скидка, %", min_value=0.0, max_value=100.0, value=20.0, step=1.0, key="test_new_spp_discount")
                
                if st.button("💾 Сохранить тестовый товар", type="primary", use_container_width=True, key="save_test_product_sidebar"):
                    if test_new_product_name:
                        # Создаем данные тестового товара
                        test_product_data = {
                            'product_name': test_new_product_name,
                            'product_type': test_new_product_type,
                            'cost_price': test_new_cost_price,
                            'retail_price': test_new_retail_price,
                            'discount_percent': test_new_discount_percent,
                            'commission_rate': test_new_commission_rate,
                            'logistics_cost': test_new_logistics_cost,
                            'advertising_percent': test_new_advertising_percent,
                            'buyout_percent': test_new_buyout_percent,
                            'storage_cost': test_new_storage_cost,
                            'purchased_quantity': test_new_purchased_quantity,
                            'stock_quantity': test_new_stock_quantity,
                            'spp_discount': test_new_spp_discount,
                            'timestamp': datetime.now().isoformat(),
                            'created_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        }
                        
                        # Сохраняем тестовый товар
                        filename = save_test_product(test_product_data)
                        if filename:
                            st.success(f"✅ Тестовый товар '{test_new_product_name}' успешно сохранен!")
                            st.rerun()
                    else:
                        st.error("❌ Введите название тестового товара!")
            
            # Форма редактирования тестовых товаров
            if test_saved_products:
                with st.expander("✏️ Редактировать тестовый товар", expanded=False):
                    st.subheader("📝 Редактирование тестового товара")
                    
                    # Выбор тестового товара для редактирования
                    test_edit_product_names = [p['product_name'] for p in test_saved_products]
                    test_selected_edit_product = st.selectbox(
                        "Выберите тестовый товар для редактирования:",
                        options=test_edit_product_names,
                        key="test_edit_product_select"
                    )
                    
                    if test_selected_edit_product:
                        # Находим выбранный тестовый товар
                        test_edit_product = None
                        for product in test_saved_products:
                            if product['product_name'] == test_selected_edit_product:
                                test_edit_product = product
                                break
                        
                        if test_edit_product:
                            test_edit_product_name = st.text_input("Название товара", value=test_edit_product['product_name'], key="test_edit_product_name")
                            test_edit_product_type = st.text_input("Тип товара", value=test_edit_product.get('product_type', 'Тест'), key="test_edit_product_type")
                            test_edit_cost_price = st.number_input("Себестоимость, ₽", min_value=0.0, value=float(test_edit_product['cost_price']), step=10.0, key="test_edit_cost_price")
                            test_edit_retail_price = st.number_input("Розничная цена (до скидки), ₽", min_value=0.0, value=float(test_edit_product['retail_price']), step=10.0, key="test_edit_retail_price")
                            test_edit_discount_percent = st.number_input("Скидка на сайте, %", min_value=0.0, max_value=100.0, value=float(test_edit_product['discount_percent']), step=1.0, key="test_edit_discount_percent")
                            test_edit_commission_rate = st.number_input("Комиссия, %", min_value=0.0, max_value=100.0, value=float(test_edit_product['commission_rate']), step=0.1, key="test_edit_commission_rate")
                            test_edit_logistics_cost = st.number_input("Логистика, ₽", min_value=0.0, value=float(test_edit_product['logistics_cost']), step=10.0, key="test_edit_logistics_cost")
                            test_edit_advertising_percent = st.number_input("Реклама, % от цены", min_value=0.0, max_value=100.0, value=float(test_edit_product['advertising_percent']), step=0.1, key="test_edit_advertising_percent")
                            test_edit_buyout_percent = st.number_input("% выкупа", min_value=0.0, max_value=100.0, value=float(test_edit_product['buyout_percent']), step=1.0, key="test_edit_buyout_percent")
                            test_edit_storage_cost = st.number_input("Хранение, ₽", min_value=0.0, value=float(test_edit_product['storage_cost']), step=10.0, key="test_edit_storage_cost")
                            test_edit_purchased_quantity = st.number_input("Закуплено товара, шт", min_value=0, value=int(test_edit_product.get('purchased_quantity', 150)), step=1, key="test_edit_purchased_quantity")
                            test_edit_stock_quantity = st.number_input("Остаток товара, шт", min_value=0, value=int(test_edit_product['stock_quantity']), step=1, key="test_edit_stock_quantity")
                            test_edit_spp_discount = st.number_input("СПП скидка, %", min_value=0.0, max_value=100.0, value=float(test_edit_product['spp_discount']), step=1.0, key="test_edit_spp_discount")
                            
                            if st.button("💾 Сохранить изменения", type="primary", use_container_width=True, key="update_test_product_sidebar"):
                                if test_edit_product_name:
                                    # Обновляем данные тестового товара
                                    test_edit_product.update({
                                        'product_name': test_edit_product_name,
                                        'product_type': test_edit_product_type,
                                        'cost_price': test_edit_cost_price,
                                        'retail_price': test_edit_retail_price,
                                        'discount_percent': test_edit_discount_percent,
                                        'commission_rate': test_edit_commission_rate,
                                        'logistics_cost': test_edit_logistics_cost,
                                        'advertising_percent': test_edit_advertising_percent,
                                        'buyout_percent': test_edit_buyout_percent,
                                        'storage_cost': test_edit_storage_cost,
                                        'purchased_quantity': test_edit_purchased_quantity,
                                        'stock_quantity': test_edit_stock_quantity,
                                        'spp_discount': test_edit_spp_discount,
                                        'updated_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                                    })
                                    
                                    # Сохраняем изменения
                                    if update_test_product(test_edit_product['filename'], test_edit_product):
                                        st.success(f"✅ Тестовый товар '{test_edit_product_name}' успешно обновлен!")
                                        st.rerun()
                                else:
                                    st.error("❌ Введите название тестового товара!")
            
            # Форма удаления тестовых товаров
            if test_saved_products:
                with st.expander("🗑️ Удалить тестовый товар", expanded=False):
                    st.subheader("🗑️ Удаление тестового товара")
                    
                    # Выбор тестового товара для удаления
                    test_delete_product_names = [p['product_name'] for p in test_saved_products]
                    test_selected_delete_product = st.selectbox(
                        "Выберите тестовый товар для удаления:",
                        options=test_delete_product_names,
                        key="test_delete_product_select"
                    )
                    
                    if test_selected_delete_product:
                        # Находим выбранный тестовый товар
                        test_delete_product_data = None
                        for product in test_saved_products:
                            if product['product_name'] == test_selected_delete_product:
                                test_delete_product_data = product
                                break
                        
                        if test_delete_product_data:
                            st.warning(f"⚠️ Вы собираетесь удалить тестовый товар: **{test_selected_delete_product}**")
                            st.info(f"Тип: {test_delete_product_data.get('product_type', 'Не указан')}")
                            
                            if st.button("🗑️ Удалить тестовый товар", type="secondary", use_container_width=True, key="delete_test_product_sidebar"):
                                if delete_test_product(test_delete_product_data['filename']):
                                    st.success(f"✅ Тестовый товар '{test_selected_delete_product}' успешно удален!")
                                    st.rerun()
                            if st.button("❌ Отмена", use_container_width=True, key="cancel_delete_test_sidebar"):
                                st.info("Удаление отменено")
            

        
        # Отображение сохраненных тестовых товаров
        if test_saved_products:
            
            # Рассчитываем показатели для всех тестовых товаров
            test_filtered_products = []
            for product in test_saved_products:
                # Рассчитываем показатели для каждого тестового товара
                results = calculate_unit_economics(
                    cost_price=product['cost_price'],
                    retail_price=product['retail_price'],
                    discount_percent=product['discount_percent'],
                    commission_rate=product['commission_rate'],
                    logistics_cost=product['logistics_cost'],
                    advertising_percent=product['advertising_percent'],
                    buyout_percent=product['buyout_percent'],
                    storage_cost=product['storage_cost'],
                    stock_quantity=product['stock_quantity'],
                    purchased_quantity=product.get('purchased_quantity', 0),
                    spp_discount=product['spp_discount']
                )
                
                # Добавляем результаты к товару
                product['results'] = results
                test_filtered_products.append(product)
            
            # Создаем таблицу тестовых товаров
            st.markdown("---")
            st.subheader(f"📋 Таблица тестовых товаров ({len(test_filtered_products)} шт)")
            
            test_table_data = []
            
            # Группируем тестовые товары по типам
            test_products_by_type = {}
            for product in test_filtered_products:
                product_type = product.get('product_type', 'Тест')
                if product_type not in test_products_by_type:
                    test_products_by_type[product_type] = []
                test_products_by_type[product_type].append(product)
            
            # Сортируем типы товаров
            sorted_test_types = sorted(test_products_by_type.keys())
            
            # Добавляем данные в таблицу с промежуточными итогами
            for product_type in sorted_test_types:
                products = test_products_by_type[product_type]
                
                # Добавляем товары данного типа
                for product in products:
                    results = product['results']
                    test_table_data.append({
                        'Тип': product_type,
                        'Товар': product['product_name'],
                        'Себестоимость': format_currency(product['cost_price']),
                        'Розничная цена': format_currency(product['retail_price']),
                        'Скидка': format_percent(product['discount_percent']),
                        'Цена со скидкой': format_currency(results['Цена со скидкой']),
                        'Цена с СПП': format_currency(results['Цена с учетом СПП']),
                        'Комиссия': format_percent(product['commission_rate']),
                        'Логистика': format_currency(product['logistics_cost']),
                        'Реклама': format_percent(product['advertising_percent']),
                        '% выкупа': format_percent(product['buyout_percent']),
                        'Закуплено': format_number(product.get('purchased_quantity', 0)),
                        'Остаток': format_number(product['stock_quantity']),
                        'Продано': format_number(results['Продано товара']),
                        'Выручка с ед.': format_currency(results['Выручка с ед.']),
                        'Прибыль с ед.': format_currency(results['Прибыль с ед.']),
                        'Маржинальность': format_percent(results['Маржинальность, %']),
                        'Рентабельность': format_percent(results['Рентабельность, %']),
                        'Выручка с остатков (без налога)': format_currency(results['Выручка с остатков без налога']),
                        'Выручка с остатков (с налогом)': format_currency(results['Выручка с остатков с налогом 7%']),
                        'Себестоимость остатков': format_currency(results['Себестоимость остатков']),
                        'Прибыль с остатков': format_currency(results['Прибыль с остатков']),
                        'Дата создания': product.get('created_date', 'Неизвестно')
                    })
                
                # Добавляем промежуточный итог по типу
                if len(products) > 1:
                    test_type_total_row = {
                        'Тип': f"ИТОГО по {product_type}",
                        'Товар': f"({len(products)} товаров)",
                        'Себестоимость': '-',
                        'Розничная цена': '-',
                        'Скидка': '-',
                        'Цена со скидкой': '-',
                        'Цена с СПП': '-',
                        'Комиссия': '-',
                        'Логистика': '-',
                        'Реклама': '-',
                        '% выкупа': '-',
                        'Закуплено': format_number(sum(p.get('purchased_quantity', 0) for p in products)),
                        'Остаток': format_number(sum(p['stock_quantity'] for p in products)),
                        'Продано': format_number(sum(p['results']['Продано товара'] for p in products)),
                        'Выручка с ед.': '-',
                        'Прибыль с ед.': '-',
                        'Маржинальность': format_percent(sum(p['results']['Маржинальность, %'] for p in products) / len(products)),
                        'Рентабельность': format_percent(sum(p['results']['Рентабельность, %'] for p in products) / len(products)),
                        'Выручка с остатков (без налога)': format_currency(sum(p['results']['Выручка с остатков без налога'] for p in products)),
                        'Выручка с остатков (с налогом)': format_currency(sum(p['results']['Выручка с остатков с налогом 7%'] for p in products)),
                        'Себестоимость остатков': format_currency(sum(p['results']['Себестоимость остатков'] for p in products)),
                        'Прибыль с остатков': format_currency(sum(p['results']['Прибыль с остатков'] for p in products)),
                        'Дата создания': '-'
                    }
                    test_table_data.append(test_type_total_row)
            
            # Создаем DataFrame для тестовых товаров
            test_df_table = pd.DataFrame(test_table_data)
            
            # Функция для стилизации строк тестовых товаров
            def highlight_test_rows(row):
                """Выделяет цветом промежуточные итоги и общий итог для тестовых товаров"""
                if 'ИТОГО по' in str(row['Тип']):
                    return ['background-color: #e6f3ff'] * len(row)  # Голубой для промежуточных итогов
                elif row['Тип'] == 'ИТОГО':
                    return ['background-color: #ffe6e6'] * len(row)  # Красный для общего итога
                else:
                    return [''] * len(row)
            
            # Добавляем строку итого для тестовых товаров
            if len(test_table_data) > 0:
                # Создаем данные для строки итого
                test_total_row = {
                    'Тип': 'ИТОГО',
                    'Товар': f"({len(test_filtered_products)} товаров)",
                    'Себестоимость': '-',
                    'Розничная цена': '-',
                    'Скидка': '-',
                    'Цена со скидкой': '-',
                    'Цена с СПП': '-',
                    'Комиссия': '-',
                    'Логистика': '-',
                    'Реклама': '-',
                    '% выкупа': '-',
                    'Закуплено': format_number(sum(product.get('purchased_quantity', 0) for product in test_filtered_products)),
                    'Остаток': format_number(sum(product['stock_quantity'] for product in test_filtered_products)),
                    'Продано': format_number(sum(product['results']['Продано товара'] for product in test_filtered_products)),
                    'Выручка с ед.': '-',
                    'Прибыль с ед.': '-',
                    'Маржинальность': format_percent(sum(product['results']['Маржинальность, %'] for product in test_filtered_products) / len(test_filtered_products)),
                    'Рентабельность': format_percent(sum(product['results']['Рентабельность, %'] for product in test_filtered_products) / len(test_filtered_products)),
                    'Выручка с остатков (без налога)': format_currency(sum(product['results']['Выручка с остатков без налога'] for product in test_filtered_products)),
                    'Выручка с остатков (с налогом)': format_currency(sum(product['results']['Выручка с остатков с налогом 7%'] for product in test_filtered_products)),
                    'Себестоимость остатков': format_currency(sum(product['results']['Себестоимость остатков'] for product in test_filtered_products)),
                    'Прибыль с остатков': format_currency(sum(product['results']['Прибыль с остатков'] for product in test_filtered_products)),
                    'Дата создания': '-'
                }
                
                # Добавляем строку итого в DataFrame
                test_df_table = pd.concat([test_df_table, pd.DataFrame([test_total_row])], ignore_index=True)
            
            # Применяем стили к таблице тестовых товаров
            styled_test_df = test_df_table.style.apply(highlight_test_rows, axis=1)
            
            # Отображаем таблицу тестовых товаров
            st.dataframe(
                styled_test_df,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Тип": st.column_config.TextColumn("Тип", width="medium"),
                    "Товар": st.column_config.TextColumn("Товар", width="medium"),
                    "Себестоимость": st.column_config.TextColumn("Себестоимость", width="medium"),
                    "Розничная цена": st.column_config.TextColumn("Розничная цена", width="medium"),
                    "Скидка": st.column_config.TextColumn("Скидка", width="medium"),
                    "Цена со скидкой": st.column_config.TextColumn("Цена со скидкой", width="medium"),
                    "Цена с СПП": st.column_config.TextColumn("Цена с СПП", width="medium"),
                    "Комиссия": st.column_config.TextColumn("Комиссия", width="medium"),
                    "Логистика": st.column_config.TextColumn("Логистика", width="medium"),
                    "Реклама": st.column_config.TextColumn("Реклама", width="medium"),
                    "% выкупа": st.column_config.TextColumn("% выкупа", width="medium"),
                    "Закуплено": st.column_config.TextColumn("Закуплено", width="medium"),
                    "Остаток": st.column_config.TextColumn("Остаток", width="medium"),
                    "Продано": st.column_config.TextColumn("Продано", width="medium"),
                    "Выручка с ед.": st.column_config.TextColumn("Выручка с ед.", width="medium"),
                    "Прибыль с ед.": st.column_config.TextColumn("Прибыль с ед.", width="medium"),
                    "Маржинальность": st.column_config.TextColumn("Маржинальность", width="medium"),
                    "Рентабельность": st.column_config.TextColumn("Рентабельность", width="medium"),
                    "Выручка с остатков (без налога)": st.column_config.TextColumn("Выручка с остатков (без налога)", width="medium"),
                    "Выручка с остатков (с налогом)": st.column_config.TextColumn("Выручка с остатков (с налогом)", width="medium"),
                    "Себестоимость остатков": st.column_config.TextColumn("Себестоимость остатков", width="medium"),
                    "Прибыль с остатков": st.column_config.TextColumn("Прибыль с остатков", width="medium"),
                    "Дата создания": st.column_config.TextColumn("Дата создания", width="medium")
                }
            )
            
            # Общий расчет по всем тестовым товарам
            st.markdown("---")
            st.subheader("📊 Общий расчет по всем тестовым товарам")
            
            # Рассчитываем общие показатели для тестовых товаров
            test_total_purchased = sum(product.get('purchased_quantity', 0) for product in test_saved_products)
            test_total_stock = sum(product['stock_quantity'] for product in test_saved_products)
            test_total_sold = test_total_purchased - test_total_stock
            
            test_total_revenue_no_tax = sum(product['results']['Выручка с остатков без налога'] for product in test_filtered_products)
            test_total_revenue_with_tax = sum(product['results']['Выручка с остатков с налогом 7%'] for product in test_filtered_products)
            test_total_stock_cost = sum(product['results']['Себестоимость остатков'] for product in test_filtered_products)
            test_total_profit_from_stock = sum(product['results']['Прибыль с остатков'] for product in test_filtered_products)
            
            # Средние показатели для тестовых товаров
            test_avg_margin = sum(product['results']['Маржинальность, %'] for product in test_filtered_products) / len(test_filtered_products) if test_filtered_products else 0
            test_avg_profitability = sum(product['results']['Рентабельность, %'] for product in test_filtered_products) / len(test_filtered_products) if test_filtered_products else 0
            test_avg_profit_per_unit = sum(product['results']['Прибыль с ед.'] for product in test_filtered_products) / len(test_filtered_products) if test_filtered_products else 0
            test_avg_revenue_per_unit = sum(product['results']['Выручка с ед.'] for product in test_filtered_products) / len(test_filtered_products) if test_filtered_products else 0
            
            # Общий расчет тестовых товаров в 4 колонках
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.markdown("### 📦 Общие показатели тестовых товаров")
                st.metric("Всего тестовых товаров", len(test_filtered_products))
                st.metric("Закуплено товаров", format_number(test_total_purchased))
                st.metric("Остаток товаров", format_number(test_total_stock))
                st.metric("Продано товаров", format_number(test_total_sold))
            
            with col2:
                st.markdown("### 💰 Общая выручка тестовых товаров")
                st.metric("Выручка (без налога)", format_currency(test_total_revenue_no_tax))
                st.metric("Выручка (с налогом 7%)", format_currency(test_total_revenue_with_tax))
                st.metric("Себестоимость остатков", format_currency(test_total_stock_cost))
                st.metric("Прибыль с остатков", format_currency(test_total_profit_from_stock))
            
            with col3:
                st.markdown("### 📊 Средние показатели тестовых товаров")
                st.metric("Средняя маржинальность", format_percent(test_avg_margin))
                st.metric("Средняя рентабельность", format_percent(test_avg_profitability))
                st.metric("Средняя прибыль с ед.", format_currency(test_avg_profit_per_unit))
                st.metric("Средняя выручка с ед.", format_currency(test_avg_revenue_per_unit))
            
            with col4:
                st.markdown("### 🎯 Ключевые метрики тестовых товаров")
                if test_total_purchased > 0:
                    test_sell_through_rate = (test_total_sold / test_total_purchased) * 100
                    st.metric("Процент продаж", format_percent(test_sell_through_rate))
                else:
                    st.metric("Процент продаж", "0%")
                
                if test_total_revenue_no_tax > 0:
                    test_profit_margin = (test_total_profit_from_stock / test_total_revenue_no_tax) * 100
                    st.metric("Общая рентабельность", format_percent(test_profit_margin))
                else:
                    st.metric("Общая рентабельность", "0%")
                
                if test_total_stock_cost > 0:
                    test_roi = (test_total_profit_from_stock / test_total_stock_cost) * 100
                    st.metric("ROI остатков", format_percent(test_roi))
                else:
                    st.metric("ROI остатков", "0%")
                
                if len(test_filtered_products) > 0:
                    test_avg_price = sum(product['retail_price'] for product in test_filtered_products) / len(test_filtered_products)
                    st.metric("Средняя цена", format_currency(test_avg_price))
                else:
                    st.metric("Средняя цена", "0 ₽")
            
            # Детальный расчет для тестовых товаров
            st.markdown("---")
            st.subheader("🔍 Детальный расчет по тестовым товарам")
            
            # Выбор тестового товара для детального просмотра
            test_selected_for_detail = st.selectbox(
                "Выберите тестовый товар для детального просмотра:",
                options=[p['product_name'] for p in test_filtered_products],
                key="test_detail_select",
                help="Выберите тестовый товар, чтобы увидеть полный детальный расчет"
            )
            
            # Находим выбранный тестовый товар
            test_selected_product = None
            for product in test_filtered_products:
                if product['product_name'] == test_selected_for_detail:
                    test_selected_product = product
                    break
            
            if test_selected_product:
                test_results_detail = test_selected_product['results']
                
                # Детальный расчет тестового товара
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.markdown(f"### 💰 Цены - {test_selected_product['product_name']}")
                    st.metric("Розничная цена", format_currency(test_selected_product['retail_price']))
                    st.metric("Скидка", format_percent(test_selected_product['discount_percent']))
                    st.metric("Цена со скидкой", format_currency(test_results_detail['Цена со скидкой']))
                    st.metric("СПП скидка", format_percent(test_selected_product['spp_discount']))
                    st.metric("Цена с учетом СПП", format_currency(test_results_detail['Цена с учетом СПП']))
                
                with col2:
                    st.markdown("### 📊 Результаты")
                    st.metric("Выручка с ед.", format_currency(test_results_detail['Выручка с ед.']))
                    st.metric("Прибыль с ед.", format_currency(test_results_detail['Прибыль с ед.']))
                    st.metric("Маржинальность", format_percent(test_results_detail['Маржинальность, %']))
                    st.metric("Рентабельность", format_percent(test_results_detail['Рентабельность, %']))
                
                with col3:
                    st.markdown("### 📦 Расчеты с остатками")
                    st.metric("Закуплено товара", format_number(test_selected_product.get('purchased_quantity', 0)))
                    st.metric("Остаток товара", format_number(test_selected_product['stock_quantity']))
                    st.metric("Продано товара", format_number(test_results_detail['Продано товара']))
                    st.metric("Выручка с остатков (без налога)", format_currency(test_results_detail['Выручка с остатков без налога']))
                    st.metric("Выручка с остатков (с налогом 7%)", format_currency(test_results_detail['Выручка с остатков с налогом 7%']))
                    st.metric("Себестоимость остатков", format_currency(test_results_detail['Себестоимость остатков']))
                    st.metric("Прибыль с остатков", format_currency(test_results_detail['Прибыль с остатков']))
                
                with col4:
                    st.markdown("### 💸 Затраты")
                    st.metric("Комиссия (%)", format_percent(test_selected_product['commission_rate']))
                    st.metric("Комиссия (₽)", format_currency(test_results_detail['Комиссия, руб']))
                    st.metric("Логистика", format_currency(test_selected_product['logistics_cost']))
                    st.metric("Реклама (%)", format_percent(test_selected_product['advertising_percent']))
                    st.metric("Реклама (₽)", format_currency(test_results_detail['Реклама, руб']))
                    st.metric("Налог с ед. (7%)", format_currency(test_results_detail['Налог с ед., руб']))
                    st.metric("Хранение", format_currency(test_selected_product['storage_cost']))
                    st.metric("Себестоимость", format_currency(test_selected_product['cost_price']))
                    st.metric("Доставка с учетом выкупа", format_currency(test_results_detail['Доставка с учетом выкупа']))
        else:
            st.info("📝 Сохраненных тестовых товаров нет.")
    
    with tab3:
        # Себестоимость товаров
        
        
        # Загружаем сохраненные расчеты себестоимости
        cost_products = load_cost_products()
        
        # Сайдбар для управления расчетами себестоимости
        with st.sidebar:
            st.header("💰 Управление расчетами себестоимости")
            
            # Форма создания нового расчета себестоимости
            with st.expander("➕ Создать расчет себестоимости", expanded=False):
                st.subheader("📝 Создание расчета себестоимости")
                
                # Выбор существующего товара (основные + тестовые)
                all_products = []
                
                # Добавляем основные товары
                if saved_products:
                    for product in saved_products:
                        all_products.append({
                            'name': product['product_name'],
                            'type': 'Основной товар'
                        })
                
                # Добавляем тестовые товары
                test_products = load_test_products()
                if test_products:
                    for product in test_products:
                        all_products.append({
                            'name': product['product_name'],
                            'type': 'Тестовый товар'
                        })
                
                if all_products:
                    # Создаем список для отображения с указанием типа
                    display_options = [f"{p['name']} ({p['type']})" for p in all_products]
                    product_names = [p['name'] for p in all_products]
                    
                    cost_selected_product_display = st.selectbox(
                        "Выберите товар для расчета себестоимости:",
                        options=display_options,
                        key="cost_product_select"
                    )
                    
                    # Получаем выбранное имя товара
                    if cost_selected_product_display:
                        cost_selected_product = cost_selected_product_display.split(" (")[0]
                    else:
                        cost_selected_product = None
                else:
                    st.warning("Нет сохраненных товаров для расчета себестоимости")
                    cost_selected_product = None
                
                # Поля ввода на отдельных строках
                cost_price_yuan = st.number_input("Стоимость товара в юанях", min_value=0.0, value=100.0, step=1.0, key="cost_price_yuan")

                cost_delivery_russia_usd = st.number_input("Стоимость доставки в России (USD)", min_value=0.0, value=10.0, step=0.5, key="cost_delivery_russia_usd")
                cost_weight = st.number_input("Вес (г)", min_value=0.0, value=1000.0, step=10.0, key="cost_weight")
                cost_quantity = st.number_input("Количество", min_value=1, value=100, step=1, key="cost_quantity")

                cost_ff = st.number_input("ФФ (руб)", min_value=0.0, value=50.0, step=5.0, key="cost_ff")
                cost_development = st.number_input("Разработка (RUB)", min_value=0.0, value=0.0, step=10.0, key="cost_development")
                cost_other_expenses = st.number_input("Прочие расходы (RUB)", min_value=0.0, value=0.0, step=10.0, key="cost_other_expenses")
                cost_yuan_rate = st.number_input("Курс юаня", min_value=0.0, value=12.5, step=0.1, key="cost_yuan_rate")
                cost_usd_rate = st.number_input("Курс доллара", min_value=0.0, value=95.0, step=0.5, key="cost_usd_rate")
                
                # Автоматический расчет логистики из Китая (после определения всех переменных)
                auto_logistics_china = (cost_weight / 1000) * cost_delivery_russia_usd * cost_usd_rate * cost_quantity
                cost_logistics_china = st.number_input(
                    "Стоимость логистики из Китая (автоматически рассчитано)", 
                    min_value=0.0, 
                    value=float(auto_logistics_china), 
                    step=10.0, 
                    key="cost_logistics_china",
                    help="Автоматически рассчитывается как: (вес в г / 1000) × стоимость доставки USD × курс доллара × количество"
                )
                

                
                if st.button("💾 Сохранить расчет себестоимости", type="primary", use_container_width=True, key="save_cost_product_sidebar"):
                    if cost_selected_product:
                        # Рассчитываем себестоимость
                        cost_results = calculate_cost_price(
                            price_yuan=cost_price_yuan,
                            delivery_russia_usd=cost_delivery_russia_usd,
                            logistics_china=cost_logistics_china,
                            weight=cost_weight,
                            quantity=cost_quantity,
                            ff=cost_ff,
                            development=cost_development,
                            other_expenses=cost_other_expenses,
                            yuan_rate=cost_yuan_rate,
                            usd_rate=cost_usd_rate
                        )
                        
                        # Создаем данные расчета себестоимости
                        cost_product_data = {
                            'product_name': cost_selected_product,
                            'price_yuan': cost_price_yuan,
                            'delivery_russia_usd': cost_delivery_russia_usd,
                            'logistics_china': cost_logistics_china,
                            'weight': cost_weight,
                            'quantity': cost_quantity,
                            'ff': cost_ff,
                            'development': cost_development,
                            'other_expenses': cost_other_expenses,
                            'yuan_rate': cost_yuan_rate,
                            'usd_rate': cost_usd_rate,
                            'results': cost_results,
                            'timestamp': datetime.now().isoformat(),
                            'created_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        }
                        
                        # Сохраняем расчет себестоимости
                        filename = save_cost_product(cost_product_data)
                        if filename:
                            # Обновляем себестоимость в основных и тестовых товарах
                            updated_count = update_products_cost_price(cost_selected_product, cost_results['cost_per_unit'])
                            if updated_count > 0:
                                st.success(f"✅ Расчет себестоимости для товара '{cost_selected_product}' успешно сохранен! Обновлена себестоимость в {updated_count} товарах.")
                            else:
                                st.success(f"✅ Расчет себестоимости для товара '{cost_selected_product}' успешно сохранен!")
                            st.rerun()
                    else:
                        st.error("❌ Выберите товар для расчета себестоимости!")
            
            # Форма редактирования расчетов себестоимости
            if cost_products:
                with st.expander("✏️ Редактировать расчет себестоимости", expanded=False):
                    st.subheader("📝 Редактирование расчета себестоимости")
                    
                    # Выбор расчета себестоимости для редактирования
                    cost_edit_product_names = [p['product_name'] for p in cost_products]
                    cost_selected_edit_product = st.selectbox(
                        "Выберите расчет себестоимости для редактирования:",
                        options=cost_edit_product_names,
                        key="cost_edit_product_select"
                    )
                    
                    if cost_selected_edit_product:
                        # Находим выбранный расчет себестоимости
                        cost_edit_product = None
                        for product in cost_products:
                            if product['product_name'] == cost_selected_edit_product:
                                cost_edit_product = product
                                break
                        
                        if cost_edit_product:
                            cost_edit_product_name = st.text_input("Название товара", value=cost_edit_product['product_name'], key="cost_edit_product_name")
                            
                            # Поля редактирования на отдельных строках
                            cost_edit_price_yuan = st.number_input("Стоимость товара в юанях", min_value=0.0, value=float(cost_edit_product['price_yuan']), step=1.0, key="cost_edit_price_yuan")

                            cost_edit_delivery_russia_usd = st.number_input("Стоимость доставки в России (USD)", min_value=0.0, value=float(cost_edit_product['delivery_russia_usd']), step=0.5, key="cost_edit_delivery_russia_usd")
                            cost_edit_weight = st.number_input("Вес (г)", min_value=0.0, value=float(cost_edit_product['weight']), step=10.0, key="cost_edit_weight")
                            cost_edit_quantity = st.number_input("Количество", min_value=1, value=int(cost_edit_product['quantity']), step=1, key="cost_edit_quantity")

                            cost_edit_ff = st.number_input("ФФ (руб)", min_value=0.0, value=float(cost_edit_product['ff']), step=5.0, key="cost_edit_ff")
                            cost_edit_development = st.number_input("Разработка (RUB)", min_value=0.0, value=float(cost_edit_product.get('development', 0.0)), step=10.0, key="cost_edit_development")
                            cost_edit_other_expenses = st.number_input("Прочие расходы (RUB)", min_value=0.0, value=float(cost_edit_product.get('other_expenses', 0.0)), step=10.0, key="cost_edit_other_expenses")
                            cost_edit_yuan_rate = st.number_input("Курс юаня", min_value=0.0, value=float(cost_edit_product['yuan_rate']), step=0.1, key="cost_edit_yuan_rate")
                            cost_edit_usd_rate = st.number_input("Курс доллара", min_value=0.0, value=float(cost_edit_product['usd_rate']), step=0.5, key="cost_edit_usd_rate")
                            
                            # Автоматический расчет логистики из Китая для редактирования (после определения всех переменных)
                            auto_edit_logistics_china = cost_edit_weight * cost_edit_delivery_russia_usd * cost_edit_usd_rate * cost_edit_quantity
                            cost_edit_logistics_china = st.number_input(
                                "Стоимость логистики из Китая (автоматически рассчитано)", 
                                min_value=0.0, 
                                value=float(auto_edit_logistics_china), 
                                step=10.0, 
                                key="cost_edit_logistics_china",
                                help="Автоматически рассчитывается как: (вес в г / 1000) × стоимость доставки USD × курс доллара × количество"
                            )
                            

                            
                            if st.button("💾 Сохранить изменения", type="primary", use_container_width=True, key="update_cost_product_sidebar"):
                                if cost_edit_product_name:
                                    # Рассчитываем обновленную себестоимость
                                    cost_edit_results = calculate_cost_price(
                                        price_yuan=cost_edit_price_yuan,
                                        delivery_russia_usd=cost_edit_delivery_russia_usd,
                                        logistics_china=cost_edit_logistics_china,
                                        weight=cost_edit_weight,
                                        quantity=cost_edit_quantity,
                                        ff=cost_edit_ff,
                                        development=cost_edit_development,
                                        other_expenses=cost_edit_other_expenses,
                                        yuan_rate=cost_edit_yuan_rate,
                                        usd_rate=cost_edit_usd_rate
                                    )
                                    
                                    # Обновляем данные расчета себестоимости
                                    cost_edit_product.update({
                                        'product_name': cost_edit_product_name,
                                        'price_yuan': cost_edit_price_yuan,
                                        'delivery_russia_usd': cost_edit_delivery_russia_usd,
                                        'logistics_china': cost_edit_logistics_china,
                                        'weight': cost_edit_weight,
                                        'quantity': cost_edit_quantity,
                                        'ff': cost_edit_ff,
                                        'development': cost_edit_development,
                                        'other_expenses': cost_edit_other_expenses,
                                        'yuan_rate': cost_edit_yuan_rate,
                                        'usd_rate': cost_edit_usd_rate,
                                        'results': cost_edit_results,
                                        'timestamp': datetime.now().isoformat(),
                                        'created_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                                    })
                                    
                                    # Сохраняем обновленный расчет себестоимости
                                    if update_cost_product(cost_edit_product['filename'], cost_edit_product):
                                        # Обновляем себестоимость в основных и тестовых товарах
                                        updated_count = update_products_cost_price(cost_edit_product_name, cost_edit_results['cost_per_unit'])
                                        if updated_count > 0:
                                            st.success(f"✅ Расчет себестоимости '{cost_edit_product_name}' успешно обновлен! Обновлена себестоимость в {updated_count} товарах.")
                                        else:
                                            st.success(f"✅ Расчет себестоимости '{cost_edit_product_name}' успешно обновлен!")
                                        st.rerun()
                                else:
                                    st.error("❌ Введите название товара!")
            
            # Удаление расчетов себестоимости
            if cost_products:
                with st.expander("🗑️ Удалить расчет себестоимости", expanded=False):
                    st.subheader("🗑️ Удаление расчета себестоимости")
                    
                    # Выбор расчета себестоимости для удаления
                    cost_delete_product_names = [p['product_name'] for p in cost_products]
                    cost_selected_delete_product = st.selectbox(
                        "Выберите расчет себестоимости для удаления:",
                        options=cost_delete_product_names,
                        key="cost_delete_product_select"
                    )
                    
                    if cost_selected_delete_product:
                        if st.button("🗑️ Удалить расчет себестоимости", type="secondary", use_container_width=True, key="delete_cost_product_sidebar"):
                            # Находим выбранный расчет себестоимости
                            cost_delete_product = None
                            for product in cost_products:
                                if product['product_name'] == cost_selected_delete_product:
                                    cost_delete_product = product
                                    break
                            
                            if cost_delete_product:
                                if delete_cost_product(cost_delete_product['filename']):
                                    st.success(f"✅ Расчет себестоимости '{cost_selected_delete_product}' успешно удален!")
                                    st.rerun()
        
        # Основной контент вкладки себестоимости
        
        # Убрали раздел "📊 Расчет себестоимости"
        
        if not cost_products:
            st.info("📝 Сохраненных расчетов себестоимости нет.")
        else:
            # Показываем все расчеты себестоимости
            st.subheader(f"📋 Таблица расчетов себестоимости ({len(cost_products)} расчетов)")
            
            # Создаем таблицу с расчетами себестоимости
            cost_table_data = []
            total_cost_sum = 0
            total_quantity_sum = 0
            
            for product in cost_products:
                results = product['results']
                total_cost_sum += results['total_cost']
                total_quantity_sum += product['quantity']
                
                # Обработка старых данных, которые могут не содержать новые поля логистики
                logistics_per_unit = results.get('logistics_china_per_unit', 0)
                logistics_total = results.get('logistics_china_total', 0)
                
                # Если поля не найдены, рассчитываем их из старых данных
                if logistics_per_unit == 0 and logistics_total == 0:
                    if 'logistics_china_calculated' in results:
                        # Старый формат данных
                        logistics_total = results['logistics_china_calculated']
                        logistics_per_unit = logistics_total / product['quantity'] if product['quantity'] > 0 else 0
                    else:
                        # Если нет данных о логистике, рассчитываем заново
                        logistics_per_unit = product['weight'] * product['delivery_russia_usd'] * product['usd_rate']
                        logistics_total = logistics_per_unit * product['quantity']
                
                cost_table_data.append({
                    'Товар': product['product_name'],
                    'Стоимость в юанях': format_currency(product['price_yuan']),
                    'Стоимость за ед. в Китае (RUB)': format_currency(results.get('price_rub_china_per_unit', results['price_rub_china'] / product['quantity'] if product['quantity'] > 0 else 0)),
                    'Стоимость в Китае общая (RUB)': format_currency(results['price_rub_china']),
                    'Доставка в России (USD)': format_usd(product['delivery_russia_usd']),
                    'Логистика из Китая на ед.': format_currency(logistics_per_unit),
                    'Логистика из Китая общая': format_currency(logistics_total),
                    'Вес (г)': format_number(product['weight']),
                    'Количество': format_number(product['quantity']),
                    'ФФ общий': format_currency(product['ff']),
                    'ФФ на ед.': format_currency(results.get('ff_per_unit', product['ff'] / product['quantity'] if product['quantity'] > 0 else 0)),
                    'Разработка': format_currency(product.get('development', 0)),
                    'Прочие расходы': format_currency(product.get('other_expenses', 0)),
                    'Курс юаня': format_number(product['yuan_rate']),
                    'Курс доллара': format_number(product['usd_rate']),
                    'Себестоимость на ед.': format_currency(results['cost_per_unit']),
                    'Общая себестоимость': format_currency(results['total_cost']),
                    'Дата создания': product.get('created_date', 'Неизвестно')
                })
            
            # Добавляем итоговую строку
            if cost_table_data:
                cost_table_data.append({
                    'Товар': '**ИТОГО**',
                    'Стоимость в юанях': '',
                    'Стоимость за ед. в Китае (RUB)': '',
                    'Стоимость в Китае общая (RUB)': '',
                    'Доставка в России (USD)': '',
                    'Логистика из Китая на ед.': '',
                    'Логистика из Китая общая': '',
                    'Вес (г)': '',
                    'Количество': format_number(total_quantity_sum),
                    'ФФ общий': '',
                    'ФФ на ед.': '',
                    'Разработка': '',
                    'Прочие расходы': '',
                    'Курс юаня': '',
                    'Курс доллара': '',
                    'Себестоимость на ед.': '',
                    'Общая себестоимость': format_currency(total_cost_sum),
                    'Дата создания': ''
                })
            
            if cost_table_data:
                df_cost_table = pd.DataFrame(cost_table_data)
                
                # Функция для выделения итоговой строки
                def highlight_total_rows(df):
                    # Создаем копию DataFrame для стилизации
                    styled_df = df.copy()
                    
                    # Находим строки с итогами
                    total_mask = df['Товар'].str.contains('ИТОГО', na=False)
                    
                    # Применяем стили
                    styled_df = styled_df.style.apply(
                        lambda x: ['background-color: #ffcccc' if total_mask.iloc[i] else '' for i in range(len(x))],
                        axis=0
                    )
                    
                    return styled_df
                
                # Применяем стилизацию
                styled_df = highlight_total_rows(df_cost_table)
                
                st.dataframe(
                    styled_df,
                    use_container_width=True,
                    column_config={
                        "Товар": st.column_config.TextColumn("Товар", width="medium"),
                        "Стоимость в юанях": st.column_config.TextColumn("Стоимость в юанях", width="medium"),
                        "Стоимость за ед. в Китае (RUB)": st.column_config.TextColumn("Стоимость за ед. в Китае (RUB)", width="medium"),
                        "Стоимость в Китае общая (RUB)": st.column_config.TextColumn("Стоимость в Китае общая (RUB)", width="medium"),
                        "Доставка в России (USD)": st.column_config.TextColumn("Доставка в России (USD)", width="medium"),
                        "Логистика из Китая на ед.": st.column_config.TextColumn("Логистика из Китая на ед.", width="medium"),
                        "Логистика из Китая общая": st.column_config.TextColumn("Логистика из Китая общая", width="medium"),
                        "Вес (г)": st.column_config.TextColumn("Вес (г)", width="small"),
                        "Количество": st.column_config.TextColumn("Количество", width="small"),
                        "ФФ общий": st.column_config.TextColumn("ФФ общий", width="medium"),
                        "ФФ на ед.": st.column_config.TextColumn("ФФ на ед.", width="medium"),
                        "Разработка": st.column_config.TextColumn("Разработка", width="medium"),
                        "Прочие расходы": st.column_config.TextColumn("Прочие расходы", width="medium"),
                        "Курс юаня": st.column_config.TextColumn("Курс юаня", width="small"),
                        "Курс доллара": st.column_config.TextColumn("Курс доллара", width="small"),
                        "Себестоимость на ед.": st.column_config.TextColumn("Себестоимость на ед.", width="medium"),
                        "Общая себестоимость": st.column_config.TextColumn("Общая себестоимость", width="medium"),
                        "Дата создания": st.column_config.TextColumn("Дата создания", width="medium")
                    }
                )
            
            # KPI по выбранному товару
            st.markdown("---")
            st.subheader("📊 KPI по выбранному товару")
            
            # Выбор товара для KPI
            if cost_products:
                cost_kpi_product_names = [p['product_name'] for p in cost_products]
                cost_kpi_selected_product = st.selectbox(
                    "Выберите товар для отображения KPI:",
                    options=cost_kpi_product_names,
                    key="cost_kpi_product_select"
                )
                
                if cost_kpi_selected_product:
                    # Находим выбранный товар
                    cost_kpi_product = None
                    for product in cost_products:
                        if product['product_name'] == cost_kpi_selected_product:
                            cost_kpi_product = product
                            break
                    
                    if cost_kpi_product:
                        results = cost_kpi_product['results']
                        
                        # Отображаем KPI для выбранного товара
                        col1, col2, col3, col4 = st.columns(4)
                        
                        with col1:
                            st.markdown(f"### 💰 Стоимость - {cost_kpi_product['product_name']}")
                            st.metric("Количество товара", format_number(cost_kpi_product['quantity']))
                            st.metric("Стоимость в юанях", format_currency(cost_kpi_product['price_yuan']))
                            st.metric("Стоимость за ед. в Китае (RUB)", format_currency(results['price_rub_china']))

                        
                        with col2:
                            st.markdown("### 🚚 Логистика")
                            st.metric("Вес единицы", format_number(cost_kpi_product['weight']) + " г")
                            st.metric("Общий вес", format_number((cost_kpi_product['weight'] * cost_kpi_product['quantity']) / 1000) + " кг")
                            st.metric("Стоимость доставки в России (USD)", format_usd(cost_kpi_product['delivery_russia_usd']))
                            
                            # Обработка старых данных для KPI
                            logistics_per_unit = results.get('logistics_china_per_unit', 0)
                            logistics_total = results.get('logistics_china_total', 0)
                            
                            # Если поля не найдены, рассчитываем их из старых данных
                            if logistics_per_unit == 0 and logistics_total == 0:
                                if 'logistics_china_calculated' in results:
                                    # Старый формат данных
                                    logistics_total = results['logistics_china_calculated']
                                    logistics_per_unit = logistics_total / cost_kpi_product['quantity'] if cost_kpi_product['quantity'] > 0 else 0
                                else:
                                    # Если нет данных о логистике, рассчитываем заново
                                    logistics_per_unit = cost_kpi_product['weight'] * cost_kpi_product['delivery_russia_usd'] * cost_kpi_product['usd_rate']
                                    logistics_total = logistics_per_unit * cost_kpi_product['quantity']
                            
                            st.metric("Логистика из Китая на ед.", format_currency(logistics_per_unit))
                            st.metric("Логистика из Китая общая", format_currency(logistics_total))
                        
                        with col3:
                            st.markdown("### 📦 Дополнительные расходы")
                            st.metric("ФФ общий", format_currency(cost_kpi_product['ff']))
                            st.metric("ФФ на ед.", format_currency(results.get('ff_per_unit', cost_kpi_product['ff'] / cost_kpi_product['quantity'] if cost_kpi_product['quantity'] > 0 else 0)))
                            st.metric("Разработка (общая)", format_currency(cost_kpi_product.get('development', 0)))
                            st.metric("Разработка на ед.", format_currency(results.get('development_per_unit', cost_kpi_product.get('development', 0) / cost_kpi_product['quantity'] if cost_kpi_product['quantity'] > 0 else 0)))
                            st.metric("Прочие расходы (общие)", format_currency(cost_kpi_product.get('other_expenses', 0)))
                            st.metric("Прочие расходы на ед.", format_currency(results.get('other_expenses_per_unit', cost_kpi_product.get('other_expenses', 0) / cost_kpi_product['quantity'] if cost_kpi_product['quantity'] > 0 else 0)))
                        
                        with col4:
                            st.markdown("### 💎 Итоговая себестоимость")
                            st.metric("Себестоимость на ед.", format_currency(results['cost_per_unit']))
                            st.metric("Общая себестоимость", format_currency(results['total_cost']))
                            st.metric("Количество", format_number(cost_kpi_product['quantity']))
                        
                        # Дополнительные метрики
                        st.markdown("---")
                        col1, col2, col3, col4 = st.columns(4)
                        
                        with col1:
                            st.markdown("### 💱 Курсы валют")
                            st.metric("Курс юаня", format_number(cost_kpi_product['yuan_rate']))
                            st.metric("Курс доллара", format_number(cost_kpi_product['usd_rate']))
                        
                        # Убрали раздел "📊 Показатели эффективности"
                        
                        # Убрали раздел "🎯 Доли затрат"
                        
                        with col4:
                            st.markdown("### 📅 Информация")
                            st.metric("Дата создания", cost_kpi_product.get('created_date', 'Неизвестно'))
            else:
                st.info("📝 Нет сохраненных расчетов себестоимости для отображения KPI")
            
            # Общий итог по всем расчетам себестоимости
            st.markdown("---")
            st.subheader("📊 Общий итог по всем расчетам себестоимости")
            
            if cost_products:
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Всего расчетов", len(cost_products))
                    st.metric("Общее количество товаров", format_number(total_quantity_sum))
                
                with col2:
                    st.metric("Общая себестоимость", format_currency(total_cost_sum))
                    if total_quantity_sum > 0:
                        avg_cost_per_unit = total_cost_sum / total_quantity_sum
                        st.metric("Средняя себестоимость на ед.", format_currency(avg_cost_per_unit))
                    else:
                        st.metric("Средняя себестоимость на ед.", "0 ₽")
                
                with col3:
                    # Средние показатели
                    avg_yuan_rate = sum(p['yuan_rate'] for p in cost_products) / len(cost_products)
                    avg_usd_rate = sum(p['usd_rate'] for p in cost_products) / len(cost_products)
                    st.metric("Средний курс юаня", format_number(avg_yuan_rate))
                    st.metric("Средний курс доллара", format_number(avg_usd_rate))
                
                with col4:
                    # Общие затраты по категориям
                    total_ff = sum(p['ff'] for p in cost_products)
                    total_development = sum(p.get('development', 0) for p in cost_products)
                    total_other_expenses = sum(p.get('other_expenses', 0) for p in cost_products)
                    st.metric("Общий ФФ", format_currency(total_ff))
                    st.metric("Общая разработка", format_currency(total_development))
                    st.metric("Общие прочие расходы", format_currency(total_other_expenses))
            
            # Экспорт данных себестоимости
            st.markdown("---")
            st.subheader("📤 Экспорт данных себестоимости")
            
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("📥 Экспорт в Excel", type="primary", key="export_cost_excel"):
                    # Создаем Excel файл с расчетами себестоимости
                    output = BytesIO()
                    with pd.ExcelWriter(output, engine='openpyxl') as writer:
                        # Таблица себестоимости
                        df_cost_table.to_excel(writer, sheet_name='Расчеты себестоимости', index=False)
                        
                        # Детальные данные
                        detailed_cost_data = []
                        for product in cost_products:
                            results = product['results']
                            
                            # Обработка старых данных для экспорта
                            logistics_per_unit = results.get('logistics_china_per_unit', 0)
                            logistics_total = results.get('logistics_china_total', 0)
                            
                            # Если поля не найдены, рассчитываем их из старых данных
                            if logistics_per_unit == 0 and logistics_total == 0:
                                if 'logistics_china_calculated' in results:
                                    # Старый формат данных
                                    logistics_total = results['logistics_china_calculated']
                                    logistics_per_unit = logistics_total / product['quantity'] if product['quantity'] > 0 else 0
                                else:
                                    # Если нет данных о логистике, рассчитываем заново
                                    logistics_per_unit = product['weight'] * product['delivery_russia_usd'] * product['usd_rate']
                                    logistics_total = logistics_per_unit * product['quantity']
                            
                            detailed_cost_data.append({
                                'Товар': product['product_name'],
                                'Стоимость в юанях': product['price_yuan'],
                                'Стоимость за ед. в Китае (RUB)': results.get('price_rub_china_per_unit', results['price_rub_china'] / product['quantity'] if product['quantity'] > 0 else 0),
                                'Стоимость в Китае общая (RUB)': results['price_rub_china'],
                                'Доставка в России (USD)': product['delivery_russia_usd'],
                                'Логистика из Китая на ед.': logistics_per_unit,
                                'Логистика из Китая общая': logistics_total,
                                'Вес (г)': product['weight'],
                                'Количество': product['quantity'],
                                'ФФ общий': product['ff'],
                                'ФФ на ед.': results.get('ff_per_unit', product['ff'] / product['quantity'] if product['quantity'] > 0 else 0),
                                'Курс юаня': product['yuan_rate'],
                                'Курс доллара': product['usd_rate'],
                                'Себестоимость на ед.': results['cost_per_unit'],
                                'Общая себестоимость': results['total_cost'],
                                'Дата создания': product.get('created_date', 'Неизвестно')
                            })
                        
                        pd.DataFrame(detailed_cost_data).to_excel(writer, sheet_name='Детальные данные', index=False)
                    
                    output.seek(0)
                    st.download_button(
                        label="Скачать Excel файл",
                        data=output.getvalue(),
                        file_name=f"cost_calculations_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
            
            with col2:
                if st.button("📊 Экспорт в CSV", key="export_cost_csv"):
                    csv = df_cost_table.to_csv(index=False, encoding='utf-8-sig')
                    st.download_button(
                        label="Скачать CSV файл",
                        data=csv,
                        file_name=f"cost_calculations_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv"
                    )


if __name__ == "__main__":
    main()
