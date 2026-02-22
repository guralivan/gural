# 📁 Структура проекта

## Организация приложений

Все приложения организованы в папке `apps/`, каждое приложение находится в своей папке:

```
apps/
├── dashboard/              # 📈 Основной дашборд
│   └── dashboard_final.py
│
├── analytics_45/           # 📊 Аналитика 45.xlsx
│   ├── app_45_simple.py
│   ├── app_45_combined_api_new.py
│   └── ...
│
├── prophet_orders/         # 📦 Прогноз заказов Prophet
│   ├── app_prophet_orders.py
│   └── ...
│
├── prophet_forecast/       # 📈 Прогнозирование Prophet
│   ├── app_prophet_forecast_new.py
│   └── ...
│
├── forecast_45/            # 🔮 Прогноз 45
│   └── app_forecast_45.py
│
├── forecast_orders/        # 📊 Прогноз заказов
│   └── app_forecast_orders.py
│
├── order_balance/          # 📦 Калькулятор баланса заказов
│   └── order_balance_app.py
│
├── seasonal_calculator/    # 🌡️ Сезонный калькулятор
│   └── seasonal_expenses_calculator.py
│
├── production_calendar/    # 📅 Календарь производства
│   └── production_calendar.py
│
├── color_recognition/      # 🎨 Распознавание цветов
│   └── color_recognition_app.py
│
├── contract_generator/     # 📄 Генератор договоров
│   └── contract_generator_app.py
│
├── sales_planning/         # 💼 Планирование продаж
│   └── sales_planning_app.py
│
├── voronka/                # 🔄 Воронка продаж
│   ├── voronka_app.py
│   └── Plan_prodazh.py
│
├── ord_yandex/             # 📋 Заказы Яндекс
│   ├── ord_yandex_app.py
│   └── ord_yandex_app_full.py
│
├── wb_api/                 # 🌐 API Wildberries
│   ├── wb_api_optimized.py
│   ├── wb_api_extended.py
│   └── ...
│
├── ai_analyst/             # 🤖 AI Аналитик
│   └── ai_analyst.py
│
├── auto_downloader/        # ⬇️ Автоскачивание
│   └── wb_auto_downloader.py
│
└── inventory_calculator/   # 📊 Калькулятор инвентаря
    └── inventory_calculator.py
```

## Backup файлы

Все backup-файлы приложений находятся в папке `apps_backup/`:

```
apps_backup/
├── dashboard_final_backup_*.py
├── app_45_simple_backup_*.py
└── ...
```

## Запуск приложений

### Из корня проекта

Все launch-скрипты обновлены для работы с новой структурой. Например:

```bash
# Основной дашборд
./📈_Дашборд.command

# Или через launch-скрипты
./launch_app_45_8509.command
./launch_prophet_orders.command
```

### С рабочего стола

Ярлыки на рабочем столе для быстрого доступа:

- 📈 **Дашборд** - `📈_Дашборд.command`
- 📅 **Календарь производства** - `📅_Календарь_производства.command`
- 🚀 **Все приложения** - `🚀_Все_приложения.command`

Для создания ярлыков выполните:

```bash
./create_desktop_shortcuts.command
```

## Импорты

Файлы в `apps/` используют `sys.path` для импорта модулей из `utils/`. Код добавлен автоматически в файлы, которые используют импорты из `utils/`.

Если нужно добавить вручную, добавьте в начало файла:

```python
import sys
from pathlib import Path
# Добавляем корневую директорию проекта в sys.path для импорта utils
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
```

## Структура папок

```
wb_dashboard_streamlit/
├── apps/                   # Все приложения
├── apps_backup/            # Backup файлы приложений
├── utils/                  # Общие утилиты
├── backups/                # Другие backup файлы
├── UNIT/                   # Юнит-экономика (отдельное приложение)
├── 3/                      # Анализ отчетов (отдельное приложение)
├── OTCHET/                 # Отчеты (отдельное приложение)
└── ...                     # Остальные файлы проекта
```
























