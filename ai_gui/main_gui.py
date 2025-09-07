import logging
import tkinter as tk
from tkinter import ttk
import os

from .config_manager import load_config
from .gui_logger import setup_gui_logging
from .services import AppState, init_logging_for_gui, disconnect_moomoo
from .tabs_logs import LogsTab
from .tabs_config import ConfigTab
from .tabs_data import DataTab
from .tabs_agents import AgentsTab
from .tabs_trading import TradingTab
from .tabs_market import MarketsTab
from .tabs_llm import LLMTab


def create_app() -> tk.Tk:
    root = tk.Tk()
    root.title("AI Hedge Fund - Trading Dashboard")
    root.geometry("1000x700")

    # Shared state
    state = AppState()
    # Load environment variables from .env if present (so FINANCIAL_DATASETS_API_KEY works in GUI)
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except Exception:
        pass
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
    logs_tab = LogsTab(nb, log_queue=state.log_queue, poll_ms=state.config.get("refresh_intervals", {}).get("logs_ms", 300), app_state=state)
    markets_tab = MarketsTab(nb, app_state=state)
    llm_tab = LLMTab(nb, app_state=state)

    nb.add(config_tab, text="配置")
    nb.add(data_tab, text="数据分析")
    nb.add(agents_tab, text="AI分析师")
    nb.add(trading_tab, text="交易决策")
    nb.add(logs_tab, text="日志监控")
    nb.add(markets_tab, text="Markets")
    nb.add(llm_tab, text="LLM对话")

    # Status bar
    status = ttk.Label(root, text="就绪", anchor=tk.W)
    status.pack(fill=tk.X, side=tk.BOTTOM)

    # Graceful close: disconnect and destroy, then ensure interpreter exits
    def _on_close():
        # Try graceful cleanup first
        try:
            disconnect_moomoo(state)
        except Exception:
            pass
        try:
            root.quit()
            root.destroy()
        except Exception:
            pass
        # Some third-party SDKs may spawn non-daemon threads preventing return to shell.
        # Ensure process terminates.
        try:
            import os
            os._exit(0)
        except Exception:
            pass

    root.protocol("WM_DELETE_WINDOW", _on_close)

    return root


if __name__ == "__main__":
    app = create_app()
    app.mainloop()
