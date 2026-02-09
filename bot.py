import os, telebot, threading, http.server, io, textwrap
import google.generativeai as genai
from PIL import Image, ImageDraw

# 1. ОБМАНКА
def run_dummy_server():
    port = int(os.environ.get("PORT", 10000))
    http.server.HTTPServer(('', port), http.server.SimpleHTTPRequestHandler).serve_forever()
threading.Thread(target=run_dummy_server, daemon=True).start()

# 2. НАСТРОЙКИ (с защитой от 404)
bot = telebot.TeleBot(os.getenv("BOT_TOKEN"))
genai.configure(api_key=os.getenv("GEMINI_KEY"))

# Список названий моделей, которые мы будем перебирать
MODEL_NAMES = ['gemini-1.5-flash', 'gemini-1.5-pro', 'gemini-pro']

def get_ai_response(prompt):
    for name in MODEL_NAMES:
        try:
            m = genai.GenerativeModel(name)
            res = m.generate_content(prompt)
            return res.text
        except Exception as e:
            if "404" in str(e): continue
            return f"Ошибка: {e}"
    return "Ни одна модель не доступна. Проверь API ключ в настройках Render!"

# 3. КАРТИНКА NANO BANANA
def create_card(text):
    img = Image.new('RGB', (800, 400), color=(15, 15, 15))
    draw = ImageDraw.Draw(img)
    draw.rectangle([10, 10, 790, 390], outline=(255, 215, 0), width=3)
    lines = textwrap.wrap(text, width=40)
    y = 60
    for line in lines[:6]:
        draw.text((40, y), line, fill=(255, 255, 255))
        y += 45
    draw.text((600, 350), "Nano Banana 🍌", fill=(255, 215, 0))
    bio = io.BytesIO(); img.save(bio, 'PNG'); bio.seek(0)
    return bio

# 4. ОБРАБОТЧИКИ
@bot.message_handler(commands=['image'])
def img_h(message):
    txt = message.text.replace('/image', '').strip()
    if not txt: return bot.reply_to(message, "Напиши текст!")
    bot.send_chat_action(message.chat.id, 'upload_photo')
    response_text = get_ai_response(f"Опиши кратко для картинки: {txt}")
    bot.send_photo(message.chat.id, create_card(response_text))

@bot.message_handler(func=lambda m: True)
def chat_h(message):
    bot.reply_to(message, get_ai_response(message.text))

if __name__ == "__main__":
    print("🎉 СИСТЕМА ЗАПУЩЕНА")
    bot.infinity_polling(timeout=90, long_polling_timeout=30)


