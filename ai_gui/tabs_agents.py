import tkinter as tk
from tkinter import ttk
from typing import Optional, Dict, Any


class AgentsTab(ttk.Frame):
    def __init__(self, master, app_state=None):
        super().__init__(master)
        self.app_state = app_state
        self._last_seq = -1

        # Analyst signals table
        frame = ttk.LabelFrame(self, text="分析师信号")
        frame.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)
        cols = ("analyst", "ticker", "action", "confidence")
        self.tree = ttk.Treeview(frame, columns=cols, show="headings", height=16)
        for c, w in zip(cols, (200, 120, 120, 120)):
            self.tree.heading(c, text=c)
            self.tree.column(c, width=w, anchor=tk.CENTER)
        self.tree.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)

        self.after(800, self._poll)

    def _poll(self):
        try:
            seq = getattr(self.app_state, "state_seq", 0)
            if seq != self._last_seq:
                self._last_seq = seq
                self._render()
        finally:
            self.after(800, self._poll)

    def _render(self):
        result: Optional[Dict[str, Any]] = getattr(self.app_state, "last_result", None)
        for item in self.tree.get_children():
            self.tree.delete(item)
        if not result:
            return
        analyst_signals: Dict[str, Any] = result.get("analyst_signals", {}) or {}
        # Expect structure: {analyst: {ticker: {action, confidence, ...}}}
        for analyst, ticker_map in analyst_signals.items():
            if not isinstance(ticker_map, dict):
                continue
            for tkr, sig in ticker_map.items():
                # Some agents output key 'signal' instead of 'action'
                sdict = sig or {}
                action = sdict.get("action") or sdict.get("signal", "-")
                conf = (sig or {}).get("confidence", 0)
                self.tree.insert("", tk.END, values=(analyst, tkr, action, f"{conf:.1f}%"))
