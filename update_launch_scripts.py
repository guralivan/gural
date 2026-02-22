#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для обновления путей в launch-скриптах после перемещения приложений в apps/
"""

import os
import re
from pathlib import Path

# Маппинг старых путей на новые
PATH_MAPPING = {
    'dashboard_final.py': 'apps/dashboard/dashboard_final.py',
    'app_45_simple.py': 'apps/analytics_45/app_45_simple.py',
    'app_45_combined_api_new.py': 'apps/analytics_45/app_45_combined_api_new.py',
    'app_45_combined_api.py': 'apps/analytics_45/app_45_combined_api.py',
    'app_45_analysis.py': 'apps/analytics_45/app_45_analysis.py',
    'app_45_analysis_enhanced.py': 'apps/analytics_45/app_45_analysis_enhanced.py',
    'app_45_analysis_with_api.py': 'apps/analytics_45/app_45_analysis_with_api.py',
    'app_prophet_orders.py': 'apps/prophet_orders/app_prophet_orders.py',
    'app_prophet_forecast_new.py': 'apps/prophet_forecast/app_prophet_forecast_new.py',
    'app_prophet_forecast.py': 'apps/prophet_forecast/app_prophet_forecast.py',
    'app_prophet_orders_cache.py': 'apps/prophet_orders/app_prophet_orders_cache.py',
    'app_prophet_orders_sales_cache.py': 'apps/prophet_orders/app_prophet_orders_sales_cache.py',
    'app_forecast_45.py': 'apps/forecast_45/app_forecast_45.py',
    'app_forecast_orders.py': 'apps/forecast_orders/app_forecast_orders.py',
    'order_balance_app.py': 'apps/order_balance/order_balance_app.py',
    'seasonal_expenses_calculator.py': 'apps/seasonal_calculator/seasonal_expenses_calculator.py',
    'production_calendar.py': 'apps/production_calendar/production_calendar.py',
    'color_recognition_app.py': 'apps/color_recognition/color_recognition_app.py',
    'contract_generator_app.py': 'apps/contract_generator/contract_generator_app.py',
    'sales_planning_app.py': 'apps/sales_planning/sales_planning_app.py',
    'voronka_app.py': 'apps/voronka/voronka_app.py',
    'voronka_app_simple.py': 'apps/voronka/voronka_app_simple.py',
    'Plan_prodazh.py': 'apps/voronka/Plan_prodazh.py',
    'ord_yandex_app.py': 'apps/ord_yandex/ord_yandex_app.py',
    'ord_yandex_app_full.py': 'apps/ord_yandex/ord_yandex_app_full.py',
    'wb_api_optimized.py': 'apps/wb_api/wb_api_optimized.py',
    'wb_api_extended.py': 'apps/wb_api/wb_api_extended.py',
    'wb_api_fbo.py': 'apps/wb_api/wb_api_fbo.py',
    'wb_api_app.py': 'apps/wb_api/wb_api_app.py',
    'wb_api_app_fixed.py': 'apps/wb_api/wb_api_app_fixed.py',
    'ai_analyst.py': 'apps/ai_analyst/ai_analyst.py',
    'wb_auto_downloader.py': 'apps/auto_downloader/wb_auto_downloader.py',
    'inventory_calculator.py': 'apps/inventory_calculator/inventory_calculator.py',
    # Специальные случаи с путями
    'UNIT/unit_economics_products_table_FINAL.py': 'UNIT/unit_economics_products_table_FINAL.py',  # Оставляем как есть
    '3/weekly_expenses_analyzer_final_stable.py': '3/weekly_expenses_analyzer_final_stable.py',  # Оставляем как есть
}

def update_file(filepath):
    """Обновляет пути в файле"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        updated = False
        
        # Обновляем каждый путь
        for old_path, new_path in PATH_MAPPING.items():
            # Ищем паттерны типа "streamlit run old_path" или "run old_path"
            patterns = [
                (rf'streamlit run\s+{re.escape(old_path)}', f'streamlit run {new_path}'),
                (rf'streamlit run\s+"{re.escape(old_path)}"', f'streamlit run "{new_path}"'),
                (rf'streamlit run\s+\'{re.escape(old_path)}\'', f"streamlit run '{new_path}'"),
                (rf'python.*-m streamlit run\s+{re.escape(old_path)}', f'python3 -m streamlit run {new_path}'),
                (rf'python.*-m streamlit run\s+"{re.escape(old_path)}"', f'python3 -m streamlit run "{new_path}"'),
                # Для путей в кавычках внутри скриптов
                (rf'"{re.escape(old_path)}"', f'"{new_path}"'),
                (rf"'{re.escape(old_path)}'", f"'{new_path}'"),
            ]
            
            for pattern, replacement in patterns:
                if re.search(pattern, content):
                    content = re.sub(pattern, replacement, content)
                    updated = True
        
        if updated and content != original_content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✅ {filepath}")
            return True
        else:
            print(f"⏭️  {filepath} - нет изменений")
            return False
            
    except Exception as e:
        print(f"❌ {filepath} - ошибка: {e}")
        return False

def main():
    """Основная функция"""
    project_root = Path(__file__).parent
    
    # Находим все .command файлы
    command_files = list(project_root.glob('*.command'))
    command_files.extend(project_root.glob('**/*.command'))
    
    print(f"🔍 Найдено {len(command_files)} .command файлов")
    print()
    
    updated_count = 0
    for filepath in command_files:
        if update_file(filepath):
            updated_count += 1
    
    print()
    print(f"✅ Обновлено {updated_count} файлов")

if __name__ == '__main__':
    main()
























