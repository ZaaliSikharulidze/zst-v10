import streamlit as st
import pandas as pd
import requests
import numpy as np
import sqlite3

st.set_page_config(page_title="ZST PRO SaaS", layout="wide")

st.title("🚀 ZST LEVEL 2 PRO SAAS")

# =====================================================
# AUTO REFRESH
# =====================================================

try:
    from streamlit_autorefresh import st_autorefresh
    st_autorefresh(interval=10000, key="refresh")
except:
    pass

# =====================================================
# DATABASE
# =====================================================

conn = sqlite3.connect("zst.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS signals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    price REAL,
    rsi REAL,
    macd REAL,
    signal REAL,
    momentum REAL,
    decision TEXT,
    score REAL
)
""")

conn.commit()

def save_signal(price, rsi, macd, signal, momentum, decision, score):
    cursor.execute("""
        INSERT INTO signals (
            price, rsi, macd, signal, momentum, decision, score
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (price, rsi, macd, signal, momentum, decision, score))
    conn.commit()

# =====================================================
# DATA (COINGECKO ONLY)
# =====================================================

@st.cache_data(ttl=30)
def get_data():

    url = "https://api.coingecko.com/api/v3/coins/bitcoin/ohlc?vs_currency=usd&days=1"

    try:
        r = requests.get(url, timeout=10)
        data = r.json()

        if not data or len(data) < 20:
            return None

        df = pd.DataFrame(data, columns=["time","open","high","low","close"])
        df["close"] = df["close"].astype(float)

        return df

    except:
        return None

def get_price(df):
    return float(df["close"].iloc[-1])

# =====================================================
# INDICATORS
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
    return float(last.iloc[-1]) if len(last) else 50

def ema(series, period):
    return series.ewm(span=period, adjust=False).mean()

def macd(series):
    ema12 = ema(series, 12)
    ema26 = ema(series, 26)

    macd_line = ema12 - ema26
    signal = ema(macd_line, 9)

    return macd_line.iloc[-1], signal.iloc[-1]

def momentum(df):
    if len(df) < 20:
        return 0
    return ((df["close"].iloc[-1] - df["close"].iloc[-20]) / df["close"].iloc[-20]) * 100

# =====================================================
# AI LOGIC
# =====================================================

def ai(rsi_v, macd_v, signal_v, mom):

    score = 0
    reasons = []

    if rsi_v < 30:
        score += 2
        reasons.append("RSI oversold")
    elif rsi_v > 70:
        score -= 2
        reasons.append("RSI overbought")

    if macd_v > signal_v:
        score += 2
        reasons.append("MACD bullish")
    else:
        score -= 2
        reasons.append("MACD bearish")

    if mom > 0:
        score += 1
        reasons.append("Positive momentum")
    else:
        score -= 1
        reasons.append("Negative momentum")

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
# BACKTEST
# =====================================================

def backtest(df):

    balance = 1000
    position = 0
    entry = 0

    for i in range(20, len(df)):

        window = df["close"].iloc[:i]

        rsi_v = rsi(window)
        macd_v, signal_v = macd(window)
        mom = momentum(df.iloc[:i])

        score = 0

        if rsi_v < 30:
            score += 2
        elif rsi_v > 70:
            score -= 2

        if macd_v > signal_v:
            score += 2
        else:
            score -= 2

        if mom > 0:
            score += 1
        else:
            score -= 1

        price = df["close"].iloc[i]

        if score >= 4 and position == 0:
            position = 1
            entry = price

        elif score <= -4 and position == 1:
            balance *= price / entry
            position = 0

    return balance

def buy_hold(df):
    return 1000 * (df["close"].iloc[-1] / df["close"].iloc[0])

def equity_curve(df):

    balance = 1000
    curve = []
    position = 0
    entry = 0

    for i in range(20, len(df)):

        window = df["close"].iloc[:i]

        rsi_v = rsi(window)
        macd_v, signal_v = macd(window)
        mom = momentum(df.iloc[:i])

        score = 0

        if rsi_v < 30:
            score += 2
        elif rsi_v > 70:
            score -= 2

        if macd_v > signal_v:
            score += 2
        else:
            score -= 2

        if mom > 0:
            score += 1
        else:
            score -= 1

        price = df["close"].iloc[i]

        if score >= 4 and position == 0:
            position = 1
            entry = price

        elif score <= -4 and position == 1:
            balance *= price / entry
            position = 0

        curve.append(balance)

    return curve

# =====================================================
# RUN
# =====================================================

df = get_data()

if df is None:
    st.error("Market data unavailable")
    st.stop()

price = get_price(df)

rsi_v = rsi(df["close"])
macd_v, signal_v = macd(df["close"])
mom = momentum(df)

decision, reasons, score = ai(rsi_v, macd_v, signal_v, mom)

save_signal(price, rsi_v, macd_v, signal_v, mom, decision, score)

# =====================================================
# UI
# =====================================================

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("BTC", f"${price:,.2f}")

with col2:
    st.metric("RSI", f"{rsi_v:.2f}")

with col3:
    st.metric("Momentum", f"{mom:.2f}%")

st.markdown(f"# 🧠 {decision}")
st.write(f"Score: {score}")

st.write("## 📋 Reasons")
for r in reasons:
    st.write("•", r)

# =====================================================
# ANALYTICS
# =====================================================

st.write("## 📊 Performance")

cursor.execute("SELECT * FROM signals ORDER BY id DESC LIMIT 50")
rows = cursor.fetchall()

log_df = pd.DataFrame(rows, columns=[
    "id","time","price","rsi","macd","signal","momentum","decision","score"
])

st.dataframe(log_df)

wins = len(log_df[log_df["score"] > 2])
losses = len(log_df[log_df["score"] < -2])

col1, col2 = st.columns(2)

with col1:
    st.metric("Wins", wins)

with col2:
    st.metric("Losses", losses)

# =====================================================
# BACKTEST SECTION
# =====================================================

st.write("## 📈 Backtest Results")

bt = backtest(df)
bh = buy_hold(df)

st.write(f"Strategy: ${bt:.2f}")
st.write(f"Buy & Hold: ${bh:.2f}")

st.write("## 📊 Equity Curve")
st.line_chart(equity_curve(df))

# =====================================================
# END
# =====================================================

st.caption("ZST LEVEL 2 PRO SaaS")
