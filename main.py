# Forex Signal Bot with Charts - XAU/USD & EUR/USD
# Sends 15-minute signals to Telegram with TP/SL, time, and chart image

import requests
import pytz
import time
import datetime
import matplotlib.pyplot as plt
from random import uniform

# === Configuration ===
TELEGRAM_TOKEN = "8116137625:AAGq68Q-Ng8rxyI3Z5qMJOLBitsYVopd8Es"
CHAT_ID = "799287945"
PAIR_LIST = ["XAUUSD", "EURUSD"]
SIGNAL_INTERVAL = 15 * 60  # every 15 minutes
SIGNAL_TIMEOUT = 60 * 60   # 1 hour expiry

signals = {}

# === Simulated price feed ===
def get_price(pair):
    if pair == "XAUUSD":
        return uniform(3330, 3360)
    elif pair == "EURUSD":
        return uniform(1.165, 1.175)
    return 0

# === Telegram messaging ===
def send_telegram_text(message):
    tehran_tz = pytz.timezone("Asia/Tehran")
    now_tehran = datetime.datetime.now(tehran_tz)
    timestamp = now_tehran.strftime("%Y/%m/%d - %H:%M")
    full_message = f"🕰 {timestamp}\\n" + message
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": full_message})

def send_telegram_chart(pair, prices):
    times = [f"-{i*15}m" for i in range(len(prices))][::-1]
    plt.figure(figsize=(6, 3))
    plt.plot(times, prices, marker='o', linestyle='-', color='gold' if pair == "XAUUSD" else 'blue')
    plt.title(f"{pair} - 15min Chart")
    plt.xlabel("Time")
    plt.ylabel("Price")
    plt.grid(True)
    plt.tight_layout()
    filename = f"{pair}_chart.png"
    plt.savefig(filename)
    plt.close()

    with open(filename, "rb") as f:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
        requests.post(url, files={"photo": f}, data={"chat_id": CHAT_ID})

# === Signal generation ===
def generate_signal(pair):
    price = get_price(pair)
    if pair == "XAUUSD":
        direction = "Buy" if price < 3345 else "Sell"
        sl = price - 10 if direction == "Buy" else price + 10
        tp = price + 15 if direction == "Buy" else price - 15
    else:
        direction = "Buy" if price < 1.17 else "Sell"
        sl = price - 0.002 if direction == "Buy" else price + 0.002
        tp = price + 0.003 if direction == "Buy" else price - 0.003

    signal = {
        "pair": pair,
        "direction": direction,
        "entry": round(price, 3 if pair == "XAUUSD" else 5),
        "sl": round(sl, 3 if pair == "XAUUSD" else 5),
        "tp": round(tp, 3 if pair == "XAUUSD" else 5),
        "created_at": time.time(),
        "history": [price]  # store historical prices
    }
    signals[pair] = signal

    msg = (f"📊 سیگنال جدید - {pair}\n"
           f"🟢 نوع: {direction}\n🎯 ورود: {signal['entry']}\n💰 TP: {signal['tp']} | 🛡 SL: {signal['sl']}\n⏳ تایم‌فریم: 15 دقیقه")
    send_telegram_text(msg)
    send_telegram_chart(pair, signal['history'])

def check_signal_status(pair):
    if pair not in signals:
        return

    current_price = get_price(pair)
    signals[pair]['history'].append(current_price)

    signal = signals[pair]
    entry, tp, sl = signal['entry'], signal['tp'], signal['sl']

    if (signal['direction'] == "Buy" and current_price >= tp) or        (signal['direction'] == "Sell" and current_price <= tp):
        send_telegram_text(f"✅ {pair} TP Hit at {round(current_price, 3)}")
        generate_signal(pair)
    elif (signal['direction'] == "Buy" and current_price <= sl) or          (signal['direction'] == "Sell" and current_price >= sl):
        send_telegram_text(f"❌ {pair} SL Hit at {round(current_price, 3)}")
        generate_signal(pair)
    elif time.time() - signal['created_at'] > SIGNAL_TIMEOUT:
        send_telegram_text(f"⌛ سیگنال منقضی شد برای {pair}. سیگنال جدید صادر شد.")
        generate_signal(pair)

def main():
    for pair in PAIR_LIST:
        generate_signal(pair)

    while True:
        for pair in PAIR_LIST:
            check_signal_status(pair)
        time.sleep(SIGNAL_INTERVAL // 3)

if __name__ == "__main__":
    main()
