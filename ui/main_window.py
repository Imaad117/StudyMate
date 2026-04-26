from __future__ import annotations
import tkinter as tk
from tkinter import ttk, messagebox
import app_config as cfg
from ui.theme import THEME, apply_ttk_theme
from ui.session_view    import SessionView
from ui.subjects_view   import SubjectsView
from ui.goals_view      import GoalsView
from ui.summary_view    import SummaryView
from ui.history_view    import HistoryView
from ui.flashcards_view import FlashcardsView
from ui.data_view       import DataView
from ui.settings_view   import SettingsView
from ui.about_view      import AboutView


class StudyMateApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("StudyMate")
        # start maximised
        self.state("zoomed")          # Windows maximise
        self.minsize(800, 540)
        self.configure(bg=THEME.CARD)
        self.wm_attributes("-alpha", 0.0)

        self._style = ttk.Style(self)
        apply_ttk_theme(self._style, THEME)

        self._tab_frames: list[tk.Frame] = []
        self._tab_btns:   list[tk.Button] = []
        self._active_tab  = 0

        self._build_ui()
        self._alpha = 0.0
        self.after(20, self._fade_in)

    def _fade_in(self):
        self._alpha = min(1.0, self._alpha + 0.07)
        self.wm_attributes("-alpha", self._alpha)
        if self._alpha < 1.0:
            self.after(20, self._fade_in)

    def _build_ui(self):
        t = THEME

        # ── header ────────────────────────────────────────────────────────────
        hdr = tk.Frame(self, bg=t.CARD)
        hdr.pack(fill="x")
        tk.Frame(hdr, bg=t.MAIN, width=5).pack(side="left", fill="y")
        inner = tk.Frame(hdr, bg=t.CARD, padx=14, pady=10)
        inner.pack(side="left", fill="both", expand=True)

        logo_pill = tk.Frame(inner, bg=t.MAIN, padx=14, pady=5)
        logo_pill.pack(side="left")
        tk.Label(logo_pill, text="StudyMate", bg=t.MAIN, fg="white",
                 font=("Segoe UI", 14, "bold")).pack()

        profile = cfg.get_active_profile()
        self._badge_frame = tk.Frame(inner, bg=t.LIGHT, cursor="hand2",
                                     highlightthickness=1,
                                     highlightbackground=t.BORDER)
        self._badge_frame.pack(side="right", padx=(0, 4))
        self._badge_lbl = tk.Label(
            self._badge_frame,
            text=f"  {profile[0].upper()}  {profile}  ▾",
            bg=t.LIGHT, fg=t.DARK,
            font=("Segoe UI", 10, "bold"))
        self._badge_lbl.pack(padx=4, pady=6)

        for w in (self._badge_frame, self._badge_lbl):
            w.bind("<Button-1>", self._show_profile_menu)
            w.bind("<Enter>", lambda _e: (
                self._badge_frame.configure(bg=t.MAIN),
                self._badge_lbl.configure(bg=t.MAIN, fg="white")))
            w.bind("<Leave>", lambda _e: (
                self._badge_frame.configure(bg=t.LIGHT),
                self._badge_lbl.configure(bg=t.LIGHT, fg=t.DARK)))

        tk.Frame(self, bg=t.MAIN, height=3).pack(fill="x")

        # ── custom pill tab bar ───────────────────────────────────────────────
        tab_bar = tk.Frame(self, bg=t.BG, pady=8)
        tab_bar.pack(fill="x", padx=12)

        tabs = [
            ("Session",       SessionView),
            ("Subjects",      SubjectsView),
            ("Goals",         GoalsView),
            ("Summary",       SummaryView),
            ("History",       HistoryView),
            ("Flashcards",    FlashcardsView),
            ("Export/Import", DataView),
            ("Settings",      SettingsView),
            ("Help/About",    AboutView),
        ]

        # content area — fills all remaining space
        self._content = tk.Frame(self, bg=t.BG)
        self._content.pack(fill="both", expand=True)
        self._content.rowconfigure(0, weight=1)
        self._content.columnconfigure(0, weight=1)

        for i, (label, ViewClass) in enumerate(tabs):
            try:
                frame = ViewClass(self._content)
            except Exception as e:
                frame = tk.Frame(self._content, bg=t.BG)
                tk.Label(frame, text=f"Error loading {label}: {e}",
                         fg="red", bg=t.BG).pack(padx=20, pady=20)
            frame.place(relx=0, rely=0, relwidth=1, relheight=1)
            self._tab_frames.append(frame)

            btn = tk.Button(
                tab_bar, text=label,
                command=lambda idx=i: self._switch_tab(idx),
                bg=t.MAIN if i == 0 else t.BG,
                fg="white" if i == 0 else t.MID,
                activebackground=t.MAIN,
                activeforeground="white",
                relief="flat", cursor="hand2",
                font=("Segoe UI", 9, "bold") if i == 0 else ("Segoe UI", 9),
                padx=12, pady=5,
            )
            btn.pack(side="left", padx=3)
            self._tab_btns.append(btn)

        self._tab_frames[0].lift()
        # intercept the window X button so we can auto-save before closing
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _on_close(self):
        # save any running session then close the app normally
        self._auto_save_session()
        self.destroy()

    def _auto_save_session(self):
        # if a session is running when the user closes or logs out, save it silently
        # this way they don't lose study time just because something interrupted them
        try:
            session_view = self._tab_frames[0]
            if not getattr(session_view, "running", False):
                return
            import time as _time
            from data.session_manager import add_session, now_iso
            # figure out how much time actually elapsed
            if session_view.paused:
                duration = session_view.elapsed_before_pause
            else:
                duration = session_view.elapsed_before_pause + int(
                    _time.time() - (session_view.start_epoch or _time.time()))
            # don't save tiny accidental sessions (under 10 seconds)
            if duration < 10:
                return
            add_session(
                subject_name=session_view._subject,
                start_time=session_view.start_time_iso,
                end_time=now_iso(),
                duration_seconds=duration,
                focus_pre=int(session_view.focus_pre or 3),
                focus_post=int(session_view.focus_pre or 3),
                reflection="[Auto-saved on exit]")
        except Exception:
            pass  # never block the app from closing even if something goes wrong

    def _switch_tab(self, idx: int):
        t = THEME
        old = self._active_tab
        self._tab_btns[old].configure(bg=t.BG, fg=t.MID, font=("Segoe UI", 9))
        self._tab_btns[idx].configure(bg=t.MAIN, fg="white", font=("Segoe UI", 9, "bold"))
        self._tab_frames[idx].lift()
        self._active_tab = idx
        # Force geometry update so the newly-visible frame has real dimensions,
        # then call refresh so canvas-based views (flashcards, summary) draw correctly.
        self._content.update_idletasks()
        if hasattr(self._tab_frames[idx], "refresh"):
            self._tab_frames[idx].refresh()
        # Second deferred refresh catches any remaining layout settling
        self.after(80, lambda: (
            self._tab_frames[idx].refresh()
            if hasattr(self._tab_frames[idx], "refresh") else None
        ))

    def _show_profile_menu(self, _e=None):
        t = THEME
        popup = tk.Toplevel(self)
        popup.overrideredirect(True)
        popup.configure(bg=t.CARD, highlightthickness=1,
                        highlightbackground=t.BORDER)
        popup.wm_attributes("-topmost", True)
        self._badge_frame.update_idletasks()
        x = self._badge_frame.winfo_rootx()
        y = self._badge_frame.winfo_rooty() + self._badge_frame.winfo_height() + 2
        popup.geometry(f"200x152+{x}+{y}")
        tk.Frame(popup, bg=t.LIGHT).place(x=0, y=0, relwidth=1, height=42)
        tk.Label(popup, text=f"  {cfg.get_active_profile()}",
                 bg=t.LIGHT, fg=t.TEXT,
                 font=("Segoe UI", 11, "bold")).place(x=0, y=10)
        tk.Frame(popup, bg=t.BORDER, height=1).place(x=0, y=42, relwidth=1)

        def _item(text, y_pos, fg, cmd):
            row = tk.Frame(popup, bg=t.CARD, cursor="hand2")
            row.place(x=0, y=y_pos, relwidth=1, height=36)
            lbl = tk.Label(row, text=f"  {text}", bg=t.CARD, fg=fg,
                           font=("Segoe UI", 10), anchor="w")
            lbl.place(x=0, y=0, relwidth=1, relheight=1)
            def _on(_e, r=row, l=lbl): r.configure(bg=t.LIGHT); l.configure(bg=t.LIGHT)
            def _off(_e, r=row, l=lbl): r.configure(bg=t.CARD); l.configure(bg=t.CARD)
            for w in (row, lbl):
                w.bind("<Enter>", _on); w.bind("<Leave>", _off)
                w.bind("<Button-1>", lambda _e, c=cmd: (popup.destroy(), c()))

        _item("Switch profile", 44,  t.FG,      self._relaunch)
        _item("Log out",        80,  "#dc2626",  self._relaunch)
        _item("Exit app",       116, "#6b7280",  self._on_close)
        popup.bind("<FocusOut>", lambda _e: popup.destroy())
        popup.bind("<Escape>",   lambda _e: popup.destroy())
        popup.focus_set(); popup.lift()

    def _relaunch(self):
        self._auto_save_session()
        self.destroy()
        from ui.login_window import LoginWindow
        login = LoginWindow()
        login.mainloop()
        if login.get_chosen_profile():
            StudyMateApp().mainloop()
