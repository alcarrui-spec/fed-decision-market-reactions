"""
Event study: how did markets move on Fed decision days?

For each decision date t, the move is measured from the close on the trading
day before (t-1) to the close on the decision day (t0), which captures the
2:00 PM statement and the 2:30 PM press conference.

- Yields: change in basis points (1 bp = 0.01 percentage point)
- Dollar, S&P 500, gold: percent change
"""
import numpy as np
import pandas as pd

YIELDS = ["yield_2y", "yield_10y", "real_yield_10y"]
PRICES = ["dollar_index", "sp500", "gold"]

LABELS = {
    "yield_2y": "2-yr Treasury (bp)",
    "yield_10y": "10-yr Treasury (bp)",
    "real_yield_10y": "10-yr real yield (bp)",
    "dollar_index": "Dollar (%)",
    "sp500": "S&P 500 (%)",
    "gold": "Gold (%)",
}


def daily_changes(df: pd.DataFrame) -> pd.DataFrame:
    """Day-over-day change for each series: bp for yields, % for prices."""
    out = pd.DataFrame(index=df.index)
    for col in YIELDS:
        if col in df:
            out[col] = df[col].diff() * 100
    for col in PRICES:
        if col in df:
            out[col] = df[col].pct_change(fill_method=None) * 100
    return out


def classify_decisions(df: pd.DataFrame, dates) -> pd.DataFrame:
    """Read each decision from the Fed's own target range: Cut, Hold or Hike."""
    rows = []
    for d in dates:
        before = df.loc[df.index < d, "fed_upper"].iloc[-1]
        after = df.loc[df.index > d, "fed_upper"].iloc[0]   # new range takes effect the next day
        move = round((after - before) * 100)
        decision = "Hike" if move > 0 else ("Cut" if move < 0 else "Hold")
        low = df.loc[df.index > d, "fed_lower"].iloc[0]
        rows.append({"date": d, "decision": decision, "change_bp": move,
                     "target_range": f"{low:.2f}%–{after:.2f}%"})
    return pd.DataFrame(rows).set_index("date")


def decision_day_moves(df: pd.DataFrame, dates) -> pd.DataFrame:
    """Market moves on each decision day, joined to what the Fed decided."""
    changes = daily_changes(df)
    moves = changes.reindex(dates)
    moves.index.name = "date"
    return classify_decisions(df, dates).join(moves)


def fed_day_vs_normal(df: pd.DataFrame, dates) -> pd.DataFrame:
    """Average size of moves (ignoring direction) on Fed days vs. all other days."""
    changes = daily_changes(df).dropna(how="all")
    is_fed = changes.index.isin(dates)
    table = pd.DataFrame({
        "fed_days_avg_abs_move": changes[is_fed].abs().mean(),
        "other_days_avg_abs_move": changes[~is_fed].abs().mean(),
    })
    table["ratio"] = table["fed_days_avg_abs_move"] / table["other_days_avg_abs_move"]
    return table.rename(index=LABELS).round(2)


def event_window(df: pd.DataFrame, date, days: int = 20) -> pd.DataFrame:
    """
    Path of each series from `days` trading days before to `days` after an event.
    Yields: bp change vs. the day before the event. Prices: % change vs. that day.
    """
    pos = df.index.get_indexer([pd.Timestamp(date)], method="bfill")[0]
    window = df.iloc[pos - days: pos + days + 1].copy()
    base = window.iloc[days - 1]  # close on the day before the event (t-1)
    # label rows so the decision day is 0 and the day before is -1
    out = pd.DataFrame(index=np.arange(len(window)) - days)
    out.index.name = "trading_days_from_decision"
    for col in YIELDS:
        if col in window:
            out[col] = ((window[col] - base[col]) * 100).to_numpy()
    for col in PRICES:
        if col in window:
            out[col] = ((window[col] / base[col] - 1) * 100).to_numpy()
    return out
