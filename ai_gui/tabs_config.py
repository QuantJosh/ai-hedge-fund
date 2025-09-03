import logging
import tkinter as tk
from tkinter import filedialog, ttk, messagebox
from typing import List

from .config_manager import load_config, save_config
from .services import start_background_analysis, connect_moomoo, sync_portfolio, sync_orders, ensure_moomoo_connected


class ConfigTab(ttk.Frame):
    def __init__(self, master, app_state):
        super().__init__(master)
        self.app_state = app_state
        self.logger = logging.getLogger(__name__)

        # Left: basic config
        left = ttk.LabelFrame(self, text="基础配置")
        left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=8, pady=8)

        # Tickers
        ttk.Label(left, text="股票代码(逗号分隔)").pack(anchor=tk.W, padx=6, pady=(6, 2))
        self.tickers_var = tk.StringVar(value=",")
        self.tickers_entry = ttk.Entry(left, textvariable=self.tickers_var)
        self.tickers_entry.pack(fill=tk.X, padx=6, pady=(0, 8))

        # Analysts (free text for Phase 1; later we can fetch from ANALYST_ORDER)
        ttk.Label(left, text="分析师ID(逗号分隔)").pack(anchor=tk.W, padx=6, pady=(6, 2))
        self.analysts_var = tk.StringVar(value=",")
        self.analysts_entry = ttk.Entry(left, textvariable=self.analysts_var)
        self.analysts_entry.pack(fill=tk.X, padx=6, pady=(0, 8))

        # Toggles
        self.paper_var = tk.BooleanVar(value=True)
        self.auto_exec_var = tk.BooleanVar(value=False)
        self.reason_var = tk.BooleanVar(value=True)
        toggles = ttk.Frame(left)
        toggles.pack(fill=tk.X, padx=6, pady=(4, 8))
        ttk.Checkbutton(toggles, text="纸质交易(强制开启)", variable=self.paper_var, state=tk.DISABLED).pack(anchor=tk.W)
        ttk.Checkbutton(toggles, text="自动执行交易", variable=self.auto_exec_var).pack(anchor=tk.W)
        ttk.Checkbutton(toggles, text="显示推理", variable=self.reason_var).pack(anchor=tk.W)

        # Right: account panel placeholder (Phase 2 will populate)
        right = ttk.LabelFrame(self, text="Moomoo账户状态")
        right.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 8), pady=8)
        self.account_status = ttk.Label(right, text="未连接")
        self.account_status.pack(anchor=tk.W, padx=6, pady=6)
        # Cash/Assets summary
        summary = ttk.Frame(right)
        summary.pack(fill=tk.X, padx=6, pady=(0, 6))
        self.cash_var = tk.StringVar(value="现金: -")
        self.assets_var = tk.StringVar(value="总资产: -")
        ttk.Label(summary, textvariable=self.cash_var).pack(anchor=tk.W)
        ttk.Label(summary, textvariable=self.assets_var).pack(anchor=tk.W)
        btns = ttk.Frame(right)
        btns.pack(fill=tk.X, padx=6, pady=(0, 6))
        # Left cluster: account ops
        left_ops = ttk.Frame(btns)
        left_ops.pack(side=tk.LEFT)
        ttk.Button(left_ops, text="连接/刷新账户", command=self._refresh_account).pack(side=tk.LEFT)
        ttk.Button(left_ops, text="同步持仓", command=self._sync_positions).pack(side=tk.LEFT, padx=(6, 0))
        ttk.Button(left_ops, text="同步订单", command=self._sync_orders).pack(side=tk.LEFT, padx=(6, 0))
        # Right cluster: config ops (moved from bottom)
        right_ops = ttk.Frame(btns)
        right_ops.pack(side=tk.RIGHT)
        ttk.Button(right_ops, text="保存配置...", command=self._save_as).pack(side=tk.LEFT, padx=(0, 6))
        ttk.Button(right_ops, text="加载配置...", command=self._load_from).pack(side=tk.LEFT, padx=(0, 6))
        self.start_btn = ttk.Button(right_ops, text="开始处理", command=self._start_processing)
        self.start_btn.pack(side=tk.LEFT)

        # Positions table
        positions_frame = ttk.LabelFrame(right, text="持仓")
        positions_frame.pack(fill=tk.BOTH, expand=True, padx=6, pady=(6, 6))
        cols = ("ticker", "long", "short", "market_value", "unrealized_pnl")
        self.pos_tree = ttk.Treeview(positions_frame, columns=cols, show="headings", height=10)
        headers = {
            "ticker": "代码",
            "long": "多头",
            "short": "空头",
            "market_value": "市值",
            "unrealized_pnl": "浮动盈亏",
        }
        widths = {"ticker": 100, "long": 80, "short": 80, "market_value": 120, "unrealized_pnl": 120}
        for c in cols:
            self.pos_tree.heading(c, text=headers[c])
            self.pos_tree.column(c, width=widths[c], anchor=tk.CENTER)
        self.pos_tree.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)

        # Orders table
        orders_frame = ttk.LabelFrame(right, text="订单记录（当日/历史）")
        orders_frame.pack(fill=tk.BOTH, expand=True, padx=6, pady=(0, 6))
        order_cols = ("time", "ticker", "side", "status", "qty", "dealt_qty", "price", "avg_fill", "order_id")
        self.orders_tree = ttk.Treeview(orders_frame, columns=order_cols, show="headings", height=10)
        order_headers = {
            "time": "时间",
            "ticker": "代码",
            "side": "方向",
            "status": "状态",
            "qty": "数量",
            "dealt_qty": "成交量",
            "price": "委托价",
            "avg_fill": "成交均价",
            "order_id": "订单ID",
        }
        order_widths = {"time": 140, "ticker": 80, "side": 70, "status": 110, "qty": 70, "dealt_qty": 80, "price": 90, "avg_fill": 90, "order_id": 160}
        for c in order_cols:
            self.orders_tree.heading(c, text=order_headers[c])
            self.orders_tree.column(c, width=order_widths[c], anchor=tk.CENTER)
        self.orders_tree.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)

        self._load_into_ui(self.app_state.config)
        self.after(800, self._poll_status)

    def _load_into_ui(self, cfg):
        self.tickers_var.set(",".join(cfg.get("tickers", [])))
        self.analysts_var.set(",".join(cfg.get("analysts", [])))
        self.paper_var.set(bool(cfg.get("paper_trading_only", True)))
        self.auto_exec_var.set(bool(cfg.get("auto_execute", False)))
        self.reason_var.set(bool(cfg.get("show_reasoning", True)))

    def _collect_from_ui(self):
        cfg = self.app_state.config.copy()
        cfg["tickers"] = [x.strip().upper() for x in self.tickers_var.get().split(",") if x.strip()]
        cfg["analysts"] = [x.strip() for x in self.analysts_var.get().split(",") if x.strip()]
        cfg["paper_trading_only"] = True
        cfg["auto_execute"] = bool(self.auto_exec_var.get())
        cfg["show_reasoning"] = bool(self.reason_var.get())
        self.app_state.config = cfg
        return cfg

    def _save_as(self):
        cfg = self._collect_from_ui()
        path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON files", "*.json")])
        if path:
            save_config(cfg, path)
            messagebox.showinfo("保存成功", f"配置已保存到: {path}")
            logging.getLogger(__name__).info(f"配置已保存到 {path}")

    def _load_from(self):
        path = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])
        if path:
            from .config_manager import load_config as _load
            cfg = _load(path)
            self.app_state.config = cfg
            self._load_into_ui(cfg)
            logging.getLogger(__name__).info(f"配置已从 {path} 加载")

    def _start_processing(self):
        cfg = self._collect_from_ui()
        logger = logging.getLogger(__name__)
        logger.info(
            f"开始处理：标的 {cfg.get('tickers')}，分析师 {cfg.get('analysts')}，自动执行={cfg.get('auto_execute')}"
        )

        # Ensure Moomoo connected and account synced before starting
        if not ensure_moomoo_connected(self.app_state):
            try:
                messagebox.showwarning("提示", "未连接 Moomoo。已尝试连接但超时，请先点击‘连接/刷新账户’再重试。")
            finally:
                return
        # Optional: quick portfolio sync to reflect latest status
        try:
            sync_portfolio(self.app_state)
        except Exception:
            pass

        # Disable button during processing
        self.start_btn.state(["disabled"])  # type: ignore

        def on_done():
            # Re-enable in UI thread
            try:
                self.start_btn.state(["!disabled"])  # type: ignore
            except Exception:
                pass
            logger.info("处理完成。可以切换到其他Tab查看结果（下一阶段将填充内容）。")
            try:
                self.after(0, lambda: messagebox.showinfo("完成", "分析已完成。后续页面将在下一阶段展示详细结果。"))
            except Exception:
                pass

        # Start background analysis
        start_background_analysis(self.app_state, on_done=on_done)

    # Placeholders for Phase 2
    def _refresh_account(self):
        # Try to connect in background; status label will update via poll
        connect_moomoo(self.app_state)
        messagebox.showinfo("提示", "正在尝试连接/刷新账户（纸质模式）。")

    def _sync_positions(self):
        pf = sync_portfolio(self.app_state)
        if pf is None:
            messagebox.showwarning("提示", "未连接 Moomoo 或同步失败。")
        else:
            messagebox.showinfo("完成", "已同步持仓（详情请查看日志）。")

    def _sync_orders(self):
        # For now fetch today's orders; later we can prompt for a date range
        orders = sync_orders(self.app_state)
        if orders is None:
            messagebox.showwarning("提示", "未连接 Moomoo 或同步失败。")
        else:
            messagebox.showinfo("完成", f"已同步订单，共 {len(orders)} 条。")

    def _poll_status(self):
        try:
            if getattr(self.app_state, "moomoo_connected", False):
                self.account_status.config(text="已连接（纸质交易）")
            else:
                self.account_status.config(text="未连接")
            self._render_portfolio()
        finally:
            self.after(800, self._poll_status)

    def _render_portfolio(self):
        pf = getattr(self.app_state, "portfolio", None)
        # Update summary
        if pf:
            cash = pf.get("cash")
            total = pf.get("total_assets")
            self.cash_var.set(f"现金: ${cash:,.2f}" if isinstance(cash, (int, float)) else "现金: -")
            self.assets_var.set(f"总资产: ${total:,.2f}" if isinstance(total, (int, float)) else "总资产: -")
        else:
            self.cash_var.set("现金: -")
            self.assets_var.set("总资产: -")

        # Update positions
        for i in self.pos_tree.get_children():
            self.pos_tree.delete(i)
        if pf and isinstance(pf.get("positions"), dict):
            for tkr, pos in pf["positions"].items():
                long_q = pos.get("long", 0)
                short_q = pos.get("short", 0)
                mv = pos.get("market_value", 0.0)
                upnl = pos.get("unrealized_pnl", 0.0)
                self.pos_tree.insert("", tk.END, values=(tkr, long_q, short_q, f"${mv:,.2f}", f"${upnl:,.2f}"))

        # Update orders
        for i in getattr(self, "orders_tree", []).get_children() if hasattr(self, "orders_tree") else []:
            self.orders_tree.delete(i)
        orders = getattr(self.app_state, "orders", None)
        if isinstance(orders, list):
            for od in orders:
                tkr = od.get("ticker") or (od.get("code") or "").split(".")[-1]
                side = od.get("trd_side", "")
                status = od.get("order_status", "")
                qty = od.get("qty", 0)
                dqty = od.get("dealt_qty", 0)
                price = od.get("price", 0.0)
                avg = od.get("dealt_avg_price", 0.0)
                tm = od.get("updated_time") or od.get("create_time") or ""
                oid = od.get("order_id", "")
                self.orders_tree.insert("", tk.END, values=(tm, tkr, side, status, qty, dqty, f"${price:,.2f}", f"${avg:,.2f}", oid))
