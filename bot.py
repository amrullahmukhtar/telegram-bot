import json, os, uuid
from flask import Flask
from threading import Thread
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# ====== KEEP ALIVE SECTION ======
app = Flask('')

@app.route('/')
def home():
    return "Bot is running!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()
# =================================

TOKEN = "7238254596:AAH81y0LUS84kaqOVwc4TsN8QzKJIocBTbo"
DATA_FILE = "data.json"

CHANNEL_ID = -1002792301572
GROUP_ID = -1002808214921

# Load data
if os.path.exists(DATA_FILE):
    with open(DATA_FILE, "r") as f:
        DATA = json.load(f)
else:
    DATA = {}

def save_data():
    with open(DATA_FILE, "w") as f:
        json.dump(DATA, f)

async def is_member(bot, user_id):
    try:
        ch_status = await bot.get_chat_member(CHANNEL_ID, user_id)
        gc_status = await bot.get_chat_member(GROUP_ID, user_id)
        if (ch_status.status not in ["left", "kicked"]) and (gc_status.status not in ["left", "kicked"]):
            return True
        else:
            return False
    except Exception as e:
        print(f"Error cek member: {e}")
        return False

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if not await is_member(context.bot, user_id):
        await update.message.reply_text(
            "🚫 Kamu harus join dulu ke Channel & Group sebelum bisa akses konten!\n\n"
            "👉 Channel: https://t.me/+PmiJeujimNA1MWM9\n"
            "👉 Group: https://t.me/+PmiJeujimNA1MWM9"
        )
        return

    if context.args:
        key = context.args[0]
        if key in DATA:
            file_id = DATA[key]["file_id"]
            caption = DATA[key]["caption"]
            await update.message.reply_photo(photo=file_id, caption=caption)
        else:
            await update.message.reply_text("⚠️ Link tidak valid atau sudah kadaluarsa.")
    else:
        await update.message.reply_text("Halo Bub 👋 kirim foto + caption, nanti aku kasih link unik.")

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    photo = update.message.photo[-1]
    file_id = photo.file_id
    caption = update.message.caption if update.message.caption else "(Tidak ada caption)"

    key = str(uuid.uuid4())[:8]
    DATA[key] = {"file_id": file_id, "caption": caption}
    save_data()

    bot_username = (await context.bot.get_me()).username
    link = f"https://t.me/{bot_username}?start={key}"

    await update.message.reply_text(
        f"✅ Foto diterima!\n\nCaption: {caption}\n\n🔗 Link unik untuk share (hanya bisa dibuka member ch & gc):\n{link}"
    )

def main():
    keep_alive()  # 🔥 Tambahkan ini agar bot tetap aktif di Render
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))

    print("Bot berjalan dengan proteksi join ch & gc...")
    app.run_polling()

if __name__ == "__main__":
    main()
