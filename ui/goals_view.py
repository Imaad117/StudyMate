from __future__ import annotations
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date, timedelta
from data.data_manager import get_subjects
from data.goals_manager import (get_goals, add_goal, update_goal, delete_goal,
                                 complete_goal, uncomplete_goal, deadline_display)
from ui.theme import THEME
from ui.subjects_view import get_subject_colour
from ui.scroll_helper import bind_mousewheel


class GoalsView(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=THEME.BG)
        self._tab = "active"
        self._filter_subject = "All"
        self._build()

    def _build(self):
        t = THEME
        top = tk.Frame(self, bg=t.CARD)
        top.pack(fill="x")
        tk.Frame(self, bg=t.MAIN, height=3).pack(fill="x")
        inner = tk.Frame(top, bg=t.CARD, padx=20, pady=12)
        inner.pack(fill="x")
        tk.Label(inner, text="Goals", bg=t.CARD, fg=t.MAIN,
                 font=("Segoe UI", 18, "bold")).pack(side="left")
        tk.Button(inner, text="＋  Add goal",
                  command=self._open_add_popup,
                  bg=t.MAIN, fg="white",
                  activebackground=t.DARK, activeforeground="white",
                  relief="flat", cursor="hand2",
                  font=("Segoe UI", 10, "bold"),
                  padx=18, pady=7).pack(side="right")

        tab_bar = tk.Frame(self, bg=t.CARD, padx=20)
        tab_bar.pack(fill="x")
        self._tab_btns: dict[str, tk.Button] = {}
        for key, label in [("active", "Active"), ("completed", "Completed")]:
            btn = tk.Button(tab_bar, text=label,
                            command=lambda k=key: self._switch_tab(k),
                            bg=t.MAIN if key=="active" else t.CARD,
                            fg="white" if key=="active" else t.MUTED,
                            relief="flat", cursor="hand2",
                            font=("Segoe UI", 10, "bold" if key=="active" else "normal"),
                            padx=18, pady=8)
            btn.pack(side="left", padx=(0, 4))
            self._tab_btns[key] = btn
        self._count_lbl = tk.Label(tab_bar, text="",
                                    bg=t.CARD, fg=t.MUTED, font=("Segoe UI", 9))
        self._count_lbl.pack(side="left", padx=(8, 0))

        # Subject filter pills
        self._subj_filter_frame = tk.Frame(self, bg=t.BG, padx=20, pady=8)
        self._subj_filter_frame.pack(fill="x")
        self._subj_filter_btns: dict[str, tk.Button] = {}

        tk.Frame(self, bg=t.BORDER, height=1).pack(fill="x")

        outer = tk.Frame(self, bg=t.BG)
        outer.pack(fill="both", expand=True)
        canvas = tk.Canvas(outer, bg=t.BG, highlightthickness=0)
        sb = ttk.Scrollbar(outer, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)
        bind_mousewheel(canvas)

        self._inner = tk.Frame(canvas, bg=t.BG)
        win = canvas.create_window((0, 0), window=self._inner, anchor="nw")
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(win, width=e.width))
        self._inner.bind("<Configure>",
                         lambda _e: canvas.configure(scrollregion=canvas.bbox("all")))
        self._render_subject_filter()
        self._render_list()

    def _render_subject_filter(self):
        t = THEME
        for w in self._subj_filter_frame.winfo_children():
            w.destroy()
        self._subj_filter_btns.clear()
        for name in ["All"] + get_subjects():
            is_sel = (name == self._filter_subject)
            colour = t.MAIN if name == "All" else get_subject_colour(name)
            btn = tk.Button(
                self._subj_filter_frame, text=name,
                command=lambda n=name: self._set_subject_filter(n),
                bg=colour if is_sel else t.CARD,
                fg="white" if is_sel else t.MUTED,
                activebackground=colour, activeforeground="white",
                relief="flat", cursor="hand2",
                font=("Segoe UI", 9, "bold" if is_sel else "normal"),
                padx=12, pady=5)
            btn.pack(side="left", padx=(0, 5))
            self._subj_filter_btns[name] = btn

    def _set_subject_filter(self, name: str):
        self._filter_subject = name
        self._render_subject_filter()
        self._render_list()

    def _switch_tab(self, key: str):
        t = THEME
        self._tab = key
        for k, btn in self._tab_btns.items():
            active = (k == key)
            btn.configure(bg=t.MAIN if active else t.CARD,
                          fg="white" if active else t.MUTED,
                          font=("Segoe UI", 10, "bold" if active else "normal"))
        self._render_list()

    def _render_list(self):
        from datetime import date as _date
        t = THEME
        for w in self._inner.winfo_children():
            w.destroy()
        active = (self._tab == "active")
        goals  = get_goals(active_only=active)

        # Subject filter
        if hasattr(self, "_filter_subject") and self._filter_subject != "All":
            goals = [g for g in goals if g["subject_name"] == self._filter_subject]

        # Sort active goals by deadline urgency
        if active:
            def _sort_key(g):
                dl = g.get("deadline", "")
                if not dl or str(dl) in ("", "nan"):
                    return (2, 0)
                try:
                    days = (_date.fromisoformat(str(dl)) - _date.today()).days
                    return (0 if days <= 0 else 1, days)
                except Exception:
                    return (2, 0)
            goals = sorted(goals, key=_sort_key)

        self._count_lbl.configure(
            text=f"{len(goals)} {'active' if active else 'completed'} "
                 f"goal{'s' if len(goals)!=1 else ''}")
        if not goals:
            msg = ("No active goals yet. Click '＋ Add goal' to get started."
                   if active else "No completed goals yet.")
            tk.Label(self._inner, text=msg, bg=t.BG, fg=t.MUTED,
                     font=("Segoe UI", 11)).pack(pady=40)
            return
        for goal in goals:
            self._goal_card(goal, active)

    def _goal_card(self, goal: dict, active: bool):
        t = THEME
        colour   = get_subject_colour(goal["subject_name"])
        dl_text, dl_colour = deadline_display(goal["deadline"])

        card = tk.Frame(self._inner, bg=t.CARD,
                        highlightthickness=1, highlightbackground=t.BORDER)
        card.pack(fill="x", padx=16, pady=6)
        tk.Frame(card, bg=colour, width=5).pack(side="left", fill="y")

        body = tk.Frame(card, bg=t.CARD, padx=16, pady=14)
        body.pack(side="left", fill="both", expand=True)

        top_row = tk.Frame(body, bg=t.CARD)
        top_row.pack(fill="x", anchor="w")
        tk.Label(top_row, text=goal["subject_name"],
                 bg=colour, fg="white",
                 font=("Segoe UI", 9, "bold"), padx=10, pady=4).pack(side="left")
        # Only show deadline badge on active goals
        if dl_text and active:
            tk.Label(top_row, text=f"⏱  {dl_text}",
                     bg=t.CARD, fg=dl_colour,
                     font=("Segoe UI", 10, "bold")).pack(side="left", padx=(12, 0))

        tk.Label(body, text=goal["goal_text"],
                 bg=t.CARD, fg=t.FG,
                 font=("Segoe UI", 11),
                 anchor="w", justify="left",
                 wraplength=800).pack(anchor="w", pady=(8, 0))

        # right side buttons
        btns = tk.Frame(card, bg=t.CARD, padx=14, pady=10)
        btns.pack(side="right", fill="y")

        if active:
            tk.Button(btns, text="✓  Mark complete",
                      command=lambda gid=goal["goal_id"]: self._complete(gid),
                      bg=t.MAIN, fg="white",
                      activebackground=t.DARK, activeforeground="white",
                      relief="flat", cursor="hand2",
                      font=("Segoe UI", 9, "bold"),
                      padx=14, pady=7).pack(pady=(0, 8))
        else:
            tk.Button(btns, text="↩  Reactivate",
                      command=lambda gid=goal["goal_id"]: self._uncomplete(gid),
                      bg=t.LIGHT, fg=t.DARK,
                      activebackground=t.MAIN, activeforeground="white",
                      relief="flat", cursor="hand2",
                      font=("Segoe UI", 9),
                      padx=14, pady=7).pack(pady=(0, 8))

        icon_row = tk.Frame(btns, bg=t.CARD)
        icon_row.pack()

        _ICON_KW = dict(relief="flat", cursor="hand2",
                        font=("Segoe UI", 9, "bold"),
                        padx=10, pady=6)

        tk.Button(icon_row, text="Edit",
                  command=lambda g=goal: self._open_edit_popup(g),
                  bg=t.LIGHT, fg=t.DARK,
                  activebackground=t.MAIN, activeforeground="white",
                  **_ICON_KW).pack(side="left", padx=(0, 4))

        def _show_info(g=goal):
            created   = g["created_at"][:16].replace("T", " at ")
            completed = g.get("completed_at", "")
            msg = f"Created: {created}"
            if completed and completed not in ("", "nan"):
                msg += f"\nCompleted: {completed[:16].replace('T', ' at ')}"
            if g.get("deadline") and g["deadline"] not in ("", "nan"):
                msg += f"\nDeadline: {g['deadline']}"
            messagebox.showinfo("Goal info", msg)

        tk.Button(icon_row, text="Info",
                  command=_show_info,
                  bg=t.LIGHT, fg=t.MUTED,
                  activebackground=t.LIGHT, activeforeground=t.DARK,
                  **_ICON_KW).pack(side="left", padx=(0, 4))

        tk.Button(icon_row, text="Delete",
                  command=lambda gid=goal["goal_id"]: self._delete(gid),
                  bg=t.LIGHT, fg="#ef4444",
                  activebackground="#fee2e2", activeforeground="#dc2626",
                  **_ICON_KW).pack(side="left")

    def _complete(self, gid):   complete_goal(gid);   self._render_list()
    def _uncomplete(self, gid): uncomplete_goal(gid); self._render_list()
    def _delete(self, gid):
        if messagebox.askyesno("Delete goal", "Delete this goal permanently?"):
            delete_goal(gid); self._render_list()

    # ── date picker mini-popup ────────────────────────────────────────────────

    def _pick_date_popup(self, initial: str, on_pick):
        """Calendar date picker popup — buttons pinned at bottom, calendar scrolls."""
        import calendar as _cal_mod
        t = THEME
        win = tk.Toplevel(self)
        win.title("Pick a date")
        win.configure(bg=t.CARD)
        win.resizable(False, False)
        win.grab_set()
        win.transient(self.winfo_toplevel())
        w, h = 400, 580          # tall enough for any 6-row month + buttons
        sw, sh = win.winfo_screenwidth(), win.winfo_screenheight()
        win.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")

        tk.Frame(win, bg=t.MAIN, height=5).pack(fill="x")

        # ── bottom button bar (packed first so it's always visible) ───────────
        btn_bar = tk.Frame(win, bg=t.CARD, padx=24, pady=16)
        btn_bar.pack(side="bottom", fill="x")
        tk.Frame(win, bg=t.BORDER, height=1).pack(side="bottom", fill="x")

        def _confirm():
            win.destroy()
            on_pick(selected["value"])

        tk.Button(btn_bar, text="Confirm date",
                  command=_confirm,
                  bg=t.MAIN, fg="white",
                  activebackground=t.DARK, activeforeground="white",
                  relief="flat", cursor="hand2",
                  font=("Segoe UI", 11, "bold"),
                  pady=10).pack(fill="x", pady=(0, 8))
        tk.Button(btn_bar, text="Cancel",
                  command=win.destroy,
                  bg=t.LIGHT, fg=t.DARK,
                  relief="flat", cursor="hand2",
                  font=("Segoe UI", 10),
                  pady=7).pack(fill="x")

        # ── scrollable body ───────────────────────────────────────────────────
        body = tk.Frame(win, bg=t.CARD, padx=24, pady=20)
        body.pack(fill="both", expand=True)

        tk.Label(body, text="Pick a date", bg=t.CARD, fg=t.MAIN,
                 font=("Segoe UI", 14, "bold")).pack(anchor="w", pady=(0, 12))

        try:
            init_date = date.fromisoformat(initial) if initial else date.today()
        except Exception:
            init_date = date.today()

        selected = {"value": str(init_date)}

        display_lbl = tk.Label(body,
                               text=f"Selected:  {selected['value']}",
                               bg=t.LIGHT, fg=t.MAIN,
                               font=("Segoe UI", 11, "bold"), pady=8)
        display_lbl.pack(fill="x", pady=(0, 14))

        cal_frame = tk.Frame(body, bg=t.CARD)
        cal_frame.pack(fill="x")

        today   = date.today()
        year_v  = tk.IntVar(value=init_date.year)
        month_v = tk.IntVar(value=init_date.month)

        def _render_cal():
            for w in cal_frame.winfo_children():
                w.destroy()

            # nav
            nav = tk.Frame(cal_frame, bg=t.CARD)
            nav.pack(fill="x", pady=(0, 8))
            tk.Button(nav, text="◀", command=_prev,
                      bg=t.CARD, fg=t.MUTED, relief="flat", cursor="hand2",
                      font=("Segoe UI", 12, "bold"), padx=10).pack(side="left")
            tk.Label(nav,
                     text=f"{_cal_mod.month_name[month_v.get()]} {year_v.get()}",
                     bg=t.CARD, fg=t.FG,
                     font=("Segoe UI", 12, "bold")).pack(side="left", expand=True)
            tk.Button(nav, text="▶", command=_next,
                      bg=t.CARD, fg=t.MUTED, relief="flat", cursor="hand2",
                      font=("Segoe UI", 12, "bold"), padx=10).pack(side="right")

            # weekday headers
            hdr = tk.Frame(cal_frame, bg=t.CARD)
            hdr.pack(fill="x")
            for i, d in enumerate(["Mo","Tu","We","Th","Fr","Sa","Su"]):
                tk.Label(hdr, text=d, bg=t.CARD, fg=t.MUTED,
                         font=("Segoe UI", 9, "bold"),
                         width=4, anchor="center").grid(row=0, column=i, padx=2)

            # days
            grid = tk.Frame(cal_frame, bg=t.CARD)
            grid.pack(fill="x", pady=(6, 0))
            weeks   = _cal_mod.monthcalendar(year_v.get(), month_v.get())
            sel_str = selected["value"]

            for r, week in enumerate(weeks):
                for c, day in enumerate(week):
                    if day == 0:
                        tk.Label(grid, text="", bg=t.CARD, width=4).grid(
                            row=r, column=c, padx=2, pady=3)
                        continue
                    d = date(year_v.get(), month_v.get(), day)
                    is_sel   = (str(d) == sel_str)
                    is_today = (d == today)
                    is_past  = (d < today)

                    if is_sel:   bg, fg = t.MAIN, "white"
                    elif is_today: bg, fg = t.LIGHT, t.DARK
                    elif is_past:  bg, fg = t.CARD, t.MUTED
                    else:          bg, fg = t.CARD, t.FG

                    btn = tk.Button(grid, text=str(day),
                                    bg=bg, fg=fg,
                                    activebackground=t.MAIN, activeforeground="white",
                                    relief="flat",
                                    cursor="hand2" if not is_past else "arrow",
                                    font=("Segoe UI", 10,
                                          "bold" if is_sel or is_today else "normal"),
                                    width=4, pady=5,
                                    state="normal" if not is_past else "disabled")
                    btn.grid(row=r, column=c, padx=2, pady=3)
                    btn.configure(command=lambda d=d: _pick_day(d))

        def _pick_day(d: date):
            selected["value"] = str(d)
            display_lbl.configure(text=f"Selected:  {d}")
            _render_cal()

        def _prev():
            m, y = month_v.get(), year_v.get()
            if m == 1: month_v.set(12); year_v.set(y-1)
            else: month_v.set(m-1)
            _render_cal()

        def _next():
            m, y = month_v.get(), year_v.get()
            if m == 12: month_v.set(1); year_v.set(y+1)
            else: month_v.set(m+1)
            _render_cal()

        _render_cal()
        win.bind("<Escape>", lambda _e: win.destroy())

    # ── shared popup ──────────────────────────────────────────────────────────

    def _goal_popup(self, title: str, prefill_text: str = "",
                    prefill_subject: str = "", prefill_deadline: str = "",
                    show_subject: bool = True,
                    on_save=None):
        t = THEME
        popup = tk.Toplevel(self)
        popup.title(title)
        popup.configure(bg=t.CARD)
        popup.resizable(False, False)
        popup.grab_set()
        popup.transient(self.winfo_toplevel())
        w, h = 540, 480 if not show_subject else 540
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        popup.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")

        tk.Frame(popup, bg=t.MAIN, height=5).pack(fill="x")
        body = tk.Frame(popup, bg=t.CARD, padx=32, pady=24)
        body.pack(fill="both", expand=True)

        tk.Label(body, text=title, bg=t.CARD, fg=t.MAIN,
                 font=("Segoe UI", 14, "bold")).pack(anchor="w", pady=(0, 16))

        # ── Subject (only shown when adding) ─────────────────────────────────
        subj_var = tk.StringVar(value=prefill_subject)
        if show_subject:
            tk.Label(body, text="Subject", bg=t.CARD, fg=t.MUTED,
                     font=("Segoe UI", 9, "bold")).pack(anchor="w", pady=(0, 6))
            subjects  = get_subjects()
            subj_frame = tk.Frame(body, bg=t.CARD)
            subj_frame.pack(fill="x", pady=(0, 16))
            subj_btns: list[tk.Button] = []

            def _pick_subj(name, btn):
                subj_var.set(name)
                c = get_subject_colour(name)
                for b in subj_btns: b.configure(bg=t.LIGHT, fg=t.DARK, font=("Segoe UI", 10))
                btn.configure(bg=c, fg="white", font=("Segoe UI", 10, "bold"))

            cols = 3
            for i, name in enumerate(subjects):
                c      = get_subject_colour(name)
                is_sel = (name == prefill_subject) or (not prefill_subject and i == 0)
                btn = tk.Button(subj_frame, text=name,
                                bg=c if is_sel else t.LIGHT,
                                fg="white" if is_sel else t.DARK,
                                activebackground=c, activeforeground="white",
                                relief="flat", cursor="hand2",
                                font=("Segoe UI", 10, "bold" if is_sel else "normal"),
                                padx=12, pady=9)
                btn.grid(row=i//cols, column=i%cols, padx=4, pady=4, sticky="ew")
                subj_frame.columnconfigure(i%cols, weight=1)
                btn.configure(command=lambda n=name, b=btn: _pick_subj(n, b))
                subj_btns.append(btn)
                if is_sel and not subj_var.get():
                    subj_var.set(name)
        else:
            # Edit mode — show subject as read-only badge, not editable
            colour = get_subject_colour(prefill_subject) if prefill_subject else t.MAIN
            badge_row = tk.Frame(body, bg=t.CARD)
            badge_row.pack(anchor="w", pady=(0, 16))
            tk.Label(badge_row, text="Subject:", bg=t.CARD, fg=t.MUTED,
                     font=("Segoe UI", 9)).pack(side="left")
            tk.Label(badge_row, text=prefill_subject,
                     bg=colour, fg="white",
                     font=("Segoe UI", 9, "bold"), padx=12, pady=4).pack(side="left", padx=(8,0))

        # ── Goal text ─────────────────────────────────────────────────────────
        tk.Label(body, text="Goal", bg=t.CARD, fg=t.MUTED,
                 font=("Segoe UI", 9, "bold")).pack(anchor="w", pady=(0, 6))
        goal_txt = tk.Text(body, height=3, wrap="word", font=("Segoe UI", 10),
                           bg=t.BG, fg=t.FG, insertbackground=t.MAIN,
                           relief="solid", bd=1, highlightthickness=1,
                           highlightbackground=t.BORDER, highlightcolor=t.MAIN,
                           padx=10, pady=8)
        goal_txt.pack(fill="x", pady=(0, 16))
        if prefill_text:
            goal_txt.insert("1.0", prefill_text)

        # ── Deadline ──────────────────────────────────────────────────────────
        tk.Label(body, text="Deadline  (optional)", bg=t.CARD, fg=t.MUTED,
                 font=("Segoe UI", 9, "bold")).pack(anchor="w", pady=(0, 8))

        # dl_state holds the resolved deadline string ("" = no deadline, or ISO date)
        dl_state = {"value": prefill_deadline or ""}

        today    = date.today()
        QUICK    = [
            ("No deadline", ""),
            ("1 week",      str(today + timedelta(weeks=1))),
            ("2 weeks",     str(today + timedelta(weeks=2))),
            ("1 month",     str(today + timedelta(days=30))),
        ]
        quick_vals = {v for _, v in QUICK}

        dl_btns: list[tk.Button] = []
        dl_display = tk.Label(body, text="", bg=t.CARD, fg=t.MUTED,
                              font=("Segoe UI", 9))
        dl_display.pack(anchor="w", pady=(0, 4))

        def _refresh_display():
            v = dl_state["value"]
            if not v:
                dl_display.configure(text="No deadline set", fg=t.MUTED)
            else:
                dl_display.configure(text=f"⏱  Deadline: {v}", fg=THEME.MAIN)

        def _select_dl(val, btn):
            dl_state["value"] = val
            for b in dl_btns: b.configure(bg=t.LIGHT, fg=t.DARK, font=("Segoe UI", 9))
            btn.configure(bg=t.MAIN, fg="white", font=("Segoe UI", 9, "bold"))
            _refresh_display()

        def _open_date_picker(btn):
            popup.grab_release()
            current = dl_state["value"] if dl_state["value"] not in quick_vals else ""
            def _on_pick(val):
                dl_state["value"] = val
                for b in dl_btns: b.configure(bg=t.LIGHT, fg=t.DARK, font=("Segoe UI", 9))
                btn.configure(bg=t.MAIN, fg="white", font=("Segoe UI", 9, "bold"))
                _refresh_display()
                popup.grab_set()
            self._pick_date_popup(current, _on_pick)

        dl_frame = tk.Frame(body, bg=t.CARD)
        dl_frame.pack(fill="x", pady=(0, 0))

        for label, val in QUICK:
            is_sel = (val == prefill_deadline)
            btn = tk.Button(dl_frame, text=label,
                            bg=t.MAIN if is_sel else t.LIGHT,
                            fg="white" if is_sel else t.DARK,
                            activebackground=t.MAIN, activeforeground="white",
                            relief="flat", cursor="hand2",
                            font=("Segoe UI", 9, "bold" if is_sel else "normal"),
                            padx=10, pady=8)
            btn.pack(side="left", padx=(0, 6))
            btn.configure(command=lambda v=val, b=btn: _select_dl(v, b))
            dl_btns.append(btn)

        # Custom date button opens the date picker popup
        is_custom = bool(prefill_deadline and prefill_deadline not in quick_vals)
        custom_btn = tk.Button(dl_frame, text="Custom date",
                               bg=t.MAIN if is_custom else t.LIGHT,
                               fg="white" if is_custom else t.DARK,
                               activebackground=t.MAIN, activeforeground="white",
                               relief="flat", cursor="hand2",
                               font=("Segoe UI", 9, "bold" if is_custom else "normal"),
                               padx=10, pady=8)
        custom_btn.pack(side="left")
        custom_btn.configure(command=lambda b=custom_btn: _open_date_picker(b))
        dl_btns.append(custom_btn)

        _refresh_display()

        err_lbl = tk.Label(body, text="", bg=t.CARD, fg="#ef4444",
                           font=("Segoe UI", 9))
        err_lbl.pack(anchor="w", pady=(10, 0))

        def _save():
            subj = subj_var.get().strip()
            text = goal_txt.get("1.0", "end-1c").strip()
            dl   = dl_state["value"]
            if not subj: err_lbl.configure(text="Pick a subject."); return
            if not text: err_lbl.configure(text="Enter a goal.");    return
            ok, msg = on_save(subj, text, dl)
            if not ok: err_lbl.configure(text=msg); return
            popup.destroy()
            self._render_list()

        tk.Button(body, text="Save goal", command=_save,
                  bg=t.MAIN, fg="white",
                  activebackground=t.DARK, activeforeground="white",
                  relief="flat", cursor="hand2",
                  font=("Segoe UI", 11, "bold"),
                  pady=12).pack(fill="x", pady=(12, 0))

        popup.bind("<Return>", lambda _e: _save())
        popup.bind("<Escape>", lambda _e: popup.destroy())
        goal_txt.focus_set()

    def _open_add_popup(self):
        self._goal_popup(
            title="New Goal",
            show_subject=True,
            on_save=lambda subj, text, dl: add_goal(subj, text, dl))

    def _open_edit_popup(self, goal: dict):
        gid = goal["goal_id"]
        self._goal_popup(
            title="Edit Goal",
            show_subject=False,
            prefill_text=goal["goal_text"],
            prefill_subject=goal["subject_name"],
            prefill_deadline=goal.get("deadline", ""),
            on_save=lambda subj, text, dl: update_goal(gid, goal_text=text, deadline=dl))

    def refresh(self):
        self._render_subject_filter()
        self._render_list()
