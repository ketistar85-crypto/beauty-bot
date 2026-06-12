import os
import sys
import logging
from flask import Flask, request
import requests
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime, date

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

TOKEN = os.environ.get("TOKEN")
DATABASE_URL = os.environ.get("DATABASE_URL")

if not TOKEN:
    logging.error("TOKEN не найден!")
    sys.exit(1)

if not DATABASE_URL:
    logging.error("DATABASE_URL не найден!")
    sys.exit(1)

def get_db_connection():
    return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)

def init_db():
    """Создаёт таблицы, если их нет"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Таблица салонов
    cur.execute("""
        CREATE TABLE IF NOT EXISTS salons (
            id SERIAL PRIMARY KEY,
            name VARCHAR(255),
            email VARCHAR(255),
            bot_token VARCHAR(100) UNIQUE,
            plan VARCHAR(50) DEFAULT 'free',
            masters_count INTEGER DEFAULT 0,
            appointments_this_month INTEGER DEFAULT 0,
            is_active BOOLEAN DEFAULT true
        )
    """)
    
    # Таблица мастеров
    cur.execute("""
        CREATE TABLE IF NOT EXISTS masters (
            id SERIAL PRIMARY KEY,
            salon_id INTEGER REFERENCES salons(id),
            name VARCHAR(255),
            specialization VARCHAR(255),
            is_active BOOLEAN DEFAULT true
        )
    """)
    
    # Таблица услуг
    cur.execute("""
        CREATE TABLE IF NOT EXISTS services (
            id SERIAL PRIMARY KEY,
            salon_id INTEGER REFERENCES salons(id),
            name VARCHAR(255),
            duration INTEGER,
            price INTEGER,
            is_active BOOLEAN DEFAULT true
        )
    """)
    
    # Таблица клиентов
    cur.execute("""
        CREATE TABLE IF NOT EXISTS clients (
            id SERIAL PRIMARY KEY,
            salon_id INTEGER REFERENCES salons(id),
            user_id VARCHAR(100),
            name VARCHAR(255),
            phone VARCHAR(50),
            UNIQUE(salon_id, user_id)
        )
    """)
    
    # Таблица записей
    cur.execute("""
        CREATE TABLE IF NOT EXISTS appointments (
            id SERIAL PRIMARY KEY,
            salon_id INTEGER REFERENCES salons(id),
            client_id INTEGER REFERENCES clients(id),
            master_id INTEGER REFERENCES masters(id),
            service_id INTEGER REFERENCES services(id),
            appointment_time TIMESTAMP,
            status VARCHAR(50) DEFAULT 'pending'
        )
    """)
    
    conn.commit()
    conn.close()
    logging.info("База данных инициализирована")

def send_message(chat_id, text, token):
    """Отправка сообщения от имени салона"""
    url = f"https://platform-api.max.ru/messages?chat_id={chat_id}"
    headers = {"Authorization": token, "Content-Type": "application/json"}
    data = {"text": text}
    
    try:
        r = requests.post(url, json=data, headers=headers, timeout=10)
        return r.status_code == 200
    except Exception as e:
        logging.error(f"Ошибка отправки: {e}")
        return False

def check_limits(salon_id):
    """Проверка лимитов по тарифу"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute("SELECT plan, masters_count, appointments_this_month FROM salons WHERE id = %s", (salon_id,))
    salon = cur.fetchone()
    conn.close()
    
    if not salon:
        return {"allowed": False, "reason": "Салон не найден"}
    
    limits = {
        'free': {'max_masters': 1, 'max_appointments': 30},
        'base': {'max_masters': 3, 'max_appointments': 100},
        'optimal': {'max_masters': 10, 'max_appointments': 500},
        'unlimited': {'max_masters': 999999, 'max_appointments': 999999}
    }
    
    plan = salon['plan']
    max_masters = limits[plan]['max_masters']
    max_appointments = limits[plan]['max_appointments']
    
    if salon['masters_count'] >= max_masters:
        return {"allowed": False, "reason": f"Лимит мастеров ({max_masters})"}
    
    if salon['appointments_this_month'] >= max_appointments:
        return {"allowed": False, "reason": f"Лимит записей ({max_appointments})"}
    
    return {"allowed": True}

def get_or_create_client(salon_id, user_id, name):
    """Находит или создаёт клиента"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute("SELECT id FROM clients WHERE salon_id = %s AND user_id = %s", (salon_id, user_id))
    client = cur.fetchone()
    
    if not client:
        cur.execute("INSERT INTO clients (salon_id, user_id, name) VALUES (%s, %s, %s) RETURNING id", 
                    (salon_id, user_id, name))
        client_id = cur.fetchone()['id']
        conn.commit()
    else:
        client_id = client['id']
    
    conn.close()
    return client_id

# Flask приложение
app = Flask(__name__)

@app.route('/webhook', methods=['POST'])
def webhook():
    """Единая точка входа для всех салонов"""
    
    salon_token = request.headers.get('Authorization')
    if not salon_token:
        return '', 200
    
    # Находим салон по токену
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, name, plan FROM salons WHERE bot_token = %s", (salon_token,))
    salon = cur.fetchone()
    conn.close()
    
    if not salon:
        return '', 200
    
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
        
        if not chat_id:
            return '', 200
        
        # Создаём клиента
        client_id = get_or_create_client(salon['id'], str(chat_id), text[:50])
        
        # Проверяем лимиты
        limits = check_limits(salon['id'])
        if not limits['allowed']:
            send_message(chat_id, f"❌ {limits['reason']}. Обратитесь к администратору.", salon_token)
            return '', 200
        
        if text == '/start':
            send_message(chat_id, f"🌸 Добро пожаловать в {salon['name']}!\n\nТариф: {salon['plan']}", salon_token)
        else:
            send_message(chat_id, f"✅ Вы написали: {text}", salon_token)
    
    return '', 200

@app.route('/')
def index():
    return "Bot is running!"

if __name__ == '__main__':
    logging.info("🚀 Бот запущен")
    init_db()
    app.run(host='0.0.0.0', port=8080)
