from __future__ import annotations
import pandas as pd
from datetime import datetime, date
from data.storage import load_goals_df, save_goals_df

# just returns the current time as a string we can store
def _now_iso() -> str:
    return datetime.now().replace(microsecond=0).isoformat()

# makes sure a column is treated as text before we write into it
# pandas sometimes reads empty CSV columns as float64 which breaks string writes
def _str_col(df, col):
    df[col] = df[col].astype(str)
    return df

# returns all goals - pass active_only=True for the active tab, False for completed
def get_goals(active_only: bool = True) -> list[dict]:
    df = load_goals_df()
    # filter by whether the goal is completed or not
    completed_mask = df["is_completed"].isin(["1", "1.0", 1, True])
    df = df[~completed_mask] if active_only else df[completed_mask]
    df = df.sort_values("created_at", ascending=False)
    # build a clean list of dicts so the UI doesn't touch pandas directly
    rows = []
    for _, r in df.iterrows():
        rows.append({
            "goal_id":      int(pd.to_numeric(r["goal_id"], errors="coerce") or 0),
            "subject_name": str(r["subject_name"]),
            "goal_text":    str(r["goal_text"]),
            "created_at":   str(r["created_at"]),
            "completed_at": str(r.get("completed_at", "") or ""),
            "is_completed": 1 if str(r["is_completed"]) in ("1", "1.0") else 0,
            "deadline":     str(r.get("deadline", "") or ""),
        })
    return rows

# used by the session page to show goals relevant to the chosen subject
def get_goals_for_subject(subject_name: str) -> list[dict]:
    return [g for g in get_goals(active_only=True)
            if g["subject_name"].strip().lower() == subject_name.strip().lower()]

# adds a new goal to the CSV
def add_goal(subject_name: str, goal_text: str,
             deadline: str = "") -> tuple[bool, str]:
    subject_name = (subject_name or "").strip()
    goal_text    = (goal_text    or "").strip()
    deadline     = (deadline     or "").strip()
    if not subject_name: return False, "Pick a subject first."
    if not goal_text:    return False, "Type a goal first."
    df = load_goals_df()
    # auto-increment the ID
    new_id = 1 if df.empty else int(
        pd.to_numeric(df["goal_id"], errors="coerce").fillna(0).max()) + 1
    new_row = pd.DataFrame([{
        "goal_id": str(new_id), "subject_name": subject_name,
        "goal_text": goal_text, "created_at": _now_iso(),
        "is_completed": "0", "completed_at": "", "deadline": deadline,
    }])
    df = pd.concat([df, new_row], ignore_index=True)
    save_goals_df(df)
    return True, "Goal added."

# lets the user edit the text or deadline of an existing goal
def update_goal(goal_id, goal_text: str = None,
                deadline: str = None) -> tuple[bool, str]:
    df = load_goals_df()
    mask = pd.to_numeric(df["goal_id"], errors="coerce").fillna(-1).astype(int) == int(goal_id)
    if not mask.any(): return False, "Goal not found."
    if goal_text is not None:
        df = _str_col(df, "goal_text")
        df.loc[mask, "goal_text"] = goal_text.strip()
    if deadline is not None:
        df = _str_col(df, "deadline")
        df.loc[mask, "deadline"] = deadline.strip()
    save_goals_df(df)
    return True, "Goal updated."

def delete_goal(goal_id) -> tuple[bool, str]:
    df = load_goals_df()
    mask = pd.to_numeric(df["goal_id"], errors="coerce").fillna(-1).astype(int) == int(goal_id)
    if not mask.any(): return False, "Goal not found."
    save_goals_df(df[~mask].copy())
    return True, "Goal deleted."

# marks a goal as done and records when it was completed
def complete_goal(goal_id) -> tuple[bool, str]:
    df = load_goals_df()
    mask = pd.to_numeric(df["goal_id"], errors="coerce").fillna(-1).astype(int) == int(goal_id)
    if not mask.any(): return False, "Goal not found."
    df = _str_col(df, "is_completed")
    df = _str_col(df, "completed_at")
    df.loc[mask, "is_completed"] = "1"
    df.loc[mask, "completed_at"] = _now_iso()
    save_goals_df(df)
    return True, "Goal marked as completed."

# moves a completed goal back to active
def uncomplete_goal(goal_id) -> tuple[bool, str]:
    df = load_goals_df()
    mask = pd.to_numeric(df["goal_id"], errors="coerce").fillna(-1).astype(int) == int(goal_id)
    if not mask.any(): return False, "Goal not found."
    df = _str_col(df, "is_completed")
    df = _str_col(df, "completed_at")
    df.loc[mask, "is_completed"] = "0"
    df.loc[mask, "completed_at"] = ""
    save_goals_df(df)
    return True, "Goal marked as active."

# works out what to display next to a deadline and what colour to show it in
# green = loads of time, red = overdue
def deadline_display(deadline_str: str) -> tuple[str, str]:
    if not deadline_str or str(deadline_str).lower() in ("", "none", "nan"):
        return "", "#6b7280"
    try:
        dl    = date.fromisoformat(str(deadline_str).strip())
        today = date.today()
        delta = (dl - today).days
        if delta < 0:   return f"Overdue by {abs(delta)}d", "#ef4444"
        elif delta == 0: return "Due today!", "#f97316"
        elif delta <= 3: return f"Due in {delta}d", "#f97316"
        elif delta <= 7: return f"Due in {delta}d", "#eab308"
        else:            return f"Due {dl.strftime('%d %b')}", "#22c55e"
    except Exception:
        return str(deadline_str), "#6b7280"
