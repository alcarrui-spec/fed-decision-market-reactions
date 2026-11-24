"""
Download daily market data.

- FRED (St. Louis Fed), free, no API key: Fed target range, Treasury yields,
  real yield, the dollar index and the S&P 500.
- Gold: FRED stopped carrying daily gold prices in 2022, so gold comes from
  Yahoo Finance via the yfinance package (COMEX gold futures, ticker GC=F).
"""
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "market_data.csv"

FRED_SERIES = {
    "DFEDTARU": "fed_upper",       # Fed funds target range, upper limit (%)
    "DFEDTARL": "fed_lower",       # Fed funds target range, lower limit (%)
    "DGS2": "yield_2y",            # 2-year Treasury yield (%)
    "DGS10": "yield_10y",          # 10-year Treasury yield (%)
    "DFII10": "real_yield_10y",    # 10-year TIPS (real) yield (%)
    "DTWEXBGS": "dollar_index",    # Broad U.S. dollar index (Jan 2006 = 100)
    "SP500": "sp500",              # S&P 500 index level
}
FRED_URL = "https://fred.stlouisfed.org/graph/fredgraph.csv?id={series}&cosd={start}"


def fetch_fred(series_id: str, start: str) -> pd.Series:
    """Download one FRED series as a daily Series. FRED marks missing days with '.'"""
    raw = pd.read_csv(FRED_URL.format(series=series_id, start=start), na_values=".")
    raw.columns = ["date", series_id]
    raw["date"] = pd.to_datetime(raw["date"])
    return raw.set_index("date")[series_id].astype(float)


def fetch_gold(start: str) -> pd.Series:
    """Daily gold futures settlement price (USD per ounce) from Yahoo Finance."""
    import yfinance as yf
    prices = yf.download("GC=F", start=start, progress=False, auto_adjust=False)
    close = prices["Close"]
    if isinstance(close, pd.DataFrame):      # newer yfinance returns one column per ticker
        close = close.iloc[:, 0]
    close.index = pd.to_datetime(close.index).tz_localize(None).normalize()
    return close.rename("gold").astype(float)


def load_market_data(start: str = "2024-10-01", refresh: bool = False) -> pd.DataFrame:
    """
    One row per U.S. trading day with every series.
    Saves a copy to data/market_data.csv so the analysis can be rerun offline.
    """
    if DATA_PATH.exists() and not refresh:
        return pd.read_csv(DATA_PATH, index_col="date", parse_dates=True)

    frames = [fetch_fred(sid, start).rename(name) for sid, name in FRED_SERIES.items()]
    try:
        frames.append(fetch_gold(start))
    except Exception as err:  # keep going without gold rather than failing the whole run
        print(f"Gold download failed ({err}); continuing without gold.")
    df = pd.concat(frames, axis=1).sort_index()

    # The Fed target range is published every calendar day; carry it forward.
    df[["fed_upper", "fed_lower"]] = df[["fed_upper", "fed_lower"]].ffill()
    # Keep trading days only (days with a 2-year Treasury yield).
    df = df[df["yield_2y"].notna()]
    DATA_PATH.parent.mkdir(exist_ok=True)
    df.to_csv(DATA_PATH, index_label="date")
    return df
