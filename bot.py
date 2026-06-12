import os
import sys
import requests
from flask import Flask, request
import logging
import time

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    stream=sys.stdout,
    force=True
)

TOKEN = os.environ.get("TOKEN")
BASE_URL = "https://platform-api.max.ru"

app = Flask(__name__)

def send_message(chat_id, text, recipient_user_id=None):
    """Отправка сообщения через API MAX"""
    if not TOKEN:
        logging.error("Токен не найден!")
        return False
        
    url = f"{BASE_URL}/messages?chat_id={chat_id}"
    headers = {
        "Authorization": TOKEN, 
        "Content-Type": "application/json"
    }
    
    # Полная структура как в вебхуке
    data = {
        "recipient": {
            "chat_id": chat_id,
            "chat_type": "dialog",
            "user_id": recipient_user_id if recipient_user_id else 313227351  # из вебхука
        },
        "body": {
            "text": text,
            "mid": f"mid.{int(time.time() * 1000)}",
            "seq": int(time.time() * 1000000)
        },
        "sender": {
            "is_bot": True
        },
        "timestamp": int(time.time() * 1000)
    }
    
    logging.info(f"Отправка в чат {chat_id}: {text}")
    logging.info(f"Данные: {data}")
    
    try:
        r = requests.post(url, json=data, headers=headers, timeout=10)
        logging.info(f"Ответ MAX: {r.status_code} - {r.text}")
        
        if r.status_code != 200:
            logging.error(f"Ошибка API: {r.status_code}")
            try:
                logging.error(f"Детали: {r.json()}")
            except:
                pass
            return False
        return True
    except Exception as e:
        logging.error(f"Ошибка отправки: {e}")
        return False

@app.route('/webhook', methods=['POST'])
def webhook():
    logging.info("=" * 50)
    logging.info("ПОЛУЧЕН ВЕБХУК!")
    
    try:
        update = request.json
    except Exception as e:
        logging.error(f"Ошибка парсинга JSON: {e}")
        return '', 200
    
    if not update:
        return '', 200
        
    update_type = update.get('update_type')
    
    if update_type == 'message_created':
        msg = update.get('message', {})
        chat_id = msg.get('recipient', {}).get('chat_id')
        user_id = msg.get('recipient', {}).get('user_id')
        text = msg.get('body', {}).get('text', '')
        
        logging.info(f"chat_id: {chat_id}, text: {text}")
        
        if chat_id and text:
            result = send_message(chat_id, f"✅ Ты написал: {text}", user_id)
            logging.info(f"Результат: {'Успешно' if result else 'Ошибка'}")
    
    elif update_type == 'bot_started':
        chat_id = update.get('chat_id')
        user_id = update.get('user_id')
        if chat_id:
            send_message(chat_id, "👋 Привет! Я бот. Напиши мне что-нибудь!", user_id)
    
    return '', 200

@app.route('/test', methods=['GET'])
def test():
    return {
        "status": "running",
        "token_exists": bool(TOKEN)
    }

@app.route('/')
def index():
    return "Bot is running!"

if __name__ == '__main__':
    logging.info("ЗАПУСК БОТА")
    app.run(host='0.0.0.0', port=8080)
