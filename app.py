import streamlit as st
import requests
import pandas as pd
import sqlite3
from datetime import datetime

st.set_page_config(page_title="ZST v10", layout="wide")

st.title("🚀 ZST v10 - SaaS Trading Intelligence Platform")

# =========================
# DATABASE
# =========================
conn = sqlite3.connect("zst.db", check_same_thread=False)
c = conn.cursor()

c.execute("""
CREATE TABLE IF NOT EXISTS trades (
    time TEXT,
    price REAL,
    action TEXT,
    rsi REAL,
    confidence REAL,
    pnl REAL
)
""")
conn.commit()

# =========================
# PRICE
# =========================
import requests
import streamlit as st

try:
    response = requests.get(
        "https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT",
        timeout=5
    )
    data = response.json()

    price = float(data["price"])

    st.metric("BTC Price", f"${price:,.2f}")

except Exception as e:
    st.error("BTC price loading error 😕")
    st.write("Using fallback value")

    price = 0
    st.metric("BTC Price", "$0.00")

# =========================
# DATA
# =========================
def get_data(interval):
    url = f"https://api.binance.com/api/v3/klines?symbol=BTCUSDT&interval={interval}&limit=100"
    data = requests.get(url).json()
    df = pd.DataFrame(data, columns=[
        "time","open","high","low","close","volume",
        "close_time","qav","trades","tbbav","tbqav","ignore"
    ])
    df["close"] = df["close"].astype(float)
    return df

df_1m = get_data("1m")
df_5m = get_data("5m")

# =========================
# RSI FUNCTION
# =========================
def rsi_calc(df):
    try:
        if df is None or len(df) < 15:
            return 0

        rsi = df["close"].rolling(14).mean()

        if rsi is None or len(rsi) == 0:
            return 0

        return float(rsi.iloc[-1])

    except:
        return 0

# =========================
# VOLATILITY
# =========================
volatility = float(df_1m["close"].std())

# =========================
# CONFIDENCE
# =========================
confidence = max(0, 100 - (abs(50 - rsi_1m) * 1.5 + volatility / 5))

# =========================
# SIGNAL ENGINE
# =========================
if rsi_1m < 30 and rsi_5m < 40:
    action = "BUY"
elif rsi_1m > 70 and rsi_5m > 60:
    action = "SELL"
elif confidence < 40:
    action = "NO TRADE"
else:
    action = "WAIT"

# =========================
# EXPLANATION ENGINE
# =========================
explanations = []

if rsi_1m < 30:
    explanations.append("1m RSI is oversold → possible bounce")
if rsi_5m < 40:
    explanations.append("5m trend weak → bearish pressure")
if rsi_1m > 70:
    explanations.append("1m overbought → correction risk")
if confidence < 40:
    explanations.append("Low confidence market → avoid trading")

# =========================
# SIMPLE PNL SIMULATION
# =========================
pnl = 0
if "balance" not in st.session_state:
    st.session_state.balance = 1000

# =========================
# SAVE TO DB
# =========================
c.execute("""
INSERT INTO trades (time, price, action, rsi, confidence, pnl)
VALUES (?, ?, ?, ?, ?, ?)
""", (
    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    price,
    action,
    rsi_1m,
    confidence,
    pnl
))
conn.commit()

# =========================
# UI
# =========================
col1, col2, col3 = st.columns(3)

with col1:
    st.subheader("Action")
    st.markdown(f"## {action}")

with col2:
    st.subheader("RSI (1m / 5m)")
    st.write(f"{rsi_1m:.2f} / {rsi_5m:.2f}")

with col3:
    st.subheader("Confidence")
    st.metric("Score", f"{confidence:.1f}/100")

# =========================
# EXPLANATION
# =========================
st.subheader("Why this signal?")
for e in explanations:
    st.write("• " + e)

# =========================
# MARKET STATE
# =========================
if rsi_5m > 55:
    state = "📈 BULLISH"
elif rsi_5m < 45:
    state = "📉 BEARISH"
else:
    state = "⚖️ RANGE"

st.subheader("Market State")
st.write(state)

# =========================
# PERFORMANCE METRICS
# =========================
history = pd.read_sql("SELECT * FROM trades ORDER BY time DESC LIMIT 50", conn)

buy_signals = (history["action"] == "BUY").sum()
sell_signals = (history["action"] == "SELL").sum()

st.subheader("Performance")
st.write(f"BUY signals: {buy_signals}")
st.write(f"SELL signals: {sell_signals}")

# fake win-rate logic (prototype level)
win_rate = 50 + (confidence - 50) * 0.2
st.metric("Estimated Win Rate", f"{win_rate:.1f}%")

# =========================
# CHARTS
# =========================
st.subheader("Market Charts")
st.line_chart(df_1m["close"])
st.line_chart(df_5m["close"])

st.caption("ZST v10 - deployable SaaS trading intelligence system")
