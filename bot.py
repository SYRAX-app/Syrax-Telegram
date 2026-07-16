import os
import json
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

# ========== Ma'lumotlarni saqlash (subscriber ro'yxati) ==========
DATA_FILE = "subscribers.json"

def load_subscribers():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r") as f:
                return set(json.load(f))
        except Exception:
            return set()
    return set()

def save_subscribers():
    try:
        with open(DATA_FILE, "w") as f:
            json.dump(list(SUBSCRIBERS), f)
    except Exception as e:
        print(f"Subscriberlarni saqlashda xato: {e}")

SUBSCRIBERS = load_subscribers()

# ========== Holatlar ==========
LANG = {}
forwarded_messages = {}   # admin_message_id -> foydalanuvchi chat_id
admin_state = {}          # ADMIN_ID -> "broadcast" yoki None

LANG_BUTTONS = ["🇺🇿 O'zbekcha", "🇷🇺 Русский", "🇬🇧 English"]

# ========== Menyular ==========
def lang_menu():
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=3)
    markup.add(KeyboardButton(LANG_BUTTONS[0]), KeyboardButton(LANG_BUTTONS[1]), KeyboardButton(LANG_BUTTONS[2]))
    return markup

def admin_menu():
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(KeyboardButton("📢 Barchaga xabar yuborish"), KeyboardButton("📊 Statistika"))
    return markup

def cancel_menu():
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    markup.add(KeyboardButton("❌ Bekor qilish"))
    return markup

# ========== Yordamchi funksiyalar ==========
def get_ack_text(lang):
    if lang == 'uz':
        return "✅ Xabaringiz qabul qilindi!\n\n⏳ Tez orada javob beramiz."
    elif lang == 'ru':
        return "✅ Ваше сообщение получено!\n\n⏳ Мы скоро ответим."
    else:
        return "✅ Your message has been received!\n\n⏳ We will reply soon."

def user_header(message):
    user = message.from_user
    info = f"👤 {user.first_name or ''} {user.last_name or ''}".strip()
    if user.username:
        info += f" (@{user.username})"
    info += f"\n🆔 ID: {message.chat.id}\n\n"
    return info

def copy_media_to(chat_id, message, caption=None):
    """Xabarni (matn yoki media) berilgan chat_id'ga yuboradi, yuborilgan xabarni qaytaradi."""
    ct = message.content_type
    if ct == 'text':
        return bot.send_message(chat_id, message.text)
    elif ct == 'photo':
        return bot.send_photo(chat_id, message.photo[-1].file_id, caption=caption)
    elif ct == 'video':
        return bot.send_video(chat_id, message.video.file_id, caption=caption)
    elif ct == 'audio':
        return bot.send_audio(chat_id, message.audio.file_id, caption=caption)
    elif ct == 'document':
        return bot.send_document(chat_id, message.document.file_id, caption=caption)
    elif ct == 'voice':
        return bot.send_voice(chat_id, message.voice.file_id, caption=caption)
    elif ct == 'video_note':
        return bot.send_video_note(chat_id, message.video_note.file_id)
    elif ct == 'sticker':
        return bot.send_sticker(chat_id, message.sticker.file_id)
    else:
        return bot.send_message(chat_id, "[qo'llab-quvvatlanmaydigan xabar turi]")

ALL_CONTENT_TYPES = ['text', 'photo', 'video', 'audio', 'document', 'voice', 'video_note', 'sticker']

# ========== /start ==========
@bot.message_handler(commands=['start'])
def start(message):
    SUBSCRIBERS.add(message.chat.id)
    save_subscribers()
    if message.chat.id == ADMIN_ID:
        bot.send_message(message.chat.id, "👑 Admin panelga xush kelibsiz!", reply_markup=admin_menu())
        return
    bot.send_message(
        message.chat.id,
        "🇺🇿 Tilni tanlang / Выберите язык / Choose language:",
        reply_markup=lang_menu()
    )

# ========== /admin ==========
@bot.message_handler(commands=['admin'])
def admin_panel(message):
    if message.chat.id != ADMIN_ID:
        return
    admin_state[ADMIN_ID] = None
    bot.send_message(message.chat.id, "👑 Admin panel:", reply_markup=admin_menu())

# ========== Barcha xabarlarni bitta joyda boshqaramiz ==========
@bot.message_handler(content_types=ALL_CONTENT_TYPES)
def main_handler(message):
    chat_id = message.chat.id

    # ---------- ADMIN oqimi ----------
    if chat_id == ADMIN_ID:
        text = message.text if message.content_type == 'text' else None

        # Bekor qilish
        if text == "❌ Bekor qilish":
            admin_state[ADMIN_ID] = None
            bot.send_message(ADMIN_ID, "Bekor qilindi.", reply_markup=admin_menu())
            return

        # Broadcast tugmasi bosildi
        if text == "📢 Barchaga xabar yuborish":
            admin_state[ADMIN_ID] = "broadcast"
            bot.send_message(
                ADMIN_ID,
                "✉️ Barcha obunachilarga yubormoqchi bo'lgan xabaringizni yuboring.\n"
                "(matn, rasm, video, ovozli xabar — barchasi qo'llab-quvvatlanadi)",
                reply_markup=cancel_menu()
            )
            return

        # Statistika tugmasi bosildi
        if text == "📊 Statistika":
            bot.send_message(ADMIN_ID, f"👥 Jami obunachilar: {len(SUBSCRIBERS)} ta", reply_markup=admin_menu())
            return

        # Broadcast holatida — kelgan xabarni hammaga yuboramiz
        if admin_state.get(ADMIN_ID) == "broadcast":
            admin_state[ADMIN_ID] = None
            sent_count = 0
            failed_count = 0
            for uid in list(SUBSCRIBERS):
                if uid == ADMIN_ID:
                    continue
                try:
                    copy_media_to(uid, message)
                    sent_count += 1
                except Exception:
                    failed_count += 1
            bot.send_message(
                ADMIN_ID,
                f"✅ Xabar yuborildi!\n📤 Yuborildi: {sent_count} ta\n❌ Yuborilmadi: {failed_count} ta",
                reply_markup=admin_menu()
            )
            return

        # Adminning oddiy foydalanuvchiga reply qilishi
        if message.reply_to_message is not None:
            user_chat_id = forwarded_messages.get(message.reply_to_message.message_id)
            if user_chat_id:
                try:
                    copy_media_to(user_chat_id, message, caption=message.caption)
                    bot.send_message(ADMIN_ID, "✅ Javobingiz yuborildi.")
                except Exception as e:
                    bot.send_message(ADMIN_ID, f"❌ Xatolik: {e}")
            else:
                bot.send_message(ADMIN_ID, "⚠️ Bu xabarga javob yuborib bo'lmaydi (foydalanuvchi topilmadi).")
            return

        # Boshqa hech narsaga to'g'ri kelmasa — menyuni eslatamiz
        bot.send_message(ADMIN_ID, "👑 Admin panel:", reply_markup=admin_menu())
        return

    # ---------- ODDIY FOYDALANUVCHI oqimi ----------
    SUBSCRIBERS.add(chat_id)
    save_subscribers()

    # Til tanlash
    if message.content_type == 'text' and message.text in LANG_BUTTONS:
        if message.text == LANG_BUTTONS[0]:
            LANG[chat_id] = 'uz'
            bot.send_message(chat_id, "🇺🇿 Siz O'zbek tilini tanladingiz.\n\n👋 Xush kelibsiz! Savolingizni yozing, tez orada javob beramiz.")
        elif message.text == LANG_BUTTONS[1]:
            LANG[chat_id] = 'ru'
            bot.send_message(chat_id, "🇷🇺 Вы выбрали Русский язык.\n\n👋 Добро пожаловать! Напишите ваш вопрос, мы скоро ответим.")
        else:
            LANG[chat_id] = 'en'
            bot.send_message(chat_id, "🇬🇧 You selected English language.\n\n👋 Welcome! Write your question, we will reply soon.")
        return

    # Oddiy xabar (matn yoki media) — adminga forward qilamiz
    lang = LANG.get(chat_id, 'uz')
    bot.send_message(chat_id, get_ack_text(lang))

    header = user_header(message)
    try:
        if message.content_type == 'text':
            sent = bot.send_message(ADMIN_ID, header + "✉️ " + message.text)
        else:
            caption = header + (message.caption or "")
            sent = copy_media_to(ADMIN_ID, message, caption=caption)
        forwarded_messages[sent.message_id] = chat_id
    except Exception as e:
        print(f"Adminga yuborishda xato: {e}")

if __name__ == "__main__":
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()

    print("🤖 Bot ishga tushdi...")
    bot.infinity_polling()
