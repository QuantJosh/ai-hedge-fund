import tkinter as tk
from tkinter import ttk
import logging

try:
    import mplfinance as mpf
    _HAS_MPLFINANCE = True
except Exception:
    _HAS_MPLFINANCE = False

try:
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
    import matplotlib.dates as mdates
    _HAS_MPL = True
except Exception:
    _HAS_MPL = False

from .services import get_candles, get_orders_for_ticker


class MarketsTab(ttk.Frame):
    """Top-level Markets tab with English UI and interactive chart area."""

    def __init__(self, master, app_state):
        super().__init__(master)
        self.app_state = app_state
        self.logger = logging.getLogger(__name__)

        # Left panel: symbols list
        left = ttk.Frame(self, width=220)
        left.pack(side=tk.LEFT, fill=tk.Y, padx=8, pady=8)
        ttk.Label(left, text="Symbols").pack(anchor=tk.W)
        self.symbol_list = tk.Listbox(left, exportselection=False)
        self.symbol_list.pack(fill=tk.Y, expand=True)
        self.symbol_list.bind("<<ListboxSelect>>", self._on_select_symbol)

        # populate from config
        try:
            for t in (self.app_state.config.get("tickers") or []):
                self.symbol_list.insert(tk.END, t)
        except Exception:
            pass

        bottom = ttk.Frame(left)
        bottom.pack(fill=tk.X, pady=(8, 0))
        ttk.Button(bottom, text="Refresh", command=self._refresh_current).pack(side=tk.LEFT)

        # Right panel: chart
        right = ttk.Frame(self)
        right.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 8), pady=8)
        self.notice = ttk.Label(right, foreground="#9a6700")
        self.notice.pack(anchor=tk.W)
        # containers
        self.chart_container = right
        self.toolbar_widget = None
        self.canvas = None
        self.fig = None
        self.ax = None
        self._hover_cid = None
        self._hover_annot = None
        self._last_df = None

        if _HAS_MPL:
            self._create_canvas(plt.Figure(figsize=(8, 5), dpi=100))
            self.notice.config(text="")
        else:
            self.notice.config(text="Matplotlib not installed. Please install matplotlib.")

    def _on_select_symbol(self, _evt=None):
        sel = self.symbol_list.curselection()
        if not sel:
            return
        symbol = self.symbol_list.get(sel[0])
        self._plot_symbol(symbol)

    def _refresh_current(self):
        sel = self.symbol_list.curselection()
        if not sel:
            return
        symbol = self.symbol_list.get(sel[0])
        self._plot_symbol(symbol)

    def _plot_symbol(self, symbol: str):
        candles = get_candles(self.app_state, symbol, bars=180)
        # Convert to DataFrame indexed by datetime if mplfinance available, else draw manually
        if _HAS_MPLFINANCE and _HAS_MPL and candles:
            import pandas as pd
            try:
                df = pd.DataFrame(candles)
                # Normalize time column
                from datetime import datetime
                def _parse(s):
                    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y/%m/%d %H:%M:%S", "%Y-%m-%d"):
                        try:
                            return datetime.strptime(str(s), fmt)
                        except Exception:
                            pass
                    try:
                        return datetime.fromisoformat(str(s))
                    except Exception:
                        return datetime.now()
                df["Date"] = df["time"].apply(_parse)
                df.set_index("Date", inplace=True)
                df = df[["open", "high", "low", "close"]]
                df.columns = ["Open", "High", "Low", "Close"]

                apds = []
                # Overlay orders
                orders = get_orders_for_ticker(self.app_state, symbol) if self.app_state else []
                if orders:
                    import pandas as pd
                    buy_pts, sell_pts = [], []
                    for od in orders:
                        ts = od.get("updated_time") or od.get("create_time")
                        px = od.get("dealt_avg_price") or od.get("price")
                        if not ts or px is None:
                            continue
                        ts_parsed = df.index.asof(_parse(ts)) if hasattr(df.index, 'asof') else None
                        if ts_parsed is None:
                            continue
                        if str(od.get("trd_side", "")).lower().startswith("buy"):
                            buy_pts.append((ts_parsed, float(px)))
                        elif str(od.get("trd_side", "")).lower().startswith("sell"):
                            sell_pts.append((ts_parsed, float(px)))
                    if buy_pts:
                        b_index = [p[0] for p in buy_pts]; b_val = [p[1] for p in buy_pts]
                        b_series = pd.Series(b_val, index=b_index)
                        apds.append(mpf.make_addplot(b_series, type='scatter', markersize=60, marker='^', color='#16a34a', panel=0, secondary_y=False))
                    if sell_pts:
                        s_index = [p[0] for p in sell_pts]; s_val = [p[1] for p in sell_pts]
                        s_series = pd.Series(s_val, index=s_index)
                        apds.append(mpf.make_addplot(s_series, type='scatter', markersize=60, marker='v', color='#dc2626', panel=0, secondary_y=False))
                # Use returnfig to let mplfinance manage figure creation (fix suptitle issue)
                fig, _axlist = mpf.plot(df, type='candle', style='yahoo', addplot=apds, title=f"{symbol}", returnfig=True)
                self._create_canvas(fig)
                # enable hover on first axes
                ax = _axlist[0] if _axlist else fig.axes[0]
                self._enable_hover(ax, df)
                return
            except Exception:
                logging.getLogger(__name__).exception("mplfinance plotting failed, fallback to matplotlib.")

        if _HAS_MPL:
            # Fallback manual drawing
            if self.ax is None or self.fig is None:
                self._create_canvas(plt.Figure(figsize=(8, 5), dpi=100))
            self.ax.clear()
            if not candles:
                self.ax.set_title(f"{symbol} - no data")
                self.canvas.draw();
                return
            xs = []
            opens, highs, lows, closes = [], [], [], []
            from datetime import datetime
            def _parse_dt(s):
                for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y/%m/%d %H:%M:%S", "%Y-%m-%d"):
                    try:
                        return datetime.strptime(str(s), fmt)
                    except Exception:
                        continue
                try:
                    return datetime.fromisoformat(str(s))
                except Exception:
                    return datetime.now()
            for c in candles:
                xs.append(mdates.date2num(_parse_dt(c.get('time'))))
                opens.append(c.get('open', 0.0))
                highs.append(c.get('high', 0.0))
                lows.append(c.get('low', 0.0))
                closes.append(c.get('close', 0.0))
            for i, x in enumerate(xs):
                o, h, l, cl = opens[i], highs[i], lows[i], closes[i]
                color = '#16a34a' if cl >= o else '#dc2626'
                self.ax.plot([x, x], [l, h], color=color, linewidth=1)
                self.ax.add_patch(plt.Rectangle((x - 0.2, min(o, cl)), 0.4, abs(cl - o) or 0.01, color=color, alpha=0.6))
            self.ax.xaxis_date(); self.ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
            self.ax.set_title(f"{symbol} OHLC")
            # Orders overlay
            orders = get_orders_for_ticker(self.app_state, symbol) if self.app_state else []
            if orders:
                buy_x, buy_y, sell_x, sell_y = [], [], [], []
                for od in orders:
                    ts = od.get('updated_time') or od.get('create_time')
                    px = od.get('dealt_avg_price') or od.get('price') or None
                    if not ts or px is None:
                        continue
                    x = mdates.date2num(_parse_dt(ts))
                    if str(od.get('trd_side', '')).lower().startswith('buy'):
                        buy_x.append(x); buy_y.append(float(px))
                    elif str(od.get('trd_side', '')).lower().startswith('sell'):
                        sell_x.append(x); sell_y.append(float(px))
                if buy_x:
                    self.ax.scatter(buy_x, buy_y, marker='^', color='#16a34a', s=50, label='BUY')
                if sell_x:
                    self.ax.scatter(sell_x, sell_y, marker='v', color='#dc2626', s=50, label='SELL')
                if buy_x or sell_x:
                    self.ax.legend(loc='best')
            self.canvas.draw()
        else:
            self.notice.config(text="Matplotlib not installed. Please install matplotlib.")

    # helpers
    def _create_canvas(self, fig):
        # destroy old widgets
        if self.canvas is not None:
            try:
                self.canvas.get_tk_widget().destroy()
            except Exception:
                pass
        if self.toolbar_widget is not None:
            try:
                self.toolbar_widget.destroy()
            except Exception:
                pass
        self.fig = fig
        # attach canvas
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.chart_container)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        # toolbar for pan/zoom
        try:
            toolbar = NavigationToolbar2Tk(self.canvas, self.chart_container)
            toolbar.update()
            toolbar.pack(side=tk.BOTTOM, fill=tk.X)
            self.toolbar_widget = toolbar
        except Exception:
            self.toolbar_widget = None
        # disconnect previous hover
        if self._hover_cid is not None:
            try:
                self.fig.canvas.mpl_disconnect(self._hover_cid)
            except Exception:
                pass
            self._hover_cid = None
        self._hover_annot = None
        self._last_df = None

    def _enable_hover(self, ax, df):
        """Show OHLC under cursor."""
        import pandas as pd
        self._last_df = df
        if self._hover_annot is None:
            self._hover_annot = ax.annotate("", xy=(0,0), xytext=(15,15), textcoords="offset points",
                                            bbox=dict(boxstyle="round", fc="w", ec="#666"),
                                            arrowprops=dict(arrowstyle="->"))
            self._hover_annot.set_visible(False)

        def _on_move(event):
            if not event.inaxes:
                if self._hover_annot.get_visible():
                    self._hover_annot.set_visible(False)
                    self.canvas.draw_idle()
                return
            try:
                x = pd.to_datetime(mdates.num2date(event.xdata))
                idx = df.index.get_indexer([x], method='nearest')[0]
                row = df.iloc[idx]
                txt = f"{df.index[idx].strftime('%Y-%m-%d %H:%M')}\nO:{row['Open']:.2f} H:{row['High']:.2f} L:{row['Low']:.2f} C:{row['Close']:.2f}"
                self._hover_annot.xy = (event.xdata, event.ydata)
                self._hover_annot.set_text(txt)
                self._hover_annot.set_visible(True)
                self.canvas.draw_idle()
            except Exception:
                pass

        # connect
        try:
            import matplotlib.dates as mdates
            if self._hover_cid is not None:
                self.fig.canvas.mpl_disconnect(self._hover_cid)
            self._hover_cid = self.fig.canvas.mpl_connect('motion_notify_event', _on_move)
        except Exception:
            self._hover_cid = None
