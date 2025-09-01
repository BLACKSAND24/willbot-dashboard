# WillBot.py - Command-line based Live Crypto Trading Bot (Binance)
import os
import json
from binance.client import Client
import pandas as pd
import ta
import requests
import time

# Dynamically construct the path to settings.json
base_dir = os.path.dirname(__file__)
settings_path = os.path.join(base_dir, "settings.json")

# Load settings
with open(settings_path) as f:
    config = json.load(f)

API_KEY = config["binance_api_key"]
API_SECRET = config["binance_api_secret"]
client = Client(API_KEY, API_SECRET, requests_params={"timeout": 30})
symbol_list = config["symbols"]
quantity = config["quantity"]
telegram_token = config["telegram_token"]
chat_id = config["telegram_chat_id"]

def get_data(symbol):
    klines = client.get_klines(symbol=symbol, interval=Client.KLINE_INTERVAL_1MINUTE, limit=100)
    df = pd.DataFrame(klines, columns=[
        'time','open','high','low','close','volume','close_time','qav','num_trades','taker_base_vol','taker_quote_vol','ignore'
    ])
    df['close'] = df['close'].astype(float)
    return df

def calculate_indicators(df):
    df['rsi'] = ta.momentum.RSIIndicator(df['close']).rsi()
    df['macd'] = ta.trend.MACD(df['close']).macd()
    return df

def signal_strategy(df):
    last = df.iloc[-1]
    if last['rsi'] < 30 and last['macd'] > 0:
        return "BUY"
    elif last['rsi'] > 70 and last['macd'] < 0:
        return "SELL"
    return "HOLD"

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{telegram_token}/sendMessage"
    payload = {"chat_id": chat_id, "text": message}
    requests.post(url, json=payload)

def place_order(signal, symbol):
    if signal == "BUY":
        client.order_market_buy(symbol=symbol, quantity=quantity)
        send_telegram_message(f"✅ BUY executed for {symbol}")
    elif signal == "SELL":
        client.order_market_sell(symbol=symbol, quantity=quantity)
        send_telegram_message(f"🚨 SELL executed for {symbol}")

while True:
    for symbol in symbol_list:
        df = get_data(symbol)
        df = calculate_indicators(df)
        signal = signal_strategy(df)
        if signal != "HOLD":
            place_order(signal, symbol)
    time.sleep(60)
