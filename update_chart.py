#!/usr/bin/env python3
"""
GitHub-runner-proof daily-price updater for 10 KLSE banks.
Plots daily lines (no resample) → no string-index bugs.
"""

import yfinance as yf
import pandas as pd
import json
import pathlib
from datetime import datetime, timedelta

# ---------- config ----------
BANKS = {
    "1155.KL": "Maybank",
    "1295.KL": "Public Bank",
    "1023.KL": "CIMB",
    "5819.KL": "HLB",
    "1066.KL": "RHB",
    "1082.KL": "HLFG",
    "1015.KL": "AmBank",
    "2488.KL": "Alliance Bank",
    "1171.KL": "MBSB Bank",
    "5185.KL": "Affin Bank"
}
BASE_DATE     = "2024-07-01"
END_DATE      = (datetime.today() + timedelta(days=1)).strftime("%Y-%m-%d")
CACHE_DIR     = pathlib.Path("cache")
CACHE_DIR.mkdir(exist_ok=True)
# ----------------------------

def cached_download(ticker: str) -> pd.Series:
    """Daily Adj Close from Yahoo; parquet cache."""
    file = CACHE_DIR / f"{ticker}.parquet"
    if file.exists():
        return pd.read_parquet(file)
    s = yf.download(ticker, start="2024-06-25", end=END_DATE, auto_adjust=False, progress=False)["Adj Close"]
    s = s.dropna().rename(ticker)
    s.to_parquet(file)
    return s

def build_data():
    # 1. download all banks (daily)
    raw = {t: cached_download(t) for t in BANKS}

    # 2. common daily index + forward fill
    idx = pd.date_range(BASE_DATE, END_DATE, freq='D')
    df  = pd.DataFrame({t: raw[t].reindex(idx, method='ffill') for t in BANKS})
    df  = df.dropna(how='all')                # remove all-NaN rows

    # 3. rebase to 1.0 on first valid day
    base = df.iloc[0]
    rel  = df.div(base).fillna(method='ffill')

    # 4. build JSON for Plotly
    data = []
    for t, name in BANKS.items():
        prices = [{"date": d.strftime("%Y-%m-%d"), "price": round(v, 4)}
                  for d, v in rel[t].items()]
        data.append({"symbol": t, "name": name, "prices": prices})
    return data

def update_html(data):
    pathlib.Path("index.html").write_text(
        pathlib.Path("index.html").read_text(encoding="utf-8")
        .replace("/* JSON_DATA_PLACEHOLDER */", json.dumps(data)),
        encoding="utf-8"
    )

if __name__ == "__main__":
    update_html(build_data())
