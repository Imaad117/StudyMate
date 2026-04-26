from pathlib import Path

# ── directories ───────────────────────────────────────────────────────────────
APP_DATA_DIR = Path.home() / "Documents" / "StudyMate"
STORAGE_DIR  = APP_DATA_DIR / "storage"   # legacy only
PROFILES_DIR = APP_DATA_DIR / "profiles"

# ── active profile ────────────────────────────────────────────────────────────
_active_profile: str = "default"

def set_active_profile(name: str) -> None:
    global _active_profile
    _active_profile = name.strip() or "default"
    get_profile_dir().mkdir(parents=True, exist_ok=True)

def get_active_profile() -> str:
    return _active_profile

def get_profile_dir(name: str | None = None) -> Path:
    return PROFILES_DIR / (name or _active_profile)

# ── per-profile CSV paths (ALL data is now per-profile) ───────────────────────
def get_subjects_csv() -> Path:
    return get_profile_dir() / "studymate_subjects.csv"

def get_sessions_csv() -> Path:
    return get_profile_dir() / "studymate_sessions.csv"

def get_goals_csv() -> Path:
    return get_profile_dir() / "studymate_goals.csv"

def get_flashcards_csv() -> Path:
    return get_profile_dir() / "studymate_flashcards.csv"

# ── profile metadata (PIN stored here) ───────────────────────────────────────
import json

def _meta_path(name: str) -> Path:
    return get_profile_dir(name) / ".profile_meta.json"

def get_profile_meta(name: str) -> dict:
    try:
        return json.loads(_meta_path(name).read_text())
    except Exception:
        return {"pin": None, "display_name": name}

def save_profile_meta(name: str, meta: dict) -> None:
    get_profile_dir(name).mkdir(parents=True, exist_ok=True)
    _meta_path(name).write_text(json.dumps(meta))

def get_profile_pin(name: str) -> str | None:
    return get_profile_meta(name).get("pin")

def set_profile_pin(name: str, pin: str | None) -> None:
    meta = get_profile_meta(name)
    meta["pin"] = pin
    save_profile_meta(name, meta)

def verify_pin(name: str, pin: str) -> bool:
    stored = get_profile_pin(name)
    if stored is None:
        return True   # no PIN set — always allow
    return pin == stored

# ── profile management ────────────────────────────────────────────────────────
def list_profiles() -> list[str]:
    if not PROFILES_DIR.exists():
        return []
    return sorted(
        p.name for p in PROFILES_DIR.iterdir()
        if p.is_dir() and not p.name.startswith(".")
    )

def create_profile(name: str, pin: str | None = None) -> tuple[bool, str]:
    name = name.strip()
    if not name:
        return False, "Profile name cannot be empty."
    if len(name) > 30:
        return False, "Name must be 30 characters or less."
    bad = set(r'\/:*?"<>|')
    if any(c in bad for c in name):
        return False, "Name contains invalid characters."
    d = get_profile_dir(name)
    if d.exists():
        return False, f"'{name}' already exists."
    d.mkdir(parents=True, exist_ok=True)
    save_profile_meta(name, {"pin": pin, "display_name": name})
    return True, f"Profile '{name}' created."

def delete_profile(name: str, pin: str | None = None) -> tuple[bool, str]:
    import shutil
    if name == _active_profile:
        return False, "Cannot delete the active profile."
    stored_pin = get_profile_pin(name)
    if stored_pin is not None:
        if pin is None or pin != stored_pin:
            return False, "Incorrect PIN."
    d = get_profile_dir(name)
    if not d.exists():
        return False, "Profile not found."
    shutil.rmtree(d)
    return True, f"Profile '{name}' deleted."
