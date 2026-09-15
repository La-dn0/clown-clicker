from flask import Flask, request, jsonify
from flask_cors import CORS
import telebot
from telebot import types
import threading

BOT_TOKEN = "8765047857:AAF0vWvkEhnqhYfD9MQiaktR7fltZ9WBgLY"
bot = telebot.TeleBot(BOT_TOKEN)

app = Flask(__name__)
CORS(app)

DONATE_CATALOG = {
    "keys_1": {"title": "Набор Новичка (+1 Ключ)", "amount": 1, "type": "keys", "stars": 25},
    "keys_5": {"title": "Набор Смурфа (+5 Ключей)", "amount": 5, "type": "keys", "stars": 100},
    "keys_15": {"title": "Сундук Претендента (+15 Ключей)", "amount": 15, "type": "keys", "stars": 250},
    "mastery_2": {"title": "Горсть Осколков (+2 Мастери)", "amount": 2, "type": "mastery", "stars": 35},
    "mastery_6": {"title": "Мешок Мастери (+6 Осколков)", "amount": 6, "type": "mastery", "stars": 95},
    "mastery_15": {"title": "Хранилище Мастери (+15 Осколков)", "amount": 15, "type": "mastery", "stars": 220},
}

# 1. Раздача игры
@app.route('/')
def index():
    try:
        with open('index.html', 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return "Файл index.html не найден рядом с server.py!"

# 2. Генерация нативной ссылки на оплату звёздами Stars
@app.route('/api/create-star-invoice', methods=['GET'])
def create_star_invoice():
    item_type = request.args.get('type')
    amount = request.args.get('amount', type=int)
    stars = request.args.get('stars', type=int)
    user_id = request.args.get('userId', default=0, type=int)

    item_key = f"{item_type}_{amount}"
    item = DONATE_CATALOG.get(item_key)

    title = item["title"] if item else f"Покупка {amount} {item_type}"
    description = f"Пополнение игрового баланса на +{amount} ({item_type})"
    payload = f"clown_{item_type}_{amount}_{user_id}"

    prices = [types.LabeledPrice(label=title, amount=stars)]

    try:
        # Генерация нативной ссылки инвойса для WebApp
        invoice_link = bot.create_invoice_link(
            title=title,
            description=description,
            invoice_payload=payload,
            provider_token="",  # Для Stars пустая строка
            currency="XTR",
            prices=prices
        )
        return jsonify({"invoiceLink": invoice_link})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# 3. Подтверждение доступности товара
@bot.pre_checkout_query_handler(func=lambda query: True)
def process_pre_checkout(pre_checkout_query):
    bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)

# 4. Обработка успешного платежа
@bot.message_handler(content_types=['successful_payment'])
def process_successful_payment(message):
    payment_info = message.successful_payment
    payload_parts = payment_info.invoice_payload.split('_')
    
    item_type = payload_parts[1]
    amount = int(payload_parts[2])
    stars_paid = payment_info.total_amount

    bot.send_message(
        message.chat.id, 
        f"✅ Оплата прошла успешно!\nСписано: {stars_paid} ⭐️\nТовар: +{amount} {item_type}"
    )

# 5. Кнопка запуска игры при старте бота
@bot.message_handler(commands=['start'])
def start_cmd(message):
    # Укажите рабочий HTTPS адрес (например, ссылку ngrok)
    game_url = "https://your-public-url.ngrok-free.app"

    markup = types.InlineKeyboardMarkup()
    btn = types.InlineKeyboardButton(text="🎪 Играть в Лигу Клоунов", web_app=types.WebAppInfo(url=game_url))
    markup.add(btn)

    bot.send_message(
        message.chat.id,
        "👋 Добро пожаловать в <b>Лигу Клоунов</b>!\nНажмите кнопку ниже, чтобы запустить игру:",
        reply_markup=markup,
        parse_mode="HTML"
    )

def run_flask():
    app.run(host='0.0.0.0', port=8000)

if __name__ == '__main__':
    # Запускаем веб-сервер в отдельном потоке
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()

    # Запускаем бота
    bot.infinity_polling()
