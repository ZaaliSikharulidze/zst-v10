import streamlit as st
import pandas as pd
import numpy as np
import requests
import sqlite3

from sklearn.linear_model import LogisticRegression

st.set_page_config(page_title="ZST LEVEL 4 PRO FIXED", layout="wide")

st.title("🚀 ZST LEVEL 4 PRO ML (FIXED STABLE VERSION)")

# =====================================================
# AUTO REFRESH
# =====================================================

try:
    from streamlit_autorefresh import st_autorefresh
    st_autorefresh(interval=10000, key="refresh")
except:
    pass

# =====================================================
# DB (SAFE RESET-FREE VERSION)
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
    prob REAL,
    decision TEXT
)
""")

conn.commit()

def save(price, rsi, macd, signal, mom, vol, prob, decision):

    cursor.execute("""
        INSERT INTO signals (
            price, rsi, macd, signal,
            momentum, volatility, prob, decision
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        price, rsi, macd, signal,
        mom, vol, prob, decision
    ))

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

    df = pd.DataFrame(data, columns=["t","o","h","l","c"])
    df["c"] = df["c"].astype(float)

    return df

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
    rsi_val = 100 - (100 / (1 + rs))

    return float(rsi_val.dropna().iloc[-1]) if len(rsi_val.dropna()) else 50

def ema(s, p):
    return s.ewm(span=p, adjust=False).mean()

def macd(s):
    m = ema(s, 12) - ema(s, 26)
    sig = ema(m, 9)
    return float(m.iloc[-1]), float(sig.iloc[-1])

def momentum(df):
    if len(df) < 20:
        return 0
    return ((df["c"].iloc[-1] - df["c"].iloc[-20]) / df["c"].iloc[-20]) * 100

def volatility(series):
    return float(series.pct_change().std() * 100)

# =====================================================
# ML MODEL
# =====================================================

def train_model(X, y):
    model = LogisticRegression()
    model.fit(X, y)
    return model

def create_dataset(df):

    X, y = [], []

    for i in range(30, len(df)):

        window = df["c"].iloc[:i]

        r = rsi(window)
        m, s = macd(window)
        mom = momentum(df.iloc[:i])
        vol = volatility(window)

        X.append([r, m, s, mom, vol])

        future = df["c"].iloc[i] > df["c"].iloc[i-1]
        y.append(1 if future else 0)

    return np.array(X), np.array(y)

# =====================================================
# LOAD DATA
# =====================================================

df = get_data()

if df is None:
    st.error("Market data unavailable")
    st.stop()

price = df["c"].iloc[-1]

# =====================================================
# LIVE FEATURES
# =====================================================

r = rsi(df["c"])
m, s = macd(df["c"])
mom = momentum(df)
vol = volatility(df["c"])

# =====================================================
# TRAIN ML
# =====================================================

X, y = create_dataset(df)

model = train_model(X, y)

prob = model.predict_proba([[r, m, s, mom, vol]])[0][1]

# =====================================================
# DECISION
# =====================================================

if prob > 0.6:
    decision = "🟢 BUY"
elif prob < 0.4:
    decision = "🔴 SELL"
else:
    decision = "⚪ HOLD"

# =====================================================
# SAVE TO DB
# =====================================================

save(price, r, m, s, mom, vol, prob, decision)

# =====================================================
# UI
# =====================================================

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("BTC", f"${price:,.2f}")

with col2:
    st.metric("ML Probability", f"{prob:.2f}")

with col3:
    st.metric("Volatility", f"{vol:.2f}%")

st.markdown(f"# 🧠 Decision: {decision}")

st.write("## 📊 Live Indicators")

st.write({
    "RSI": r,
    "MACD": m,
    "Signal": s,
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
# PERFORMANCE
# =====================================================

wins = len(log_df[log_df["prob"] > 0.6])
losses = len(log_df[log_df["prob"] <= 0.6])

col1, col2 = st.columns(2)

with col1:
    st.metric("Wins", wins)

with col2:
    st.metric("Losses", losses)

st.caption("ZST LEVEL 4 PRO ML - FIXED STABLE VERSION")
