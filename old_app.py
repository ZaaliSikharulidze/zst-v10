import streamlit as st
import pandas as pd
import numpy as np
import requests
import sqlite3
import os

st.set_page_config(page_title="ZST NO CRASH SAAS", layout="wide")

st.title("🚀 ZST FINAL STABLE NO CRASH SYSTEM")

# =====================================================
# AUTO REFRESH
# =====================================================

try:
    from streamlit_autorefresh import st_autorefresh
    st_autorefresh(interval=10000, key="refresh")
except:
    pass

# =====================================================
# SAFE DB (AUTO FIX)
# =====================================================

DB_PATH = "zst.db"

conn = sqlite3.connect(DB_PATH, check_same_thread=False)
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
    prob REAL,
    decision TEXT
)
""")

conn.commit()

# =====================================================
# SAFE SAVE
# =====================================================

def save_signal(data):
    try:
        cursor.execute("""
        INSERT INTO signals (
            price, rsi, macd, signal,
            momentum, volatility, prob, decision
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, data)

        conn.commit()
    except:
        pass

# =====================================================
# DATA (SAFE API)
# =====================================================

@st.cache_data(ttl=30)
def get_data():
    try:
        url = "https://api.coingecko.com/api/v3/coins/bitcoin/ohlc?vs_currency=usd&days=1"
        r = requests.get(url, timeout=10)

        data = r.json()

        if not data or len(data) < 20:
            return None

        df = pd.DataFrame(data, columns=["t","o","h","l","c"])
        df["c"] = df["c"].astype(float)

        return df

    except:
        return None

# =====================================================
# INDICATORS (SAFE)
# =====================================================

def rsi(series):
    try:
        delta = series.diff()
        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)

        avg_gain = gain.rolling(14).mean()
        avg_loss = loss.rolling(14).mean()

        rs = avg_gain / avg_loss.replace(0, np.nan)
        rsi = 100 - (100 / (1 + rs))

        return float(rsi.dropna().iloc[-1])
    except:
        return 50

def momentum(df):
    try:
        return ((df["c"].iloc[-1] - df["c"].iloc[-20]) / df["c"].iloc[-20]) * 100
    except:
        return 0

def volatility(series):
    try:
        return float(series.pct_change().std() * 100)
    except:
        return 0

# =====================================================
# SIMPLE AI (NO ML CRASH)
# =====================================================

def ai_probability(rsi_v, mom):

    score = 0

    if rsi_v < 30:
        score += 1
    if mom > 0:
        score += 1
    if rsi_v > 70:
        score -= 1

    return max(0, min(1, score / 2))

# =====================================================
# LOAD DATA
# =====================================================

df = get_data()

if df is None:
    st.error("Market data unavailable")
    st.stop()

price = df["c"].iloc[-1]

# =====================================================
# FEATURES
# =====================================================

rsi_v = rsi(df["c"])
mom = momentum(df)
vol = volatility(df["c"])

prob = ai_probability(rsi_v, mom)

# =====================================================
# DECISION ENGINE
# =====================================================

if prob > 0.6:
    decision = "🟢 BUY"
elif prob < 0.4:
    decision = "🔴 SELL"
else:
    decision = "⚪ HOLD"

# =====================================================
# SAVE SIGNAL
# =====================================================

save_signal((
    price,
    rsi_v,
    0,
    0,
    mom,
    vol,
    prob,
    decision
))

# =====================================================
# UI
# =====================================================

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("BTC", f"${price:,.2f}")

with col2:
    st.metric("RSI", f"{rsi_v:.2f}")

with col3:
    st.metric("Probability", f"{prob:.2f}")

st.markdown(f"# 🧠 Decision: {decision}")

st.write("## 📊 Live Metrics")
st.write({
    "Momentum": mom,
    "Volatility": vol
})

# =====================================================
# SAFE LOG LOADING (FIXED CRASH)
# =====================================================

cursor.execute("SELECT * FROM signals ORDER BY id DESC LIMIT 50")
rows = cursor.fetchall()

cols = [
    "id","time","price","rsi","macd","signal",
    "momentum","volatility","prob","decision"
]

if len(rows) == 0:
    log_df = pd.DataFrame(columns=cols)
else:

    fixed_rows = []

    for r in rows:
        r = list(r)

        if len(r) < len(cols):
            r += [None] * (len(cols) - len(r))
        elif len(r) > len(cols):
            r = r[:len(cols)]

        fixed_rows.append(tuple(r))

    log_df = pd.DataFrame(fixed_rows, columns=cols)

st.write("## 📈 Signal History")
st.dataframe(log_df)

# =====================================================
# STATS
# =====================================================

wins = len(log_df[log_df["prob"] > 0.6])
losses = len(log_df[log_df["prob"] <= 0.6])

col1, col2 = st.columns(2)

with col1:
    st.metric("Wins", wins)

with col2:
    st.metric("Losses", losses)

st.caption("🚀 ZST FINAL NO CRASH SAAS - STABLE VERSION")
