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

    with open("news.txt", "w", encoding="utf-8") as file:
        for item in items[:10]:
            title = item.title.text.strip()
            link = item.link.text.strip()
            news.append((title, link))
            file.write(f"{title}\n{link}\n{'-' * 50}\n")

    print("✅ News saved to file.")
    return news

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton("📢 دریافت اخبار", callback_data="get_news")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "سلام! ⚡\nبه FlashWire خوش اومدی 🌍\n\n"
        "من هر لحظه جدیدترین تیترهای BBC فارسی رو برات می‌فرستم!\n"
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
    news = getNews()
    if not news:
        await update.message.reply_text("❗اوپس... در دریافت اخبار مشکلی پیش اومده 😕\nکمی بعد دوباره امتحان کن.")
        return

    message = "🗞️ تازه‌ترین خبرهای BBC فارسی از FlashWire ⚡\n\n"
    for title, link in news:
        message += f"• <b>{title}</b>\n🔗 {link}\n\n"

    await update.message.reply_text(message, parse_mode="HTML")

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "get_news":
        news = getNews()
        if not news:
            await query.message.reply_text("❗اوپس... در دریافت اخبار مشکلی پیش اومده 😕\nلطفاً کمی بعد دوباره امتحان کن.")
            return

        message = "🗞️ تازه‌ترین خبرهای BBC فارسی از FlashWire ⚡\n\n"
        for title, link in news:
            message += f"• <b>{title}</b>\n🔗 {link}\n\n"

        await query.message.reply_text(message, parse_mode="HTML")

if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("news", news_command))
    app.add_handler(CallbackQueryHandler(button))

    print("🤖 FlashWire bot is running...")
    app.run_polling()