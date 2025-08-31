#!/usr/bin/env python3
"""
AI Hedge Fund Log Viewer
Simple tool to view and analyze JSONL logs in a human-readable format.
"""

import json
import sys
import argparse
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional


class LogViewer:
    """Simple log viewer for JSONL files"""
    
    def __init__(self):
        self.emoji_map = {
            "agent_start": "🤖",
            "agent_end": "✅", 
            "model_request": "🧠",
            "model_response": "💭",
            "data_fetch": "📊",
            "decision": "🎯",
            "error": "❌",
            "system": "⚙️"
        }
        
        self.level_colors = {
            "DEBUG": "\033[36m",    # Cyan
            "INFO": "\033[32m",     # Green
            "WARNING": "\033[33m",  # Yellow
            "ERROR": "\033[31m",    # Red
            "CRITICAL": "\033[35m"  # Magenta
        }
        self.reset_color = "\033[0m"
    
    def load_logs(self, file_path: str) -> List[Dict[str, Any]]:
        """Load logs from JSONL file"""
        logs = []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if line:
                        try:
                            log_entry = json.loads(line)
                            logs.append(log_entry)
                        except json.JSONDecodeError as e:
                            print(f"Warning: Invalid JSON on line {line_num}: {e}")
        except FileNotFoundError:
            print(f"Error: Log file not found: {file_path}")
            return []
        except Exception as e:
            print(f"Error reading log file: {e}")
            return []
        
        return logs
    
    def filter_logs(self, logs: List[Dict], 
                   agent: Optional[str] = None,
                   level: Optional[str] = None,
                   event_type: Optional[str] = None,
                   ticker: Optional[str] = None,
                   last_n: Optional[int] = None) -> List[Dict]:
        """Filter logs based on criteria"""
        filtered = logs
        
        if agent:
            filtered = [log for log in filtered if log.get('agent', '').lower() == agent.lower()]
        
        if level:
            filtered = [log for log in filtered if log.get('level', '').upper() == level.upper()]
        
        if event_type:
            filtered = [log for log in filtered if log.get('type', '').lower() == event_type.lower()]
        
        if ticker:
            filtered = [log for log in filtered if log.get('ticker', '').upper() == ticker.upper()]
        
        if last_n:
            filtered = filtered[-last_n:]
        
        return filtered
    
    def format_timestamp(self, timestamp_str: str) -> str:
        """Format timestamp for display"""
        try:
            dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            return dt.strftime('%H:%M:%S')
        except:
            return timestamp_str[:8] if len(timestamp_str) > 8 else timestamp_str
    
    def format_log_entry(self, log: Dict[str, Any], show_details: bool = False) -> str:
        """Format a single log entry for display"""
        # Basic info
        timestamp = self.format_timestamp(log.get('timestamp', ''))
        level = log.get('level', 'INFO')
        event_type = log.get('type', 'unknown')
        agent = log.get('agent', 'Unknown')
        message = log.get('message', '')
        ticker = log.get('ticker', '')
        
        # Colors and emoji
        emoji = self.emoji_map.get(event_type, "📝")
        color = self.level_colors.get(level, "")
        
        # Build main line
        parts = [f"[{timestamp}]", emoji]
        
        if ticker:
            parts.append(f"[{ticker}]")
        
        parts.append(f"{color}{agent}{self.reset_color}")
        parts.append(f"→ {message}")
        
        # Add duration if available
        if 'duration_ms' in log:
            duration = log['duration_ms']
            if duration > 1000:
                parts.append(f"({duration/1000:.1f}s)")
            else:
                parts.append(f"({duration:.0f}ms)")
        
        main_line = " ".join(parts)
        
        if not show_details:
            return main_line
        
        # Add details
        details = []
        
        # Model info
        if 'model' in log:
            model_info = log['model']
            if isinstance(model_info, dict):
                model_name = model_info.get('model', model_info.get('name', 'Unknown'))
                details.append(f"    Model: {model_name}")
                
                if 'prompt_length' in model_info:
                    details.append(f"    Prompt: {model_info['prompt_length']} chars")
                
                if 'response_length' in model_info:
                    details.append(f"    Response: {model_info['response_length']} chars")
        
        # Data info
        if 'data' in log:
            data = log['data']
            if isinstance(data, dict):
                if 'data_type' in data:
                    details.append(f"    Data Type: {data['data_type']}")
                
                if 'count' in data:
                    details.append(f"    Count: {data['count']}")
                
                if 'signal' in data:
                    signal = data['signal']
                    confidence = data.get('confidence', 0)
                    details.append(f"    Decision: {signal.upper()} (confidence: {confidence:.1f}%)")
        
        # Error info
        if 'error' in log:
            error_info = log['error']
            if isinstance(error_info, dict):
                error_msg = error_info.get('message', error_info.get('details', str(error_info)))
                details.append(f"    Error: {error_msg}")
        
        if details:
            return main_line + "\n" + "\n".join(details)
        else:
            return main_line
    
    def display_logs(self, logs: List[Dict], show_details: bool = False):
        """Display logs in formatted output"""
        if not logs:
            print("No logs found matching the criteria.")
            return
        
        print(f"\n📋 Showing {len(logs)} log entries:\n")
        
        for log in logs:
            print(self.format_log_entry(log, show_details))
        
        print()
    
    def show_summary(self, logs: List[Dict]):
        """Show summary statistics"""
        if not logs:
            return
        
        # Count by type
        type_counts = {}
        level_counts = {}
        agent_counts = {}
        
        for log in logs:
            event_type = log.get('type', 'unknown')
            level = log.get('level', 'INFO')
            agent = log.get('agent', 'Unknown')
            
            type_counts[event_type] = type_counts.get(event_type, 0) + 1
            level_counts[level] = level_counts.get(level, 0) + 1
            agent_counts[agent] = agent_counts.get(agent, 0) + 1
        
        print("📊 Log Summary:")
        print(f"   Total entries: {len(logs)}")
        
        print("\n   By Event Type:")
        for event_type, count in sorted(type_counts.items()):
            emoji = self.emoji_map.get(event_type, "📝")
            print(f"     {emoji} {event_type}: {count}")
        
        print("\n   By Level:")
        for level, count in sorted(level_counts.items()):
            color = self.level_colors.get(level, "")
            print(f"     {color}{level}{self.reset_color}: {count}")
        
        print("\n   By Agent:")
        for agent, count in sorted(agent_counts.items()):
            print(f"     🤖 {agent}: {count}")
        
        print()


def main():
    parser = argparse.ArgumentParser(description="View AI Hedge Fund JSONL logs")
    parser.add_argument("file", nargs="?", help="JSONL log file path")
    parser.add_argument("--agent", "-a", help="Filter by agent name")
    parser.add_argument("--level", "-l", help="Filter by log level")
    parser.add_argument("--type", "-t", help="Filter by event type")
    parser.add_argument("--ticker", "-k", help="Filter by ticker")
    parser.add_argument("--last", "-n", type=int, help="Show last N entries")
    parser.add_argument("--details", "-d", action="store_true", help="Show detailed information")
    parser.add_argument("--summary", "-s", action="store_true", help="Show summary statistics")
    parser.add_argument("--find", "-f", action="store_true", help="Auto-find log files")
    
    args = parser.parse_args()
    
    viewer = LogViewer()
    
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
            print(f"Found log file: {log_file}")
        else:
            print("Multiple log files found:")
            for i, f in enumerate(log_files):
                print(f"  {i+1}. {f}")
            
            try:
                choice = int(input("Select file number: ")) - 1
                log_file = log_files[choice]
            except (ValueError, IndexError):
                print("Invalid selection.")
                return
    else:
        log_file = Path(args.file)
    
    # Load and filter logs
    logs = viewer.load_logs(str(log_file))
    if not logs:
        return
    
    filtered_logs = viewer.filter_logs(
        logs,
        agent=args.agent,
        level=args.level,
        event_type=args.type,
        ticker=args.ticker,
        last_n=args.last
    )
    
    # Display results
    if args.summary:
        viewer.show_summary(filtered_logs)
    else:
        viewer.display_logs(filtered_logs, show_details=args.details)


if __name__ == "__main__":
    main()