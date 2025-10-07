import os
import requests
from bs4 import BeautifulSoup
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

TOKEN = os.environ.get("TELEGRAM_TOKEN")

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/114.0.0.0 Safari/537.36"
}


def getNews():
    url = "https://feeds.bbci.co.uk/persian/rss.xml"
    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        print("❌ RSS ran into a problem, HTTP Status:", response.status_code)
        return []

    soup = BeautifulSoup(response.content, "xml")
    items = soup.find_all("item")

    news = []

    for item in items[:10]:
        title = item.title.text.strip()
        link = item.link.text.strip()
        news.append((title, link))

    print("✅ News fetched successfully.")
    return news


async def send_news(update, context, index=0):
    if "news_data" not in context.user_data:
        context.user_data["news_data"] = getNews()

    news_data = context.user_data["news_data"]
    if not news_data:
        await update.message.reply_text("❗ اوپس، خبری موجود نیست!")
        return

    title, link = news_data[index]
    message = f"🗞️ <b>{title}</b>\n🔗 {link}"

    keyboard = []
    if index > 0:
        keyboard.append(InlineKeyboardButton("⬅️ قبلی", callback_data=f"news_{index-1}"))
    if index < len(news_data) - 1:
        keyboard.append(InlineKeyboardButton("بعدی ➡️", callback_data=f"news_{index+1}"))

    reply_markup = InlineKeyboardMarkup([keyboard])

    if hasattr(update, "message") and update.message:
        await update.message.reply_text(message, parse_mode="HTML", reply_markup=reply_markup)
    else:
        await update.callback_query.edit_message_text(
            message, parse_mode="HTML", reply_markup=reply_markup
        )


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton("📢 دریافت اخبار", callback_data="get_news")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "سلام! ⚡\nبه FlashWire خوش اومدی 🌍\n\n"
        "من جدیدترین تیترهای BBC فارسی رو برات می‌فرستم!\n"
        "برای شروع روی دکمه زیر بزن 👇",
        reply_markup=reply_markup
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📘 راهنمای استفاده از FlashWire:\n\n"
        "/start - شروع گفتگو با ربات\n"
        "/help - نمایش راهنما\n"
        "/news - دریافت جدیدترین اخبار BBC فارسی"
    )


async def news_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await send_news(update, context, index=0)


async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "get_news":
        await send_news(update, context, index=0)
    elif query.data.startswith("news_"):
        index = int(query.data.split("_")[1])
        await send_news(update, context, index=index)


if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("news", news_command))
    app.add_handler(CallbackQueryHandler(button))

    print("🤖 FlashWire bot is running...")
    app.run_polling()
