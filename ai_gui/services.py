import logging
import queue
from dataclasses import dataclass, field
from typing import Any, Dict, Optional
import threading
import sys
from pathlib import Path


@dataclass
class AppState:
    """Shared app state kept minimal for Phase 1."""
    config: Dict[str, Any] = field(default_factory=dict)
    log_queue: "queue.Queue[tuple[str, str]]" = field(default_factory=queue.Queue)

    # Placeholders for future phases
    runner: Any = None  # AIHedgeFundMoomooRunner instance when used
    moomoo_connected: bool = False
    last_result: Optional[Dict[str, Any]] = None
    state_seq: int = 0  # increment when important state changes
    moomoo_decisions: Optional[Dict[str, Any]] = None
    execution_results: Optional[Dict[str, Any]] = None
    performance: Optional[Dict[str, Any]] = None
    portfolio: Optional[Dict[str, Any]] = None
    orders: Optional[list] = None


def init_logging_for_gui(log_queue: queue.Queue) -> None:
    """Ensure base logging is set up; attach GUI sink in main_gui via setup_gui_logging."""
    # If root logger has no handlers, set a basic console handler to avoid missing logs
    logger = logging.getLogger()
    if not logger.handlers:
        logging.basicConfig(
            level=logging.INFO,
            format="[%(asctime)s] %(levelname)s - %(message)s",
            datefmt="%H:%M:%S",
        )


def _ensure_src_on_path() -> None:
    """Make sure project src is importable when launched as module."""
    root = Path(__file__).resolve().parents[1]
    src_path = root / "src"
    if str(src_path) not in sys.path:
        sys.path.append(str(src_path))


def mark_state_changed(state: AppState) -> None:
    """Increment state sequence for tab pollers to react to changes."""
    try:
        state.state_seq += 1
    except Exception:
        pass


def convert_decisions_for_moomoo(state: AppState) -> Optional[Dict[str, Any]]:
    """Convert AI decisions to Moomoo format using runner (no connection needed)."""
    logger = logging.getLogger(__name__)
    if not state.runner or not state.last_result or not state.last_result.get("decisions"):
        logger.warning("[GUI] 无法转换：缺少 runner 或 decisions")
        return None
    try:
        moomoo_decisions = state.runner.convert_ai_decisions_to_moomoo_format(state.last_result["decisions"])
        state.moomoo_decisions = moomoo_decisions
        mark_state_changed(state)
        return moomoo_decisions
    except Exception as e:
        logger.exception(f"[GUI] 转换决策失败: {e}")
        return None


def sync_orders(state: AppState, start_date: Optional[str] = None, end_date: Optional[str] = None) -> Optional[list]:
    """Fetch orders from Moomoo (today if no dates) and cache in AppState.orders."""
    logger = logging.getLogger(__name__)
    try:
        if state.runner and state.moomoo_connected and state.runner.moomoo_integration:
            orders = state.runner.moomoo_integration.get_orders(start_date=start_date, end_date=end_date)
            state.orders = orders
            mark_state_changed(state)
            return orders
        logger.warning("[GUI] 未连接 Moomoo，无法同步订单")
        return None
    except Exception as e:
        logger.exception(f"[GUI] 同步订单失败: {e}")
        return None


def simulate_execution(state: AppState) -> Optional[Dict[str, Any]]:
    """Simulate execution results locally without Moomoo connection."""
    logger = logging.getLogger(__name__)
    if not state.moomoo_decisions:
        logger.warning("[GUI] 无法模拟执行：请先完成决策转换")
        return None
    try:
        sim = {
            tkr: {
                "success": True,
                "message": "simulated",
                "order_id": f"SIM-{i:04d}",
                "executed_price": None,
                "executed_quantity": d.get("quantity", 0),
            }
            for i, (tkr, d) in enumerate(state.moomoo_decisions.items(), start=1)
        }
        state.execution_results = sim
        mark_state_changed(state)
        logger.info("[GUI] 已生成模拟执行结果（未连接 Moomoo）")
        return sim
    except Exception as e:
        logger.exception(f"[GUI] 模拟执行失败: {e}")
        return None


def start_background_analysis(state: AppState, on_done: Optional[callable] = None) -> None:
    """Run AI analysis in a background thread without requiring Moomoo connection.

    Important: Construct AIHedgeFundMoomooRunner on the main thread to avoid signal() errors.
    The background thread only calls run_ai_hedge_fund_analysis().
    """
    logger = logging.getLogger(__name__)

    # Prepare runner on the main thread (signal handlers must be set in main thread)
    _ensure_src_on_path()
    from run_ai_hedge_fund_with_moomoo import AIHedgeFundMoomooRunner

    cfg = state.config
    tickers = cfg.get("tickers", [])
    start_date = cfg.get("start_date")
    end_date = cfg.get("end_date")
    analysts = cfg.get("analysts", [])
    auto_execute = bool(cfg.get("auto_execute", False))
    show_reasoning = bool(cfg.get("show_reasoning", True))

    try:
        runner = AIHedgeFundMoomooRunner(
            tickers=tickers,
            start_date=start_date,
            end_date=end_date,
            selected_analysts=analysts if analysts else None,
            paper_trading_only=True,
            auto_execute=auto_execute,
            show_reasoning=show_reasoning,
        )
        state.runner = runner
    except Exception as e:
        logger.exception(f"[GUI] 无法创建分析Runner: {e}")
        if on_done:
            try:
                on_done()
            except Exception:
                pass
        return

    def worker():
        try:
            logger.info("[GUI] 启动后台分析...")
            # Do NOT connect to Moomoo in Phase 2 minimal; run analysis only
            result = state.runner.run_ai_hedge_fund_analysis()
            state.last_result = result
            mark_state_changed(state)

            if result:
                logger.info("[GUI] 分析完成。可在后续页面显示决策与分析师输出。")
            else:
                logger.error("[GUI] 分析失败或无结果。")
        except Exception as e:
            logger.exception(f"[GUI] 后台分析异常: {e}")
        finally:
            if on_done:
                try:
                    on_done()
                except Exception:
                    pass

    t = threading.Thread(target=worker, daemon=True)
    t.start()


def connect_moomoo(state: AppState, on_done: Optional[callable] = None) -> None:
    """Attempt to connect to Moomoo in background and sync initial portfolio.

    Safe: runner enforces paper_trading_only.
    """
    logger = logging.getLogger(__name__)

    def _ensure_runner_main_thread():
        if not state.runner:
            _ensure_src_on_path()
            from run_ai_hedge_fund_with_moomoo import AIHedgeFundMoomooRunner
            cfg = state.config
            # IMPORTANT: Construct on the calling (GUI) thread to avoid signal() errors
            state.runner = AIHedgeFundMoomooRunner(
                tickers=cfg.get("tickers", []),
                start_date=cfg.get("start_date"),
                end_date=cfg.get("end_date"),
                selected_analysts=cfg.get("analysts", []) or None,
                paper_trading_only=True,
                auto_execute=bool(cfg.get("auto_execute", False)),
                show_reasoning=bool(cfg.get("show_reasoning", True)),
            )

    def worker():
        try:
            ok = state.runner.initialize_moomoo()
            state.moomoo_connected = bool(ok)
            if ok:
                logger.info("[GUI] 已连接至 Moomoo（纸质交易）")
                # Try initial portfolio fetch
                try:
                    pf = state.runner.moomoo_integration.get_portfolio_sync()
                    state.runner.results["portfolio_before"] = pf
                    state.portfolio = pf
                except Exception:
                    pass
            else:
                logger.warning("[GUI] 无法连接 Moomoo，请确认 OpenD 状态")
            mark_state_changed(state)
        except Exception as e:
            logger.exception(f"[GUI] 连接 Moomoo 失败: {e}")
        finally:
            if on_done:
                try:
                    on_done()
                except Exception:
                    pass

    # Ensure runner is created on the main thread BEFORE starting worker
    _ensure_runner_main_thread()
    threading.Thread(target=worker, daemon=True).start()


def ensure_moomoo_connected(state: AppState, timeout_sec: float = 12.0) -> bool:
    """Ensure Moomoo is connected. Returns True if connected or becomes connected within timeout.

    Safe wrapper used before starting processing.
    """
    logger = logging.getLogger(__name__)
    if state.moomoo_connected:
        return True
    try:
        _evt = threading.Event()
        connect_moomoo(state, on_done=_evt.set)
        _evt.wait(timeout=timeout_sec)
        if state.moomoo_connected:
            logger.info("[GUI] 已连接 Moomoo (ensure)")
            return True
        logger.warning("[GUI] ensure_moomoo_connected 等待超时")
        return False
    except Exception as e:
        logger.exception(f"[GUI] ensure_moomoo_connected 异常: {e}")
        return False


def get_candles(state: AppState, ticker: str, bars: int = 120):
    """Fetch recent candles for ticker for charting. Returns list of dicts with time, open, high, low, close.

    Placeholder implementation: attempts via Moomoo when available; else returns [].
    """
    logger = logging.getLogger(__name__)
    try:
        if state.runner and state.moomoo_connected and state.runner.moomoo_integration and \
           state.runner.moomoo_integration.client and state.runner.moomoo_integration.client.quote_ctx:
            # Try current kline first (recent bars). API may vary; handle exceptions gracefully.
            mm = state.runner.moomoo_integration.client
            code = f"{mm.market}.{ticker}"
            try:
                # Attempt get_cur_kline if available
                ret, data = mm.quote_ctx.get_cur_kline(code,  num=bars)
            except Exception:
                # Fallback: try get_history_kline style API if present
                try:
                    ret, data = mm.quote_ctx.get_history_kline(code)
                except Exception as _:
                    ret, data = None, None
            out = []
            if ret == 0 and data is not None and not getattr(data, 'empty', True):
                for _, row in data.iterrows():
                    ts = row.get('time_key') or row.get('time') or row.get('timestamp')
                    out.append({
                        'time': str(ts),
                        'open': float(row.get('open', 0.0)),
                        'high': float(row.get('high', 0.0)),
                        'low': float(row.get('low', 0.0)),
                        'close': float(row.get('close', 0.0)),
                    })
            # If we got data from Moomoo, return it; otherwise continue to fallback
            if out:
                return out
        # Fallback: use yfinance to fetch recent OHLC
        try:
            import yfinance as yf
            import pandas as pd
            def _yf_symbol(sym: str) -> str:
                # Map common cases for Yahoo symbols (e.g., BRK.B -> BRK-B)
                return sym.replace('.', '-')
            def _to_float_scalar(v):
                # Robustly convert pandas/numpy scalars or single-element Series to float
                try:
                    if hasattr(v, 'item'):
                        return float(v.item())
                    if hasattr(v, 'iloc'):
                        return float(v.iloc[0])
                    return float(v)
                except Exception:
                    try:
                        return float(str(v))
                    except Exception:
                        return 0.0
            # Heuristic: if symbol lacks suffix, try as-is; users can provide proper tickers
            period = '5d' if bars <= 390 else '1mo'
            interval = '5m' if bars <= 390 else '1d'
            df = yf.download(_yf_symbol(ticker), period=period, interval=interval, progress=False, auto_adjust=False)
            out = []
            if isinstance(df, pd.DataFrame) and not df.empty:
                # Take the last N rows
                df = df.tail(bars)
                for idx, row in df.iterrows():
                    out.append({
                        'time': str(idx.to_pydatetime()),
                        'open': _to_float_scalar(row.get('Open', 0.0)),
                        'high': _to_float_scalar(row.get('High', 0.0)),
                        'low': _to_float_scalar(row.get('Low', 0.0)),
                        'close': _to_float_scalar(row.get('Close', 0.0)),
                    })
            if not out:
                logger.info("[GUI] yfinance 返回空数据: %s", ticker)
            return out
        except Exception as yf_err:
            logger.info("[GUI] yfinance 获取K线失败: %s", yf_err)
            return []
    except Exception as e:
        logger.exception(f"[GUI] 获取K线失败: {e}")
        return []


def get_orders_for_ticker(state: AppState, ticker: str):
    """Filter cached orders by ticker (expects AppState.orders already synced)."""
    try:
        orders = state.orders or []
        t = ticker.upper()
        return [o for o in orders if (o.get('ticker') or (o.get('code') or '').split('.')[-1]).upper() == t]
    except Exception:
        return []


def disconnect_moomoo(state: AppState) -> None:
    logger = logging.getLogger(__name__)
    try:
        if state.runner and getattr(state.runner, "moomoo_integration", None):
            state.runner.moomoo_integration.disconnect()
        state.moomoo_connected = False
        logger.info("[GUI] 已断开 Moomoo")
    except Exception:
        logger.warning("[GUI] 断开 Moomoo 时出现问题")
    finally:
        mark_state_changed(state)


def sync_portfolio(state: AppState) -> Optional[Dict[str, Any]]:
    logger = logging.getLogger(__name__)
    try:
        if state.runner and state.moomoo_connected and state.runner.moomoo_integration:
            pf = state.runner.moomoo_integration.get_portfolio_sync()
            state.runner.results["portfolio_before"] = pf
            state.portfolio = pf
            mark_state_changed(state)
            return pf
        logger.warning("[GUI] 未连接 Moomoo，无法同步持仓")
        return None
    except Exception as e:
        logger.exception(f"[GUI] 同步持仓失败: {e}")
        return None


def execute_on_moomoo(state: AppState, on_done: Optional[callable] = None) -> None:
    """Execute converted decisions on Moomoo in background (paper trading)."""
    logger = logging.getLogger(__name__)

    def worker():
        try:
            if not state.moomoo_decisions:
                convert_decisions_for_moomoo(state)
            if not state.moomoo_connected:
                logger.info("[GUI] 未连接，尝试连接 Moomoo...")
                _evt = threading.Event()
                connect_moomoo(state, on_done=_evt.set)
                _evt.wait(timeout=15)
            if not state.moomoo_connected:
                logger.error("[GUI] 执行失败：仍未连接 Moomoo")
                return

            # Ensure auto_execute to avoid CLI prompt in runner
            state.runner.auto_execute = True
            decisions = state.moomoo_decisions or {}
            exec_res = state.runner.execute_trades_on_moomoo(decisions)
            # exec_res is likely a mapping of ticker->result object; runner.results has formatted dict
            state.execution_results = state.runner.results.get("moomoo_execution", {}) or exec_res
            mark_state_changed(state)

            perf = state.runner.analyze_performance()
            state.performance = perf
            results_file = state.runner.save_results()
            logger.info(f"[GUI] 交易与绩效分析完成，结果保存：{results_file}")
            mark_state_changed(state)
        except Exception as e:
            logger.exception(f"[GUI] 执行交易失败: {e}")
        finally:
            if on_done:
                try:
                    on_done()
                except Exception:
                    pass

    threading.Thread(target=worker, daemon=True).start()
