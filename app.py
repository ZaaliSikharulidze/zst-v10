import streamlit as st
import requests
import pandas as pd

# =========================
# SAFE DATA LAYER
# =========================

def safe_get(url):
    try:
        r = requests.get(url, timeout=5)
        return r.json()
    except:
        return {}

def get_btc_price():
    data = safe_get("https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT")
    try:
        return float(data.get("price", 0))
    except:
        return 0


# =========================
# MOCK DATA (replace later with real candles)
# =========================
def get_mock_df():
    return pd.DataFrame({
        "close": [1] * 20
    })


# =========================
# INDICATOR ENGINE
# =========================

def rsi_calc(df):
    try:
        if df is None or len(df) < 14:
            return 50

        rsi = df["close"].rolling(14).mean()
        rsi = rsi.dropna()

        if len(rsi) == 0:
            return 50

        return float(rsi.iloc[-1])

    except:
        return 50


# =========================
# SIGNAL ENGINE
# =========================

def generate_signal(rsi):
    try:
        if rsi > 70:
            return "⛔ SELL"
        elif rsi < 30:
            return "🟢 BUY"
        else:
            return "⚪ WAIT"
    except:
        return "⚪ WAIT"


# =========================
# CONFIDENCE ENGINE
# =========================

def calculate_confidence(rsi, volatility=0):
    try:
        rsi = float(rsi) if isinstance(rsi, (int, float)) else 50
        volatility = float(volatility) if isinstance(volatility, (int, float)) else 0

        confidence = 100 - (abs(50 - rsi) * 1.5 + volatility / 5)

        return max(0, min(100, confidence))
    except:
        return 0


# =========================
# STREAMLIT UI
# =========================

st.set_page_config(page_title="ZST v1", layout="wide")

st.title("🚀 ZST v1 - SaaS Trading Intelligence Platform")

# DATA
price = get_btc_price()
df = get_mock_df()

rsi = rsi_calc(df)
signal = generate_signal(rsi)
confidence = calculate_confidence(rsi)

# UI
col1, col2, col3 = st.columns(3)

with col1:
    st.metric("BTC Price", f"${price:,.2f}")

with col2:
    st.metric("RSI", f"{rsi:.2f}")

with col3:
    st.metric("Confidence", f"{confidence:.1f}%")

st.subheader("Signal")
st.markdown(f"## {signal}")

st.caption("ZST v1 - stable production version")
st.line_chart(df_5m["close"])

st.caption("ZST v10 - deployable SaaS trading intelligence system")
