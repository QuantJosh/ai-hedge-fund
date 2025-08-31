#!/usr/bin/env python3
"""
AI Hedge Fund with Moomoo Integration
Connects Portfolio Manager decisions with Moomoo paper trading platform
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
from src.integrations.moomoo_client import MoomooIntegration, create_moomoo_integration


def load_config(config_path="config_moomoo.yaml"):
    """Load configuration file with Moomoo settings"""
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


def validate_moomoo_config(config):
    """Validate Moomoo configuration"""
    moomoo_config = config.get("moomoo", {})
    
    if not moomoo_config.get("enabled", False):
        return True  # Moomoo not enabled, no validation needed
    
    errors = []
    
    # Check required Moomoo settings
    if not isinstance(moomoo_config.get("port"), int):
        errors.append("moomoo.port must be an integer")
    
    if moomoo_config.get("port", 0) <= 0:
        errors.append("moomoo.port must be a positive integer")
    
    if not isinstance(moomoo_config.get("paper_trading"), bool):
        errors.append("moomoo.paper_trading must be true or false")
    
    if errors:
        print("[ERROR] Moomoo configuration validation failed:")
        for error in errors:
            print(f"   - {error}")
        return False
    
    return True


def setup_moomoo_integration(config) -> MoomooIntegration:
    """Setup Moomoo integration based on configuration"""
    moomoo_config = config.get("moomoo", {})
    
    if not moomoo_config.get("enabled", False):
        print("[INFO] Moomoo integration disabled")
        return None
    
    print("[INFO] Setting up Moomoo integration...")
    
    try:
        integration = MoomooIntegration(
            host=moomoo_config.get("host", "127.0.0.1"),
            port=moomoo_config.get("port", 11111),
            paper_trading=moomoo_config.get("paper_trading", True),
            auto_execute=moomoo_config.get("auto_execute", False)
        )
        
        if integration.connect():
            print("✅ Moomoo integration connected successfully")
            
            # Display account info
            account_info = integration.client.get_account_info()
            if account_info:
                print(f"   💰 Account Balance: ${account_info.get('cash', 0):,.2f}")
                print(f"   📊 Total Assets: ${account_info.get('total_assets', 0):,.2f}")
                print(f"   📈 Market Value: ${account_info.get('market_value', 0):,.2f}")
            
            # Display current positions
            positions = integration.client.get_positions()
            if positions:
                print(f"   📋 Current Positions: {len(positions)} tickers")
                for ticker, pos in positions.items():
                    if pos["quantity"] != 0:
                        print(f"      {ticker}: {pos['quantity']} shares @ ${pos['current_price']:.2f}")
            else:
                print("   📋 No current positions")
            
            return integration
        else:
            print("❌ Failed to connect to Moomoo")
            return None
            
    except Exception as e:
        print(f"❌ Error setting up Moomoo integration: {e}")
        print("   Make sure Moomoo OpenD is running and accessible")
        return None


def run_hedge_fund_with_moomoo(config):
    """Run hedge fund with Moomoo integration"""
    # Setup logging first
    logger = setup_logging(
        console_format=config.get("logging", {}).get("console_format", "human"),
        console_level=config.get("logging", {}).get("console_level", "INFO"),
        log_dir=config.get("logging", {}).get("log_dir", "logs")
    )
    
    print("[INFO] Starting AI Hedge Fund with Moomoo integration...")
    
    # Setup Moomoo integration
    moomoo_integration = setup_moomoo_integration(config)
    
    # Prepare parameters
    hedge_fund_config = config["hedge_fund"]
    model_config = config["model"]
    moomoo_config = config.get("moomoo", {})
    
    tickers = hedge_fund_config["tickers"]
    start_date, end_date = prepare_dates(config)
    selected_analysts = prepare_analysts(config)
    
    print(f"[INFO] Tickers: {', '.join(tickers)}")
    print(f"[INFO] Date range: {start_date} to {end_date}")
    print(f"[INFO] Selected analysts: {len(selected_analysts)} analysts")
    print(f"[INFO] Using model: {model_config['provider']} - {model_config['name']}")
    
    if moomoo_integration:
        print(f"[INFO] Moomoo integration: {'✅ Enabled' if moomoo_config.get('enabled') else '❌ Disabled'}")
        print(f"[INFO] Auto-execute trades: {'✅ Yes' if moomoo_config.get('auto_execute') else '❌ No'}")
        print(f"[INFO] Sync positions: {'✅ Yes' if moomoo_config.get('sync_positions') else '❌ No'}")
    print()
    
    # 创建投资组合 - 如果有Moomoo集成，从Moomoo同步
    if moomoo_integration and moomoo_config.get("sync_positions", True):
        print("[INFO] Syncing portfolio from Moomoo...")
        try:
            moomoo_portfolio = moomoo_integration.get_portfolio_sync()
            if moomoo_portfolio:
                portfolio = {
                    "cash": moomoo_portfolio.get("cash", hedge_fund_config["initial_cash"]),
                    "margin_requirement": hedge_fund_config["margin_requirement"],
                    "margin_used": moomoo_portfolio.get("margin_used", 0.0),
                    "positions": moomoo_portfolio.get("positions", {}),
                    "realized_gains": {ticker: {"long": 0.0, "short": 0.0} for ticker in tickers},
                }
                print(f"✅ Portfolio synced from Moomoo: ${moomoo_portfolio.get('total_assets', 0):,.2f} total assets")
            else:
                raise Exception("Failed to sync portfolio from Moomoo")
        except Exception as e:
            print(f"⚠️ Failed to sync from Moomoo, using default portfolio: {e}")
            portfolio = create_default_portfolio(hedge_fund_config, tickers)
    else:
        portfolio = create_default_portfolio(hedge_fund_config, tickers)
    
    try:
        # 运行对冲基金 - 传递Moomoo集成
        result = run_hedge_fund_with_moomoo_integration(
            tickers=tickers,
            start_date=start_date,
            end_date=end_date,
            portfolio=portfolio,
            show_reasoning=hedge_fund_config.get("show_reasoning", False),
            selected_analysts=selected_analysts,
            model_name=model_config["name"],
            model_provider=model_config["provider"],
            config=config,
            moomoo_integration=moomoo_integration
        )
        
        # 显示结果
        print_trading_output(result)
        
        # 如果启用了自动执行，显示执行结果
        if moomoo_integration and moomoo_config.get("auto_execute", False):
            print("\n" + "="*50)
            print("🚀 MOOMOO EXECUTION RESULTS")
            print("="*50)
            
            # 从结果中提取执行信息
            if "moomoo_execution" in result:
                execution_results = result["moomoo_execution"]
                for ticker, exec_result in execution_results.items():
                    status = "✅" if exec_result.get("success") else "❌"
                    print(f"{status} {ticker}: {exec_result.get('message', 'No message')}")
        
        # 保存结果
        save_results_with_moomoo(result, config)
        
        return result
        
    except Exception as e:
        print(f"[ERROR] Execution failed: {e}")
        return None
    finally:
        # 断开Moomoo连接
        if moomoo_integration:
            moomoo_integration.disconnect()


def create_default_portfolio(hedge_fund_config, tickers):
    """Create default portfolio structure"""
    return {
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


def run_hedge_fund_with_moomoo_integration(
    tickers,
    start_date,
    end_date,
    portfolio,
    show_reasoning,
    selected_analysts,
    model_name,
    model_provider,
    config,
    moomoo_integration=None
):
    """Modified run_hedge_fund function with Moomoo integration"""
    
    # Import the Moomoo-enabled portfolio manager
    from src.agents.portfolio_manager_moomoo import portfolio_management_agent_moomoo
    
    # Get Moomoo configuration
    moomoo_config = config.get("moomoo", {})
    
    # Create a modified workflow that uses the Moomoo portfolio manager
    def moomoo_portfolio_agent(state: AgentState):
        return portfolio_management_agent_moomoo(
            state=state,
            agent_id="portfolio_manager_moomoo",
            moomoo_integration=moomoo_integration,
            sync_positions=moomoo_config.get("sync_positions", True),
            execute_trades=moomoo_config.get("auto_execute", False)
        )
    
    # Use the regular run_hedge_fund but replace the portfolio manager
    # This is a simplified approach - in a full implementation, you'd modify the workflow graph
    result = run_hedge_fund(
        tickers=tickers,
        start_date=start_date,
        end_date=end_date,
        portfolio=portfolio,
        show_reasoning=show_reasoning,
        selected_analysts=selected_analysts,
        model_name=model_name,
        model_provider=model_provider,
        config=config,
    )
    
    # If Moomoo integration is enabled and auto_execute is True, execute the trades
    if moomoo_integration and moomoo_config.get("auto_execute", False):
        try:
            print("\n🚀 Executing trades on Moomoo...")
            
            # Extract decisions from result
            decisions = result.get("decisions", {})
            current_prices = result.get("current_prices", {})
            
            # Execute on Moomoo
            execution_results = moomoo_integration.execute_decisions(decisions, current_prices)
            
            # Add execution results to the main result
            result["moomoo_execution"] = {
                ticker: {
                    "success": exec_result.success,
                    "message": exec_result.message,
                    "order_id": exec_result.order_id,
                    "timestamp": exec_result.timestamp.isoformat() if exec_result.timestamp else None
                }
                for ticker, exec_result in execution_results.items()
            }
            
            # Save execution log
            moomoo_integration.save_execution_log()
            
        except Exception as e:
            print(f"❌ Failed to execute trades on Moomoo: {e}")
            result["moomoo_execution_error"] = str(e)
    
    return result


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


def save_results_with_moomoo(results, config):
    """保存结果到文件，包括Moomoo执行日志"""
    output_config = config.get("output", {})
    
    if not output_config.get("save_results", False):
        return
    
    # 创建输出目录
    output_dir = Path(output_config.get("output_dir", "results"))
    output_dir.mkdir(exist_ok=True)
    
    # 生成文件名
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base_filename = f"hedge_fund_moomoo_results_{timestamp}"
    
    # 保存格式
    format_type = output_config.get("format", "json")
    
    if format_type in ["json", "both"]:
        json_file = output_dir / f"{base_filename}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False, default=str)
        print(f"[SUCCESS] Results saved to: {json_file}")


def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="AI Hedge Fund with Moomoo Integration")
    parser.add_argument("--config", "-c", default="config_moomoo.yaml", help="Configuration file path")
    parser.add_argument("--validate", action="store_true", help="Validate configuration file only")
    parser.add_argument("--test-connection", action="store_true", help="Test Moomoo connection only")
    
    args = parser.parse_args()
    
    # Load configuration
    config = load_config(args.config)
    if not config:
        return
    
    # Validate configuration
    if not validate_moomoo_config(config):
        return
    
    if args.validate:
        print("[SUCCESS] Configuration validation passed")
        return
    
    # Test Moomoo connection only
    if args.test_connection:
        print("Testing Moomoo connection...")
        moomoo_integration = setup_moomoo_integration(config)
        if moomoo_integration:
            print("✅ Moomoo connection test successful")
            moomoo_integration.disconnect()
        else:
            print("❌ Moomoo connection test failed")
        return
    
    print("AI Hedge Fund with Moomoo Integration")
    print("=" * 50)
    
    # Run hedge fund with Moomoo integration
    result = run_hedge_fund_with_moomoo(config)
    
    if result:
        print("\n[SUCCESS] Execution completed!")
        
        # Display summary
        if "moomoo_execution" in result:
            executed_trades = sum(1 for r in result["moomoo_execution"].values() if r.get("success"))
            total_trades = len(result["moomoo_execution"])
            print(f"[INFO] Moomoo trades executed: {executed_trades}/{total_trades}")
    else:
        print("\n[ERROR] Execution failed!")


if __name__ == "__main__":
    main()