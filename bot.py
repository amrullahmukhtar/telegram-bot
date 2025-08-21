import os
import json
import uuid
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    filters, ContextTypes, CallbackQueryHandler
)

# File untuk menyimpan data user
DATA_FILE = "data.json"


# ---------------------------
# Utility untuk load/simpan data
# ---------------------------
def load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, "r") as f:
        return json.load(f)


def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)


# ---------------------------
# Command /start
# ---------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    data = load_data()

    if user_id not in data:
        data[user_id] = {"history": []}
        save_data(data)

    keyboard = [[InlineKeyboardButton("Coba Lagi", callback_data="retry_start")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        f"Halo {update.effective_user.first_name}! 👋\n\n"
        "Saya adalah bot demo. Kirimkan teks atau foto untuk disimpan ke history.",
        reply_markup=reply_markup
    )


# ---------------------------
# Command /help
# ---------------------------
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "/start - Mulai bot\n"
        "/help - Bantuan\n"
        "/history - Lihat riwayat pesan/foto kamu"
    )


# ---------------------------
# Command /history
# ---------------------------
async def history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    data = load_data()

    if user_id not in data or not data[user_id]["history"]:
        await update.message.reply_text("Belum ada history tersimpan.")
        return

    text_history = "📜 Riwayat kamu:\n\n"
    for i, item in enumerate(data[user_id]["history"], start=1):
        if "text" in item:
            text_history += f"{i}. (Teks) {item['text']}\n"
        elif "file_path" in item:
            text_history += f"{i}. (Foto) {item['file_id']}\n"

    await update.message.reply_text(text_history)


# ---------------------------
# Handler teks
# ---------------------------
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    text = update.message.text

    data = load_data()
    if user_id not in data:
        data[user_id] = {"history": []}

    data[user_id]["history"].append({"text": text})
    save_data(data)

    keyboard = [[InlineKeyboardButton("Coba Lagi", callback_data="retry_text")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        f"Teks berhasil disimpan!\n\nIsi: {text}",
        reply_markup=reply_markup
    )


# ---------------------------
# Handler foto
# ---------------------------
async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    data = load_data()

    photo = update.message.photo[-1]
    file = await photo.get_file()
    file_id = str(uuid.uuid4()) + ".jpg"
    file_path = f"downloads/{file_id}"

    os.makedirs("downloads", exist_ok=True)
    await file.download_to_drive(file_path)

    if user_id not in data:
        data[user_id] = {"history": []}

    data[user_id]["history"].append({"file_id": file_id, "file_path": file_path})
    save_data(data)

    keyboard = [[InlineKeyboardButton("Coba Lagi", callback_data="retry_photo")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_photo(
        photo=open(file_path, "rb"),
        caption="Foto berhasil disimpan!",
        reply_markup=reply_markup
    )


# ---------------------------
# Inline button handler
# ---------------------------
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = str(query.from_user.id)
    data = load_data()

    if query.data == "retry_start":
        keyboard = [[InlineKeyboardButton("Coba Lagi", callback_data="retry_start")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.reply_text("Silakan kirim pesan atau foto lagi.", reply_markup=reply_markup)

    elif query.data == "retry_text":
        if user_id in data and data[user_id]["history"]:
            last_entry = next((x for x in reversed(data[user_id]["history"]) if "text" in x), None)
            if last_entry:
                await query.message.reply_text(f"Ulang teks terakhir:\n{last_entry['text']}")
            else:
                await query.message.reply_text("Tidak ada teks di history.")

    elif query.data == "retry_photo":
        if user_id in data and data[user_id]["history"]:
            last_entry = next((x for x in reversed(data[user_id]["history"]) if "file_path" in x), None)
            if last_entry:
                await query.message.reply_photo(
                    photo=open(last_entry["file_path"], "rb"),
                    caption="Ulang foto terakhir!"
                )
            else:
                await query.message.reply_text("Tidak ada foto di history.")


# ---------------------------
# Main
# ---------------------------
def main():
    TOKEN = os.getenv("BOT_TOKEN")
    if not TOKEN:
        raise ValueError("BOT_TOKEN tidak ditemukan di Railway environment!")

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("history", history))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(CallbackQueryHandler(button_handler))

    app.run_polling()


if __name__ == "__main__":
    main()
