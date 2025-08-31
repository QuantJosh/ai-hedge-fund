#!/usr/bin/env python3
"""
Pretty Log Formatter
Converts JSONL logs to human-readable format with colors and formatting.
"""

import json
import sys
import argparse
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional


class PrettyLogFormatter:
    """Format JSONL logs in a beautiful, readable way"""
    
    def __init__(self, use_colors: bool = True):
        self.use_colors = use_colors
        
        # Color codes
        self.colors = {
            'reset': '\033[0m',
            'bold': '\033[1m',
            'dim': '\033[2m',
            'red': '\033[31m',
            'green': '\033[32m',
            'yellow': '\033[33m',
            'blue': '\033[34m',
            'magenta': '\033[35m',
            'cyan': '\033[36m',
            'white': '\033[37m',
            'bg_red': '\033[41m',
            'bg_green': '\033[42m',
            'bg_yellow': '\033[43m',
        }
        
        # Event type styling
        self.event_styles = {
            'system': {'color': 'cyan', 'icon': '⚙️'},
            'agent_start': {'color': 'green', 'icon': '🚀'},
            'agent_end': {'color': 'green', 'icon': '✅'},
            'model_request': {'color': 'blue', 'icon': '🧠'},
            'model_response': {'color': 'magenta', 'icon': '💭'},
            'data_fetch': {'color': 'yellow', 'icon': '📊'},
            'decision': {'color': 'red', 'icon': '🎯'},
            'error': {'color': 'red', 'icon': '❌'},
        }
        
        # Level styling
        self.level_styles = {
            'DEBUG': {'color': 'dim', 'bg': None},
            'INFO': {'color': 'white', 'bg': None},
            'WARNING': {'color': 'yellow', 'bg': None},
            'ERROR': {'color': 'white', 'bg': 'bg_red'},
            'CRITICAL': {'color': 'white', 'bg': 'bg_red'},
        }
    
    def colorize(self, text: str, color: str = None, bg: str = None, bold: bool = False) -> str:
        """Apply colors to text"""
        if not self.use_colors:
            return text
        
        result = ""
        if bold:
            result += self.colors.get('bold', '')
        if bg:
            result += self.colors.get(bg, '')
        if color:
            result += self.colors.get(color, '')
        
        result += text
        if self.use_colors:
            result += self.colors.get('reset', '')
        
        return result
    
    def format_timestamp(self, timestamp_str: str) -> str:
        """Format timestamp for display"""
        try:
            dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            return dt.strftime('%H:%M:%S.%f')[:-3]  # Include milliseconds
        except:
            return timestamp_str
    
    def format_duration(self, duration_ms: float) -> str:
        """Format duration in a readable way"""
        if duration_ms >= 1000:
            return f"{duration_ms/1000:.1f}s"
        else:
            return f"{duration_ms:.0f}ms"
    
    def format_log_entry(self, log: Dict[str, Any], show_details: bool = True) -> str:
        """Format a single log entry beautifully"""
        # Extract basic info
        timestamp = self.format_timestamp(log.get('timestamp', ''))
        level = log.get('level', 'INFO')
        event_type = log.get('type', 'unknown')
        agent = log.get('agent', 'Unknown')
        message = log.get('message', '')
        ticker = log.get('ticker', '')
        
        # Get styling
        event_style = self.event_styles.get(event_type, {'color': 'white', 'icon': '📝'})
        level_style = self.level_styles.get(level, {'color': 'white', 'bg': None})
        
        # Build the main line
        parts = []
        
        # Timestamp
        parts.append(self.colorize(f"[{timestamp}]", 'dim'))
        
        # Level badge
        level_text = f" {level} "
        parts.append(self.colorize(level_text, level_style['color'], level_style['bg'], bold=True))
        
        # Event icon
        parts.append(event_style['icon'])
        
        # Ticker (if available)
        if ticker:
            parts.append(self.colorize(f"[{ticker}]", 'cyan', bold=True))
        
        # Agent name
        parts.append(self.colorize(agent, event_style['color'], bold=True))
        
        # Message
        parts.append("→")
        parts.append(self.colorize(message, 'white'))
        
        # Duration (if available)
        if 'duration_ms' in log:
            duration = self.format_duration(log['duration_ms'])
            parts.append(self.colorize(f"({duration})", 'dim'))
        
        main_line = " ".join(parts)
        
        if not show_details:
            return main_line
        
        # Add detailed information
        details = []
        
        # Model information
        if 'model' in log:
            model_info = log['model']
            if isinstance(model_info, dict):
                model_details = []
                
                provider = model_info.get('provider', 'Unknown')
                model_name = model_info.get('model', 'Unknown')
                if provider != 'Unknown' or model_name != 'Unknown':
                    model_details.append(f"Model: {provider}/{model_name}")
                
                if 'prompt_length' in model_info:
                    model_details.append(f"Prompt: {model_info['prompt_length']} chars")
                
                if 'response_length' in model_info:
                    model_details.append(f"Response: {model_info['response_length']} chars")
                
                if model_details:
                    details.append(self.colorize("    " + " | ".join(model_details), 'blue'))
        
        # Data information
        if 'data' in log:
            data = log['data']
            if isinstance(data, dict):
                data_details = []
                
                if 'data_type' in data:
                    data_details.append(f"Type: {data['data_type']}")
                
                if 'count' in data:
                    data_details.append(f"Count: {data['count']}")
                
                if 'signal' in data and 'confidence' in data:
                    signal = data['signal']
                    confidence = data['confidence']
                    data_details.append(f"Decision: {signal.upper()} ({confidence:.1f}%)")
                
                # Show preview of important data
                if 'prompt_preview' in data:
                    preview = data['prompt_preview'][:100] + "..." if len(str(data['prompt_preview'])) > 100 else data['prompt_preview']
                    data_details.append(f"Preview: {preview}")
                
                if 'response_preview' in data:
                    preview = data['response_preview'][:100] + "..." if len(str(data['response_preview'])) > 100 else data['response_preview']
                    data_details.append(f"Response: {preview}")
                
                if data_details:
                    details.append(self.colorize("    " + " | ".join(data_details), 'yellow'))
        
        # Error information
        if 'error' in log:
            error_info = log['error']
            if isinstance(error_info, dict):
                error_msg = error_info.get('message', error_info.get('details', str(error_info)))
                details.append(self.colorize(f"    ❌ Error: {error_msg}", 'red'))
        
        # Combine main line with details
        if details:
            return main_line + "\n" + "\n".join(details)
        else:
            return main_line
    
    def format_session_header(self, session_id: str, log_count: int) -> str:
        """Format session header"""
        header = f"📋 Session: {session_id} ({log_count} entries)"
        return self.colorize(header, 'cyan', bold=True)
    
    def format_separator(self) -> str:
        """Format separator line"""
        return self.colorize("─" * 80, 'dim')


def load_and_format_logs(file_path: str, 
                        show_details: bool = True,
                        filter_level: str = None,
                        filter_agent: str = None,
                        filter_type: str = None,
                        last_n: int = None,
                        use_colors: bool = True) -> None:
    """Load and format JSONL logs"""
    
    formatter = PrettyLogFormatter(use_colors=use_colors)
    
    try:
        logs = []
        with open(file_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if line:
                    try:
                        log_entry = json.loads(line)
                        logs.append(log_entry)
                    except json.JSONDecodeError as e:
                        print(f"Warning: Invalid JSON on line {line_num}: {e}")
        
        if not logs:
            print("No valid log entries found.")
            return
        
        # Apply filters
        filtered_logs = logs
        
        if filter_level:
            filtered_logs = [log for log in filtered_logs if log.get('level', '').upper() == filter_level.upper()]
        
        if filter_agent:
            filtered_logs = [log for log in filtered_logs if filter_agent.lower() in log.get('agent', '').lower()]
        
        if filter_type:
            filtered_logs = [log for log in filtered_logs if log.get('type', '').lower() == filter_type.lower()]
        
        if last_n:
            filtered_logs = filtered_logs[-last_n:]
        
        if not filtered_logs:
            print("No logs match the specified filters.")
            return
        
        # Display header
        session_id = logs[0].get('session_id', 'Unknown')
        print(formatter.format_session_header(session_id, len(filtered_logs)))
        print(formatter.format_separator())
        print()
        
        # Display logs
        for log in filtered_logs:
            print(formatter.format_log_entry(log, show_details))
            print()  # Add spacing between entries
        
        print(formatter.format_separator())
        
    except FileNotFoundError:
        print(f"Error: Log file not found: {file_path}")
    except Exception as e:
        print(f"Error reading log file: {e}")


def main():
    parser = argparse.ArgumentParser(description="Pretty format JSONL logs")
    parser.add_argument("file", nargs="?", help="JSONL log file path")
    parser.add_argument("--details", "-d", action="store_true", help="Show detailed information")
    parser.add_argument("--level", "-l", help="Filter by log level")
    parser.add_argument("--agent", "-a", help="Filter by agent name")
    parser.add_argument("--type", "-t", help="Filter by event type")
    parser.add_argument("--last", "-n", type=int, help="Show last N entries")
    parser.add_argument("--no-colors", action="store_true", help="Disable colors")
    parser.add_argument("--find", "-f", action="store_true", help="Auto-find log files")
    
    args = parser.parse_args()
    
    # Auto-find log files if requested or no file specified
    if args.find or not args.file:
        log_files = []
        
        # Look in common locations
        for pattern in ["logs/**/*.jsonl", "logs/*.jsonl", "*.jsonl"]:
            log_files.extend(Path(".").glob(pattern))
        
        if not log_files:
            print("No JSONL log files found.")
            return
        
        if len(log_files) == 1:
            log_file = log_files[0]
            print(f"📁 Found log file: {log_file}\n")
        else:
            print("📁 Multiple log files found:")
            for i, f in enumerate(log_files):
                print(f"  {i+1}. {f}")
            
            try:
                choice = int(input("\nSelect file number: ")) - 1
                log_file = log_files[choice]
                print()
            except (ValueError, IndexError):
                print("Invalid selection.")
                return
    else:
        log_file = Path(args.file)
    
    # Format and display logs
    load_and_format_logs(
        str(log_file),
        show_details=args.details,
        filter_level=args.level,
        filter_agent=args.agent,
        filter_type=args.type,
        last_n=args.last,
        use_colors=not args.no_colors
    )


if __name__ == "__main__":
    main()