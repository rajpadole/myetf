import yfinance as yf
import pandas as pd
import requests
import os

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

TICKERS = [
    "NIFTYBEES.NS", "JUNIORBEES.NS", "MID150BEES.NS", "MOMENTUM50.NS",
    "BANKBEES.NS", "ITBEES.NS", "CPSEETF.NS", "AUTOIETF.NS", 
    "GOLDBEES.NS", "LIQUIDBEES.NS"
]

def calculate_rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def send_telegram_alert(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    params = {"chat_id": TELEGRAM_CHAT_ID, "text": text, "parse_mode": "Markdown"}
    response = requests.get(url, params=params)
    response.raise_for_status()

def scan_etfs():
    alert_message = "📊 *Daily ETF RSI Scan (Bottom Catching)*\n\n"
    found_setups = False

    for ticker in TICKERS:
        try:
            data = yf.download(ticker, period="3mo", interval="1d", progress=False)
            
            if len(data) >= 15:
                # 1. Safely extract Close column regardless of yfinance version
                if isinstance(data.columns, pd.MultiIndex):
                    close_col = data["Close"].iloc[:, 0]
                else:
                    close_col = data["Close"]
                
                # 2. Force to 1D series, ensure numeric, and completely drop NaNs
                close = pd.to_numeric(close_col.squeeze(), errors='coerce').dropna()
                
                # 3. Ensure we still have enough data to calculate RSI
                if len(close) < 15:
                    continue
                    
                rsi_series = calculate_rsi(close)
                
                current_rsi = round(float(rsi_series.iloc[-1]), 2)
                current_price = round(float(close.iloc[-1]), 2)

                if current_rsi < 35:
                    found_setups = True
                    target = round(current_price * 1.03, 2)
                    alert_message += f"🟢 *{ticker.replace('.NS', '')}*\n"
                    alert_message += f"• *RSI(14):* {current_rsi}\n"
                    alert_message += f"• *CMP:* ₹{current_price}\n"
                    alert_message += f"• *Target (+3%):* ₹{target}\n\n"
        except Exception as e:
            print(f"Error processing {ticker}: {e}")
            continue

    if not found_setups:
        alert_message += "No ETFs are currently below RSI 35 today. Keep cash in LIQUIDBEES."

    send_telegram_alert(alert_message)

if __name__ == "__main__":
    scan_etfs()
