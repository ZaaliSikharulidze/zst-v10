import streamlit as st
import requests
import pandas as pd

st.set_page_config(page_title="ZST Stable", layout="wide")

st.title("🚀 ZST - Stable Trading Core")

# =========================
# PRICE
# =========================
def get_price():
    try:
        r = requests.get(
            "https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT",
            timeout=5
        )
        data = r.json()
        return float(data["price"])
    except:
        return None


# =========================
# KLINES
# =========================
def get_data():
    try:
        r = requests.get(
            "https://api.binance.com/api/v3/klines?symbol=BTCUSDT&interval=1m&limit=50",
            timeout=5
        )
        data = r.json()

        df = pd.DataFrame(data, columns=[
            "open_time","open","high","low","close","volume",
            "close_time","q","n","tbb","tbq","ignore"
        ])

        df["close"] = pd.to_numeric(df["close"], errors="coerce")
        df = df.dropna()

        return df if len(df) > 0 else None

    except:
        return None


# =========================
# RSI
# =========================
def rsi(series):
    try:
        if series is None or len(series) < 10:
            return 50

        delta = series.diff()

        gain = delta.clip(lower=0).mean()
        loss = -delta.clip(upper=0).mean()

        if loss == 0:
            return 50

        rs = gain / loss
        return 100 - (100 / (1 + rs))

    except:
        return 50


# =========================
# SIGNAL
# =========================
def signal(rsi_value):
    if rsi_value > 70:
        return "⛔ SELL"
    elif rsi_value < 30:
        return "🟢 BUY"
    return "⚪ WAIT"


# =========================
# LOAD DATA
# =========================
price = get_price()
df = get_data()

if df is None:
    st.warning("No market data available")
    st.stop()


# =========================
# CALCULATIONS
# =========================
rsi_val = rsi(df["close"])
sig = signal(rsi_val)


# =========================
# UI
# =========================
col1, col2 = st.columns(2)

with col1:
    if price:
        st.metric("BTC Price", f"${price:,.2f}")
    else:
        st.metric("BTC Price", "N/A")

with col2:
    st.metric("RSI", f"{rsi_val:.2f}")

st.markdown(f"### Signal: {sig}")

st.line_chart(df["close"])

st.caption("ZST Stable Core - Clean Production Version")
