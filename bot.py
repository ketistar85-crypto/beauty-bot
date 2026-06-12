import os
import sys
import requests
from flask import Flask, request
import logging
from datetime import datetime, timedelta

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    stream=sys.stdout,
    force=True
)

TOKEN = os.environ.get("TOKEN")
BASE_URL = "https://platform-api.max.ru"

app = Flask(__name__)

# Хранилище данных (временное, без БД)
services = {
    "1": {"name": "Стрижка женская", "duration": 60, "price": 1500},
    "2": {"name": "Стрижка мужская", "duration": 30, "price": 800},
    "3": {"name": "Окрашивание", "duration": 120, "price": 3500},
    "4": {"name": "Маникюр", "duration": 60, "price": 1200}
}

masters = {
    "1": {"name": "Анна", "specialization": "Парикмахер"},
    "2": {"name": "Елена", "specialization": "Колорист"},
    "3": {"name": "Мария", "specialization": "Маникюр"}
}

# Хранилище сессий пользователей (временное)
user_sessions = {}

def send_message(chat_id, text, keyboard=None):
    """Отправка сообщения с возможной клавиатурой"""
    url = f"{BASE_URL}/messages?chat_id={chat_id}"
    headers = {"Authorization": TOKEN, "Content-Type": "application/json"}
    data = {"text": text}
    
    if keyboard:
        data["keyboard"] = keyboard
    
    try:
        r = requests.post(url, json=data, headers=headers, timeout=10)
        logging.info(f"Ответ MAX: {r.status_code}")
        return r.status_code == 200
    except Exception as e:
        logging.error(f"Ошибка: {e}")
        return False

def send_main_menu(chat_id):
    """Отправляет главное меню с кнопками"""
    keyboard = {
        "buttons": [
            [{"text": "📅 Записаться", "callback_data": "booking"}],
            [{"text": "📋 Мои записи", "callback_data": "my_appointments"}],
            [{"text": "❌ Отменить запись", "callback_data": "cancel"}]
        ]
    }
    send_message(chat_id, "🌸 Добро пожаловать! Выберите действие:", keyboard)

def send_services_menu(chat_id):
    """Отправляет меню выбора услуги"""
    keyboard = {
        "buttons": []
    }
    for idx, service in services.items():
        keyboard["buttons"].append([{"text": f"{service['name']} — {service['price']} ₽", "callback_data": f"service_{idx}"}])
    
    send_message(chat_id, "💇 Выберите услугу:", keyboard)

def send_masters_menu(chat_id):
    """Отправляет меню выбора мастера"""
    keyboard = {
        "buttons": []
    }
    for idx, master in masters.items():
        keyboard["buttons"].append([{"text": f"{master['name']} — {master['specialization']}", "callback_data": f"master_{idx}"}])
    
    send_message(chat_id, "👩‍🎨 Выберите мастера:", keyboard)

def send_time_slots(chat_id):
    """Отправляет доступные временные слоты (упрощённо)"""
    keyboard = {
        "buttons": []
    }
    # Предлагаем слоты на сегодня с 10:00 до 18:00
    for hour in range(10, 19):
        time_str = f"{hour:02d}:00"
        keyboard["buttons"].append([{"text": time_str, "callback_data": f"time_{time_str}"}])
    
    send_message(chat_id, "🕐 Выберите удобное время:", keyboard)

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
    
    # Обработка текстовых сообщений
    if update_type == 'message_created':
        msg = update.get('message', {})
        chat_id = msg.get('recipient', {}).get('chat_id')
        text = msg.get('body', {}).get('text', '')
        
        logging.info(f"chat_id={chat_id}, text={text}")
        
        if text == '/start':
            send_main_menu(chat_id)
        else:
            send_message(chat_id, f"✅ Вы написали: {text}")
    
    # Обработка нажатий на кнопки
    elif update_type == 'callback_query':
        callback = update.get('data', {})
        chat_id = callback.get('chat_id')
        callback_data = callback.get('callback_data')
        
        logging.info(f"callback_data={callback_data}")
        
        if not chat_id:
            return '', 200
        
        if callback_data == 'booking':
            user_sessions[chat_id] = {'step': 'service'}
            send_services_menu(chat_id)
        
        elif callback_data.startswith('service_'):
            service_id = callback_data.split('_')[1]
            user_sessions[chat_id] = {'step': 'master', 'service_id': service_id}
            send_masters_menu(chat_id)
        
        elif callback_data.startswith('master_'):
            master_id = callback_data.split('_')[1]
            user_sessions[chat_id]['step'] = 'time'
            user_sessions[chat_id]['master_id'] = master_id
            send_time_slots(chat_id)
        
        elif callback_data.startswith('time_'):
            time_slot = callback_data.split('_')[1]
            session = user_sessions.get(chat_id, {})
            service_id = session.get('service_id')
            master_id = session.get('master_id')
            
            service = services.get(service_id, {})
            master = masters.get(master_id, {})
            
            text = f"✅ Вы записаны!\n\n💇 Услуга: {service.get('name')}\n👩‍🎨 Мастер: {master.get('name')}\n🕐 Время: {time_slot}\n\nСпасибо за запись!"
            send_message(chat_id, text)
            
            # Очищаем сессию
            user_sessions.pop(chat_id, None)
        
        elif callback_data == 'my_appointments':
            send_message(chat_id, "📋 У вас пока нет активных записей.")
        
        elif callback_data == 'cancel':
            send_message(chat_id, "❌ Отмена записи: у вас нет активных записей.")
        
        # Отвечаем на callback, чтобы убрать часики
        callback_url = f"{BASE_URL}/callbacks"
        callback_headers = {"Authorization": TOKEN, "Content-Type": "application/json"}
        callback_data = {"id": update.get('id')}
        requests.post(callback_url, json=callback_data, headers=callback_headers)
    
    return '', 200

@app.route('/')
def index():
    return "Bot is running!"

if __name__ == '__main__':
    logging.info("🚀 Бот запущен!")
    app.run(host='0.0.0.0', port=8080)
