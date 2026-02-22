# -*- coding: utf-8 -*-
"""
Модуль расчётов юнит-экономики и прибыли
"""

def calculate_unit_economics(
    cost_price, retail_price, commission_rate, logistics_cost, advertising_percent, 
    buyout_percent, storage_cost=0, tax_rate=7.0
):
    """Расчёт юнит-экономики для одной единицы товара"""
    # Комиссия WB
    commission = retail_price * (commission_rate / 100)
    
    # Реклама
    advertising = retail_price * (advertising_percent / 100)
    
    # Логистика с учётом выкупа
    # Формула: (buyout% × logistics + (100% - buyout%) × (logistics + 50)) × 100 / buyout%
    if buyout_percent > 0:
        logistics_with_buyout = (
            (buyout_percent / 100) * logistics_cost + 
            (1 - buyout_percent / 100) * (logistics_cost + 50)
        ) * 100 / buyout_percent
    else:
        logistics_with_buyout = logistics_cost
    
    # Выручка с единицы (после вычета комиссии, логистики и рекламы)
    revenue_per_unit = retail_price - commission - logistics_with_buyout - advertising
    
    # Налог от чистого прихода на расчётный счёт
    taxable_base = revenue_per_unit if revenue_per_unit > 0 else 0
    tax = taxable_base * (tax_rate / 100)
    
    # Прибыль с единицы
    profit_per_unit = revenue_per_unit - cost_price - tax
    
    # Маржинальность (% от цены)
    margin_percent = (profit_per_unit / retail_price * 100) if retail_price > 0 else 0
    
    # Рентабельность (% от себестоимости)
    profitability_percent = (profit_per_unit / cost_price * 100) if cost_price > 0 else 0
    
    return {
        'Цена продажи': retail_price,
        'Себестоимость': cost_price,
        'Комиссия, руб': commission,
        'Логистика с учетом выкупа': logistics_with_buyout,
        'Реклама, руб': advertising,
        'Налог, руб': tax,
        'Выручка с ед.': revenue_per_unit,
        'Прибыль с ед.': profit_per_unit,
        'Маржинальность, %': margin_percent,
        'Рентабельность, %': profitability_percent
    }


def calculate_daily_profit(
    sales_count, price_no_spp, cost_price, commission_rate, logistics_cost,
    advertising_percent, buyout_percent, storage_cost=0, tax_rate=7.0
):
    """Расчёт дневной прибыли от цены без СПП"""
    ue = calculate_unit_economics(
        cost_price=cost_price,
        retail_price=price_no_spp,
        commission_rate=commission_rate,
        logistics_cost=logistics_cost,
        advertising_percent=advertising_percent,
        buyout_percent=buyout_percent,
        storage_cost=storage_cost,
        tax_rate=tax_rate
    )
    
    total_revenue = ue['Выручка с ед.'] * sales_count
    total_profit = ue['Прибыль с ед.'] * sales_count
    
    return {
        'Продажи': sales_count,
        'Цена': price_no_spp,
        'Прибыль с ед.': ue['Прибыль с ед.'],
        'Общая выручка': total_revenue,
        'Общая прибыль': total_profit
    }




























