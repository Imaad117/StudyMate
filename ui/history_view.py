from __future__ import annotations
from ui.scroll_helper import bind_mousewheel
import tkinter as tk
from tkinter import ttk
from data.data_manager import get_subjects
from data.history_manager import get_sessions_filtered
from ui.theme import THEME
from ui.subjects_view import get_subject_colour as _gsc

def _lighten(hex_col: str, f: float = 0.85) -> str:
    h = hex_col.lstrip("#")
    r,g,b = int(h[0:2],16), int(h[2:4],16), int(h[4:6],16)
    return f"#{int(r+(255-r)*f):02x}{int(g+(255-g)*f):02x}{int(b+(255-b)*f):02x}"

def _focus_colour(val: str) -> str:
    try:
        n = int(val)
        colours = ["#ef4444","#f97316","#eab308","#22c55e","#14b8a6"]
        return colours[n-1]
    except Exception:
        return "#9ca3af"

def _fmt_dur(secs: int) -> str:
    h, r = divmod(secs, 3600)
    m, s = divmod(r, 60)
    if h: return f"{h}h {m}m"
    if m: return f"{m}m {s}s"
    return f"{s}s"


class HistoryView(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=THEME.BG)
        self._range = "Last 7 days"
        self._subject = "All"
        self._build()

    def _build(self):
        t = THEME

        # ── top bar ───────────────────────────────────────────────────────────
        top = tk.Frame(self, bg=t.CARD)
        top.pack(fill="x")
        tk.Frame(self, bg=t.MAIN, height=3).pack(fill="x")
        top_inner = tk.Frame(top, bg=t.CARD, padx=20, pady=14)
        top_inner.pack(fill="x")
        tk.Label(top_inner, text="History", bg=t.CARD, fg="#ffffff" if t.dark_mode else t.MAIN,
                 font=("Segoe UI", 18, "bold")).pack(side="left")

        # ── filter bar ────────────────────────────────────────────────────────
        filter_outer = tk.Frame(self, bg=t.BG, padx=20, pady=10)
        filter_outer.pack(fill="x")

        # Row 1: time range pills
        range_row = tk.Frame(filter_outer, bg=t.BG)
        range_row.pack(fill="x", pady=(0, 6))
        tk.Label(range_row, text="Range:", bg=t.BG, fg=t.MUTED,
                 font=("Segoe UI", 9)).pack(side="left", padx=(0, 8))
        self._range_btns: list[tk.Button] = []
        for label in ["Last 7 days", "Last 30 days", "All time"]:
            is_active = (label == self._range)
            btn = tk.Button(
                range_row, text=label,
                command=lambda l=label: self._set_range(l),
                bg=t.MAIN if is_active else t.CARD,
                fg="white" if is_active else t.MUTED,
                activebackground=t.MAIN, activeforeground="white",
                relief="flat", cursor="hand2",
                font=("Segoe UI", 9, "bold" if is_active else "normal"),
                padx=14, pady=5)
            btn.pack(side="left", padx=(0, 6))
            self._range_btns.append(btn)

        self._session_count = tk.Label(range_row, text="", bg=t.BG,
                                        fg=t.MUTED, font=("Segoe UI", 9))
        self._session_count.pack(side="right")

        # Row 2: subject pills (populated in _load_subjects)
        self._subj_row = tk.Frame(filter_outer, bg=t.BG)
        self._subj_row.pack(fill="x")
        self._subject_btns: dict[str, tk.Button] = {}
        self._subject_var = tk.StringVar(value="All")

        # ── scrollable session cards ──────────────────────────────────────────
        outer = tk.Frame(self, bg=t.BG)
        outer.pack(fill="both", expand=True, padx=20, pady=(0, 16))
        outer.rowconfigure(0, weight=1)
        outer.columnconfigure(0, weight=1)

        canvas = tk.Canvas(outer, bg=t.BG, highlightthickness=0)
        canvas.grid(row=0, column=0, sticky="nsew")
        sb = ttk.Scrollbar(outer, orient="vertical", command=canvas.yview)
        sb.grid(row=0, column=1, sticky="ns")
        canvas.configure(yscrollcommand=sb.set)

        self._sess_frame = tk.Frame(canvas, bg=t.BG)
        win = canvas.create_window((0, 0), window=self._sess_frame, anchor="nw")
        self._sess_frame.bind("<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>",
            lambda e: canvas.itemconfig(win, width=e.width))

        bind_mousewheel(canvas)

        self._canvas = canvas
        self._filter_btns: list[tk.Button] = []
        self._load_subjects()
        self._render_sessions()

    def _set_range(self, label: str):
        self._range = label
        t = THEME
        for btn in self._range_btns:
            is_sel = (btn.cget("text") == label)
            btn.configure(bg=t.MAIN if is_sel else t.CARD,
                          fg="white" if is_sel else t.MUTED,
                          font=("Segoe UI", 9, "bold" if is_sel else "normal"))
        self._apply_filter()

    def _set_subject(self, name: str):
        self._subject_var.set(name)
        t = THEME
        for subj, btn in self._subject_btns.items():
            is_sel = (subj == name)
            colour = t.MAIN if subj == "All" else _gsc(subj)
            btn.configure(bg=colour if is_sel else t.CARD,
                          fg="white" if is_sel else t.MUTED,
                          font=("Segoe UI", 9, "bold" if is_sel else "normal"))
        self._apply_filter()

    def _apply_filter(self):
        self._subject = self._subject_var.get()
        self._render_sessions()

    def _load_subjects(self):
        t = THEME
        subjects = get_subjects()
        all_names = ["All"] + subjects
        current = self._subject_var.get()
        if current not in all_names:
            self._subject_var.set("All")
            current = "All"

        # Rebuild subject pill row
        for w in self._subj_row.winfo_children():
            w.destroy()
        self._subject_btns.clear()

        tk.Label(self._subj_row, text="Subject:", bg=t.BG, fg=t.MUTED,
                 font=("Segoe UI", 9)).pack(side="left", padx=(0, 8))

        for name in all_names:
            is_sel = (name == current)
            colour = t.MAIN if name == "All" else _gsc(name)
            btn = tk.Button(
                self._subj_row, text=name,
                command=lambda n=name: self._set_subject(n),
                bg=colour if is_sel else t.CARD,
                fg="white" if is_sel else t.MUTED,
                activebackground=colour, activeforeground="white",
                relief="flat", cursor="hand2",
                font=("Segoe UI", 9, "bold" if is_sel else "normal"),
                padx=12, pady=5)
            btn.pack(side="left", padx=(0, 5))
            self._subject_btns[name] = btn

    def _range_days(self) -> int | None:
        return {"Last 7 days": 7, "Last 30 days": 30}.get(self._range)

    def _render_sessions(self):
        t = THEME
        self._load_subjects()
        for w in self._sess_frame.winfo_children():
            w.destroy()

        rows = get_sessions_filtered(
            subject=self._subject_var.get(),
            range_days=self._range_days())

        self._session_count.configure(
            text=f"{len(rows)} session{'s' if len(rows) != 1 else ''}")

        if not rows:
            tk.Label(self._sess_frame,
                     text="No sessions found for this filter.",
                     bg=t.BG, fg=t.MUTED,
                     font=("Segoe UI", 11)).pack(pady=40)
            return

        for r in rows:
            self._session_card(r)

    def _session_card(self, r: dict):
        t = THEME
        subj   = r.get("subject", "")
        colour = _gsc(subj)
        tint   = _lighten(colour)

        card = tk.Frame(self._sess_frame, bg=t.CARD,
                        highlightthickness=1,
                        highlightbackground=t.BORDER)
        card.pack(fill="x", pady=5)
        card.columnconfigure(1, weight=1)

        # left colour bar
        tk.Frame(card, bg=colour, width=6).grid(
            row=0, column=0, rowspan=4, sticky="ns")

        # row 0: subject pill + date
        top_row = tk.Frame(card, bg=t.CARD)
        top_row.grid(row=0, column=1, sticky="ew", padx=(12,12), pady=(12,4))

        subj_pill = tk.Label(top_row,
                             text=f"  {subj}  ",
                             bg=tint, fg=colour,
                             font=("Segoe UI", 8, "bold"), padx=2, pady=3)
        subj_pill.pack(side="left")

        start = str(r.get("start_time","")).replace("T"," ")[:16]
        tk.Label(top_row, text=start, bg=t.CARD, fg=t.MUTED,
                 font=("Segoe UI", 9)).pack(side="right")

        # row 1: duration + focus indicators
        mid_row = tk.Frame(card, bg=t.CARD)
        mid_row.grid(row=1, column=1, sticky="ew", padx=(12,12), pady=(0,6))

        dur = _fmt_dur(r.get("duration_seconds", 0))
        tk.Label(mid_row, text=dur, bg=t.CARD, fg=t.TEXT,
                 font=("Segoe UI", 13, "bold")).pack(side="left")

        # focus before → after
        pre  = str(r.get("focus_pre",""))
        post = str(r.get("focus_post",""))
        pre_col  = _focus_colour(pre)
        post_col = _focus_colour(post)

        focus_frame = tk.Frame(mid_row, bg=t.CARD)
        focus_frame.pack(side="left", padx=(16, 0))
        tk.Label(focus_frame, text="Focus:", bg=t.CARD, fg=t.MUTED,
                 font=("Segoe UI", 9)).pack(side="left")

        # pre circle
        pre_c = tk.Canvas(focus_frame, width=24, height=24,
                           bg=t.CARD, highlightthickness=0)
        pre_c.pack(side="left", padx=(6, 2))
        pre_c.create_oval(2, 2, 22, 22, fill=pre_col, outline="")
        pre_c.create_text(12, 12, text=pre, fill="white",
                          font=("Segoe UI", 8, "bold"))

        tk.Label(focus_frame, text="→", bg=t.CARD, fg=t.MUTED,
                 font=("Segoe UI", 10)).pack(side="left", padx=2)

        # post circle
        post_c = tk.Canvas(focus_frame, width=24, height=24,
                            bg=t.CARD, highlightthickness=0)
        post_c.pack(side="left", padx=(2, 0))
        post_c.create_oval(2, 2, 22, 22, fill=post_col, outline="")
        post_c.create_text(12, 12, text=post, fill="white",
                           font=("Segoe UI", 8, "bold"))

        # row 2: reflection (if any)
        ref = str(r.get("reflection","")).strip()
        if ref and ref.lower() not in ("", "nan"):
            display = ref if len(ref) <= 120 else ref[:117] + "..."
            ref_frame = tk.Frame(card, bg=t.CARD)
            ref_frame.grid(row=2, column=1, sticky="ew",
                           padx=(12,12), pady=(0,12))
            tk.Frame(ref_frame, bg=colour, width=3).pack(
                side="left", fill="y")
            tk.Label(ref_frame, text=f"  {display}",
                     bg=t.CARD, fg=t.MUTED,
                     font=("Segoe UI", 9), anchor="w",
                     justify="left", wraplength=600).pack(
                side="left", fill="x")
        else:
            tk.Frame(card, bg=t.CARD, height=8).grid(row=2, column=1)

    def refresh(self):
        self._load_subjects()
        self._render_sessions()
