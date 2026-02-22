# -*- coding: utf-8 -*-
"""
Модуль интеграции данных для ИИ-аналитика
Позволяет получать данные из различных приложений проекта
"""

import pandas as pd
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

class DataIntegration:
    """Класс для интеграции данных из различных источников"""
    
    def __init__(self):
        self.base_path = os.path.dirname(os.path.abspath(__file__))
    
    def get_wb_analysis_data(self) -> Optional[pd.DataFrame]:
        """Получает данные из анализа WB (45.xlsx)"""
        try:
            # Пробуем загрузить из кеша
            cache_file = os.path.join(self.base_path, 'data_cache.csv')
            if os.path.exists(cache_file):
                df = pd.read_csv(cache_file)
                df['Дата'] = pd.to_datetime(df['Дата'])
                return df
            
            # Если кеша нет, загружаем из основного файла
            excel_file = os.path.join(self.base_path, '45.xlsx')
            if os.path.exists(excel_file):
                df = pd.read_excel(excel_file, sheet_name='Товары', header=1)
                df['Дата'] = pd.to_datetime(df['Дата'])
                
                # Преобразуем числовые столбцы
                numeric_cols = ['Заказали, шт', 'Выкупили, шт', 'Выкупили на сумму, ₽', 
                               'Переходы в карточку', 'Положили в корзину', 'Процент выкупа',
                               'Заказали на сумму, ₽']
                for col in numeric_cols:
                    if col in df.columns:
                        df[col] = pd.to_numeric(df[col], errors='coerce')
                
                return df
        except Exception as e:
            print(f"Ошибка загрузки данных WB анализа: {e}")
            return None
    
    def get_production_calendar_data(self) -> Optional[List[Dict]]:
        """Получает данные из календаря производства"""
        try:
            calendar_file = os.path.join(self.base_path, 'production_calendar_data.json')
            if os.path.exists(calendar_file):
                with open(calendar_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Ошибка загрузки данных календаря производства: {e}")
            return None
    
    def get_seasonal_calculator_data(self) -> Optional[Dict]:
        """Получает данные из сезонного калькулятора"""
        try:
            seasonal_file = os.path.join(self.base_path, 'seasonal_data.json')
            if os.path.exists(seasonal_file):
                with open(seasonal_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Ошибка загрузки данных сезонного калькулятора: {e}")
            return None
    
    def get_investments_data(self) -> Optional[Dict]:
        """Получает данные об инвестициях"""
        try:
            investments_file = os.path.join(self.base_path, 'investments_data.json')
            if os.path.exists(investments_file):
                with open(investments_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Ошибка загрузки данных инвестиций: {e}")
            return None
    
    def get_unit_economics_data(self) -> Optional[pd.DataFrame]:
        """Получает данные из юнит-экономики"""
        try:
            unit_file = os.path.join(self.base_path, 'UNIT', 'unit_economics_products_table_FINAL.py')
            if os.path.exists(unit_file):
                # Здесь можно добавить логику для извлечения данных из юнит-экономики
                # Пока возвращаем None, так как нужно изучить структуру данных
                pass
        except Exception as e:
            print(f"Ошибка загрузки данных юнит-экономики: {e}")
            return None
    
    def get_all_data_sources(self) -> Dict[str, Any]:
        """Получает все доступные источники данных"""
        data_sources = {}
        
        # WB анализ
        wb_data = self.get_wb_analysis_data()
        if wb_data is not None:
            data_sources['wb_analysis'] = wb_data
        
        # Календарь производства
        production_data = self.get_production_calendar_data()
        if production_data is not None:
            data_sources['production_calendar'] = production_data
        
        # Сезонный калькулятор
        seasonal_data = self.get_seasonal_calculator_data()
        if seasonal_data is not None:
            data_sources['seasonal_calculator'] = seasonal_data
        
        # Инвестиции
        investments_data = self.get_investments_data()
        if investments_data is not None:
            data_sources['investments'] = investments_data
        
        # Юнит-экономика
        unit_data = self.get_unit_economics_data()
        if unit_data is not None:
            data_sources['unit_economics'] = unit_data
        
        return data_sources
    
    def get_data_summary(self) -> Dict[str, Any]:
        """Получает сводку по всем доступным данным"""
        data_sources = self.get_all_data_sources()
        summary = {
            'total_sources': len(data_sources),
            'available_sources': list(data_sources.keys()),
            'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'details': {}
        }
        
        # Детали по каждому источнику
        if 'wb_analysis' in data_sources:
            df = data_sources['wb_analysis']
            summary['details']['wb_analysis'] = {
                'records': len(df),
                'date_range': f"{df['Дата'].min().strftime('%d.%m.%Y')} - {df['Дата'].max().strftime('%d.%m.%Y')}",
                'products': df['Артикул WB'].nunique(),
                'total_orders': df['Заказали, шт'].sum(),
                'total_sales': df['Выкупили, шт'].sum(),
                'total_revenue': df['Выкупили на сумму, ₽'].sum()
            }
        
        if 'production_calendar' in data_sources:
            projects = data_sources['production_calendar']
            active_projects = [p for p in projects if 
                             datetime.strptime(p['wb_end'], "%Y-%m-%d").date() >= datetime.now().date()]
            summary['details']['production_calendar'] = {
                'total_projects': len(projects),
                'active_projects': len(active_projects),
                'total_development_cost': sum(p.get('total_development_cost', 0) for p in projects)
            }
        
        if 'seasonal_calculator' in data_sources:
            seasonal = data_sources['seasonal_calculator']
            summary['details']['seasonal_calculator'] = {
                'data_points': len(seasonal) if isinstance(seasonal, list) else 1,
                'available': True
            }
        
        if 'investments' in data_sources:
            investments = data_sources['investments']
            summary['details']['investments'] = {
                'data_points': len(investments) if isinstance(investments, list) else 1,
                'available': True
            }
        
        return summary
    
    def validate_data_quality(self) -> Dict[str, Any]:
        """Проверяет качество данных"""
        data_sources = self.get_all_data_sources()
        quality_report = {
            'overall_score': 0,
            'sources_checked': 0,
            'issues': [],
            'recommendations': []
        }
        
        total_score = 0
        sources_checked = 0
        
        # Проверка WB анализа
        if 'wb_analysis' in data_sources:
            df = data_sources['wb_analysis']
            sources_checked += 1
            
            # Проверяем наличие обязательных колонок
            required_cols = ['Дата', 'Заказали, шт', 'Выкупили, шт', 'Выкупили на сумму, ₽']
            missing_cols = [col for col in required_cols if col not in df.columns]
            
            if missing_cols:
                quality_report['issues'].append(f"WB анализ: отсутствуют колонки {missing_cols}")
                total_score += 50
            else:
                total_score += 100
            
            # Проверяем на пропуски в данных
            null_counts = df[required_cols].isnull().sum()
            if null_counts.sum() > 0:
                quality_report['issues'].append(f"WB анализ: найдены пропуски в данных")
                total_score += 75
            
            # Проверяем актуальность данных
            latest_date = df['Дата'].max()
            days_old = (datetime.now() - latest_date).days
            if days_old > 30:
                quality_report['issues'].append(f"WB анализ: данные устарели на {days_old} дней")
                quality_report['recommendations'].append("Обновите данные WB анализа")
        
        # Проверка календаря производства
        if 'production_calendar' in data_sources:
            projects = data_sources['production_calendar']
            sources_checked += 1
            
            if not projects:
                quality_report['issues'].append("Календарь производства: нет проектов")
                total_score += 0
            else:
                total_score += 100
                
                # Проверяем просроченные проекты
                overdue_count = 0
                for project in projects:
                    target_date = datetime.strptime(project['target_launch'], "%Y-%m-%d").date()
                    if target_date < datetime.now().date():
                        overdue_count += 1
                
                if overdue_count > 0:
                    quality_report['issues'].append(f"Календарь производства: {overdue_count} просроченных проектов")
                    quality_report['recommendations'].append("Пересмотрите временные рамки проектов")
        
        # Расчет общего балла
        if sources_checked > 0:
            quality_report['overall_score'] = total_score / sources_checked
        quality_report['sources_checked'] = sources_checked
        
        # Общие рекомендации
        if quality_report['overall_score'] < 70:
            quality_report['recommendations'].append("Общее качество данных требует улучшения")
        
        return quality_report
    
    def get_cross_app_insights(self) -> Dict[str, Any]:
        """Получает инсайты на основе данных из разных приложений"""
        data_sources = self.get_all_data_sources()
        insights = {
            'sales_vs_production': {},
            'investment_analysis': {},
            'seasonal_patterns': {},
            'recommendations': []
        }
        
        # Сравнение продаж и производства
        if 'wb_analysis' in data_sources and 'production_calendar' in data_sources:
            wb_data = data_sources['wb_analysis']
            production_data = data_sources['production_calendar']
            
            # Анализ текущих продаж
            current_month = datetime.now().month
            current_year = datetime.now().year
            current_month_sales = wb_data[
                (wb_data['Дата'].dt.month == current_month) & 
                (wb_data['Дата'].dt.year == current_year)
            ]
            
            total_sales = current_month_sales['Выкупили, шт'].sum()
            total_revenue = current_month_sales['Выкупили на сумму, ₽'].sum()
            
            # Анализ активных проектов
            active_projects = [p for p in production_data if 
                             datetime.strptime(p['wb_end'], "%Y-%m-%d").date() >= datetime.now().date()]
            
            insights['sales_vs_production'] = {
                'current_month_sales': total_sales,
                'current_month_revenue': total_revenue,
                'active_projects_count': len(active_projects),
                'development_investment': sum(p.get('total_development_cost', 0) for p in active_projects)
            }
            
            # Рекомендации
            if total_sales > 0 and len(active_projects) > 0:
                revenue_per_project = total_revenue / len(active_projects)
                insights['recommendations'].append(
                    f"Средняя выручка на активный проект: {revenue_per_project:,.0f} ₽"
                )
        
        # Анализ инвестиций
        if 'production_calendar' in data_sources:
            projects = data_sources['production_calendar']
            total_development_cost = sum(p.get('total_development_cost', 0) for p in projects)
            
            if total_development_cost > 0:
                insights['investment_analysis'] = {
                    'total_development_cost': total_development_cost,
                    'average_cost_per_project': total_development_cost / len(projects) if projects else 0,
                    'projects_with_costs': len([p for p in projects if p.get('total_development_cost', 0) > 0])
                }
        
        return insights

# Функция для использования в других приложениях
def get_integrated_data() -> Dict[str, Any]:
    """Удобная функция для получения интегрированных данных"""
    integration = DataIntegration()
    return integration.get_all_data_sources()

def get_data_summary() -> Dict[str, Any]:
    """Удобная функция для получения сводки данных"""
    integration = DataIntegration()
    return integration.get_data_summary()

def validate_data() -> Dict[str, Any]:
    """Удобная функция для проверки качества данных"""
    integration = DataIntegration()
    return integration.validate_data_quality()

def get_cross_insights() -> Dict[str, Any]:
    """Удобная функция для получения кросс-приложенческих инсайтов"""
    integration = DataIntegration()
    return integration.get_cross_app_insights()

if __name__ == "__main__":
    # Тестирование модуля
    integration = DataIntegration()
    
    print("🔍 Тестирование интеграции данных...")
    print("=" * 50)
    
    # Получение всех данных
    data_sources = integration.get_all_data_sources()
    print(f"📊 Найдено источников данных: {len(data_sources)}")
    for source in data_sources.keys():
        print(f"   ✅ {source}")
    
    # Сводка данных
    summary = integration.get_data_summary()
    print(f"\n📋 Сводка данных:")
    print(f"   Обновлено: {summary['last_updated']}")
    print(f"   Источников: {summary['total_sources']}")
    
    # Проверка качества
    quality = integration.validate_data_quality()
    print(f"\n🔍 Качество данных: {quality['overall_score']:.1f}/100")
    if quality['issues']:
        print("   ⚠️ Проблемы:")
        for issue in quality['issues']:
            print(f"      - {issue}")
    
    # Инсайты
    insights = integration.get_cross_app_insights()
    if insights['recommendations']:
        print(f"\n💡 Рекомендации:")
        for rec in insights['recommendations']:
            print(f"      - {rec}")
    
    print("\n✅ Тестирование завершено!")












