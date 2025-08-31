@echo off
REM AI Hedge Fund Quick Runner (Windows)
REM Automated execution using preset configuration

echo AI Hedge Fund Quick Runner
echo ================================

REM Check if config file exists
if not exist "config.yaml" (
    echo Config file not found, creating default configuration...
    poetry run python run_with_config.py --create-config
    echo.
    echo Please edit config.yaml file to set your parameters:
    echo    - Stock tickers
    echo    - Date range (start_date, end_date)  
    echo    - AI analysts selection
    echo    - Model configuration
    echo.
    echo Run this script again after editing the config file
    pause
    exit /b 1
)

echo Found config file: config.yaml
echo.

REM Validate config file
echo Validating configuration...
poetry run python run_with_config.py --validate
if %errorlevel% neq 0 (
    echo.
    echo Configuration validation failed, please check your config
    pause
    exit /b 1
)

echo Configuration validation passed
echo.

REM Run AI Hedge Fund
echo Starting AI Hedge Fund execution...
echo.
poetry run python run_with_config.py

echo.
echo Execution completed!
echo Results saved in results/ directory
echo.
pause