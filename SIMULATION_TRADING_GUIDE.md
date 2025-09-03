# AI Hedge Fund - 模拟交易使用指南

## 🎯 概述

AI对冲基金模拟交易系统让你可以安全地测试AI驱动的投资决策，使用Moomoo纸质交易账户，无需真实资金风险。

## 🚀 快速开始

### 方法1：快速启动（推荐新手）
```bash
python quick_start_simulation.py
```
- 选择预设的股票组合
- 选择执行模式
- 一键开始模拟交易

### 方法2：命令行启动（高级用户）
```bash
# 基本使用
python run_simulation_trading.py --tickers AAPL MSFT GOOGL

# 自动执行模式
python run_simulation_trading.py --tickers AAPL MSFT --auto-execute

# 不同步持仓
python run_simulation_trading.py --tickers AAPL --no-sync
```

## 📊 预设股票组合

### 1. Tech Giants (科技巨头)
- **股票**: AAPL, MSFT, GOOGL, AMZN
- **描述**: 苹果、微软、谷歌、亚马逊
- **适合**: 稳健投资者

### 2. AI & Innovation (AI与创新)
- **股票**: NVDA, TSLA, META, NFLX
- **描述**: 英伟达、特斯拉、Meta、Netflix
- **适合**: 成长型投资者

### 3. Market Leaders (市场领导者)
- **股票**: AAPL, MSFT, NVDA, TSLA
- **描述**: 按市值排名前4
- **适合**: 追求市场表现

### 4. Diversified Mix (多元化组合)
- **股票**: AAPL, MSFT, GOOGL, TSLA, NVDA, META
- **描述**: 6只主要科技股
- **适合**: 分散风险

## ⚡ 执行模式

### 手动确认模式（推荐）
- 显示AI决策后等待用户确认
- 可以审查每个交易决策
- 更安全，适合学习

### 自动执行模式
- AI决策后自动执行交易
- 更快速，适合批量测试
- 仍然是纸质交易，无风险

## 🔧 系统要求

### 必需软件
1. **Python 3.8+**
2. **Moomoo OpenD** - 必须运行在127.0.0.1:11111
3. **虚拟环境** - 推荐使用

### 必需包
```bash
pip install moomoo-api
pip install -r requirements.txt
```

### Moomoo设置
1. 下载并安装Moomoo OpenD
2. 登录你的Moomoo账户
3. 确保启用**纸质交易模式**
4. 启用API访问（端口11111）

## 📋 使用流程

### 1. 准备阶段
```bash
# 启动Moomoo OpenD
python start_moomoo.py

# 测试连接
python src/brokers/moomoo/test_moomoo_broker.py
```

### 2. 运行模拟
```bash
# 快速启动
python quick_start_simulation.py

# 或命令行
python run_simulation_trading.py --tickers AAPL MSFT
```

### 3. 查看结果
- 结果保存在 `results/` 目录
- JSON格式，包含完整交易日志
- 包含性能分析和AI决策

## 🛡️ 安全特性

### 强制纸质交易
- 系统强制使用纸质交易模式
- 检测到真实交易会拒绝执行
- 多重安全检查

### 用户确认
- 默认需要用户确认才执行交易
- 显示详细的交易决策
- 可以随时取消

### Ctrl+C支持
- 任何时候按Ctrl+C都能安全退出
- 自动清理连接
- 保存部分结果

## 📊 AI决策系统

### 当前实现
- 使用模拟AI分析（用于测试）
- 基于简单的信心度算法
- 支持买入、卖出、持有决策

### 未来集成
- Ben Graham价值投资分析
- Warren Buffett投资策略
- 技术分析指标
- 市场情绪分析

## 💰 模拟价格

由于美股行情权限限制，系统使用模拟价格：

```python
模拟价格表:
AAPL: $175.50    MSFT: $335.20
GOOGL: $138.75   TSLA: $248.90
NVDA: $465.30    AMZN: $145.80
META: $298.50    NFLX: $425.60
```

### 获取实时价格
1. 在Moomoo App中申请Level 1美股行情
2. 等待审批通过
3. 系统会自动使用实时价格

## 📁 输出文件

### 模拟结果
- **位置**: `results/simulation_results_YYYYMMDD_HHMMSS.json`
- **内容**: 完整的交易会话记录

### 执行日志
- **位置**: `simulation_execution_YYYYMMDD_HHMMSS.json`
- **内容**: 详细的交易执行记录

### 日志文件
- **位置**: `logs/` 目录
- **内容**: 系统运行日志

## 🔍 测试命令

### 连接测试
```bash
# 全面测试
python src/brokers/moomoo/test_moomoo_broker.py

# 快速测试
python test_simulation_trading.py
```

### 功能测试
```bash
# 测试特定功能
python src/brokers/moomoo/test_moomoo_broker.py --test connection
python src/brokers/moomoo/test_moomoo_broker.py --test account
python src/brokers/moomoo/test_moomoo_broker.py --test market
```

## ❓ 常见问题

### Q: 为什么价格显示"mock price"？
A: 需要申请美股Level 1行情权限。在此之前使用模拟价格进行测试。

### Q: 如何确保是纸质交易？
A: 系统有多重检查，强制纸质交易模式，不会使用真实资金。

### Q: 可以添加自定义股票吗？
A: 可以，选择"Custom"选项或使用命令行参数 `--tickers`。

### Q: 如何停止运行中的模拟？
A: 按Ctrl+C即可安全退出，系统会自动清理。

### Q: 结果文件在哪里？
A: 在 `results/` 目录中，文件名包含时间戳。

## 🚨 故障排除

### 连接失败
1. 确保Moomoo OpenD正在运行
2. 检查端口11111是否开放
3. 确认已登录Moomoo账户

### 交易失败
1. 检查是否启用纸质交易
2. 确认账户有足够模拟资金
3. 查看错误日志获取详细信息

### 权限错误
1. 申请美股行情权限
2. 或继续使用模拟价格测试

## 📞 支持

如果遇到问题：
1. 查看日志文件 `logs/`
2. 运行测试脚本诊断
3. 检查Moomoo OpenD状态
4. 确认网络连接正常

---

🎉 **开始你的AI投资之旅！**