@echo off
echo Starting Moomoo OpenD...
echo Please wait while the application launches...

cd /d "%~dp0"
start "" "src\brokers\moomoo_OpenD-GUI_9.4.5408_Windows\$PLUGINSDIR\moomoo_OpenD.exe"

echo Moomoo OpenD is starting...
echo Please:
echo 1. Log in with your Moomoo account
echo 2. Switch to PAPER TRADING mode
echo 3. Enable API access on port 11111
echo 4. Then run: python test_simulation_trading.py

pause