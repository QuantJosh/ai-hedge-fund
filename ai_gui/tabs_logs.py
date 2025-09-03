import logging
import queue
import tkinter as tk
from tkinter import ttk
from tkinter.scrolledtext import ScrolledText
from typing import Optional

try:
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    import matplotlib.pyplot as plt
    _HAS_MPL = True
except Exception:
    _HAS_MPL = False

from .services import get_candles, get_orders_for_ticker


class LogsTab(ttk.Frame):
    def __init__(self, master, log_queue: queue.Queue, poll_ms: int = 300, app_state=None):
        super().__init__(master)
        self.log_queue = log_queue
        self.poll_ms = poll_ms
        self.app_state = app_state

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

        # Notebook inside: Logs and Markets
        self.nb = ttk.Notebook(self)
        self.nb.pack(fill=tk.BOTH, expand=True)

        # Tab 1: Log window
        logs_frame = ttk.Frame(self.nb)
        self.nb.add(logs_frame, text="日志")
        self.text = ScrolledText(logs_frame, height=20, wrap=tk.WORD, state=tk.DISABLED)
        self.text.pack(fill=tk.BOTH, expand=True, padx=8, pady=(0, 8))

        # Tab 2: Markets (candlestick + tickers)
        markets = ttk.Frame(self.nb)
        self.nb.add(markets, text="行情")
        markets.pack(fill=tk.BOTH, expand=True)

        left = ttk.Frame(markets, width=200)
        left.pack(side=tk.LEFT, fill=tk.Y, padx=6, pady=6)
        ttk.Label(left, text="股票列表").pack(anchor=tk.W)
        self.ticker_list = tk.Listbox(left, exportselection=False)
        self.ticker_list.pack(fill=tk.Y, expand=True)
        self.ticker_list.bind("<<ListboxSelect>>", self._on_select_ticker)

        # Populate tickers from config
        try:
            for t in (self.app_state.config.get("tickers") or []):
                self.ticker_list.insert(tk.END, t)
        except Exception:
            pass

        right = ttk.Frame(markets)
        right.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 6), pady=6)
        self.chart_notice = ttk.Label(right, foreground="#9a6700")
        self.chart_notice.pack(anchor=tk.W)
        self.canvas = None
        self.fig = None
        self.ax = None
        if _HAS_MPL:
            self.fig, self.ax = plt.subplots(figsize=(7, 4), dpi=100)
            self.canvas = FigureCanvasTkAgg(self.fig, master=right)
            self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
            self.chart_notice.config(text="")
        else:
            self.chart_notice.config(text="未安装 matplotlib，无法显示K线图。请安装 matplotlib 再重试。")

        # Tag styles (colors kept simple for cross-platform)
        self.text.tag_config("INFO", foreground="#1f6feb")
        self.text.tag_config("WARNING", foreground="#9a6700")
        self.text.tag_config("ERROR", foreground="#d1242f")
        self.text.tag_config("DEBUG", foreground="#57606a")

        self._after_id = self.after(self.poll_ms, self._poll_logs)
        # Cancel timers on destroy to avoid callbacks after close
        self.bind("<Destroy>", self._on_destroy)

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
        # If widget still exists, reschedule
        if self.winfo_exists():
            self._after_id = self.after(self.poll_ms, self._poll_logs)

    def clear(self) -> None:
        self.text.configure(state=tk.NORMAL)
        self.text.delete("1.0", tk.END)
        self.text.configure(state=tk.DISABLED)

    def _on_destroy(self, _evt=None):
        try:
            if getattr(self, "_after_id", None):
                self.after_cancel(self._after_id)
                self._after_id = None
        except Exception:
            pass

    # Markets helpers
    def _on_select_ticker(self, _evt=None):
        if not _HAS_MPL:
            return
        try:
            selection = self.ticker_list.curselection()
            if not selection:
                return
            tkr = self.ticker_list.get(selection[0])
            self._plot_ticker(tkr)
        except Exception:
            logging.getLogger(__name__).exception("选择股票失败")

    def _plot_ticker(self, ticker: str):
        if not (_HAS_MPL and self.ax and self.fig):
            return
        # fetch candles
        candles = get_candles(self.app_state, ticker, bars=120) if self.app_state else []
        self.ax.clear()
        if not candles:
            self.ax.set_title(f"{ticker} - 无数据")
            if self.canvas:
                self.canvas.draw()
            return
        # Draw simple OHLC as line segments and body rectangles
        import matplotlib.dates as mdates
        from datetime import datetime
        xs = []
        opens, highs, lows, closes = [], [], [], []
        for c in candles:
            xs.append(mdates.date2num(self._parse_dt(c.get('time'))))
            opens.append(c.get('open', 0.0))
            highs.append(c.get('high', 0.0))
            lows.append(c.get('low', 0.0))
            closes.append(c.get('close', 0.0))
        # Plot candles
        for i, x in enumerate(xs):
            o, h, l, cl = opens[i], highs[i], lows[i], closes[i]
            color = '#16a34a' if cl >= o else '#dc2626'
            # Wick
            self.ax.plot([x, x], [l, h], color=color, linewidth=1)
            # Body
            self.ax.add_patch(
                plt.Rectangle((x - 0.2, min(o, cl)), 0.4, abs(cl - o) or 0.01, color=color, alpha=0.6)
            )
        self.ax.xaxis_date()
        self.ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d %H:%M'))
        self.ax.set_title(f"{ticker} K线")

        # Overlay orders as triangles
        orders = get_orders_for_ticker(self.app_state, ticker) if self.app_state else []
        if orders:
            buy_x, buy_y, sell_x, sell_y = [], [], [], []
            for od in orders:
                ts = od.get('updated_time') or od.get('create_time')
                px = od.get('dealt_avg_price') or od.get('price') or None
                if not ts or px is None:
                    continue
                x = mdates.date2num(self._parse_dt(ts))
                if str(od.get('trd_side', '')).lower().startswith('buy'):
                    buy_x.append(x); buy_y.append(float(px))
                elif str(od.get('trd_side', '')).lower().startswith('sell'):
                    sell_x.append(x); sell_y.append(float(px))
            if buy_x:
                self.ax.scatter(buy_x, buy_y, marker='^', color='#16a34a', s=50, label='买入')
            if sell_x:
                self.ax.scatter(sell_x, sell_y, marker='v', color='#dc2626', s=50, label='卖出')
            if buy_x or sell_x:
                self.ax.legend(loc='best')

        if self.canvas:
            self.canvas.draw()

    @staticmethod
    def _parse_dt(s):
        from datetime import datetime
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y/%m/%d %H:%M:%S", "%Y-%m-%d"):
            try:
                return datetime.strptime(str(s), fmt)
            except Exception:
                continue
        try:
            # last resort
            return datetime.fromisoformat(str(s))
        except Exception:
            return datetime.now()
