#!/usr/bin/env python3
"""
AI Hedge Fund Configuration Runner
Supports automated execution via YAML configuration file
"""

import yaml
import sys
import os
import json
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from pathlib import Path

# 添加src目录到Python路径
sys.path.append(str(Path(__file__).parent / "src"))

from src.main import run_hedge_fund, create_workflow
from src.backtester import Backtester
from src.utils.analysts import ANALYST_ORDER
from src.utils.display import print_trading_output, print_backtest_results
from src.utils.llm_logger import setup_logging


def load_config(config_path="config.yaml"):
    """Load configuration file"""
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        print(f"[SUCCESS] Configuration loaded: {config_path}")
        return config
    except FileNotFoundError:
        print(f"[ERROR] Configuration file not found: {config_path}")
        print("Please create config file or use --create-config to generate default")
        return None
    except yaml.YAMLError as e:
        print(f"[ERROR] Configuration file format error: {e}")
        return None


def create_default_config(config_path="config.yaml"):
    """Create default configuration file"""
    default_config = {
        "hedge_fund": {
            "tickers": ["AAPL"],
            "start_date": "",
            "end_date": "",
            "initial_cash": 100000.0,
            "margin_requirement": 0.0,
            "show_reasoning": False,
            "show_agent_graph": False
        },
        "analysts": {
            "selected": [
                "ben_graham",
                "warren_buffett",
                "charlie_munger"
            ],
            "use_all": False
        },
        "model": {
            "provider": "OpenRouter",
            "name": "google/gemini-2.5-pro",
            "use_ollama": False
        },
        "backtest": {
            "enabled": False,
            "start_date": "2024-01-01",
            "end_date": "2024-12-31",
            "initial_capital": 100000.0,
            "margin_requirement": 0.0
        },
        "output": {
            "save_results": True,
            "output_dir": "results",
            "format": "both",
            "include_analysis": True
        },
        "logging": {
            "enable_console": True,
            "enable_file": True,
            "enable_json": True,
            "console_format": "human",
            "console_level": "INFO",
            "log_dir": "logs",
            "auto_session_id": True,
            "session_id": ""
        }
    }
    
    try:
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.dump(default_config, f, default_flow_style=False, allow_unicode=True, indent=2)
        print(f"[SUCCESS] Default configuration created: {config_path}")
        print("Please edit the configuration file and run again")
        return True
    except Exception as e:
        print(f"[ERROR] Failed to create configuration file: {e}")
        return False


def validate_config(config):
    """Validate configuration file"""
    errors = []
    
    # Check required configuration items
    if not config.get("hedge_fund", {}).get("tickers"):
        errors.append("hedge_fund.tickers cannot be empty")
    
    if not config.get("model", {}).get("provider"):
        errors.append("model.provider cannot be empty")
    
    if not config.get("model", {}).get("name"):
        errors.append("model.name cannot be empty")
    
    # Check analysts configuration
    analysts_config = config.get("analysts", {})
    if not analysts_config.get("use_all", False) and not analysts_config.get("selected"):
        errors.append("Must select analysts or set analysts.use_all = true")
    
    if errors:
        print("[ERROR] Configuration validation failed:")
        for error in errors:
            print(f"   - {error}")
        return False
    
    return True


def prepare_dates(config):
    """准备日期配置"""
    hedge_fund_config = config.get("hedge_fund", {})
    
    # 处理结束日期
    end_date = hedge_fund_config.get("end_date")
    if not end_date:
        end_date = datetime.now().strftime("%Y-%m-%d")
    
    # 处理开始日期
    start_date = hedge_fund_config.get("start_date")
    if not start_date:
        end_date_obj = datetime.strptime(end_date, "%Y-%m-%d")
        start_date = (end_date_obj - relativedelta(months=3)).strftime("%Y-%m-%d")
    
    return start_date, end_date


def prepare_analysts(config):
    """准备分析师配置"""
    analysts_config = config.get("analysts", {})
    
    if analysts_config.get("use_all", False):
        return [analyst_id for _, analyst_id in ANALYST_ORDER]
    else:
        selected = analysts_config.get("selected", [])
        # 验证分析师ID是否有效
        valid_analysts = [analyst_id for _, analyst_id in ANALYST_ORDER]
        invalid_analysts = [a for a in selected if a not in valid_analysts]
        
        if invalid_analysts:
            print(f"[WARNING] Invalid analyst IDs: {invalid_analysts}")
            print(f"Available analyst IDs: {valid_analysts}")
        
        return [a for a in selected if a in valid_analysts]


def save_results(results, config):
    """保存结果到文件"""
    output_config = config.get("output", {})
    
    if not output_config.get("save_results", False):
        return
    
    # 创建输出目录
    output_dir = Path(output_config.get("output_dir", "results"))
    output_dir.mkdir(exist_ok=True)
    
    # 生成文件名
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base_filename = f"hedge_fund_results_{timestamp}"
    
    # 保存格式
    format_type = output_config.get("format", "json")
    
    if format_type in ["json", "both"]:
        json_file = output_dir / f"{base_filename}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False, default=str)
        print(f"[SUCCESS] Results saved to: {json_file}")
    
    if format_type in ["csv", "both"]:
        # CSV format saving logic can be added here
        print("[INFO] CSV format saving feature to be implemented")


def setup_logging_from_config(config):
    """Setup logging system from configuration"""
    logging_config = config.get("logging", {})
    
    # Setup logging with config parameters
    logger = setup_logging(
        console_format=logging_config.get("console_format", "human"),
        console_level=logging_config.get("console_level", "INFO"),
        log_dir=logging_config.get("log_dir", "logs")
    )
    
    return logger


def run_hedge_fund_with_config(config):
    """Run hedge fund using configuration file"""
    # Setup logging first
    logger = setup_logging_from_config(config)
    
    print("[INFO] Starting AI Hedge Fund execution...")
    
    # Prepare parameters
    hedge_fund_config = config["hedge_fund"]
    model_config = config["model"]
    
    tickers = hedge_fund_config["tickers"]
    start_date, end_date = prepare_dates(config)
    selected_analysts = prepare_analysts(config)
    
    print(f"[INFO] Tickers: {', '.join(tickers)}")
    print(f"[INFO] Date range: {start_date} to {end_date}")
    print(f"[INFO] Selected analysts: {len(selected_analysts)} analysts")
    print(f"[INFO] Using model: {model_config['provider']} - {model_config['name']}")
    print()
    
    # 创建投资组合
    portfolio = {
        "cash": hedge_fund_config["initial_cash"],
        "margin_requirement": hedge_fund_config["margin_requirement"],
        "margin_used": 0.0,
        "positions": {
            ticker: {
                "long": 0,
                "short": 0,
                "long_cost_basis": 0.0,
                "short_cost_basis": 0.0,
                "short_margin_used": 0.0,
            }
            for ticker in tickers
        },
        "realized_gains": {
            ticker: {
                "long": 0.0,
                "short": 0.0,
            }
            for ticker in tickers
        },
    }
    
    try:
        # 运行对冲基金
        result = run_hedge_fund(
            tickers=tickers,
            start_date=start_date,
            end_date=end_date,
            portfolio=portfolio,
            show_reasoning=hedge_fund_config.get("show_reasoning", False),
            selected_analysts=selected_analysts,
            model_name=model_config["name"],
            model_provider=model_config["provider"],
            config=config,  # Pass full config for data source settings
        )
        
        # 显示结果
        print_trading_output(result)
        
        # 保存结果
        save_results(result, config)
        
        return result
        
    except Exception as e:
        print(f"[ERROR] Execution failed: {e}")
        return None


def run_backtest_with_config(config):
    """Run backtest using configuration file"""
    # Setup logging first
    logger = setup_logging_from_config(config)
    
    print("[INFO] Starting backtest execution...")
    
    # Prepare parameters
    backtest_config = config["backtest"]
    model_config = config["model"]
    
    tickers = config["hedge_fund"]["tickers"]
    selected_analysts = prepare_analysts(config)
    
    print(f"[INFO] Tickers: {', '.join(tickers)}")
    print(f"[INFO] Backtest period: {backtest_config['start_date']} to {backtest_config['end_date']}")
    print(f"[INFO] Selected analysts: {len(selected_analysts)} analysts")
    print(f"[INFO] Using model: {model_config['provider']} - {model_config['name']}")
    print()
    
    try:
        # 创建回测器
        backtester = Backtester(
            agent=run_hedge_fund,
            tickers=tickers,
            start_date=backtest_config["start_date"],
            end_date=backtest_config["end_date"],
            initial_capital=backtest_config["initial_capital"],
            model_name=model_config["name"],
            model_provider=model_config["provider"],
            selected_analysts=selected_analysts,
            initial_margin_requirement=backtest_config["margin_requirement"],
            config=config,  # Pass full config for data source settings
        )
        
        # 运行回测
        performance_metrics = backtester.run_backtest()
        
        # 分析性能
        performance_df = backtester.analyze_performance()
        
        # 保存结果
        results = {
            "performance_metrics": performance_metrics,
            "performance_data": performance_df.to_dict() if not performance_df.empty else {}
        }
        save_results(results, config)
        
        return results
        
    except Exception as e:
        print(f"[ERROR] Backtest failed: {e}")
        return None


def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="AI Hedge Fund Configuration Runner")
    parser.add_argument("--config", "-c", default="config.yaml", help="Configuration file path")
    parser.add_argument("--create-config", action="store_true", help="Create default configuration file")
    parser.add_argument("--validate", action="store_true", help="Validate configuration file only")
    
    args = parser.parse_args()
    
    # Create default configuration
    if args.create_config:
        create_default_config(args.config)
        return
    
    # Load configuration
    config = load_config(args.config)
    if not config:
        return
    
    # Validate configuration
    if not validate_config(config):
        return
    
    if args.validate:
        print("[SUCCESS] Configuration validation passed")
        return
    
    print("AI Hedge Fund Automated Runner")
    print("=" * 50)
    
    # Check if running backtest
    if config.get("backtest", {}).get("enabled", False):
        result = run_backtest_with_config(config)
    else:
        result = run_hedge_fund_with_config(config)
    
    if result:
        print("\n[SUCCESS] Execution completed!")
    else:
        print("\n[ERROR] Execution failed!")


if __name__ == "__main__":
    main()