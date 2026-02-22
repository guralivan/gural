#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для восстановления удаленного параметра из проекта
"""
import json
import os
import glob
import sys

def restore_param_from_project(project_name_contains, param_name):
    """Восстанавливает параметр из проекта по названию проекта"""
    
    # Ищем файлы проектов
    project_files = glob.glob('*.json')
    found_project = None
    
    for file in project_files:
        try:
            with open(file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, dict) and 'project_name' in data:
                    project_name = data.get('project_name', '')
                    if project_name_contains.lower() in project_name.lower():
                        print(f'✅ Найден проект: "{project_name}" в файле {file}')
                        found_project = (file, data)
                        break
        except Exception as e:
            continue
    
    if not found_project:
        print(f'❌ Проект с названием, содержащим "{project_name_contains}", не найден')
        return False
    
    file_path, project_data = found_project
    
    # Проверяем, есть ли параметр в удаленных
    deleted_params = project_data.get('deleted_params', [])
    if isinstance(deleted_params, list):
        deleted_params = set(deleted_params)
    else:
        deleted_params = set(deleted_params) if deleted_params else set()
    
    if param_name not in deleted_params:
        print(f'⚠️ Параметр "{param_name}" не найден в списке удаленных параметров проекта')
        print(f'   Удаленные параметры: {sorted(deleted_params)}')
        return False
    
    print(f'✅ Параметр "{param_name}" найден в удаленных параметрах')
    
    # Удаляем параметр из списка удаленных
    deleted_params.discard(param_name)
    project_data['deleted_params'] = sorted(list(deleted_params))
    
    # Инициализируем параметр пустыми значениями, если его нет
    param_values = project_data.get('param_values', {})
    param_options = project_data.get('param_options', {})
    
    if param_name not in param_values:
        param_values[param_name] = {}
        project_data['param_values'] = param_values
    
    if param_name not in param_options:
        param_options[param_name] = []
        project_data['param_options'] = param_options
    
    # Сохраняем обновленный проект
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(project_data, f, ensure_ascii=False, indent=2, default=str)
        print(f'✅ Проект обновлен и сохранен в {file_path}')
        print(f'✅ Параметр "{param_name}" восстановлен!')
        print(f'\n💡 Теперь нужно:')
        print(f'   1. Загрузить проект "{project_data.get("project_name")}" в приложении')
        print(f'   2. Параметр "{param_name}" будет доступен (но значения нужно будет заполнить заново)')
        return True
    except Exception as e:
        print(f'❌ Ошибка сохранения проекта: {e}')
        return False

if __name__ == '__main__':
    # Параметры для восстановления
    project_name = 'Минимальная мука'  # или 'Минадльная мука' если опечатка
    param_name = 'Упаковка'
    
    print(f'Восстановление параметра "{param_name}" из проекта "{project_name}"...')
    print('=' * 60)
    
    # Пробуем оба варианта названия (на случай опечатки)
    success = restore_param_from_project('минимальная мука', param_name)
    if not success:
        print('\nПробую вариант с опечаткой "Минадльная мука"...')
        success = restore_param_from_project('минадльная мука', param_name)
    
    if success:
        print('\n' + '=' * 60)
        print('✅ Готово!')
    else:
        print('\n' + '=' * 60)
        print('❌ Параметр не восстановлен. Проверьте:')
        print('   1. Существует ли проект с таким названием')
        print('   2. Был ли параметр действительно удален')
        sys.exit(1)




