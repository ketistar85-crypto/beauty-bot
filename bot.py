import os
import requests
from flask import Flask, request

TOKEN = os.environ.get("TOKEN")
BASE_URL = "https://platform-api.max.ru"

app = Flask(__name__)

def send_message(chat_id, text):
    """Отправка сообщения через API MAX"""
    # chat_id передаётся в query-параметре
    url = f"{BASE_URL}/messages?chat_id={chat_id}"
    headers = {"Authorization": TOKEN, "Content-Type": "application/json"}
    data = {"body": {"text": text}}
    
    try:
        r = requests.post(url, json=data, headers=headers)
        print(f"📤 Ответ MAX: {r.status_code} - {r.text}")
        return r.status_code == 200
    except Exception as e:
        print(f"Ошибка отправки: {e}")
        return False

@app.route('/webhook', methods=['POST'])
def webhook():
    update = request.json
    print("📥 Получен вебхук:", update)
    
    if update and update.get('update_type') == 'message_created':
        msg = update.get('message', {})
        chat_id = msg.get('recipient', {}).get('chat_id')
        text = msg.get('body', {}).get('text', '')
        
        if chat_id:
            send_message(chat_id, f"✅ Ты написал: {text}")
    
    # Возвращаем ПУСТОЙ ответ с кодом 200
    return '', 200

@app.route('/')
def index():
    return "Bot is running!"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
