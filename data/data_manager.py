from __future__ import annotations
import pandas as pd
from data.storage import (load_subjects_df, save_subjects_df,
                           load_goals_df, save_goals_df,
                           load_sessions_df, save_sessions_df)

# returns a sorted list of all subject names for the current profile
def get_subjects() -> list[str]:
    df = load_subjects_df()
    subjects = [s.strip() for s in df["subject_name"].dropna().astype(str).tolist()
                if s.strip()]
    return sorted(list(set(subjects)), key=str.lower)

# adds a new subject - checks for duplicates and length limits first
def add_subject(subject_name: str) -> tuple[bool, str]:
    name = (subject_name or "").strip()
    if not name:            return False, "Subject name cannot be empty."
    if len(name) > 40:      return False, "Subject name must be 40 characters or less."
    if any(s.lower() == name.lower() for s in get_subjects()):
        return False, "That subject already exists."
    df = load_subjects_df()
    df.loc[len(df)] = {"subject_name": name}
    save_subjects_df(df)
    return True, "Subject added."

# removes a subject and cleans up any goals/sessions linked to it
def delete_subject(subject_name: str) -> tuple[bool, str]:
    name = (subject_name or "").strip()
    if not name: return False, "No subject selected."
    df = load_subjects_df()
    df["subject_name"] = df["subject_name"].astype(str).str.strip()
    filtered = df[~df["subject_name"].str.lower().eq(name.lower())].copy()
    if len(filtered) == len(df):
        return False, "Subject not found."
    save_subjects_df(filtered.reset_index(drop=True))
    # also remove any goals and sessions that belong to this subject
    for load_fn, save_fn in [(load_goals_df, save_goals_df),
                              (load_sessions_df, save_sessions_df)]:
        d = load_fn()
        if not d.empty and "subject_name" in d.columns:
            d["subject_name"] = d["subject_name"].astype(str).str.strip()
            d = d[~d["subject_name"].str.lower().eq(name.lower())].copy()
            save_fn(d.reset_index(drop=True))
    return True, "Subject deleted (linked goals/sessions removed too)."
