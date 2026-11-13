

import os
import requests
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
)

BOT_TOKEN = os.getenv("9266213015:AAE6u9QN3lSIVkSgALgeyCmbC0qd7OI0oc4")
API_KEY = os.getenv("TWELVE_DATA_API_KEY")
SYMBOL = "XAU/USD"

subscribers = set()


def get_gold_analysis():
    url = "https://api.twelvedata.com/time_series"
    params = {
        "symbol": SYMBOL,
        "interval": "1h",
        "outputsize": 60,
        "apikey": API_KEY,
    }

    response = requests.get(url, params=params, timeout=20)
    data = response.json()

    if "values" not in data:
        raise ValueError(data.get("message", "Data unavailable"))

    candles = list(reversed(data["values"]))
    closes = [float(c["close"]) for c in candles]

    if len(closes) < 30:
        raise ValueError("Not enough candle data")

    previous = closes[-2]
    current = closes[-1]

    ema20 = sum(closes[-20:]) / 20
    ema50 = sum(closes[-50:]) / 50

    changes = [
        closes[i] - closes[i - 1]
        for i in range(1, len(closes))
    ]
    gains = [max(x, 0) for x in changes[-14:]]
    losses = [abs(min(x, 0)) for x in changes[-14:]]

    avg_gain = sum(gains) / 14
    avg_loss = sum(losses) / 14

    if avg_loss == 0:
        rsi = 100
    else:
        rsi = 100 - (100 / (1 + avg_gain / avg_loss))

    if current > ema20 and ema20 > ema50:
        trend = "ميل صاعد"
    elif current < ema20 and ema20 < ema50:
        trend = "ميل هابط"
    else:
        trend = "اتجاه غير واضح"

    return (
        f"تحليل الذهب التعليمي XAU/USD\n\n"
        f"السعر الأخير: {current:.2f}\n"
        f"السعر السابق: {previous:.2f}\n"
        f"EMA 20: {ema20:.2f}\n"
        f"EMA 50: {ema50:.2f}\n"
        f"RSI 14: {rsi:.1f}\n"
        f"قراءة الاتجاه: {trend}\n\n"
        "هذه قراءة تعليمية للمؤشرات وليست توصية تداول "
        "ولا تتنبأ بشكل مؤكد بالشمعة القادمة."
    )


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "مرحباً بك في NIDAL GOLD AI\n\n"
        "/gold - تحليل الذهب\n"
        "/alerts - تفعيل التنبيهات\n"
        "/stop - إيقاف التنبيهات"
    )


async def gold(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        result = get_gold_analysis()
        await update.message.reply_text(result)
    except Exception as error:
        await update.message.reply_text(
            f"تعذر جلب البيانات حالياً: {error}"
        )


async def alerts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    subscribers.add(update.effective_chat.id)
    await update.message.reply_text(
        "تم تفعيل التنبيهات التعليمية كل 15 دقيقة."
    )


async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    subscribers.discard(update.effective_chat.id)
    await update.message.reply_text("تم إيقاف التنبيهات.")


async def send_alerts(context: ContextTypes.DEFAULT_TYPE):
    if not subscribers:
        return

    try:
        message = get_gold_analysis()
        for chat_id in list(subscribers):
            await context.bot.send_message(
                chat_id=chat_id,
                text=message
            )
    except Exception:
        pass


def main():
    if not BOT_TOKEN or not API_KEY:
        raise RuntimeError("Missing environment variables")

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("gold", gold))
    app.add_handler(CommandHandler("alerts", alerts))
    app.add_handler(CommandHandler("stop", stop))

    app.job_queue.run_repeating(
        send_alerts,
        interval=900,
        first=30
    )

    print("NIDAL GOLD AI is running")
    app.run_polling()


if __name__ == "__main__":
    main()
