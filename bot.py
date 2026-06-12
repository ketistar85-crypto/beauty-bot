import os
import sys
import requests
from flask import Flask, request
import logging

logging.basicConfig(level=logging.INFO)

TOKEN = os.environ.get("TOKEN")
BASE_URL = "https://platform-api.max.ru"

app = Flask(__name__)

def send_message(chat_id, text, buttons=None):
    url = f"{BASE_URL}/messages?chat_id={chat_id}"
    headers = {"Authorization": TOKEN, "Content-Type": "application/json"}
    
    data = {"text": text}
    
    if buttons:
        data["attachments"] = [
            {
                "type": "inline_keyboard",
                "payload": {
                    "buttons": buttons
                }
            }
        ]
    
    r = requests.post(url, json=data, headers=headers)
    logging.info(f"Ответ: {r.status_code} - {r.text}")

@app.route('/webhook', methods=['POST'])
def webhook():
    update = request.json
    if not update:
        return '', 200
    
    if update.get('update_type') == 'message_created':
        msg = update.get('message', {})
        chat_id = msg.get('recipient', {}).get('chat_id')
        text = msg.get('body', {}).get('text', '')
        
        if text == '/start':
            buttons = [
                [
                    {"type": "callback", "text": "📅 Записаться", "payload": {"callback_data": "booking"}},
                    {"type": "callback", "text": "📋 Мои записи", "payload": {"callback_data": "my_appointments"}}
                ],
                [
                    {"type": "callback", "text": "❌ Отменить запись", "payload": {"callback_data": "cancel"}}
                ]
            ]
            send_message(chat_id, "🌸 Добро пожаловать! Выберите действие:", buttons)
        else:
            send_message(chat_id, f"✅ Ты написал: {text}")
    
    elif update.get('update_type') == 'callback_query':
        callback = update.get('data', {})
        chat_id = callback.get('chat_id')
        callback_data = callback.get('payload', {}).get('callback_data') if callback.get('payload') else None
        
        logging.info(f"Нажата кнопка: {callback_data}")
        
        if callback_data == 'booking':
            send_message(chat_id, "📅 Здесь будет запись")
        elif callback_data == 'my_appointments':
            send_message(chat_id, "📋 У вас пока нет записей")
        elif callback_data == 'cancel':
            send_message(chat_id, "❌ Нет записей для отмены")
        
        # Ответ на callback
        callback_url = f"{BASE_URL}/callbacks"
        callback_headers = {"Authorization": TOKEN, "Content-Type": "application/json"}
        requests.post(callback_url, json={"id": update.get('id')}, headers=callback_headers)
    
    return '', 200

@app.route('/')
def index():
    return "Bot is running!"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
