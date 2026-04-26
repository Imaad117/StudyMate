from __future__ import annotations
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from data.backup_manager import export_backup, import_backup
from ui.theme import THEME
from ui.scroll_helper import bind_mousewheel


class DataView(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=THEME.BG)
        self._build()

    def _build(self):
        t = THEME

        # header
        top = tk.Frame(self, bg=t.CARD)
        top.pack(fill="x")
        tk.Frame(self, bg=t.MAIN, height=3).pack(fill="x")
        top_inner = tk.Frame(top, bg=t.CARD, padx=20, pady=14)
        top_inner.pack(fill="x")
        tk.Label(top_inner, text="Export / Import",
                 bg=t.CARD, fg="#ffffff" if t.dark_mode else t.MAIN,
                 font=("Segoe UI", 18, "bold")).pack(side="left")

        # scrollable body
        outer = tk.Frame(self, bg=t.BG)
        outer.pack(fill="both", expand=True)
        outer.rowconfigure(0, weight=1)
        outer.columnconfigure(0, weight=1)

        canvas = tk.Canvas(outer, bg=t.BG, highlightthickness=0)
        canvas.grid(row=0, column=0, sticky="nsew")
        sb = ttk.Scrollbar(outer, orient="vertical", command=canvas.yview)
        sb.grid(row=0, column=1, sticky="ns")
        canvas.configure(yscrollcommand=sb.set)

        body = tk.Frame(canvas, bg=t.BG)
        win = canvas.create_window((0, 0), window=body, anchor="nw")
        body.bind("<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>",
            lambda e: canvas.itemconfig(win, width=e.width))
        bind_mousewheel(canvas)
        body.columnconfigure(0, weight=1)

        def _card(title, row):
            c = tk.Frame(body, bg=t.CARD,
                         highlightthickness=1, highlightbackground=t.BORDER)
            c.grid(row=row, column=0, sticky="ew",
                   padx=20, pady=(16 if row == 0 else 0, 12))
            c.columnconfigure(0, weight=1)
            tk.Label(c, text=title, bg=t.CARD, fg=t.MID,
                     font=("Segoe UI", 9, "bold")).grid(
                row=0, column=0, sticky="w", padx=16, pady=(14, 8))
            return c

        # ── export section ────────────────────────────────────────────────────
        exp = _card("EXPORT BACKUP", 0)

        tk.Label(exp,
                 text="Saves your sessions, goals, flashcards, subjects, and colour settings "
                      "into a timestamped folder of your choice.",
                 bg=t.CARD, fg=t.FG, font=("Segoe UI", 10),
                 wraplength=580, justify="left").grid(
            row=1, column=0, sticky="w", padx=16, pady=(0, 10))

        # what gets exported
        files_frame = tk.Frame(exp, bg=t.CARD)
        files_frame.grid(row=2, column=0, sticky="w", padx=16, pady=(0, 12))
        for name in ["studymate_sessions.csv", "studymate_goals.csv",
                     "studymate_flashcards.csv", "studymate_subjects.csv",
                     "subject_colours.json"]:
            row_f = tk.Frame(files_frame, bg=t.CARD)
            row_f.pack(anchor="w")
            tk.Label(row_f, text="•", bg=t.CARD, fg=t.MAIN,
                     font=("Segoe UI", 9)).pack(side="left")
            tk.Label(row_f, text=name, bg=t.CARD, fg=t.MUTED,
                     font=("Segoe UI", 9)).pack(side="left", padx=(6, 0))

        self.export_status = tk.StringVar()
        tk.Label(exp, textvariable=self.export_status,
                 bg=t.CARD, fg=t.DARK, font=("Segoe UI", 9),
                 wraplength=580).grid(
            row=3, column=0, sticky="w", padx=16, pady=(0, 4))

        tk.Button(exp, text="Choose folder and export…",
                  command=self._export,
                  bg=t.MAIN, fg="white",
                  activebackground=t.DARK, activeforeground="white",
                  relief="flat", cursor="hand2",
                  font=("Segoe UI", 10, "bold"),
                  padx=16, pady=9).grid(
            row=4, column=0, sticky="w", padx=16, pady=(4, 16))

        # ── import section ────────────────────────────────────────────────────
        imp = _card("IMPORT BACKUP", 1)

        tk.Label(imp,
                 text="Select the backup folder (the one named studymate_backup_...) "
                      "and all files inside it will be restored. "
                      "This overwrites your current data for this profile.",
                 bg=t.CARD, fg=t.FG, font=("Segoe UI", 10),
                 wraplength=580, justify="left").grid(
            row=1, column=0, sticky="w", padx=16, pady=(0, 12))

        # show which folder has been selected
        self._import_folder = tk.StringVar(value="No folder selected")
        folder_row = tk.Frame(imp, bg=t.CARD)
        folder_row.grid(row=2, column=0, sticky="ew", padx=16, pady=(0, 10))
        folder_row.columnconfigure(1, weight=1)
        tk.Button(folder_row, text="Browse for backup folder…",
                  command=self._pick_import_folder,
                  bg=t.LIGHT, fg=t.DARK,
                  activebackground=t.MAIN, activeforeground="white",
                  relief="flat", cursor="hand2",
                  font=("Segoe UI", 10), padx=12, pady=7).grid(
            row=0, column=0, sticky="w")
        tk.Label(folder_row, textvariable=self._import_folder,
                 bg=t.CARD, fg=t.MUTED, font=("Segoe UI", 9),
                 anchor="w", wraplength=400).grid(
            row=0, column=1, sticky="w", padx=(12, 0))

        self.import_status = tk.StringVar()
        tk.Label(imp, textvariable=self.import_status,
                 bg=t.CARD, fg=t.DARK, font=("Segoe UI", 9)).grid(
            row=3, column=0, sticky="w", padx=16, pady=(0, 4))

        tk.Button(imp, text="Restore from this backup",
                  command=self._import,
                  bg=t.MAIN, fg="white",
                  activebackground=t.DARK, activeforeground="white",
                  relief="flat", cursor="hand2",
                  font=("Segoe UI", 10, "bold"),
                  padx=16, pady=9).grid(
            row=4, column=0, sticky="w", padx=16, pady=(4, 16))

        # tip
        tip = tk.Frame(body, bg=t.LIGHT,
                       highlightthickness=1, highlightbackground=t.BORDER)
        tip.grid(row=2, column=0, sticky="ew", padx=20, pady=(0, 20))
        tk.Label(tip,
                 text="💡  Tip: keep your backup folder on a USB drive or cloud storage "
                      "so you don't lose data if something happens to your machine.",
                 bg=t.LIGHT, fg=t.MID, font=("Segoe UI", 9),
                 wraplength=580, justify="left").pack(padx=16, pady=10)

    # ── export ────────────────────────────────────────────────────────────────

    def _export(self):
        folder = filedialog.askdirectory(title="Choose where to save your backup")
        if not folder:
            return
        ok, msg, path = export_backup(folder)
        if ok:
            self.export_status.set(f"✓  {msg}")
            messagebox.showinfo("Export complete",
                                f"{msg}\n\nSaved to:\n{path}")
        else:
            self.export_status.set(f"✗  {msg}")
            messagebox.showerror("Export failed", msg)

    # ── import ────────────────────────────────────────────────────────────────

    def _pick_import_folder(self):
        folder = filedialog.askdirectory(
            title="Select your backup folder (studymate_backup_...)")
        if folder:
            self._import_folder.set(folder)
            self.import_status.set("")

    def _import(self):
        folder = self._import_folder.get()
        if folder == "No folder selected":
            messagebox.showwarning("Import", "Please select a backup folder first.")
            return
        if not messagebox.askyesno("Confirm restore",
                "This will overwrite your current sessions, goals, "
                "flashcards, subjects, and colours for this profile.\n\n"
                "Are you sure?"):
            return
        ok, msg = import_backup(folder)
        if ok:
            self.import_status.set(f"✓  {msg}")
            messagebox.showinfo("Restored", msg + "\n\nRestart the app to see your restored data.")
        else:
            self.import_status.set(f"✗  {msg}")
            messagebox.showerror("Import failed", msg)
