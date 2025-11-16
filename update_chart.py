import yfinance as yf, pandas as pd, numpy as np, json, pathlib
from datetime import datetime, timedelta

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
HIGHLIGHT_SYM   = "1155.KL"
BASE_DATE       = "2024-07-01"   # we'll find the nearest trading day
END_DATE        = datetime.today().strftime("%Y-%m-%d")
CACHE_DIR       = pathlib.Path("cache"); CACHE_DIR.mkdir(exist_ok=True)
# ----------------------------

def trading_calendar(start: str, end: str) -> pd.DatetimeIndex:
    """Return all trading days for KLSE using Maybank as proxy."""
    df = yf.download("1155.KL", start=start, end=end, progress=False)
    return df.index

def cached_download(ticker: str, cal: pd.DatetimeIndex) -> pd.Series:
    """Return Close series indexed by the KLSE calendar; forward fill gaps."""
    cache_file = CACHE_DIR / f"{ticker}.parquet"  # faster than CSV
    if cache_file.exists():
        s = pd.read_parquet(cache_file)
    else:
        df = yf.download(ticker, start=BASE_DATE, end=END_DATE, progress=False)
        s = df["Close"].dropna().rename(ticker)
        s.to_parquet(cache_file)
    # Reindex to common calendar; forward-fill up to 5 days, then stop
    return s.reindex(cal).ffill(limit=5)

def build_data():
    cal = trading_calendar(BASE_DATE, END_DATE)
    # Find the *last* trading day on or before BASE_DATE that has data for majority
    base_candidates = cal[cal <= pd.Timestamp(BASE_DATE)]
    base_day = base_candidates[-1]  # guaranteed trading day

    series_map = {t: cached_download(t, cal) for t in TICKER_NAME_MAP}
    # Verify base_day has prices for at least 8 out of 10 banks
    base_prices = {t: s.loc[base_day] for t, s in series_map.items() if pd.notna(s.loc[base_day])}
    if len(base_prices) < 8:
        raise ValueError(f"Base day {base_day} has data for only {len(base_prices)} banks; choose another date.")

    data = []
    for ticker, name in TICKER_NAME_MAP.items():
        s = series_map[ticker]
        if s.isna().all():
            prices = []  # truly no data at all
        else:
            # Drop leading NaNs and keep only weekly points (reduce size)
            s = s.dropna().asfreq('W-FRI', method='ffill')
            prices = [{"date": d.strftime("%Y-%m-%d"), "price": round(v, 4)}
                      for d, v in s.items()]
        data.append({"symbol": ticker, "name": name, "prices": prices})
    return data

def update_html(data):
    html = pathlib.Path("index.html")
    content = html.read_text(encoding="utf-8")
    updated = content.replace("/* JSON_DATA_PLACEHOLDER */", json.dumps(data))
    html.write_text(updated, encoding="utf-8")

if __name__ == "__main__":
    update_html(build_data())
