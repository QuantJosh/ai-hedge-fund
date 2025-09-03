import tkinter as tk
from tkinter import ttk
from typing import Optional, Dict, Any


class DataTab(ttk.Frame):
    def __init__(self, master, app_state=None):
        super().__init__(master)
        self.app_state = app_state
        self._last_seq = -1

        # Summary area
        summary = ttk.LabelFrame(self, text="分析概要")
        summary.pack(fill=tk.X, padx=8, pady=(8, 4))
        self.summary_lbl = ttk.Label(summary, text="尚无结果")
        self.summary_lbl.pack(anchor=tk.W, padx=8, pady=6)

        # Decisions table
        table_frame = ttk.LabelFrame(self, text="AI 决策（来自分析结果）")
        table_frame.pack(fill=tk.BOTH, expand=True, padx=8, pady=(0, 8))
        cols = ("ticker", "action", "quantity", "confidence")
        self.tree = ttk.Treeview(table_frame, columns=cols, show="headings", height=12)
        for c, w in zip(cols, (120, 120, 100, 120)):
            self.tree.heading(c, text=c)
            self.tree.column(c, width=w, anchor=tk.CENTER)
        self.tree.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)

        self.after(800, self._poll_state)

    def _poll_state(self):
        try:
            seq = getattr(self.app_state, "state_seq", 0)
            if seq != self._last_seq:
                self._last_seq = seq
                self._render()
        finally:
            self.after(800, self._poll_state)

    def _render(self):
        result: Optional[Dict[str, Any]] = getattr(self.app_state, "last_result", None)
        cfg = getattr(self.app_state, "config", {}) or {}
        if not result:
            self.summary_lbl.config(text="尚无结果")
            for item in self.tree.get_children():
                self.tree.delete(item)
            return

        tickers = cfg.get("tickers", [])
        period = f"{cfg.get('start_date') or '-'} 至 {cfg.get('end_date') or '-'}"
        self.summary_lbl.config(text=f"标的: {', '.join(tickers)} | 时段: {period}")

        # Populate decisions
        for item in self.tree.get_children():
            self.tree.delete(item)
        decisions = result.get("decisions", {}) or {}
        for tkr, d in decisions.items():
            action = d.get("action", "hold")
            qty = d.get("quantity", 0)
            conf = d.get("confidence", 0)
            self.tree.insert("", tk.END, values=(tkr, action, qty, f"{conf:.1f}%"))

