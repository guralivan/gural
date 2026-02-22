#!/usr/bin/env python3
"""Скрипт для принудительной очистки удаленных параметров из всех файлов"""
import json
import glob
import os

def clean_deleted_params_from_all_files(deleted_params_list):
    """Удаляет удаленные параметры из всех файлов параметров"""
    if not deleted_params_list:
        print("Нет удаленных параметров для очистки")
        return 0
    
    deleted_params = set(deleted_params_list)
    print(f"Очистка параметров: {deleted_params}")
    
    cleaned_count = 0
    
    # Очищаем все файлы param_values*.json
    param_files = glob.glob("param_values*.json")
    print(f"Найдено файлов: {len(param_files)}")
    
    for param_file in param_files:
        try:
            with open(param_file, "r", encoding="utf-8") as f:
                param_data = json.load(f)
            
            original_keys_count = 0
            cleaned_keys_count = 0
            
            # Поддерживаем оба формата: новый (с file_name) и старый (прямой словарь)
            if isinstance(param_data, dict) and "param_values" in param_data:
                # Новый формат
                file_params = param_data.get("param_values", {})
                file_options = param_data.get("param_options", {})
                
                original_keys_count = len(file_params)
                
                # Удаляем удаленные параметры
                cleaned_params = {k: v for k, v in file_params.items() if k not in deleted_params}
                cleaned_options = {k: v for k, v in file_options.items() if k not in deleted_params}
                
                cleaned_keys_count = len(cleaned_params)
                
                # Обновляем данные
                param_data["param_values"] = cleaned_params
                param_data["param_options"] = cleaned_options
                
                # Сохраняем обратно если были изменения
                if cleaned_params != file_params or cleaned_options != file_options:
                    with open(param_file, "w", encoding="utf-8") as f:
                        json.dump(param_data, f, ensure_ascii=False, indent=2)
                    cleaned_count += 1
                    print(f"  ✓ {param_file}: удалено {original_keys_count - cleaned_keys_count} параметров")
            else:
                # Старый формат - прямой словарь
                if isinstance(param_data, dict):
                    original_keys_count = len(param_data)
                    cleaned_params = {k: v for k, v in param_data.items() if k not in deleted_params}
                    cleaned_keys_count = len(cleaned_params)
                    
                    if cleaned_params != param_data:
                        with open(param_file, "w", encoding="utf-8") as f:
                            json.dump(cleaned_params, f, ensure_ascii=False, indent=2)
                        cleaned_count += 1
                        print(f"  ✓ {param_file}: удалено {original_keys_count - cleaned_keys_count} параметров")
        except Exception as e:
            print(f"  ✗ Ошибка при обработке {param_file}: {e}")
            continue
    
    # Очищаем глобальный файл
    if os.path.exists("param_values_global.json"):
        try:
            with open("param_values_global.json", "r", encoding="utf-8") as f:
                global_data = json.load(f)
            
            original_keys = 0
            cleaned_keys = 0
            
            # Поддерживаем оба формата
            if isinstance(global_data, dict) and "param_values" in global_data:
                original_keys = len(global_data.get("param_values", {}))
                cleaned_params = {k: v for k, v in global_data.get("param_values", {}).items() if k not in deleted_params}
                cleaned_options = {k: v for k, v in global_data.get("param_options", {}).items() if k not in deleted_params}
                cleaned_keys = len(cleaned_params)
                
                global_data["param_values"] = cleaned_params
                global_data["param_options"] = cleaned_options
            else:
                # Старый формат
                if isinstance(global_data, dict):
                    original_keys = len(global_data)
                    global_data = {k: v for k, v in global_data.items() if k not in deleted_params}
                    cleaned_keys = len(global_data)
            
            if original_keys != cleaned_keys:
                with open("param_values_global.json", "w", encoding="utf-8") as f:
                    json.dump(global_data, f, ensure_ascii=False, indent=2)
                cleaned_count += 1
                print(f"  ✓ param_values_global.json: удалено {original_keys - cleaned_keys} параметров")
        except Exception as e:
            print(f"  ✗ Ошибка при обработке param_values_global.json: {e}")
    
    # Очищаем table_cache.json
    if os.path.exists("table_cache.json"):
        try:
            with open("table_cache.json", "r", encoding="utf-8") as f:
                table_cache_data = json.load(f)
            
            if isinstance(table_cache_data, dict):
                original_keys = 0
                cleaned_keys = 0
                
                # Очищаем param_values
                if "param_values" in table_cache_data:
                    original_keys = len(table_cache_data["param_values"])
                    table_cache_data["param_values"] = {
                        k: v for k, v in table_cache_data["param_values"].items() 
                        if k not in deleted_params
                    }
                    cleaned_keys = len(table_cache_data["param_values"])
                
                # Очищаем param_options
                if "param_options" in table_cache_data:
                    table_cache_data["param_options"] = {
                        k: v for k, v in table_cache_data["param_options"].items() 
                        if k not in deleted_params
                    }
                
                if original_keys != cleaned_keys:
                    with open("table_cache.json", "w", encoding="utf-8") as f:
                        json.dump(table_cache_data, f, ensure_ascii=False, indent=2)
                    cleaned_count += 1
                    print(f"  ✓ table_cache.json: удалено {original_keys - cleaned_keys} параметров")
        except Exception as e:
            print(f"  ✗ Ошибка при обработке table_cache.json: {e}")
    
    return cleaned_count

if __name__ == "__main__":
    # Загружаем список удаленных параметров
    if os.path.exists("deleted_params.json"):
        with open("deleted_params.json", "r", encoding="utf-8") as f:
            deleted_params_list = json.load(f)
        print(f"Загружено удаленных параметров из файла: {deleted_params_list}")
    else:
        deleted_params_list = []
        print("Файл deleted_params.json не найден")
    
    # Можно также указать параметры вручную
    if len(deleted_params_list) == 0:
        # Если файл пуст или не существует, можно указать параметры вручную
        print("\nВведите параметры для удаления (через запятую) или нажмите Enter для выхода:")
        manual_input = input().strip()
        if manual_input:
            deleted_params_list = [p.strip() for p in manual_input.split(",")]
    
    if deleted_params_list:
        print(f"\nНачинаем очистку параметров: {deleted_params_list}")
        cleaned_count = clean_deleted_params_from_all_files(deleted_params_list)
        print(f"\n✓ Готово! Очищено файлов: {cleaned_count}")
    else:
        print("Нет параметров для удаления")


