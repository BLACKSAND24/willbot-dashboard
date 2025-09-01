from binance.client import Client
import pandas as pd
import json
import os

# Load config
base_dir = os.path.dirname(__file__)
settings_path = os.path.join(base_dir, "settings.json")
with open(settings_path) as f:
    config = json.load(f)

API_KEY = config["binance_api_key"]
API_SECRET = config["binance_api_secret"]

client = Client(API_KEY, API_SECRET)

# Fetch market data
def get_data(symbol):
    klines = client.get_klines(
        symbol=symbol,
        interval=Client.KLINE_INTERVAL_1MINUTE,
        limit=100
    )
    df = pd.DataFrame(klines, columns=[
        'time', 'open', 'high', 'low', 'close', 'volume', 'close_time',
        'qav', 'num_trades', 'taker_base_vol', 'taker_quote_vol', 'ignore'
    ])
    df['close'] = df['close'].astype(float)
    return df

# Example indicator
def calculate_indicators(df):
    df['SMA'] = df['close'].rolling(window=14).mean()
    return df

# Example strategy
def signal_strategy(df):
    if df['close'].iloc[-1] > df['SMA'].iloc[-1]:
        return "BUY"
    elif df['close'].iloc[-1] < df['SMA'].iloc[-1]:
        return "SELL"
    else:
        return "HOLD"

# Dummy order placement
def place_order(signal, symbol):
    print(f"Placing {signal} order for {symbol}")
    for symbol in ["BTCUSDT", "ETHUSDT", "BNBUSDT"]:
        if signal == "BUY":
            place_order("BUY", symbol)
        elif signal == "SELL":
            place_order("SELL", symbol)
        else:
            print(f"No order placed for {symbol}")
