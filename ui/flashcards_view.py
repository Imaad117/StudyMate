from __future__ import annotations
from ui.scroll_helper import bind_mousewheel
import tkinter as tk
from tkinter import ttk, messagebox
from data.data_manager import get_subjects
from data.flashcards_manager import get_flashcards, add_flashcard, delete_flashcard, update_flashcard
from ui.theme import THEME
from ui.subjects_view import get_subject_colour

def _hex_lighten(hex_col: str, factor: float = 0.15) -> str:
    h = hex_col.lstrip("#")
    r, g, b = int(h[0:2],16), int(h[2:4],16), int(h[4:6],16)
    r = int(r+(255-r)*factor); g = int(g+(255-g)*factor); b = int(b+(255-b)*factor)
    return f"#{r:02x}{g:02x}{b:02x}"

def _hex_darken(hex_col: str, factor: float = 0.15) -> str:
    h = hex_col.lstrip("#")
    r, g, b = int(h[0:2],16), int(h[2:4],16), int(h[4:6],16)
    r = int(r*(1-factor)); g = int(g*(1-factor)); b = int(b*(1-factor))
    return f"#{r:02x}{g:02x}{b:02x}"


class FlashcardsView(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=THEME.BG)
        self._cards: list[dict] = []
        self._idx   = 0
        self._front = True
        self._animating = False
        self._active_subject = "All"
        self._subject_pills: dict[str, tk.Frame] = {}
        self._build()

    def _build(self):
        t = THEME

        top = tk.Frame(self, bg=t.CARD)
        top.pack(fill="x")
        tk.Frame(self, bg=t.MAIN, height=3).pack(fill="x")

        top_inner = tk.Frame(top, bg=t.CARD, padx=20, pady=12)
        top_inner.pack(fill="x")

        tk.Label(top_inner, text="Flashcards",
                 bg=t.CARD, fg=t.MAIN,
                 font=("Segoe UI", 18, "bold")).pack(side="left")

        self._count_lbl = tk.Label(top_inner, text="0 cards",
                                    bg=t.LIGHT, fg=t.MID,
                                    font=("Segoe UI", 9, "bold"), padx=10, pady=3)
        self._count_lbl.pack(side="left", padx=(12, 0))

        tk.Button(top_inner, text="＋  Create card",
                  command=self._open_create_popup,
                  bg=t.MAIN, fg="white",
                  activebackground=t.DARK, activeforeground="white",
                  relief="flat", cursor="hand2",
                  font=("Segoe UI", 10, "bold"), padx=18, pady=7).pack(side="right")

        tk.Button(top_inner, text="⋮  Manage cards",
                  command=self._open_manage_popup,
                  bg=t.LIGHT, fg=t.DARK,
                  activebackground=t.MAIN, activeforeground="white",
                  relief="flat", cursor="hand2",
                  font=("Segoe UI", 10), padx=14, pady=7).pack(side="right", padx=(0, 8))

        self._pill_bar = tk.Frame(self, bg=t.BG, padx=20, pady=10)
        self._pill_bar.pack(fill="x")
        self._render_pill_bar()

        prog_bg = tk.Frame(self, bg=t.LIGHT, height=6)
        prog_bg.pack(fill="x")
        self._prog_fill = tk.Frame(prog_bg, bg=t.MAIN, height=6)
        self._prog_fill.place(x=0, y=0, relheight=1, relwidth=0)

        # ── card row with side arrows ─────────────────────────────────────────
        card_row = tk.Frame(self, bg=t.BG)
        card_row.pack(fill="both", expand=True, pady=16)
        card_row.columnconfigure(1, weight=1)
        card_row.rowconfigure(0, weight=1)

        self._prev_btn = tk.Button(
            card_row, text="❮",
            command=self._prev,
            bg=t.BG, fg=t.MUTED,
            activebackground=t.LIGHT, activeforeground=t.DARK,
            relief="flat", cursor="hand2",
            font=("Segoe UI", 22, "bold"),
            padx=12, bd=0, highlightthickness=0)
        self._prev_btn.grid(row=0, column=0, sticky="ns", padx=(12, 0))

        self._card_canvas = tk.Canvas(card_row, bg=t.BG,
                                       highlightthickness=0, cursor="hand2")
        self._card_canvas.grid(row=0, column=1, sticky="nsew", padx=4)
        self._card_canvas.bind("<Configure>", self._on_canvas_configure)
        self._card_canvas.bind("<Button-1>", lambda _e: self._flip())

        self._next_btn = tk.Button(
            card_row, text="❯",
            command=self._next,
            bg=t.BG, fg=t.MUTED,
            activebackground=t.LIGHT, activeforeground=t.DARK,
            relief="flat", cursor="hand2",
            font=("Segoe UI", 22, "bold"),
            padx=12, bd=0, highlightthickness=0)
        self._next_btn.grid(row=0, column=2, sticky="ns", padx=(0, 12))

        # ── bottom position label ─────────────────────────────────────────────
        nav = tk.Frame(self, bg=t.BG, pady=8)
        nav.pack(fill="x")
        self._pos_lbl = tk.Label(nav, text="", bg=t.BG, fg=t.MUTED,
                                  font=("Segoe UI", 10))
        self._pos_lbl.pack()

        self._load_cards()

    # ── pill bar ──────────────────────────────────────────────────────────────

    def _render_pill_bar(self):
        t = THEME
        for w in self._pill_bar.winfo_children():
            w.destroy()
        self._subject_pills.clear()

        for name in ["All"] + get_subjects():
            is_active = (name == self._active_subject)
            colour = t.MAIN if name == "All" else get_subject_colour(name)
            bg = colour if is_active else t.CARD
            fg = "white" if is_active else t.MUTED

            pill = tk.Frame(self._pill_bar, bg=bg, cursor="hand2",
                            highlightthickness=2, highlightbackground=colour)
            pill.pack(side="left", padx=4)
            lbl = tk.Label(pill, text=name, bg=bg, fg=fg,
                           font=("Segoe UI", 9, "bold"), padx=12, pady=5)
            lbl.pack()
            self._subject_pills[name] = pill

            def _select(_e=None, n=name):
                self._active_subject = n
                self._render_pill_bar()
                self._load_cards()

            def _hover_on(_e, p=pill, l=lbl, c=colour, a=is_active):
                if not a:
                    p.configure(bg=_hex_lighten(c, 0.7))
                    l.configure(bg=_hex_lighten(c, 0.7), fg=c)

            def _hover_off(_e, p=pill, l=lbl, c=colour, a=is_active):
                if not a:
                    p.configure(bg=t.CARD)
                    l.configure(bg=t.CARD, fg=t.MUTED)

            for w in (pill, lbl):
                w.bind("<Button-1>", _select)
                w.bind("<Enter>",    _hover_on)
                w.bind("<Leave>",    _hover_off)

    # ── loading ───────────────────────────────────────────────────────────────

    def _load_cards(self):
        self._animating = False
        subj = self._active_subject
        self._cards = get_flashcards(subject=subj if subj != "All" else None)
        self._idx   = 0
        self._front = True
        self._update_count()
        self._update_nav()
        self._draw_card()
        self.after(120, self._draw_card)

    def _update_count(self):
        n = len(self._cards)
        self._count_lbl.configure(text=f"{n} card{'s' if n != 1 else ''}")

    def _update_nav(self):
        n = len(self._cards)
        # show/hide prev arrow based on position
        if n == 0 or self._idx == 0:
            self._prev_btn.configure(fg=THEME.BG)   # invisible
            self._prev_btn.configure(state="disabled", cursor="arrow")
        else:
            self._prev_btn.configure(fg=THEME.MUTED, state="normal", cursor="hand2")

        if n == 0:
            self._pos_lbl.configure(text="")
            self._update_progress(0)
        else:
            face = "front" if self._front else "back"
            self._pos_lbl.configure(text=f"{self._idx + 1} / {n}")
            self._update_progress((self._idx + 1) / n)

    def _update_progress(self, ratio: float):
        self._prog_fill.place(x=0, y=0, relheight=1, relwidth=ratio)

    # ── canvas configure ──────────────────────────────────────────────────────

    def _on_canvas_configure(self, _event=None):
        if not self._animating:
            self._draw_card()
            self.after(60, lambda: self._draw_card() if not self._animating else None)

    # ── card drawing ──────────────────────────────────────────────────────────

    def _draw_card(self, y_scale: float = 1.0, darken: float = 0.0):
        t  = THEME
        c  = self._card_canvas
        c.delete("all")
        W  = c.winfo_width()
        H  = c.winfo_height()
        if W < 20 or H < 20:
            return

        pad_x, pad_y = 30, 16
        full_w = W - pad_x * 2
        full_h = H - pad_y * 2
        ch = int(full_h * abs(y_scale))
        cx = W // 2
        cy = H // 2
        x1 = cx - full_w // 2
        x2 = cx + full_w // 2
        y1 = cy - ch // 2
        y2 = cy + ch // 2

        if not self._cards:
            self._rounded_rect(c, x1, cy-full_h//2, x2, cy+full_h//2,
                               r=20, fill=t.CARD, outline=t.BORDER, width=2)
            if full_w > 80:
                c.create_text(cx, cy-16, text="No cards yet",
                              fill=t.MUTED, font=("Segoe UI", 14), anchor="center")
                c.create_text(cx, cy+14, text="Click '＋ Create card' to add one",
                              fill=t.MUTED, font=("Segoe UI", 10), anchor="center")
            return

        card     = self._cards[self._idx]
        subj     = card.get("subject_name", "")
        colour   = get_subject_colour(subj) if subj else t.MAIN
        tint     = _hex_lighten(colour, 0.82)

        is_front = self._front
        bg_col   = tint if is_front else colour
        if darken > 0:
            bg_col = _hex_darken(bg_col, darken * 0.35)

        # shadow
        if ch > 10:
            self._rounded_rect(c, x1+5, y1+5, x2+5, y2+5,
                               r=22, fill="#d0d0d0", outline="")

        self._rounded_rect(c, x1, y1, x2, y2, r=22, fill=bg_col, outline="", width=0)

        if ch < 28:
            return

        # subject pill at top
        pill_h = max(14, int(24 * abs(y_scale)))
        pill_by1 = y1 + int(16 * abs(y_scale))
        pill_by2 = pill_by1 + pill_h
        self._rounded_rect(c, cx-50, pill_by1, cx+50, pill_by2, r=pill_h//2,
                           fill=colour if is_front else _hex_lighten(colour, 0.3),
                           outline="")
        if pill_h > 12:
            c.create_text(cx, (pill_by1+pill_by2)//2, text=subj,
                          fill="white", font=("Segoe UI", 8, "bold"), anchor="center")

        # main text — only when card is large enough
        if ch > full_h * 0.3:
            text    = card["front"] if is_front else card["back"]
            text_fg = colour if is_front else "white"
            fs = max(10, int(15 * min(1.0, abs(y_scale) * 1.5)))
            c.create_text(cx, cy, text=text,
                          fill=text_fg,
                          font=("Segoe UI", fs, "bold"),
                          width=full_w - 80,
                          justify="center", anchor="center")

        # hint at bottom — "tap to see answer" / "tap to see question"
        if not self._animating and ch > full_h * 0.6:
            hint = "tap to see answer" if is_front else "tap to see question"
            hint_fg = _hex_darken(colour, 0.1) if is_front else _hex_lighten(colour, 0.55)
            c.create_text(cx, y2 - int(16 * abs(y_scale)),
                          text=hint,
                          fill=hint_fg,
                          font=("Segoe UI", 9),
                          anchor="center")

    def _rounded_rect(self, canvas, x1, y1, x2, y2, r=16, **kw):
        canvas.create_rectangle(x1+r, y1, x2-r, y2, **kw)
        canvas.create_rectangle(x1, y1+r, x2, y2-r, **kw)
        canvas.create_oval(x1, y1, x1+2*r, y1+2*r, **kw)
        canvas.create_oval(x2-2*r, y1, x2, y1+2*r, **kw)
        canvas.create_oval(x1, y2-2*r, x1+2*r, y2, **kw)
        canvas.create_oval(x2-2*r, y2-2*r, x2, y2, **kw)

    # ── Quizlet-style flip: squish down then expand back up ───────────────────
    # phase 1: card squishes vertically toward the middle (ease in)
    # phase 2: new face expands back outward (ease out)
    # darkening during shrink makes it look like the card is physically turning

    _STEPS = 10

    def _ease(self, t: float) -> float:
        # smooth ease in-out curve so the flip doesn't feel robotic
        if t < 0.5: return 4*t*t*t
        p = 2*t - 2; return 1 + p*p*p/2

    def _flip(self):
        # don't allow flipping if mid-animation or no cards loaded
        if not self._cards or self._animating:
            return
        self._animating = True
        self._run_flip(shrinking=True, step=0)

    def _run_flip(self, shrinking: bool, step: int):
        total = self._STEPS
        if shrinking:
            # card is collapsing — scale it down and darken it
            progress = self._ease(step / total)
            y_scale  = 1.0 - progress
            darken   = progress
            self._draw_card(y_scale=max(0.01, y_scale), darken=darken)
            if step < total:
                self.after(13, lambda: self._run_flip(True, step+1))
            else:
                # halfway through — swap front/back now while card is flat
                self._front = not self._front
                self.after(6, lambda: self._run_flip(False, 0))
        else:
            # card is expanding with the new face showing
            progress = self._ease(step / total)
            y_scale  = progress
            self._draw_card(y_scale=max(0.01, y_scale), darken=0)
            if step < total:
                self.after(13, lambda: self._run_flip(False, step+1))
            else:
                # animation done — draw at full size and unlock
                self._animating = False
                self._draw_card()
                self._update_nav()

    # ── navigation ────────────────────────────────────────────────────────────

    def _next(self):
        if not self._cards or self._animating: return
        self._idx = (self._idx + 1) % len(self._cards)
        self._front = True
        self._draw_card()
        self._update_nav()

    def _prev(self):
        if not self._cards or self._animating or self._idx == 0: return
        self._idx -= 1
        self._front = True
        self._draw_card()
        self._update_nav()

    def refresh(self):
        self._animating = False
        self._render_pill_bar()
        self._load_cards()

    # ── manage popup ──────────────────────────────────────────────────────────

    def _open_manage_popup(self):
        t = THEME
        popup = tk.Toplevel(self)
        popup.title("Manage Flashcards")
        popup.configure(bg=t.BG)
        popup.grab_set()
        popup.transient(self.winfo_toplevel())
        w, h = 720, 580
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        popup.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")
        popup.resizable(True, True)
        popup.minsize(500, 400)

        tk.Frame(popup, bg=t.MAIN, height=4).pack(fill="x")

        header = tk.Frame(popup, bg=t.CARD, padx=20, pady=14)
        header.pack(fill="x")
        tk.Label(header, text="Manage Cards", bg=t.CARD,
                 fg=t.MAIN, font=("Segoe UI", 15, "bold")).pack(side="left")

        filter_var = tk.StringVar(value="All")
        filter_frame = tk.Frame(header, bg=t.CARD)
        filter_frame.pack(side="right")

        all_subjects = ["All"] + get_subjects()
        filter_pills: dict[str, tk.Label] = {}

        def _set_filter(subj):
            filter_var.set(subj)
            for s, lbl in filter_pills.items():
                is_sel = (s == subj)
                col = t.MAIN if s == "All" else get_subject_colour(s)
                lbl.configure(bg=col if is_sel else t.CARD,
                              fg="white" if is_sel else t.MUTED,
                              highlightbackground=col)
            _render_list()

        for subj in all_subjects:
            col = t.MAIN if subj == "All" else get_subject_colour(subj)
            lbl = tk.Label(filter_frame, text=subj,
                           bg=t.MAIN if subj=="All" else t.CARD,
                           fg="white" if subj=="All" else t.MUTED,
                           font=("Segoe UI", 8, "bold"), padx=10, pady=4,
                           cursor="hand2",
                           highlightthickness=1, highlightbackground=col)
            lbl.pack(side="left", padx=3)
            filter_pills[subj] = lbl
            lbl.bind("<Button-1>", lambda _e, s=subj: _set_filter(s))

        tk.Frame(popup, bg=t.BORDER, height=1).pack(fill="x")

        outer = tk.Frame(popup, bg=t.BG)
        outer.pack(fill="both", expand=True)
        canvas = tk.Canvas(outer, bg=t.BG, highlightthickness=0)
        sb = ttk.Scrollbar(outer, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)
        bind_mousewheel(canvas)

        inner = tk.Frame(canvas, bg=t.BG)
        win = canvas.create_window((0,0), window=inner, anchor="nw")
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(win, width=e.width))
        inner.bind("<Configure>", lambda _e: canvas.configure(scrollregion=canvas.bbox("all")))

        def _render_list():
            for w in inner.winfo_children():
                w.destroy()
            selected = filter_var.get()
            cards = get_flashcards(subject=selected if selected != "All" else None)
            if not cards:
                tk.Label(inner, text="No cards found.", bg=t.BG,
                         fg=t.MUTED, font=("Segoe UI", 11)).pack(pady=40)
                return
            for card in cards:
                colour = get_subject_colour(card["subject_name"])
                row = tk.Frame(inner, bg=t.CARD,
                               highlightthickness=1, highlightbackground=t.BORDER)
                row.pack(fill="x", padx=16, pady=5)
                tk.Frame(row, bg=colour, width=5).pack(side="left", fill="y")
                body = tk.Frame(row, bg=t.CARD, padx=14, pady=10)
                body.pack(side="left", fill="both", expand=True)
                tk.Label(body, text=card["subject_name"],
                         bg=colour, fg="white",
                         font=("Segoe UI", 8, "bold"), padx=8, pady=2).pack(anchor="w")
                tk.Label(body,
                         text=f"Q: {card['front'][:90]}{'…' if len(card['front'])>90 else ''}",
                         bg=t.CARD, fg=t.FG, font=("Segoe UI", 10, "bold"),
                         anchor="w", wraplength=440, justify="left").pack(anchor="w", pady=(4,0))
                tk.Label(body,
                         text=f"A: {card['back'][:90]}{'…' if len(card['back'])>90 else ''}",
                         bg=t.CARD, fg=t.MUTED, font=("Segoe UI", 9),
                         anchor="w", wraplength=440, justify="left").pack(anchor="w")
                btns = tk.Frame(row, bg=t.CARD, padx=10)
                btns.pack(side="right", fill="y")

                def _do_edit(c=card):
                    popup.grab_release(); popup.destroy()
                    self._open_edit_popup(c)

                def _do_delete(c=card):
                    if messagebox.askyesno("Delete card",
                            f"Delete this card?\n\n\"{c['front'][:60]}\"",
                            parent=popup):
                        ok, _ = delete_flashcard(c["card_id"])
                        if ok:
                            _render_list()
                            self.refresh()

                _BTN = dict(relief="flat", cursor="hand2",
                            font=("Segoe UI", 9, "bold"),
                            padx=14, pady=6)
                tk.Button(btns, text="Edit", command=_do_edit,
                          bg=t.LIGHT, fg=t.DARK,
                          activebackground=t.MAIN, activeforeground="white",
                          **_BTN).pack(pady=(10, 4))
                tk.Button(btns, text="Delete", command=_do_delete,
                          bg="#fee2e2", fg="#dc2626",
                          activebackground="#dc2626", activeforeground="white",
                          **_BTN).pack(pady=(0, 10))

        _render_list()
        popup.bind("<Escape>", lambda _e: popup.destroy())

    # ── edit popup ────────────────────────────────────────────────────────────

    def _open_edit_popup(self, card: dict):
        t = THEME
        popup = tk.Toplevel(self)
        popup.title("Edit Flashcard")
        popup.configure(bg="#1e293b")
        popup.resizable(False, False)
        popup.grab_set()
        popup.transient(self.winfo_toplevel())
        w, h = 600, 500
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        popup.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")

        colour = get_subject_colour(card["subject_name"])
        tk.Frame(popup, bg=colour, height=5).pack(fill="x")
        main = tk.Frame(popup, bg="#1e293b", padx=32, pady=28)
        main.pack(fill="both", expand=True)
        main.columnconfigure(0, weight=1)

        subj_row = tk.Frame(main, bg="#1e293b")
        subj_row.grid(row=0, column=0, sticky="w", pady=(0,20))
        tk.Label(subj_row, text="Editing card for:", bg="#1e293b",
                 fg="#94a3b8", font=("Segoe UI", 9)).pack(side="left")
        tk.Label(subj_row, text=card["subject_name"],
                 bg=colour, fg="white",
                 font=("Segoe UI", 9, "bold"), padx=10, pady=4).pack(side="left", padx=(8,0))

        for row_idx, (label, key) in enumerate(
                [("Front  (Question)", "front"), ("Back  (Answer)", "back")]):
            tk.Label(main, text=label, bg="#1e293b", fg="#94a3b8",
                     font=("Segoe UI", 9, "bold")).grid(
                row=1+row_idx*2, column=0, sticky="w", pady=(0,5))
            txt = tk.Text(main, height=6, wrap="word", font=("Segoe UI", 10),
                          bg="#334155", fg="#e2e8f0", insertbackground="white",
                          relief="flat", padx=12, pady=10,
                          highlightthickness=1, highlightbackground="#475569",
                          highlightcolor=t.MAIN)
            txt.grid(row=2+row_idx*2, column=0, sticky="ew", pady=(0,16))
            txt.insert("1.0", card[key])
            if key == "front": front_txt = txt
            else:              back_txt  = txt

        err_lbl = tk.Label(main, text="", bg="#1e293b", fg="#f87171", font=("Segoe UI", 9))
        err_lbl.grid(row=5, column=0, sticky="w")

        btn_row = tk.Frame(main, bg="#1e293b")
        btn_row.grid(row=6, column=0, sticky="ew", pady=(12,0))
        btn_row.columnconfigure(0, weight=1); btn_row.columnconfigure(1, weight=1)

        def _save():
            ok, msg = update_flashcard(card["card_id"],
                                       front_txt.get("1.0","end-1c").strip(),
                                       back_txt.get("1.0","end-1c").strip())
            if not ok: err_lbl.configure(text=msg); return
            popup.destroy(); self.refresh()

        tk.Button(btn_row, text="Save changes", command=_save,
                  bg=t.MAIN, fg="white",
                  activebackground=t.DARK, activeforeground="white",
                  relief="flat", cursor="hand2",
                  font=("Segoe UI", 10, "bold"), pady=10).grid(
            row=0, column=0, sticky="ew", padx=(0,6))
        tk.Button(btn_row, text="Cancel", command=popup.destroy,
                  bg="#334155", fg="#e2e8f0",
                  activebackground="#475569", activeforeground="white",
                  relief="flat", cursor="hand2",
                  font=("Segoe UI", 10), pady=10).grid(
            row=0, column=1, sticky="ew", padx=(6,0))

        popup.bind("<Escape>", lambda _e: popup.destroy())
        front_txt.focus_set()

    # ── create popup ──────────────────────────────────────────────────────────

    def _open_create_popup(self):
        t = THEME
        popup = tk.Toplevel(self)
        popup.title("Create Flashcard")
        popup.configure(bg=t.CARD)
        popup.resizable(False, False)
        popup.grab_set()
        popup.transient(self.winfo_toplevel())
        w, h = 800, 620
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        popup.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")

        tk.Frame(popup, bg=t.MAIN, height=5).pack(fill="x")
        main = tk.Frame(popup, bg=t.CARD)
        main.pack(fill="both", expand=True)
        main.columnconfigure(0, weight=1); main.columnconfigure(1, weight=1)
        main.rowconfigure(0, weight=1)

        left = tk.Frame(main, bg="#1e293b", padx=24, pady=18)
        left.grid(row=0, column=0, sticky="nsew")
        left.columnconfigure(0, weight=1)

        tk.Label(left, text="Create New Card", bg="#1e293b", fg="#e2e8f0",
                 font=("Segoe UI", 13, "bold")).grid(row=0, column=0, sticky="w", pady=(0,14))

        tk.Label(left, text="Subject", bg="#1e293b", fg="#94a3b8",
                 font=("Segoe UI", 9, "bold")).grid(row=1, column=0, sticky="w", pady=(0,5))
        subj_var = tk.StringVar()
        subjects = get_subjects()

        subj_pill_frame = tk.Frame(left, bg="#1e293b")
        subj_pill_frame.grid(row=2, column=0, sticky="ew", pady=(0,12))
        subj_btns: list[tk.Button] = []

        def _pick_subj(name, btn):
            subj_var.set(name)
            c = get_subject_colour(name)
            for b in subj_btns: b.configure(bg="#334155", fg="#94a3b8", font=("Segoe UI", 9))
            btn.configure(bg=c, fg="white", font=("Segoe UI", 9, "bold"))
            _update_preview()

        cols = 3
        for i, name in enumerate(subjects):
            c = get_subject_colour(name)
            is_first = (i == 0)
            btn = tk.Button(subj_pill_frame, text=name,
                            bg=c if is_first else "#334155",
                            fg="white" if is_first else "#94a3b8",
                            activebackground=c, activeforeground="white",
                            relief="flat", cursor="hand2",
                            font=("Segoe UI", 9, "bold" if is_first else "normal"),
                            padx=10, pady=5)
            btn.grid(row=i//cols, column=i%cols, padx=3, pady=2, sticky="ew")
            subj_pill_frame.columnconfigure(i%cols, weight=1)
            btn.configure(command=lambda n=name, b=btn: _pick_subj(n, b))
            subj_btns.append(btn)
            if is_first and subjects:
                subj_var.set(name)

        tk.Label(left, text="Front  (Question)", bg="#1e293b", fg="#94a3b8",
                 font=("Segoe UI", 9, "bold")).grid(row=3, column=0, sticky="w", pady=(0,4))
        front_txt = tk.Text(left, height=4, wrap="word", font=("Segoe UI", 10),
                            bg="#334155", fg="#e2e8f0", insertbackground="white",
                            relief="flat", padx=10, pady=8,
                            highlightthickness=1, highlightbackground="#475569",
                            highlightcolor=t.MAIN)
        front_txt.grid(row=4, column=0, sticky="ew", pady=(0,12))

        tk.Label(left, text="Back  (Answer)", bg="#1e293b", fg="#94a3b8",
                 font=("Segoe UI", 9, "bold")).grid(row=5, column=0, sticky="w", pady=(0,4))
        back_txt = tk.Text(left, height=4, wrap="word", font=("Segoe UI", 10),
                           bg="#334155", fg="#e2e8f0", insertbackground="white",
                           relief="flat", padx=10, pady=8,
                           highlightthickness=1, highlightbackground="#475569",
                           highlightcolor=t.MAIN)
        back_txt.grid(row=6, column=0, sticky="ew", pady=(0,12))

        err_lbl = tk.Label(left, text="", bg="#1e293b", fg="#f87171", font=("Segoe UI", 9))
        err_lbl.grid(row=7, column=0, sticky="w")

        save_btn = tk.Button(left, text="Create card",
                             bg=t.MAIN, fg="white",
                             activebackground=t.DARK, activeforeground="white",
                             relief="flat", cursor="hand2",
                             font=("Segoe UI", 10, "bold"), pady=10)
        save_btn.grid(row=8, column=0, sticky="ew", pady=(8, 0))

        right = tk.Frame(main, bg=t.BG, padx=24, pady=24)
        right.grid(row=0, column=1, sticky="nsew")
        right.columnconfigure(0, weight=1); right.rowconfigure(1, weight=1)

        tk.Label(right, text="Preview", bg=t.BG, fg=t.MUTED,
                 font=("Segoe UI", 9, "bold")).grid(row=0, column=0, sticky="w", pady=(0,10))

        preview_canvas = tk.Canvas(right, bg=t.BG, highlightthickness=0)
        preview_canvas.grid(row=1, column=0, sticky="nsew")
        preview_canvas.bind("<Button-1>", lambda _e: _toggle_preview())
        self._preview_front = True

        def _toggle_preview():
            self._preview_front = not self._preview_front; _update_preview()

        def _draw_preview(text, subj, is_front):
            preview_canvas.delete("all")
            W = preview_canvas.winfo_width(); H = preview_canvas.winfo_height()
            if W < 20 or H < 20: return
            colour = get_subject_colour(subj) if subj else t.MAIN
            tint   = _hex_lighten(colour, 0.82)
            bg_col = tint if is_front else colour
            pad = 12
            self._rounded_rect(preview_canvas, pad, pad, W-pad, H-pad, r=16, fill=bg_col, outline="")
            cx = W//2
            self._rounded_rect(preview_canvas, cx-40, pad+10, cx+40, pad+26, r=10, fill=colour, outline="")
            preview_canvas.create_text(cx, pad+18, text=subj or "Subject",
                                       fill="white", font=("Segoe UI", 8, "bold"), anchor="center")
            display = text.strip() or ("Question here" if is_front else "Answer here")
            preview_canvas.create_text(cx, H//2, text=display,
                                       fill=colour if is_front else "white",
                                       font=("Segoe UI", 11, "bold"),
                                       width=W-50, justify="center", anchor="center")
            hint = "tap to see answer" if is_front else "tap to see question"
            hint_fg = _hex_darken(colour, 0.1) if is_front else _hex_lighten(colour, 0.55)
            preview_canvas.create_text(cx, H-18, text=hint,
                                       fill=hint_fg, font=("Segoe UI", 8), anchor="center")

        def _update_preview(_e=None):
            text = front_txt.get("1.0","end-1c") if self._preview_front else back_txt.get("1.0","end-1c")
            _draw_preview(text, subj_var.get(), self._preview_front)

        preview_canvas.bind("<Configure>", lambda _e: _update_preview())
        front_txt.bind("<KeyRelease>", _update_preview)
        back_txt.bind("<KeyRelease>",  _update_preview)
        # subject changes trigger preview via _pick_subj directly

        def _save():
            ok, msg = add_flashcard(subj_var.get(),
                                    front_txt.get("1.0","end-1c").strip(),
                                    back_txt.get("1.0","end-1c").strip())
            if not ok: err_lbl.configure(text=msg); return
            popup.destroy(); self.refresh()

        save_btn.configure(command=_save)
        popup.bind("<Escape>", lambda _e: popup.destroy())
        front_txt.focus_set()
