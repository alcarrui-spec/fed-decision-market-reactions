"""
FOMC policy decision dates, January 2025 to October 2026.

Each scheduled meeting runs two days; the decision is announced at 2:00 PM ET
on the second day, so that is the date used here. Source: Federal Reserve,
"Meeting calendars, statements, and minutes" (federalreserve.gov).

The August 22, 2025 notation vote approved a strategy statement, not a rate
decision, so it is not included.

What the Fed decided at each meeting is NOT typed in by hand: the notebook
reads it from the Fed's target range data (FRED series DFEDTARU / DFEDTARL),
so the labels always match the official record.
"""
import pandas as pd

DECISION_DATES = pd.to_datetime([
    # 2025
    "2025-01-29", "2025-03-19", "2025-05-07", "2025-06-18",
    "2025-07-30", "2025-09-17", "2025-10-29", "2025-12-10",
    # 2026
    "2026-01-28", "2026-03-18", "2026-04-29", "2026-06-17",
    "2026-07-29", "2026-09-16", "2026-10-28",
])

NEXT_MEETING = pd.Timestamp("2026-12-09")  # December 8-9, 2026
