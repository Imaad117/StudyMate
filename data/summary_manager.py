from __future__ import annotations
import pandas as pd
from datetime import datetime, timedelta
from data.storage import load_sessions_df


def _load_clean() -> pd.DataFrame:
    df = load_sessions_df()
    if df.empty:
        return df
    df["start_dt"] = pd.to_datetime(df["start_time"], errors="coerce")
    df["duration_seconds"] = pd.to_numeric(df["duration_seconds"], errors="coerce").fillna(0).astype(int)
    df["focus_pre"]  = pd.to_numeric(df["focus_pre"],  errors="coerce")
    df["focus_post"] = pd.to_numeric(df["focus_post"], errors="coerce")
    df["subject_name"] = df["subject_name"].astype(str).fillna("").str.strip()
    return df.dropna(subset=["start_dt"])


def get_last_7_days_summary() -> dict:
    empty = {
        "total_minutes": 0, "session_count": 0,
        "avg_focus_pre": None, "avg_focus_post": None,
        "minutes_by_subject": {}, "focus_trend": [],
    }
    df = _load_clean()
    if df.empty:
        return empty
    week = df[df["start_dt"] >= datetime.now() - timedelta(days=7)].copy()
    if week.empty:
        return empty
    total_minutes  = int(week["duration_seconds"].sum()) // 60
    session_count  = len(week)
    avg_focus_pre  = float(week["focus_pre"].mean())  if week["focus_pre"].notna().any()  else None
    avg_focus_post = float(week["focus_post"].mean()) if week["focus_post"].notna().any() else None
    minutes_by_subject = {
        k: round(v / 60, 1)
        for k, v in week.groupby("subject_name")["duration_seconds"].sum().items() if k
    }
    week_sorted = week.sort_values("start_dt")
    focus_trend = []
    for _, r in week_sorted.iterrows():
        if pd.notna(r["focus_pre"]) and pd.notna(r["focus_post"]):
            focus_trend.append({
                "date": r["start_dt"].strftime("%d %b"),
                "pre":  float(r["focus_pre"]),
                "post": float(r["focus_post"]),
            })
    return {
        "total_minutes": total_minutes, "session_count": session_count,
        "avg_focus_pre": avg_focus_pre, "avg_focus_post": avg_focus_post,
        "minutes_by_subject": minutes_by_subject, "focus_trend": focus_trend,
    }


def get_full_analytics() -> dict:
    """Extended analytics for the full dashboard."""
    df = _load_clean()

    empty = {
        "total_minutes_all": 0, "total_sessions_all": 0,
        "current_streak": 0, "longest_streak": 0,
        "best_focus_day": None, "best_subject_focus": None,
        "focus_improvement_pct": None,
        "minutes_by_subject_all": {},
        "sessions_by_weekday": {d: 0 for d in ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"]},
        "daily_minutes_30": {},
        "avg_session_length": 0,
        "most_studied_subject": None,
        "focus_trend_30": [],
    }

    if df.empty:
        return empty

    # ── all-time totals ───────────────────────────────────────────────────────
    total_minutes_all  = int(df["duration_seconds"].sum()) // 60
    total_sessions_all = len(df)
    avg_session_length = int(df["duration_seconds"].mean()) // 60 if len(df) else 0

    # ── streak calculation ────────────────────────────────────────────────────
    study_days = sorted(set(df["start_dt"].dt.date.tolist()))
    current_streak = 0
    longest_streak = 0
    streak = 1
    today  = datetime.now().date()
    # current streak (count back from today)
    for i in range(len(study_days) - 1, -1, -1):
        d = study_days[i]
        diff = (today - d).days
        if diff == 0 or diff == current_streak:
            current_streak += 1
        else:
            break
    if study_days and (today - study_days[-1]).days > 1:
        current_streak = 0
    # longest streak
    for i in range(1, len(study_days)):
        if (study_days[i] - study_days[i-1]).days == 1:
            streak += 1
            longest_streak = max(longest_streak, streak)
        else:
            streak = 1
    longest_streak = max(longest_streak, 1 if study_days else 0)

    # ── subject breakdown ─────────────────────────────────────────────────────
    mbs = {
        k: round(v / 60, 1)
        for k, v in df.groupby("subject_name")["duration_seconds"].sum().items() if k
    }
    most_studied = max(mbs, key=mbs.get) if mbs else None

    # ── sessions by weekday ───────────────────────────────────────────────────
    day_names = ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"]
    weekday_counts = {d: 0 for d in day_names}
    for d, count in df["start_dt"].dt.day_name().value_counts().items():
        short = d[:3]
        if short in weekday_counts:
            weekday_counts[short] = int(count)

    # ── daily minutes last 30 days ────────────────────────────────────────────
    last30 = df[df["start_dt"] >= datetime.now() - timedelta(days=30)].copy()
    daily_minutes = {}
    for i in range(29, -1, -1):
        d = (datetime.now() - timedelta(days=i)).strftime("%d %b")
        daily_minutes[d] = 0
    for date_str, grp in last30.groupby(last30["start_dt"].dt.strftime("%d %b")):
        if date_str in daily_minutes:
            daily_minutes[date_str] = int(grp["duration_seconds"].sum()) // 60

    # ── focus insights ────────────────────────────────────────────────────────
    focus_df = df.dropna(subset=["focus_pre", "focus_post"])
    focus_improvement_pct = None
    best_focus_day = None
    best_subject_focus = None

    if not focus_df.empty:
        avg_pre  = focus_df["focus_pre"].mean()
        avg_post = focus_df["focus_post"].mean()
        if avg_pre > 0:
            focus_improvement_pct = round(((avg_post - avg_pre) / avg_pre) * 100, 1)

        # best day of week for focus
        focus_df = focus_df.copy()
        focus_df["weekday"] = focus_df["start_dt"].dt.day_name()
        day_focus = focus_df.groupby("weekday")["focus_post"].mean()
        if not day_focus.empty:
            best_focus_day = day_focus.idxmax()

        # best subject for focus
        subj_focus = focus_df.groupby("subject_name")["focus_post"].mean()
        if not subj_focus.empty:
            best_subject_focus = subj_focus.idxmax()

    # ── 30-day focus trend ────────────────────────────────────────────────────
    trend_df = focus_df.sort_values("start_dt") if not focus_df.empty else pd.DataFrame()
    focus_trend_30 = []
    if not trend_df.empty:
        for _, r in trend_df.iterrows():
            focus_trend_30.append({
                "date": r["start_dt"].strftime("%d %b"),
                "pre":  float(r["focus_pre"]),
                "post": float(r["focus_post"]),
                "subject": r["subject_name"],
            })

    return {
        "total_minutes_all":    total_minutes_all,
        "total_sessions_all":   total_sessions_all,
        "current_streak":       current_streak,
        "longest_streak":       longest_streak,
        "best_focus_day":       best_focus_day,
        "best_subject_focus":   best_subject_focus,
        "focus_improvement_pct": focus_improvement_pct,
        "minutes_by_subject_all": mbs,
        "sessions_by_weekday":  weekday_counts,
        "daily_minutes_30":     daily_minutes,
        "avg_session_length":   avg_session_length,
        "most_studied_subject": most_studied,
        "focus_trend_30":       focus_trend_30,
    }
