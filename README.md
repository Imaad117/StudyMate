# StudyMate

An offline desktop application for tracking study sessions, built with Python and Tkinter.

StudyMate lets students log their study sessions, rate their focus before and after each session, write short reflections, manage goals and flashcards, and view visual summaries of their study patterns — all without an internet connection or an account.

---

## Features

- **Session timing** — start, pause, resume, and end sessions with an optional duration target and progress bar
- **Focus ratings** — rate your focus 1–5 before and after each session to track quality over time
- **Reflections** — write a short note at the end of each session; it appears in the smart insight panel before your next session on the same subject
- **Subjects** — create colour-coded subjects to categorise your sessions
- **Goals** — set study goals with optional deadlines, mark them complete, and reactivate them if needed
- **Flashcards** — create flashcards with a live preview, review them in a full-screen flip viewer
- **Summary analytics** — four embedded charts showing time by subject, focus trends, day frequency, and daily minutes
- **History** — browse all past sessions with date range and subject filters
- **Multi-user profiles** — separate data directories per profile with optional PIN protection
- **Export and import** — back up and restore your data as plain CSV files

---

## Requirements

- Python 3.10 or later
- Windows 10 or 11 (packaged .exe) or any OS with Python installed (run from source)

---

## Running from Source

**1. Clone the repository**

```bash
git clone https://github.com/Imaad117/StudyMate.git
cd StudyMate
```

**2. Install dependencies**

```bash
pip install -r requirements.txt
```

**3. Run the application**

```bash
cd Prototype
python main.py
```

---

## Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| pandas | 3.0.0 | Session data storage and analytics |
| matplotlib | 3.10.8 | Chart rendering |
| Pillow | 12.1.0 | Avatar image rendering on profile screen |
| numpy | 2.4.2 | Required by matplotlib |

All other dependencies (Tkinter, csv, json, pathlib) are part of the Python standard library.

---

## Data Storage

All data is stored locally under `Documents/StudyMate/profiles/{profile_name}/` on your machine. Nothing is sent externally. Each profile directory contains:

```
profiles/
  YourName/
    studymate_sessions.csv
    studymate_subjects.csv
    studymate_goals.csv
    studymate_flashcards.csv
    subject_colours.json
    settings.json
    .profile_meta.json
```

---

## Project Structure

```
Prototype/
  main.py               — entry point
  app_config.py         — profile paths and configuration
  ui/                   — all view files (one per tab/dialog)
  data/                 — all data manager files
  requirements.txt      — Python dependencies
```

---

## Built With

- Python 3.13
- Tkinter — GUI
- pandas — data handling
- matplotlib — charts
- Pillow — image rendering

---

## Author

Imaad Malik — W2046639  
BSc (Hons) Computer Science  
University of Westminster  
Final Year Project, April 2026
