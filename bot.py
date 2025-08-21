import json, os, uuid
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    Application, CommandHandler, MessageHandler, CallbackQueryHandler,
    filters, ContextTypes
)

# Ambil variabel dari Railway
TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))
GROUP_ID = int(os.getenv("GROUP_ID"))
DATA_FILE = "data.json"

# Daftar admin yang boleh upload foto
ADMINS = [8459702708, 7665073181]  # ganti dengan Telegram user_id kamu

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
async def is_member(bot, user_id):
    try:
        ch_status = await bot.get_chat_member(CHANNEL_ID, user_id)
        gc_status = await bot.get_chat_member(GROUP_ID, user_id)
        return (ch_status.status not in ["left", "kicked"]) and (gc_status.status not in ["left", "kicked"])
    except Exception as e:
        print(f"Error cek member: {e}")
        return False

# /start handler
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    # Jika belum join → kasih tombol join + coba lagi
    if not await is_member(context.bot, user_id):
        keyboard = [
            [InlineKeyboardButton("📢 Join Channel", url="https://t.me/+PmiJeujimNA1MWM9")],
            [InlineKeyboardButton("💬 Join Group", url="https://t.me/+l6NLPfofBHg1N2Q1")],
            [InlineKeyboardButton("🔄 Coba Lagi", callback_data=f"retry_{' '.join(context.args) if context.args else ''}")]
        ]
        await update.message.reply_text(
            "🚫 Kamu harus join dulu ke Channel & Group sebelum bisa akses konten!",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    # Kalau sudah join
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

# Handler untuk tombol coba lagi
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data.startswith("retry_"):
        key = query.data.replace("retry_", "").strip()
        if key:
            context.args = [key]  # simpan argumen lama
        else:
            context.args = []
        await start(update, context)

# Handler foto masuk dari user (khusus admin)
async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id

    if user_id not in ADMINS:
        await update.message.reply_text("🚫 Kamu bukan admin, tidak boleh upload foto!")
        return

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

    # Command handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("retry", start))

    # Callback button handler
    app.add_handler(CallbackQueryHandler(button_handler))

    # Photo handler
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))

    print("🤖 Bot aktif dengan proteksi member & admin upload only.")
    app.run_polling()

if __name__ == "__main__":
    main()
