from __future__ import annotations
from pathlib import Path
from datetime import datetime
import shutil
import app_config as cfg

def _ts() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")

def export_backup(destination_folder: str) -> tuple[bool, str, str]:
    dest    = Path(destination_folder).expanduser().resolve()
    profile = cfg.get_active_profile()
    # include profile name in folder so it's clear whose data this is
    folder  = dest / f"studymate_backup_{profile}_{_ts()}"
    folder.mkdir(parents=True, exist_ok=True)

    # build the list of files to copy using the correct profile-aware functions
    sources = [
        cfg.get_subjects_csv(),
        cfg.get_sessions_csv(),
        cfg.get_goals_csv(),
        cfg.get_flashcards_csv(),
    ]

    # also include the colour preferences file if it exists
    colour_file = cfg.get_profile_dir() / "subject_colours.json"
    if colour_file.exists():
        sources.append(colour_file)

    copied = []
    for src in sources:
        if src.exists():
            shutil.copy2(src, folder / src.name)
            copied.append(src.name)

    if not copied:
        return False, "No data files found to export. Make sure you have added subjects and sessions first.", str(folder)

    return True, f"Exported {len(copied)} file(s): {', '.join(copied)}", str(folder)


def import_backup(backup_folder: str) -> tuple[bool, str]:
    # accept either a folder path or a path to one of the individual CSVs inside a backup folder
    src_path = Path(backup_folder).expanduser().resolve()

    # if the user pointed to a file, use its parent folder
    if src_path.is_file():
        src_path = src_path.parent

    if not src_path.is_dir():
        return False, "Please select the backup folder (not a file)."

    # map of filenames to where they should be restored
    restore_map = {
        "studymate_subjects.csv":   cfg.get_subjects_csv(),
        "studymate_sessions.csv":   cfg.get_sessions_csv(),
        "studymate_goals.csv":      cfg.get_goals_csv(),
        "studymate_flashcards.csv": cfg.get_flashcards_csv(),
        "subject_colours.json":     cfg.get_profile_dir() / "subject_colours.json",
    }

    restored = []
    for filename, dest in restore_map.items():
        src_file = src_path / filename
        if src_file.exists():
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src_file, dest)
            restored.append(filename)

    if not restored:
        return False, "No recognisable backup files found in that folder."

    return True, f"Restored {len(restored)} file(s): {', '.join(restored)}"
