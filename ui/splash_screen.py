from __future__ import annotations
import tkinter as tk
from pathlib import Path
from ui.theme import THEME
from resource_path import resource_path


class SplashScreen(tk.Tk):
    def __init__(self):
        super().__init__()
        self.overrideredirect(True)
        self.wm_attributes("-alpha", 0.0)
        self.configure(bg="#0f172a")
        self.resizable(False, False)

        w, h = 360, 300
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        self.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")

        self._build()
        self._alpha = 0.0
        self._phase = "fade_in"
        self._done  = False
        self.after(50, self._animate)

    def _build(self):
        frame = tk.Frame(self, bg="#0f172a")
        frame.place(relx=0.5, rely=0.5, anchor="center")

        # Try to show the PNG logo — resource_path works both as script and .exe
        logo_path = resource_path("studymate_logo.png")
        self._logo_img = None
        if logo_path.exists():
            try:
                from PIL import Image, ImageTk
                img = Image.open(logo_path).resize((100, 100), Image.LANCZOS)
                self._logo_img = ImageTk.PhotoImage(img)
                tk.Label(frame, image=self._logo_img,
                         bg="#0f172a").pack(pady=(0, 8))
            except Exception:
                pass

        # Fallback: coloured pill if no PIL
        if self._logo_img is None:
            pill = tk.Frame(frame, bg=THEME.MAIN, padx=20, pady=12)
            pill.pack(pady=(0, 8))
            tk.Label(pill, text="SM", bg=THEME.MAIN, fg="white",
                     font=("Segoe UI", 36, "bold")).pack()

        # App name
        tk.Label(frame, text="StudyMate",
                 bg="#0f172a", fg="#ffffff",
                 font=("Segoe UI", 26, "bold")).pack()

        # Tagline
        tk.Label(frame, text="Your offline study companion",
                 bg="#0f172a", fg="#475569",
                 font=("Segoe UI", 10)).pack(pady=(4, 0))

        # Loading dots
        self._dots_label = tk.Label(frame, text="",
                                     bg="#0f172a", fg=THEME.MAIN,
                                     font=("Segoe UI", 14))
        self._dots_label.pack(pady=(14, 0))
        self._dot_count = 0
        self.after(400, self._animate_dots)

    def _animate_dots(self):
        if self._done:
            return
        try:
            self._dot_count = (self._dot_count + 1) % 4
            self._dots_label.configure(text="·" * self._dot_count)
            self._dots_after_id = self.after(300, self._animate_dots)
        except Exception:
            pass

    def _animate(self):
        if self._phase == "fade_in":
            self._alpha = min(1.0, self._alpha + 0.06)
            self.wm_attributes("-alpha", self._alpha)
            if self._alpha >= 1.0:
                self._phase = "hold"
                self.after(1200, self._animate)
            else:
                self.after(30, self._animate)
        elif self._phase == "hold":
            self._phase = "fade_out"
            self.after(30, self._animate)
        elif self._phase == "fade_out":
            self._alpha = max(0.0, self._alpha - 0.07)
            try:
                self.wm_attributes("-alpha", self._alpha)
            except Exception:
                return
            if self._alpha <= 0.0:
                self._done = True
                try:
                    if hasattr(self, "_dots_after_id"):
                        self.after_cancel(self._dots_after_id)
                except Exception:
                    pass
                try:
                    self.destroy()
                except Exception:
                    pass
            else:
                self.after(30, self._animate)
