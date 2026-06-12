import os
import requests
from flask import Flask, request, jsonify

TOKEN = os.environ.get("TOKEN")
BASE_URL = "https://platform-api.max.ru"

app = Flask(__name__)

@app.route('/webhook', methods=['POST'])
def webhook():
    print("✅ Вебхук сработал!")
    return jsonify({'status': 'ok'}), 200

@app.route('/')
def index():
    return "Bot is running"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
