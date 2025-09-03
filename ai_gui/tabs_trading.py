import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from typing import Optional, Dict, Any

from .services import convert_decisions_for_moomoo, simulate_execution, execute_on_moomoo


class TradingTab(ttk.Frame):
    def __init__(self, master, app_state=None):
        super().__init__(master)
        self.app_state = app_state
        self._last_seq = -1

        # Controls
        controls = ttk.Frame(self)
        controls.pack(fill=tk.X, padx=8, pady=6)
        ttk.Button(controls, text="转换为Moomoo格式", command=self._convert).pack(side=tk.LEFT)
        ttk.Button(controls, text="模拟执行(安全)", command=self._simulate).pack(side=tk.LEFT, padx=(8, 0))
        ttk.Button(controls, text="在Moomoo执行(纸质)", command=self._execute).pack(side=tk.LEFT, padx=(8, 0))

        # Decisions preview
        frame = ttk.LabelFrame(self, text="交易决策预览")
        frame.pack(fill=tk.BOTH, expand=True, padx=8, pady=(0, 8))
        cols = ("ticker", "action", "quantity", "confidence", "reasoning")
        self.tree = ttk.Treeview(frame, columns=cols, show="headings", height=14)
        widths = (100, 100, 90, 110, 500)
        for c, w in zip(cols, widths):
            self.tree.heading(c, text=c)
            self.tree.column(c, width=w, anchor=tk.W if c == "reasoning" else tk.CENTER)
        self.tree.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)

        # Execution status
        self.exec_lbl = ttk.Label(self, text="未执行")
        self.exec_lbl.pack(fill=tk.X, padx=8, pady=(0, 8))

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
        # Refresh decisions preview
        for i in self.tree.get_children():
            self.tree.delete(i)

        decisions = None
        if self.app_state.moomoo_decisions:
            decisions = self.app_state.moomoo_decisions
        else:
            result: Optional[Dict[str, Any]] = self.app_state.last_result
            if result:
                decisions = result.get("decisions", {})

        if decisions:
            for tkr, d in decisions.items():
                self.tree.insert(
                    "", tk.END,
                    values=(
                        tkr,
                        d.get("action", "-"),
                        d.get("quantity", 0),
                        f"{d.get('confidence', 0):.1f}%",
                        (d.get("reasoning") or "")[:300],
                    ),
                )

        # Execution label
        if self.app_state.execution_results:
            ok = sum(1 for r in self.app_state.execution_results.values() if r.get("success"))
            total = len(self.app_state.execution_results)
            self.exec_lbl.config(text=f"模拟执行结果：{ok}/{total} 成功")
        else:
            self.exec_lbl.config(text="未执行")

    def _convert(self):
        out = convert_decisions_for_moomoo(self.app_state)
        if out:
            messagebox.showinfo("完成", "已转换为 Moomoo 决策格式（仍处于安全模式，无真实下单）。")
        self._render()

    def _simulate(self):
        if not self.app_state.moomoo_decisions and not (self.app_state.last_result and self.app_state.last_result.get("decisions")):
            messagebox.showwarning("提示", "没有可执行的决策，请先完成分析与转换。")
            return
        if not self.app_state.moomoo_decisions:
            # Try auto-convert
            self._convert()
        out = simulate_execution(self.app_state)
        if out:
            messagebox.showinfo("完成", "已生成模拟执行结果（未连接 Moomoo）。")
        self._render()

    def _execute(self):
        if not (self.app_state.last_result and self.app_state.last_result.get("decisions")):
            messagebox.showwarning("提示", "没有可执行的决策，请先完成分析。")
            return
        # Run background execution (paper)
        execute_on_moomoo(self.app_state)
        messagebox.showinfo("执行中", "已开始在 Moomoo（纸质）执行，完成后请查看日志与结果。")
