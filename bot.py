import os
import requests
import telebot
import yt_dlp
import threading
from flask import Flask
from datetime import datetime

app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running"

def run():
    app.run(host='0.0.0.0', port=10000)

threading.Thread(target=run).start()

TOKEN = "8875076734:AAFUBO4YjVgkdzdC5E4d0RhLjL6ScN2N6Yw"
ADMIN_ID = 539671493
bot = telebot.TeleBot(TOKEN)

# إعداد قائمة الأوامر التي تظهر للمسؤول
bot.set_my_commands([
    telebot.types.BotCommand("start", "بدء تشغيل البوت"),
    telebot.types.BotCommand("stats", "إحصائيات البوت"),
    telebot.types.BotCommand("ban", "حظر مستخدم"),
    telebot.types.BotCommand("unban", "إلغاء حظر مستخدم"),
    telebot.types.BotCommand("logs", "الحصول على ملف السجلات")
])

LOG_FILE = "users_log.txt"
BAN_FILE = "banned_users.txt"

def get_banned_users():
    if not os.path.exists(BAN_FILE):
        return set()
    with open(BAN_FILE, "r", encoding="utf-8") as f:
        return set(line.strip() for line in f if line.strip())

def ban_user(user_id):
    banned = get_banned_users()
    banned.add(str(user_id))
    with open(BAN_FILE, "w", encoding="utf-8") as f:
        for uid in banned:
            f.write(f"{uid}\n")

def unban_user(user_id):
    banned = get_banned_users()
    banned.discard(str(user_id))
    with open(BAN_FILE, "w", encoding="utf-8") as f:
        for uid in banned:
            f.write(f"{uid}\n")

def log_user(user):
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    user_name = f"{user.first_name} {user.last_name or ''}"
    is_new = True
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r", encoding="utf-8") as file:
            if str(user.id) in file.read():
                is_new = False
    log_entry = f"التاريخ: {current_time} | الاسم: {user_name} | ID: {user.id}\n"
    with open(LOG_FILE, "a", encoding="utf-8") as file:
        file.write(log_entry)
    if is_new:
        try:
            bot.send_message(ADMIN_ID, f"🔔 **مستخدم جديد:** {user_name}\n🆔 `{user.id}`")
        except: pass

@bot.message_handler(func=lambda message: str(message.from_user.id) in get_banned_users())
def handle_banned(message):
    bot.reply_to(message, "❌ تم حظرك.")

@bot.message_handler(commands=["stats", "ban", "unban", "logs"], func=lambda message: message.from_user.id == ADMIN_ID)
def admin_commands(message):
    command = message.text.split()
    cmd = command[0].lower()
    if cmd == "/stats":
        banned_count = len(get_banned_users())
        bot.reply_to(message, f"📊 عدد المحظورين: {banned_count}")
    elif cmd == "/ban" and len(command) > 1:
        ban_user(command[1])
        bot.reply_to(message, f"🚫 تم حظر: {command[1]}")
    elif cmd == "/unban" and len(command) > 1:
        unban_user(command[1])
        bot.reply_to(message, f"✅ تم فك حظر: {command[1]}")
    elif cmd == "/logs":
        if os.path.exists(LOG_FILE):
            with open(LOG_FILE, "rb") as f:
                bot.send_document(message.chat.id, f)

@bot.message_handler(commands=["start"])
def send_welcome(message):
    log_user(message.from_user)
    bot.reply_to(message, "أهلاً بك! أرسل رابط الفيديو للتحميل.")

@bot.message_handler(func=lambda message: message.text and ("tiktok.com" in message.text or "instagram.com" in message.text or "youtu" in message.text))
def handle_download(message):
    url = message.text.strip()
    status_msg = bot.reply_to(message, "جاري التحميل... ⏳")
    api_url = f"https://api.v02.savetube.me/download?url={url}"
    try:
        data = requests.get(api_url, timeout=10).json()
        if data.get("status") and "video_url" in data:
            bot.send_video(message.chat.id, data["video_url"])
            bot.delete_message(message.chat.id, status_msg.message_id)
            return
    except: pass
    bot.edit_message_text("❌ حدث خطأ، يرجى المحاولة لاحقاً.", message.chat.id, status_msg.message_id)

if __name__ == "__main__":
    bot.infinity_polling()
