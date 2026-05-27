import streamlit as st
import requests
import pandas as pd

st.set_page_config(page_title="ZST Stable Core", layout="wide")

st.title("🚀 ZST - Stable Trading System")

# =========================
# PRICE (Binance + CoinGecko fallback)
# =========================
def get_price():
    # Binance
    try:
        r = requests.get(
            "https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT",
            timeout=5
        )
        data = r.json()
        if "price" in data:
            return float(data["price"])
    except:
        pass

    # CoinGecko fallback
    try:
        r = requests.get(
            "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd",
            timeout=5
        )
        data = r.json()
        return float(data["bitcoin"]["usd"])
    except:
        return None


# =========================
# MARKET DATA (Binance + fallback safe)
# =========================
def get_data():
    urls = [
        "https://api.binance.com/api/v3/klines?symbol=BTCUSDT&interval=1m&limit=50",
        "https://api1.binance.com/api/v3/klines?symbol=BTCUSDT&interval=1m&limit=50",
        "https://api2.binance.com/api/v3/klines?symbol=BTCUSDT&interval=1m&limit=50"
    ]

    for url in urls:
        try:
            r = requests.get(url, timeout=5)
            data = r.json()

            if isinstance(data, list) and len(data) > 10:
                df = pd.DataFrame(data, columns=[
                    "open_time","open","high","low","close","volume",
                    "close_time","q","n","tbb","tbq","ignore"
                ])

                df["close"] = pd.to_numeric(df["close"], errors="coerce")
                df = df.dropna()

                if len(df) > 0:
                    return df
        except:
            continue

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
# AI TRADING BRAIN
# =========================
def ai_brain(rsi_value, price_change=0):
    reasons = []

    if rsi_value > 70:
        reasons.append("Overbought market (RSI > 70)")
    elif rsi_value < 30:
        reasons.append("Oversold market (RSI < 30)")
    else:
        reasons.append("Neutral RSI zone")

    if price_change > 0:
        reasons.append("Positive momentum")
    elif price_change < 0:
        reasons.append("Negative momentum")

    if rsi_value < 30 and price_change >= 0:
        decision = "🟢 STRONG BUY"
    elif rsi_value > 70 and price_change <= 0:
        decision = "⛔ STRONG SELL"
    else:
        decision = "⚪ WAIT"

    return decision, reasons


# =========================
# PRICE CHANGE
# =========================
def price_change(df):
    try:
        if df is None or len(df) < 2:
            return 0

        first = float(df["close"].iloc[0])
        last = float(df["close"].iloc[-1])

        return ((last - first) / first) * 100
    except:
        return 0


# =========================
# LOAD DATA
# =========================
price = get_price()
df = get_data()

if df is None:
    st.error("No market data available")
    st.stop()

# =========================
# CALCULATIONS
# =========================
rsi_val = rsi(df["close"])
pc = price_change(df)
decision, reasons = ai_brain(rsi_val, pc)

# =========================
# UI
# =========================
col1, col2, col3 = st.columns(3)

with col1:
    st.metric("BTC Price", f"${price:,.2f}" if price else "N/A")

with col2:
    st.metric("RSI", f"{rsi_val:.2f}")

with col3:
    st.metric("Change %", f"{pc:.2f}%")

st.markdown(f"### 🧠 AI Decision: {decision}")

st.write("### Reasoning:")
for r in reasons:
    st.write("•", r)

st.line_chart(df["close"])

st.caption("ZST Stable Core - Clean Production Base")
st.line_chart(df["close"])

st.caption("ZST Stable Core - Clean Production Version")
