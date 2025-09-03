# AI Hedge Fund GUI — Design & Requirements

## 1. Overview
- Purpose: A clean, minimal Tkinter GUI to run AI hedge fund analysis, review agent outputs, preview and execute paper trades on Moomoo, and monitor logs in real time.
- Scope: Configuration, Data Analysis, AI Agents, Trading Decisions, Logs. All compute and IO in background threads to keep UI responsive.
- Safety: Paper trading only by default; never place real orders from the GUI.

## 2. Architecture
- Shared state: `ai_gui/services.py::AppState`
  - `config: Dict[str, Any]` — GUI configuration
  - `log_queue: Queue` — GUI logging sink
  - `runner: AIHedgeFundMoomooRunner | None` — created on main thread
  - `moomoo_connected: bool`
  - `last_result: Dict | None` — output of `run_ai_hedge_fund_analysis()`
  - `moomoo_decisions: Dict | None` — converted trade instructions
  - `execution_results: Dict | None` — results of trade execution
  - `performance: Dict | None` — post-trade performance metrics
  - `state_seq: int` — monotonically increasing sequence for tab polling

- Services (`ai_gui/services.py`)
  - Logging bootstrap: `init_logging_for_gui()`
  - State signal: `mark_state_changed()`
  - Background analysis: `start_background_analysis(state, on_done)`
    - Creates `AIHedgeFundMoomooRunner` on main thread, runs analysis in a background thread
  - Moomoo helpers (paper mode):
    - `connect_moomoo(state, on_done)`
    - `disconnect_moomoo(state)`
    - `sync_portfolio(state)` — fetch holdings/cash if connected
    - `convert_decisions_for_moomoo(state)`
    - `simulate_execution(state)` — safe local mock
    - `execute_on_moomoo(state, on_done)` — paper execution + performance + save results

- Runner integration: `run_ai_hedge_fund_with_moomoo.AIHedgeFundMoomooRunner`
  - Methods used: `initialize_moomoo()`, `run_ai_hedge_fund_analysis()`, `convert_ai_decisions_to_moomoo_format()`, `execute_trades_on_moomoo()`, `analyze_performance()`, `save_results()`

## 3. Tabs (UI)
- Config (`ai_gui/tabs_config.py`)
  - Inputs: tickers, analysts, toggles (paper only enforced, auto-execute, show reasoning)
  - Actions: 保存配置, 加载配置, 开始处理（后台分析）
  - Account panel: 连接/刷新账户（后台连接，纸质模式），同步持仓，状态实时轮询显示

- 数据分析 (`ai_gui/tabs_data.py`)
  - 显示标的及分析区间概要
  - 决策表格：ticker/action/quantity/confidence（基于 `last_result['decisions']`）
  - 轮询 `state_seq` 自动刷新

- AI 分析师 (`ai_gui/tabs_agents.py`)
  - 显示 `analyst_signals`：analyst/ticker/action/confidence
  - 轮询 `state_seq` 自动刷新

- 交易决策 (`ai_gui/tabs_trading.py`)
  - 按钮：转换为Moomoo格式、模拟执行(安全)、在Moomoo执行(纸质)
  - 预览表格：ticker/action/quantity/confidence/reasoning（显示原始或转换后的决策）
  - 执行状态：显示模拟/纸质执行结果汇总

- 日志监控 (`ai_gui/tabs_logs.py`)
  - 从 `log_queue` 拉取并显示，滚动追踪

## 4. Threading & Responsiveness
- 所有耗时任务在后台线程执行：AI 分析、Moomoo 连接、持仓同步、交易执行、绩效分析、保存结果
- GUI 仅做 polling：每 800ms 读取 `AppState.state_seq`/状态字段刷新视图
- 避免在子线程里创建 `AIHedgeFundMoomooRunner`（涉及 `signal`），在主线程实例化

## 5. Configuration Schema (JSON)
- Located in `ai_gui/configs/default.json` (loaded via `load_config()`)
- Minimal keys:
  - `tickers: List[str]`
  - `analysts: List[str]`
  - `paper_trading_only: true` (enforced from GUI)
  - `auto_execute: bool`
  - `show_reasoning: bool`
  - `refresh_intervals.logs_ms: int` (e.g., 300)
  - `start_date: str | null`, `end_date: str | null`

## 6. Logging
- Python logging routed to both console and GUI via `setup_gui_logging()` and `log_queue`
- Tabs and services record lifecycle messages, warnings, and exceptions for traceability

## 7. Safety & Modes
- 默认强制纸质交易：GUI 不提供关闭选项
- `execute_on_moomoo()` 仅在连接成功后进行纸质执行
- 可随时使用 `simulate_execution()` 进行本地安全演练

## 8. Primary Flows
- 分析流程
  1) 配置 Tab 填写参数 → 点击“开始处理”
  2) `start_background_analysis()` 运行 → 更新 `last_result` → `state_seq++`
  3) 数据/分析师/交易 Tabs 自动刷新显示

- 交易流程（安全/纸质）
  1) 交易 Tab → 转换为 Moomoo 格式 → 预览
  2) 模拟执行(安全) 或 在Moomoo执行(纸质)
  3) 执行后生成 `execution_results` 和 `performance`，保存结果文件

- Moomoo 连接/同步
  1) 配置 Tab → 连接/刷新账户（后台连接）
  2) 成功后 → 同步持仓（写入 runner.results['portfolio_before']）

## 9. Non-Functional Requirements
- 简洁、稳定、无阻塞 UI
- 结构清晰，增量迭代友好
- 关键错误具备用户提示与日志记录

## 10. Run Instructions
- Windows + venv 示例：
  ```bash
  ..\venv\Scripts\python.exe -m ai_gui.main_gui
  ```

## 11. Future Enhancements
- 数据分析 Tab：嵌入 matplotlib 价格图、舆情/新闻面板
- 绩效可视化：交易明细、收益曲线、风险指标
- 更细的账户与风控面板：现金、持仓权重、限额控制
- 自动化测试与 CI 集成

## 12. Manual Test Checklist
- 配置
  - 修改 tickers/analysts，保存并加载配置
  - 切换“自动执行”“显示推理”并生效
- 分析
  - 点击开始处理，日志显示进度；完成后 Data/Agents/Trading 自动刷新
- Moomoo（纸质）
  - 连接/刷新账户 → 状态更新
  - 同步持仓 → 日志显示成功或错误
- 交易
  - 转换为 Moomoo 格式 → 表格显示转换后项
  - 模拟执行(安全) → 显示执行汇总
  - 在Moomoo执行(纸质) → 日志显示执行、生成绩效并保存结果文件
- 日志
  - 实时滚动，异常有栈信息
