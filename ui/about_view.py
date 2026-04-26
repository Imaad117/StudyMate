from __future__ import annotations
import tkinter as tk
from tkinter import ttk
import app_config as cfg
from ui.theme import THEME, pill_btn
from ui.scroll_helper import bind_mousewheel
BG=THEME.BG; WHITE=THEME.CARD; GREEN=THEME.MAIN; GREEN_D=THEME.DARK; GREEN_L=THEME.LIGHT; DARK=THEME.TEXT; MID=THEME.MID; MUTED=THEME.MUTED; BORDER=THEME.BORDER; FONT_HEADING=THEME.F_HEAD; FONT_BODY=THEME.F_BODY; FONT_SMALL=THEME.F_SMALL; FONT_TIMER=THEME.F_TIMER

VERSION = "1.0.0"

FEATURES = [
    ("Study sessions",    "Track how long you study, with a live timer and automatic saving."),
    ("Focus ratings",     "Rate your focus before and after each session (1–5) to spot patterns."),
    ("Reflections",       "Write a short note at the end of each session to capture key thoughts."),
    ("Goals",             "Set subject-specific study goals, mark them complete, and review history."),
    ("Flashcards",        "Create your own flashcards and review them one by one with a flip view."),
    ("Weekly summary",    "See total study time, session count, and two charts: time per subject and focus trend."),
    ("History",           "Browse all past sessions with subject and date range filters."),
    ("Multi-user profiles","Each person on the device has their own profile with separate data."),
    ("Export / Import",   "Back up and restore your data as CSV files at any time."),
    ("Fully offline",     "No internet, no accounts, no cloud. All data stays on your device."),
]

SHORTCUTS = [
    ("Enter",   "Submit forms and popups (focus ratings, reflections)"),
    ("Escape",  "Cancel / close any popup"),
    ("Tab",     "Move between fields in a form"),
]


class AboutView(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent, padding=0)
        self.columnconfigure(0, weight=1)
        self._build()

    def _build(self):
        # scrollable canvas
        canvas = tk.Canvas(self, bg=BG, highlightthickness=0)
        sb = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)
        bind_mousewheel(canvas)

        content = tk.Frame(canvas, bg=BG)
        window = canvas.create_window((0, 0), window=content, anchor="nw")

        def _on_resize(e):
            canvas.itemconfig(window, width=e.width)
        canvas.bind("<Configure>", _on_resize)

        def _on_frame_configure(_e):
            canvas.configure(scrollregion=canvas.bbox("all"))
        content.bind("<Configure>", _on_frame_configure)

        content.columnconfigure(0, weight=1)
        p = 16  # padding shorthand

        # ── hero banner ───────────────────────────────────────────────────────
        hero = tk.Frame(content, bg=GREEN, pady=24)
        hero.pack(fill="x")
        tk.Label(hero, text="StudyMate", bg=GREEN, fg=WHITE,
                 font=("Segoe UI", 24, "bold")).pack()
        tk.Label(hero, text=f"Version {VERSION}  ·  Offline Study Tracker",
                 bg=GREEN, fg=GREEN_L, font=("Segoe UI", 11)).pack(pady=(4, 0))
        tk.Label(hero, text="Built with Python · Tkinter · pandas · matplotlib",
                 bg=GREEN, fg=GREEN_L, font=("Segoe UI", 9)).pack(pady=(4, 0))

        body = tk.Frame(content, bg=BG, padx=p, pady=p)
        body.pack(fill="both", expand=True)
        body.columnconfigure(0, weight=1)

        # ── about blurb ───────────────────────────────────────────────────────
        blurb_card = tk.Frame(body, bg=WHITE, highlightthickness=1, highlightbackground=BORDER)
        blurb_card.pack(fill="x", pady=(0, 12))
        tk.Label(blurb_card, text="ABOUT", bg=WHITE, fg=MID,
                 font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=p, pady=(14, 6))
        tk.Label(blurb_card,
                 text=("StudyMate is a lightweight, fully offline desktop application designed to help "
                        "students log, reflect on, and improve their study habits. It stores everything "
                        "locally on your device — no accounts, no internet, no distractions.\n\n"
                        "Each user can create their own profile so that multiple people can share a "
                        "device while keeping their data completely separate."),
                 bg=WHITE, fg=DARK, font=("Segoe UI", 10),
                 wraplength=680, justify="left").pack(anchor="w", padx=p, pady=(0, 14))

        # active profile
        tk.Frame(blurb_card, bg=BORDER, height=1).pack(fill="x", padx=p)
        prof_row = tk.Frame(blurb_card, bg=WHITE)
        prof_row.pack(fill="x", padx=p, pady=(10, 14))
        tk.Label(prof_row, text="Active profile:", bg=WHITE, fg=DARK,
                 font=FONT_BODY).pack(side="left")
        tk.Label(prof_row, text=cfg.get_active_profile(), bg=WHITE, fg=GREEN_D,
                 font=("Segoe UI", 10, "bold")).pack(side="left", padx=(8, 0))

        # ── features ─────────────────────────────────────────────────────────
        feat_card = tk.Frame(body, bg=WHITE, highlightthickness=1, highlightbackground=BORDER)
        feat_card.pack(fill="x", pady=(0, 12))
        tk.Label(feat_card, text="FEATURES", bg=WHITE, fg=MID,
                 font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=p, pady=(14, 8))

        for name, desc in FEATURES:
            row = tk.Frame(feat_card, bg=WHITE)
            row.pack(fill="x", padx=p, pady=(0, 8))
            dot = tk.Frame(row, bg=GREEN, width=8, height=8)
            dot.pack(side="left", padx=(0, 10), pady=5)
            dot.pack_propagate(False)
            tk.Label(row, text=name, bg=WHITE, fg=GREEN_D,
                     font=("Segoe UI", 10, "bold"), width=18, anchor="w").pack(side="left")
            tk.Label(row, text=desc, bg=WHITE, fg=DARK,
                     font=("Segoe UI", 10), anchor="w", justify="left").pack(side="left", fill="x")

        tk.Frame(feat_card, bg=BG, height=6).pack()

        # ── keyboard shortcuts ────────────────────────────────────────────────
        keys_card = tk.Frame(body, bg=WHITE, highlightthickness=1, highlightbackground=BORDER)
        keys_card.pack(fill="x", pady=(0, 12))
        tk.Label(keys_card, text="KEYBOARD SHORTCUTS", bg=WHITE, fg=MID,
                 font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=p, pady=(14, 8))

        for key, desc in SHORTCUTS:
            row = tk.Frame(keys_card, bg=WHITE)
            row.pack(fill="x", padx=p, pady=(0, 8))
            key_badge = tk.Label(row, text=key, bg=GREEN_L, fg=GREEN_D,
                                 font=("Segoe UI", 9, "bold"),
                                 padx=8, pady=3, relief="flat")
            key_badge.pack(side="left", padx=(0, 12))
            tk.Label(row, text=desc, bg=WHITE, fg=DARK,
                     font=("Segoe UI", 10)).pack(side="left")

        tk.Frame(keys_card, bg=BG, height=6).pack()

        # ── data storage info ─────────────────────────────────────────────────
        data_card = tk.Frame(body, bg=WHITE, highlightthickness=1, highlightbackground=BORDER)
        data_card.pack(fill="x", pady=(0, 12))
        tk.Label(data_card, text="DATA STORAGE", bg=WHITE, fg=MID,
                 font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=p, pady=(14, 8))

        paths = [
            ("App data folder",  str(cfg.APP_DATA_DIR)),
            ("Profile folder",   str(cfg.get_profile_dir())),
            ("Subjects CSV",     str(cfg.get_subjects_csv())),
            ("Sessions CSV",     str(cfg.get_sessions_csv())),
            ("Goals CSV",        str(cfg.get_goals_csv())),
            ("Flashcards CSV",   str(cfg.get_flashcards_csv())),
        ]
        for label, path in paths:
            row = tk.Frame(data_card, bg=WHITE)
            row.pack(fill="x", padx=p, pady=(0, 6))
            tk.Label(row, text=label + ":", bg=WHITE, fg=DARK,
                     font=FONT_BODY, width=18, anchor="w").pack(side="left")
            tk.Label(row, text=path, bg=WHITE, fg=MUTED,
                     font=FONT_SMALL, anchor="w").pack(side="left", fill="x")

        tk.Frame(data_card, bg=BG, height=8).pack()

        # ── credits ───────────────────────────────────────────────────────────
        cred_card = tk.Frame(body, bg=WHITE, highlightthickness=1, highlightbackground=BORDER)
        cred_card.pack(fill="x", pady=(0, 16))
        tk.Label(cred_card, text="CREDITS", bg=WHITE, fg=MID,
                 font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=p, pady=(14, 8))
        tk.Label(cred_card,
                 text=("Developed by Imaad Malik (W2046639) as a Final Year Project\n"
                        "University of Westminster  ·  BSc (Hons) Computer Science\n"
                        "Supervisor: Stephen Roberts\n\n"
                        "Built using open-source libraries: Python 3, Tkinter, pandas, matplotlib."),
                 bg=WHITE, fg=DARK, font=("Segoe UI", 10),
                 justify="left").pack(anchor="w", padx=p, pady=(0, 14))
