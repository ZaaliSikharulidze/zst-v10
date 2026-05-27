import streamlit as st
import pandas as pd
import requests
import numpy as np
import sqlite3

st.set_page_config(page_title="ZST LEVEL 3 PRO ML", layout="wide")

st.title("🚀 ZST LEVEL 3 PRO ML SAAS")

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
    volatility REAL,
    probability REAL,
    decision TEXT,
    score REAL
)
""")

conn.commit()

def save_signal(data):
    cursor.execute("""
        INSERT INTO signals (
            price, rsi, macd, signal, momentum,
            volatility, probability, decision, score
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, data)
    conn.commit()

# =====================================================
# DATA (COINGECKO)
# =====================================================

@st.cache_data(ttl=30)
def get_data():

    url = "https://api.coingecko.com/api/v3/coins/bitcoin/ohlc?vs_currency=usd&days=1"

    r = requests.get(url, timeout=10)
    data = r.json()

    if not data or len(data) < 30:
        return None

    df = pd.DataFrame(data, columns=["time","open","high","low","close"])
    df["close"] = df["close"].astype(float)

    return df

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

    return float(rsi_series.dropna().iloc[-1]) if len(rsi_series.dropna()) else 50

def ema(series, period):
    return series.ewm(span=period, adjust=False).mean()

def macd(series):
    macd_line = ema(series, 12) - ema(series, 26)
    signal = ema(macd_line, 9)
    return macd_line.iloc[-1], signal.iloc[-1]

def momentum(df):
    if len(df) < 20:
        return 0
    return ((df["close"].iloc[-1] - df["close"].iloc[-20]) / df["close"].iloc[-20]) * 100

def volatility(series):
    return float(series.pct_change().std() * 100)

# =====================================================
# ML-LIKE PROBABILITY MODEL (NO LIBRARY VERSION)
# =====================================================

def ml_score(rsi_v, macd_v, signal_v, mom, vol):

    # normalize features
    rsi_score = (50 - rsi_v) / 50
    macd_score = 1 if macd_v > signal_v else -1
    mom_score = np.tanh(mom / 5)
    vol_penalty = -vol / 10

    raw = (
        rsi_score * 0.35 +
        macd_score * 0.35 +
        mom_score * 0.2 +
        vol_penalty * 0.1
    )

    # sigmoid → probability
    prob = 1 / (1 + np.exp(-raw))

    return float(prob), float(raw)

# =====================================================
# DYNAMIC THRESHOLD
# =====================================================

def threshold(vol):
    if vol > 2:
        return 0.65
    elif vol > 1:
        return 0.6
    return 0.55

# =====================================================
# BACKTEST (ML VERSION)
# =====================================================

def backtest(df):

    balance = 1000
    position = 0
    entry = 0
    fee = 0.001

    for i in range(30, len(df)):

        window = df["close"].iloc[:i]

        rsi_v = rsi(window)
        macd_v, signal_v = macd(window)
        mom = momentum(df.iloc[:i])
        vol = volatility(window)

        prob, _ = ml_score(rsi_v, macd_v, signal_v, mom, vol)

        th = threshold(vol)

        price = df["close"].iloc[i]

        if prob > th and position == 0:
            position = 1
            entry = price

        elif prob < (1 - th) and position == 1:
            balance *= (price / entry) * (1 - fee)
            position = 0

    return balance

def buy_hold(df):
    return 1000 * (df["close"].iloc[-1] / df["close"].iloc[0])

def equity_curve(df):

    balance = 1000
    curve = []
    position = 0
    entry = 0
    fee = 0.001

    for i in range(30, len(df)):

        window = df["close"].iloc[:i]

        rsi_v = rsi(window)
        macd_v, signal_v = macd(window)
        mom = momentum(df.iloc[:i])
        vol = volatility(window)

        prob, _ = ml_score(rsi_v, macd_v, signal_v, mom, vol)

        th = threshold(vol)

        price = df["close"].iloc[i]

        if prob > th and position == 0:
            position = 1
            entry = price

        elif prob < (1 - th) and position == 1:
            balance *= (price / entry) * (1 - fee)
            position = 0

        curve.append(balance)

    return curve

# =====================================================
# LOAD DATA
# =====================================================

df = get_data()

if df is None:
    st.error("Market data unavailable")
    st.stop()

price = get_price(df)

# =====================================================
# FEATURES
# =====================================================

rsi_v = rsi(df["close"])
macd_v, signal_v = macd(df["close"])
mom = momentum(df)
vol = volatility(df["close"])

prob, raw = ml_score(rsi_v, macd_v, signal_v, mom, vol)
th = threshold(vol)

decision = "🟢 BUY" if prob > th else "🔴 SELL/WAIT"

# =====================================================
# SAVE TO DB
# =====================================================

save_signal((
    price, rsi_v, macd_v, signal_v,
    mom, vol, prob, decision, raw
))

# =====================================================
# UI
# =====================================================

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("BTC", f"${price:,.2f}")

with col2:
    st.metric("Probability", f"{prob:.2f}")

with col3:
    st.metric("Volatility", f"{vol:.2f}%")

st.markdown(f"# 🧠 ML Decision: {decision}")

st.write(f"Threshold: {th:.2f}")

# =====================================================
# PERFORMANCE
# =====================================================

st.write("## 📊 Performance")

cursor.execute("SELECT * FROM signals ORDER BY id DESC LIMIT 50")
rows = cursor.fetchall()

log_df = pd.DataFrame(rows, columns=[
    "id","time","price","rsi","macd","signal",
    "momentum","volatility","probability","decision","score"
])

st.dataframe(log_df)

wins = len(log_df[log_df["probability"] > 0.6])
losses = len(log_df[log_df["probability"] <= 0.6])

col1, col2 = st.columns(2)

with col1:
    st.metric("Wins", wins)

with col2:
    st.metric("Losses", losses)

# =====================================================
# BACKTEST
# =====================================================

st.write("## 📈 Backtest")

bt = backtest(df)
bh = buy_hold(df)

st.write(f"ML Strategy: ${bt:.2f}")
st.write(f"Buy & Hold: ${bh:.2f}")

st.write("## 📊 Equity Curve")
st.line_chart(equity_curve(df))

st.caption("ZST LEVEL 3 PRO ML SaaS")
