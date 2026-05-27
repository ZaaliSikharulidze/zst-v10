import streamlit as st
import pandas as pd
import numpy as np
import requests
import sqlite3
import os

# =====================================================
# SAFE IMPORT (NO CRASH)
# =====================================================

try:
    from sklearn.linear_model import LogisticRegression
    SKLEARN_OK = True
except:
    SKLEARN_OK = False

st.set_page_config(page_title="ZST NO CRASH SAAS", layout="wide")

st.title("🚀 ZST NO CRASH ARCHITECTURE SAAS")

# =====================================================
# AUTO REFRESH
# =====================================================

try:
    from streamlit_autorefresh import st_autorefresh
    st_autorefresh(interval=10000, key="refresh")
except:
    pass

# =====================================================
# SAFE DATABASE (AUTO RECOVERY)
# =====================================================

DB_PATH = "zst.db"

def init_db():

    try:
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
        return conn, cursor

    except Exception as e:

        if os.path.exists(DB_PATH):
            os.remove(DB_PATH)

        conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        cursor = conn.cursor()

        cursor.execute("""
        CREATE TABLE signals (
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
        return conn, cursor


conn, cursor = init_db()

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
# DATA (COINGECKO SAFE)
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
# FEATURES (SAFE SIMPLE VERSION)
# =====================================================

def safe_rsi(series):
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
# SIMPLE ML / FALLBACK MODEL
# =====================================================

def fallback_prob(rsi, mom):

    score = 0

    if rsi < 30:
        score += 1
    if mom > 0:
        score += 1

    return score / 2

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

rsi_v = safe_rsi(df["c"])
mom = momentum(df)
vol = volatility(df["c"])

prob = fallback_prob(rsi_v, mom)

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
# SAVE
# =====================================================

save_signal((
    price, rsi_v, 0, 0,
    mom, vol, prob, decision
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
# LOGS
# =====================================================

cursor.execute("SELECT * FROM signals ORDER BY id DESC LIMIT 50")
rows = cursor.fetchall()

log_df = pd.DataFrame(rows, columns=[
    "id","time","price","rsi","macd","signal",
    "momentum","volatility","prob","decision"
])

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

st.caption("🚀 ZST NO CRASH SAAS - STABLE VERSION")
