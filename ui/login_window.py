"""
Profile selection — full screen, large circles, clean.
Edit mode for PIN management and deletion.
"""
from __future__ import annotations
import tkinter as tk
from tkinter import messagebox, simpledialog
import app_config as cfg
from ui.theme import THEME

AVATAR_COLOURS = [
    "#ec4899","#3b82f6","#7c3aed","#f97316",
    "#22c55e","#ef4444","#14b8a6","#f59e0b",
]

def _ac(name: str) -> str:
    return AVATAR_COLOURS[sum(ord(c) for c in name) % len(AVATAR_COLOURS)]


class LoginWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("StudyMate")
        self.configure(bg="#0a0f1e")
        self.wm_attributes("-alpha", 0.0)
        # Full screen from the start
        self.state("zoomed")
        self.resizable(True, True)

        self._chosen: str | None = None
        self._edit_mode = False
        self._build()
        self._alpha = 0.0
        self.after(20, self._fade_in)

    def _fade_in(self):
        self._alpha = min(1.0, self._alpha + 0.08)
        try:
            self.wm_attributes("-alpha", self._alpha)
        except Exception:
            return
        if self._alpha < 1.0:
            self.after(20, self._fade_in)

    def _fade_out(self, alpha=1.0):
        alpha = max(0.0, alpha - 0.1)
        try:
            self.wm_attributes("-alpha", alpha)
        except Exception:
            return
        if alpha > 0:
            self.after(20, lambda a=alpha: self._fade_out(a))
        else:
            try:
                self.destroy()
            except Exception:
                pass

    def _build(self):
        # centre content vertically
        wrapper = tk.Frame(self, bg="#0a0f1e")
        wrapper.place(relx=0.5, rely=0.5, anchor="center")

        # logo pill
        pill = tk.Frame(wrapper, bg=THEME.MAIN, padx=24, pady=10)
        pill.pack()
        tk.Label(pill, text="StudyMate", bg=THEME.MAIN, fg="white",
                 font=("Segoe UI", 26, "bold")).pack()

        self._title_lbl = tk.Label(wrapper, text="Who's studying today?",
                                    bg="#0a0f1e", fg="#e2e8f0",
                                    font=("Segoe UI", 20, "bold"))
        self._title_lbl.pack(pady=(20, 6))

        self._sub_lbl = tk.Label(wrapper,
                                  text="Select your profile to continue",
                                  bg="#0a0f1e", fg="#475569",
                                  font=("Segoe UI", 12))
        self._sub_lbl.pack(pady=(0, 36))

        self._profiles_row = tk.Frame(wrapper, bg="#0a0f1e")
        self._profiles_row.pack()

        self._bottom = tk.Frame(wrapper, bg="#0a0f1e")
        self._bottom.pack(pady=(32, 0))

        self._edit_btn = tk.Button(
            self._bottom, text="✏  Edit profiles",
            command=self._toggle_edit,
            bg="#1e293b", fg="#94a3b8",
            activebackground="#334155", activeforeground="white",
            relief="flat", cursor="hand2",
            font=("Segoe UI", 12), padx=28, pady=10)
        self._edit_btn.pack()

        self._err_var = tk.StringVar()
        tk.Label(wrapper, textvariable=self._err_var,
                 bg="#0a0f1e", fg="#f87171",
                 font=("Segoe UI", 9)).pack(pady=(10, 0))

        self._render_profiles()

    def _render_profiles(self):
        for w in self._profiles_row.winfo_children():
            w.destroy()

        profiles = cfg.list_profiles()
        for name in profiles:
            self._profile_card(name)
        self._add_card()

        if self._edit_mode:
            self._title_lbl.configure(text="Edit profiles")
            self._sub_lbl.configure(text="Tap a profile's ✕ to remove it, or tap the PIN label to manage PIN")
            self._edit_btn.configure(text="✓  Done", fg="#22c55e")
        else:
            self._title_lbl.configure(text="Who's studying today?")
            self._sub_lbl.configure(text="Select your profile to continue")
            self._edit_btn.configure(text="✏  Edit profiles", fg="#94a3b8")

    def _make_avatar(self, letter: str, colour: str, size: int,
                     outline: str = None):
        # renders a smooth circular avatar using PIL
        # we draw it at 4x the display size then scale it down — this gives anti-aliased edges
        # tkinter's built-in canvas ovals are pixelated so this looks much better
        try:
            from PIL import Image, ImageDraw, ImageFont as PILFont, ImageTk
            scale = 4
            S = size * scale   # draw at 4x resolution
            img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
            d   = ImageDraw.Draw(img)
            pad = scale * 3
            if outline:
                # draw the outline ring first, then the coloured circle on top
                d.ellipse([0, 0, S-1, S-1], fill=outline)
                d.ellipse([pad, pad, S-pad, S-pad], fill=colour)
            else:
                d.ellipse([pad, pad, S-pad, S-pad], fill=colour)

            # draw the initial letter centred in the circle
            fs = int(S * 0.38)
            for path in ["C:/Windows/Fonts/arialbd.ttf",
                         "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"]:
                try:
                    font = PILFont.truetype(path, fs); break
                except Exception:
                    font = None
            if font is None:
                font = PILFont.load_default()
            bbox = d.textbbox((0, 0), letter, font=font)
            lw, lh = bbox[2]-bbox[0], bbox[3]-bbox[1]
            d.text(((S-lw)//2 - bbox[0], (S-lh)//2 - bbox[1]),
                   letter, font=font, fill="white")

            # scale back down using LANCZOS for smooth edges
            img = img.resize((size, size), Image.LANCZOS)
            return ImageTk.PhotoImage(img)
        except Exception:
            return None  # fallback to plain canvas oval if PIL isn't available

    def _profile_card(self, name: str):
        colour  = _ac(name)
        has_pin = cfg.get_profile_pin(name) is not None

        outer = tk.Frame(self._profiles_row, bg="#0a0f1e",
                         cursor="hand2" if not self._edit_mode else "arrow")
        outer.pack(side="left", padx=18)

        size = 130
        cv = tk.Canvas(outer, width=size, height=size,
                       bg="#0a0f1e", highlightthickness=0)
        cv.pack()

        # Try PIL smooth circles first
        img_n = self._make_avatar(name[0].upper(), colour, size)
        img_h = self._make_avatar(name[0].upper(), colour, size, outline="white")

        if img_n:
            outer._img_n = img_n
            outer._img_h = img_h
            cv.create_image(size//2, size//2, anchor="center",
                            image=img_n, tags="avt")

            if has_pin:
                bs, bp = 30, 4
                bx, by = size-bs-bp, size-bs-bp
                # dark ring then white fill so it pops on any avatar colour
                cv.create_oval(bx-2, by-2, bx+bs+2, by+bs+2,
                               fill="#0a0f1e", outline="")
                cv.create_oval(bx, by, bx+bs, by+bs,
                               fill="white", outline="")
                cv.create_text(bx+bs//2, by+bs//2-1, text="🔒",
                               font=("Segoe UI", 13))

            if self._edit_mode:
                cv.create_oval(size-34, 0, size, 34,
                               fill="#ef4444", outline="", tags="del_bg")
                cv.create_text(size-17, 17, text="✕",
                               fill="white", font=("Segoe UI", 12, "bold"),
                               tags="del_x")
                for tag in ("del_bg", "del_x"):
                    cv.tag_bind(tag, "<Button-1>",
                                lambda _e, n=name: self._delete_profile(n))

            def _on(_e):
                if outer._img_h:
                    cv.delete("avt")
                    cv.create_image(size//2, size//2, anchor="center",
                                    image=outer._img_h, tags="avt")
            def _off(_e):
                cv.delete("avt")
                cv.create_image(size//2, size//2, anchor="center",
                                image=outer._img_n, tags="avt")
        else:
            # fallback plain oval
            pad = 4
            cv.create_oval(pad, pad, size-pad, size-pad,
                           fill=colour, outline="", tags="circle")
            cv.create_text(size//2, size//2, text=name[0].upper(),
                           fill="white", font=("Segoe UI", 40, "bold"),
                           tags="letter")
            if has_pin:
                cv.create_oval(size-32, size-32, size, size,
                               fill="#0a0f1e", outline="")
                cv.create_oval(size-30, size-30, size-2, size-2,
                               fill="white", outline="")
                cv.create_text(size-16, size-17, text="🔒",
                               font=("Segoe UI", 13))
            if self._edit_mode:
                cv.create_oval(size-32, 0, size, 32,
                               fill="#ef4444", outline="", tags="del_bg")
                cv.create_text(size-16, 16, text="✕",
                               fill="white", font=("Segoe UI", 11, "bold"),
                               tags="del_x")
                for tag in ("del_bg", "del_x"):
                    cv.tag_bind(tag, "<Button-1>",
                                lambda _e, n=name: self._delete_profile(n))

            def _on(_e, cv=cv, c=colour, s=size, p=pad):
                cv.delete("circle")
                cv.create_oval(p-4, p-4, s-p+4, s-p+4,
                               fill=c, outline="white", width=4, tags="circle")
                cv.tag_raise("letter")
            def _off(_e, cv=cv, c=colour, s=size, p=pad):
                cv.delete("circle")
                cv.create_oval(p, p, s-p, s-p,
                               fill=c, outline="", tags="circle")
                cv.tag_raise("letter")

        lbl = tk.Label(outer, text=name, bg="#0a0f1e", fg="#e2e8f0",
                       font=("Segoe UI", 13, "bold"))
        lbl.pack(pady=(12, 0))

        if self._edit_mode:
            ptxt = "🔒 PIN set  (tap to change)" if has_pin else "No PIN  (tap to add)"
            pfg  = "#86efac" if has_pin else "#475569"
            pl = tk.Label(outer, text=ptxt, bg="#0a0f1e", fg=pfg,
                          font=("Segoe UI", 9), cursor="hand2")
            pl.pack(pady=(4, 0))
            pl.bind("<Button-1>", lambda _e, n=name: self._manage_pin(n))

        for w in (outer, cv, lbl):
            w.bind("<Enter>", _on)
            w.bind("<Leave>", _off)
            if not self._edit_mode:
                w.bind("<Button-1>", lambda _e, n=name: self._try_enter(n))

    def _add_card(self):
        outer = tk.Frame(self._profiles_row, bg="#0a0f1e", cursor="hand2")
        outer.pack(side="left", padx=18)
        size = 130
        cv = tk.Canvas(outer, width=size, height=size,
                       bg="#0a0f1e", highlightthickness=0)
        cv.pack()

        img_n = self._make_avatar("+", "#1e293b", size)
        img_h = self._make_avatar("+", "#1e3a2f", size, outline=THEME.MAIN)

        if img_n:
            outer._img_n = img_n
            outer._img_h = img_h
            cv.create_image(size//2, size//2, anchor="center",
                            image=img_n, tags="avt")
            lbl = tk.Label(outer, text="Add new", bg="#0a0f1e", fg="#475569",
                           font=("Segoe UI", 13))
            lbl.pack(pady=(12, 0))

            def _on(_e):
                cv.delete("avt")
                cv.create_image(size//2, size//2, anchor="center",
                                image=outer._img_h, tags="avt")
                lbl.configure(fg=THEME.MAIN)
            def _off(_e):
                cv.delete("avt")
                cv.create_image(size//2, size//2, anchor="center",
                                image=outer._img_n, tags="avt")
                lbl.configure(fg="#475569")
        else:
            pad = 4
            cv.create_oval(pad, pad, size-pad, size-pad,
                           fill="#1e293b", outline="#334155", width=2, tags="circle")
            cv.create_text(size//2, size//2, text="+",
                           fill="#475569", font=("Segoe UI", 40, "bold"),
                           tags="letter")
            lbl = tk.Label(outer, text="Add new", bg="#0a0f1e", fg="#475569",
                           font=("Segoe UI", 13))
            lbl.pack(pady=(12, 0))

            def _on(_e):
                cv.delete("circle")
                cv.create_oval(pad-5, pad-5, size-pad+5, size-pad+5,
                               fill="#1e293b", outline=THEME.MAIN, width=4,
                               tags="circle")
                cv.tag_raise("letter")
                cv.itemconfig("letter", fill=THEME.MAIN)
                lbl.configure(fg=THEME.MAIN)
            def _off(_e):
                cv.delete("circle")
                cv.create_oval(pad, pad, size-pad, size-pad,
                               fill="#1e293b", outline="#334155", width=2,
                               tags="circle")
                cv.tag_raise("letter")
                cv.itemconfig("letter", fill="#475569")
                lbl.configure(fg="#475569")

        for w in (outer, cv, lbl):
            w.bind("<Enter>", _on)
            w.bind("<Leave>", _off)
            w.bind("<Button-1>", lambda _e: self._create_popup())

    def _toggle_edit(self):
        self._edit_mode = not self._edit_mode
        self._render_profiles()

    def _manage_pin(self, name: str):
        choice = simpledialog.askstring(
            f"PIN — {name}",
            "Enter new 4-digit PIN (blank to remove):",
            parent=self)
        if choice is None:
            return
        choice = choice.strip()
        if choice == "":
            cfg.set_profile_pin(name, None)
            messagebox.showinfo("Done", "PIN removed.", parent=self)
        elif len(choice) == 4 and choice.isdigit():
            cfg.set_profile_pin(name, choice)
            messagebox.showinfo("Done", "PIN set.", parent=self)
        else:
            messagebox.showerror("Invalid", "PIN must be exactly 4 digits.",
                                  parent=self)
        self._render_profiles()

    def _delete_profile(self, name: str):
        pin = cfg.get_profile_pin(name)
        if pin:
            entered = simpledialog.askstring(
                "PIN required",
                f"Enter PIN for '{name}' to delete it:",
                parent=self, show="*")
            if entered is None:
                return
            ok, msg = cfg.delete_profile(name, entered.strip())
        else:
            if not messagebox.askyesno(
                "Delete", f"Delete '{name}' and all their data?",
                parent=self):
                return
            ok, msg = cfg.delete_profile(name)
        if not ok:
            messagebox.showerror("Error", msg, parent=self)
        self._render_profiles()

    def _create_popup(self):
        popup = tk.Toplevel(self)
        popup.title("New Profile")
        popup.configure(bg="#1e293b")
        popup.resizable(False, False)
        popup.grab_set()
        popup.transient(self)
        # Fixed size, auto-sized to content
        popup.update_idletasks()
        w, h = 400, 340
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        popup.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")

        tk.Label(popup, text="Create Profile",
                 bg="#1e293b", fg="#e2e8f0",
                 font=("Segoe UI", 15, "bold")).pack(pady=(28, 20))

        for lbl_txt, attr, show in [
            ("Name:", "_name_var", ""),
            ("PIN (optional, 4 digits):", "_pin_var", "●"),
        ]:
            tk.Label(popup, text=lbl_txt, bg="#1e293b", fg="#94a3b8",
                     font=("Segoe UI", 10)).pack(anchor="w", padx=28)
            var = tk.StringVar()
            setattr(self, attr, var)
            tk.Entry(popup, textvariable=var,
                     show=show if show else "",
                     bg="#334155", fg="#e2e8f0",
                     insertbackground="white",
                     relief="flat",
                     font=("Segoe UI", 12)).pack(
                fill="x", padx=28, ipady=8,
                pady=(4, 14 if attr == "_name_var" else 0))

        self._create_err = tk.StringVar()
        tk.Label(popup, textvariable=self._create_err,
                 bg="#1e293b", fg="#f87171",
                 font=("Segoe UI", 9)).pack(pady=(8, 0))

        def _create():
            name = self._name_var.get().strip()
            pin  = self._pin_var.get().strip()
            if pin and (len(pin) != 4 or not pin.isdigit()):
                self._create_err.set("PIN must be exactly 4 digits.")
                return
            ok, msg = cfg.create_profile(name, pin or None)
            if not ok:
                self._create_err.set(msg)
                return
            popup.destroy()
            self._render_profiles()

        tk.Button(popup, text="Create profile",
                  command=_create,
                  bg=THEME.MAIN, fg="white",
                  activebackground=THEME.DARK, activeforeground="white",
                  relief="flat", cursor="hand2",
                  font=("Segoe UI", 11, "bold"),
                  pady=10).pack(fill="x", padx=28, pady=(12, 0))

        popup.bind("<Return>", lambda _e: _create())
        popup.bind("<Escape>", lambda _e: popup.destroy())

    def _try_enter(self, name: str):
        if cfg.get_profile_pin(name) is None:
            self._enter(name)
        else:
            self._pin_popup(name)

    def _pin_popup(self, name: str):
        popup = tk.Toplevel(self)
        popup.title("")
        popup.configure(bg="#1e293b")
        popup.resizable(False, False)
        popup.grab_set()
        popup.transient(self)
        w, h = 300, 440
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        popup.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")

        colour = _ac(name)
        cv = tk.Canvas(popup, width=68, height=68,
                        bg="#1e293b", highlightthickness=0)
        cv.pack(pady=(18, 0))
        cv.create_oval(3, 3, 65, 65, fill=colour, outline="")
        cv.create_text(34, 34, text=name[0].upper(),
                       fill="white", font=("Segoe UI", 24, "bold"))

        tk.Label(popup, text=name, bg="#1e293b", fg="#e2e8f0",
                 font=("Segoe UI", 12, "bold")).pack(pady=(6, 0))
        tk.Label(popup, text="Enter PIN", bg="#1e293b", fg="#64748b",
                 font=("Segoe UI", 9)).pack(pady=(2, 10))

        dots_f = tk.Frame(popup, bg="#1e293b")
        dots_f.pack()
        dots = []
        for _ in range(4):
            d = tk.Label(dots_f, text="○", bg="#1e293b", fg="#334155",
                         font=("Segoe UI", 18))
            d.pack(side="left", padx=6)
            dots.append(d)

        err_lbl = tk.Label(popup, text="", bg="#1e293b", fg="#f87171",
                           font=("Segoe UI", 9))
        err_lbl.pack(pady=(4, 0))

        pin_entered = []

        def _upd():
            for i, d in enumerate(dots):
                d.configure(text="●" if i < len(pin_entered) else "○",
                            fg=THEME.MAIN if i < len(pin_entered) else "#334155")

        def _press(digit):
            if len(pin_entered) >= 4:
                return
            pin_entered.append(str(digit))
            _upd()
            if len(pin_entered) == 4:
                popup.after(150, _check)

        def _back():
            if pin_entered:
                pin_entered.pop()
                _upd()
                err_lbl.configure(text="")

        def _check():
            if cfg.verify_pin(name, "".join(pin_entered)):
                popup.destroy()
                self.after(50, lambda: self._enter(name))
            else:
                pin_entered.clear()
                _upd()
                err_lbl.configure(text="Incorrect PIN")

        numpad = tk.Frame(popup, bg="#1e293b")
        numpad.pack(pady=(8, 14))
        for i, val in enumerate([1,2,3,4,5,6,7,8,9,None,0,"⌫"]):
            r, c = divmod(i, 3)
            if val is None:
                tk.Frame(numpad, bg="#1e293b", width=62, height=36).grid(
                    row=r, column=c, padx=3, pady=3)
                continue
            cmd = _back if val == "⌫" else lambda v=val: _press(v)
            tk.Button(numpad, text=str(val), command=cmd,
                      bg="#334155", fg="#e2e8f0",
                      activebackground=THEME.MAIN,
                      activeforeground="white",
                      font=("Segoe UI", 12, "bold"),
                      width=4, relief="flat", cursor="hand2").grid(
                row=r, column=c, padx=3, pady=3, ipady=4)

        popup.bind("<Escape>", lambda _e: popup.destroy())

    def _enter(self, name: str):
        cfg.set_active_profile(name)
        self._chosen = name
        self.after(50, self._fade_out)

    def get_chosen_profile(self) -> str | None:
        return self._chosen
