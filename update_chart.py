import yfinance as yf
from datetime import datetime, timedelta
import json
import os

TOP_10_KLSE_BANKS = [
    "1155.KL", "1023.KL", "5819.KL", "6947.KL", "1295.KL",
    "5183.KL", "1066.KL", "1795.KL", "2481.KL", "9682.KL"
]

START_DATE = "2024-07-01"
END_DATE = datetime.today().strftime("%Y-%m-%d")

def fetch_data():
    data = []
    for symbol in TOP_10_KLSE_BANKS:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(start=START_DATE, end=END_DATE)
        prices = [
            {"date": date.strftime("%Y-%m-%d"), "price": round(row["Close"], 2)}
            for date, row in hist.iterrows()
        ]
        data.append({"symbol": symbol, "prices": prices})
    return data

def update_html(data):
    with open("index.html", "r", encoding="utf-8") as f:
        template = f.read()
    updated = template.replace("/* JSON_DATA_PLACEHOLDER */", json.dumps(data))
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(updated)

if __name__ == "__main__":
    data = fetch_data()
    update_html(data)
