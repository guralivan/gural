# -*- coding: utf-8 -*-
import logging
import os

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)


BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
WEBAPP_URL = os.getenv("WEBAPP_URL", "").strip()
SET_MENU_BUTTON = os.getenv("SET_MENU_BUTTON", "1") == "1"


def _build_keyboard():
    return InlineKeyboardMarkup(
        [[InlineKeyboardButton("Открыть каталог", web_app=WebAppInfo(url=WEBAPP_URL))]]
    )


async def start(update, context: ContextTypes.DEFAULT_TYPE):
    if not WEBAPP_URL:
        await update.message.reply_text(
            "WEBAPP_URL не задан. Укажите URL мини‑приложения."
        )
        return
    await update.message.reply_text(
        "Откройте каталог JASMU:",
        reply_markup=_build_keyboard(),
    )


async def help_cmd(update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Команда /start откроет каталог.")


async def on_startup(app):
    if not WEBAPP_URL or not SET_MENU_BUTTON:
        return
    try:
        await app.bot.set_chat_menu_button(
            menu_button={"type": "web_app", "text": "Открыть каталог", "web_app": {"url": WEBAPP_URL}}
        )
    except Exception as exc:
        logging.warning("Не удалось установить меню бота: %s", exc)


def main():
    if not BOT_TOKEN:
        raise SystemExit("BOT_TOKEN не задан")
    app = ApplicationBuilder().token(BOT_TOKEN).post_init(on_startup).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.run_polling()


if __name__ == "__main__":
    main()
