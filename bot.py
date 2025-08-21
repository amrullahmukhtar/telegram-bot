import os
import json
import uuid
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler

# File untuk menyimpan data
DATA_FILE = "data.json"

# Load data history
def load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, "r") as f:
        return json.load(f)

# Simpan data history
def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

# Fungsi start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    data = load_data()

    if user_id not in data:
        data[user_id] = {"history": []}
        save_data(data)

    keyboard = [
        [InlineKeyboardButton("Coba Lagi", callback_data="retry_start")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "Halo! Kirim foto untuk saya convert.",
        reply_markup=reply_markup
    )

# Handler foto
async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    data = load_data()

    photo = update.message.photo[-1]
    file = await photo.get_file()
    file_id = str(uuid.uuid4()) + ".jpg"
    file_path = f"downloads/{file_id}"

    os.makedirs("downloads", exist_ok=True)
    await file.download_to_drive(file_path)

    # Simpan ke history user
    history_entry = {
        "file_id": file_id,
        "file_path": file_path,
    }
    data[user_id]["history"].append(history_entry)
    save_data(data)

    keyboard = [
        [InlineKeyboardButton("Coba Lagi", callback_data="retry_photo")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_photo(
        photo=open(file_path, "rb"),
        caption="Foto berhasil di-convert!",
        reply_markup=reply_markup
    )

# Handler tombol inline
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = str(query.from_user.id)
    data = load_data()

    if query.data == "retry_start":
        keyboard = [
            [InlineKeyboardButton("Coba Lagi", callback_data="retry_start")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.reply_text(
            "Halo! Kirim foto untuk saya convert.",
            reply_markup=reply_markup
        )

    elif query.data == "retry_photo":
        if user_id in data and data[user_id]["history"]:
            last_entry = data[user_id]["history"][-1]
            file_path = last_entry["file_path"]

            keyboard = [
                [InlineKeyboardButton("Coba Lagi", callback_data="retry_photo")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await query.message.reply_photo(
                photo=open(file_path, "rb"),
                caption="Foto terakhir diulang!",
                reply_markup=reply_markup
            )
        else:
            await query.message.reply_text("Belum ada foto sebelumnya.")

def main():
    TOKEN = os.getenv("BOT_TOKEN")  # Ambil token dari Railway variable
    if not TOKEN:
        raise ValueError("BOT_TOKEN tidak ditemukan di environment variables.")

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(CallbackQueryHandler(button_handler))

    app.run_polling()

if __name__ == "__main__":
    main()
