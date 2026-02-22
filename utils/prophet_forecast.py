# -*- coding: utf-8 -*-
"""
Модуль для прогнозирования с помощью Prophet
"""
import pandas as pd
from datetime import datetime, timedelta

# Импорт Prophet с обработкой ошибок
try:
    from prophet import Prophet
    from prophet.plot import plot_plotly, plot_components_plotly
    PROPHET_AVAILABLE = True
except ImportError:
    PROPHET_AVAILABLE = False


def prepare_data_for_prophet(df, metric_column, date_column=None):
    """Подготавливает данные для Prophet"""
    if not PROPHET_AVAILABLE:
        return None
    
    # Если нет колонки с датами, создаем искусственную временную последовательность
    if date_column is None or date_column not in df.columns:
        # Создаем даты на основе индекса
        start_date = datetime.now() - timedelta(days=len(df)-1)
        dates = [start_date + timedelta(days=i) for i in range(len(df))]
        df_prophet = pd.DataFrame({
            'ds': dates,
            'y': df[metric_column].values
        })
    else:
        # Используем существующую колонку с датами
        df_prophet = pd.DataFrame({
            'ds': pd.to_datetime(df[date_column]),
            'y': df[metric_column].values
        })
    
    # Удаляем строки с NaN значениями
    df_prophet = df_prophet.dropna()
    
    return df_prophet


def create_prophet_forecast(df_prophet, periods=30, seasonality_mode='additive'):
    """Создает прогноз с помощью Prophet"""
    if not PROPHET_AVAILABLE or df_prophet is None or len(df_prophet) < 2:
        return None, None, None
    
    try:
        # Создаем модель Prophet
        model = Prophet(
            seasonality_mode=seasonality_mode,
            daily_seasonality=True,
            weekly_seasonality=True,
            yearly_seasonality=True,
            changepoint_prior_scale=0.05
        )
        
        # Обучаем модель
        model.fit(df_prophet)
        
        # Создаем будущие даты
        future = model.make_future_dataframe(periods=periods)
        
        # Делаем прогноз
        forecast = model.predict(future)
        
        return model, forecast, future
        
    except Exception as e:
        return None, None, None


def plot_prophet_forecast(model, forecast, title="Прогноз Prophet"):
    """Создает график прогноза с помощью plotly"""
    if not PROPHET_AVAILABLE or model is None or forecast is None:
        return None
    
    try:
        # Создаем график с помощью Prophet
        fig = plot_plotly(model, forecast)
        
        # Обновляем заголовок
        fig.update_layout(
            title=title,
            xaxis_title="Дата",
            yaxis_title="Значение",
            width=1000,
            height=600
        )
        
        return fig
        
    except Exception as e:
        return None


def plot_prophet_components(model, forecast, title="Компоненты прогноза"):
    """Создает график компонентов прогноза"""
    if not PROPHET_AVAILABLE or model is None or forecast is None:
        return None
    
    try:
        # Создаем график компонентов
        fig = plot_components_plotly(model, forecast)
        
        # Обновляем заголовок
        fig.update_layout(title=title)
        
        return fig
        
    except Exception as e:
        return None



























