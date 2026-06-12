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
