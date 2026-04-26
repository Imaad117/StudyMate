from __future__ import annotations
import time
import tkinter as tk
from tkinter import ttk, messagebox
import pandas as pd
from data.data_manager import get_subjects
from data.session_manager import add_session, now_iso
from data.storage import load_sessions_df
from data.history_manager import get_sessions_filtered
from data.goals_manager import get_goals_for_subject, deadline_display
from ui.theme import THEME
from ui.subjects_view import get_subject_colour

BG      = THEME.BG
WHITE   = THEME.CARD
GREEN   = THEME.MAIN
GREEN_D = THEME.DARK
GREEN_L = THEME.LIGHT
BORDER  = THEME.BORDER
MUTED   = THEME.MUTED
MID     = THEME.MID


class SessionView(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=BG)
        self.running        = False
        self.paused         = False
        self.start_epoch: float | None = None
        self.pause_epoch: float | None = None
        self.elapsed_before_pause: int = 0
        self.start_time_iso = ""
        self.end_time_iso   = ""
        self.focus_pre:  int | None = None
        self.focus_post: int | None = None
        self._subject: str  = ""
        self._target_secs: int = 0
        self._beat_target   = False

        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)
        self.rowconfigure(1, weight=1)
        self._build()

    # ── layout ────────────────────────────────────────────────────────────────

    def _build(self):
        t = THEME

        tk.Label(self, text="Study Session",
                 bg=BG, fg=t.MAIN,
                 font=("Segoe UI", 18, "bold")).grid(
            row=0, column=0, columnspan=2, sticky="w", pady=(0, 14))

        # ── LEFT card ────────────────────────────────────────────────────────
        left = tk.Frame(self, bg=t.CARD,
                        highlightthickness=1, highlightbackground=BORDER)
        left.grid(row=1, column=0, sticky="nsew", padx=(0, 8))
        left.columnconfigure(0, weight=1)
        left.rowconfigure(3, weight=1)   # timer row expands

        tk.Label(left, text="CURRENT SESSION",
                 bg=t.CARD, fg=MID,
                 font=("Segoe UI", 9, "bold")).grid(
            row=0, column=0, sticky="w", padx=24, pady=(20, 0))

        # ── Subject picker (always visible) ──────────────────────────────────
        self._subj_picker_frame = tk.Frame(left, bg=t.CARD)
        self._subj_picker_frame.grid(row=1, column=0, sticky="ew",
                                      padx=24, pady=(14, 0))
        self._render_subject_picker()

        # ── Active subject pill (shown when session running) ──────────────────
        self._subj_pill = tk.Label(
            left, text="",
            bg=t.LIGHT, fg=MID,
            font=("Segoe UI", 14, "bold"),
            padx=32, pady=14)
        # hidden by default, shown when session starts

        # ── Big timer ─────────────────────────────────────────────────────────
        self.timer_label = tk.Label(
            left, text="00:00:00",
            bg=t.CARD, fg=t.FG,
            font=("Consolas", 72, "bold"))
        self.timer_label.grid(row=3, column=0, sticky="nsew")

        # ── Target label ──────────────────────────────────────────────────────
        self._target_lbl = tk.Label(left, text="", bg=t.CARD, fg=MUTED,
                                     font=("Segoe UI", 11))
        self._target_lbl.grid(row=4, column=0, pady=(0, 4))

        # ── Progress bar ──────────────────────────────────────────────────────
        prog_outer = tk.Frame(left, bg=t.LIGHT, height=10)
        prog_outer.grid(row=5, column=0, sticky="ew", padx=28, pady=(0, 16))
        self._prog_fill = tk.Frame(prog_outer, bg=t.MAIN, height=10)
        self._prog_fill.place(x=0, y=0, relheight=1, relwidth=0)

        # ── Buttons ───────────────────────────────────────────────────────────
        btn_row = tk.Frame(left, bg=t.CARD)
        btn_row.grid(row=6, column=0, pady=(0, 16))

        self.start_btn = tk.Button(
            btn_row, text="▶  Start session",
            command=self._start_session,
            bg=t.MAIN, fg="white",
            activebackground=GREEN_D, activeforeground="white",
            relief="flat", cursor="hand2",
            font=("Segoe UI", 12, "bold"), padx=28, pady=12)
        self.start_btn.pack(side="left", padx=(0, 8))

        self.pause_btn = tk.Button(
            btn_row, text="⏸  Pause",
            command=self._toggle_pause,
            bg=t.LIGHT, fg=t.DARK,
            activebackground="#f59e0b", activeforeground="white",
            relief="flat", cursor="hand2",
            font=("Segoe UI", 12), padx=20, pady=12,
            state="disabled")
        self.pause_btn.pack(side="left", padx=(0, 8))

        self.end_btn = tk.Button(
            btn_row, text="■  End session",
            command=self._end_session_flow,
            bg=t.LIGHT, fg=t.DARK,
            activebackground=GREEN, activeforeground="white",
            relief="flat", cursor="hand2",
            font=("Segoe UI", 12), padx=28, pady=12,
            state="disabled")
        self.end_btn.pack(side="left")

        # ── Last reflection ───────────────────────────────────────────────────
        tk.Frame(left, bg=BORDER, height=1).grid(
            row=7, column=0, sticky="ew", padx=20)
        self.reflection_label = tk.Label(
            left, text="Last reflection: —",
            bg=t.CARD, fg=MUTED,
            font=("Segoe UI", 9),
            wraplength=360, justify="left", anchor="w")
        self.reflection_label.grid(
            row=8, column=0, sticky="ew", padx=20, pady=(10, 20))

        # ── RIGHT card ───────────────────────────────────────────────────────
        right = tk.Frame(self, bg=t.CARD,
                         highlightthickness=1, highlightbackground=BORDER)
        right.grid(row=1, column=1, sticky="nsew", padx=(8, 0))
        right.columnconfigure(0, weight=1)

        tk.Label(right, text="TODAY'S PROGRESS",
                 bg=t.CARD, fg=MID,
                 font=("Segoe UI", 9, "bold")).pack(
            anchor="w", padx=20, pady=(18, 10))

        self._bar_frame = tk.Frame(right, bg=t.CARD)
        self._bar_frame.pack(fill="x", padx=20)
        self._render_bars()

        tk.Frame(right, bg=BORDER, height=1).pack(fill="x", padx=20, pady=(14, 8))

        stats_row = tk.Frame(right, bg=t.CARD)
        stats_row.pack(fill="x", padx=20, pady=(0, 14))
        for i in range(3):
            stats_row.columnconfigure(i, weight=1)
        self.stat_sessions = self._stat_card(stats_row, "0",  "Sessions today", 0)
        self.stat_focus    = self._stat_card(stats_row, "—",  "Avg focus",      1)
        self.stat_minutes  = self._stat_card(stats_row, "0m", "Total today",    2)
        self._update_stats()

        # Subject detail panel (shown after subject is chosen)
        tk.Frame(right, bg=BORDER, height=1).pack(fill="x", padx=20, pady=(6, 0))
        self._subject_detail = tk.Frame(right, bg=t.CARD)
        self._subject_detail.pack(fill="x", padx=20, pady=(10, 0))
        self._render_subject_detail()

    # ── subject picker ────────────────────────────────────────────────────────

    def _render_subject_picker(self):
        t = THEME
        for w in self._subj_picker_frame.winfo_children():
            w.destroy()

        subjects = get_subjects()
        if not subjects:
            tk.Label(self._subj_picker_frame,
                     text="Add subjects first in the Subjects tab.",
                     bg=t.CARD, fg=t.MUTED,
                     font=("Segoe UI", 9)).pack(anchor="w")
            return

        tk.Label(self._subj_picker_frame, text="What are you studying?",
                 bg=t.CARD, fg=t.MUTED,
                 font=("Segoe UI", 9, "bold")).pack(anchor="w", pady=(0, 8))

        grid = tk.Frame(self._subj_picker_frame, bg=t.CARD)
        grid.pack(fill="x")
        self._subj_btns: dict[str, tk.Button] = {}
        cols = 4
        for i, name in enumerate(subjects):
            colour = get_subject_colour(name)
            is_sel = (name == self._subject)
            btn = tk.Button(grid, text=name,
                            bg=colour if is_sel else t.LIGHT,
                            fg="white" if is_sel else t.DARK,
                            activebackground=colour, activeforeground="white",
                            relief="flat", cursor="hand2",
                            font=("Segoe UI", 10, "bold" if is_sel else "normal"),
                            padx=12, pady=8)
            btn.grid(row=i//cols, column=i%cols, padx=4, pady=4, sticky="ew")
            grid.columnconfigure(i%cols, weight=1)
            btn.configure(command=lambda n=name: self._pick_subject(n))
            self._subj_btns[name] = btn

    def _pick_subject(self, name: str):
        if self.running:
            return   # can't change subject mid-session
        self._subject = name
        self._render_subject_picker()
        self._update_reflection_preview()
        self._render_subject_detail()

    # ── subject detail panel ──────────────────────────────────────────────────

    def _render_subject_detail(self):
        t = THEME
        for w in self._subject_detail.winfo_children():
            w.destroy()

        if not self._subject:
            return

        colour = get_subject_colour(self._subject)

        # Header
        hdr = tk.Frame(self._subject_detail, bg=t.CARD)
        hdr.pack(fill="x", pady=(0, 8))
        tk.Label(hdr, text=self._subject,
                 bg=colour, fg="white",
                 font=("Segoe UI", 10, "bold"),
                 padx=12, pady=4).pack(side="left")
        tk.Label(hdr, text="GOALS & DEADLINES",
                 bg=t.CARD, fg=MID,
                 font=("Segoe UI", 8, "bold")).pack(side="left", padx=(10, 0))

        # Smart insight
        self._render_smart_insight()

        # Goals for this subject
        goals = get_goals_for_subject(self._subject)
        if not goals:
            tk.Label(self._subject_detail,
                     text="No active goals for this subject.",
                     bg=t.CARD, fg=t.MUTED,
                     font=("Segoe UI", 9)).pack(anchor="w", pady=(4, 0))
        else:
            for goal in goals[:4]:   # show max 4
                dl_text, dl_colour = deadline_display(goal["deadline"])
                row = tk.Frame(self._subject_detail, bg=t.CARD, pady=3)
                row.pack(fill="x")
                tk.Label(row, text="•", bg=t.CARD, fg=colour,
                         font=("Segoe UI", 10)).pack(side="left")
                tk.Label(row, text=goal["goal_text"][:60] + ("…" if len(goal["goal_text"])>60 else ""),
                         bg=t.CARD, fg=t.FG,
                         font=("Segoe UI", 9),
                         anchor="w").pack(side="left", padx=(4, 0))
                if dl_text:
                    tk.Label(row, text=f" · {dl_text}",
                             bg=t.CARD, fg=dl_colour,
                             font=("Segoe UI", 9, "bold")).pack(side="left")

        # Recent reflections
        self._render_recent_reflections(colour)

    def _render_recent_reflections(self, colour: str):
        """Show last 3 reflections for this subject with dismiss buttons."""
        t = THEME
        df = load_sessions_df()
        if df is None or df.empty:
            return
        df = df.copy()
        df["subject_name"] = df["subject_name"].astype(str).str.strip()
        df = df[df["subject_name"].str.lower() == self._subject.lower()]
        df["reflection"] = df["reflection"].astype(str).str.strip()
        df = df[~df["reflection"].isin(["", "nan"])]
        if df.empty:
            return
        df["start_dt"] = pd.to_datetime(df["start_time"], errors="coerce")
        df = df.sort_values("start_dt", ascending=False).head(3)

        tk.Frame(self._subject_detail, bg=t.BORDER, height=1).pack(
            fill="x", pady=(12, 8))
        tk.Label(self._subject_detail, text="RECENT REFLECTIONS",
                 bg=t.CARD, fg=MID,
                 font=("Segoe UI", 8, "bold")).pack(anchor="w", pady=(0, 6))

        for _, row in df.iterrows():
            ref = str(row["reflection"]).strip()
            dt  = str(row.get("start_time", ""))[:10]
            card = tk.Frame(self._subject_detail, bg="#0f172a",
                            highlightthickness=1, highlightbackground=t.BORDER)
            card.pack(fill="x", pady=(0, 5))
            inner = tk.Frame(card, bg="#0f172a", padx=10, pady=8)
            inner.pack(fill="x")
            tk.Label(inner, text=dt, bg="#0f172a", fg=t.MUTED,
                     font=("Segoe UI", 8)).pack(anchor="w")
            display = ref if len(ref) <= 90 else ref[:87] + "…"
            tk.Label(inner, text=display,
                     bg="#0f172a", fg="#94a3b8",
                     font=("Segoe UI", 9),
                     wraplength=300, justify="left",
                     anchor="w").pack(anchor="w", pady=(3, 0))

    def _render_smart_insight(self):
        """Deadline-aware study suggestion panel."""
        from datetime import date as _date
        t = THEME
        if not self._subject:
            return

        all_subjects = get_subjects()
        if len(all_subjects) < 2:
            return

        rows = get_sessions_filtered(subject="All", range_days=1)
        studied_today: dict[str, int] = {}
        for r in rows:
            studied_today[r["subject"]] = studied_today.get(r["subject"], 0) + r["duration_seconds"]

        # Build deadline urgency map: subject → days until nearest deadline
        from data.goals_manager import get_goals
        all_goals = get_goals(active_only=True)
        urgency: dict[str, int] = {}   # subject → min days to deadline
        for g in all_goals:
            dl = g.get("deadline", "")
            if dl and dl not in ("", "nan"):
                try:
                    days = (_date.fromisoformat(dl) - _date.today()).days
                    subj = g["subject_name"]
                    urgency[subj] = min(urgency.get(subj, 9999), days)
                except Exception:
                    pass

        current_mins = studied_today.get(self._subject, 0) // 60
        not_studied  = [s for s in all_subjects if s not in studied_today]

        # Priority 1: overdue / urgent deadlines not studied today
        urgent_not_done = sorted(
            [(s, d) for s, d in urgency.items()
             if s not in studied_today and d <= 7],
            key=lambda x: x[1])

        # Priority 2: subjects with close deadlines regardless
        deadline_urgent = sorted(
            [(s, d) for s, d in urgency.items() if d <= 3],
            key=lambda x: x[1])

        if urgent_not_done:
            subj, days = urgent_not_done[0]
            if days < 0:
                msg = f"⚠️  {subj} has an overdue deadline and hasn't been studied today. Consider switching to it."
            elif days == 0:
                msg = f"🔴  {subj} deadline is TODAY and you haven't studied it yet."
            else:
                msg = f"🟡  {subj} has a deadline in {days}d and hasn't been touched today."
        elif deadline_urgent and deadline_urgent[0][0] != self._subject:
            subj, days = deadline_urgent[0]
            msg = (f"📅  {subj} has a deadline in {days}d. "
                   f"You've put in {current_mins}m on {self._subject} today — "
                   f"consider switching focus.")
        elif not_studied:
            suggestion = not_studied[0]
            if current_mins > 0:
                msg = (f"You've put in {current_mins}m on {self._subject} today — "
                       f"great start! {suggestion} hasn't been studied yet.")
            else:
                msg = (f"You haven't studied {self._subject} yet today. "
                       f"Also consider: {', '.join(not_studied[:2])}.")
        else:
            least = min(studied_today, key=studied_today.get)
            least_mins = studied_today[least] // 60
            if least != self._subject:
                msg = f"{least} has only had {least_mins}m today — balancing your time will help."
            else:
                msg = "You've covered all subjects today — great work, keep going!"

        # Focus tip: check last 3 sessions for this subject
        focus_tip = ""
        subj_rows = get_sessions_filtered(subject=self._subject, range_days=7)
        if subj_rows:
            recent_post = []
            for r in subj_rows[:3]:
                try:
                    v = int(r.get("focus_post", 0))
                    if 1 <= v <= 5:
                        recent_post.append(v)
                except Exception:
                    pass
            if len(recent_post) >= 2:
                avg = sum(recent_post) / len(recent_post)
                if avg <= 2.0:
                    focus_tip = f"⚡ Your last {len(recent_post)} {self._subject} sessions averaged {avg:.1f}/5 focus — try a shorter session or a quick break first."
                elif avg >= 4.5:
                    focus_tip = f"🔥 You've been averaging {avg:.1f}/5 focus for {self._subject} — you're in the zone!"

        colour = get_subject_colour(self._subject)
        insight_frame = tk.Frame(self._subject_detail, bg="#0f172a",
                                 highlightthickness=1,
                                 highlightbackground=colour)
        insight_frame.pack(fill="x", pady=(0, 10))
        inner = tk.Frame(insight_frame, bg="#0f172a", padx=12, pady=10)
        inner.pack(fill="x")
        tk.Label(inner, text="💡  Smart Insight",
                 bg="#0f172a", fg=colour,
                 font=("Segoe UI", 8, "bold")).pack(anchor="w")
        tk.Label(inner, text=msg,
                 bg="#0f172a", fg="#94a3b8",
                 font=("Segoe UI", 9),
                 wraplength=320, justify="left").pack(anchor="w", pady=(4, 0))
        if focus_tip:
            tk.Label(inner, text=focus_tip,
                     bg="#0f172a", fg="#60a5fa",
                     font=("Segoe UI", 9),
                     wraplength=320, justify="left").pack(anchor="w", pady=(4, 0))

    # ── session start ─────────────────────────────────────────────────────────

    def _start_session(self):
        if self.running:
            return
        if not self._subject:
            messagebox.showwarning("No subject",
                "Pick a subject above before starting.")
            return
        self._open_duration_popup()

    def _open_duration_popup(self):
        t = THEME
        colour = get_subject_colour(self._subject)
        popup = tk.Toplevel(self)
        popup.title("")
        popup.configure(bg=t.CARD)
        popup.resizable(False, False)
        popup.grab_set()
        popup.transient(self.winfo_toplevel())
        w, h = 560, 290
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        popup.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")

        tk.Frame(popup, bg=colour, height=5).pack(fill="x")
        body = tk.Frame(popup, bg=t.CARD, padx=32, pady=24)
        body.pack(fill="both", expand=True)

        hdr = tk.Frame(body, bg=t.CARD)
        hdr.pack(anchor="w", pady=(0, 8))
        tk.Label(hdr, text=self._subject, bg=colour, fg="white",
                 font=("Segoe UI", 10, "bold"), padx=14, pady=5).pack(side="left")

        tk.Label(body, text="How long are you studying for?",
                 bg=t.CARD, fg=t.FG,
                 font=("Segoe UI", 13, "bold")).pack(anchor="w", pady=(0, 16))

        dur_state = {"secs": 45 * 60}
        dur_btns: list[tk.Button] = []

        _BTN_KW = dict(relief="flat", cursor="hand2",
                       font=("Segoe UI", 10, "bold"), padx=14, pady=10)

        def _select(secs, btn):
            dur_state["secs"] = secs
            for b in dur_btns:
                b.configure(bg=t.LIGHT, fg=t.DARK)
            btn.configure(bg=colour, fg="white")

        def _open_custom_popup():
            for b in dur_btns: b.configure(bg=t.LIGHT, fg=t.DARK)
            popup.grab_release()
            sub = tk.Toplevel(popup)
            sub.title("Custom duration")
            sub.configure(bg=t.CARD)
            sub.resizable(False, False)
            sub.grab_set()
            sub.transient(popup)
            sub.geometry(f"300x190+{(sw-300)//2}+{(sh-190)//2}")
            tk.Frame(sub, bg=colour, height=4).pack(fill="x")
            sb = tk.Frame(sub, bg=t.CARD, padx=28, pady=22)
            sb.pack(fill="both", expand=True)
            tk.Label(sb, text="Enter minutes (1–600):", bg=t.CARD, fg=t.FG,
                     font=("Segoe UI", 11, "bold")).pack(anchor="w", pady=(0, 10))
            cv = tk.StringVar()
            entry = tk.Entry(sb, textvariable=cv, width=8,
                             font=("Segoe UI", 14), bg=t.BG, fg=t.FG,
                             insertbackground=colour, relief="flat",
                             highlightthickness=2,
                             highlightbackground=colour,
                             highlightcolor=colour)
            entry.pack(anchor="w", ipady=6)
            err = tk.Label(sb, text="", bg=t.CARD, fg="#ef4444", font=("Segoe UI", 9))
            err.pack(anchor="w", pady=(4, 0))

            def _confirm():
                try:
                    m = int(cv.get().strip())
                    if not 1 <= m <= 600: raise ValueError
                    dur_state["secs"] = m * 60
                    sub.destroy()
                    popup.grab_set()
                    for b in dur_btns: b.configure(bg=t.LIGHT, fg=t.DARK)
                    dur_btns[-1].configure(bg=colour, fg="white",
                                           text=f"Custom ({m}m)")
                except ValueError:
                    err.configure(text="Enter a whole number: 1–600")

            entry.bind("<Return>", lambda _e: _confirm())
            sub.bind("<Escape>", lambda _e: (sub.destroy(), popup.grab_set()))
            tk.Button(sb, text="Confirm", command=_confirm,
                      bg=colour, fg="white", relief="flat", cursor="hand2",
                      font=("Segoe UI", 10, "bold"),
                      padx=14, pady=7,
                      activebackground=t.DARK).pack(anchor="w", pady=(10, 0))
            entry.focus_set()

        btn_row = tk.Frame(body, bg=t.CARD)
        btn_row.pack(fill="x", pady=(0, 16))

        for label, secs in [("25m", 25*60), ("45m", 45*60), ("60m", 60*60), ("90m", 90*60)]:
            is_default = (secs == 45*60)
            btn = tk.Button(btn_row, text=label,
                            bg=colour if is_default else t.LIGHT,
                            fg="white" if is_default else t.DARK,
                            activebackground=colour, activeforeground="white",
                            **_BTN_KW)
            btn.pack(side="left", padx=(0, 6))
            btn.configure(command=lambda s=secs, b=btn: _select(s, b))
            dur_btns.append(btn)

        indef_btn = tk.Button(btn_row, text="∞  No limit",
                              bg=t.LIGHT, fg=t.DARK,
                              activebackground=colour, activeforeground="white",
                              **_BTN_KW)
        indef_btn.pack(side="left", padx=(0, 6))
        indef_btn.configure(command=lambda b=indef_btn: _select(0, b))
        dur_btns.append(indef_btn)

        custom_btn = tk.Button(btn_row, text="Custom",
                               bg=t.LIGHT, fg=t.DARK,
                               activebackground=colour, activeforeground="white",
                               **_BTN_KW)
        custom_btn.pack(side="left")
        custom_btn.configure(command=_open_custom_popup)
        dur_btns.append(custom_btn)

        def _go():
            target_secs = dur_state["secs"]
            popup.grab_release(); popup.destroy()
            focus = self._ask_focus_rating("Focus — before",
                                           "How focused are you feeling right now?")
            if focus is None: return
            self.focus_pre      = focus
            self._target_secs   = target_secs
            self._beat_target   = False
            self.running        = True
            self.paused         = False
            self.elapsed_before_pause = 0
            self.start_epoch    = time.time()
            self.start_time_iso = now_iso()
            self._subj_picker_frame.grid_remove()
            c = get_subject_colour(self._subject)
            self._subj_pill.configure(text=self._subject, bg=c, fg="white")
            self._subj_pill.grid(row=1, column=0, sticky="ew", padx=24, pady=(14, 0))
            if target_secs > 0:
                self._target_lbl.configure(text=f"Goal: {target_secs // 60} mins")
            else:
                self._target_lbl.configure(text="Free session — no time limit")
            self._prog_fill.configure(bg=t.MAIN)
            self.start_btn.configure(state="disabled", bg=GREEN_L, fg=MUTED)
            self.pause_btn.configure(state="normal")
            self.end_btn.configure(state="normal", bg=t.MAIN, fg="white")
            self._update_reflection_preview()
            self._render_subject_detail()
            self._tick()

        tk.Button(body, text="Let's go  →",
                  command=_go,
                  bg=colour, fg="white",
                  activebackground=GREEN_D, activeforeground="white",
                  relief="flat", cursor="hand2",
                  font=("Segoe UI", 12, "bold"),
                  pady=12).pack(fill="x")

        popup.bind("<Escape>", lambda _e: popup.destroy())

    # ── pause / resume ────────────────────────────────────────────────────────

    def _toggle_pause(self):
        if not self.running:
            return
        t = THEME
        if not self.paused:
            # pausing — store how much time has elapsed so far
            self.paused = True
            self.pause_epoch = time.time()
            self.elapsed_before_pause += int(time.time() - (self.start_epoch or time.time()))
            self.start_epoch = None
            # turn the button amber and make the timer numbers amber so it's obvious we're paused
            self.pause_btn.configure(text="▶  Resume", bg="#f59e0b", fg="white")
            self.timer_label.configure(fg="#f59e0b")
        else:
            # resuming — reset the epoch so the timer picks up from where we left off
            self.paused = False
            self.start_epoch = time.time()
            self.pause_epoch = None
            self.pause_btn.configure(text="⏸  Pause", bg=t.LIGHT, fg=t.DARK)
            self.timer_label.configure(fg=t.FG)
            self._tick()

    # ── timer tick ────────────────────────────────────────────────────────────

    def _tick(self):
        # stops the tick if the window has been closed mid-session
        try:
            if not self.winfo_exists():
                return
        except Exception:
            return
        if not self.running or self.paused or self.start_epoch is None:
            return

        # total time = anything before a pause + time since we (re)started
        elapsed = self.elapsed_before_pause + int(time.time() - self.start_epoch)
        h = elapsed // 3600
        m = (elapsed % 3600) // 60
        s = elapsed % 60
        self.timer_label.configure(text=f"{h:02d}:{m:02d}:{s:02d}")

        # fill the progress bar toward the target time
        if self._target_secs > 0:
            pct = min(1.0, elapsed / self._target_secs)
            self._prog_fill.place(x=0, y=0, relheight=1, relwidth=pct)
            if pct >= 1.0 and not self._beat_target:
                # first time hitting the target — celebrate a little
                self._beat_target = True
                self._prog_fill.configure(bg="#22c55e")
                self._target_lbl.configure(
                    text="✓ Target reached! Keep going or end.",
                    fg="#16a34a")

        # call this again in 1 second to keep the timer ticking
        self.after(1000, self._tick)

    # ── end session ───────────────────────────────────────────────────────────

    def _end_session_flow(self):
        if not self.running or (self.start_epoch is None and not self.paused):
            return
        self.running = False
        self.end_time_iso = now_iso()

        # Calculate total elapsed including any pre-pause time
        if self.paused:
            duration = self.elapsed_before_pause
        else:
            duration = self.elapsed_before_pause + int(time.time() - (self.start_epoch or time.time()))

        subject = self._subject

        focus_after = self._ask_focus_rating("Focus — after",
                                              "How focused were you during the session?")
        if focus_after is None:
            self.running = True
            if not self.paused: self._tick()
            return
        self.focus_post = focus_after

        reflection = self._ask_reflection(subject=subject)
        if reflection is None:
            self.running = True
            if not self.paused: self._tick()
            return

        ok, msg = add_session(
            subject_name=subject,
            start_time=self.start_time_iso,
            end_time=self.end_time_iso,
            duration_seconds=duration,
            focus_pre=int(self.focus_pre or 1),
            focus_post=int(self.focus_post or 1),
            reflection=reflection)

        if not ok:
            messagebox.showerror("Save session", msg)
            self.running = True
            if not self.paused: self._tick()
            return

        messagebox.showinfo("Session saved",
            f"Great work! {duration//60}m {duration%60}s logged.")

        # reset
        t = THEME
        self.start_epoch    = None
        self.pause_epoch    = None
        self.elapsed_before_pause = 0
        self.paused         = False
        self.start_time_iso = ""
        self.end_time_iso   = ""
        self.focus_pre      = None
        self.focus_post     = None
        self._target_secs   = 0
        self._beat_target   = False

        self.timer_label.configure(text="00:00:00", fg=t.FG)
        self._subj_pill.grid_remove()
        self._subj_picker_frame.grid()
        self._render_subject_picker()
        self._target_lbl.configure(text="", fg=MUTED)
        self._prog_fill.place(relwidth=0)
        self._prog_fill.configure(bg=t.MAIN)
        self.start_btn.configure(state="normal", bg=t.MAIN, fg="white")
        self.pause_btn.configure(state="disabled", text="⏸  Pause",
                                  bg=t.LIGHT, fg=t.DARK)
        self.end_btn.configure(state="disabled", bg=t.LIGHT, fg=t.DARK)
        self._update_reflection_preview()
        self._render_bars()
        self._update_stats()
        self._render_subject_detail()

    # ── focus rating popup ────────────────────────────────────────────────────

    def _ask_focus_rating(self, title: str, subtitle: str) -> int | None:
        result: dict = {"val": None}
        t = THEME
        win = tk.Toplevel(self)
        win.title(title)
        win.transient(self.winfo_toplevel())
        win.grab_set()
        win.resizable(False, False)
        win.configure(bg=t.CARD)

        tk.Frame(win, bg=t.MAIN, height=5).pack(fill="x")
        body = tk.Frame(win, bg=t.CARD, padx=28, pady=24)
        body.pack(fill="both", expand=True)

        tk.Label(body, text=subtitle, bg=t.CARD, fg=t.FG,
                 font=("Segoe UI", 13, "bold")).pack(anchor="w")
        tk.Label(body, text="1 = struggling to focus  ·  5 = fully locked in",
                 bg=t.CARD, fg=MUTED, font=("Segoe UI", 9)).pack(anchor="w", pady=(4, 18))

        btn_row = tk.Frame(body, bg=t.CARD)
        btn_row.pack(anchor="w", pady=(0, 16))

        COLOURS = ["#fee2e2","#fef3c7","#fefce8","#dcfce7","#d1fae5"]
        TEXT_C  = ["#991b1b","#92400e","#713f12","#166534","#064e3b"]
        LABELS  = ["1\nLow","2","3\nOK","4","5\nHigh"]

        def choose(n):
            result["val"] = n; win.destroy()

        for i in range(5):
            tk.Button(btn_row, text=LABELS[i], width=6, height=2,
                      font=("Segoe UI", 10, "bold"),
                      bg=COLOURS[i], fg=TEXT_C[i],
                      activebackground=GREEN, activeforeground="white",
                      relief="flat", cursor="hand2",
                      command=lambda n=i+1: choose(n)).pack(side="left", padx=5)

        def cancel():
            result["val"] = None; win.destroy()

        tk.Button(body, text="Cancel", command=cancel,
                  bg=t.LIGHT, fg=t.DARK, relief="flat",
                  padx=12, pady=5, cursor="hand2").pack(anchor="e")
        win.protocol("WM_DELETE_WINDOW", cancel)
        win.bind("<Escape>", lambda _e: cancel())
        win.update_idletasks()
        p = self.winfo_toplevel()
        nx = p.winfo_rootx() + (p.winfo_width()  - 460) // 2
        ny = p.winfo_rooty() + (p.winfo_height() - 260) // 2
        win.geometry(f"460x260+{nx}+{ny}")
        win.wait_window()
        return result["val"]

    # ── reflection popup ──────────────────────────────────────────────────────

    def _ask_reflection(self, subject: str, max_chars: int = 300) -> str | None:
        result: dict = {"val": None}
        t = THEME
        win = tk.Toplevel(self)
        win.title("Quick reflection")
        win.transient(self.winfo_toplevel())
        win.grab_set()
        win.resizable(False, False)
        win.configure(bg=t.CARD)

        tk.Frame(win, bg=t.MAIN, height=5).pack(fill="x")
        body = tk.Frame(win, bg=t.CARD, padx=28, pady=24)
        body.pack(fill="both", expand=True)

        colour = get_subject_colour(subject) if subject else t.MAIN
        tk.Label(body, text=f"Reflection — {subject}",
                 bg=t.CARD, fg=colour,
                 font=("Segoe UI", 13, "bold")).pack(anchor="w")
        tk.Label(body, text="What did you cover? What was tricky? What's next?",
                 bg=t.CARD, fg=MUTED, font=("Segoe UI", 9)).pack(anchor="w", pady=(4, 12))

        txt = tk.Text(body, width=52, height=6, wrap="word",
                      font=("Segoe UI", 10),
                      bg=t.CARD, fg=t.FG,
                      relief="solid", bd=1,
                      highlightthickness=1,
                      highlightbackground=BORDER,
                      highlightcolor=GREEN,
                      insertbackground=GREEN)
        txt.pack(fill="x")

        counter = tk.Label(body, text=f"0/{max_chars}",
                           bg=t.CARD, fg=MUTED, font=("Segoe UI", 9))
        counter.pack(anchor="e", pady=(4, 0))

        def on_key(_e=None):
            cur = txt.get("1.0", "end-1c")
            if len(cur) > max_chars:
                txt.delete("1.0", "end"); txt.insert("1.0", cur[:max_chars])
                cur = cur[:max_chars]
            counter.configure(text=f"{len(cur)}/{max_chars}")
        txt.bind("<KeyRelease>", on_key)

        acts = tk.Frame(body, bg=t.CARD)
        acts.pack(fill="x", pady=(12, 0))

        def cancel():
            result["val"] = None; win.destroy()
        def ok():
            result["val"] = txt.get("1.0", "end-1c").strip(); win.destroy()

        tk.Button(acts, text="Skip",
                  command=lambda: (result.update({"val": ""}), win.destroy()),
                  bg=t.LIGHT, fg=MUTED, relief="flat",
                  padx=12, pady=6, cursor="hand2").pack(side="left")
        tk.Button(acts, text="Cancel", command=cancel,
                  bg=t.LIGHT, fg=t.DARK, relief="flat",
                  padx=12, pady=6, cursor="hand2").pack(side="right")
        tk.Button(acts, text="Save reflection", command=ok,
                  bg=t.MAIN, fg="white", relief="flat",
                  font=("Segoe UI", 10, "bold"),
                  padx=14, pady=6, cursor="hand2",
                  activebackground=GREEN_D).pack(side="right", padx=(0, 8))

        win.protocol("WM_DELETE_WINDOW", cancel)
        win.bind("<Escape>", lambda _e: cancel())
        win.update_idletasks()
        p = self.winfo_toplevel()
        nx = p.winfo_rootx() + (p.winfo_width()  - 540) // 2
        ny = p.winfo_rooty() + (p.winfo_height() - 320) // 2
        win.geometry(f"540x320+{nx}+{ny}")
        txt.focus_set()
        win.wait_window()
        return result["val"]

    # ── right card helpers ────────────────────────────────────────────────────

    def _stat_card(self, parent, val, lbl, col):
        t = THEME
        f = tk.Frame(parent, bg=t.LIGHT)
        f.grid(row=0, column=col, sticky="ew", padx=3)
        v = tk.Label(f, text=val, bg=t.LIGHT, fg=t.DARK,
                     font=("Segoe UI", 20, "bold"))
        v.pack(pady=(10, 0))
        tk.Label(f, text=lbl, bg=t.LIGHT, fg=MID,
                 font=("Segoe UI", 9)).pack(pady=(0, 10))
        return v

    def _render_bars(self):
        t = THEME
        for w in self._bar_frame.winfo_children():
            w.destroy()
        rows = get_sessions_filtered(subject="All", range_days=1)
        if not rows:
            tk.Label(self._bar_frame, text="No sessions today yet.",
                     bg=t.CARD, fg=MUTED,
                     font=("Segoe UI", 9)).pack(anchor="w", pady=4)
            return
        totals: dict[str, int] = {}
        for r in rows:
            totals[r["subject"]] = totals.get(r["subject"], 0) + r["duration_seconds"]
        max_secs = max(totals.values()) if totals else 1
        for subj, secs in sorted(totals.items(), key=lambda x: -x[1]):
            mins   = round(secs / 60, 1)
            colour = get_subject_colour(subj)
            row = tk.Frame(self._bar_frame, bg=t.CARD)
            row.pack(fill="x", pady=3)
            tk.Label(row, text=subj, bg=t.CARD, fg=t.FG,
                     font=("Segoe UI", 9), width=14, anchor="w").pack(side="left")
            bar_bg = tk.Frame(row, bg=t.LIGHT, height=12)
            bar_bg.pack(side="left", fill="x", expand=True, padx=(4, 8))
            bar_bg.update_idletasks()
            tk.Frame(bar_bg, bg=colour, height=12).place(
                x=0, y=0, relwidth=secs/max_secs, relheight=1)
            tk.Label(row, text=f"{mins}m", bg=t.CARD, fg=MUTED,
                     font=("Segoe UI", 9), width=5).pack(side="left")

    def _update_stats(self):
        rows = get_sessions_filtered(subject="All", range_days=1)
        total_secs = sum(r["duration_seconds"] for r in rows)
        focus_vals = [float(r["focus_pre"]) for r in rows
                      if str(r.get("focus_pre", "")).replace(".", "").isdigit()]
        avg_f = f"{sum(focus_vals)/len(focus_vals):.1f}" if focus_vals else "—"
        self.stat_sessions.configure(text=str(len(rows)))
        self.stat_focus.configure(text=avg_f)
        self.stat_minutes.configure(text=f"{total_secs//60}m")

    def _update_reflection_preview(self):
        subject = self._subject
        if not subject:
            self.reflection_label.configure(text="Last reflection: —")
            return
        df = load_sessions_df()
        if df is None or df.empty:
            self.reflection_label.configure(text="Last reflection: —")
            return
        df = df.copy()
        df["subject_name"] = df["subject_name"].astype(str).str.strip()
        df = df[df["subject_name"].str.lower() == subject.lower()]
        if df.empty:
            self.reflection_label.configure(text="Last reflection: —")
            return
        df["start_dt"] = pd.to_datetime(df["start_time"], errors="coerce")
        df = df.sort_values("start_dt", ascending=False)
        for _, row in df.iterrows():
            ref = str(row.get("reflection", "")).strip()
            if ref and ref.lower() not in ("nan", ""):
                display = ref if len(ref) <= 100 else ref[:97] + "..."
                self.reflection_label.configure(
                    text=f"Last reflection: {display}")
                return
        self.reflection_label.configure(text="Last reflection: —")

    def refresh(self):
        if not self.running:
            self._render_subject_picker()
        self._render_bars()
        self._update_stats()
        self._render_subject_detail()
