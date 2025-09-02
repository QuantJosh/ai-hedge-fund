#!/usr/bin/env python3
"""
Moomoo OpenD Launcher
Starts Moomoo OpenD and verifies connection for simulation trading
"""

import os
import sys
import time
import signal
import socket
import subprocess
from pathlib import Path


def check_port_open(host="127.0.0.1", port=11111, timeout=3):
    """Check if Moomoo OpenD port is open"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except:
        return False


def find_moomoo_executable():
    """Find Moomoo OpenD executable"""
    possible_paths = [
        "src/brokers/moomoo_OpenD-GUI_9.4.5408_Windows.exe",
        "src/brokers/moomoo_OpenD-GUI_9.4.5408_Windows/$PLUGINSDIR/moomoo_OpenD.exe",
        "src/brokers/moomoo_OpenD-GUI_9.4.5408_Windows/$PLUGINSDIR/open-d/windows/OpenD.exe"
    ]
    
    for path in possible_paths:
        full_path = Path(path)
        if full_path.exists():
            return full_path
    
    return None


def start_moomoo_opend():
    """Start Moomoo OpenD"""
    print("🚀 Starting Moomoo OpenD...")
    
    # Check if already running
    if check_port_open():
        print("✅ Moomoo OpenD is already running on port 11111")
        return True
    
    # Find executable
    exe_path = find_moomoo_executable()
    if not exe_path:
        print("❌ Moomoo OpenD executable not found")
        print("   Please make sure Moomoo OpenD is installed in src/brokers/")
        return False
    
    print(f"📁 Found Moomoo OpenD: {exe_path}")
    
    try:
        # Start Moomoo OpenD
        print("🔄 Launching Moomoo OpenD...")
        
        # Use the installer first if it's the main exe
        if exe_path.name.endswith("Windows.exe"):
            print("📦 Running Moomoo OpenD installer...")
            print("   Please follow the installation wizard")
            print("   Choose a location and complete the installation")
            
            subprocess.Popen([str(exe_path)], shell=True)
            
            print("\n⏳ Waiting for installation to complete...")
            print("   After installation, please:")
            print("   1. Launch Moomoo OpenD from the installed location")
            print("   2. Log in with your Moomoo account")
            print("   3. Make sure you're using PAPER TRADING mode")
            print("   4. Then run this script again")
            
            return False
        else:
            # Direct executable
            subprocess.Popen([str(exe_path)], shell=True)
        
        # Wait for startup
        print("⏳ Waiting for Moomoo OpenD to start...")
        
        for i in range(30):  # Wait up to 30 seconds
            if check_port_open():
                print("✅ Moomoo OpenD started successfully!")
                return True
            
            print(f"   Waiting... ({i+1}/30)")
            time.sleep(1)
        
        print("❌ Moomoo OpenD failed to start within 30 seconds")
        print("   Please start it manually and ensure it's running on port 11111")
        return False
        
    except Exception as e:
        print(f"❌ Error starting Moomoo OpenD: {e}")
        return False


def verify_moomoo_connection():
    """Verify Moomoo OpenD connection and setup"""
    print("\n🔍 Verifying Moomoo OpenD connection...")
    
    if not check_port_open():
        print("❌ Moomoo OpenD is not running on port 11111")
        return False
    
    print("✅ Moomoo OpenD is running on port 11111")
    
    # Test API connection
    try:
        sys.path.append(str(Path(__file__).parent / "src"))
        from src.brokers.moomoo import create_moomoo_trading
        
        print("🔌 Testing API connection...")
        
        trading = create_moomoo_trading()
        if trading.connect():
            account_info = trading.get_account_info()
            
            if account_info:
                print("✅ Successfully connected to Moomoo API")
                print(f"   💰 Account Balance: ${account_info.cash:,.2f}")
                print(f"   📊 Total Assets: ${account_info.total_assets:,.2f}")
                print(f"   💱 Currency: {account_info.currency}")
                
                # Verify paper trading
                if trading.config.paper_trading:
                    print("✅ Confirmed: Using PAPER TRADING mode")
                else:
                    print("⚠️  WARNING: Not in paper trading mode!")
                    print("   Please switch to paper trading in Moomoo OpenD")
                
                trading.disconnect()
                return True
            else:
                print("❌ Failed to get account information")
                print("   Please make sure you're logged in to Moomoo OpenD")
                trading.disconnect()
                return False
        else:
            print("❌ Failed to connect to Moomoo API")
            return False
            
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("   Please make sure moomoo-api is installed: pip install moomoo-api")
        return False
    except Exception as e:
        print(f"❌ Connection test failed: {e}")
        return False


def signal_handler(signum, frame):
    """Handle Ctrl+C gracefully"""
    print("\n⚠️ Startup interrupted by user (Ctrl+C)")
    print("👋 Goodbye!")
    sys.exit(1)

def main():
    """Main function"""
    # Set up signal handler
    signal.signal(signal.SIGINT, signal_handler)
    
    print("🤖 Moomoo OpenD Launcher for AI Hedge Fund")
    print("=" * 50)
    print("⚠️  This will start Moomoo OpenD for PAPER TRADING")
    print("=" * 50)
    
    # Step 1: Start Moomoo OpenD
    if not start_moomoo_opend():
        print("\n❌ Failed to start Moomoo OpenD")
        print("\n📋 Manual Setup Instructions:")
        print("1. Install and start Moomoo OpenD manually")
        print("2. Log in with your Moomoo account")
        print("3. Switch to PAPER TRADING mode")
        print("4. Ensure OpenD API is enabled on port 11111")
        print("5. Run this script again to verify connection")
        return False
    
    # Step 2: Verify connection
    if verify_moomoo_connection():
        print("\n🎉 Moomoo OpenD is ready for simulation trading!")
        print("\n📋 Next Steps:")
        print("1. Run: python test_simulation_trading.py")
        print("2. Run: python run_simulation_trading.py")
        return True
    else:
        print("\n❌ Moomoo OpenD connection verification failed")
        print("\n🔧 Troubleshooting:")
        print("1. Make sure Moomoo OpenD is running")
        print("2. Check that you're logged in")
        print("3. Verify paper trading mode is enabled")
        print("4. Ensure API access is enabled on port 11111")
        return False


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        signal_handler(None, None)