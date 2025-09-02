#!/bin/bash

# AI Hedge Fund - Quick Start Simulation Trading
# This script sets up and runs the complete simulation trading workflow

echo "🚀 AI Hedge Fund - Simulation Trading Quick Start"
echo "=================================================="
echo "⚠️  PAPER TRADING ONLY - No real money will be used"
echo "=================================================="

# Check if Python is available
if ! command -v python &> /dev/null; then
    echo "❌ Python not found. Please install Python 3.8+"
    exit 1
fi

# Check if we're in the right directory
if [ ! -f "run_simulation_trading.py" ]; then
    echo "❌ Please run this script from the project root directory"
    exit 1
fi

# Check if Moomoo OpenD is running
echo "🔍 Checking Moomoo OpenD connection..."
if ! nc -z 127.0.0.1 11111 2>/dev/null; then
    echo "❌ Moomoo OpenD is not running on port 11111"
    echo "   Please start Moomoo OpenD and log into your paper trading account"
    echo "   Then run this script again"
    exit 1
fi

echo "✅ Moomoo OpenD detected"

# Install dependencies if needed
echo "📦 Checking dependencies..."
python -c "import moomoo" 2>/dev/null || {
    echo "📦 Installing moomoo-api..."
    pip install moomoo-api
}

# Run tests first
echo ""
echo "🧪 Running simulation trading tests..."
python test_simulation_trading.py

if [ $? -ne 0 ]; then
    echo "❌ Tests failed. Please check your Moomoo setup"
    exit 1
fi

echo ""
echo "✅ All tests passed!"
echo ""

# Ask user for confirmation
echo "🤔 Ready to run AI hedge fund simulation trading?"
echo "   This will:"
echo "   - Analyze market data using AI agents"
echo "   - Generate trading decisions"
echo "   - Execute trades on Moomoo PAPER TRADING account"
echo ""
read -p "Continue? (yes/no): " -r
echo

if [[ ! $REPLY =~ ^[Yy]([Ee][Ss])?$ ]]; then
    echo "❌ Simulation cancelled"
    exit 0
fi

# Run the simulation
echo "🚀 Starting simulation trading..."
echo ""

python run_simulation_trading.py "$@"

# Check result
if [ $? -eq 0 ]; then
    echo ""
    echo "🎉 Simulation completed successfully!"
    echo "📊 Check the results/ directory for detailed logs"
    echo "📈 Review your Moomoo paper trading account for executed trades"
else
    echo ""
    echo "❌ Simulation failed. Check the error messages above"
    exit 1
fi