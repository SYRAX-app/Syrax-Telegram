import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton

# ========== TOKEN ==========
TOKEN = "8956591210:AAGRDfVvG3Mg7uDSxJSkFMrEaEb4B4swcfw"
bot = telebot.TeleBot(TOKEN)

# ========== Tillar ==========
LANG = {}

# ========== Til menyusi ==========
def lang_menu():
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=3)
    btn1 = KeyboardButton("🇺🇿 O'zbekcha")
    btn2 = KeyboardButton("🇷🇺 Русский")
    btn3 = KeyboardButton("🇬🇧 English")
    markup.add(btn1, btn2, btn3)
    return markup

# ========== /start ==========
@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(
        message.chat.id,
        "🇺🇿 Tilni tanlang / Выберите язык / Choose language:",
        reply_markup=lang_menu()
    )

# ========== Til tanlash ==========
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

# ========== Boshqa xabarlar ==========
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

# ========== Botni ishga tushirish ==========
print("🤖 Bot ishga tushdi...")
bot.polling()