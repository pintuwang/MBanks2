"""
Regenerate index.html with:
  - readable bank names
  - one bank highlighted
  - local CSV cache (folder `cache/`)
"""

import yfinance as yf
from datetime import datetime
import json, os, pandas as pd, pathlib

# ---------- config ----------
BASE_DATE     = "2024-07-22"
END_DATE      = datetime.today().strftime("%Y-%m-%d")
HIGHLIGHT_SYM = "1155.KL"          # <<<<< change here if you want another bank
CACHE_DIR     = pathlib.Path("cache")
CACHE_DIR.mkdir(exist_ok=True)

# ticker -> nice name
BANKS = {
    "1155.KL": "Maybank",
    "1295.KL": "Public Bank",
    "1023.KL": "CIMB",
    "5819.KL": "HLB",
    "1066.KL": "RHB",
    "1015.KL": "AmBank",
    "1082.KL": "HLFG",
    "2488.KL": "Alliance Bank",
    "1171.KL": "MBSB Bank",
    "5185.KL": "Affin Bank"
}

# ----------------------------

def cached_download(ticker: str) -> pd.DataFrame:
    """Return Yahoo history from cache or download then save."""
    cache_file = CACHE_DIR / f"{ticker}.csv"
    if cache_file.exists():
        df = pd.read_csv(cache_file, index_col=0, parse_dates=True)
    else:
        df = yf.Ticker(ticker).history(start=BASE_DATE, end=END_DATE)
        df.to_csv(cache_file)
    return df

def build_json():
    data = []
    for ticker, name in BANKS.items():
        df = cached_download(ticker)
        prices = [
            {"date": d.strftime("%Y-%m-%d"), "price": round(v, 4)}
            for d, v in df["Close"].items()
        ]
        data.append({"symbol": ticker, "name": name, "prices": prices})
    return data

def update_html(data):
    template_file = pathlib.Path("index.html")
    template = template_file.read_text(encoding="utf-8")
    updated = template.replace("/* JSON_DATA_PLACEHOLDER */", json.dumps(data))
    template_file.write_text(updated, encoding="utf-8")

if __name__ == "__main__":
    update_html(build_json())
