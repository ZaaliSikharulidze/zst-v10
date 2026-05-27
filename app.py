import streamlit as st
import requests
import pandas as pd

st.set_page_config(page_title="ZST Stable", layout="wide")

st.title("🚀 ZST - Stable Core System")

# =========================
# PRICE (SAFE)
# =========================
def get_price():
    try:
        r = requests.get(
            "https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT",
            timeout=5
        ).json()
        return float(r["price"])
    except:
        return None


# =========================
# KLINES (SAFE)
# =========================
def get_data():
    try:
        r = requests.get(
            "https://api.binance.com/api/v3/klines?symbol=BTCUSDT&interval=1m&limit=50",
            timeout=5
        ).json()

        df = pd.DataFrame(r, columns=[
            "open_time","open","high","low","close","volume",
            "close_time","q","n","tbb","tbq","ignore"
        ])

        df["close"] = pd.to_numeric(df["close"], errors="coerce")
        return df.dropna()

    except:
        return None


# =========================
# RSI (SIMPLE + SAFE)
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
def signal(r):
    if r > 70:
        return "⛔ SELL"
    elif r < 30:
        return "🟢 BUY"
    return "⚪ WAIT"


# =========================
# LOAD DATA
# =========================
price = get_price()
df = get_data()

# =========================
# CALC
# =========================
if df is not None:
    rsi_val = rsi(df["close"])
else:
    rsi_val = 50

sig = signal(rsi_val)

# =========================
# UI
# =========================
if price:
    st.metric("BTC Price", f"${price:,.2f}")
else:
    st.metric("BTC Price", "N/A")

st.metric("RSI", f"{rsi_val:.2f}")
st.markdown(f"### Signal: {sig}")

if df is not None:
    st.line_chart(df["close"])
else:
    st.warning("No market data available") v1 - Real-Time Binance Powered System")
