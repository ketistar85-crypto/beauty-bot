import requests
import json
from flask import Flask, request, jsonify

TOKEN = "ВАШ_ТОКЕН"
BASE_URL = "https://platform-api.max.ru"

app = Flask(__name__)

def send_message(chat_id, text):
    """Отправка сообщения через API MAX"""
    url = f"{BASE_URL}/messages"
    headers = {"Authorization": TOKEN, "Content-Type": "application/json"}
    data = {"recipient": {"chat_id": chat_id}, "body": {"text": text}}
    
    response = requests.post(url, json=data, headers=headers)
    return response.status_code == 200

@app.route('/webhook', methods=['POST'])
def webhook():
    """Обработка входящих вебхуков от MAX"""
    update = request.json
    
    if update.get('update_type') == 'message_created':
        msg = update.get('message', {})
        chat_id = msg.get('recipient', {}).get('chat_id')
        text = msg.get('body', {}).get('text', '')
        
        if chat_id:
            print(f"📩 Получено: {text}")
            send_message(chat_id, f"✅ Вы написали: {text}")
    
    return jsonify({'status': 'ok'}), 200

@app.route('/')
def index():
    return 'Бот работает!'

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)