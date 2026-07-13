import os
import threading
from flask import Flask
import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton

# ========== TOKEN ==========
# Tokenni Render'da Environment Variable sifatida qo'shing! Kodga yozmang.
TOKEN = os.environ.get("TOKEN")
if not TOKEN:
    raise ValueError("TOKEN environment variable topilmadi! Render > Environment bo'limiga qo'shing.")

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

@bot.message_handler(func=lambda message: True)
def reply(message):
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

if __name__ == "__main__":
    # Flask serverni alohida thread'da ishga tushiramiz (Render port talabini qondirish uchun)
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()

    print("🤖 Bot ishga tushdi...")
    bot.infinity_polling()
