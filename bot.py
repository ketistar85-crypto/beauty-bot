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
        
    # chat_id в теле запроса, не в URL
    url = f"{BASE_URL}/messages"
    headers = {
        "Authorization": TOKEN, 
        "Content-Type": "application/json"
    }
    data = {
        "chat_id": chat_id,
        "body": {"text": text}
    }
    
    logging.info(f"Отправка в чат {chat_id}: {text}")
    logging.info(f"URL: {url}")
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
        logging.info(f"Структура вебхука: {update}")
    except Exception as e:
        logging.error(f"Ошибка парсинга JSON: {e}")
        return '', 200
    
    if not update:
        logging.warning("Пустой вебхук")
        return '', 200
        
    update_type = update.get('update_type')
    logging.info(f"Тип обновления: {update_type}")
    
    if update_type == 'message_created':
        msg = update.get('message', {})
        chat_id = msg.get('recipient', {}).get('chat_id')
        text = msg.get('body', {}).get('text', '')
        
        logging.info(f"chat_id: {chat_id}")
        logging.info(f"text: {text}")
        
        if chat_id and text:
            result = send_message(chat_id, f"✅ Ты написал: {text}")
            logging.info(f"Результат отправки: {'Успешно' if result else 'Ошибка'}")
        elif not chat_id:
            logging.error("chat_id не найден!")
        elif not text:
            logging.warning("Текст сообщения пустой")
    else:
        logging.info(f"Пропускаем обновление типа: {update_type}")
    
    return '', 200

@app.route('/test', methods=['GET'])
def test():
    return {
        "status": "running",
        "token_exists": bool(TOKEN),
        "base_url": BASE_URL
    }

@app.route('/')
def index():
    return "Bot is running!"

if __name__ == '__main__':
    logging.info("=" * 50)
    logging.info("ЗАПУСК БОТА")
    logging.info(f"Токен установлен: {bool(TOKEN)}")
    logging.info("=" * 50)
    app.run(host='0.0.0.0', port=8080)
