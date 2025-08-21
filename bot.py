import os
import json
import uuid
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)
from telegram.error import BadRequest

# === CONFIG VIA ENV (Railway Variables) ===
TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))   # contoh: -100123456789
GROUP_ID = int(os.getenv("GROUP_ID"))       # contoh: -100987654321
DATA_FILE = "data.json"

# === LOAD / SAVE DATA ===
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

DATA = load_data()

# === CEK MEMBER ===
async def check_membership(user_id: int, context: ContextTypes.DEFAULT_TYPE):
    try:
        ch_member = await context.bot.get_chat_member(CHANNEL_ID, user_id)
        gp_member = await context.bot.get_chat_member(GROUP_ID, user_id)
        return (ch_member.status in ["member", "administrator", "creator"]) and \
               (gp_member.status in ["member", "administrator", "creator"])
    except BadRequest:
        return False

# === /START HANDLER ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    args = context.args

    if not await check_membership(user.id, context):
        # Tombol Join + Coba Lagi
        keyboard = [
            [
                InlineKeyboardButton("📢 Join Ch", url=f"https://t.me/{abs(CHANNEL_ID)}"),
                InlineKeyboardButton("👥 Join Gc", url=f"https://t.me/{abs(GROUP_ID)}"),
            ],
            [InlineKeyboardButton("🔄 Coba Lagi", callback_data="retry_start")]
        ]
        await update.message.reply_text(
            "🚫 Kamu harus join dulu ke Channel & Group sebelum bisa akses konten!",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    if args:  # Jika akses via link unik
        key = args[0]
        if key in DATA:
            file_url = DATA[key]["file_url"]
            await update.message.reply_photo(photo=file_url, caption="📸 Berikut foto hasil convert kamu!")
        else:
            await update.message.reply_text("⚠️ Link tidak valid atau sudah kadaluarsa.")
    else:
        await update.message.reply_text("✅ Bot aktif! Kirim fotonya untuk di-convert.")

# === CALLBACK RETRY ===
async def retry_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    # Jalankan ulang start seperti user ketik /start
    fake_update = Update(update.update_id, message=query.message)
    fake_update.message.from_user = query.from_user
    await start(fake_update, context)

# === CONVERT FOTO & GENERATE LINK ===
async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not await check_membership(user.id, context):
        keyboard = [
            [
                InlineKeyboardButton("📢 Join Ch", url=f"https://t.me/{abs(CHANNEL_ID)}"),
                InlineKeyboardButton("👥 Join Gc", url=f"https://t.me/{abs(GROUP_ID)}"),
            ],
            [InlineKeyboardButton("🔄 Coba Lagi", callback_data="retry_start")]
        ]
        await update.message.reply_text(
            "🚫 Kamu harus join dulu ke Channel & Group sebelum bisa akses konten!",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    file = await update.message.photo[-1].get_file()
    file_url = file.file_path

    key = str(uuid.uuid4())
    DATA[key] = {"file_url": file_url, "user_id": user.id}
    save_data(DATA)

    bot_username = (await context.bot.get_me()).username
    share_link = f"https://t.me/{bot_username}?start={key}"

    await update.message.reply_text(f"✅ Foto berhasil di-convert!\n\n🔗 Link share: {share_link}")

# === MAIN ===
def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(retry_callback, pattern="^retry_start$"))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))

    print("🤖 Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
