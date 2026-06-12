import os
import sys
import requests
from flask import Flask, request
import logging

logging.basicConfig(level=logging.INFO)

TOKEN = os.environ.get("TOKEN")
BASE_URL = "https://platform-api.max.ru"

app = Flask(__name__)

services = {
    "1": {"name": "Стрижка женская", "price": 1500},
    "2": {"name": "Стрижка мужская", "price": 800},
    "3": {"name": "Окрашивание", "price": 3500}
}

masters = {
    "1": {"name": "Анна"},
    "2": {"name": "Елена"}
}

def send_message(chat_id, text, buttons=None):
    url = f"{BASE_URL}/messages?chat_id={chat_id}"
    headers = {"Authorization": TOKEN, "Content-Type": "application/json"}
    data = {"text": text}
    
    if buttons:
        data["attachments"] = [{
            "type": "inline_keyboard",
            "payload": {"inline_keyboard": buttons}
        }]
    
    requests.post(url, json=data, headers=headers)

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
                [{"text": "📅 Записаться", "callback_data": "booking"}],
                [{"text": "📋 Мои записи", "callback_data": "my_appointments"}],
                [{"text": "❌ Отменить запись", "callback_data": "cancel"}]
            ]
            send_message(chat_id, "🌸 Добро пожаловать! Выберите действие:", buttons)
    
    elif update.get('update_type') == 'callback_query':
        data = update.get('data', {})
        chat_id = data.get('chat_id')
        callback_data = data.get('callback_data')
        
        if callback_data == 'booking':
            buttons = [[{"text": s['name'], "callback_data": f"service_{k}"}] for k, s in services.items()]
            send_message(chat_id, "💇 Выберите услугу:", buttons)
        
        elif callback_data.startswith('service_'):
            service_id = callback_data.split('_')[1]
            buttons = [[{"text": m['name'], "callback_data": f"master_{k}"}] for k, m in masters.items()]
            send_message(chat_id, "👩‍🎨 Выберите мастера:", buttons)
        
        elif callback_data.startswith('master_'):
            send_message(chat_id, "✅ Вы записаны! Спасибо!")
        
        # Ответ на callback
        callback_url = f"{BASE_URL}/callbacks"
        callback_headers = {"Authorization": TOKEN, "Content-Type": "application/json"}
        requests.post(callback_url, json={"id": update.get('id')}, headers=callback_headers)
    
    return '', 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
