# WillBot.py - Command-line based Live Crypto Trading Bot (Binance)
import os
import json
from binance.client import Client
import pandas as pd
import ta
import requests
import time
import csv
import threading
import streamlit as st

# Dynamically construct the path to settings.json
base_dir = os.path.dirname(__file__)
settings_path = os.path.join(base_dir, "settings.json")

# Load settings
trade_history = []
latest_status = {"symbol": None, "signal": None, "price": None, "time": None}
TRADE_HISTORY_FILE = "trade_history.csv"
STATUS_FILE = "bot_status.json"
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
    try:
        klines = client.get_klines(symbol=symbol, interval=Client.KLINE_INTERVAL_1MINUTE, limit=100)
        df = pd.DataFrame(klines, columns=[
            'time','open','high','low','close','volume','close_time','qav','num_trades','taker_base_vol','taker_quote_vol','ignore'
        ])
        df['close'] = df['close'].astype(float)
        return df
    except Exception as e:
        print(f"Error fetching data for {symbol}: {e}")
        return None

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
        price = None
        try:
            if signal == "BUY":
                order = client.order_market_buy(symbol=symbol, quantity=quantity)
                price = order['fills'][0]['price'] if 'fills' in order and order['fills'] else None
                send_telegram_message(f"✅ BUY executed for {symbol}")
            elif signal == "SELL":
                order = client.order_market_sell(symbol=symbol, quantity=quantity)
                price = order['fills'][0]['price'] if 'fills' in order and order['fills'] else None
                send_telegram_message(f"🚨 SELL executed for {symbol}")
        except Exception as e:
            print(f"Order error for {symbol}: {e}")
        # Record trade
        trade = {
            "symbol": symbol,
            "signal": signal,
            "price": price,
            "time": time.strftime('%Y-%m-%d %H:%M:%S')
        }
        trade_history.append(trade)
        latest_status.update(trade)
        # Save trade to CSV
        with open(TRADE_HISTORY_FILE, "a", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["symbol", "signal", "price", "time"])
            if f.tell() == 0:
                writer.writeheader()
            writer.writerow(trade)
        # Save status to JSON
        with open(STATUS_FILE, "w") as f:
            json.dump(latest_status, f)

def bot_loop():
    paused = False
    while True:
        # Check for dashboard commands
        try:
            with open("dashboard_commands.json", "r") as f:
                command = json.load(f)
            if command.get("type") == "pause":
                paused = True
                print("Bot paused by dashboard.")
            elif command.get("type") == "resume":
                paused = False
                print("Bot resumed by dashboard.")
            elif command.get("type") == "trade":
                symbol = command.get("symbol")
                quantity = float(command.get("quantity"))
                action = command.get("action")
                print(f"Dashboard trade: {action} {quantity} {symbol}")
                place_order(action, symbol)
            # Remove command after processing
            import os
            os.remove("dashboard_commands.json")
        except Exception:
            pass
        if paused:
            time.sleep(2)
            continue
        for symbol in symbol_list:
            df = get_data(symbol)
            if df is None:
                continue
            df = calculate_indicators(df)
            signal = signal_strategy(df)
            latest_status.update({"symbol": symbol, "signal": signal, "price": df['close'].iloc[-1], "time": time.strftime('%Y-%m-%d %H:%M:%S')})
            # Save status to JSON for dashboard
            with open(STATUS_FILE, "w") as f:
                json.dump(latest_status, f)
            if signal != "HOLD":
                place_order(signal, symbol)
        time.sleep(60)

def dashboard():
    st.title("WillBot Live Dashboard")
    st.write("## Current Status")
    status = latest_status.copy()
    st.write(f"Symbol: {status.get('symbol')}")
    st.write(f"Signal: {status.get('signal')}")
    st.write(f"Price: {status.get('price')}")
    st.write(f"Time: {status.get('time')}")
    st.write("## Trade History")
    if trade_history:
        st.dataframe(trade_history)
    else:
        st.write("No trades yet.")

def run_dashboard():
    import os
    os.environ["STREAMLIT_SERVER_HEADLESS"] = "true"
    st.set_page_config(page_title="WillBot Dashboard", layout="wide")
    while True:
        dashboard()
        time.sleep(2)

if __name__ == "__main__":
    bot_loop()
