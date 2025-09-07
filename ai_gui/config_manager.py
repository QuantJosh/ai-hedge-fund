import json
from pathlib import Path
from typing import Any, Dict, Optional

DEFAULT_CONFIG = {
    "tickers": ["AAPL", "MSFT", "GOOGL"],
    "analysts": [
        "warren_buffett", "ben_graham", "charlie_munger", "peter_lynch", "fundamentals_analyst"
    ],
    "start_date": None,
    "end_date": None,
    "paper_trading_only": True,
    "auto_execute": False,
    "show_reasoning": True,
    # LLM settings (GUI-selectable)
    "model_provider": "OpenRouter",
    "model_name": "openai/gpt-4o-mini",
    # LLM runtime controls
    "llm_max_concurrency": "3",   # string for easy textbox editing
    "llm_request_timeout": "60",  # seconds, string
    # Whether to sync live portfolio from Moomoo before analysis (may slow down)
    "use_live_portfolio_for_analysis": False,
    "refresh_intervals": {"account_seconds": 60, "logs_ms": 300},
}

CONFIG_DIR = Path("ai_gui/configs")
CONFIG_DIR.mkdir(parents=True, exist_ok=True)
DEFAULT_CONFIG_PATH = CONFIG_DIR / "default.json"


def load_config(path: Optional[Path] = None) -> Dict[str, Any]:
    p = Path(path) if path else DEFAULT_CONFIG_PATH
    if not p.exists():
        save_config(DEFAULT_CONFIG, p)
        return DEFAULT_CONFIG.copy()
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)


def save_config(cfg: Dict[str, Any], path: Optional[Path] = None) -> Path:
    p = Path(path) if path else DEFAULT_CONFIG_PATH
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)
    return p
