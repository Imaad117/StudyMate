"""
Utility: bind mousewheel scrolling to a canvas.
Call bind_mousewheel(canvas) after creating any scrollable canvas.
"""
from __future__ import annotations
import tkinter as tk


def bind_mousewheel(canvas: tk.Canvas) -> None:
    """Binds mousewheel scroll when mouse enters canvas area."""
    def _scroll(event):
        canvas.yview_scroll(-1 * (event.delta // 120), "units")

    canvas.bind("<Enter>",
        lambda _e: canvas.bind_all("<MouseWheel>", _scroll))
    canvas.bind("<Leave>",
        lambda _e: canvas.unbind_all("<MouseWheel>"))
