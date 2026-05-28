from fastapi import FastAPI
import numpy as np
import requests

app = FastAPI()

# =========================
# FEATURE ENGINE
# =========================

def get_price():
    url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd"
    data = requests.get(url, timeout=10).json()
    return float(data["bitcoin"]["usd"])

def generate_features():
    rsi = np.random.uniform(20, 80)
    mom = np.random.uniform(-2, 2)
    vol = np.random.uniform(0, 1)
    return rsi, mom, vol

# =========================
# SIMPLE ML LOGIC
# =========================

def predict(rsi, mom, vol):

    score = 0

    if rsi < 30:
        score += 1
    if mom > 0:
        score += 1

    prob = score / 2
    return prob

# =========================
# API ENDPOINT
# =========================

@app.get("/predict")
def predict_signal():

    price = get_price()
    rsi, mom, vol = generate_features()

    prob = predict(rsi, mom, vol)

    if prob > 0.6:
        decision = "BUY"
    elif prob < 0.4:
        decision = "SELL"
    else:
        decision = "HOLD"

    return {
        "price": price,
        "rsi": rsi,
        "momentum": mom,
        "volatility": vol,
        "probability": prob,
        "decision": decision
    }