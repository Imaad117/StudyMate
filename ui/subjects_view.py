from __future__ import annotations
from ui.scroll_helper import bind_mousewheel
import json
import tkinter as tk
from tkinter import ttk, messagebox
from data.data_manager import get_subjects, add_subject, delete_subject
from ui.theme import THEME
from ui.popup_helper import show_popup
import app_config as cfg

# 12 clearly distinct colours — each visually unique, all visible on dark backgrounds
COLOUR_PALETTE = [
    ("#7c3aed", "Purple"),
    ("#2563eb", "Blue"),
    ("#059669", "Green"),
    ("#dc2626", "Red"),
    ("#d97706", "Amber"),
    ("#db2777", "Pink"),
    ("#0891b2", "Cyan"),
    ("#ea580c", "Orange"),
    ("#be185d", "Rose"),
    ("#0d9488", "Teal"),
    ("#4f46e5", "Indigo"),
    ("#b45309", "Brown"),
]

# lightens a hex colour for tinted backgrounds (used for card previews etc)
def _lighten(hex_col: str, f: float = 0.82) -> str:
    h = hex_col.lstrip("#")
    r,g,b = int(h[0:2],16), int(h[2:4],16), int(h[4:6],16)
    return f"#{int(r+(255-r)*f):02x}{int(g+(255-g)*f):02x}{int(b+(255-b)*f):02x}"

# stores subject colours in memory so we're not reading the JSON file on every render
_subject_colours: dict[str, str] = {}
_colours_loaded_for: str = ""   # tracks which profile was last loaded

def _colours_file() -> "Path":
    # each profile has its own colours file
    return cfg.get_profile_dir() / "subject_colours.json"

def _load_colours() -> None:
    # only reload if we've switched profiles
    global _subject_colours, _colours_loaded_for
    profile = cfg.get_active_profile()
    if _colours_loaded_for == profile:
        return
    try:
        _subject_colours = json.loads(_colours_file().read_text())
    except Exception:
        _subject_colours = {}
    _colours_loaded_for = profile

def _save_colours() -> None:
    try:
        _colours_file().parent.mkdir(parents=True, exist_ok=True)
        _colours_file().write_text(json.dumps(_subject_colours))
    except Exception:
        pass

# used everywhere in the app to get the colour for a subject name
def get_subject_colour(name: str) -> str:
    _load_colours()
    if name in _subject_colours:
        return _subject_colours[name]
    # if no colour saved yet, pick one based on the name so it's always the same
    return COLOUR_PALETTE[sum(ord(c) for c in name) % len(COLOUR_PALETTE)][0]

def set_subject_colour(name: str, colour: str) -> None:
    _load_colours()
    _subject_colours[name] = colour
    _save_colours()

def reset_colours_cache() -> None:
    """Call when switching profiles so we reload the right colours."""
    global _colours_loaded_for
    _colours_loaded_for = ""


def _orb_picker(parent, selected_colour: list, on_pick, initial: str | None = None):
    """Render colour orbs in a 2-row grid. Returns list of (hex, canvas)."""
    orb_size = 36
    orbs = []
    initial = initial or COLOUR_PALETTE[0][0]
    cols = 6

    for i, (col_hex, _) in enumerate(COLOUR_PALETTE):
        cv = tk.Canvas(parent, width=orb_size, height=orb_size,
                       bg=parent.cget("bg"), highlightthickness=0, cursor="hand2")
        cv.grid(row=i//cols, column=i%cols, padx=5, pady=3)
        orbs.append((col_hex, cv))

    def _refresh(chosen):
        selected_colour[0] = chosen
        for ch, oc in orbs:
            oc.delete("all")
            if ch == chosen:
                oc.create_oval(0, 0, orb_size, orb_size,
                               fill=ch, outline="white", width=3)
            else:
                oc.create_oval(2, 2, orb_size-2, orb_size-2,
                               fill=ch, outline="")
        on_pick(chosen)

    for col_hex, cv in orbs:
        cv.bind("<Button-1>", lambda _e, c=col_hex: _refresh(c))

    _refresh(initial)
    return orbs


class SubjectsView(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=THEME.BG)
        _load_colours()   # load for current profile on init
        self._build()

    def _build(self):
        t = THEME
        top = tk.Frame(self, bg=t.CARD)
        top.pack(fill="x")
        tk.Frame(self, bg=t.MAIN, height=3).pack(fill="x")
        top_inner = tk.Frame(top, bg=t.CARD, padx=20, pady=14)
        top_inner.pack(fill="x")
        tk.Label(top_inner, text="Subjects", bg=t.CARD,
                 fg="#ffffff" if t.dark_mode else t.MAIN,
                 font=("Segoe UI", 18, "bold")).pack(side="left")
        self._count_lbl = tk.Label(top_inner, text="", bg=t.CARD,
                                   fg=t.MUTED, font=("Segoe UI", 10))
        self._count_lbl.pack(side="left", padx=(12, 0))
        tk.Button(top_inner, text="＋  Add subject",
                  command=self._open_add_popup,
                  bg=t.MAIN, fg="white",
                  activebackground=t.DARK, activeforeground="white",
                  relief="flat", cursor="hand2",
                  font=("Segoe UI", 10, "bold"),
                  padx=18, pady=7).pack(side="right")

        outer = tk.Frame(self, bg=t.BG)
        outer.pack(fill="both", expand=True, padx=20, pady=16)
        outer.rowconfigure(0, weight=1)
        outer.columnconfigure(0, weight=1)
        canvas = tk.Canvas(outer, bg=t.BG, highlightthickness=0)
        canvas.grid(row=0, column=0, sticky="nsew")
        sb = ttk.Scrollbar(outer, orient="vertical", command=canvas.yview)
        sb.grid(row=0, column=1, sticky="ns")
        canvas.configure(yscrollcommand=sb.set)
        self._grid_frame = tk.Frame(canvas, bg=t.BG)
        self._win_id = canvas.create_window((0, 0), window=self._grid_frame, anchor="nw")
        self._grid_frame.bind("<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>", self._on_resize)
        bind_mousewheel(canvas)
        self._canvas = canvas
        self._refresh_grid()

    def _on_resize(self, event):
        self._canvas.itemconfig(self._win_id, width=event.width)
        self._refresh_grid()

    def _refresh_grid(self):
        t = THEME
        for w in self._grid_frame.winfo_children():
            w.destroy()
        subjects = get_subjects()
        n = len(subjects)
        self._count_lbl.configure(text=f"{n} subject{'s' if n != 1 else ''}")

        if not subjects:
            empty = tk.Frame(self._grid_frame, bg=t.BG)
            empty.pack(pady=60)
            ic = tk.Canvas(empty, width=90, height=90, bg=t.BG, highlightthickness=0)
            ic.pack()
            ic.create_oval(4, 4, 86, 86, fill=t.LIGHT, outline="")
            ic.create_text(45, 45, text="📚", font=("Segoe UI", 28))
            tk.Label(empty, text="No subjects yet",
                     bg=t.BG, fg="#ffffff" if t.dark_mode else t.TEXT,
                     font=("Segoe UI", 15, "bold")).pack(pady=(14, 6))
            tk.Label(empty, text="Add a subject to start tracking your study sessions.",
                     bg=t.BG, fg=t.MUTED, font=("Segoe UI", 10)).pack()
            tk.Button(empty, text="＋  Add your first subject",
                      command=self._open_add_popup,
                      bg=t.MAIN, fg="white",
                      activebackground=t.DARK, activeforeground="white",
                      relief="flat", cursor="hand2",
                      font=("Segoe UI", 11, "bold"),
                      padx=24, pady=10).pack(pady=(18, 0))
            return

        cw = self._canvas.winfo_width()
        cols = max(1, min(4, cw // 200))
        for i, name in enumerate(subjects):
            r, c = divmod(i, cols)
            self._grid_frame.columnconfigure(c, weight=1)
            self._subject_card(name, r, c)

    def _subject_card(self, name: str, row: int, col: int):
        t = THEME
        colour = get_subject_colour(name)
        card = tk.Frame(self._grid_frame, bg=t.CARD,
                        highlightthickness=1, highlightbackground=t.BORDER)
        card.grid(row=row, column=col, padx=8, pady=8, sticky="ew")
        card.columnconfigure(0, weight=1)
        tk.Frame(card, bg=colour, height=8).grid(row=0, column=0, columnspan=2, sticky="ew")
        av_f = tk.Frame(card, bg=t.CARD)
        av_f.grid(row=1, column=0, sticky="w", padx=16, pady=(14, 0))
        cv = tk.Canvas(av_f, width=46, height=46, bg=t.CARD, highlightthickness=0)
        cv.pack()
        cv.create_oval(2, 2, 44, 44, fill=colour, outline="")
        cv.create_text(23, 23, text=name[0].upper(), fill="white",
                       font=("Segoe UI", 17, "bold"))
        tk.Label(card, text=name, bg=t.CARD, fg=colour,
                 font=("Segoe UI", 12, "bold"), anchor="w").grid(
            row=2, column=0, sticky="w", padx=16, pady=(8, 16))
        btn_col = tk.Frame(card, bg=t.CARD)
        btn_col.grid(row=1, column=1, rowspan=2, sticky="ne", padx=(0, 10), pady=(10, 0))
        tk.Button(btn_col, text="✏", command=lambda n=name, c=colour: self._edit(n, c),
                  bg=t.CARD, fg=t.MUTED,
                  activebackground=t.LIGHT, activeforeground=t.DARK,
                  relief="flat", cursor="hand2", font=("Segoe UI", 12)).pack(pady=(0, 4))
        tk.Button(btn_col, text="✕", command=lambda n=name: self._delete(n),
                  bg=t.CARD, fg=t.MUTED,
                  activebackground="#fee2e2", activeforeground="#dc2626",
                  relief="flat", cursor="hand2", font=("Segoe UI", 12)).pack()
        card.bind("<Enter>", lambda _e, c=card: c.configure(highlightbackground=colour))
        card.bind("<Leave>", lambda _e, c=card: c.configure(highlightbackground=t.BORDER))

    def _popup_body(self, inner, selected_colour, initial_colour, name_var, preview_strip, avatar_cv):
        t = THEME

        def _draw_avatar():
            avatar_cv.delete("all")
            col = selected_colour[0]
            avatar_cv.create_oval(2, 2, 54, 54, fill=col, outline="")
            n = name_var.get().strip()
            if n:
                avatar_cv.create_text(28, 28, text=n[0].upper(),
                                      fill="white", font=("Segoe UI", 18, "bold"))

        def _on_type(*_):
            preview_strip.configure(bg=selected_colour[0])
            _draw_avatar()

        name_var.trace_add("write", _on_type)

        row_f = tk.Frame(inner, bg=t.CARD)
        row_f.grid(row=1, column=0, sticky="ew", pady=(0, 14))
        row_f.columnconfigure(0, weight=1)

        entry = tk.Entry(row_f, textvariable=name_var, font=("Segoe UI", 13),
                         bg="#1e293b" if t.dark_mode else t.BG,
                         fg="#e2e8f0" if t.dark_mode else t.FG,
                         insertbackground=selected_colour[0],
                         relief="flat", highlightthickness=2,
                         highlightbackground=selected_colour[0],
                         highlightcolor=selected_colour[0])
        entry.grid(row=0, column=0, sticky="ew", ipady=10)

        def _update_entry_colour():
            col = selected_colour[0]
            entry.configure(highlightbackground=col, highlightcolor=col,
                            insertbackground=col)

        tk.Label(inner, text="Choose a colour:", bg=t.CARD,
                 fg="#94a3b8" if t.dark_mode else t.MUTED,
                 font=("Segoe UI", 9, "bold")).grid(row=2, column=0, sticky="w", pady=(0, 8))
        orb_frame = tk.Frame(inner, bg=t.CARD)
        orb_frame.grid(row=3, column=0, sticky="w", pady=(0, 14))

        def _on_pick(col):
            selected_colour[0] = col
            preview_strip.configure(bg=col)
            _draw_avatar()
            _update_entry_colour()

        _orb_picker(orb_frame, selected_colour, _on_pick, initial=initial_colour)
        _draw_avatar()
        return entry

    def _open_add_popup(self):
        t = THEME
        root = self.winfo_toplevel()
        overlay, popup, body, _close = show_popup(root, 440, 400, title="Add Subject")
        hdr = tk.Frame(body, bg=t.LIGHT, padx=20, pady=14)
        hdr.pack(fill="x")
        tk.Label(hdr, text="New Subject", bg=t.LIGHT,
                 fg="#1e1b4b", font=("Segoe UI", 14, "bold")).pack(anchor="w")
        tk.Label(hdr, text="What are you studying?", bg=t.LIGHT, fg=t.MUTED,
                 font=("Segoe UI", 10)).pack(anchor="w", pady=(2, 0))
        inner = tk.Frame(body, bg=t.CARD, padx=24, pady=20)
        inner.pack(fill="both", expand=True)
        inner.columnconfigure(0, weight=1)
        selected_colour = [COLOUR_PALETTE[0][0]]
        name_var = tk.StringVar()
        preview_strip = tk.Frame(inner, bg=selected_colour[0], height=8)
        preview_strip.grid(row=0, column=0, sticky="ew", pady=(0, 14))
        avatar_cv = tk.Canvas(inner, width=56, height=56, bg=t.CARD, highlightthickness=0)
        err_lbl = tk.Label(inner, text="", bg=t.CARD, fg="#dc2626", font=("Segoe UI", 9))
        err_lbl.grid(row=4, column=0, sticky="w")
        entry = self._popup_body(inner, selected_colour, COLOUR_PALETTE[0][0],
                                  name_var, preview_strip, avatar_cv)
        entry.focus_set()

        def _save(_e=None):
            name = name_var.get().strip()
            ok, msg = add_subject(name)
            if not ok:
                err_lbl.configure(text=msg); return
            set_subject_colour(name, selected_colour[0])
            overlay.destroy(); popup.destroy()
            self._refresh_grid()

        tk.Button(inner, text="Add subject", command=_save,
                  bg=t.MAIN, fg="white", activebackground=t.DARK,
                  activeforeground="white", relief="flat", cursor="hand2",
                  font=("Segoe UI", 11, "bold"), pady=9).grid(
            row=5, column=0, sticky="ew", pady=(14, 0))
        entry.bind("<Return>", _save)

    def _edit(self, old_name: str, old_colour: str):
        t = THEME
        root = self.winfo_toplevel()
        overlay, popup, body, _close = show_popup(root, 440, 400, title="Edit Subject")
        hdr = tk.Frame(body, bg=t.LIGHT, padx=20, pady=14)
        hdr.pack(fill="x")
        tk.Label(hdr, text="Edit Subject", bg=t.LIGHT,
                 fg="#1e1b4b", font=("Segoe UI", 14, "bold")).pack(anchor="w")
        tk.Label(hdr, text=f"Editing: {old_name}", bg=t.LIGHT, fg=t.MUTED,
                 font=("Segoe UI", 10)).pack(anchor="w", pady=(2, 0))
        inner = tk.Frame(body, bg=t.CARD, padx=24, pady=20)
        inner.pack(fill="both", expand=True)
        inner.columnconfigure(0, weight=1)
        selected_colour = [old_colour]
        name_var = tk.StringVar(value=old_name)
        preview_strip = tk.Frame(inner, bg=old_colour, height=8)
        preview_strip.grid(row=0, column=0, sticky="ew", pady=(0, 14))
        avatar_cv = tk.Canvas(inner, width=56, height=56, bg=t.CARD, highlightthickness=0)
        err_lbl = tk.Label(inner, text="", bg=t.CARD, fg="#dc2626", font=("Segoe UI", 9))
        err_lbl.grid(row=4, column=0, sticky="w")
        entry = self._popup_body(inner, selected_colour, old_colour,
                                  name_var, preview_strip, avatar_cv)
        entry.focus_set()

        def _save(_e=None):
            new_name = name_var.get().strip()
            if not new_name:
                err_lbl.configure(text="Name cannot be empty."); return
            if new_name != old_name:
                from data.data_manager import get_subjects
                if any(s.lower() == new_name.lower() for s in get_subjects() if s != old_name):
                    err_lbl.configure(text="That subject already exists."); return
                delete_subject(old_name)
                add_subject(new_name)
            set_subject_colour(new_name, selected_colour[0])
            overlay.destroy(); popup.destroy()
            self._refresh_grid()

        tk.Button(inner, text="Save changes", command=_save,
                  bg=t.MAIN, fg="white", activebackground=t.DARK,
                  activeforeground="white", relief="flat", cursor="hand2",
                  font=("Segoe UI", 11, "bold"), pady=9).grid(
            row=5, column=0, sticky="ew", pady=(14, 0))
        entry.bind("<Return>", _save)

    def _delete(self, name: str):
        t = THEME
        root = self.winfo_toplevel()
        overlay, popup, body, _close = show_popup(root, 380, 210,
                                                   title="Delete Subject", accent_strip=False)
        tk.Frame(body, bg="#ef4444", height=5).pack(fill="x")
        inner = tk.Frame(body, bg=t.CARD, padx=24, pady=24)
        inner.pack(fill="both", expand=True)
        tk.Label(inner, text="Delete subject?", bg=t.CARD,
                 fg="#e2e8f0" if t.dark_mode else t.TEXT,
                 font=("Segoe UI", 13, "bold")).pack(anchor="w")
        tk.Label(inner, text=f"'{name}' and all its data will be removed.",
                 bg=t.CARD, fg=t.MUTED, font=("Segoe UI", 10),
                 justify="left").pack(anchor="w", pady=(8, 20))
        row = tk.Frame(inner, bg=t.CARD)
        row.pack(fill="x")

        def _confirm():
            overlay.destroy(); popup.destroy()
            ok, msg = delete_subject(name)
            if not ok: messagebox.showerror("Error", msg)
            else: self._refresh_grid()

        tk.Button(row, text="Delete", command=_confirm, bg="#ef4444", fg="white",
                  activebackground="#dc2626", activeforeground="white",
                  relief="flat", cursor="hand2",
                  font=("Segoe UI", 10, "bold"), padx=20, pady=7).pack(side="left")
        tk.Button(row, text="Cancel", command=_close, bg=t.LIGHT, fg=t.DARK,
                  relief="flat", cursor="hand2", padx=20, pady=7).pack(side="left", padx=(10, 0))

    def refresh(self):
        _load_colours()
        self._refresh_grid()
