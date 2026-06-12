import os
import sys
import requests
from flask import Flask, request
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    stream=sys.stdout,
    force=True
)

TOKEN = os.environ.get("TOKEN")
BASE_URL = "https://platform-api.max.ru"

app = Flask(__name__)

def send_message(chat_id, text):
    """Отправка сообщения через API MAX"""
    if not TOKEN:
        logging.error("Токен не найден!")
        return False
        
    # chat_id в query-параметре
    url = f"{BASE_URL}/messages?chat_id={chat_id}"
    headers = {
        "Authorization": TOKEN, 
        "Content-Type": "application/json"
    }
    
    # В теле только text (как в документации!)
    data = {
        "text": text
    }
    
    logging.info(f"Отправка: URL={url}")
    logging.info(f"Данные: {data}")
    
    try:
        r = requests.post(url, json=data, headers=headers, timeout=10)
        logging.info(f"Ответ MAX: {r.status_code} - {r.text}")
        
        if r.status_code == 200:
            logging.info("✅ Сообщение отправлено!")
            return True
        else:
            logging.error(f"❌ Ошибка: {r.status_code}")
            try:
                logging.error(f"Детали: {r.json()}")
            except:
                pass
            return False
    except Exception as e:
        logging.error(f"Ошибка: {e}")
        return False

@app.route('/webhook', methods=['POST'])
def webhook():
    logging.info("=" * 50)
    
    try:
        update = request.json
    except:
        return '', 200
    
    if not update:
        return '', 200
    
    update_type = update.get('update_type')
    
    if update_type == 'message_created':
        msg = update.get('message', {})
        chat_id = msg.get('recipient', {}).get('chat_id')
        text = msg.get('body', {}).get('text', '')
        
        logging.info(f"chat_id={chat_id}, text={text}")
        
        if chat_id and text:
            result = send_message(chat_id, f"✅ Ты написал: {text}")
            logging.info(f"Результат: {'✅' if result else '❌'}")
    
    elif update_type == 'bot_started':
        chat_id = update.get('chat_id')
        if chat_id:
            send_message(chat_id, "👋 Привет! Я бот. Напиши мне что-нибудь!")
    
    return '', 200

@app.route('/')
def index():
    return "Bot is running! v5"

if __name__ == '__main__':
    logging.info("ЗАПУСК БОТА v5")
    app.run(host='0.0.0.0', port=8080)
