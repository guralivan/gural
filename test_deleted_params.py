#!/usr/bin/env python3
"""Скрипт для проверки удаленных параметров"""
import json
import glob

# Загружаем список удаленных параметров
if __name__ == "__main__":
    try:
        with open("deleted_params.json", "r", encoding="utf-8") as f:
            deleted_params = json.load(f)
        print(f"✅ В deleted_params.json: {deleted_params}")
    except:
        deleted_params = []
        print("❌ Файл deleted_params.json не найден или пуст")
    
    if not deleted_params:
        print("⚠️ Нет удаленных параметров")
        exit(0)
    
    deleted_params_set = set(deleted_params)
    
    # Проверяем файлы
    files_with_deleted = {}
    param_files = glob.glob("param_values*.json")
    
    for param_file in param_files:
        try:
            with open(param_file, "r", encoding="utf-8") as f:
                param_data = json.load(f)
            
            # Поддерживаем оба формата
            if isinstance(param_data, dict) and "param_values" in param_data:
                file_params = param_data.get("param_values", {})
            else:
                file_params = param_data if isinstance(param_data, dict) else {}
            
            # Проверяем, есть ли удаленные параметры
            found_deleted = [p for p in deleted_params_set if p in file_params]
            if found_deleted:
                files_with_deleted[param_file] = found_deleted
        except:
            continue
    
    if files_with_deleted:
        print(f"\n❌ Найдено {len(files_with_deleted)} файлов с удаленными параметрами:")
        for file, params in files_with_deleted.items():
            print(f"  - {file}: {params}")
        print("\n⚠️ Нужно запустить clean_deleted_params.py для очистки!")
    else:
        print(f"\n✅ Все файлы очищены от удаленных параметров: {deleted_params}")
        
        # Проверяем param_values_global.json
        if glob.glob("param_values_global.json"):
            try:
                with open("param_values_global.json", "r", encoding="utf-8") as f:
                    global_data = json.load(f)
                if isinstance(global_data, dict) and "param_values" in global_data:
                    global_params = global_data.get("param_values", {})
                else:
                    global_params = global_data if isinstance(global_data, dict) else {}
                
                found_deleted = [p for p in deleted_params_set if p in global_params]
                if found_deleted:
                    print(f"❌ param_values_global.json содержит удаленные параметры: {found_deleted}")
                else:
                    print("✅ param_values_global.json очищен")
            except:
                pass


