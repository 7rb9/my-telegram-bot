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
    user_name = user.first_name or ""
    if user.last_name:
        user_name += f" {user.last_name}"
    is_new = True
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r", encoding="utf-8") as file:
            if str(user.id) in file.read():
                is_new = False
    log_entry = f"التاريخ: {current_time} | الاسم: {user_name} | المعرف: @{user.username or 'لا يوجد'} | ID: {user.id}\n"
    with open(LOG_FILE, "a", encoding="utf-8") as file:
        file.write(log_entry)
    if is_new:
        try:
            bot.send_message(ADMIN_ID, f"🔔 **مستخدم جديد دخل البوت!**\n\n👤 الاسم: {user_name}\n🆔 الآيدي: `{user.id}`\n🔗 المعرف: @{user.username or 'لا يوجد'}", parse_mode="Markdown", disable_web_page_preview=True)
        except Exception:
            pass

@bot.message_handler(func=lambda message: str(message.from_user.id) in get_banned_users())
def handle_banned(message):
    bot.reply_to(message, "❌ نعتذر منك، لقد تم حظرك من استخدام هذا البوت.")

@bot.message_handler(commands=["stats", "ban", "unban", "logs"], func=lambda message: message.from_user.id == ADMIN_ID)
def admin_commands(message):
    command = message.text.split()
    cmd_name = command[0].lower()
    if cmd_name == "/stats":
        total_users = 0
        if os.path.exists(LOG_FILE):
            with open(LOG_FILE, "r", encoding="utf-8") as f:
                total_users = len(set(line.split("ID: ")[1].strip() for line in f if "ID: " in line))
        banned_count = len(get_banned_users())
        bot.reply_to(message, f"📊 **إحصائيات البوت الحالية:**\n\n👥 إجمالي المستخدمين: {total_users}\n🚫 عدد المحظورين: {banned_count}", parse_mode="Markdown")
    elif cmd_name == "/ban":
        if len(command) < 2:
            bot.reply_to(message, "❌ يرجى كتابة الأمر بالشكل الصحيح: `/ban رقم_الآيدي`")
            return
        target_id = command[1].strip()
        ban_user(target_id)
        bot.reply_to(message, f"🚫 تم حظر المستخدم صاحب الآيدي `{target_id}` بنجاح.")
    elif cmd_name == "/unban":
        if len(command) < 2:
            bot.reply_to(message, "❌ يرجى كتابة الأمر بالشكل الصحيح: `/unban رقم_الآيدي`")
            return
        target_id = command[1].strip()
        unban_user(target_id)
        bot.reply_to(message, f"✅ تم إلغاء الحظر عن المستخدم صاحب الآيدي `{target_id}`.")
    elif cmd_name == "/logs":
        if os.path.exists(LOG_FILE):
            with open(LOG_FILE, "rb") as f:
                bot.send_document(message.chat.id, f)
        else:
            bot.reply_to(message, "❌ ملف السجلات فارغ أو غير موجود.")

@bot.message_handler(commands=["start"])
def send_welcome(message):
    log_user(message.from_user)
    welcome_text = f"أهلاً بك يا {message.from_user.first_name}! 🌹\n\nأرسل لي الآن رابط الفيديو أو الصور من مواقع التواصل الاجتماعي لأقوم بتحميلها لك فوراً."
    bot.reply_to(message, welcome_text)

@bot.message_handler(func=lambda message: message.text and ("tiktok.com" in message.text or "instagram.com" in message.text or "youtu" in message.text))
def handle_download(message):
    url = message.text.strip()
    status_msg = bot.reply_to(message, "جاري معالجة الرابط والتحميل... انتظر لحظة من فضلك ⏳")
    caption_text = "تم التحميل بواسطة بوت رامي 🎬"
    api_url = f"https://api.v02.savetube.me/download?url={url}"
    try:
        response = requests.get(api_url, timeout=15)
        data = response.json()
        if data.get("status") and "video_url" in data:
            bot.send_video(message.chat.id, data["video_url"], caption=caption_text, reply_to_message_id=message.message_id)
            bot.delete_message(message.chat.id, status_msg.message_id)
            return
    except Exception:
        pass
    ydl_opts = {"format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best", "outtmpl": "downloaded_media.%(ext)s", "merge_output_format": "mp4", "quiet": True}
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            if "entries" in info:
                for entry in info["entries"]:
                    filename = ydl.prepare_filename(entry)
                    if os.path.exists(filename):
                        with open(filename, "rb") as media:
                            if filename.endswith((".jpg", ".jpeg", ".png")):
                                bot.send_photo(message.chat.id, media, caption=caption_text)
                            else:
                                bot.send_video(message.chat.id, media, caption=caption_text)
                        os.remove(filename)
                bot.delete_message(message.chat.id, status_msg.message_id)
                return
            filename = ydl.prepare_filename(info)
            if not os.path.exists(filename) and os.path.exists("downloaded_media.mp4"):
                filename = "downloaded_media.mp4"
            if os.path.exists(filename):
                with open(filename, "rb") as media:
                    if filename.endswith((".jpg", ".jpeg", ".png")):
                        bot.send_photo(message.chat.id, media, caption=caption_text, reply_to_message_id=message.message_id)
                    else:
                        bot.send_video(message.chat.id, media, caption=caption_text, reply_to_message_id=message.message_id)
                bot.delete_message(message.chat.id, status_msg.message_id)
                os.remove(filename)
                return
    except Exception as e:
        print(f"Error: {e}")
    bot.edit_message_text("❌ تعذر تحميل المحتوى حالياً. تأكد من صحة الرابط أو جرب رابطاً آخر.", message.chat.id, status_msg.message_id)

if __name__ == "__main__":
    print("🤖 البوت المطور يعمل الآن بنجاح...")
    bot.infinity_polling()
