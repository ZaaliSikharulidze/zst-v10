import streamlit as st
import requests
import pandas as pd
import numpy as np

st.set_page_config(page_title="ZST Stable Core", layout="wide")

st.title("🚀 ZST - Stable Trading System")

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

# =====================================================
# PRICE
# =====================================================
def get_price():

    # Binance
    binance_urls = [
        "https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT",
        "https://api1.binance.com/api/v3/ticker/price?symbol=BTCUSDT",
        "https://api2.binance.com/api/v3/ticker/price?symbol=BTCUSDT",
    ]

    for url in binance_urls:
        try:
            r = requests.get(url, headers=HEADERS, timeout=5)

            if r.status_code == 200:
                data = r.json()
                if "price" in data:
                    return float(data["price"])
        except:
            continue

    # CoinGecko fallback
    try:
        r = requests.get(
            "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd",
            headers=HEADERS,
            timeout=5
        )

        if r.status_code == 200:
            data = r.json()
            return float(data["bitcoin"]["usd"])

    except:
        pass

    return None


# =====================================================
# MARKET DATA (SAFE BINANCE ONLY)
# =====================================================
def get_data():

    urls = [
        "https://api.binance.com/api/v3/klines?symbol=BTCUSDT&interval=1m&limit=100",
        "https://api1.binance.com/api/v3/klines?symbol=BTCUSDT&interval=1m&limit=100",
        "https://api2.binance.com/api/v3/klines?symbol=BTCUSDT&interval=1m&limit=100"
    ]

    for url in urls:
        try:
            r = requests.get(url, headers=HEADERS, timeout=5)

            if r.status_code != 200:
                continue

            data = r.json()

            if not isinstance(data, list):
                continue

            if len(data) < 20:
                continue

            df = pd.DataFrame(data, columns=[
                "open_time","open","high","low","close","volume",
                "close_time","q","n","tbb","tbq","ignore"
            ])

            df["close"] = pd.to_numeric(df["close"], errors="coerce")
            df = df.dropna()

            if len(df) > 20:
                return df

        except:
            continue

    return None


# =====================================================
# RSI
# =====================================================
def rsi(series, period=14):

    try:
        if series is None or len(series) < period:
            return 50

        delta = series.diff()

        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)

        avg_gain = gain.rolling(period).mean()
        avg_loss = loss.rolling(period).mean()

        rs = avg_gain / avg_loss

        rsi_value = 100 - (100 / (1 + rs))

        return float(rsi_value.iloc[-1])

    except:
        return 50


# =====================================================
# PRICE CHANGE
# =====================================================
def price_change(df):

    try:
        first = float(df["close"].iloc[0])
        last = float(df["close"].iloc[-1])

        return ((last - first) / first) * 100

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

    elif change < 0:
        reasons.append("Negative momentum")

    if rsi_value < 30 and change > 0:
        decision = "🟢 STRONG BUY"

    elif rsi_value > 70 and change < 0:
        decision = "🔴 STRONG SELL"

    elif 45 <= rsi_value <= 55:
        decision = "⚪ SIDEWAYS"

    else:
        decision = "🟡 WAIT"

    return decision, reasons


# =====================================================
# LOAD DATA SAFELY
# =====================================================
with st.spinner("Loading market data..."):

    price = get_price()
    df = get_data()


# =====================================================
# FAIL SAFE (NO CRASH EVER)
# =====================================================
if df is None or price is None:

    st.error("❌ No market data available")

    st.info("""
Possible reasons:
- Binance blocked request
- Network timeout
- Streamlit Cloud restriction
- API rate limit
""")

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

st.write("### Reasoning")

for r in reasons:
    st.write("•", r)


# =====================================================
# CHART
# =====================================================
st.line_chart(df["close"])


# =====================================================
# FOOTER
# =====================================================
st.caption("ZST Stable Core - Production Safe Version 🚀")
