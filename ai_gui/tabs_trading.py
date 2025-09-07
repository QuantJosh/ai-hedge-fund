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
        ttk.Button(controls, text="模拟执行(安全)", command=self._simulate).pack(side=tk.LEFT)
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

        # Execution details
        detail_frame = ttk.LabelFrame(self, text="执行结果明细")
        detail_frame.pack(fill=tk.BOTH, expand=True, padx=8, pady=(0, 8))
        self.exec_text = tk.Text(detail_frame, height=10, wrap=tk.NONE)
        self.exec_text.configure(state=tk.DISABLED)
        self.exec_text.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)

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
            # Update details
            try:
                self.exec_text.configure(state=tk.NORMAL)
                self.exec_text.delete("1.0", tk.END)
                for tkr, r in self.app_state.execution_results.items():
                    line = (
                        f"{tkr}: success={r.get('success')}, "
                        f"order_id={r.get('order_id')}, "
                        f"executed_qty={r.get('executed_quantity')}, "
                        f"price={r.get('executed_price')}, "
                        f"msg={r.get('message')}\n"
                    )
                    self.exec_text.insert(tk.END, line)
                self.exec_text.configure(state=tk.DISABLED)
            except Exception:
                try:
                    self.exec_text.configure(state=tk.DISABLED)
                except Exception:
                    pass
        else:
            self.exec_lbl.config(text="未执行")
            try:
                self.exec_text.configure(state=tk.NORMAL)
                self.exec_text.delete("1.0", tk.END)
                self.exec_text.insert(tk.END, "尚无执行结果。\n")
                self.exec_text.configure(state=tk.DISABLED)
            except Exception:
                pass

    def _simulate(self):
        if not self.app_state.moomoo_decisions and not (self.app_state.last_result and self.app_state.last_result.get("decisions")):
            messagebox.showwarning("提示", "没有可执行的决策，请先完成分析与转换。")
            return
        if not self.app_state.moomoo_decisions:
            # Auto-convert silently
            convert_decisions_for_moomoo(self.app_state)
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
