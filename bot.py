import telebot
import google.generativeai as genai
from PIL import Image, ImageDraw, ImageFont
import io
from datetime import datetime
import textwrap
import httpx  # Нужно для работы через прокси

# --- НАСТРОЙКИ ---
TOKEN = os.getenv("BOT_TOKEN")
# Если у тебя есть прокси (SOCKS5 или HTTP), впиши его сюда. 
# Без него итальянский ключ в РФ работать не будет.
PROXY_URL = "http://username:password@proxy_address:port" 

bot = telebot.TeleBot(TOKEN)

# ✅ НАСТРОЙКА GEMINI
# Render сам подставит твой итальянский ключ вместо этой команды
genai.configure(api_key=os.getenv("GEMINI_KEY"))

# Самая актуальная и быстрая модель на сегодня
model = genai.GenerativeModel('gemini-1.5-flash')

cache = {}

@bot.message_handler(commands=['start'])
def start(message):
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("🖼️ Картинка", "📝 Текст")
    markup.add("🔥 Сюрприз")
    
    bot.send_message(message.chat.id,
        "🎉 ГЕМИНИ БОТ ИЗ ИТАЛИИ ОНЛАЙН!\n\n"
        "🖼️ Картинка — синяя с ответом\n"
        "📝 Текст — просто ответ\n"
        "🔥 Сюрприз — рандомный ответ\n\n"
        "Пиши любой вопрос! 🚀", 
        reply_markup=markup)

@bot.message_handler(func=lambda m: True)
def handle_message(message):
    # Улучшенная логика выбора режима
    text_lower = message.text.lower()
    mode = "🖼️ Картинка" if "картинк" in text_lower else "📝 Текст"
    
    try:
        if message.text in cache:
            answer = cache[message.text]
        else:
            # Отправляем запрос в Gemini
            response = model.generate_content(message.text)
            answer = response.text[:500] # Увеличил лимит для текста
            cache[message.text] = answer
        
        if "сюрприз" in text_lower:
            send_surprise(message)
        elif mode == "🖼️ Картинка":
            send_image(message, answer)
        else:
            bot.reply_to(message, f"🤖 *Gemini AI*:\n\n{answer}", parse_mode='Markdown')
            
    except Exception as e:
        error_msg = str(e)
        if "403" in error_msg:
            bot.reply_to(message, "❌ Ошибка 403: Google блокирует российский IP. Нужен прокси в коде!")
        else:
            bot.reply_to(message, f"❌ Ошибка: `{error_msg[:100]}`")

def send_image(message, text):
    # Твой крутой синий градиент
    img = Image.new('RGB', (640, 480), color='#1E3A8A')
    draw = ImageDraw.Draw(img)
    
    for i in range(480):
        r = int(30 + i * 0.15)
        g = int(58 + i * 0.15)
        b = int(138 + i * 0.2)
        draw.line([(0, i), (640, i)], fill=(r, g, b))
    
    # Пытаемся загрузить шрифт, если нет - берем стандартный
    try:
        font_title = ImageFont.truetype("arial.ttf", 36)
        font_text = ImageFont.truetype("arial.ttf", 24)
    except:
        font_title = ImageFont.load_default()
        font_text = ImageFont.load_default()
    
    lines = textwrap.wrap(text, width=40)
    
    draw.text((40, 30), "🤖 GEMINI AI • ITALY", fill='white', font=font_title)
    
    y = 120
    for line in lines[:10]:
        draw.text((40, y), line, fill='white', font=font_text)
        y += 35
    
    draw.text((40, 430), f"⏰ {datetime.now().strftime('%H:%M:%S')}", fill='#94A3B8')
    
    bio = io.BytesIO()
    img.save(bio, 'PNG')
    bio.seek(0)
    bot.send_photo(message.chat.id, bio, caption="✨ *Результат из Италии!* 🇮🇹", parse_mode='Markdown')

def send_surprise(message):
    surprises = ["🌟 Секретный режим!", "🎲 Рандом!", "⚡ Турбо!", "💎 Premium!"]
    gift = surprises[hash(message.text) % 4]
    bot.send_message(message.chat.id, f"{gift}\n\nТвой запрос обработан особым образом! ✨")

print("🎉 БОТ ЗАПУЩЕН!")

bot.infinity_polling()
