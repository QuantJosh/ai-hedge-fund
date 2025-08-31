# Moomoo Integration Guide

本指南将帮助您将AI对冲基金系统与Moomoo模拟交易平台集成，实现自动化交易执行。

## 🚀 功能特性

- **实时持仓同步**: 从Moomoo账户同步当前持仓和资金
- **自动交易执行**: Portfolio Manager的决策自动在Moomoo上执行
- **风险管理**: 集成风险控制和仓位限制
- **模拟交易**: 支持Moomoo纸上交易，安全测试策略
- **执行日志**: 详细记录所有交易执行过程

## 📋 前置要求

### 1. 安装Moomoo OpenD

1. 下载并安装 [Moomoo OpenD](https://www.moomoo.com/download/openapi)
2. 启动Moomoo OpenD应用程序
3. 确保OpenD在默认端口11111上运行

### 2. 安装Python依赖

```bash
pip install futu
```

### 3. 设置Moomoo账户

1. 注册Moomoo账户
2. 开通模拟交易功能
3. 在OpenD中登录您的账户

## ⚙️ 配置设置

### 1. 复制配置文件

```bash
cp config_moomoo.yaml my_moomoo_config.yaml
```

### 2. 编辑配置文件

```yaml
# Moomoo Integration Settings
moomoo:
  enabled: true                # 启用Moomoo集成
  host: "127.0.0.1"           # OpenD主机地址
  port: 11111                 # OpenD端口
  paper_trading: true         # 使用模拟交易账户
  auto_execute: false         # 是否自动执行交易
  sync_positions: true        # 是否同步持仓信息
  
  # Trading preferences
  order_type: "market"        # 订单类型: "market" 或 "limit"
  execution_delay: 1.0        # 订单间延迟(秒)
  
  # Risk settings
  max_position_size: 0.2      # 单个仓位最大占比(20%)
  require_confirmation: true   # 执行前需要确认
```

## 🎯 使用方法

### 1. 测试连接

```bash
python run_with_moomoo.py --test-connection
```

### 2. 验证配置

```bash
python run_with_moomoo.py --validate
```

### 3. 运行分析(不执行交易)

```bash
python run_with_moomoo.py --config my_moomoo_config.yaml
```

### 4. 运行并自动执行交易

编辑配置文件，设置 `auto_execute: true`，然后运行：

```bash
python run_with_moomoo.py --config my_moomoo_config.yaml
```

## 📊 工作流程

### 1. 持仓同步阶段
```
AI系统 → Moomoo OpenD → 获取当前持仓和资金
```

### 2. 分析决策阶段
```
市场数据 → AI分析师 → Portfolio Manager → 交易决策
```

### 3. 交易执行阶段
```
交易决策 → Moomoo OpenD → 模拟交易账户 → 执行确认
```

## 🔧 API集成详解

### MoomooClient类

```python
from src.integrations.moomoo_client import MoomooClient

# 创建客户端
client = MoomooClient(
    host="127.0.0.1",
    port=11111,
    paper_trading=True
)

# 连接
if client.connect():
    # 获取账户信息
    account_info = client.get_account_info()
    
    # 获取当前持仓
    positions = client.get_positions()
    
    # 获取实时价格
    price = client.get_current_price("AAPL")
    
    # 执行交易
    result = client.place_order(
        ticker="AAPL",
        side=OrderSide.BUY,
        quantity=10
    )
```

### MoomooIntegration类

```python
from src.integrations.moomoo_client import MoomooIntegration

# 创建集成
integration = MoomooIntegration(paper_trading=True)

if integration.connect():
    # 执行Portfolio Manager决策
    decisions = {
        "AAPL": {
            "action": "buy",
            "quantity": 10,
            "confidence": 85.0,
            "reasoning": "Strong bullish signal"
        }
    }
    
    results = integration.execute_decisions(decisions)
```

## 📈 交易决策映射

| Portfolio Manager Action | Moomoo Order Type |
|-------------------------|-------------------|
| `buy`                   | BUY (开多仓)        |
| `sell`                  | SELL (平多仓)       |
| `short`                 | SELL (开空仓)       |
| `cover`                 | BUY (平空仓)        |
| `hold`                  | 无操作              |

## 🛡️ 风险管理

### 1. 仓位限制
- 单个股票最大仓位: 20%
- 总仓位限制: 基于可用资金
- 保证金要求: 自动计算

### 2. 订单验证
- 检查可用资金
- 验证持仓状态
- 确认订单数量

### 3. 错误处理
- 连接失败重试
- 订单失败回滚
- 异常情况记录

## 📝 日志和监控

### 1. 执行日志
```json
{
  "timestamp": "2025-08-31T20:00:00",
  "ticker": "AAPL",
  "decision": {
    "action": "buy",
    "quantity": 10,
    "confidence": 85.0
  },
  "result": {
    "success": true,
    "order_id": "12345",
    "message": "Order placed successfully"
  }
}
```

### 2. 查看日志
```bash
# 查看执行日志
ls moomoo_execution_log_*.json

# 查看系统日志
python view_logs.py
```

## 🔍 故障排除

### 1. 连接问题

**问题**: 无法连接到Moomoo OpenD
```
❌ Failed to connect to Moomoo: Connection refused
```

**解决方案**:
- 确保Moomoo OpenD正在运行
- 检查端口11111是否被占用
- 验证防火墙设置

### 2. 认证问题

**问题**: 交易解锁失败
```
Warning: Failed to unlock trading: Invalid password
```

**解决方案**:
- 检查模拟交易密码(默认: 123456)
- 确保账户已开通模拟交易
- 重新登录Moomoo账户

### 3. 订单失败

**问题**: 订单执行失败
```
❌ AAPL: buy 10 shares - Order failed: Insufficient funds
```

**解决方案**:
- 检查账户余额
- 验证股票代码格式
- 确认市场交易时间

## 📚 示例代码

### 完整使用示例

```python
#!/usr/bin/env python3
"""
Moomoo集成使用示例
"""

from src.integrations.moomoo_client import create_moomoo_integration

def main():
    # 创建Moomoo集成
    integration = create_moomoo_integration(
        paper_trading=True,
        auto_execute=False
    )
    
    if not integration:
        print("Failed to create Moomoo integration")
        return
    
    try:
        # 获取账户信息
        account_info = integration.client.get_account_info()
        print(f"Account Balance: ${account_info.get('cash', 0):,.2f}")
        
        # 获取当前持仓
        positions = integration.client.get_positions()
        print(f"Current Positions: {len(positions)}")
        
        # 模拟交易决策
        decisions = {
            "AAPL": {
                "action": "buy",
                "quantity": 1,
                "confidence": 85.0,
                "reasoning": "Test order"
            }
        }
        
        # 执行决策
        results = integration.execute_decisions(decisions)
        
        for ticker, result in results.items():
            status = "✅" if result.success else "❌"
            print(f"{status} {ticker}: {result.message}")
        
        # 保存执行日志
        integration.save_execution_log()
        
    finally:
        integration.disconnect()

if __name__ == "__main__":
    main()
```

## 🎯 最佳实践

### 1. 测试流程
1. 先在模拟环境测试
2. 验证所有功能正常
3. 小额资金实盘测试
4. 逐步增加投资规模

### 2. 监控建议
- 定期检查执行日志
- 监控账户余额变化
- 跟踪策略表现
- 及时调整参数

### 3. 安全措施
- 使用模拟交易测试
- 设置合理的仓位限制
- 启用交易确认
- 定期备份配置

## 📞 支持和帮助

如果您在使用过程中遇到问题，请：

1. 查看日志文件获取详细错误信息
2. 检查Moomoo OpenD连接状态
3. 验证配置文件设置
4. 参考故障排除部分

---

**注意**: 本集成仅用于教育和研究目的。实际交易请谨慎操作，并充分了解相关风险。