"""
AI Hedge Fund Logging System
Records all agent and model interactions with structured, readable logs.
"""

import json
import logging
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, asdict
from enum import Enum


class LogLevel(Enum):
    """Log levels for different types of events"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class EventType(Enum):
    """Types of events to log"""
    AGENT_START = "AGENT_START"
    AGENT_END = "AGENT_END"
    MODEL_REQUEST = "MODEL_REQUEST"
    MODEL_RESPONSE = "MODEL_RESPONSE"
    DATA_FETCH = "DATA_FETCH"
    DECISION = "DECISION"
    ERROR = "ERROR"
    SYSTEM = "SYSTEM"


@dataclass
class LogEntry:
    """Structured log entry"""
    timestamp: str
    session_id: str
    event_type: EventType
    level: LogLevel
    agent_name: str
    ticker: Optional[str]
    message: str
    data: Optional[Dict[str, Any]] = None
    duration_ms: Optional[float] = None
    model_info: Optional[Dict[str, str]] = None
    error_info: Optional[Dict[str, str]] = None


class AIHedgeFundLogger:
    """Main logging system for AI Hedge Fund"""
    
    def __init__(self, 
                 log_dir: str = "logs",
                 session_id: Optional[str] = None,
                 enable_console: bool = True,
                 enable_file: bool = True,
                 enable_json: bool = True,
                 console_format: str = "human",  # "human" or "json"
                 console_level: str = "INFO"):
        
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        
        self.session_id = session_id or self._generate_session_id()
        self.enable_console = enable_console
        self.enable_file = enable_file
        self.enable_json = enable_json
        self.console_format = console_format  # "human" or "json"
        self.console_level = getattr(logging, console_level.upper(), logging.INFO)
        
        # Create session directory
        self.session_dir = self.log_dir / self.session_id
        self.session_dir.mkdir(exist_ok=True)
        
        # Initialize loggers
        self._setup_loggers()
        
        # Track active operations
        self._active_operations: Dict[str, float] = {}
        
        # Log session start
        self.log_system("Logging session started", {
            "session_id": self.session_id,
            "log_directory": str(self.session_dir)
        })
    
    def _generate_session_id(self) -> str:
        """Generate unique session ID"""
        return datetime.now().strftime("%Y%m%d_%H%M%S")
    
    def _setup_loggers(self):
        """Setup different types of loggers"""
        
        # Console logger with enhanced formatting
        if self.enable_console:
            self.console_logger = logging.getLogger(f"hedge_fund_console_{self.session_id}")
            self.console_logger.setLevel(self.console_level)
            
            if not self.console_logger.handlers:
                console_handler = logging.StreamHandler()
                if self.console_format == "human":
                    # Human-readable format with emojis
                    console_formatter = logging.Formatter(
                        '[%(asctime)s] %(message)s',
                        datefmt='%H:%M:%S'
                    )
                else:
                    # JSON format for console (if needed)
                    console_formatter = logging.Formatter('%(message)s')
                console_handler.setFormatter(console_formatter)
                self.console_logger.addHandler(console_handler)
        
        # File logger
        if self.enable_file:
            self.file_logger = logging.getLogger(f"hedge_fund_file_{self.session_id}")
            self.file_logger.setLevel(logging.DEBUG)
            
            if not self.file_logger.handlers:
                file_handler = logging.FileHandler(
                    self.session_dir / "hedge_fund.log", 
                    encoding='utf-8'
                )
                file_formatter = logging.Formatter(
                    '%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S'
                )
                file_handler.setFormatter(file_formatter)
                self.file_logger.addHandler(file_handler)
        
        # JSON logger for structured data
        if self.enable_json:
            self.json_log_file = self.session_dir / "structured_log.jsonl"
    
    def _create_log_entry(self,
                         event_type: EventType,
                         level: LogLevel,
                         agent_name: str,
                         message: str,
                         ticker: Optional[str] = None,
                         data: Optional[Dict[str, Any]] = None,
                         duration_ms: Optional[float] = None,
                         model_info: Optional[Dict[str, str]] = None,
                         error_info: Optional[Dict[str, str]] = None) -> LogEntry:
        """Create a structured log entry"""
        
        return LogEntry(
            timestamp=datetime.now().isoformat(),
            session_id=self.session_id,
            event_type=event_type,
            level=level,
            agent_name=agent_name,
            ticker=ticker,
            message=message,
            data=data,
            duration_ms=duration_ms,
            model_info=model_info,
            error_info=error_info
        )
    
    def _write_log(self, entry: LogEntry):
        """Write log entry to all enabled outputs"""
        
        # Console logging
        if self.enable_console and self.console_logger:
            log_level = getattr(logging, entry.level.value)
            
            if self.console_format == "human":
                # Human-readable format with emojis
                display_message = self._format_display_message(entry)
                self.console_logger.log(log_level, display_message)
            else:
                # JSON format for console
                json_data = self._prepare_json_data(entry)
                self.console_logger.log(log_level, json.dumps(json_data, ensure_ascii=False))
        
        # File logging
        if self.enable_file and self.file_logger:
            log_level = getattr(logging, entry.level.value)
            detailed_message = self._format_detailed_message(entry)
            self.file_logger.log(log_level, detailed_message)
        
        # JSON logging
        if self.enable_json:
            self._write_json_log(entry)
    
    def _format_display_message(self, entry: LogEntry) -> str:
        """Format message for console display with emojis and colors"""
        # Event type emojis
        emoji_map = {
            EventType.AGENT_START: "🤖",
            EventType.AGENT_END: "✅",
            EventType.MODEL_REQUEST: "🧠",
            EventType.MODEL_RESPONSE: "💭",
            EventType.DATA_FETCH: "📊",
            EventType.DECISION: "🎯",
            EventType.ERROR: "❌",
            EventType.SYSTEM: "⚙️"
        }
        
        emoji = emoji_map.get(entry.event_type, "📝")
        
        # Build readable message
        parts = [emoji]
        
        if entry.ticker:
            parts.append(f"[{entry.ticker}]")
        
        parts.append(f"{entry.agent_name}")
        
        # Customize message based on event type
        if entry.event_type == EventType.MODEL_REQUEST and entry.model_info:
            model = entry.model_info.get('model', 'Unknown')
            prompt_len = entry.model_info.get('prompt_length', 0)
            parts.append(f"→ {model} 调用 (提示词: {prompt_len}字符)")
            
        elif entry.event_type == EventType.MODEL_RESPONSE and entry.model_info:
            model = entry.model_info.get('model', 'Unknown')
            response_len = entry.model_info.get('response_length', 0)
            duration_text = f" 耗时:{entry.duration_ms:.1f}ms" if entry.duration_ms else ""
            parts.append(f"→ {model} 响应 (长度: {response_len}字符{duration_text})")
            
        elif entry.event_type == EventType.DATA_FETCH and entry.data:
            data_type = entry.data.get('data_type', '数据')
            count = entry.data.get('count', 0)
            status = "成功" if "successful" in entry.message else "失败"
            parts.append(f"→ {data_type} {status} ({count}条记录)" if count else f"→ {data_type} {status}")
            
        elif entry.event_type == EventType.DECISION and entry.data:
            signal = entry.data.get('signal', '').upper()
            confidence = entry.data.get('confidence', 0)
            parts.append(f"→ 决策: {signal} (置信度: {confidence:.1f}%)")
            
        elif entry.event_type == EventType.AGENT_START:
            parts.append("→ 开始分析")
            
        elif entry.event_type == EventType.AGENT_END:
            duration_text = f" (耗时: {entry.duration_ms/1000:.1f}秒)" if entry.duration_ms else ""
            parts.append(f"→ 分析完成{duration_text}")
            
        else:
            parts.append(f"→ {entry.message}")
        
        return " ".join(parts)
    
    def _format_detailed_message(self, entry: LogEntry) -> str:
        """Format detailed message for file logging"""
        parts = [
            f"Event: {entry.event_type.value}",
            f"Agent: {entry.agent_name}",
        ]
        
        if entry.ticker:
            parts.append(f"Ticker: {entry.ticker}")
        
        parts.append(f"Message: {entry.message}")
        
        if entry.duration_ms:
            parts.append(f"Duration: {entry.duration_ms:.1f}ms")
        
        if entry.model_info:
            parts.append(f"Model: {entry.model_info}")
        
        return " | ".join(parts)
    
    def _prepare_json_data(self, entry: LogEntry) -> Dict[str, Any]:
        """Prepare optimized JSON data structure"""
        json_data = {
            "timestamp": entry.timestamp,
            "session_id": entry.session_id,
            "type": entry.event_type.value.lower(),
            "level": entry.level.value,
            "agent": entry.agent_name,
            "message": entry.message
        }
        
        # Add optional fields only if they exist
        if entry.ticker:
            json_data["ticker"] = entry.ticker
            
        if entry.duration_ms is not None:
            json_data["duration_ms"] = round(entry.duration_ms, 2)
            
        if entry.model_info:
            json_data["model"] = entry.model_info
            
        if entry.data:
            json_data["data"] = entry.data
            
        if entry.error_info:
            json_data["error"] = entry.error_info
            
        return json_data
    
    def _write_json_log(self, entry: LogEntry):
        """Write structured log entry to JSONL file"""
        try:
            with open(self.json_log_file, 'a', encoding='utf-8') as f:
                json_data = self._prepare_json_data(entry)
                f.write(json.dumps(json_data, ensure_ascii=False, separators=(',', ':')) + '\n')
        except Exception as e:
            print(f"Error writing JSON log: {e}")
    
    # Public logging methods
    
    def log_agent_start(self, agent_name: str, ticker: Optional[str] = None, data: Optional[Dict] = None):
        """Log agent execution start"""
        operation_key = f"{agent_name}_{ticker or 'all'}"
        self._active_operations[operation_key] = time.time()
        
        entry = self._create_log_entry(
            event_type=EventType.AGENT_START,
            level=LogLevel.INFO,
            agent_name=agent_name,
            ticker=ticker,
            message="Agent execution started",
            data=data
        )
        self._write_log(entry)
    
    def log_agent_end(self, agent_name: str, ticker: Optional[str] = None, result: Optional[Dict] = None):
        """Log agent execution end"""
        operation_key = f"{agent_name}_{ticker or 'all'}"
        duration_ms = None
        
        if operation_key in self._active_operations:
            duration_ms = (time.time() - self._active_operations[operation_key]) * 1000
            del self._active_operations[operation_key]
        
        entry = self._create_log_entry(
            event_type=EventType.AGENT_END,
            level=LogLevel.INFO,
            agent_name=agent_name,
            ticker=ticker,
            message="Agent execution completed",
            data=result,
            duration_ms=duration_ms
        )
        self._write_log(entry)
    
    def log_model_request(self, agent_name: str, model_provider: str, model_name: str, 
                         prompt: str, ticker: Optional[str] = None):
        """Log model API request"""
        entry = self._create_log_entry(
            event_type=EventType.MODEL_REQUEST,
            level=LogLevel.DEBUG,
            agent_name=agent_name,
            ticker=ticker,
            message="Model API request sent",
            model_info={
                "provider": model_provider,
                "model": model_name,
                "prompt_length": len(prompt)
            },
            data={
                "prompt_preview": prompt[:200] + "..." if len(prompt) > 200 else prompt,
                "full_prompt": prompt,  # 保存完整的prompt
                "prompt_lines": len(prompt.split('\n')) if prompt else 0
            }
        )
        self._write_log(entry)
    
    def log_model_response(self, agent_name: str, model_provider: str, model_name: str,
                          response: str, ticker: Optional[str] = None, duration_ms: Optional[float] = None):
        """Log model API response"""
        entry = self._create_log_entry(
            event_type=EventType.MODEL_RESPONSE,
            level=LogLevel.DEBUG,
            agent_name=agent_name,
            ticker=ticker,
            message="Model API response received",
            model_info={
                "provider": model_provider,
                "model": model_name,
                "response_length": len(response)
            },
            data={
                "response_preview": response[:200] + "..." if len(response) > 200 else response,
                "full_response": response,  # 保存完整的响应
                "response_lines": len(response.split('\n')) if response else 0
            },
            duration_ms=duration_ms
        )
        self._write_log(entry)
    
    def log_data_fetch(self, agent_name: str, data_type: str, ticker: str, 
                      success: bool, count: Optional[int] = None, error: Optional[str] = None):
        """Log data fetching operations"""
        message = f"Data fetch {'successful' if success else 'failed'}: {data_type}"
        if count is not None:
            message += f" ({count} items)"
        
        entry = self._create_log_entry(
            event_type=EventType.DATA_FETCH,
            level=LogLevel.INFO if success else LogLevel.WARNING,
            agent_name=agent_name,
            ticker=ticker,
            message=message,
            data={"data_type": data_type, "count": count},
            error_info={"error": error} if error else None
        )
        self._write_log(entry)
    
    def log_decision(self, agent_name: str, ticker: str, signal: str, confidence: float, reasoning: str):
        """Log trading decision"""
        entry = self._create_log_entry(
            event_type=EventType.DECISION,
            level=LogLevel.INFO,
            agent_name=agent_name,
            ticker=ticker,
            message=f"Decision: {signal.upper()} (confidence: {confidence:.1f}%)",
            data={
                "signal": signal,
                "confidence": confidence,
                "reasoning": reasoning[:500] + "..." if len(reasoning) > 500 else reasoning
            }
        )
        self._write_log(entry)
    
    def log_error(self, agent_name: str, error_message: str, ticker: Optional[str] = None, 
                 exception: Optional[Exception] = None):
        """Log error events"""
        error_info = {"message": error_message}
        if exception:
            error_info.update({
                "type": type(exception).__name__,
                "details": str(exception)
            })
        
        entry = self._create_log_entry(
            event_type=EventType.ERROR,
            level=LogLevel.ERROR,
            agent_name=agent_name,
            ticker=ticker,
            message=f"Error: {error_message}",
            error_info=error_info
        )
        self._write_log(entry)
    
    def log_system(self, message: str, data: Optional[Dict] = None):
        """Log system-level events"""
        entry = self._create_log_entry(
            event_type=EventType.SYSTEM,
            level=LogLevel.INFO,
            agent_name="SYSTEM",
            message=message,
            data=data
        )
        self._write_log(entry)
    
    def get_session_summary(self) -> Dict[str, Any]:
        """Get summary of current session"""
        summary = {
            "session_id": self.session_id,
            "log_directory": str(self.session_dir),
            "active_operations": len(self._active_operations),
            "files": {
                "main_log": str(self.session_dir / "hedge_fund.log"),
                "structured_log": str(self.json_log_file),
                "summary": str(self.session_dir / "session_summary.json")
            }
        }
        
        # Save summary to file
        try:
            with open(self.session_dir / "session_summary.json", 'w', encoding='utf-8') as f:
                json.dump(summary, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving session summary: {e}")
        
        return summary
    
    def close(self):
        """Close logging session"""
        self.log_system("Logging session ended")
        
        # Close handlers
        if hasattr(self, 'console_logger'):
            for handler in self.console_logger.handlers[:]:
                handler.close()
                self.console_logger.removeHandler(handler)
        
        if hasattr(self, 'file_logger'):
            for handler in self.file_logger.handlers[:]:
                handler.close()
                self.file_logger.removeHandler(handler)
        
        # Generate session summary
        self.get_session_summary()


# Global logger instance
_global_logger: Optional[AIHedgeFundLogger] = None


def get_logger() -> AIHedgeFundLogger:
    """Get the global logger instance"""
    global _global_logger
    if _global_logger is None:
        _global_logger = AIHedgeFundLogger()
    return _global_logger


def init_logger(log_dir: str = "logs", 
               session_id: Optional[str] = None,
               enable_console: bool = True,
               enable_file: bool = True,
               enable_json: bool = True,
               console_format: str = "human",
               console_level: str = "INFO") -> AIHedgeFundLogger:
    """Initialize the global logger"""
    global _global_logger
    _global_logger = AIHedgeFundLogger(
        log_dir=log_dir,
        session_id=session_id,
        enable_console=enable_console,
        enable_file=enable_file,
        enable_json=enable_json,
        console_format=console_format,
        console_level=console_level
    )
    return _global_logger


def close_logger():
    """Close the global logger"""
    global _global_logger
    if _global_logger:
        _global_logger.close()
        _global_logger = None