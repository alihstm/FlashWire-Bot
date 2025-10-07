import os
import requests
from bs4 import BeautifulSoup
import sqlite3
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

# early settings
TOKEN = os.environ.get("TELEGRAM_TOKEN")

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/114.0.0.0 Safari/537.36"
}

# connect to database and create the table
conn = sqlite3.connect("flashwire.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chat_id INTEGER UNIQUE
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS news (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT UNIQUE,
    link TEXT
)
""")

conn.commit()

# manage the users
def add_user(chat_id):
    try:
        cursor.execute("INSERT OR IGNORE INTO users (chat_id) VALUES (?)", (chat_id,))
        conn.commit()
    except Exception as e:
        print("❌ Error adding user:", e)

def get_all_users():
    cursor.execute("SELECT chat_id FROM users")
    return [row[0] for row in cursor.fetchall()]

# recive and save the earliest news
def getNews():
    url = "https://feeds.bbci.co.uk/persian/rss.xml"
    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        print("❌ RSS ran into a problem, HTTP Status:", response.status_code)
        return []

    soup = BeautifulSoup(response.content, "xml")
    items = soup.find_all("item")

    news = [(item.title.text.strip(), item.link.text.strip()) for item in items[:10]]

    print("✅ News fetched successfully.")
    return news

def save_new_news(news_list):
    new_items = []
    for title, link in news_list:
        try:
            cursor.execute("INSERT OR IGNORE INTO news (title, link) VALUES (?, ?)", (title, link))
            conn.commit()
            if cursor.rowcount > 0:
                new_items.append((title, link))
        except Exception as e:
            print("❌ Error saving news:", e)
    return new_items

# send news to the users
async def send_news(update, context, index=0):
    # get early news from news_data
    if "news_data" not in context.user_data:
        context.user_data["news_data"] = getNews()

    news_data = context.user_data["news_data"]
    if not news_data:
        await update.message.reply_text("❗خبری موجود نیست")
        return

    # news message
    title, link = news_data[index]
    message = f"🗞️ <b>{title}</b>\n🔗 {link}"

    # next/pervious buttons
    keyboard = []
    if index > 0:
        keyboard.append(InlineKeyboardButton("قبلی ⬅️", callback_data=f"news_{index-1}"))
    if index < len(news_data) - 1:
        keyboard.append(InlineKeyboardButton("➡️ بعدی", callback_data=f"news_{index+1}"))

    reply_markup = InlineKeyboardMarkup([keyboard]) if keyboard else None

    # send message
    if hasattr(update, "message") and update.message:
        await update.message.reply_text(message, parse_mode="HTML", reply_markup=reply_markup)
    else:
        await update.callback_query.edit_message_text(
            message, parse_mode="HTML", reply_markup=reply_markup
        )

# update news
async def check_for_updates(context):
    news_list = getNews()
    new_items = save_new_news(news_list)
    if not new_items:
        return

    for user_id in get_all_users():
        for title, link in new_items:
            try:
                await context.bot.send_message(user_id, f"🆕 <b>{title}</b>\n🔗 {link}", parse_mode="HTML")
            except Exception as e:
                print("❌ Error sending to user:", e)

# commands and buttons
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    add_user(update.effective_user.id)
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
    add_user(update.effective_user.id)
    await send_news(update, context, index=0)

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "get_news":
        await send_news(update, context, index=0)
    elif query.data.startswith("news_"):
        index = int(query.data.split("_")[1])
        await send_news(update, context, index=index)

# run the bot
if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()

    # add commands
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("news", news_command))
    app.add_handler(CallbackQueryHandler(button))

    # update news each 30 minutes
    app.job_queue.run_repeating(check_for_updates, interval=1800, first=10)

    print("🤖 FlashWire bot is running...")
    app.run_polling()
