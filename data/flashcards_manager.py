from __future__ import annotations
import pandas as pd
from datetime import datetime
from data.storage import load_flashcards_df, save_flashcards_df

def _now_iso() -> str:
    return datetime.now().replace(microsecond=0).isoformat()

# same fix as in goals_manager - makes sure the column stays as text
def _str_col(df, col):
    df[col] = df[col].astype(str)
    return df

# gets all flashcards, optionally filtered to one subject
def get_flashcards(subject: str | None = None) -> list[dict]:
    df = load_flashcards_df()
    if df.empty:
        return []
    if subject and subject != "All":
        df["subject_name"] = df["subject_name"].astype(str).str.strip()
        df = df[df["subject_name"].str.lower() == subject.lower()]
    # newest cards show first
    df = df.sort_values("created_at", ascending=False)
    rows = []
    for _, r in df.iterrows():
        rows.append({
            "card_id":      int(pd.to_numeric(r["card_id"], errors="coerce") or 0),
            "subject_name": str(r["subject_name"]),
            "front":        str(r["front"]),
            "back":         str(r["back"]),
            "created_at":   str(r["created_at"]),
        })
    return rows

# saves a new card to the CSV
def add_flashcard(subject_name: str, front: str, back: str) -> tuple[bool, str]:
    subject_name = (subject_name or "").strip()
    front = (front or "").strip()
    back  = (back  or "").strip()
    # basic validation before saving
    if not subject_name: return False, "Pick a subject first."
    if not front:        return False, "Front of card cannot be empty."
    if not back:         return False, "Back of card cannot be empty."
    if len(front) > 200: return False, "Front must be 200 characters or less."
    if len(back)  > 200: return False, "Back must be 200 characters or less."
    df = load_flashcards_df()
    # auto-increment card ID
    new_id = 1 if df.empty else int(
        pd.to_numeric(df["card_id"], errors="coerce").fillna(0).max()) + 1
    new_row = pd.DataFrame([{
        "card_id": str(new_id), "subject_name": subject_name,
        "front": front, "back": back, "created_at": _now_iso()
    }])
    df = pd.concat([df, new_row], ignore_index=True)
    save_flashcards_df(df)
    return True, "Flashcard added."

# updates the front and back text of an existing card
def update_flashcard(card_id, front: str, back: str) -> tuple[bool, str]:
    front = (front or "").strip()
    back  = (back  or "").strip()
    if not front: return False, "Front of card cannot be empty."
    if not back:  return False, "Back of card cannot be empty."
    if len(front) > 200: return False, "Front must be 200 characters or less."
    if len(back)  > 200: return False, "Back must be 200 characters or less."
    df = load_flashcards_df()
    mask = pd.to_numeric(df["card_id"], errors="coerce").fillna(-1).astype(int) == int(card_id)
    if not mask.any(): return False, "Card not found."
    # make sure the columns are string type before writing
    df = _str_col(df, "front")
    df = _str_col(df, "back")
    df.loc[mask, "front"] = front
    df.loc[mask, "back"]  = back
    save_flashcards_df(df)
    return True, "Card updated."

def delete_flashcard(card_id) -> tuple[bool, str]:
    df = load_flashcards_df()
    mask = pd.to_numeric(df["card_id"], errors="coerce").fillna(-1).astype(int) == int(card_id)
    if not mask.any(): return False, "Card not found."
    save_flashcards_df(df[~mask].copy())
    return True, "Card deleted."
