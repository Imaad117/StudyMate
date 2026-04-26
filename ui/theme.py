"""
StudyMate theme — standardised purple accent.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path
import json

# ── Purple palette ────────────────────────────────────────────────────────────
PURPLE      = "#16a34a"   # main accent (green — best contrast on dark navy)
PURPLE_DARK = "#15803d"   # hover / active
PURPLE_MED  = "#22c55e"   # softer variant
PURPLE_LIGHT= "#dcfce7"   # tint backgrounds
PURPLE_XL   = "#f0fdf4"   # page background
PURPLE_TEXT = "#14532d"   # strong text on light bg
PURPLE_MID  = "#15803d"   # labels / secondary text

# ── Subject colour palette (orbs) ─────────────────────────────────────────────
SUBJECT_PALETTE = [
    "#7c3aed",  # purple
    "#2563eb",  # blue
    "#059669",  # green
    "#dc2626",  # red
    "#d97706",  # amber
    "#db2777",  # pink
    "#0891b2",  # cyan
    "#65a30d",  # lime
    "#7c3aed",  # violet
    "#ea580c",  # orange
]

# ── dark mode base ─────────────────────────────────────────────────────────────
DARK_BG    = "#0f172a"
DARK_CARD  = "#1e293b"
DARK_BORD  = "#334155"
DARK_TEXT  = "#f1f5f9"
DARK_MUTED = "#94a3b8"


@dataclass
class ThemeConfig:
    dark_mode: bool = False

    MAIN:   str = field(default=PURPLE,       init=False)
    DARK:   str = field(default=PURPLE_DARK,  init=False)
    LIGHT:  str = field(default=PURPLE_LIGHT, init=False)
    XLIGHT: str = field(default=PURPLE_XL,    init=False)
    TEXT:   str = field(default=PURPLE_TEXT,  init=False)
    MID:    str = field(default=PURPLE_MID,   init=False)
    MUTED:  str = field(default="#6b7280",    init=False)
    BORDER: str = field(default="#ddd6fe",    init=False)
    BG:     str = field(default=PURPLE_XL,   init=False)
    CARD:   str = field(default="#ffffff",    init=False)
    FG:     str = field(default=PURPLE_TEXT,  init=False)

    def __post_init__(self):
        self.apply()

    def apply(self):
        if self.dark_mode:
            self.BG     = DARK_BG
            self.CARD   = DARK_CARD
            self.BORDER = DARK_BORD
            self.FG     = DARK_TEXT
            self.MUTED  = DARK_MUTED
        else:
            self.BG     = PURPLE_XL
            self.CARD   = "#ffffff"
            self.BORDER = "#ddd6fe"
            self.FG     = PURPLE_TEXT
            self.MUTED  = "#6b7280"

    @property
    def F_HEAD(self):  return ("Segoe UI", 16, "bold")
    @property
    def F_SUB(self):   return ("Segoe UI", 11, "bold")
    @property
    def F_BODY(self):  return ("Segoe UI", 10)
    @property
    def F_SMALL(self): return ("Segoe UI", 9)
    @property
    def F_TIMER(self): return ("Consolas", 34, "bold")


THEME = ThemeConfig()


def load_and_apply_theme(settings_file: Path) -> None:
    try:
        data = json.loads(settings_file.read_text())
        THEME.dark_mode = data.get("dark_mode", False)
    except Exception:
        pass
    THEME.apply()


def apply_ttk_theme(style, t: ThemeConfig) -> None:
    style.theme_use("clam")
    style.configure(".",
        background=t.BG, foreground=t.FG,
        font=("Segoe UI", 10),
        bordercolor=t.BORDER, focuscolor=t.MAIN,
    )
    style.configure("TFrame",  background=t.BG)
    style.configure("TLabel",  background=t.BG, foreground=t.FG)
    style.configure("TNotebook",
        background=t.CARD, bordercolor=t.BORDER, tabmargins=[0,0,0,0])
    style.configure("TNotebook.Tab",
        background=t.CARD, foreground=t.MUTED,
        padding=[16, 9], font=("Segoe UI", 10),
        bordercolor=t.BORDER,
    )
    style.map("TNotebook.Tab",
        background=[("selected", t.BG),   ("active", t.LIGHT)],
        foreground=[("selected", t.DARK),  ("active", t.DARK)],
    )
    style.configure("TButton",
        background=t.LIGHT, foreground=t.DARK,
        relief="flat", padding=[12, 7],
        font=("Segoe UI", 10), bordercolor=t.BORDER,
    )
    style.map("TButton",
        background=[("active", t.MAIN),   ("pressed", t.DARK)],
        foreground=[("active", "#ffffff"), ("pressed", "#ffffff")],
    )
    style.configure("TEntry",
        fieldbackground=t.CARD, foreground=t.FG,
        bordercolor=t.BORDER, insertcolor=t.MAIN,
    )
    style.configure("TCombobox",
        fieldbackground=t.CARD, foreground=t.FG,
        bordercolor=t.BORDER,
        selectbackground=t.LIGHT, selectforeground=t.FG,
    )
    style.configure("Treeview",
        background=t.CARD, foreground=t.FG,
        fieldbackground=t.CARD, bordercolor=t.BORDER, rowheight=28,
    )
    style.configure("Treeview.Heading",
        background=t.LIGHT, foreground=t.MID,
        font=("Segoe UI", 9, "bold"),
        bordercolor=t.BORDER, relief="flat",
    )
    style.map("Treeview",
        background=[("selected", t.LIGHT)],
        foreground=[("selected", t.TEXT)],
    )
    style.configure("TScrollbar",
        background=t.LIGHT, troughcolor=t.BG, bordercolor=t.BORDER)
    style.configure("TLabelframe",
        background=t.BG, bordercolor=t.BORDER, relief="solid")
    style.configure("TLabelframe.Label",
        background=t.BG, foreground=t.MID,
        font=("Segoe UI", 9, "bold"))
    style.configure("TSpinbox",
        fieldbackground=t.CARD, foreground=t.FG,
        bordercolor=t.BORDER,
    )


def pill_btn(parent, text, command, primary=True, **kw):
    t = THEME
    bg  = t.MAIN  if primary else t.LIGHT
    fg  = "white" if primary else t.DARK
    abg = t.DARK  if primary else t.MAIN
    return tk.Button(
        parent, text=text, command=command,
        bg=bg, fg=fg,
        activebackground=abg, activeforeground="white",
        relief="flat", cursor="hand2",
        font=("Segoe UI", 10, "bold") if primary else ("Segoe UI", 10),
        padx=kw.pop("padx", 18), pady=kw.pop("pady", 7),
        **kw
    )


import tkinter as tk
