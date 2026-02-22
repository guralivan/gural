# -*- coding: utf-8 -*-
"""
ИИ-сотрудник для анализа данных и генерации ежедневных отчетов
Анализирует продажи, заказы, выручку, динамику и прогнозы на основе данных приложений
"""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta, date
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json
import os
import warnings
warnings.filterwarnings('ignore')

# Импорт модуля интеграции данных
try:
    from data_integration import DataIntegration
    INTEGRATION_AVAILABLE = True
except ImportError:
    INTEGRATION_AVAILABLE = False

# Настройка страницы
st.set_page_config(
    page_title="ИИ-аналитик данных",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Кастомные стили
st.markdown("""
<style>
    /* Основные стили */
    .main-header {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    
    .metric-card {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        border-left: 4px solid #667eea;
        margin-bottom: 1rem;
    }
    
    .alert-critical {
        background: linear-gradient(135deg, #ff6b6b, #ee5a52);
        color: white;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
    }
    
    .alert-high {
        background: linear-gradient(135deg, #ffa726, #ff9800);
        color: white;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
    }
    
    .alert-medium {
        background: linear-gradient(135deg, #42a5f5, #2196f3);
        color: white;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
    }
    
    .recommendation-card {
        background: white;
        border-radius: 10px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
        border-left: 4px solid;
    }
    
    .recommendation-critical {
        border-left-color: #ff6b6b;
    }
    
    .recommendation-high {
        border-left-color: #ffa726;
    }
    
    .recommendation-medium {
        border-left-color: #42a5f5;
    }
    
    .recommendation-positive {
        border-left-color: #4caf50;
    }
    
    .section-header {
        background: linear-gradient(90deg, #f8f9fa, #e9ecef);
        padding: 1rem;
        border-radius: 8px;
        margin: 1.5rem 0 1rem 0;
        border-left: 4px solid #667eea;
    }
    
    .filter-section {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
        border: 1px solid #dee2e6;
    }
    
    .chart-container {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        margin: 1rem 0;
    }
    
    .period-selector {
        background: linear-gradient(135deg, #667eea, #764ba2);
        color: white;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
    }
    
    /* Анимации */
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    .fade-in {
        animation: fadeIn 0.5s ease-out;
    }
    
    /* Улучшенные кнопки */
    .stButton > button {
        background: linear-gradient(90deg, #667eea, #764ba2);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.5rem 1rem;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
    }
</style>
""", unsafe_allow_html=True)

class AIAnalyst:
    """ИИ-сотрудник для анализа данных и генерации отчетов"""
    
    def __init__(self):
        self.name = "Александр"
        self.position = "Старший аналитик данных"
        self.avatar = "🤖"
        self.current_date = datetime.now()
        
    def load_data_sources(self):
        """Загружает данные из различных источников"""
        if INTEGRATION_AVAILABLE:
            # Используем модуль интеграции данных
            integration = DataIntegration()
            data_sources = integration.get_all_data_sources()
            
            # Показываем информацию о качестве данных
            quality = integration.validate_data_quality()
            if quality['overall_score'] < 80:
                st.warning(f"⚠️ Качество данных: {quality['overall_score']:.1f}/100. Рекомендуется обновить данные.")
            
            return data_sources
        else:
            # Резервный метод загрузки данных
            data_sources = {}
            
            # Загрузка данных из анализа 45.xlsx
            try:
                if os.path.exists('data_cache.csv'):
                    df_45 = pd.read_csv('data_cache.csv')
                    df_45['Дата'] = pd.to_datetime(df_45['Дата'])
                    data_sources['wb_analysis'] = df_45
                elif os.path.exists('45.xlsx'):
                    df_45 = pd.read_excel('45.xlsx', sheet_name='Товары', header=1)
                    df_45['Дата'] = pd.to_datetime(df_45['Дата'])
                    data_sources['wb_analysis'] = df_45
            except Exception as e:
                st.warning(f"Не удалось загрузить данные WB анализа: {e}")
            
            # Загрузка данных календаря производства
            try:
                if os.path.exists('production_calendar_data.json'):
                    with open('production_calendar_data.json', 'r', encoding='utf-8') as f:
                        data_sources['production_calendar'] = json.load(f)
            except Exception as e:
                st.warning(f"Не удалось загрузить данные календаря производства: {e}")
            
            # Загрузка данных сезонного калькулятора
            try:
                if os.path.exists('seasonal_data.json'):
                    with open('seasonal_data.json', 'r', encoding='utf-8') as f:
                        data_sources['seasonal_calculator'] = json.load(f)
            except Exception as e:
                st.warning(f"Не удалось загрузить данные сезонного калькулятора: {e}")
            
            # Загрузка данных инвестиций
            try:
                if os.path.exists('investments_data.json'):
                    with open('investments_data.json', 'r', encoding='utf-8') as f:
                        data_sources['investments'] = json.load(f)
            except Exception as e:
                st.warning(f"Не удалось загрузить данные инвестиций: {e}")
            
            return data_sources
    
    def analyze_sales_performance(self, df, period_days=30, start_date=None, end_date=None):
        """Анализ производительности продаж с учетом выбранного периода и сезонности"""
        if df is None or df.empty:
            return None
        
        # Определение периода анализа
        if start_date and end_date:
            analysis_start = start_date
            analysis_end = end_date
        else:
            analysis_end = self.current_date
            analysis_start = self.current_date - timedelta(days=period_days)
        
        # Преобразование дат в datetime для корректного сравнения
        if isinstance(analysis_start, date):
            analysis_start = pd.Timestamp(analysis_start)
        if isinstance(analysis_end, date):
            analysis_end = pd.Timestamp(analysis_end)
        
        # Данные за выбранный период
        period_data = df[
            (df['Дата'] >= analysis_start) & 
            (df['Дата'] <= analysis_end)
        ]
        
        # Данные за предыдущий период для сравнения
        period_length = (analysis_end - analysis_start).days + 1
        prev_period_start = analysis_start - timedelta(days=period_length)
        prev_period_end = analysis_start - timedelta(days=1)
        prev_period_data = df[
            (df['Дата'] >= prev_period_start) & 
            (df['Дата'] <= prev_period_end)
        ]
        
        if period_data.empty:
            return None
        
        # Основные метрики
        total_orders = period_data['Заказали, шт'].sum()
        total_sales = period_data['Выкупили, шт'].sum()
        total_revenue = period_data['Выкупили на сумму, ₽'].sum()
        conversion_rate = (total_sales / total_orders * 100) if total_orders > 0 else 0
        
        # Сравнение с предыдущим периодом
        period_comparison = {}
        if not prev_period_data.empty:
            prev_orders = prev_period_data['Заказали, шт'].sum()
            prev_sales = prev_period_data['Выкупили, шт'].sum()
            prev_revenue = prev_period_data['Выкупили на сумму, ₽'].sum()
            
            orders_change = ((total_orders - prev_orders) / prev_orders * 100) if prev_orders > 0 else 0
            sales_change = ((total_sales - prev_sales) / prev_sales * 100) if prev_sales > 0 else 0
            revenue_change = ((total_revenue - prev_revenue) / prev_revenue * 100) if prev_revenue > 0 else 0
            
            period_comparison = {
                'orders_change': orders_change,
                'sales_change': sales_change,
                'revenue_change': revenue_change
            }
        
        # Анализ сезонности
        seasonality_analysis = self._analyze_seasonality(df, analysis_start, analysis_end)
        
        return {
            'period_start': analysis_start,
            'period_end': analysis_end,
            'period_days': period_length,
            'total_orders': total_orders,
            'total_sales': total_sales,
            'total_revenue': total_revenue,
            'conversion_rate': conversion_rate,
            'period_data': period_data,
            'period_comparison': period_comparison,
            'seasonality_analysis': seasonality_analysis
        }
    
    def _analyze_seasonality(self, df, start_date, end_date):
        """Анализ сезонности продаж"""
        if df is None or df.empty:
            return None
        
        # Преобразование дат в datetime для корректного сравнения
        if isinstance(start_date, date):
            start_date = pd.Timestamp(start_date)
        if isinstance(end_date, date):
            end_date = pd.Timestamp(end_date)
        
        # Получаем данные за последние 12 месяцев для анализа сезонности
        twelve_months_ago = start_date - timedelta(days=365)
        historical_data = df[df['Дата'] >= twelve_months_ago]
        
        if historical_data.empty:
            return None
        
        # Анализ по месяцам
        historical_data['month'] = historical_data['Дата'].dt.month
        monthly_stats = historical_data.groupby('month').agg({
            'Заказали, шт': 'sum',
            'Выкупили, шт': 'sum',
            'Выкупили на сумму, ₽': 'sum'
        }).reset_index()
        
        # Анализ по дням недели
        historical_data['weekday'] = historical_data['Дата'].dt.dayofweek
        weekday_stats = historical_data.groupby('weekday').agg({
            'Заказали, шт': 'mean',
            'Выкупили, шт': 'mean',
            'Выкупили на сумму, ₽': 'mean'
        }).reset_index()
        
        # Определение текущего сезона
        current_month = start_date.month if hasattr(start_date, 'month') else start_date.month
        if current_month in [12, 1, 2]:
            current_season = 'Зима'
            season_multiplier = 1.2  # Зимние праздники
        elif current_month in [3, 4, 5]:
            current_season = 'Весна'
            season_multiplier = 1.0
        elif current_month in [6, 7, 8]:
            current_season = 'Лето'
            season_multiplier = 0.9  # Летний спад
        else:
            current_season = 'Осень'
            season_multiplier = 1.1  # Осенний подъем
        
        # Анализ трендов
        monthly_revenue = historical_data.groupby(historical_data['Дата'].dt.to_period('M'))['Выкупили на сумму, ₽'].sum()
        if len(monthly_revenue) > 1:
            revenue_trend = (monthly_revenue.iloc[-1] - monthly_revenue.iloc[-2]) / monthly_revenue.iloc[-2] * 100 if monthly_revenue.iloc[-2] > 0 else 0
        else:
            revenue_trend = 0
        
        return {
            'current_season': current_season,
            'season_multiplier': season_multiplier,
            'monthly_stats': monthly_stats.to_dict('records'),
            'weekday_stats': weekday_stats.to_dict('records'),
            'revenue_trend': revenue_trend,
            'is_seasonal_peak': season_multiplier > 1.1,
            'is_seasonal_low': season_multiplier < 1.0
        }
    
    def analyze_trends(self, df, period_days=30):
        """Анализ трендов и динамики с учетом сезонности"""
        if df is None or df.empty:
            return None
        
        # Группировка по дням для анализа трендов
        daily_data = df.groupby('Дата').agg({
            'Заказали, шт': 'sum',
            'Выкупили, шт': 'sum',
            'Выкупили на сумму, ₽': 'sum'
        }).reset_index()
        
        # Расчет скользящего среднего
        daily_data['orders_ma_7'] = daily_data['Заказали, шт'].rolling(window=7, min_periods=1).mean()
        daily_data['sales_ma_7'] = daily_data['Выкупили, шт'].rolling(window=7, min_periods=1).mean()
        daily_data['revenue_ma_7'] = daily_data['Выкупили на сумму, ₽'].rolling(window=7, min_periods=1).mean()
        
        # Анализ роста за выбранный период
        if len(daily_data) >= period_days:
            analysis_period = daily_data.tail(period_days)
            first_half = analysis_period.head(period_days // 2)
            second_half = analysis_period.tail(period_days // 2)
            
            orders_growth = ((second_half['Заказали, шт'].mean() - first_half['Заказали, шт'].mean()) / 
                           first_half['Заказали, шт'].mean() * 100) if first_half['Заказали, шт'].mean() > 0 else 0
            
            sales_growth = ((second_half['Выкупили, шт'].mean() - first_half['Выкупили, шт'].mean()) / 
                           first_half['Выкупили, шт'].mean() * 100) if first_half['Выкупили, шт'].mean() > 0 else 0
            
            revenue_growth = ((second_half['Выкупили на сумму, ₽'].mean() - first_half['Выкупили на сумму, ₽'].mean()) / 
                             first_half['Выкупили на сумму, ₽'].mean() * 100) if first_half['Выкупили на сумму, ₽'].mean() > 0 else 0
        else:
            orders_growth = sales_growth = revenue_growth = 0
        
        # Анализ графиков и паттернов
        chart_analysis = self._analyze_charts(daily_data)
        
        return {
            'daily_data': daily_data,
            'orders_growth': orders_growth,
            'sales_growth': sales_growth,
            'revenue_growth': revenue_growth,
            'chart_analysis': chart_analysis
        }
    
    def _analyze_charts(self, daily_data):
        """Анализ графиков и выявление паттернов"""
        if daily_data is None or daily_data.empty:
            return None
        
        # Анализ волатильности
        revenue_std = daily_data['Выкупили на сумму, ₽'].std()
        revenue_mean = daily_data['Выкупили на сумму, ₽'].mean()
        revenue_cv = (revenue_std / revenue_mean * 100) if revenue_mean > 0 else 0
        
        # Выявление пиков и спадов
        revenue_threshold_high = revenue_mean + revenue_std
        revenue_threshold_low = revenue_mean - revenue_std
        
        peaks = daily_data[daily_data['Выкупили на сумму, ₽'] > revenue_threshold_high]
        lows = daily_data[daily_data['Выкупили на сумму, ₽'] < revenue_threshold_low]
        
        # Анализ недельных паттернов
        daily_data['weekday'] = daily_data['Дата'].dt.dayofweek
        weekday_performance = daily_data.groupby('weekday')['Выкупили на сумму, ₽'].mean()
        
        best_day_idx = weekday_performance.idxmax()
        worst_day_idx = weekday_performance.idxmin()
        
        weekday_names = ['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота', 'Воскресенье']
        
        return {
            'revenue_mean': revenue_mean,
            'revenue_std': revenue_std,
            'revenue_cv': revenue_cv,
            'peaks_count': len(peaks),
            'lows_count': len(lows),
            'best_weekday': weekday_names[best_day_idx] if best_day_idx < len(weekday_names) else 'Неизвестно',
            'worst_weekday': weekday_names[worst_day_idx] if worst_day_idx < len(weekday_names) else 'Неизвестно',
            'is_volatile': revenue_cv > 30,
            'is_stable': revenue_cv < 15,
            'peak_dates': peaks['Дата'].tolist() if not peaks.empty else [],
            'low_dates': lows['Дата'].tolist() if not lows.empty else []
        }
    
    def generate_forecast(self, df):
        """Генерация прогнозов"""
        if df is None or df.empty:
            return None
        
        # Простой прогноз на основе тренда
        daily_data = df.groupby('Дата').agg({
            'Заказали, шт': 'sum',
            'Выкупили, шт': 'sum',
            'Выкупили на сумму, ₽': 'sum'
        }).reset_index()
        
        if len(daily_data) < 7:
            return None
        
        # Прогноз на следующие 7 дней
        last_7_days = daily_data.tail(7)
        
        avg_orders = last_7_days['Заказали, шт'].mean()
        avg_sales = last_7_days['Выкупили, шт'].mean()
        avg_revenue = last_7_days['Выкупили на сумму, ₽'].mean()
        
        # Прогноз на неделю
        weekly_forecast = {
            'orders': avg_orders * 7,
            'sales': avg_sales * 7,
            'revenue': avg_revenue * 7
        }
        
        # Прогноз на месяц
        monthly_forecast = {
            'orders': avg_orders * 30,
            'sales': avg_sales * 30,
            'revenue': avg_revenue * 30
        }
        
        return {
            'weekly_forecast': weekly_forecast,
            'monthly_forecast': monthly_forecast,
            'confidence': 'Средняя' if len(daily_data) >= 14 else 'Низкая'
        }
    
    def analyze_production_status(self, production_data):
        """Анализ статуса производства"""
        if not production_data:
            return None
        
        active_projects = [p for p in production_data if 
                          datetime.strptime(p['wb_end'], "%Y-%m-%d").date() >= self.current_date.date()]
        
        overdue_projects = [p for p in production_data if 
                           datetime.strptime(p['target_launch'], "%Y-%m-%d").date() < self.current_date.date()]
        
        total_development_cost = sum(p.get('total_development_cost', 0) for p in production_data)
        
        return {
            'total_projects': len(production_data),
            'active_projects': len(active_projects),
            'overdue_projects': len(overdue_projects),
            'total_development_cost': total_development_cost
        }
    
    def generate_daily_report(self, data_sources, period_days=30, start_date=None, end_date=None):
        """Генерация ежедневного отчета с учетом выбранного периода"""
        report = {
            'date': self.current_date.strftime('%d.%m.%Y'),
            'analyst': self.name,
            'position': self.position,
            'analysis_period': {
                'period_days': period_days,
                'start_date': start_date.strftime('%d.%m.%Y') if start_date and hasattr(start_date, 'strftime') else None,
                'end_date': end_date.strftime('%d.%m.%Y') if end_date and hasattr(end_date, 'strftime') else None
            },
            'summary': {},
            'sales_analysis': {},
            'trends_analysis': {},
            'forecast': {},
            'production_status': {},
            'recommendations': [],
            'alerts': []
        }
        
        # Анализ продаж с учетом периода
        if 'wb_analysis' in data_sources:
            sales_analysis = self.analyze_sales_performance(
                data_sources['wb_analysis'], period_days, start_date, end_date
            )
            if sales_analysis:
                report['sales_analysis'] = sales_analysis
                
                # Сравнение с предыдущим периодом
                if 'period_comparison' in sales_analysis and sales_analysis['period_comparison']:
                    report['sales_analysis']['monthly_comparison'] = sales_analysis['period_comparison']
        
        # Анализ трендов с учетом периода
        if 'wb_analysis' in data_sources:
            trends_analysis = self.analyze_trends(data_sources['wb_analysis'], period_days)
            if trends_analysis:
                report['trends_analysis'] = trends_analysis
        
        # Прогнозы
        if 'wb_analysis' in data_sources:
            forecast = self.generate_forecast(data_sources['wb_analysis'])
            if forecast:
                report['forecast'] = forecast
        
        # Статус производства
        if 'production_calendar' in data_sources:
            production_status = self.analyze_production_status(data_sources['production_calendar'])
            if production_status:
                report['production_status'] = production_status
        
        # Генерация рекомендаций
        self.generate_recommendations(report)
        
        # Генерация предупреждений
        self.generate_alerts(report)
        
        # Добавляем кросс-приложенческие инсайты
        if INTEGRATION_AVAILABLE:
            integration = DataIntegration()
            cross_insights = integration.get_cross_app_insights()
            report['cross_app_insights'] = cross_insights
        
        return report
    
    def generate_recommendations(self, report):
        """Генерация развернутых рекомендаций на основе анализа"""
        recommendations = []
        
        # Рекомендации по продажам
        if 'sales_analysis' in report and report['sales_analysis']:
            sales_data = report['sales_analysis']
            conversion = sales_data['conversion_rate']
            total_orders = sales_data['total_orders']
            total_sales = sales_data['total_sales']
            total_revenue = sales_data['total_revenue']
            
            # Анализ конверсии
            if conversion < 30:
                recommendations.append({
                    'type': 'Продажи',
                    'priority': 'Критическая',
                    'title': 'Критически низкая конверсия',
                    'text': f'Конверсия составляет всего {conversion:.1f}% ({total_sales:,} выкупов из {total_orders:,} заказов).',
                    'details': [
                        'Проверьте качество товаров и соответствие описанию',
                        'Проанализируйте отзывы покупателей',
                        'Оптимизируйте процесс логистики и доставки',
                        'Рассмотрите возможность улучшения упаковки',
                        'Проанализируйте ценообразование конкурентов'
                    ],
                    'actions': [
                        'Немедленно проанализировать причины отказов',
                        'Связаться с клиентами, не выкупившими товар',
                        'Провести аудит качества товаров',
                        'Оптимизировать процесс обработки заказов'
                    ]
                })
            elif conversion < 50:
                recommendations.append({
                    'type': 'Продажи',
                    'priority': 'Высокая',
                    'title': 'Низкая конверсия требует внимания',
                    'text': f'Конверсия {conversion:.1f}% ниже рекомендуемого уровня (50%+).',
                    'details': [
                        'Улучшите качество фотографий товаров',
                        'Добавьте подробные описания и характеристики',
                        'Оптимизируйте время обработки заказов',
                        'Проанализируйте сезонность спроса',
                        'Рассмотрите программы лояльности'
                    ],
                    'actions': [
                        'Запустить A/B тестирование карточек товаров',
                        'Улучшить систему уведомлений клиентов',
                        'Оптимизировать процесс возвратов',
                        'Внедрить систему обратной связи'
                    ]
                })
            elif conversion > 80:
                recommendations.append({
                    'type': 'Продажи',
                    'priority': 'Позитивная',
                    'title': 'Отличная конверсия!',
                    'text': f'Превосходная конверсия {conversion:.1f}%! Это указывает на высокое качество товаров и сервиса.',
                    'details': [
                        'Поддерживайте текущий уровень качества',
                        'Рассмотрите возможность увеличения цен',
                        'Масштабируйте успешные товары',
                        'Используйте как кейс для других товаров',
                        'Анализируйте факторы успеха'
                    ],
                    'actions': [
                        'Документировать успешные практики',
                        'Масштабировать на другие товары',
                        'Увеличить закупки популярных позиций',
                        'Развивать бренд на основе качества'
                    ]
                })
            
            # Анализ выручки
            if 'monthly_comparison' in sales_data:
                revenue_change = sales_data['monthly_comparison']['revenue_change']
                orders_change = sales_data['monthly_comparison']['orders_change']
                sales_change = sales_data['monthly_comparison']['sales_change']
                
                if revenue_change < -20:
                    recommendations.append({
                        'type': 'Финансы',
                        'priority': 'Критическая',
                        'title': 'Критическое падение выручки',
                        'text': f'Выручка снизилась на {abs(revenue_change):.1f}% ({orders_change:+.1f}% заказов, {sales_change:+.1f}% выкупов).',
                        'details': [
                            'Проанализируйте причины падения спроса',
                            'Проверьте активность конкурентов',
                            'Оцените сезонные факторы',
                            'Проанализируйте изменения в алгоритмах WB',
                            'Рассмотрите корректировку стратегии ценообразования'
                        ],
                        'actions': [
                            'Немедленно провести анализ конкурентов',
                            'Оптимизировать цены на товары',
                            'Увеличить рекламный бюджет',
                            'Запустить промо-акции',
                            'Проанализировать изменения в маркетплейсе'
                        ]
                    })
                elif revenue_change < -10:
                    recommendations.append({
                        'type': 'Финансы',
                        'priority': 'Высокая',
                        'title': 'Снижение выручки требует внимания',
                        'text': f'Выручка снизилась на {abs(revenue_change):.1f}%. Необходимо принять меры.',
                        'details': [
                            'Проанализируйте тренды по категориям товаров',
                            'Оцените эффективность рекламных кампаний',
                            'Проверьте изменения в позиционировании',
                            'Рассмотрите сезонные корректировки',
                            'Оптимизируйте ассортимент'
                        ],
                        'actions': [
                            'Пересмотреть рекламную стратегию',
                            'Оптимизировать ассортимент товаров',
                            'Улучшить позиционирование',
                            'Провести анализ целевой аудитории'
                        ]
                    })
                elif revenue_change > 30:
                    recommendations.append({
                        'type': 'Финансы',
                        'priority': 'Позитивная',
                        'title': 'Отличный рост выручки!',
                        'text': f'Выручка выросла на {revenue_change:.1f}%! Это отличный результат.',
                        'details': [
                            'Документируйте успешные стратегии',
                            'Масштабируйте эффективные подходы',
                            'Рассмотрите расширение ассортимента',
                            'Инвестируйте в развитие бренда',
                            'Поддерживайте текущий темп роста'
                        ],
                        'actions': [
                            'Увеличить закупки популярных товаров',
                            'Расширить линейку успешных продуктов',
                            'Инвестировать в развитие команды',
                            'Планировать дальнейшее масштабирование'
                        ]
                    })
        
        # Рекомендации по трендам
        if 'trends_analysis' in report and report['trends_analysis']:
            trends = report['trends_analysis']
            orders_growth = trends['orders_growth']
            sales_growth = trends['sales_growth']
            revenue_growth = trends['revenue_growth']
            
            if sales_growth < -15:
                recommendations.append({
                    'type': 'Тренды',
                    'priority': 'Критическая',
                    'title': 'Критическое падение продаж',
                    'text': f'Продажи снизились на {abs(sales_growth):.1f}% за последние 30 дней.',
                    'details': [
                        'Проанализируйте причины падения спроса',
                        'Проверьте активность конкурентов',
                        'Оцените сезонные факторы',
                        'Проанализируйте изменения в предпочтениях клиентов',
                        'Рассмотрите корректировку стратегии'
                    ],
                    'actions': [
                        'Немедленно провести анализ рынка',
                        'Оптимизировать товарное предложение',
                        'Усилить маркетинговые активности',
                        'Пересмотреть ценообразование',
                        'Запустить исследование клиентов'
                    ]
                })
            elif sales_growth < -5:
                recommendations.append({
                    'type': 'Тренды',
                    'priority': 'Высокая',
                    'title': 'Снижение продаж',
                    'text': f'Наблюдается снижение продаж на {abs(sales_growth):.1f}%.',
                    'details': [
                        'Пересмотрите маркетинговую стратегию',
                        'Оптимизируйте рекламные кампании',
                        'Проанализируйте сезонность',
                        'Улучшите позиционирование товаров',
                        'Рассмотрите новые каналы продаж'
                    ],
                    'actions': [
                        'Оптимизировать рекламные кампании',
                        'Улучшить контент-маркетинг',
                        'Проанализировать конкурентов',
                        'Обновить стратегию ценообразования'
                    ]
                })
            elif sales_growth > 20:
                recommendations.append({
                    'type': 'Тренды',
                    'priority': 'Позитивная',
                    'title': 'Отличный рост продаж!',
                    'text': f'Продажи выросли на {sales_growth:.1f}%! Продолжайте в том же направлении.',
                    'details': [
                        'Масштабируйте успешные стратегии',
                        'Инвестируйте в развитие',
                        'Рассмотрите расширение ассортимента',
                        'Поддерживайте качество сервиса',
                        'Планируйте дальнейший рост'
                    ],
                    'actions': [
                        'Увеличить закупки товаров',
                        'Расширить команду',
                        'Инвестировать в технологии',
                        'Планировать новые продукты'
                    ]
                })
        
        # Рекомендации по производству
        if 'production_status' in report and report['production_status']:
            prod = report['production_status']
            total_projects = prod['total_projects']
            active_projects = prod['active_projects']
            overdue_projects = prod['overdue_projects']
            total_cost = prod['total_development_cost']
            
            if overdue_projects > 0:
                recommendations.append({
                    'type': 'Производство',
                    'priority': 'Критическая',
                    'title': 'Критическая ситуация с проектами',
                    'text': f'У вас {overdue_projects} просроченных проектов из {total_projects} общих.',
                    'details': [
                        'Проанализируйте причины задержек',
                        'Пересмотрите временные рамки проектов',
                        'Оптимизируйте процессы планирования',
                        'Улучшите коммуникацию с поставщиками',
                        'Рассмотрите возможность аутсорсинга'
                    ],
                    'actions': [
                        'Немедленно связаться с поставщиками',
                        'Пересмотреть временные планы',
                        'Оптимизировать логистические процессы',
                        'Улучшить систему контроля проектов',
                        'Рассмотреть альтернативных поставщиков'
                    ]
                })
            
            if active_projects > 10:
                recommendations.append({
                    'type': 'Производство',
                    'priority': 'Средняя',
                    'title': 'Большое количество активных проектов',
                    'text': f'У вас {active_projects} активных проектов. Убедитесь в эффективном управлении.',
                    'details': [
                        'Оптимизируйте процессы управления проектами',
                        'Используйте системы планирования',
                        'Улучшите коммуникацию между командами',
                        'Рассмотрите приоритизацию проектов',
                        'Автоматизируйте рутинные процессы'
                    ],
                    'actions': [
                        'Внедрить систему управления проектами',
                        'Оптимизировать процессы планирования',
                        'Улучшить отчетность по проектам',
                        'Провести аудит эффективности'
                    ]
                })
            
            if total_cost > 500000:  # Если расходы на разработку превышают 500k
                recommendations.append({
                    'type': 'Инвестиции',
                    'priority': 'Средняя',
                    'title': 'Значительные инвестиции в разработку',
                    'text': f'Общие расходы на разработку составляют {total_cost:,.0f} ₽.',
                    'details': [
                        'Проанализируйте ROI от инвестиций в разработку',
                        'Оптимизируйте процессы разработки',
                        'Рассмотрите возможность совместной разработки',
                        'Оцените эффективность каждого проекта',
                        'Планируйте бюджет на следующие проекты'
                    ],
                    'actions': [
                        'Провести анализ ROI проектов',
                        'Оптимизировать расходы на разработку',
                        'Планировать бюджет на будущие проекты',
                        'Рассмотреть альтернативные подходы'
                    ]
                })
        
        # Кросс-приложенческие рекомендации
        if 'cross_app_insights' in report and report['cross_app_insights']:
            insights = report['cross_app_insights']
            
            if 'sales_vs_production' in insights:
                sales_prod = insights['sales_vs_production']
                current_revenue = sales_prod.get('current_month_revenue', 0)
                active_projects_count = sales_prod.get('active_projects_count', 0)
                development_investment = sales_prod.get('development_investment', 0)
                
                if active_projects_count > 0:
                    revenue_per_project = current_revenue / active_projects_count
                    if revenue_per_project < 100000:  # Если выручка на проект меньше 100k
                        recommendations.append({
                            'type': 'Стратегия',
                            'priority': 'Высокая',
                            'title': 'Низкая эффективность проектов',
                            'text': f'Выручка на активный проект составляет {revenue_per_project:,.0f} ₽.',
                            'details': [
                                'Проанализируйте эффективность каждого проекта',
                                'Оптимизируйте портфель проектов',
                                'Рассмотрите фокус на наиболее прибыльных направлениях',
                                'Улучшите процессы отбора проектов',
                                'Планируйте инвестиции более стратегически'
                            ],
                            'actions': [
                                'Провести анализ эффективности проектов',
                                'Оптимизировать портфель проектов',
                                'Сфокусироваться на высокоприбыльных направлениях',
                                'Улучшить процессы планирования'
                            ]
                        })
        
        report['recommendations'] = recommendations
    
    def generate_alerts(self, report):
        """Генерация развернутых предупреждений"""
        alerts = []
        
        # Предупреждения по продажам
        if 'sales_analysis' in report and report['sales_analysis']:
            sales_data = report['sales_analysis']
            current_week_data = sales_data['current_week_data']
            current_month_data = sales_data['current_month_data']
            
            if not current_week_data.empty:
                weekly_orders = current_week_data['Заказали, шт'].sum()
                weekly_sales = current_week_data['Выкупили, шт'].sum()
                weekly_revenue = current_week_data['Выкупили на сумму, ₽'].sum()
                
                if weekly_orders == 0:
                    alerts.append({
                        'type': 'Критическое',
                        'title': 'Отсутствие заказов',
                        'text': 'За текущую неделю не было ни одного заказа!',
                        'details': [
                            'Проверьте активность рекламных кампаний',
                            'Проанализируйте позиционирование товаров',
                            'Оцените конкурентную ситуацию',
                            'Проверьте технические проблемы с сайтом',
                            'Рассмотрите экстренные меры по стимулированию спроса'
                        ],
                        'actions': [
                            'Немедленно проверить рекламные кампании',
                            'Проанализировать конкурентов',
                            'Проверить техническую работоспособность',
                            'Запустить экстренные промо-акции',
                            'Связаться с командой маркетинга'
                        ]
                    })
                elif weekly_sales == 0:
                    alerts.append({
                        'type': 'Критическое',
                        'title': 'Отсутствие выкупов',
                        'text': f'За неделю было {weekly_orders} заказов, но 0 выкупов!',
                        'details': [
                            'Проверьте качество товаров',
                            'Проанализируйте отзывы клиентов',
                            'Оцените соответствие описанию и реальности',
                            'Проверьте процесс логистики',
                            'Рассмотрите проблемы с доставкой'
                        ],
                        'actions': [
                            'Немедленно проверить качество товаров',
                            'Проанализировать отзывы клиентов',
                            'Проверить соответствие описанию',
                            'Оптимизировать процесс доставки',
                            'Связаться с клиентами для выяснения причин'
                        ]
                    })
                elif weekly_sales < weekly_orders * 0.3:  # Если выкупов меньше 30% от заказов
                    alerts.append({
                        'type': 'Высокое',
                        'title': 'Критически низкая конверсия',
                        'text': f'Конверсия за неделю составляет всего {(weekly_sales/weekly_orders*100):.1f}%',
                        'details': [
                            'Проанализируйте причины отказа от покупки',
                            'Проверьте качество товаров и упаковки',
                            'Оцените процесс обработки заказов',
                            'Рассмотрите улучшение коммуникации с клиентами',
                            'Проанализируйте ценообразование'
                        ],
                        'actions': [
                            'Провести анализ причин отказов',
                            'Улучшить качество товаров',
                            'Оптимизировать процесс обработки',
                            'Улучшить коммуникацию с клиентами',
                            'Пересмотреть ценообразование'
                        ]
                    })
            
            # Анализ месячных данных
            if not current_month_data.empty:
                monthly_orders = current_month_data['Заказали, шт'].sum()
                monthly_sales = current_month_data['Выкупили, шт'].sum()
                monthly_revenue = current_month_data['Выкупили на сумму, ₽'].sum()
                
                # Сравнение с предыдущим месяцем
                if 'monthly_comparison' in sales_data:
                    revenue_change = sales_data['monthly_comparison']['revenue_change']
                    orders_change = sales_data['monthly_comparison']['orders_change']
                    
                    if revenue_change < -30:
                        alerts.append({
                            'type': 'Критическое',
                            'title': 'Критическое падение выручки',
                            'text': f'Выручка упала на {abs(revenue_change):.1f}% по сравнению с прошлым месяцем',
                            'details': [
                                'Проанализируйте причины резкого падения',
                                'Проверьте активность конкурентов',
                                'Оцените сезонные факторы',
                                'Проанализируйте изменения в алгоритмах маркетплейса',
                                'Рассмотрите экстренные меры по восстановлению'
                            ],
                            'actions': [
                                'Немедленно провести анализ причин',
                                'Запустить экстренные промо-акции',
                                'Оптимизировать ценообразование',
                                'Усилить рекламные активности',
                                'Проанализировать конкурентов'
                            ]
                        })
                    elif revenue_change < -15:
                        alerts.append({
                            'type': 'Высокое',
                            'title': 'Значительное снижение выручки',
                            'text': f'Выручка снизилась на {abs(revenue_change):.1f}%',
                            'details': [
                                'Проанализируйте тренды по категориям',
                                'Оцените эффективность маркетинга',
                                'Проверьте изменения в предпочтениях клиентов',
                                'Рассмотрите корректировку стратегии',
                                'Оптимизируйте ассортимент'
                            ],
                            'actions': [
                                'Пересмотреть маркетинговую стратегию',
                                'Оптимизировать ассортимент',
                                'Улучшить позиционирование',
                                'Провести анализ целевой аудитории',
                                'Корректировать ценообразование'
                            ]
                        })
        
        # Предупреждения по трендам
        if 'trends_analysis' in report and report['trends_analysis']:
            trends = report['trends_analysis']
            sales_growth = trends['sales_growth']
            orders_growth = trends['orders_growth']
            revenue_growth = trends['revenue_growth']
            
            if sales_growth < -20:
                alerts.append({
                    'type': 'Критическое',
                    'title': 'Критическое падение продаж',
                    'text': f'Продажи снизились на {abs(sales_growth):.1f}% за последние 30 дней',
                    'details': [
                        'Проанализируйте причины падения спроса',
                        'Проверьте активность конкурентов',
                        'Оцените сезонные факторы',
                        'Проанализируйте изменения в предпочтениях клиентов',
                        'Рассмотрите корректировку стратегии'
                    ],
                    'actions': [
                        'Немедленно провести анализ рынка',
                        'Оптимизировать товарное предложение',
                        'Усилить маркетинговые активности',
                        'Пересмотреть ценообразование',
                        'Запустить исследование клиентов'
                    ]
                })
            elif sales_growth < -10:
                alerts.append({
                    'type': 'Высокое',
                    'title': 'Снижение продаж',
                    'text': f'Продажи снизились на {abs(sales_growth):.1f}%',
                    'details': [
                        'Пересмотрите маркетинговую стратегию',
                        'Оптимизируйте рекламные кампании',
                        'Проанализируйте сезонность',
                        'Улучшите позиционирование товаров',
                        'Рассмотрите новые каналы продаж'
                    ],
                    'actions': [
                        'Оптимизировать рекламные кампании',
                        'Улучшить контент-маркетинг',
                        'Проанализировать конкурентов',
                        'Обновить стратегию ценообразования',
                        'Рассмотреть новые каналы продаж'
                    ]
                })
        
        # Предупреждения по производству
        if 'production_status' in report and report['production_status']:
            prod = report['production_status']
            total_projects = prod['total_projects']
            active_projects = prod['active_projects']
            overdue_projects = prod['overdue_projects']
            total_cost = prod['total_development_cost']
            
            if overdue_projects > 2:
                alerts.append({
                    'type': 'Критическое',
                    'title': 'Критическая ситуация с проектами',
                    'text': f'У вас {overdue_projects} просроченных проектов из {total_projects} общих',
                    'details': [
                        'Проанализируйте причины задержек',
                        'Пересмотрите временные рамки проектов',
                        'Оптимизируйте процессы планирования',
                        'Улучшите коммуникацию с поставщиками',
                        'Рассмотрите возможность аутсорсинга'
                    ],
                    'actions': [
                        'Немедленно связаться с поставщиками',
                        'Пересмотреть временные планы',
                        'Оптимизировать логистические процессы',
                        'Улучшить систему контроля проектов',
                        'Рассмотреть альтернативных поставщиков'
                    ]
                })
            elif overdue_projects > 0:
                alerts.append({
                    'type': 'Высокое',
                    'title': 'Просроченные проекты',
                    'text': f'{overdue_projects} проект(ов) просрочен(ы)',
                    'details': [
                        'Проанализируйте причины задержек',
                        'Пересмотрите временные рамки',
                        'Улучшите процессы планирования',
                        'Оптимизируйте коммуникацию',
                        'Рассмотрите корректировку планов'
                    ],
                    'actions': [
                        'Связаться с поставщиками',
                        'Пересмотреть планы',
                        'Оптимизировать процессы',
                        'Улучшить контроль',
                        'Рассмотреть альтернативы'
                    ]
                })
            
            if active_projects > 15:
                alerts.append({
                    'type': 'Среднее',
                    'title': 'Большое количество активных проектов',
                    'text': f'У вас {active_projects} активных проектов. Убедитесь в эффективном управлении',
                    'details': [
                        'Оптимизируйте процессы управления',
                        'Используйте системы планирования',
                        'Улучшите коммуникацию между командами',
                        'Рассмотрите приоритизацию проектов',
                        'Автоматизируйте рутинные процессы'
                    ],
                    'actions': [
                        'Внедрить систему управления проектами',
                        'Оптимизировать процессы планирования',
                        'Улучшить отчетность',
                        'Провести аудит эффективности',
                        'Автоматизировать рутинные задачи'
                    ]
                })
            
            if total_cost > 1000000:  # Если расходы превышают 1M
                alerts.append({
                    'type': 'Среднее',
                    'title': 'Высокие инвестиции в разработку',
                    'text': f'Общие расходы на разработку составляют {total_cost:,.0f} ₽',
                    'details': [
                        'Проанализируйте ROI от инвестиций',
                        'Оптимизируйте процессы разработки',
                        'Рассмотрите возможность совместной разработки',
                        'Оцените эффективность каждого проекта',
                        'Планируйте бюджет на следующие проекты'
                    ],
                    'actions': [
                        'Провести анализ ROI проектов',
                        'Оптимизировать расходы',
                        'Планировать бюджет',
                        'Рассмотреть альтернативные подходы',
                        'Улучшить процессы разработки'
                    ]
                })
        
        # Кросс-приложенческие предупреждения
        if 'cross_app_insights' in report and report['cross_app_insights']:
            insights = report['cross_app_insights']
            
            if 'sales_vs_production' in insights:
                sales_prod = insights['sales_vs_production']
                current_revenue = sales_prod.get('current_month_revenue', 0)
                active_projects_count = sales_prod.get('active_projects_count', 0)
                development_investment = sales_prod.get('development_investment', 0)
                
                if active_projects_count > 0:
                    revenue_per_project = current_revenue / active_projects_count
                    if revenue_per_project < 50000:  # Если выручка на проект меньше 50k
                        alerts.append({
                            'type': 'Высокое',
                            'title': 'Низкая эффективность проектов',
                            'text': f'Выручка на активный проект составляет всего {revenue_per_project:,.0f} ₽',
                            'details': [
                                'Проанализируйте эффективность каждого проекта',
                                'Оптимизируйте портфель проектов',
                                'Рассмотрите фокус на наиболее прибыльных направлениях',
                                'Улучшите процессы отбора проектов',
                                'Планируйте инвестиции более стратегически'
                            ],
                            'actions': [
                                'Провести анализ эффективности проектов',
                                'Оптимизировать портфель проектов',
                                'Сфокусироваться на высокоприбыльных направлениях',
                                'Улучшить процессы планирования',
                                'Пересмотреть стратегию инвестиций'
                            ]
                        })
        
        # Предупреждения по качеству данных
        if INTEGRATION_AVAILABLE:
            integration = DataIntegration()
            quality = integration.validate_data_quality()
            
            if quality['overall_score'] < 60:
                alerts.append({
                    'type': 'Критическое',
                    'title': 'Критическое качество данных',
                    'text': f'Общее качество данных составляет {quality["overall_score"]:.1f}/100',
                    'details': [
                        'Проверьте целостность данных',
                        'Обновите устаревшую информацию',
                        'Исправьте ошибки в данных',
                        'Улучшите процессы сбора данных',
                        'Автоматизируйте проверку качества'
                    ],
                    'actions': [
                        'Немедленно проверить данные',
                        'Исправить найденные ошибки',
                        'Обновить устаревшую информацию',
                        'Улучшить процессы сбора данных',
                        'Внедрить автоматическую проверку'
                    ]
                })
            elif quality['overall_score'] < 80:
                alerts.append({
                    'type': 'Среднее',
                    'title': 'Качество данных требует улучшения',
                    'text': f'Качество данных составляет {quality["overall_score"]:.1f}/100',
                    'details': [
                        'Проанализируйте проблемы с данными',
                        'Обновите устаревшую информацию',
                        'Улучшите процессы сбора данных',
                        'Рассмотрите автоматизацию',
                        'Проведите аудит данных'
                    ],
                    'actions': [
                        'Проанализировать проблемы',
                        'Обновить данные',
                        'Улучшить процессы',
                        'Рассмотреть автоматизацию',
                        'Провести аудит'
                    ]
                })
        
        report['alerts'] = alerts
    
    def format_report_for_display(self, report):
        """Форматирование отчета для отображения"""
        formatted_report = f"""
# 📊 Ежедневный отчет ИИ-аналитика

**Дата:** {report['date']}  
**Аналитик:** {report['analyst']} {self.avatar}  
**Должность:** {report['position']}

---

## 📈 Краткая сводка

"""
        
        # Сводка по продажам
        if report['sales_analysis']:
            sales = report['sales_analysis']
            formatted_report += f"""
### 💰 Продажи
- **Всего заказов:** {sales['total_orders']:,}
- **Всего выкупов:** {sales['total_sales']:,}
- **Выручка:** {sales['total_revenue']:,.0f} ₽
- **Конверсия:** {sales['conversion_rate']:.1f}%
"""
            
            if 'monthly_comparison' in sales:
                comp = sales['monthly_comparison']
                formatted_report += f"""
- **Изменение заказов:** {comp['orders_change']:+.1f}%
- **Изменение выкупов:** {comp['sales_change']:+.1f}%
- **Изменение выручки:** {comp['revenue_change']:+.1f}%
"""
        
        # Сводка по трендам
        if report['trends_analysis']:
            trends = report['trends_analysis']
            formatted_report += f"""
### 📊 Тренды (последние 30 дней)
- **Рост заказов:** {trends['orders_growth']:+.1f}%
- **Рост продаж:** {trends['sales_growth']:+.1f}%
- **Рост выручки:** {trends['revenue_growth']:+.1f}%
"""
        
        # Сводка по прогнозам
        if report['forecast']:
            forecast = report['forecast']
            formatted_report += f"""
### 🔮 Прогноз
**На неделю:**
- Заказы: {forecast['weekly_forecast']['orders']:,.0f}
- Выкупы: {forecast['weekly_forecast']['sales']:,.0f}
- Выручка: {forecast['weekly_forecast']['revenue']:,.0f} ₽

**На месяц:**
- Заказы: {forecast['monthly_forecast']['orders']:,.0f}
- Выкупы: {forecast['monthly_forecast']['sales']:,.0f}
- Выручка: {forecast['monthly_forecast']['revenue']:,.0f} ₽

*Уровень уверенности: {forecast['confidence']}*
"""
        
        # Сводка по производству
        if report['production_status']:
            prod = report['production_status']
            formatted_report += f"""
### 🏭 Производство
- **Всего проектов:** {prod['total_projects']}
- **Активных проектов:** {prod['active_projects']}
- **Просроченных проектов:** {prod['overdue_projects']}
- **Общие расходы на разработку:** {prod['total_development_cost']:,.0f} ₽
"""
        
        # Кросс-приложенческие инсайты
        if 'cross_app_insights' in report and report['cross_app_insights']:
            insights = report['cross_app_insights']
            formatted_report += f"""
### 🔗 Интеграционный анализ
"""
            
            if 'sales_vs_production' in insights and insights['sales_vs_production']:
                sales_prod = insights['sales_vs_production']
                formatted_report += f"""
**Продажи vs Производство:**
- Продажи за месяц: {sales_prod.get('current_month_sales', 0):,}
- Выручка за месяц: {sales_prod.get('current_month_revenue', 0):,.0f} ₽
- Активных проектов: {sales_prod.get('active_projects_count', 0)}
- Инвестиции в разработку: {sales_prod.get('development_investment', 0):,.0f} ₽
"""
            
            if 'investment_analysis' in insights and insights['investment_analysis']:
                inv_analysis = insights['investment_analysis']
                formatted_report += f"""
**Анализ инвестиций:**
- Общие расходы на разработку: {inv_analysis.get('total_development_cost', 0):,.0f} ₽
- Средняя стоимость проекта: {inv_analysis.get('average_cost_per_project', 0):,.0f} ₽
- Проектов с затратами: {inv_analysis.get('projects_with_costs', 0)}
"""
        
        return formatted_report

# Инициализация ИИ-аналитика
analyst = AIAnalyst()

# Интерфейс приложения
st.markdown("""
<div class="main-header">
    <h1>{analyst.avatar} ИИ-аналитик данных</h1>
    <h3>{analyst.name} - {analyst.position}</h3>
    <p>Интеллектуальный анализ продаж, трендов и сезонности</p>
</div>
""".format(analyst=analyst), unsafe_allow_html=True)

# Боковая панель с настройками
with st.sidebar:
    st.header("⚙️ Настройки анализа")
    
    # Выбор источников данных
    st.subheader("📊 Источники данных")
    use_wb_analysis = st.checkbox("Анализ WB (45.xlsx)", value=True)
    use_production_calendar = st.checkbox("Календарь производства", value=True)
    use_seasonal_calculator = st.checkbox("Сезонный калькулятор", value=False)
    use_investments = st.checkbox("Данные инвестиций", value=False)
    
    st.divider()
    
    # Настройки периода анализа
    st.subheader("📅 Период анализа")
    
    # Выбор типа периода
    period_type = st.selectbox(
        "Выберите тип периода:",
        ["Последние N дней", "Конкретный период"],
        key="period_type"
    )
    
    if period_type == "Последние N дней":
        period_days = st.slider(
            "Количество дней:",
            min_value=7,
            max_value=365,
            value=30,
            step=1,
            key="period_days"
        )
        start_date = None
        end_date = None
    else:
        # Календарь для выбора конкретного периода
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input(
                "Дата начала:",
                value=datetime.now().date() - timedelta(days=30),
                key="start_date"
            )
        with col2:
            end_date = st.date_input(
                "Дата окончания:",
                value=datetime.now().date(),
                key="end_date"
            )
        
        if start_date and end_date:
            period_days = (end_date - start_date).days + 1
        else:
            period_days = 30
    
    # Информация о выбранном периоде
    if start_date and end_date:
        st.info(f"📊 Анализ за период: {start_date.strftime('%d.%m.%Y')} - {end_date.strftime('%d.%m.%Y')} ({period_days} дней)")
    else:
        st.info(f"📊 Анализ за последние {period_days} дней")
    
    st.divider()
    
    # Настройки отчета
    st.subheader("📋 Настройки отчета")
    include_recommendations = st.checkbox("Включить рекомендации", value=True)
    include_forecasts = st.checkbox("Включить прогнозы", value=True)
    include_alerts = st.checkbox("Включить предупреждения", value=True)
    
    # Фильтры для рекомендаций и предупреждений
    if 'daily_report' in st.session_state:
        report = st.session_state['daily_report']
        
        if report.get('recommendations') or report.get('alerts'):
            st.subheader("🔍 Фильтры")
            
            # Фильтр по приоритету рекомендаций
            if report.get('recommendations'):
                st.markdown("**Приоритет рекомендаций:**")
                col1, col2 = st.columns(2)
                with col1:
                    show_critical_recs = st.checkbox("Критическая", value=True, key="rec_critical")
                    show_high_recs = st.checkbox("Высокая", value=True, key="rec_high")
                    show_medium_recs = st.checkbox("Средняя", value=True, key="rec_medium")
                with col2:
                    show_low_recs = st.checkbox("Низкая", value=True, key="rec_low")
                    show_positive_recs = st.checkbox("Позитивная", value=True, key="rec_positive")
            
            # Фильтр по типу предупреждений
            if report.get('alerts'):
                st.markdown("**Тип предупреждений:**")
                col1, col2 = st.columns(2)
                with col1:
                    show_critical_alerts = st.checkbox("Критическое", value=True, key="alert_critical")
                    show_high_alerts = st.checkbox("Высокое", value=True, key="alert_high")
                with col2:
                    show_medium_alerts = st.checkbox("Среднее", value=True, key="alert_medium")
    
    st.divider()
    
    # Информация об аналитике
    st.subheader("👤 Об аналитике")
    st.info(f"""
    **Имя:** {analyst.name}  
    **Должность:** {analyst.position}  
    **Специализация:** Анализ продаж, прогнозирование, оптимизация процессов  
    **Опыт:** 5+ лет в аналитике e-commerce
    """)

# Основная область
col1, col2 = st.columns([2, 1])

with col1:
    st.header("📊 Ежедневный анализ данных")
    
    # Кнопка генерации отчета
    if st.button("🚀 Сгенерировать ежедневный отчет", type="primary"):
        with st.spinner("Анализирую данные..."):
            # Загрузка данных
            data_sources = analyst.load_data_sources()
            
            # Фильтрация источников данных
            filtered_sources = {}
            if use_wb_analysis and 'wb_analysis' in data_sources:
                filtered_sources['wb_analysis'] = data_sources['wb_analysis']
            if use_production_calendar and 'production_calendar' in data_sources:
                filtered_sources['production_calendar'] = data_sources['production_calendar']
            if use_seasonal_calculator and 'seasonal_calculator' in data_sources:
                filtered_sources['seasonal_calculator'] = data_sources['seasonal_calculator']
            if use_investments and 'investments' in data_sources:
                filtered_sources['investments'] = data_sources['investments']
            
            if filtered_sources:
                # Генерация отчета с учетом выбранного периода
                report = analyst.generate_daily_report(filtered_sources, period_days, start_date, end_date)
                
                # Сохранение отчета в session state
                st.session_state['daily_report'] = report
                
                st.success("✅ Отчет успешно сгенерирован!")
                st.rerun()
            else:
                st.error("❌ Не удалось загрузить данные. Проверьте настройки источников данных.")
    
    # Отображение отчета
    if 'daily_report' in st.session_state:
        report = st.session_state['daily_report']
        
        # Форматированный отчет
        formatted_report = analyst.format_report_for_display(report)
        st.markdown(formatted_report)
        
        # Предупреждения
        if include_alerts and report['alerts']:
            st.subheader("🚨 Предупреждения")
            
            # Группировка по типу
            alerts_by_type = {}
            for alert in report['alerts']:
                alert_type = alert['type']
                if alert_type not in alerts_by_type:
                    alerts_by_type[alert_type] = []
                alerts_by_type[alert_type].append(alert)
            
            # Отображение по типу (критическое -> высокое -> среднее)
            alert_type_order = ['Критическое', 'Высокое', 'Среднее']
            
            for alert_type in alert_type_order:
                if alert_type in alerts_by_type:
                    # Проверка фильтра
                    should_show = True
                    if alert_type == 'Критическое' and 'show_critical_alerts' in locals() and not show_critical_alerts:
                        should_show = False
                    elif alert_type == 'Высокое' and 'show_high_alerts' in locals() and not show_high_alerts:
                        should_show = False
                    elif alert_type == 'Среднее' and 'show_medium_alerts' in locals() and not show_medium_alerts:
                        should_show = False
                    
                    if should_show:
                        alert_color = {
                            'Критическое': '🔴',
                            'Высокое': '🟠',
                            'Среднее': '🟡'
                        }.get(alert_type, '⚪')
                        
                        st.markdown(f"### {alert_color} {alert_type} ({len(alerts_by_type[alert_type])})")
                        
                        for alert in alerts_by_type[alert_type]:
                            with st.expander(f"**{alert['title']}** - {alert['text']}", expanded=(alert_type == 'Критическое')):
                                col1, col2 = st.columns([1, 1])
                                
                                with col1:
                                    st.markdown("**📋 Детали:**")
                                    for detail in alert.get('details', []):
                                        st.write(f"• {detail}")
                                
                                with col2:
                                    st.markdown("**⚡ Действия:**")
                                    for action in alert.get('actions', []):
                                        st.write(f"• {action}")
                                
                                # Цветовое выделение в зависимости от типа
                                if alert_type == 'Критическое':
                                    st.error(f"**Критическое предупреждение** требует немедленного внимания!")
                                elif alert_type == 'Высокое':
                                    st.warning(f"**Высокий приоритет** - рекомендуется принять меры в ближайшее время.")
                                else:
                                    st.info(f"**Средний приоритет** - рассмотрите возможность улучшения.")
        
        # Рекомендации
        if include_recommendations and report['recommendations']:
            st.subheader("💡 Рекомендации")
            
            # Группировка по приоритету
            recommendations_by_priority = {}
            for rec in report['recommendations']:
                priority = rec['priority']
                if priority not in recommendations_by_priority:
                    recommendations_by_priority[priority] = []
                recommendations_by_priority[priority].append(rec)
            
            # Отображение по приоритету (критическая -> высокая -> средняя -> позитивная)
            priority_order = ['Критическая', 'Высокая', 'Средняя', 'Низкая', 'Позитивная']
            
            for priority in priority_order:
                if priority in recommendations_by_priority:
                    # Проверка фильтра
                    should_show = True
                    if priority == 'Критическая' and 'show_critical_recs' in locals() and not show_critical_recs:
                        should_show = False
                    elif priority == 'Высокая' and 'show_high_recs' in locals() and not show_high_recs:
                        should_show = False
                    elif priority == 'Средняя' and 'show_medium_recs' in locals() and not show_medium_recs:
                        should_show = False
                    elif priority == 'Низкая' and 'show_low_recs' in locals() and not show_low_recs:
                        should_show = False
                    elif priority == 'Позитивная' and 'show_positive_recs' in locals() and not show_positive_recs:
                        should_show = False
                    
                    if should_show:
                        priority_color = {
                            'Критическая': '🔴',
                            'Высокая': '🟠', 
                            'Средняя': '🟡',
                            'Низкая': '🟢',
                            'Позитивная': '✅'
                        }.get(priority, '⚪')
                        
                        st.markdown(f"### {priority_color} {priority} приоритет ({len(recommendations_by_priority[priority])})")
                        
                        for i, rec in enumerate(recommendations_by_priority[priority], 1):
                            with st.expander(f"**{rec['title']}** - {rec['text']}", expanded=(priority == 'Критическая')):
                                col1, col2 = st.columns([1, 1])
                                
                                with col1:
                                    st.markdown("**📋 Детали:**")
                                    for detail in rec.get('details', []):
                                        st.write(f"• {detail}")
                                
                                with col2:
                                    st.markdown("**⚡ Действия:**")
                                    for action in rec.get('actions', []):
                                        st.write(f"• {action}")
                                
                                st.info(f"**Тип:** {rec['type']} | **Приоритет:** {rec['priority']}")
        
        # Анализ графиков и паттернов
        if 'trends_analysis' in report and report['trends_analysis'].get('chart_analysis'):
            chart_analysis = report['trends_analysis']['chart_analysis']
            
            st.markdown("---")
            st.subheader("📊 Анализ графиков")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                if chart_analysis['is_volatile']:
                    st.metric("📈 Волатильность", "Высокая", delta="Нестабильно", delta_color="normal")
                elif chart_analysis['is_stable']:
                    st.metric("📈 Волатильность", "Низкая", delta="Стабильно", delta_color="inverse")
                else:
                    st.metric("📈 Волатильность", "Средняя", delta="Обычно")
            
            with col2:
                st.metric("📊 CV выручки", f"{chart_analysis['revenue_cv']:.1f}%")
            
            with col3:
                st.metric("📈 Пики", chart_analysis['peaks_count'])
            
            with col4:
                st.metric("📉 Спады", chart_analysis['lows_count'])
            
            # Информация о лучших/худших днях
            col1, col2 = st.columns(2)
            with col1:
                st.info(f"**Лучший день недели:** {chart_analysis['best_weekday']}")
            with col2:
                st.info(f"**Худший день недели:** {chart_analysis['worst_weekday']}")
        
        # Детальная аналитика
        st.subheader("📈 Детальная аналитика")
        
        # Графики продаж
        if 'wb_analysis' in report and report['wb_analysis'] and 'trends_analysis' in report:
            trends = report['trends_analysis']
            if trends and 'daily_data' in trends:
                daily_data = trends['daily_data']
                
                # График трендов
                fig = go.Figure()
                
                fig.add_trace(go.Scatter(
                    x=daily_data['Дата'],
                    y=daily_data['Заказали, шт'],
                    name='Заказы',
                    line=dict(color='blue', width=2)
                ))
                
                fig.add_trace(go.Scatter(
                    x=daily_data['Дата'],
                    y=daily_data['Выкупили, шт'],
                    name='Выкупы',
                    line=dict(color='green', width=2)
                ))
                
                fig.add_trace(go.Scatter(
                    x=daily_data['Дата'],
                    y=daily_data['orders_ma_7'],
                    name='Заказы (7-дн. среднее)',
                    line=dict(color='lightblue', width=1, dash='dash')
                ))
                
                fig.add_trace(go.Scatter(
                    x=daily_data['Дата'],
                    y=daily_data['sales_ma_7'],
                    name='Выкупы (7-дн. среднее)',
                    line=dict(color='lightgreen', width=1, dash='dash')
                ))
                
                fig.update_layout(
                    title='Динамика заказов и выкупов',
                    xaxis_title='Дата',
                    yaxis_title='Количество',
                    hovermode='x unified',
                    height=400
                )
                
                st.plotly_chart(fig, use_container_width=True)
        
        # График выручки
        if 'wb_analysis' in report and report['wb_analysis'] and 'trends_analysis' in report:
            trends = report['trends_analysis']
            if trends and 'daily_data' in trends:
                daily_data = trends['daily_data']
                
                fig_revenue = go.Figure()
                
                fig_revenue.add_trace(go.Scatter(
                    x=daily_data['Дата'],
                    y=daily_data['Выкупили на сумму, ₽'],
                    name='Выручка',
                    line=dict(color='purple', width=2),
                    fill='tonexty'
                ))
                
                fig_revenue.add_trace(go.Scatter(
                    x=daily_data['Дата'],
                    y=daily_data['revenue_ma_7'],
                    name='Выручка (7-дн. среднее)',
                    line=dict(color='violet', width=1, dash='dash')
                ))
                
                fig_revenue.update_layout(
                    title='Динамика выручки',
                    xaxis_title='Дата',
                    yaxis_title='Выручка, ₽',
                    hovermode='x unified',
                    height=300
                )
                
                st.plotly_chart(fig_revenue, use_container_width=True)

with col2:
    st.header("📋 Быстрые метрики")
    
    if 'daily_report' in st.session_state:
        report = st.session_state['daily_report']
        
        # Ключевые показатели
        if 'sales_analysis' in report and report['sales_analysis']:
            sales = report['sales_analysis']
            
            st.metric("📦 Заказы", f"{sales['total_orders']:,}")
            st.metric("💰 Выкупы", f"{sales['total_sales']:,}")
            st.metric("💵 Выручка", f"{sales['total_revenue']:,.0f} ₽")
            st.metric("📈 Конверсия", f"{sales['conversion_rate']:.1f}%")
        
        # Тренды
        if 'trends_analysis' in report and report['trends_analysis']:
            trends = report['trends_analysis']
            
            st.metric("📊 Рост заказов", f"{trends['orders_growth']:+.1f}%")
            st.metric("📈 Рост продаж", f"{trends['sales_growth']:+.1f}%")
            st.metric("💰 Рост выручки", f"{trends['revenue_growth']:+.1f}%")
        
        # Производство
        if 'production_status' in report and report['production_status']:
            prod = report['production_status']
            
            st.metric("🏭 Активных проектов", prod['active_projects'])
            st.metric("⚠️ Просроченных", prod['overdue_projects'])
            st.metric("💸 Расходы на разработку", f"{prod['total_development_cost']:,.0f} ₽")
        
        # Кросс-приложенческие инсайты
        if 'cross_app_insights' in report and report['cross_app_insights']:
            insights = report['cross_app_insights']
            
            if 'sales_vs_production' in insights and insights['sales_vs_production']:
                sales_prod = insights['sales_vs_production']
                if sales_prod.get('active_projects_count', 0) > 0:
                    revenue_per_project = sales_prod.get('current_month_revenue', 0) / sales_prod.get('active_projects_count', 1)
                    st.metric("💰 Выручка/проект", f"{revenue_per_project:,.0f} ₽")
        
        # Анализ сезонности
        if 'daily_report' in st.session_state:
            report = st.session_state['daily_report']
            
            if 'sales_analysis' in report and report['sales_analysis'].get('seasonality_analysis'):
                seasonality = report['sales_analysis']['seasonality_analysis']
                
                st.markdown("---")
                st.subheader("🌍 Анализ сезонности")
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    season_emoji = {"Зима": "❄️", "Весна": "🌸", "Лето": "☀️", "Осень": "🍂"}.get(seasonality['current_season'], "📅")
                    st.metric("🌍 Текущий сезон", f"{season_emoji} {seasonality['current_season']}")
                
                with col2:
                    multiplier = seasonality['season_multiplier']
                    if multiplier > 1.1:
                        st.metric("📈 Сезонный фактор", f"{multiplier:.1f}x", delta="Пик сезона", delta_color="inverse")
                    elif multiplier < 1.0:
                        st.metric("📉 Сезонный фактор", f"{multiplier:.1f}x", delta="Спад сезона", delta_color="normal")
                    else:
                        st.metric("📊 Сезонный фактор", f"{multiplier:.1f}x", delta="Обычный сезон")
                
                with col3:
                    if seasonality['is_seasonal_peak']:
                        st.metric("🎯 Статус", "Пик сезона", delta="Высокий спрос")
                    elif seasonality['is_seasonal_low']:
                        st.metric("🎯 Статус", "Спад сезона", delta="Низкий спрос")
                    else:
                        st.metric("🎯 Статус", "Обычный сезон", delta="Стандартный спрос")
                
                with col4:
                    trend = seasonality['revenue_trend']
                    if trend > 0:
                        st.metric("📊 Тренд выручки", f"{trend:+.1f}%", delta="Рост")
                    else:
                        st.metric("📊 Тренд выручки", f"{trend:+.1f}%", delta="Спад", delta_color="normal")
        
        # Статистика рекомендаций и предупреждений
        if 'daily_report' in st.session_state:
            report = st.session_state['daily_report']
            
            if report.get('recommendations') or report.get('alerts'):
                st.markdown("---")
                st.subheader("📊 Статистика анализа")
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    total_recommendations = len(report.get('recommendations', []))
                    critical_recs = len([r for r in report.get('recommendations', []) if r.get('priority') == 'Критическая'])
                    st.metric("💡 Всего рекомендаций", total_recommendations, delta=f"{critical_recs} критических")
                
                with col2:
                    total_alerts = len(report.get('alerts', []))
                    critical_alerts = len([a for a in report.get('alerts', []) if a.get('type') == 'Критическое'])
                    st.metric("⚠️ Всего предупреждений", total_alerts, delta=f"{critical_alerts} критических")
                
                with col3:
                    if report.get('recommendations'):
                        high_priority = len([r for r in report['recommendations'] if r.get('priority') in ['Критическая', 'Высокая']])
                        st.metric("🔴 Высокий приоритет", high_priority)
                
                with col4:
                    if report.get('alerts'):
                        high_alerts = len([a for a in report['alerts'] if a.get('type') in ['Критическое', 'Высокое']])
                        st.metric("🚨 Критичные проблемы", high_alerts)
    
    else:
        st.info("Нажмите 'Сгенерировать отчет' для просмотра метрик")
    
    st.divider()
    
    # Экспорт отчета
    st.subheader("📤 Экспорт отчета")
    
    if 'daily_report' in st.session_state:
        report = st.session_state['daily_report']
        
        # JSON экспорт
        report_json = json.dumps(report, ensure_ascii=False, indent=2, default=str)
        st.download_button(
            label="📄 Скачать JSON",
            data=report_json,
            file_name=f"daily_report_{datetime.now().strftime('%Y%m%d')}.json",
            mime="application/json"
        )
        
        # CSV экспорт (если есть данные WB)
        if 'wb_analysis' in report and report['wb_analysis'] and 'trends_analysis' in report:
            trends = report['trends_analysis']
            if trends and 'daily_data' in trends:
                daily_data = trends['daily_data']
                csv_data = daily_data.to_csv(index=False, encoding='utf-8-sig')
                st.download_button(
                    label="📊 Скачать CSV",
                    data=csv_data,
                    file_name=f"daily_trends_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv"
                )
    else:
        st.info("Сначала сгенерируйте отчет")

# Футер
st.markdown("---")
st.markdown(f"""
<div style='text-align: center; color: #666;'>
    <p>🤖 ИИ-аналитик {analyst.name} | {analyst.position}</p>
    <p>Отчет сгенерирован: {datetime.now().strftime('%d.%m.%Y %H:%M')}</p>
</div>
""", unsafe_allow_html=True)
