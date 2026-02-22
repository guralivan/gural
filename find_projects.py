#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
import glob

print('Поиск всех проектов...')
print('=' * 60)

projects_found = []
for file in glob.glob('*.json'):
    try:
        with open(file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if isinstance(data, dict) and 'project_name' in data:
                project_name = data.get('project_name', '')
                project_id = data.get('project_id', 'N/A')
                deleted = data.get('deleted_params', [])
                if 'Упаковка' in deleted:
                    print(f'✅ НАЙДЕН: {project_name} (ID: {project_id})')
                    print(f'   Файл: {file}')
                    print(f'   Удаленные параметры: {deleted}')
                    projects_found.append((file, project_name, data))
    except:
        pass

if projects_found:
    print(f'\nНайдено проектов с удаленным параметром "Упаковка": {len(projects_found)}')
else:
    print('\nПроекты с удаленным параметром "Упаковка" не найдены')
    print('\nИщу все проекты...')
    all_projects = []
    for file in glob.glob('*.json'):
        try:
            with open(file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, dict) and 'project_name' in data:
                    all_projects.append((file, data.get('project_name', 'Без названия')))
        except:
            pass
    if all_projects:
        print(f'Всего найдено проектов: {len(all_projects)}')
        for file, name in all_projects[:10]:
            print(f'  - {name} ({file})')




