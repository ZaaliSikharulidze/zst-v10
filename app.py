import streamlit as st
import pandas as pd
import requests
import yfinance as yf
import numpy as np

st.set_page_config(
    page_title="ZST Stable Core",
    layout="wide"
)

st.title("🚀 ZST - Stable Trading System")

# =====================================================
# AUTO REFRESH (safe version)
# =====================================================

try:
    from streamlit_autorefresh import st_autorefresh
    st_autorefresh(interval=10000, key="refresh")
except:
    pass

# =====================================================
# PRICE (CACHE + SAFE FALLBACK ORDER)
# =====================================================

@st.cache_data(ttl=10)
def get_price():

    # 1. YAHOO FIRST (more stable on cloud)
    try:
        btc = yf.Ticker("BTC-USD")
        hist = btc.history(period="1d")

        if hist is not None and not hist.empty:
            return float(hist["Close"].iloc[-1])
    except:
        pass

    # 2. COINGECKO
    try:
        r = requests.get(
            "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd",
            timeout=5
        )
        data = r.json()
        return float(data["bitcoin"]["usd"])
    except:
        pass

    return None

# =====================================================
# DATA (CACHE)
# =====================================================

@st.cache_data(ttl=10)
def get_data():

    try:
        btc = yf.Ticker("BTC-USD")

        hist = btc.history(period="1d", interval="1m")

        if hist is None or hist.empty:
            return None

        df = pd.DataFrame()
        df["close"] = hist["Close"].dropna()

        if len(df) < 30:
            return None

        return df

    except:
        return None

# =====================================================
# RSI (SAFE)
# =====================================================

def rsi(series, period=14):

    delta = series.diff()

    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean()

    rs = avg_gain / avg_loss.replace(0, np.nan)

    rsi_series = 100 - (100 / (1 + rs))

    last = rsi_series.dropna()

    if len(last) == 0:
        return 50

    return float(last.iloc[-1])

# =====================================================
# EMA
# =====================================================

def ema(series, period):
    return series.ewm(span=period, adjust=False).mean()

# =====================================================
# MACD
# =====================================================

def macd(series):

    ema12 = ema(series, 12)
    ema26 = ema(series, 26)

    macd_line = ema12 - ema26
    signal = ema(macd_line, 9)

    return macd_line.iloc[-1], signal.iloc[-1]

# =====================================================
# MOMENTUM (STABILIZED)
# =====================================================

def momentum(df):

    if len(df) < 20:
        return 0

    first = df["close"].iloc[-20]
    last = df["close"].iloc[-1]

    return ((last - first) / first) * 100

# =====================================================
# AI BRAIN
# =====================================================

def ai_brain(rsi_value, macd_value, signal, momentum_value):

    score = 0
    reasons = []

    # RSI
    if rsi_value < 30:
        score += 2
        reasons.append("RSI oversold")
    elif rsi_value > 70:
        score -= 2
        reasons.append("RSI overbought")
    else:
        reasons.append("RSI neutral")

    # MACD
    if macd_value > signal:
        score += 2
        reasons.append("MACD bullish")
    else:
        score -= 2
        reasons.append("MACD bearish")

    # MOMENTUM
    if momentum_value > 0:
        score += 1
        reasons.append("Positive momentum")
    else:
        score -= 1
        reasons.append("Negative momentum")

    # DECISION
    if score >= 4:
        decision = "🟢 STRONG BUY"
    elif score >= 2:
        decision = "🟢 BUY"
    elif score <= -4:
        decision = "🔴 STRONG SELL"
    elif score <= -2:
        decision = "🔴 SELL"
    else:
        decision = "⚪ WAIT"

    return decision, reasons, score

# =====================================================
# LOAD
# =====================================================

with st.spinner("Loading market data..."):
    price = get_price()
    df = get_data()

# =====================================================
# FAIL SAFE
# =====================================================

if df is None or price is None:
    st.error("❌ Market data unavailable (API / network issue)")
    st.stop()

# =====================================================
# CALCULATIONS
# =====================================================

rsi_value = rsi(df["close"])
macd_value, signal = macd(df["close"])
momentum_value = momentum(df)

decision, reasons, score = ai_brain(
    rsi_value,
    macd_value,
    signal,
    momentum_value
)

# =====================================================
# UI
# =====================================================

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("BTC Price", f"${price:,.2f}")

with col2:
    st.metric("RSI", f"{rsi_value:.2f}")

with col3:
    st.metric("Momentum", f"{momentum_value:.2f}%")

st.markdown(f"# 🧠 AI Decision: {decision}")
st.write(f"AI Score: {score}")

st.write("## 📋 Analysis")
for r in reasons:
    st.write("•", r)

# =====================================================
# CHART
# =====================================================

chart_df = pd.DataFrame({
    "BTC": df["close"],
    "EMA20": ema(df["close"], 20),
    "EMA50": ema(df["close"], 50)
})

st.line_chart(chart_df)

# =====================================================
# RAW DATA
# =====================================================

with st.expander("📦 Raw Data"):
    st.dataframe(df.tail(20))

st.caption("ZST Stable Cloud Version v2")
