import os, telebot, threading, http.server, io, requests, urllib.parse
import google.generativeai as genai
from PIL import Image

# 1. СЕРВЕР-ОБМАНКА
def run_dummy_server():
    port = int(os.environ.get("PORT", 10000))
    http.server.HTTPServer(('', port), http.server.SimpleHTTPRequestHandler).serve_forever()
threading.Thread(target=run_dummy_server, daemon=True).start()

# 2. НАСТРОЙКИ (Добавлен принудительный REST транспорт)
bot = telebot.TeleBot(os.getenv("BOT_TOKEN"))
genai.configure(api_key=os.getenv("GEMINI_KEY"), transport='rest')

user_data = {}

# 3. ГЕНЕРАЦИЯ АРТА
def generate_art(prompt):
    clean_prompt = urllib.parse.quote(prompt)
    url = f"https://pollinations.ai/p/{clean_prompt}?width=1024&height=1024&model=flux&nologo=true"
    try:
        response = requests.get(url, timeout=60)
        if response.status_code == 200: return response.content
    except: return None
    return None

# 4. ОБРАБОТЧИКИ
@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "🍌 Nano Banana готова! Жду твое фото.")

@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    file_info = bot.get_file(message.photo[-1].file_id)
    downloaded_file = bot.download_file(file_info.file_path)
    user_data[message.chat.id] = {'photo_bytes': downloaded_file}
    bot.reply_to(message, "📸 Вижу тебя! Теперь напиши, какой образ создаем?")

@bot.message_handler(func=lambda m: m.chat.id in user_data)
def handle_prompt(message):
    chat_id = message.chat.id
    prompt_text = message.text
    photo_bytes = user_data[chat_id]['photo_bytes']
    
    bot.send_message(chat_id, "⚙️ Магия в процессе... Сохраняю твое лицо.")
    bot.send_chat_action(chat_id, 'upload_photo')

    try:
        # Используем самую стабильную версию модели
        model = genai.GenerativeModel(model_name="gemini-1.5-flash-latest")
        img = Image.open(io.BytesIO(photo_bytes))
        
        instruction = f"Describe this person's face. Then create a prompt for AI: the person with this face in the style of '{prompt_text}'. Keep only the face. No clothes or background from photo. English only."
        
        # Запрос к Gemini
        response = model.generate_content([instruction, img])
        
        art = generate_art(response.text)
        if art:
            bot.send_photo(chat_id, art, caption=f"Твой образ: {prompt_text} ✨")
        else:
            bot.reply_to(message, "❌ Художник занят, попробуй еще раз.")
            
    except Exception as e:
        bot.reply_to(message, f"Ошибка: {e}\n\nПохоже, нужно обновить API ключ.")
    finally:
        if chat_id in user_data: del user_data[chat_id]

@bot.message_handler(func=lambda m: True)
def chat(message):
    try:
        model = genai.GenerativeModel(model_name="gemini-1.5-flash-latest")
        res = model.generate_content(message.text)
        bot.reply_to(message, res.text)
    except:
        bot.reply_to(message, "Пришли фото — и начнем!")

if __name__ == "__main__":
    bot.infinity_polling(timeout=90)
