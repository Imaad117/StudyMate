from __future__ import annotations
import json
import tkinter as tk
from tkinter import ttk
from ui.scroll_helper import bind_mousewheel
import app_config as cfg
from ui.theme import THEME

SETTINGS_FILE = cfg.APP_DATA_DIR / "settings.json"

DEFAULTS = {
    "reflection_reminder": True,
    "show_focus_bars":     True,
    "default_range":       "Last 7 days",
    "session_goal_mins":   60,
    "dark_mode":           False,
}


def load_settings() -> dict:
    try:
        return {**DEFAULTS, **json.loads(SETTINGS_FILE.read_text())}
    except Exception:
        return dict(DEFAULTS)


def save_settings(data: dict) -> None:
    cfg.APP_DATA_DIR.mkdir(parents=True, exist_ok=True)
    SETTINGS_FILE.write_text(json.dumps(data, indent=2))


class SettingsView(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=THEME.BG)
        self._s = load_settings()
        self._build()

    def _build(self):
        t = THEME

        top = tk.Frame(self, bg=t.CARD)
        top.pack(fill="x")
        tk.Frame(self, bg=t.MAIN, height=3).pack(fill="x")
        tk.Label(top, text="Settings", bg=t.CARD, fg="#ffffff" if t.dark_mode else t.MAIN,
                 font=("Segoe UI", 18, "bold")).pack(
            anchor="w", padx=20, pady=14)

        outer = tk.Frame(self, bg=t.BG)
        outer.pack(fill="both", expand=True)
        outer.rowconfigure(0, weight=1)
        outer.columnconfigure(0, weight=1)

        canvas = tk.Canvas(outer, bg=t.BG, highlightthickness=0)
        canvas.grid(row=0, column=0, sticky="nsew")
        sb = ttk.Scrollbar(outer, orient="vertical", command=canvas.yview)
        sb.grid(row=0, column=1, sticky="ns")
        canvas.configure(yscrollcommand=sb.set)

        body = tk.Frame(canvas, bg=t.BG)
        win = canvas.create_window((0, 0), window=body, anchor="nw")
        body.bind("<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>",
            lambda e: canvas.itemconfig(win, width=e.width))
        bind_mousewheel(canvas)
        body.columnconfigure(0, weight=1)

        def section(title, row):
            c = tk.Frame(body, bg=t.CARD,
                         highlightthickness=1, highlightbackground=t.BORDER)
            c.grid(row=row, column=0, sticky="ew", padx=20,
                   pady=(16 if row == 0 else 0, 12))
            c.columnconfigure(1, weight=1)
            tk.Label(c, text=title, bg=t.CARD, fg=t.MID,
                     font=("Segoe UI", 9, "bold")).grid(
                row=0, column=0, columnspan=3, sticky="w",
                padx=16, pady=(14, 8))
            return c

        def toggle_row(parent, row, label, var):
            tk.Label(parent, text=label, bg=t.CARD, fg=t.FG,
                     font=("Segoe UI", 10)).grid(
                row=row, column=0, sticky="w", padx=(16, 12), pady=(0, 10))
            lbl = tk.Label(parent, bg=t.CARD, font=("Segoe UI", 10, "bold"))
            lbl.grid(row=row, column=1, sticky="w", pady=(0, 10))

            def _refresh():
                lbl.configure(text="ON" if var.get() else "OFF",
                              fg=t.DARK if var.get() else t.MUTED)
            def _toggle():
                var.set(not var.get()); _refresh()

            tk.Button(parent, text="Toggle", command=_toggle,
                      bg=t.LIGHT, fg=t.DARK, relief="flat", cursor="hand2",
                      font=("Segoe UI", 9)).grid(
                row=row, column=2, sticky="e", padx=(0, 16), pady=(0, 10))
            _refresh()

        # ── appearance ────────────────────────────────────────────────────────
        app_sec = section("APPEARANCE", 0)
        self._dark_var = tk.BooleanVar(value=self._s.get("dark_mode", False))
        toggle_row(app_sec, 1, "Dark mode  (restart to apply)", self._dark_var)
        tk.Frame(app_sec, bg=t.CARD, height=4).grid(row=2, column=0)

        # ── session ───────────────────────────────────────────────────────────
        sess_sec = section("SESSION PREFERENCES", 1)
        self._reminder_var = tk.BooleanVar(value=self._s["reflection_reminder"])
        toggle_row(sess_sec, 1, "Prompt for reflection at end of session",
                   self._reminder_var)
        self._bars_var = tk.BooleanVar(value=self._s["show_focus_bars"])
        toggle_row(sess_sec, 2, "Show today's progress bars on Session tab",
                   self._bars_var)
        goal_row = tk.Frame(sess_sec, bg=t.CARD)
        goal_row.grid(row=3, column=0, columnspan=3, sticky="w",
                      padx=16, pady=(0, 14))
        tk.Label(goal_row, text="Daily study goal:", bg=t.CARD, fg=t.FG,
                 font=("Segoe UI", 10)).pack(side="left")
        self._goal_var = tk.IntVar(value=self._s["session_goal_mins"])
        ttk.Spinbox(goal_row, from_=15, to=480, increment=15,
                    textvariable=self._goal_var, width=6).pack(
            side="left", padx=(10, 6))
        tk.Label(goal_row, text="minutes", bg=t.CARD, fg=t.MUTED,
                 font=("Segoe UI", 9)).pack(side="left")

        # ── history ───────────────────────────────────────────────────────────
        hist_sec = section("HISTORY PREFERENCES", 2)
        hist_row = tk.Frame(hist_sec, bg=t.CARD)
        hist_row.grid(row=1, column=0, columnspan=3, sticky="w",
                      padx=16, pady=(0, 14))
        tk.Label(hist_row, text="Default range:", bg=t.CARD, fg=t.FG,
                 font=("Segoe UI", 10)).pack(side="left")
        self._range_var = tk.StringVar(value=self._s["default_range"])
        ttk.Combobox(hist_row, textvariable=self._range_var, state="readonly",
                     values=["Last 7 days", "Last 30 days", "All time"],
                     width=16).pack(side="left", padx=(10, 0))

        # ── profile ───────────────────────────────────────────────────────────
        prof_sec = section("ACTIVE PROFILE", 3)
        for i, (lbl, val) in enumerate([
            ("Profile:", cfg.get_active_profile()),
            ("Data folder:", str(cfg.get_profile_dir())),
        ]):
            tk.Label(prof_sec, text=lbl, bg=t.CARD, fg=t.FG,
                     font=("Segoe UI", 10)).grid(
                row=i+1, column=0, sticky="w", padx=(16,12), pady=(0,8))
            tk.Label(prof_sec, text=val, bg=t.CARD,
                     fg=t.DARK if i==0 else t.MUTED,
                     font=("Segoe UI",10,"bold") if i==0 else ("Segoe UI",9),
                     wraplength=500, anchor="w").grid(
                row=i+1, column=1, columnspan=2, sticky="w",
                padx=(0,16), pady=(0,8))
        tk.Frame(prof_sec, bg=t.CARD, height=4).grid(row=10, column=0)

        # ── save ──────────────────────────────────────────────────────────────
        save_row = tk.Frame(body, bg=t.BG)
        save_row.grid(row=4, column=0, sticky="w", padx=20, pady=(4, 20))
        self._status = tk.StringVar()
        tk.Button(save_row, text="Save settings", command=self._save,
                  bg=t.MAIN, fg="white",
                  activebackground=t.DARK, activeforeground="white",
                  relief="flat", cursor="hand2",
                  font=("Segoe UI", 10, "bold"),
                  padx=20, pady=8).pack(side="left")
        tk.Label(save_row, textvariable=self._status,
                 bg=t.BG, fg=t.DARK,
                 font=("Segoe UI", 9)).pack(side="left", padx=(14, 0))

    def _save(self):
        self._s.update({
            "dark_mode":           self._dark_var.get(),
            "reflection_reminder": self._reminder_var.get(),
            "show_focus_bars":     self._bars_var.get(),
            "default_range":       self._range_var.get(),
            "session_goal_mins":   int(self._goal_var.get()),
        })
        save_settings(self._s)
        self._status.set("✓  Saved! Restart to apply theme changes.")
        self.after(3000, lambda: self._status.set(""))
