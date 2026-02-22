# -*- coding: utf-8 -*-
"""
Модуль для кеширования файлов
"""
import os
import json
import pandas as pd


def save_file_cache(file_data, filename):
    """Сохраняет файл в кеш"""
    try:
        cache_dir = "file_cache"
        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir)
        
        # Сохраняем файл
        cache_path = os.path.join(cache_dir, filename)
        with open(cache_path, "wb") as f:
            f.write(file_data)
        
        # Сохраняем метаданные
        meta_data = {
            "filename": filename,
            "timestamp": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"),
            "size": len(file_data)
        }
        
        with open("file_cache_meta.json", "w", encoding="utf-8") as f:
            json.dump(meta_data, f, ensure_ascii=False, indent=2)
        
        return True
    except Exception as e:
        return False


def load_file_cache():
    """Загружает файл из кеша"""
    try:
        # Проверяем наличие метаданных
        if not os.path.exists("file_cache_meta.json"):
            return None, None
        
        # Загружаем метаданные
        with open("file_cache_meta.json", "r", encoding="utf-8") as f:
            meta_data = json.load(f)
        
        filename = meta_data.get("filename")
        cache_path = os.path.join("file_cache", filename)
        
        # Проверяем наличие файла
        if not os.path.exists(cache_path):
            return None, None
        
        # Загружаем файл
        with open(cache_path, "rb") as f:
            file_data = f.read()
        
        return file_data, meta_data
    except Exception as e:
        return None, None


def get_file_cache_info():
    """Получает информацию о кешированном файле"""
    try:
        if os.path.exists("file_cache_meta.json"):
            with open("file_cache_meta.json", "r", encoding="utf-8") as f:
                meta_data = json.load(f)
            return meta_data
        return None
    except:
        return None


def get_all_cached_files():
    """Получает список всех кешированных файлов"""
    try:
        cache_dir = "file_cache"
        if not os.path.exists(cache_dir):
            return []
        
        cached_files = []
        for filename in os.listdir(cache_dir):
            if filename.endswith(('.xlsx', '.xls', '.csv')):
                file_path = os.path.join(cache_dir, filename)
                file_size = os.path.getsize(file_path)
                file_time = os.path.getmtime(file_path)
                
                cached_files.append({
                    "filename": filename,
                    "size": file_size,
                    "timestamp": pd.Timestamp.fromtimestamp(file_time).strftime("%Y-%m-%d %H:%M:%S"),
                    "path": file_path
                })
        
        # Сортируем по времени изменения (новые сначала)
        cached_files.sort(key=lambda x: x["timestamp"], reverse=True)
        return cached_files
    except Exception as e:
        return []


def save_file_to_cache(file_data, filename):
    """Сохраняет файл в кеш с улучшенной системой"""
    try:
        cache_dir = "file_cache"
        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir)
        
        # Сохраняем файл
        cache_path = os.path.join(cache_dir, filename)
        with open(cache_path, "wb") as f:
            f.write(file_data)
        
        # Обновляем метаданные
        meta_data = {
            "filename": filename,
            "timestamp": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"),
            "size": len(file_data),
            "last_used": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        with open("file_cache_meta.json", "w", encoding="utf-8") as f:
            json.dump(meta_data, f, ensure_ascii=False, indent=2)
        
        return True
    except Exception as e:
        return False



























