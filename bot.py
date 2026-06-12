import os
import requests
from flask import Flask, request, jsonify

TOKEN = os.environ.get("TOKEN")
BASE_URL = "https://platform-api.max.ru"

app = Flask(__name__)

def send_message(chat_id, text):
    url = f"{BASE_URL}/messages"
    headers = {"Authorization": TOKEN, "Content-Type": "application/json"}
    data = {"recipient": {"chat_id": chat_id}, "body": {"text": text}}
    try:
        r = requests.post(url, json=data, headers=headers)
        print(f"📤 Ответ: {r.status_code}")
        return r.status_code == 200
    except Exception as e:
        print(f"Ошибка: {e}")
        return False

@app.route('/webhook', methods=['POST'])
def webhook():
    update = request.json
    print("📥 Входящий вебхук:", update)
    if update and update.get('update_type') == 'message_created':
        msg = update.get('message', {})
        chat_id = msg.get('recipient', {}).get('chat_id')
        text = msg.get('body', {}).get('text', '')
        if chat_id:
            send_message(chat_id, f"✅ Ты написал: {text}")
    return jsonify({'status': 'ok'}), 200

@app.route('/')
def index():
    return "Bot is running!"

# Bothost сам запускает приложение
