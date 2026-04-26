from __future__ import annotations
from datetime import datetime, timedelta
import pandas as pd
from data.storage import load_sessions_df

# returns sessions filtered by subject and date range
# used by both the history tab and the session page's today's progress
def get_sessions_filtered(subject: str = "All", range_days: int | None = 7) -> list[dict]:
    df = load_sessions_df()
    if df.empty:
        return []

    # make sure all the columns we need actually exist
    needed = ["subject_name","start_time","end_time","duration_seconds",
              "focus_pre","focus_post","reflection"]
    for col in needed:
        if col not in df.columns:
            df[col] = ""

    # convert start_time to a proper datetime so we can filter by date
    df["start_dt"] = pd.to_datetime(df["start_time"], errors="coerce")

    # cut down to the date range if one was given
    if range_days is not None:
        df = df[df["start_dt"] >= datetime.now() - timedelta(days=range_days)]

    # filter by subject if not showing everything
    if subject != "All":
        df["subject_name"] = df["subject_name"].astype(str).str.strip()
        df = df[df["subject_name"] == subject]

    # newest sessions first
    df = df.sort_values("start_dt", ascending=False)

    rows = []
    for _, r in df.iterrows():
        secs = int(pd.to_numeric(r.get("duration_seconds", 0), errors="coerce") or 0)
        ref  = r.get("reflection", "")
        if pd.isna(ref):
            ref = ""
        rows.append({
            "start_time":       str(r.get("start_time", "")),
            "subject":          str(r.get("subject_name", "")),
            "duration_seconds": secs,
            "focus_pre":        str(r.get("focus_pre", "")),
            "focus_post":       str(r.get("focus_post", "")),
            "reflection":       str(ref),
        })
    return rows
