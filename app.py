import streamlit as st
import requests
import pandas as pd
import numpy as np

st.set_page_config(page_title="ZST Stable Core", layout="wide")
st.title("🚀 ZST - Stable Trading System")

HEADERS = {"User-Agent": "Mozilla/5.0"}

# =====================================================
# PRICE (ONLY COINGECKO = 100% STABLE ON STREAMLIT)
# =====================================================
def get_price():
    try:
        r = requests.get(
            "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd",
            headers=HEADERS,
            timeout=10
        )

        data = r.json()
        return float(data["bitcoin"]["usd"])

    except:
        return None


# =====================================================
# MARKET DATA (COINGECKO MARKET CHART)
# =====================================================
def get_data():
    try:
        r = requests.get(
            "https://api.coingecko.com/api/v3/coins/bitcoin/market_chart?vs_currency=usd&days=1",
            headers=HEADERS,
            timeout=10
        )

        data = r.json()["prices"]

        df = pd.DataFrame(data, columns=["time", "close"])
        df["close"] = pd.to_numeric(df["close"], errors="coerce")
        df = df.dropna()

        return df

    except:
        return None


# =====================================================
# RSI
# =====================================================
def rsi(series, period=14):
    try:
        delta = series.diff()

        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)

        avg_gain = gain.rolling(period).mean()
        avg_loss = loss.rolling(period).mean()

        rs = avg_gain / avg_loss

        rsi_val = 100 - (100 / (1 + rs))

        return float(rsi_val.iloc[-1])

    except:
        return 50


# =====================================================
# PRICE CHANGE
# =====================================================
def price_change(df):
    try:
        return ((df["close"].iloc[-1] - df["close"].iloc[0]) / df["close"].iloc[0]) * 100
    except:
        return 0


# =====================================================
# AI BRAIN
# =====================================================
def ai_brain(rsi_value, change):
    reasons = []

    if rsi_value > 70:
        reasons.append("Overbought market")
    elif rsi_value < 30:
        reasons.append("Oversold market")
    else:
        reasons.append("Neutral RSI")

    if change > 0:
        reasons.append("Positive momentum")
    else:
        reasons.append("Negative momentum")

    if rsi_value < 30 and change > 0:
        decision = "🟢 STRONG BUY"
    elif rsi_value > 70 and change < 0:
        decision = "🔴 STRONG SELL"
    else:
        decision = "⚪ WAIT"

    return decision, reasons


# =====================================================
# LOAD DATA
# =====================================================
with st.spinner("Loading stable market data..."):
    price = get_price()
    df = get_data()

# =====================================================
# FAIL SAFE
# =====================================================
if df is None or price is None:
    st.error("❌ No market data available")
    st.stop()

# =====================================================
# CALCULATIONS
# =====================================================
rsi_val = rsi(df["close"])
pc = price_change(df)
decision, reasons = ai_brain(rsi_val, pc)

# =====================================================
# UI
# =====================================================
col1, col2, col3 = st.columns(3)

with col1:
    st.metric("BTC Price", f"${price:,.2f}")

with col2:
    st.metric("RSI", f"{rsi_val:.2f}")

with col3:
    st.metric("Change %", f"{pc:.2f}%")

st.markdown(f"## 🧠 AI Decision: {decision}")

for r in reasons:
    st.write("•", r)

st.line_chart(df["close"])

st.caption("ZST Stable Core - Streamlit Safe Version")on Safe Version 🚀")
