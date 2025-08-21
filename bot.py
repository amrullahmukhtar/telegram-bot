import json
import os
import uuid
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Ambil token dari environment variable
TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    raise ValueError("❌ BOT_TOKEN belum di-set di environment variable!")

DATA_FILE = "data.json"

# Ganti dengan ID channel & group kamu
CHANNEL_ID = int(os.getenv("CHANNEL_ID", "-1002792301572"))
GROUP_ID = int(os.getenv("GROUP_ID", "-1002808214921"))

# Load data
if os.path.exists(DATA_FILE):
    with open(DATA_FILE, "r") as f:
        DATA = json.load(f)
else:
    DATA = {}

# Simpan data
def save_data():
    with open(DATA_FILE, "w") as f:
        json.dump(DATA, f)

# Cek apakah user sudah join channel & group
async def is_member(bot, user_id: int) -> bool:
    try:
        ch_status = await bot.get_chat_member(CHANNEL_ID, user_id)
        gc_status = await bot.get_chat_member(GROUP_ID, user_id)
        return (
            ch_status.status not in ["left", "kicked"]
            and gc_status.status not in ["left", "kicked"]
        )
    except Exception as e:
        print(f"⚠️ Error cek member: {e}")
        return False

# /start handler
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if not await is_member(context.bot, user_id):
        await update.message.reply_text(
            "🚫 Kamu harus join dulu ke Channel & Group sebelum bisa akses konten!\n\n"
            "👉 Channel: https://t.me/+PmiJeujimNA1MWM9\n"
            "👉 Group: https://t.me/+l6NLPfofBHg1N2Q1"
        )
        return

    if context.args:
        key = context.args[0]
        if key in DATA:
            file_id = DATA[key]["file_id"]
            caption = DATA[key]["caption"]

            try:
                await update.message.reply_photo(
                    photo=file_id,
                    caption=caption
                )
            except Exception as e:
                await update.message.reply_text("⚠️ Gagal mengirim foto.")
                print(f"Error kirim foto: {e}")
        else:
            await update.message.reply_text("⚠️ Link tidak valid atau sudah kadaluarsa.")
    else:
        await update.message.reply_text("Halo Bub 👋 Donatenya mana?")

# Handler foto masuk dari user
async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.photo:
        return

    caption = update.message.caption if update.message.caption else "(Tidak ada caption)"

    # Ambil file_id dari resolusi tertinggi
    photo = update.message.photo[-1]
    file_id = photo.file_id

    key = str(uuid.uuid4())[:8]
    DATA[key] = {
        "file_id": file_id,
        "caption": caption
    }
    save_data()

    # Buat link
    bot_username = (await context.bot.get_me()).username
    link = f"https://t.me/{bot_username}?start={key}"

    try:
        with open("foto_1.jpg", "rb") as photo_file:
            await update.message.reply_photo(
                photo=photo_file,
                caption=f"{caption}\n\n🔗 Link (khusus member group & channel):\n{link}"
            )
    except FileNotFoundError:
        await update.message.reply_text(
            f"{caption}\n\n🔗 Link (khusus member group & channel):\n{link}"
        )

# Main
def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    print("🤖 Bot aktif dengan proteksi member.")
    app.run_polling()

if __name__ == "__main__":
    main()
