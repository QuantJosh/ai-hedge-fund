import logging
import queue
import tkinter as tk
from tkinter import ttk
from tkinter.scrolledtext import ScrolledText
from typing import Optional


class LogsTab(ttk.Frame):
    def __init__(self, master, log_queue: queue.Queue, poll_ms: int = 300):
        super().__init__(master)
        self.log_queue = log_queue
        self.poll_ms = poll_ms

        # Controls: level filter and buttons
        controls = ttk.Frame(self)
        controls.pack(fill=tk.X, padx=8, pady=6)

        ttk.Label(controls, text="过滤:").pack(side=tk.LEFT)
        self.level_var = tk.StringVar(value="ALL")
        level_combo = ttk.Combobox(controls, textvariable=self.level_var, width=10,
                                   values=["ALL", "ERROR", "WARNING", "INFO", "DEBUG"])
        level_combo.state(["readonly"])  # type: ignore
        level_combo.pack(side=tk.LEFT, padx=(6, 12))

        self.autoscroll = tk.BooleanVar(value=True)
        ttk.Checkbutton(controls, text="自动滚动", variable=self.autoscroll).pack(side=tk.LEFT)

        ttk.Button(controls, text="清空", command=self.clear).pack(side=tk.RIGHT)

        # Log window
        self.text = ScrolledText(self, height=20, wrap=tk.WORD, state=tk.DISABLED)
        self.text.pack(fill=tk.BOTH, expand=True, padx=8, pady=(0, 8))

        # Tag styles (colors kept simple for cross-platform)
        self.text.tag_config("INFO", foreground="#1f6feb")
        self.text.tag_config("WARNING", foreground="#9a6700")
        self.text.tag_config("ERROR", foreground="#d1242f")
        self.text.tag_config("DEBUG", foreground="#57606a")

        self.after(self.poll_ms, self._poll_logs)

    def _append(self, level: str, message: str) -> None:
        if self.level_var.get() != "ALL" and self.level_var.get() != level:
            return
        self.text.configure(state=tk.NORMAL)
        self.text.insert(tk.END, message + "\n", level)
        if self.autoscroll.get():
            self.text.see(tk.END)
        self.text.configure(state=tk.DISABLED)

    def _poll_logs(self) -> None:
        try:
            while True:
                level, msg = self.log_queue.get_nowait()
                self._append(level, msg)
        except queue.Empty:
            pass
        self.after(self.poll_ms, self._poll_logs)

    def clear(self) -> None:
        self.text.configure(state=tk.NORMAL)
        self.text.delete("1.0", tk.END)
        self.text.configure(state=tk.DISABLED)
