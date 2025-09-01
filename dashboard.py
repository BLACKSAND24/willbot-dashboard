import streamlit as st
import pandas as pd
import json
import time

TRADE_HISTORY_FILE = "trade_history.csv"
STATUS_FILE = "bot_status.json"

st.set_page_config(page_title="WillBot Dashboard", layout="wide")

st.title("WillBot Live Dashboard")

# Live status
st.write("## Current Status")
try:
    with open(STATUS_FILE, "r") as f:
        status = json.load(f)
    st.write(f"Symbol: {status.get('symbol')}")
    st.write(f"Signal: {status.get('signal')}")
    st.write(f"Price: {status.get('price')}")
    st.write(f"Time: {status.get('time')}")
except Exception as e:
    st.write("No status available.")

# Trade history
st.write("## Trade History")
try:
    df = pd.read_csv(TRADE_HISTORY_FILE)
    st.dataframe(df)
except Exception as e:
    st.write("No trades yet.")

# --- Interactive Controls ---
st.write("## Trade Controls")
symbol = st.text_input("Symbol (e.g. BTCUSDT)")
quantity = st.number_input("Quantity", min_value=0.0001, value=0.001, step=0.0001, format="%f")
trade_action = st.selectbox("Action", ["BUY", "SELL"])
if st.button("Place Trade"):
    command = {"type": "trade", "symbol": symbol, "quantity": quantity, "action": trade_action}
    with open("dashboard_commands.json", "w") as f:
        json.dump(command, f)
    st.success(f"Trade command sent: {trade_action} {quantity} {symbol}")

st.write("## Bot Controls")
if st.button("Pause Bot"):
    command = {"type": "pause"}
    with open("dashboard_commands.json", "w") as f:
        json.dump(command, f)
    st.success("Pause command sent.")
if st.button("Resume Bot"):
    command = {"type": "resume"}
    with open("dashboard_commands.json", "w") as f:
        json.dump(command, f)
    st.success("Resume command sent.")
