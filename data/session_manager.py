from __future__ import annotations
from datetime import datetime
from data.storage import append_session_row

# get current time as a string for storing in the CSV
def now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")

# focus rating has to be a whole number from 1-5
def validate_focus(value: int) -> bool:
    return isinstance(value, int) and 1 <= value <= 5

# saves a completed session to the CSV after doing some basic checks
def add_session(subject_name, start_time, end_time, duration_seconds,
                focus_pre, focus_post, reflection) -> tuple[bool, str]:
    subject    = (subject_name or "").strip()
    reflection = (reflection   or "").strip()

    # validation - catch obvious problems before writing anything
    if not subject:
        return False, "Please select a subject."
    if not start_time or not end_time:
        return False, "Session start/end time missing."
    if duration_seconds <= 0:
        return False, "Session duration must be greater than 0 seconds."
    if not validate_focus(focus_pre) or not validate_focus(focus_post):
        return False, "Focus ratings must be between 1 and 5."
    if len(reflection) > 300:
        return False, "Reflection must be 300 characters or less."

    # write the session row to the CSV
    append_session_row({
        "start_time":       start_time,
        "end_time":         end_time,
        "duration_seconds": int(duration_seconds),
        "subject_name":     subject,
        "focus_pre":        int(focus_pre),
        "focus_post":       int(focus_post),
        "reflection":       reflection,
    })
    return True, "Session saved."
