import asyncio
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.types import (
    LabeledPrice,
    PreCheckoutQuery,
    Message,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    WebAppInfo
)
import uvicorn

BOT_TOKEN = "8765047857:AAF0vWvkEhnqhYfD9MQiaktR7fltZ9WBgLY"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DONATE_CATALOG = {
    "keys_1": {"title": "Набор Новичка (+1 Ключ)", "amount": 1, "type": "keys", "stars": 25},
    "keys_5": {"title": "Набор Смурфа (+5 Ключей)", "amount": 5, "type": "keys", "stars": 100},
    "keys_15": {"title": "Сундук Претендента (+15 Ключей)", "amount": 15, "type": "keys", "stars": 250},
    "mastery_2": {"title": "Горсть Осколков (+2 Мастери)", "amount": 2, "type": "mastery", "stars": 35},
    "mastery_6": {"title": "Мешок Мастери (+6 Осколков)", "amount": 6, "type": "mastery", "stars": 95},
    "mastery_15": {"title": "Хранилище Мастери (+15 Осколков)", "amount": 15, "type": "mastery", "stars": 220},
}

@app.get("/", response_class=HTMLResponse)
async def serve_game():
    try:
        with open("index.html", "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return "<h1>Файл index.html не найден рядом с server.py!</h1>"

@app.get("/api/create-star-invoice")
async def create_star_invoice(type: str, amount: int, stars: int, userId: int = 0):
    item_key = f"{type}_{amount}"
    item = DONATE_CATALOG.get(item_key)

    title = item["title"] if item else f"Покупка {amount} {type}"
    description = f"Пополнение баланса: +{amount} ({type})"
    payload = f"clown_{type}_{amount}_{userId}"

    try:
        invoice_link = await bot.create_invoice_link(
            title=title,
            description=description,
            payload=payload,
            currency="XTR",
            prices=[LabeledPrice(label=title, amount=stars)]
        )
        return {"invoiceLink": invoice_link}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@dp.message(CommandStart())
async def start_handler(message: Message):
    # При публикации/тесте через ngrok укажите здесь HTTPS URL
    game_url = "https://your-public-url.ngrok-free.app"

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🎪 Играть в Лигу Клоунов", web_app=WebAppInfo(url=game_url))]
        ]
    )
    await message.answer(
        "👋 Добро пожаловать в <b>Лигу Клоунов</b>!\n\n"
        "Нажмите кнопку ниже, чтобы начать играть:",
        reply_markup=kb,
        parse_mode="HTML"
    )

@dp.pre_checkout_query()
async def process_pre_checkout_query(pre_checkout: PreCheckoutQuery):
    await bot.answer_pre_checkout_query(pre_checkout.id, ok=True)

@dp.message(F.successful_payment)
async def process_successful_payment(message: Message):
    payment = message.successful_payment
    await message.answer(
        f"🎉 Успешная покупка!\n"
        f"Списано: <b>{payment.total_amount} ⭐️</b>"
    )

@app.on_event("startup")
async def on_startup():
    asyncio.create_task(dp.start_polling(bot))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)