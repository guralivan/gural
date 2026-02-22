# Запуск Telegram‑бота (Mini App)

1) Установить зависимости:
```
python3 -m pip install -r requirements_bot.txt
```

2) Задать переменные окружения:
```
export BOT_TOKEN="токен_бота"
export WEBAPP_URL="https://ваш-домен/miniapp/"
```

3) Запустить бота:
```
python3 telegram_bot.py
```

Бот покажет кнопку открытия каталога. По умолчанию он также пытается установить
кнопку меню чата (можно отключить `SET_MENU_BUTTON=0`).
