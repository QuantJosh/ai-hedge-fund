import logging
import tkinter as tk
from tkinter import ttk

from .config_manager import load_config
from .gui_logger import setup_gui_logging
from .services import AppState, init_logging_for_gui, disconnect_moomoo
from .tabs_logs import LogsTab
from .tabs_config import ConfigTab
from .tabs_data import DataTab
from .tabs_agents import AgentsTab
from .tabs_trading import TradingTab


def create_app() -> tk.Tk:
    root = tk.Tk()
    root.title("AI Hedge Fund - Trading Dashboard")
    root.geometry("1000x700")

    # Shared state
    state = AppState()
    state.config = load_config()

    # Logging
    init_logging_for_gui(state.log_queue)
    setup_gui_logging(state.log_queue)
    logging.getLogger(__name__).info("GUI 启动完成")

    # Notebook
    nb = ttk.Notebook(root)
    nb.pack(fill=tk.BOTH, expand=True)

    config_tab = ConfigTab(nb, app_state=state)
    data_tab = DataTab(nb, app_state=state)
    agents_tab = AgentsTab(nb, app_state=state)
    trading_tab = TradingTab(nb, app_state=state)
    logs_tab = LogsTab(nb, log_queue=state.log_queue, poll_ms=state.config.get("refresh_intervals", {}).get("logs_ms", 300))

    nb.add(config_tab, text="配置")
    nb.add(data_tab, text="数据分析")
    nb.add(agents_tab, text="AI分析师")
    nb.add(trading_tab, text="交易决策")
    nb.add(logs_tab, text="日志监控")

    # Status bar
    status = ttk.Label(root, text="就绪", anchor=tk.W)
    status.pack(fill=tk.X, side=tk.BOTTOM)

    # Graceful close: disconnect and destroy
    def _on_close():
        try:
            disconnect_moomoo(state)
        except Exception:
            pass
        try:
            root.quit()
            root.destroy()
        finally:
            import sys as _sys
            _sys.exit(0)

    root.protocol("WM_DELETE_WINDOW", _on_close)

    return root


if __name__ == "__main__":
    app = create_app()
    app.mainloop()
