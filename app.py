import streamlit as st
import requests
import pandas as pd

# =========================
# SAFE API LAYER
# =========================

def safe_get(url):
    try:
        r = requests.get(url, timeout=5)
        return r.json()
    except:
        return None


# =========================
# PRICE
# =========================

def get_btc_price():
    data = safe_get("https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT")
    try:
        if data and "price" in data:
            return float(data["price"])
        return 0
    except:
        return 0


# =========================
# KLINES (REAL DATA)
# =========================

def get_klines(symbol="BTCUSDT", interval="1m", limit=100):
    url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval={interval}&limit={limit}"

    try:
        r = requests.get(url, timeout=5)
        data = r.json()

        if not isinstance(data, list):
            return None

        df = pd.DataFrame(data, columns=[
            "open_time", "open", "high", "low", "close", "volume",
            "close_time", "qav", "trades", "tbbav", "tbqav", "ignore"
        ])

        df["close"] = pd.to_numeric(df["close"], errors="coerce")
        df = df.dropna()

        if len(df) == 0:
            return None

        return df

    except:
        return None


# =========================
# RSI CALC
# =========================

def rsi_calc(df):
    try:
        if df is None or len(df) < 14:
            return 50

        delta = df["close"].diff()

        gain = delta.where(delta > 0, 0).rolling(14).mean()
        loss = -delta.where(delta < 0, 0).rolling(14).mean()

        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))

        rsi = rsi.dropna()

        if len(rsi) == 0:
            return 50

        return float(rsi.iloc[-1])

    except:
        return 50


# =========================
# VOLATILITY
# =========================

def volatility_calc(df):
    try:
        return float(df["close"].pct_change().std() * 100)
    except:
        return 0


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

def confidence_calc(rsi, vol):
    try:
        rsi = float(rsi) if isinstance(rsi, (int, float)) else 50
        vol = float(vol) if isinstance(vol, (int, float)) else 0

        confidence = 100 - (abs(50 - rsi) * 1.5 + vol / 5)

        return max(0, min(100, confidence))

    except:
        return 0


# =========================
# UI
# =========================

st.set_page_config(page_title="ZST v1 REAL", layout="wide")

st.title("🚀 ZST v1 - Real-Time Trading Intelligence")

# DATA
price = get_btc_price()
df = get_klines()

# SAFETY CHECK
if df is None or len(df) == 0:
    st.error("❌ No market data (Binance API unavailable)")
    st.stop()

# INDICATORS
rsi = rsi_calc(df)
volatility = volatility_calc(df)
signal = generate_signal(rsi)
confidence = confidence_calc(rsi, volatility)

# DASHBOARD
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("BTC Price", f"${price:,.2f}")

with col2:
    st.metric("RSI (1m)", f"{rsi:.2f}")

with col3:
    st.metric("Volatility", f"{volatility:.2f}%")

with col4:
    st.metric("Confidence", f"{confidence:.1f}%")

st.subheader("Signal")
st.markdown(f"## {signal}")

st.subheader("Market Chart (1m)")
st.line_chart(df["close"])

st.caption("ZST v1 - Real-Time Binance Powered System")
st.line_chart(df["close"])

st.caption("ZST v1 - Production Safe Real-Time System")-time Binance powered system")
