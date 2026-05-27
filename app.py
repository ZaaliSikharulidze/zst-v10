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
        return {}

def get_btc_price():
    data = safe_get("https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT")
    return float(data.get("price", 0))


def get_klines(symbol="BTCUSDT", interval="1m", limit=100):
    url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval={interval}&limit={limit}"
    data = safe_get(url)

    if not data:
        return pd.DataFrame({"close": []})

    df = pd.DataFrame(data, columns=[
        "open_time", "open", "high", "low", "close", "volume",
        "close_time", "qav", "trades", "tbbav", "tbqav", "ignore"
    ])

    df["close"] = df["close"].astype(float)
    return df


# =========================
# INDICATORS
# =========================

def rsi_calc(df):
    try:
        if df is None or len(df) < 14:
            return 50

        delta = df["close"].diff()
        gain = (delta.where(delta > 0, 0)).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()

        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))

        rsi = rsi.dropna()

        if len(rsi) == 0:
            return 50

        return float(rsi.iloc[-1])

    except:
        return 50


def volatility_calc(df):
    try:
        return float(df["close"].pct_change().std() * 100)
    except:
        return 0


def generate_signal(rsi):
    if rsi > 70:
        return "⛔ SELL"
    elif rsi < 30:
        return "🟢 BUY"
    else:
        return "⚪ WAIT"


def confidence_calc(rsi, vol):
    try:
        return max(0, 100 - (abs(50 - rsi) * 1.5 + vol / 5))
    except:
        return 0


# =========================
# STREAMLIT UI
# =========================

st.set_page_config(page_title="ZST v1 REAL TIME", layout="wide")

st.title("🚀 ZST v1 - REAL TIME Trading Intelligence")

# DATA
price = get_btc_price()
df_1m = get_klines("BTCUSDT", "1m")

# SAFETY CHECK
if df_1m.empty:
    st.error("No market data")
    st.stop()

# INDICATORS
rsi = rsi_calc(df_1m)
volatility = volatility_calc(df_1m)
signal = generate_signal(rsi)
confidence = confidence_calc(rsi, volatility)

# UI
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

# CHART (REAL DATA)
st.subheader("Market Chart (1m)")
st.line_chart(df_1m["close"])

st.caption("ZST v1 - Real-time Binance powered system")
