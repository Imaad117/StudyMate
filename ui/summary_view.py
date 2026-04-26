from __future__ import annotations
import tkinter as tk
from tkinter import ttk
import matplotlib
matplotlib.use("TkAgg")
import matplotlib.ticker
import matplotlib.patches as mpatches
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from data.summary_manager import get_last_7_days_summary, get_full_analytics
from ui.theme import THEME
from ui.subjects_view import get_subject_colour
from ui.scroll_helper import bind_mousewheel

GREEN_MPL = "#22c55e"
BLUE_MPL  = "#3b82f6"


class SummaryView(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=THEME.BG)
        self._build()

    def _build(self):
        t = THEME

        # ── top bar ───────────────────────────────────────────────────────────
        top = tk.Frame(self, bg=t.CARD)
        top.pack(fill="x")
        tk.Frame(self, bg=t.MAIN, height=3).pack(fill="x")
        top_inner = tk.Frame(top, bg=t.CARD, padx=20, pady=12)
        top_inner.pack(fill="x")
        tk.Label(top_inner, text="Summary",
                 bg=t.CARD, fg=t.MAIN,
                 font=("Segoe UI", 18, "bold")).pack(side="left")
        tk.Button(top_inner, text="↻  Refresh",
                  command=self.refresh,
                  bg=t.LIGHT, fg=t.DARK,
                  activebackground=t.MAIN, activeforeground="white",
                  relief="flat", cursor="hand2",
                  font=("Segoe UI", 9), padx=12, pady=5).pack(side="right")

        # ── scrollable body ───────────────────────────────────────────────────
        outer = tk.Frame(self, bg=t.BG)
        outer.pack(fill="both", expand=True)
        self._canvas = tk.Canvas(outer, bg=t.BG, highlightthickness=0)
        sb = ttk.Scrollbar(outer, orient="vertical", command=self._canvas.yview)
        self._canvas.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        self._canvas.pack(side="left", fill="both", expand=True)
        bind_mousewheel(self._canvas)

        self._body = tk.Frame(self._canvas, bg=t.BG)
        self._win  = self._canvas.create_window((0, 0), window=self._body, anchor="nw")
        self._canvas.bind("<Configure>",
                          lambda e: self._canvas.itemconfig(self._win, width=e.width))
        self._body.bind("<Configure>",
                        lambda _e: self._canvas.configure(
                            scrollregion=self._canvas.bbox("all")))

        self.refresh()

    # ── helpers ───────────────────────────────────────────────────────────────

    def _clear_body(self):
        for w in self._body.winfo_children():
            w.destroy()

    def _section(self, text: str) -> tk.Frame:
        t = THEME
        hdr = tk.Frame(self._body, bg=t.BG)
        hdr.pack(fill="x", padx=20, pady=(18, 6))
        tk.Label(hdr, text=text.upper(), bg=t.BG, fg=t.MUTED,
                 font=("Segoe UI", 8, "bold")).pack(side="left")
        tk.Frame(hdr, bg=t.BORDER, height=1).pack(side="left", fill="x",
                                                   expand=True, padx=(10, 0))
        row = tk.Frame(self._body, bg=t.BG)
        row.pack(fill="x", padx=20)
        return row

    def _stat_card(self, parent, value, label, accent=None):
        t = THEME
        accent = accent or t.MAIN
        card = tk.Frame(parent, bg=t.CARD,
                        highlightthickness=1, highlightbackground=t.BORDER)
        card.pack(side="left", fill="both", expand=True, padx=4)
        tk.Frame(card, bg=accent, height=3).pack(fill="x")
        tk.Label(card, text=value, bg=t.CARD, fg=accent,
                 font=("Segoe UI", 22, "bold")).pack(pady=(12, 2))
        tk.Label(card, text=label, bg=t.CARD, fg=t.MUTED,
                 font=("Segoe UI", 9)).pack(pady=(0, 12))
        return card

    def _insight_card(self, parent, icon, title, body_text, colour):
        t = THEME
        card = tk.Frame(parent, bg=t.CARD,
                        highlightthickness=1, highlightbackground=t.BORDER)
        card.pack(side="left", fill="both", expand=True, padx=4)
        tk.Frame(card, bg=colour, height=3).pack(fill="x")
        inner = tk.Frame(card, bg=t.CARD, padx=14, pady=10)
        inner.pack(fill="both", expand=True)
        tk.Label(inner, text=f"{icon}  {title}", bg=t.CARD, fg=colour,
                 font=("Segoe UI", 9, "bold")).pack(anchor="w")
        tk.Label(inner, text=body_text, bg=t.CARD, fg=t.FG,
                 font=("Segoe UI", 11, "bold"),
                 wraplength=180, justify="left").pack(anchor="w", pady=(4, 0))

    def _embed_chart(self, parent, fig):
        canvas = FigureCanvasTkAgg(fig, master=parent)
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=8, pady=8)
        canvas.draw()
        return canvas

    def _chart_card(self, parent, title, w_frac=0.5):
        t = THEME
        card = tk.Frame(parent, bg=t.CARD,
                        highlightthickness=1, highlightbackground=t.BORDER)
        card.pack(side="left", fill="both", expand=True, padx=4)
        tk.Label(card, text=title, bg=t.CARD, fg=t.FG,
                 font=("Segoe UI", 10, "bold")).pack(anchor="w", padx=14, pady=(12, 0))
        return card

    # ── main refresh ──────────────────────────────────────────────────────────

    def refresh(self):
        self._clear_body()
        t    = THEME
        week = get_last_7_days_summary()
        full = get_full_analytics()

        # ── 1. All-time stats row ─────────────────────────────────────────────
        row1 = self._section("All-time stats")
        h, m = divmod(full["total_minutes_all"], 60)
        time_str = f"{h}h {m}m" if h else f"{m}m"
        self._stat_card(row1, time_str,  "Total study time",  "#7c3aed")
        self._stat_card(row1, str(full["total_sessions_all"]), "Total sessions", THEME.MAIN)
        self._stat_card(row1, f"{full['current_streak']} days", "Current streak", "#f97316")
        self._stat_card(row1, f"{full['longest_streak']} days", "Longest streak", "#0891b2")
        avg = full["avg_session_length"]
        self._stat_card(row1, f"{avg}m", "Avg session length", "#db2777")

        # ── 2. This week stats ────────────────────────────────────────────────
        row2 = self._section("This week")
        h2, m2 = divmod(week["total_minutes"], 60)
        wk_str = f"{h2}h {m2}m" if h2 else f"{m2}m"
        self._stat_card(row2, wk_str, "Study time", THEME.MAIN)
        self._stat_card(row2, str(week["session_count"]), "Sessions", "#7c3aed")
        pre  = f"{week['avg_focus_pre']:.1f}"  if week["avg_focus_pre"]  is not None else "—"
        post = f"{week['avg_focus_post']:.1f}" if week["avg_focus_post"] is not None else "—"
        self._stat_card(row2, pre,  "Avg focus before", "#3b82f6")
        self._stat_card(row2, post, "Avg focus after",  GREEN_MPL)

        # ── 3. Smart insights row ─────────────────────────────────────────────
        row3 = self._section("Insights")
        if full["most_studied_subject"]:
            mins = full["minutes_by_subject_all"].get(full["most_studied_subject"], 0)
            self._insight_card(row3, "★", "Most studied",
                               f"{full['most_studied_subject']}\n{mins}m total",
                               get_subject_colour(full["most_studied_subject"]))
        if full["best_focus_day"]:
            self._insight_card(row3, "◆", "Best focus day",
                               full["best_focus_day"],
                               "#7c3aed")
        if full["focus_improvement_pct"] is not None:
            direction = "↑" if full["focus_improvement_pct"] >= 0 else "↓"
            colour    = GREEN_MPL if full["focus_improvement_pct"] >= 0 else "#ef4444"
            self._insight_card(row3, direction, "Focus shift",
                               f"{abs(full['focus_improvement_pct'])}% {'better' if full['focus_improvement_pct']>=0 else 'lower'}\nafter sessions",
                               colour)
        if full["best_subject_focus"]:
            self._insight_card(row3, "✓", "Highest focus subject",
                               full["best_subject_focus"],
                               "#0891b2")

        # ── 4. Charts row — donut + focus trend ──────────────────────────────
        # two charts side by side — donut on the left, focus line on the right
        charts_row = tk.Frame(self._body, bg=t.BG)
        charts_row.pack(fill="x", padx=20, pady=(18, 0))
        for i in range(2): charts_row.columnconfigure(i, weight=1)

        # Donut chart — subject breakdown
        donut_card = tk.Frame(charts_row, bg=t.CARD,
                              highlightthickness=1, highlightbackground=t.BORDER)
        donut_card.grid(row=0, column=0, sticky="nsew", padx=(0,6))
        tk.Label(donut_card, text="Time by subject",
                 bg=t.CARD, fg=t.FG,
                 font=("Segoe UI", 10, "bold")).pack(anchor="w", padx=14, pady=(12, 0))

        fig_d = Figure(figsize=(3.8, 2.8), dpi=96)
        fig_d.patch.set_facecolor(t.CARD)
        ax_d = fig_d.add_subplot(111)
        mbs  = full["minutes_by_subject_all"]
        if mbs:
            labels  = list(mbs.keys())
            values  = list(mbs.values())
            colours = [get_subject_colour(s) for s in labels]
            # ring chart with a hole in the middle (width=0.55)
            wedges, _ = ax_d.pie(values, colors=colours,
                                  startangle=90,
                                  wedgeprops={"width": 0.55, "edgecolor": t.CARD, "linewidth": 2})
            # centre text
            total_m = sum(values)
            h_d, m_d = divmod(int(total_m), 60)
            centre = f"{h_d}h\n{m_d}m" if h_d else f"{int(total_m)}m"
            ax_d.text(0, 0, centre, ha="center", va="center",
                      fontsize=11, fontweight="bold", color=t.FG)
            # legend
            legend_patches = [mpatches.Patch(color=c, label=f"{l}  {v}m")
                               for c, l, v in zip(colours, labels, [int(v) for v in values])]
            ax_d.legend(handles=legend_patches, loc="lower center",
                        bbox_to_anchor=(0.5, -0.18), ncol=2,
                        fontsize=7, framealpha=0,
                        labelcolor=t.FG)
        else:
            ax_d.text(0.5, 0.5, "No data yet", ha="center", va="center",
                      fontsize=10, color=t.MUTED)
        ax_d.set_facecolor(t.CARD)
        ax_d.axis("equal")
        fig_d.set_tight_layout(False)
        self._embed_chart(donut_card, fig_d)

        # Focus trend line chart
        # shows pre vs post focus rating for each session over the last 30 days
        trend_card = tk.Frame(charts_row, bg=t.CARD,
                              highlightthickness=1, highlightbackground=t.BORDER)
        trend_card.grid(row=0, column=1, sticky="nsew", padx=(6,0))
        tk.Label(trend_card, text="Focus before vs after",
                 bg=t.CARD, fg=t.FG,
                 font=("Segoe UI", 10, "bold")).pack(anchor="w", padx=14, pady=(12, 0))

        fig_t = Figure(figsize=(3.8, 2.8), dpi=96)
        fig_t.patch.set_facecolor(t.CARD)
        ax_t  = fig_t.add_subplot(111)
        ax_t.set_facecolor(t.CARD)
        trend = full["focus_trend_30"]
        if len(trend) >= 2:
            xs    = list(range(len(trend)))
            pres  = [r["pre"]  for r in trend]
            posts = [r["post"] for r in trend]
            ax_t.fill_between(xs, pres, posts,
                              alpha=0.12, color=GREEN_MPL)
            ax_t.plot(xs, pres,  color=BLUE_MPL,  marker="o", markersize=4,
                      linewidth=2, label="Before", zorder=3)
            ax_t.plot(xs, posts, color=GREEN_MPL, marker="o", markersize=4,
                      linewidth=2, label="After",  zorder=3)
            # show only a few x labels to avoid crowding
            step = max(1, len(xs) // 5)
            ax_t.set_xticks(xs[::step])
            ax_t.set_xticklabels([trend[i]["date"] for i in xs[::step]],
                                  rotation=25, fontsize=7)
            ax_t.set_yticks([1, 2, 3, 4, 5])
            ax_t.set_ylim(0.5, 5.5)
            ax_t.tick_params(axis="y", labelsize=8, colors=t.MUTED)
            ax_t.legend(fontsize=8, framealpha=0, labelcolor=t.FG)
        else:
            ax_t.text(0.5, 0.5,
                      "Complete 2+ sessions\nto see your focus trend",
                      ha="center", va="center",
                      fontsize=9, color=t.MUTED, transform=ax_t.transAxes)
            ax_t.set_xticks([]); ax_t.set_yticks([])
        for spine in ax_t.spines.values():
            spine.set_edgecolor(t.BORDER)
        fig_t.set_tight_layout(False)
        self._embed_chart(trend_card, fig_t)

        # ── 5. Activity heatmap row ───────────────────────────────────────────
        heat_frame = tk.Frame(self._body, bg=t.BG)
        heat_frame.pack(fill="x", padx=20, pady=(12, 0))

        heat_card = tk.Frame(heat_frame, bg=t.CARD,
                             highlightthickness=1, highlightbackground=t.BORDER)
        heat_card.pack(fill="x")
        tk.Label(heat_card, text="Study frequency by day of week",
                 bg=t.CARD, fg=t.FG,
                 font=("Segoe UI", 10, "bold")).pack(anchor="w", padx=14, pady=(12, 4))

        bar_area = tk.Frame(heat_card, bg=t.CARD, padx=14, pady=10)
        bar_area.pack(fill="x")
        weekday_data = full["sessions_by_weekday"]
        max_count = max(weekday_data.values()) if any(weekday_data.values()) else 1
        for day, count in weekday_data.items():
            row = tk.Frame(bar_area, bg=t.CARD)
            row.pack(fill="x", pady=2)
            tk.Label(row, text=day, bg=t.CARD, fg=t.MUTED,
                     font=("Segoe UI", 9), width=5, anchor="w").pack(side="left")
            bar_bg = tk.Frame(row, bg=t.LIGHT, height=16)
            bar_bg.pack(side="left", fill="x", expand=True, padx=(6, 10))
            bar_bg.update_idletasks()
            pct = count / max_count if max_count else 0
            if count > 0:
                tk.Frame(bar_bg, bg=THEME.MAIN, height=16).place(
                    x=0, y=0, relwidth=pct, relheight=1)
            tk.Label(row, text=str(count),
                     bg=t.CARD, fg=t.MUTED,
                     font=("Segoe UI", 9), width=3).pack(side="left")

        # ── 6. Subject bar chart ──────────────────────────────────────────────
        subj_frame = tk.Frame(self._body, bg=t.BG)
        subj_frame.pack(fill="x", padx=20, pady=(12, 20))
        subj_card = tk.Frame(subj_frame, bg=t.CARD,
                             highlightthickness=1, highlightbackground=t.BORDER)
        subj_card.pack(fill="x")
        tk.Label(subj_card, text="Minutes per subject (this week)",
                 bg=t.CARD, fg=t.FG,
                 font=("Segoe UI", 10, "bold")).pack(anchor="w", padx=14, pady=(12, 0))

        fig_b = Figure(figsize=(7, 2.2), dpi=96)
        fig_b.patch.set_facecolor(t.CARD)
        ax_b  = fig_b.add_subplot(111)
        ax_b.set_facecolor(t.CARD)
        mbs_week = week["minutes_by_subject"]
        if mbs_week:
            subjects = list(mbs_week.keys())
            minutes  = [int(v) for v in mbs_week.values()]
            colours  = [get_subject_colour(s) for s in subjects]
            bars = ax_b.bar(subjects, minutes, color=colours, edgecolor="none", width=0.5)
            for bar, val in zip(bars, minutes):
                ax_b.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.4,
                          str(val), ha="center", va="bottom", fontsize=8, color=t.FG)
            ax_b.set_ylabel("Minutes", fontsize=8, color=t.MUTED)
            ax_b.tick_params(axis="x", labelsize=9, colors=t.FG)
            ax_b.tick_params(axis="y", labelsize=8, colors=t.MUTED)
            ax_b.yaxis.set_major_formatter(
                matplotlib.ticker.FuncFormatter(lambda x, _: str(int(x))))
        else:
            ax_b.text(0.5, 0.5, "No sessions this week",
                      ha="center", va="center",
                      fontsize=9, color=t.MUTED, transform=ax_b.transAxes)
            ax_b.set_xticks([]); ax_b.set_yticks([])
        for spine in ax_b.spines.values():
            spine.set_edgecolor(t.BORDER)
        fig_b.set_tight_layout(False)
        self._embed_chart(subj_card, fig_b)
