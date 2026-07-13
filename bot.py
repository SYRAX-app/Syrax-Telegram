import os
import threading
from flask import Flask
import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton

# ========== TOKEN va ADMIN ==========
TOKEN = os.environ.get("TOKEN")
if not TOKEN:
    raise ValueError("TOKEN environment variable topilmadi! Render > Environment bo'limiga qo'shing.")

ADMIN_ID = int(os.environ.get("ADMIN_ID", "8501518219"))

bot = telebot.TeleBot(TOKEN)

# ========== Flask (Render portni ochish uchun) ==========
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot ishlayapti!"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

# ========== Tillar ==========
LANG = {}

# adminga yuborilgan xabar_id -> foydalanuvchi chat_id (admin reply qilganda kimga yuborishni bilish uchun)
forwarded_messages = {}

def lang_menu():
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=3)
    btn1 = KeyboardButton("🇺🇿 O'zbekcha")
    btn2 = KeyboardButton("🇷🇺 Русский")
    btn3 = KeyboardButton("🇬🇧 English")
    markup.add(btn1, btn2, btn3)
    return markup

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(
        message.chat.id,
        "🇺🇿 Tilni tanlang / Выберите язык / Choose language:",
        reply_markup=lang_menu()
    )

@bot.message_handler(func=lambda message: message.text in ["🇺🇿 O'zbekcha", "🇷🇺 Русский", "🇬🇧 English"])
def set_lang(message):
    if message.text == "🇺🇿 O'zbekcha":
        LANG[message.chat.id] = 'uz'
        bot.send_message(
            message.chat.id,
            "🇺🇿 Siz O'zbek tilini tanladingiz.\n\n"
            "👋 Xush kelibsiz! Savolingizni yozing, tez orada javob beramiz."
        )
    elif message.text == "🇷🇺 Русский":
        LANG[message.chat.id] = 'ru'
        bot.send_message(
            message.chat.id,
            "🇷🇺 Вы выбрали Русский язык.\n\n"
            "👋 Добро пожаловать! Напишите ваш вопрос, мы скоро ответим."
        )
    else:
        LANG[message.chat.id] = 'en'
        bot.send_message(
            message.chat.id,
            "🇬🇧 You selected English language.\n\n"
            "👋 Welcome! Write your question, we will reply soon."
        )

# ========== ADMIN javob yozganda (reply qilganda) ==========
@bot.message_handler(func=lambda message: message.chat.id == ADMIN_ID and message.reply_to_message is not None)
def admin_reply(message):
    replied_msg_id = message.reply_to_message.message_id
    user_chat_id = forwarded_messages.get(replied_msg_id)

    if user_chat_id:
        try:
            bot.send_message(user_chat_id, message.text)
            bot.send_message(ADMIN_ID, "✅ Javobingiz yuborildi.")
        except Exception as e:
            bot.send_message(ADMIN_ID, f"❌ Xatolik: {e}")
    else:
        bot.send_message(ADMIN_ID, "⚠️ Bu xabarga javob yuborib bo'lmaydi (foydalanuvchi topilmadi).")

# ========== Foydalanuvchi xabar yozganda ==========
@bot.message_handler(func=lambda message: True)
def reply(message):
    # Agar bu admin bo'lsa va reply bo'lmasa, e'tiborsiz qoldiramiz
    if message.chat.id == ADMIN_ID:
        return

    lang = LANG.get(message.chat.id, 'uz')

    if lang == 'uz':
        bot.send_message(
            message.chat.id,
            "✅ Xabaringiz qabul qilindi!\n\n"
            "⏳ Tez orada javob beramiz."
        )
    elif lang == 'ru':
        bot.send_message(
            message.chat.id,
            "✅ Ваше сообщение получено!\n\n"
            "⏳ Мы скоро ответим."
        )
    else:
        bot.send_message(
            message.chat.id,
            "✅ Your message has been received!\n\n"
            "⏳ We will reply soon."
        )

    # Foydalanuvchi haqida ma'lumot va xabarni adminga forward qilamiz
    user = message.from_user
    user_info = f"👤 {user.first_name or ''} {user.last_name or ''}".strip()
    if user.username:
        user_info += f" (@{user.username})"
    user_info += f"\n🆔 ID: {message.chat.id}\n\n"

    sent = bot.send_message(ADMIN_ID, user_info + "✉️ " + (message.text or "[matn emas xabar]"))
    # Shu xabar ID'sini foydalanuvchi chat_id bilan bog'laymiz, admin reply qilganda topish uchun
    forwarded_messages[sent.message_id] = message.chat.id

if __name__ == "__main__":
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()

    print("🤖 Bot ishga tushdi...")
    bot.infinity_polling()
