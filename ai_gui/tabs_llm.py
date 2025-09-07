import tkinter as tk
from tkinter import ttk
from typing import List, Dict, Any, Optional
import os
import json
from pathlib import Path
import threading

try:
    import requests
    _HAS_REQUESTS = True
except Exception:
    _HAS_REQUESTS = False

from . import config_manager


class LLMTab(ttk.Frame):
    """
    Displays LLM prompts and responses by reading structured logs written by
    `src.utils.logger.AIHedgeFundLogger` into `logs/<session_id>/structured_log.jsonl`.
    """
    def __init__(self, master, app_state=None):
        super().__init__(master)
        self.app_state = app_state

        # Controls
        controls = ttk.Frame(self)
        controls.pack(fill=tk.X, padx=8, pady=6)
        ttk.Button(controls, text="刷新", command=self._refresh).pack(side=tk.LEFT)
        # Provider / Model selectors
        ttk.Label(controls, text="Provider").pack(side=tk.LEFT, padx=(12, 4))
        self.provider_var = tk.StringVar(value=(self.app_state.config.get("model_provider") if self.app_state else "OpenRouter") or "OpenRouter")
        self.provider_combo = ttk.Combobox(controls, textvariable=self.provider_var, width=18, state="readonly")
        self.provider_combo.pack(side=tk.LEFT)
        self.provider_combo.bind("<<ComboboxSelected>>", self._on_select_provider)

        ttk.Label(controls, text="Model").pack(side=tk.LEFT, padx=(12, 4))
        self.model_var = tk.StringVar(value=(self.app_state.config.get("model_name") if self.app_state else "openai/gpt-4o-mini") or "openai/gpt-4o-mini")
        self.model_combo = ttk.Combobox(controls, textvariable=self.model_var, width=28, state="readonly")
        self.model_combo.pack(side=tk.LEFT)

        ttk.Button(controls, text="从 OpenRouter 获取模型", command=self._fetch_models_async).pack(side=tk.LEFT, padx=(12, 4))
        ttk.Button(controls, text="保存选择", command=self._save_model_selection).pack(side=tk.LEFT)
        ttk.Label(controls, text="仅显示最近会话").pack(side=tk.LEFT, padx=(12, 4))
        self.only_latest_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(controls, variable=self.only_latest_var, command=self._refresh).pack(side=tk.LEFT)
        ttk.Label(controls, text="按Agent分组").pack(side=tk.LEFT, padx=(12, 4))
        self.group_by_agent_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(controls, variable=self.group_by_agent_var, command=self._on_toggle_grouping).pack(side=tk.LEFT)
        ttk.Label(controls, text="合并为单个会话").pack(side=tk.LEFT, padx=(12, 4))
        self.aggregate_by_agent_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(controls, variable=self.aggregate_by_agent_var, command=self._on_toggle_grouping).pack(side=tk.LEFT)

        # Split pane
        paned = ttk.PanedWindow(self, orient=tk.VERTICAL)
        paned.pack(fill=tk.BOTH, expand=True)

        # Top: table of model events
        top_frame = ttk.Frame(paned)
        paned.add(top_frame, weight=1)
        cols = ("time", "type", "agent", "model", "ticker", "preview")
        self.tree = ttk.Treeview(top_frame, columns=cols, show="headings", height=12)
        widths = (160, 110, 160, 200, 100, 600)
        for c, w in zip(cols, widths):
            self.tree.heading(c, text=c)
            self.tree.column(c, width=w, anchor=tk.W if c in ("time", "agent", "model", "preview") else tk.CENTER)
        self.tree.pack(fill=tk.BOTH, expand=True, padx=8, pady=6)
        self.tree.bind("<<TreeviewSelect>>", self._on_select)

        # Bottom: details (tabs for Prompt / Response)
        bottom_frame = ttk.Notebook(paned)
        self.detail_notebook = bottom_frame
        paned.add(bottom_frame, weight=1)

        self.prompt_text = tk.Text(bottom_frame, wrap=tk.NONE)
        self.prompt_text.configure(state=tk.DISABLED)
        self.response_text = tk.Text(bottom_frame, wrap=tk.NONE)
        self.response_text.configure(state=tk.DISABLED)
        # Configure tags for colored transcript rendering
        try:
            self.response_text.tag_configure("req_header", foreground="#1f6feb", font=(None, 10, "bold"))  # blue
            self.response_text.tag_configure("resp_header", foreground="#2ea043", font=(None, 10, "bold"))  # green
            self.response_text.tag_configure("req_body", foreground="#0969da")  # blue-ish
            self.response_text.tag_configure("resp_body", foreground="#1a7f37")  # green-ish
            self.response_text.tag_configure("mono", font=("Consolas", 10))
        except Exception:
            pass

        bottom_frame.add(self.prompt_text, text="Prompt")
        bottom_frame.add(self.response_text, text="Response")

        # Internal storage
        self._records: List[Dict[str, Any]] = []
        self._models_by_provider: Dict[str, List[str]] = {}

        # Initial load
        self._update_detail_tabs()
        self._refresh()
        # Try initial populate of provider/model from API (non-blocking)
        self._fetch_models_async(silent=True)

    def _on_toggle_grouping(self, _evt: Optional[object] = None):
        try:
            # If aggregation is enabled, force group-by-agent on
            if self.aggregate_by_agent_var.get() and not self.group_by_agent_var.get():
                self.group_by_agent_var.set(True)
            # Update tabs according to aggregation
            self._update_detail_tabs()
            self._refresh()
        except Exception:
            self._refresh()

    # Utilities to locate and read structured logs
    def _logs_root(self) -> Path:
        # Prefer project-root "logs" folder
        return Path(os.getcwd()) / "logs"

    def _list_sessions(self) -> List[Path]:
        root = self._logs_root()
        if not root.exists():
            return []
        sessions = [p for p in root.iterdir() if p.is_dir()]
        sessions.sort(key=lambda p: p.stat().st_mtime, reverse=True)
        return sessions

    def _read_jsonl(self, path: Path) -> List[Dict[str, Any]]:
        out: List[Dict[str, Any]] = []
        try:
            with path.open("r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        out.append(json.loads(line))
                    except Exception:
                        continue
        except Exception:
            pass
        return out

    def _set_transcript(self, widget: tk.Text, content: str):
        """Render aggregated transcript with colored REQUEST/RESPONSE sections.
        Expected section headers like: "[timestamp] REQUEST | ..." or "[timestamp] RESPONSE | ...".
        """
        try:
            widget.configure(state=tk.NORMAL)
            widget.delete("1.0", tk.END)
            lines = content.splitlines()
            current_tag_body = None
            for line in lines:
                stripped = line.strip()
                if stripped.startswith("[") and (" REQUEST " in stripped or stripped.endswith(" REQUEST") or stripped.startswith("[") and " REQUEST |" in stripped):
                    widget.insert(tk.END, line + "\n", ("req_header", "mono"))
                    current_tag_body = "req_body"
                elif stripped.startswith("[") and (" RESPONSE " in stripped or stripped.endswith(" RESPONSE") or stripped.startswith("[") and " RESPONSE |" in stripped):
                    widget.insert(tk.END, line + "\n", ("resp_header", "mono"))
                    current_tag_body = "resp_body"
                else:
                    tag = current_tag_body or "mono"
                    widget.insert(tk.END, line + "\n", (tag,))
            widget.configure(state=tk.DISABLED)
        except Exception:
            # Fallback to plain
            self._set_text(widget, content)

    def _update_detail_tabs(self):
        try:
            nb = getattr(self, "detail_notebook", None)
            if not nb:
                return
            agg = bool(self.aggregate_by_agent_var.get())
            tabs = {nb.tab(i, 'text'): i for i in nb.tabs()} if hasattr(nb, 'tabs') else {}
            # Ensure both widgets are attached appropriately
            if agg:
                # Hide Prompt tab if present
                if 'Prompt' in tabs:
                    nb.forget(tabs['Prompt'])
                # Ensure Response tab present and renamed to Transcript
                tabs = {nb.tab(i, 'text'): i for i in nb.tabs()}
                if 'Response' not in tabs:
                    nb.add(self.response_text, text='Transcript')
                else:
                    nb.tab(tabs['Response'], text='Transcript')
            else:
                # Non-aggregated: ensure both Prompt and Response visible with correct labels
                tabs = {nb.tab(i, 'text'): i for i in nb.tabs()}
                # If Response is labeled Transcript, rename back
                if 'Transcript' in tabs:
                    nb.tab(tabs['Transcript'], text='Response')
                # Re-add Prompt if missing
                tabs = {nb.tab(i, 'text'): i for i in nb.tabs()}
                if 'Prompt' not in tabs:
                    nb.add(self.prompt_text, text='Prompt')
        except Exception:
            pass

    # ===== Model selector helpers =====
    def _fetch_models_async(self, silent: bool = False):
        def worker():
            self._fetch_openrouter_models(silent=silent)
        threading.Thread(target=worker, daemon=True).start()

    def _fetch_openrouter_models(self, silent: bool = False):
        # Only OpenRouter supported per request
        if not _HAS_REQUESTS:
            if not silent:
                self._show_status("请安装 requests 以从 OpenRouter 获取模型")
            return
        try:
            api_key = os.getenv("OPENROUTER_API_KEY")
            headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}
            resp = requests.get("https://openrouter.ai/api/v1/models", headers=headers, timeout=15)
            resp.raise_for_status()
            data = resp.json()
            items = data.get("data", []) if isinstance(data, dict) else []
            models_by_provider: Dict[str, List[str]] = {}
            for item in items:
                model_id = item.get("id") or item.get("name")
                prov = ((item.get("provider") or {}).get("name") or "OpenRouter").strip()
                if not model_id:
                    continue
                models_by_provider.setdefault(prov, []).append(model_id)
            # sort providers and models
            for k in models_by_provider:
                models_by_provider[k] = sorted(set(models_by_provider[k]))
            self._models_by_provider = dict(sorted(models_by_provider.items(), key=lambda kv: kv[0].lower()))
            self._populate_provider_and_models()
            if not silent:
                self._show_status("已从 OpenRouter 获取模型列表")
        except Exception as e:
            if not silent:
                self._show_status(f"获取模型失败: {e}")

    def _populate_provider_and_models(self):
        # Populate provider combobox
        providers = list(self._models_by_provider.keys()) or [self.provider_var.get() or "OpenRouter"]
        self.provider_combo["values"] = providers
        # Keep current provider if present, else default to first
        cur_provider = self.provider_var.get()
        if cur_provider not in providers and providers:
            cur_provider = providers[0]
            self.provider_var.set(cur_provider)
        # Populate model list for provider
        models = self._models_by_provider.get(cur_provider, [])
        self.model_combo["values"] = models
        # Keep current model if present else choose a common default
        cur_model = self.model_var.get()
        if cur_model not in models:
            if "openai/gpt-4o-mini" in models:
                self.model_var.set("openai/gpt-4o-mini")
            elif models:
                self.model_var.set(models[0])

    def _on_select_provider(self, _evt=None):
        self._populate_provider_and_models()

    def _save_model_selection(self):
        try:
            if not self.app_state:
                return
            provider = self.provider_var.get() or "OpenRouter"
            model = self.model_var.get() or "openai/gpt-4o-mini"
            # Update state and persist
            cfg = dict(self.app_state.config or {})
            cfg["model_provider"] = provider
            cfg["model_name"] = model
            config_manager.save_config(cfg)
            self.app_state.config = cfg
            # notify
            self._show_status(f"已保存模型设置：{provider} / {model}")
        except Exception as e:
            self._show_status(f"保存失败: {e}")

    def _show_status(self, msg: str):
        try:
            # Simple status feedback via title of the tree area
            self.tree.heading("model", text=f"model ({msg})")
            # revert after short delay
            self.after(2500, lambda: self.tree.heading("model", text="model"))
        except Exception:
            pass

    def _gather_records(self) -> List[Dict[str, Any]]:
        sessions = self._list_sessions()
        targets: List[Path] = []
        if self.only_latest_var.get():
            if sessions:
                targets = [sessions[0] / "structured_log.jsonl"]
        else:
            targets = [s / "structured_log.jsonl" for s in sessions]

        records: List[Dict[str, Any]] = []
        for p in targets:
            if p.exists():
                records.extend(self._read_jsonl(p))
        # Keep only model events
        records = [r for r in records if r.get("type") in ("model_request", "model_response")]
        return records

    def _refresh(self):
        # Clear table
        for i in self.tree.get_children():
            self.tree.delete(i)
        self._records = self._gather_records()
        # Ensure detail tabs reflect current mode
        self._update_detail_tabs()

        # Two modes: flat list (default) or grouped by agent with paired request/response
        if not self.group_by_agent_var.get():
            rows: List[Dict[str, Any]] = []
            for r in self._records:
                typ = r.get("type")
                model_info = r.get("model", {})
                agent = r.get("agent", "")
                ticker = r.get("ticker", "")
                model = model_info.get("model", model_info.get("name", "Unknown"))
                ts = r.get("timestamp", "")
                if typ == "model_request":
                    preview = (r.get("data", {}) or {}).get("prompt_preview", "")
                else:
                    preview = (r.get("data", {}) or {}).get("response_preview", "")
                rows.append({
                    "time": ts,
                    "type": "REQUEST" if typ == "model_request" else "RESPONSE",
                    "agent": agent,
                    "model": model,
                    "ticker": ticker,
                    "preview": preview,
                    "raw": r,
                })
            for row in rows:
                self.tree.insert(
                    "",
                    tk.END,
                    values=(row["time"], row["type"], row["agent"], row["model"], row["ticker"], row["preview"]),
                    tags=("model_request" if row["type"] == "REQUEST" else "model_response",)
                )
            self._rows = rows
            self._item_payload = {}
        else:
            # Group by agent and pair request/response by sequence (agent+model+ticker)
            def _key(r: Dict[str, Any]):
                m = (r.get("model", {}) or {})
                return (r.get("agent", ""), m.get("model", m.get("name", "Unknown")), r.get("ticker", ""))
            # Sort records by timestamp to ensure correct pairing order
            def _parse_ts(s: str):
                try:
                    from datetime import datetime
                    return datetime.fromisoformat(s.replace("Z", "+00:00"))
                except Exception:
                    return s
            recs_sorted = sorted(self._records, key=lambda r: _parse_ts(r.get("timestamp", "")))

            # pending map: key -> list of pending requests
            pending: Dict[tuple, List[Dict[str, Any]]] = {}
            conversations_by_agent: Dict[str, List[Dict[str, Any]]] = {}
            all_by_agent: Dict[str, List[Dict[str, Any]]] = {}

            for r in recs_sorted:
                k = _key(r)
                agent = k[0]
                all_by_agent.setdefault(agent, []).append(r)
                typ = r.get("type")
                if typ == "model_request":
                    pending.setdefault(k, []).append(r)
                elif typ == "model_response":
                    if pending.get(k):
                        req = pending[k].pop(0)
                    else:
                        req = None
                    conversations_by_agent.setdefault(agent, []).append({
                        "key": k,
                        "request": req,
                        "response": r,
                    })

            # Insert agents as parents; each conversation as child rows
            self._item_payload = {}
            for agent, convs in conversations_by_agent.items():
                parent_iid = self.tree.insert("", tk.END, values=("", "", agent, "", "", ""))
                if self.aggregate_by_agent_var.get():
                    # Build a consolidated transcript for the agent across all turns
                    lines: List[str] = []
                    lines.append(f"=== Agent: {agent} (合并会话) ===")
                    for rec in all_by_agent.get(agent, []):
                        typ = rec.get("type")
                        ts = rec.get("timestamp", "")
                        model_info = rec.get("model", {}) or {}
                        model = model_info.get("model", model_info.get("name", "Unknown"))
                        ticker = rec.get("ticker", "")
                        if typ == "model_request":
                            prompt = (rec.get("data", {}) or {}).get("full_prompt") or (rec.get("data", {}) or {}).get("prompt_preview") or ""
                            lines.append(f"[{ts}] REQUEST | model={model} ticker={ticker}\n{prompt}\n")
                        elif typ == "model_response":
                            resp = (rec.get("data", {}) or {}).get("full_response") or (rec.get("data", {}) or {}).get("response_preview") or ""
                            lines.append(f"[{ts}] RESPONSE | model={model} ticker={ticker}\n{resp}\n")
                    self._item_payload[parent_iid] = {"combined": "\n".join(lines)}
                else:
                    for conv in convs:
                        req = conv.get("request") or {}
                        resp = conv.get("response") or {}
                        model_info = (req.get("model") or resp.get("model") or {})
                        model = model_info.get("model", model_info.get("name", "Unknown"))
                        ticker = req.get("ticker") or resp.get("ticker") or ""
                        ts = resp.get("timestamp") or req.get("timestamp") or ""
                        preview = ((resp.get("data", {}) or {}).get("response_preview") or
                                   (req.get("data", {}) or {}).get("prompt_preview") or "")
                        iid = self.tree.insert(parent_iid, tk.END, values=(ts, "PAIR", agent, model, ticker, preview))
                        # store full content for selection
                        self._item_payload[iid] = {
                            "request": (req.get("data", {}) or {}).get("full_prompt") or (req.get("data", {}) or {}).get("prompt_preview") or "",
                            "response": (resp.get("data", {}) or {}).get("full_response") or (resp.get("data", {}) or {}).get("response_preview") or "",
                        }
            self._rows = []

        # Clear detail views
        try:
            self._set_text(self.prompt_text, "")
            self._set_text(self.response_text, "")
        except Exception:
            pass

    def _on_select(self, _evt=None):
        sel = self.tree.selection()
        if not sel:
            return
        item = sel[0]
        payload = getattr(self, "_item_payload", {}).get(item)
        if payload is not None:
            # Grouped mode conversation selected
            if "combined" in payload:
                # Show consolidated transcript in response panel with colors
                self._set_text(self.prompt_text, "")
                self._set_transcript(self.response_text, payload.get("combined", ""))
            else:
                self._set_text(self.prompt_text, payload.get("request", ""))
                self._set_text(self.response_text, payload.get("response", ""))
            return
        # Fallback: flat mode behavior
        idx = self.tree.index(item)
        if 0 <= idx < len(getattr(self, "_rows", [])):
            row = self._rows[idx]
            raw = row.get("raw", {})
            typ = raw.get("type")
            data = raw.get("data", {}) or {}
            if typ == "model_request":
                prompt = data.get("full_prompt") or data.get("prompt_preview") or ""
                self._set_text(self.prompt_text, prompt)
                self._set_text(self.response_text, "")
            else:
                response = data.get("full_response") or data.get("response_preview") or ""
                self._set_text(self.response_text, response)
                self._set_text(self.prompt_text, "")

    def _set_text(self, widget: tk.Text, content: str):
        try:
            widget.configure(state=tk.NORMAL)
            widget.delete("1.0", tk.END)
            widget.insert(tk.END, content)
            widget.configure(state=tk.DISABLED)
        except Exception:
            pass
