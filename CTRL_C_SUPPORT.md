# Ctrl+C 信号处理支持

## 🎯 目标
确保所有Python脚本都能通过Ctrl+C安全退出，包括：
- 清理资源（断开Moomoo连接）
- 保存部分结果
- 优雅退出

## ✅ 已修复的脚本

### 1. run_simulation_trading.py
- ✅ 添加了signal.SIGINT处理器
- ✅ 在关键步骤添加shutdown检查
- ✅ 自动断开Moomoo连接
- ✅ 保存部分结果
- ✅ 优雅退出消息

**功能**：
```python
def _signal_handler(self, signum, frame):
    """Handle Ctrl+C gracefully"""
    print("\n⚠️  Shutdown requested (Ctrl+C). Cleaning up...")
    # 断开Moomoo连接
    # 保存部分结果
    # 优雅退出
```

### 2. test_simulation_trading.py
- ✅ 添加了signal.SIGINT处理器
- ✅ 优雅退出消息

### 3. start_moomoo.py
- ✅ 添加了signal.SIGINT处理器
- ✅ 优雅退出消息

### 4. run_with_moomoo.py
- ✅ 添加了signal.SIGINT处理器
- ✅ 连接清理提示
- ✅ 优雅退出消息

## 🧪 测试方法

### 方法1：直接测试
```bash
python run_simulation_trading.py --tickers AAPL
# 然后按 Ctrl+C
```

### 方法2：使用测试脚本
```bash
python test_signal_simple.py
# 然后按 Ctrl+C
```

## 📋 信号处理特性

### 共同特性
1. **即时响应**：Ctrl+C立即触发处理器
2. **资源清理**：自动断开网络连接
3. **状态保存**：尝试保存部分结果
4. **友好消息**：显示清理过程和告别消息
5. **安全退出**：使用sys.exit(0)确保进程终止

### 特殊处理
- **Moomoo连接**：自动断开以避免连接泄漏
- **结果保存**：标记为interrupted并保存部分数据
- **日志记录**：记录中断事件

## 🔧 实现细节

### 信号处理器设置
```python
import signal
signal.signal(signal.SIGINT, signal_handler)
```

### 检查点机制
```python
def _check_shutdown(self):
    if self._shutdown_requested:
        raise KeyboardInterrupt("Shutdown requested")
```

### 资源清理
```python
if self.moomoo_integration:
    self.moomoo_integration.disconnect()
```

## ✅ 验证清单

- [x] run_simulation_trading.py - 完整信号处理
- [x] test_simulation_trading.py - 基本信号处理  
- [x] start_moomoo.py - 基本信号处理
- [x] run_with_moomoo.py - 基本信号处理
- [x] 所有脚本都有优雅退出消息
- [x] Moomoo连接自动清理
- [x] 部分结果保存机制

## 🎉 结果

现在所有主要的Python脚本都支持Ctrl+C安全退出！用户可以随时中断执行而不会留下悬挂的进程或连接。