from __future__ import annotations
import pandas as pd
from app_config import (
    get_profile_dir, get_subjects_csv,
    get_sessions_csv, get_goals_csv, get_flashcards_csv,
)

# defines what columns each CSV file should have
SUBJECTS_CSV_COLUMNS = ["subject_name", "colour"]
SESSIONS_COLUMNS   = ["session_id","subject_name","start_time","end_time",
                       "duration_seconds","focus_pre","focus_post","reflection"]
GOALS_COLUMNS      = ["goal_id","subject_name","goal_text",
                       "created_at","is_completed","completed_at","deadline"]
FLASHCARDS_COLUMNS = ["card_id","subject_name","front","back","created_at"]

def ensure_storage_ready() -> None:
    # creates the CSV files if they don't exist yet (first run for this profile)
    profile_dir = get_profile_dir()
    profile_dir.mkdir(parents=True, exist_ok=True)
    for path, cols in [
        (get_sessions_csv(),   SESSIONS_COLUMNS),
        (get_goals_csv(),      GOALS_COLUMNS),
        (get_flashcards_csv(), FLASHCARDS_COLUMNS),
    ]:
        if not path.exists():
            pd.DataFrame(columns=cols).to_csv(path, index=False)


def _safe_read(path, columns) -> pd.DataFrame:
    # reads a CSV and forces all columns to be strings
    # this prevents pandas reading empty columns as float64 which causes crashes
    try:
        df = pd.read_csv(path, dtype=str)
    except Exception:
        # if the file doesn't exist or is broken, start fresh
        df = pd.DataFrame(columns=columns)
        df.to_csv(path, index=False)
    for col in columns:
        if col not in df.columns:
            df[col] = ""
        else:
            # replace any NaN values with empty string
            df[col] = df[col].fillna("").astype(str)
    return df[columns].copy()


def load_subjects_df() -> pd.DataFrame:
    ensure_storage_ready()
    return _safe_read(get_subjects_csv(), SUBJECTS_CSV_COLUMNS)

def save_subjects_df(df: pd.DataFrame) -> None:
    ensure_storage_ready()
    df.to_csv(get_subjects_csv(), index=False)

def load_sessions_df() -> pd.DataFrame:
    ensure_storage_ready()
    return _safe_read(get_sessions_csv(), SESSIONS_COLUMNS)

def save_sessions_df(df: pd.DataFrame) -> None:
    ensure_storage_ready()
    df.to_csv(get_sessions_csv(), index=False)

def append_session_row(row: dict) -> None:
    df = load_sessions_df()
    df.loc[len(df)] = row
    df.to_csv(get_sessions_csv(), index=False)

def load_goals_df() -> pd.DataFrame:
    ensure_storage_ready()
    df = _safe_read(get_goals_csv(), GOALS_COLUMNS)
    # convert is_completed to int so we can filter it properly
    df["is_completed"] = pd.to_numeric(
        df["is_completed"], errors="coerce").fillna(0).astype(int)
    return df

def save_goals_df(df: pd.DataFrame) -> None:
    ensure_storage_ready()
    df.to_csv(get_goals_csv(), index=False)

def load_flashcards_df() -> pd.DataFrame:
    ensure_storage_ready()
    return _safe_read(get_flashcards_csv(), FLASHCARDS_COLUMNS)

def save_flashcards_df(df: pd.DataFrame) -> None:
    ensure_storage_ready()
    df.to_csv(get_flashcards_csv(), index=False)
