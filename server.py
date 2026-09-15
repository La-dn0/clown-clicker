from flask import Flask, request, jsonify
from flask_cors import CORS
import telebot
from telebot import types
import threading
import sys

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

# Отдача clown-cliker.html
@app.route('/')
def index():
    try:
        with open('clown-cliker.html', 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return "<h1>Файл clown-cliker.html не найден рядом с server.py!</h1>"

# Генерация инвойса Telegram Stars
@app.route('/api/create-star-invoice', methods=['GET'])
def create_star_invoice():
    try:
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

        # Для Telegram Stars provider_token вообще не указывается
        invoice_link = bot.create_invoice_link(
            title=title,
            description=description,
            invoice_payload=payload,
            currency="XTR",
            prices=prices
        )
        print(f"\n[УСПЕХ] Инвойс Stars создан: {invoice_link}\n", flush=True)
        return jsonify({"invoiceLink": invoice_link})
    except Exception as e:
        print("\n" + "!" * 50, flush=True)
        print(f"[ОШИБКА TELEGRAM API]: {repr(e)}", flush=True)
        print("!" * 50 + "\n", flush=True)
        return jsonify({"error": str(e)}), 500

# Подтверждение предзаказа
@bot.pre_checkout_query_handler(func=lambda query: True)
def process_pre_checkout(pre_checkout_query):
    try:
        bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)
    except Exception as e:
        print(f"[ОШИБКА PRE_CHECKOUT]: {repr(e)}", flush=True)

# Уведомление об успешной оплате
@bot.message_handler(content_types=['successful_payment'])
def process_successful_payment(message):
    payment_info = message.successful_payment
    payload_parts = payment_info.invoice_payload.split('_')
    
    item_type = payload_parts[1] if len(payload_parts) > 1 else "предмет"
    amount = payload_parts[2] if len(payload_parts) > 2 else ""
    stars_paid = payment_info.total_amount

    bot.send_message(
        message.chat.id, 
        f"🎉 <b>Оплата прошла успешно!</b>\n"
        f"Списано: <b>{stars_paid} ⭐️</b>\n"
        f"Зачислено: <b>+{amount} {item_type}</b>\n\n"
        f"Открой игру снова, баланс уже обновлен!",
        parse_mode="HTML"
    )

# Команда /start
@bot.message_handler(commands=['start'])
def start_cmd(message):
    game_url = "https://faceless-reoccupy-reproduce.ngrok-free.dev"

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
    app.run(host='0.0.0.0', port=8000, debug=False, use_reloader=False)

if __name__ == '__main__':
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()
    print("Flask запущен на порту 8000. Ожидание кликов...", flush=True)
    bot.infinity_polling()
