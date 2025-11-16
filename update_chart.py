#!/usr/bin/env python3
"""
Regenerate index.html with:
  - 10 KLSE bank names
  - one bank highlighted
  - KLSE-trading-day calendar
  - parquet cache
  - weekly sampling (runner-proof scalar build)
"""

import yfinance as yf
import pandas as pd
import numpy as np
import json
import pathlib
from datetime import datetime

# ---------- config ----------
TICKER_NAME_MAP = {
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
HIGHLIGHT_SYM = "1155.KL"
END_DATE      = datetime.today().strftime("%Y-%m-%d")
CACHE_DIR     = pathlib.Path("cache")
CACHE_DIR.mkdir(exist_ok=True)
# ----------------------------

def trading_calendar(start: str, end: str) -> pd.DatetimeIndex:
    """All trading days for KLSE using Maybank as proxy."""
    df = yf.download("1155.KL", start=start, end=end, progress=False, auto_adjust=True)
    return df.index

def cached_download(ticker: str, cal: pd.DatetimeIndex) -> pd.Series:
    """Return Close series indexed by KLSE calendar; forward-fill gaps."""
    cache_file = CACHE_DIR / f"{ticker}.parquet"
    if cache_file.exists():
        s = pd.read_parquet(cache_file)
    else:
        df = yf.download(ticker, start="2024-04-01", end=END_DATE, progress=False, auto_adjust=True)
        s = df["Close"].dropna()
        s.name = ticker
        s.to_parquet(cache_file)
    return s.reindex(cal).ffill(limit=5)

def build_data():
    # 1. KLSE trading days
    cal = trading_calendar("2024-04-01", END_DATE)

    # 2. download each ticker (wide window)
    series_map = {t: cached_download(t, cal) for t in TICKER_NAME_MAP}

    # 3. first day with ≥1 price
    first_valid = None
    for day in cal:
        if any(bool(pd.notna(s.loc[day].item())) for s in series_map.values()):
            first_valid = day
            break
    if first_valid is None:
        raise RuntimeError("No prices at all – check tickers.")

    # 4. weekly Friday list – runner-proof scalar build
    data = []
    for ticker, name in TICKER_NAME_MAP.items():
        s = series_map[ticker]

        if s.isna().all().item():          # truly no data
            data.append({"symbol": ticker, "name": name, "prices": []})
            continue

        # drop NaNs and build weekly Fridays manually
        s = s.dropna()
        fri_days = pd.date_range(s.index.min(), s.index.max(), freq='W-FRI')

        weekly = []
        for fri in fri_days:
            # nearest price on or before Friday
            price = s.loc[:fri].iloc[-1] if not s.loc[:fri].empty else np.nan
            if pd.notna(price):
                weekly.append({"date": fri.strftime("%Y-%m-%d"),  # string
                               "price": round(float(price), 4)})
        data.append({"symbol": ticker, "name": name, "prices": weekly})
    return data

def update_html(data):
    html = pathlib.Path("index.html")
    content = html.read_text(encoding="utf-8")
    updated = content.replace("/* JSON_DATA_PLACEHOLDER */", json.dumps(data))
    html.write_text(updated, encoding="utf-8")

if __name__ == "__main__":
    update_html(build_data())
