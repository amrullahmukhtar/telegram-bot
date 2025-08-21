import json, os, uuid
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters

TOKEN = "ISI_TOKEN_BOTMU"   # << ganti dengan token bot kamu
DATA_FILE = "data.json"

# -------------------- Data Handling --------------------
def load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

# -------------------- Command Start --------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [
            InlineKeyboardButton("Join Ch", url="https://t.me/+PmiJeujimNA1MWM9"),
            InlineKeyboardButton("Join Gc", url="https://t.me/+l6NLPfofBHg1N2Q1"),
        ],
        [InlineKeyboardButton("🔄 Coba Lagi", callback_data="retry_start")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.message:
        await update.message.reply_text(
            "🚫 Kamu harus join dulu ke Channel & Group sebelum bisa akses konten!",
            reply_markup=reply_markup
        )
    elif update.callback_query:
        await update.callback_query.message.reply_text(
            "🚫 Kamu harus join dulu ke Channel & Group sebelum bisa akses konten!",
            reply_markup=reply_markup
        )

# -------------------- Callback Retry --------------------
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "retry_start":
        user_id = query.from_user.id
        data = load_data()

        # ambil semua foto user ini
        user_photos = [
            val for val in data.values()
            if val["user_id"] == user_id
        ]

        if user_photos:
            last_photo = user_photos[-1]  # ambil foto terakhir
            await query.message.reply_photo(
                photo=last_photo["file_id"],
                caption=f"📸 Foto terakhir kamu.\nLink share: {last_photo['link']}"
            )
        else:
            await start(update, context)

# -------------------- Handler Foto --------------------
async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    photo = update.message.photo[-1]
    file_id = photo.file_id

    unique_key = str(uuid.uuid4())
    data = load_data()
    link = f"https://t.me/{context.bot.username}?start={unique_key}"

    # simpan foto baru (tidak overwrite, jadi semua history tersimpan)
    data[unique_key] = {
        "user_id": user.id,
        "file_id": file_id,
        "link": link
    }
    save_data(data)

    await update.message.reply_text(f"✅ Foto disimpan!\nLink share: {link}")

# -------------------- Main --------------------
def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(CallbackQueryHandler(button_handler))

    app.run_polling()

if __name__ == "__main__":
    main()
