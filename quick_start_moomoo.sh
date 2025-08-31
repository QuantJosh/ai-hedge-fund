#!/bin/bash

# AI Hedge Fund Moomoo Integration Quick Start Script

echo "🚀 AI Hedge Fund Moomoo Integration Quick Start"
echo "=============================================="

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

echo "✅ Python 3 found: $(python3 --version)"

# Check if pip is installed
if ! command -v pip3 &> /dev/null; then
    echo "❌ pip3 is not installed. Please install pip."
    exit 1
fi

echo "✅ pip3 found"

# Install requirements
echo ""
echo "📦 Installing Python dependencies..."
pip3 install -r requirements_moomoo.txt

if [ $? -ne 0 ]; then
    echo "❌ Failed to install dependencies"
    exit 1
fi

echo "✅ Dependencies installed successfully"

# Check if Moomoo OpenD is running
echo ""
echo "🔍 Checking Moomoo OpenD connection..."
python3 -c "
import socket
try:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(3)
    result = sock.connect_ex(('127.0.0.1', 11111))
    sock.close()
    if result == 0:
        print('✅ Moomoo OpenD is running on port 11111')
    else:
        print('⚠️ Moomoo OpenD is not running on port 11111')
        print('   Please start Moomoo OpenD before running the integration')
except Exception as e:
    print(f'❌ Error checking Moomoo OpenD: {e}')
"

# Test Moomoo integration
echo ""
echo "🧪 Testing Moomoo integration..."
python3 test_moomoo_integration.py

if [ $? -eq 0 ]; then
    echo ""
    echo "🎉 Setup completed successfully!"
    echo ""
    echo "📋 Next steps:"
    echo "1. Edit config_moomoo.yaml to customize your settings"
    echo "2. Run: python3 run_with_moomoo.py --test-connection"
    echo "3. Run: python3 run_with_moomoo.py --config config_moomoo.yaml"
    echo ""
    echo "📚 For detailed documentation, see: docs/MOOMOO_INTEGRATION.md"
else
    echo ""
    echo "⚠️ Setup completed with warnings. Please check the test results above."
    echo ""
    echo "🔧 Troubleshooting:"
    echo "1. Make sure Moomoo OpenD is running"
    echo "2. Check your Moomoo account login status"
    echo "3. Verify paper trading is enabled"
fi