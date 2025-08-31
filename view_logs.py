#!/usr/bin/env python3
"""
Quick Log Viewer Launcher
Provides multiple ways to view AI Hedge Fund logs in a readable format.
"""

import sys
import os
import subprocess
import webbrowser
from pathlib import Path


def main():
    print("🤖 AI Hedge Fund Log Viewer")
    print("=" * 40)
    print()
    print("Choose how you want to view your logs:")
    print()
    print("1. 🎨 Pretty Terminal View (Recommended)")
    print("2. 📊 HTML Interactive Viewer")
    print("3. 📋 Simple Text View")
    print("4. 🔍 Filter by Error Level")
    print("5. 📈 Show Statistics Only")
    print()
    
    try:
        choice = input("Enter your choice (1-5): ").strip()
        
        if choice == "1":
            # Pretty terminal view
            subprocess.run([sys.executable, "tools/pretty_logs.py", "--find", "--details"])
            
        elif choice == "2":
            # HTML viewer
            html_path = Path("tools/log_viewer.html").absolute()
            print(f"Opening HTML viewer: {html_path}")
            webbrowser.open(f"file://{html_path}")
            print("📁 Drag and drop your JSONL file into the browser window")
            
        elif choice == "3":
            # Simple text view
            subprocess.run([sys.executable, "tools/log_viewer.py", "--find"])
            
        elif choice == "4":
            # Error filter
            subprocess.run([sys.executable, "tools/pretty_logs.py", "--find", "--level", "ERROR", "--details"])
            
        elif choice == "5":
            # Statistics
            subprocess.run([sys.executable, "tools/log_viewer.py", "--find", "--summary"])
            
        else:
            print("Invalid choice. Please run the script again.")
            
    except KeyboardInterrupt:
        print("\n\nGoodbye! 👋")
    except Exception as e:
        print(f"\nError: {e}")


if __name__ == "__main__":
    main()