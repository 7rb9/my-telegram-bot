import os
import requests
import telebot
import yt_dlp
import threading
from flask import Flask
from datetime import datetime

# إعداد سيرفر الويب للبقاء مستيقظاً على رندر
app = Flask(__name__)
@app.route('/')
def home(): return "Bot is running"
def run(): app.run(host='0.0.0.0', port=10000)
threading.Thread(target=run).start()

TOKEN = "8875076734:AAFUBO4YjVgkdzdC5E4d0RhLjL6ScN2N6Yw"
ADMIN_ID = 539671493
bot = telebot.TeleBot(TOKEN)

# إعداد قائمة الأوامر للمسؤول
bot.set_my_commands([
    telebot.types.BotCommand("start", "البدء"),
    telebot.types.BotCommand("stats", "الإحصائيات"),
    telebot.types.BotCommand("ban", "حظر"),
    telebot.types.BotCommand("unban", "فك الحظر"),
    telebot.types.BotCommand("logs", "السجلات")
])

LOG_FILE = "users_log.txt"
BAN_FILE = "banned_users.txt"

def get_banned_users():
    if not os.path.exists(BAN_FILE): return set()
    with open(BAN_FILE, "r", encoding="utf-8") as f: return set(line.strip() for line in f if line.strip())

def manage_ban(user_id, action="add"):
    banned = get_banned_users()
    if action == "add": banned.add(str(user_id))
    else: banned.discard(str(user_id))
    with open(BAN_FILE, "w", encoding="utf-8") as f:
        for uid in banned: f.write(f"{uid}\n")

def log_user(user):
    entry = f"{datetime.now()} | {user.first_name} | {user.id}\n"
    with open(LOG_FILE, "a", encoding="utf-8") as f: f.write(entry)

@bot.message_handler(func=lambda m: str(m.from_user.id) in get_banned_users())
def handle_banned(m): bot.reply_to(m, "❌ تم حظرك من استخدام البوت.")

@bot.message_handler(commands=["stats", "ban", "unban", "logs"], func=lambda m: m.from_user.id == ADMIN_ID)
def admin_cmds(m):
    cmd = m.text.split()
    if cmd[0] == "/stats": bot.reply_to(m, f"👥 عدد المحظورين: {len(get_banned_users())}")
    elif cmd[0] == "/ban" and len(cmd) > 1: manage_ban(cmd[1], "add"); bot.reply_to(m, "🚫 تم الحظر.")
    elif cmd[0] == "/unban" and len(cmd) > 1: manage_ban(cmd[1], "remove"); bot.reply_to(m, "✅ تم فك الحظر.")
    elif cmd[0] == "/logs" and os.path.exists(LOG_FILE):
        with open(LOG_FILE, "rb") as f: bot.send_document(m.chat.id, f)

@bot.message_handler(commands=["start"])
def start(m): log_user(m.from_user); bot.reply_to(m, "أهلاً بك! أرسل رابط الفيديو للتحميل.")

@bot.message_handler(func=lambda m: m.text and ("tiktok" in m.text or "instagram" in m.text or "youtu" in m.text))
def download(m):
    status = bot.reply_to(m, "جاري المعالجة... ⏳")
    url = m.text.strip()
    try:
        data = requests.get(f"https://api.v02.savetube.me/download?url={url}", timeout=10).json()
        if data.get("status"):
            bot.send_video(m.chat.id, data["video_url"])
            bot.delete_message(m.chat.id, status.message_id)
            return
    except: pass
    try:
        ydl_opts = {"format": "best", "outtmpl": "media.mp4"}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
            with open("media.mp4", "rb") as f: bot.send_video(m.chat.id, f)
            os.remove("media.mp4")
            bot.delete_message(m.chat.id, status.message_id)
    except: bot.edit_message_text("❌ فشل التحميل.", m.chat.id, status.message_id)

if __name__ == "__main__": bot.infinity_polling()
