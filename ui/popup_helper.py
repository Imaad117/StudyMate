"""
Shared popup helper for StudyMate.
Creates a darkened overlay behind every popup window.
"""
from __future__ import annotations
import tkinter as tk
from ui.theme import THEME


def make_overlay(root: tk.Tk | tk.Toplevel) -> tk.Toplevel:
    """Creates a full-screen semi-transparent dark overlay over root."""
    overlay = tk.Toplevel(root)
    overlay.overrideredirect(True)
    overlay.configure(bg="#000000")
    overlay.wm_attributes("-alpha", 0.45)
    overlay.wm_attributes("-topmost", True)

    # Cover the entire root window
    root.update_idletasks()
    x = root.winfo_x()
    y = root.winfo_y()
    w = root.winfo_width()
    h = root.winfo_height()
    overlay.geometry(f"{w}x{h}+{x}+{y}")
    return overlay


def show_popup(
    root,
    width: int,
    height: int,
    title: str = "",
    accent_strip: bool = True,
) -> tuple[tk.Toplevel, tk.Toplevel, tk.Frame]:
    """
    Creates an overlay + centred popup window.
    Returns (overlay, popup, body_frame).
    Caller should call overlay.destroy() when done.
    """
    t = THEME
    overlay = make_overlay(root)

    popup = tk.Toplevel(root)
    if title:
        popup.title(title)
    popup.configure(bg=t.CARD)
    popup.resizable(False, False)
    popup.wm_attributes("-topmost", True)
    popup.grab_set()
    popup.transient(root)

    # centre on screen
    sw = popup.winfo_screenwidth()
    sh = popup.winfo_screenheight()
    x  = (sw - width)  // 2
    y  = (sh - height) // 2
    popup.geometry(f"{width}x{height}+{x}+{y}")

    if accent_strip:
        tk.Frame(popup, bg=t.MAIN, height=5).pack(fill="x")

    body = tk.Frame(popup, bg=t.CARD)
    body.pack(fill="both", expand=True)

    def _close():
        overlay.destroy()
        popup.destroy()

    popup.protocol("WM_DELETE_WINDOW", _close)
    popup.bind("<Escape>", lambda _e: _close())
    overlay.bind("<Button-1>", lambda _e: _close())

    return overlay, popup, body, _close
