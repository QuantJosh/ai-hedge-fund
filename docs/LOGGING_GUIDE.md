# AI Hedge Fund 日志系统使用指南

## 概述

AI Hedge Fund 采用混合日志方案，提供既人类可读又机器可分析的日志记录：

- **控制台输出** - 带表情符号的人类友好格式，便于开发调试
- **JSONL文件** - 结构化数据，便于后续分析和处理
- **传统日志文件** - 详细的文本日志，便于问题排查

## 快速开始

### 1. 基本设置

```python
from src.utils.llm_logger import setup_logging

# 设置日志系统
logger = setup_logging(
    console_format="human",  # 人类可读格式
    console_level="INFO",    # 控制台日志级别
    log_dir="logs"          # 日志目录
)
```

### 2. 使用装饰器

```python
from src.utils.llm_logger import log_agent_execution, log_llm_call, log_data_operation

@log_agent_execution("Michael_Burry")
def analyze_stock(state):
    # 你的分析逻辑
    return result

@log_llm_call("Michael_Burry", "AAPL")
def call_gpt4(prompt):
    # LLM调用逻辑
    return response

@log_data_operation("stock_data", "Yahoo_Finance")
def fetch_data(ticker):
    # 数据获取逻辑
    return data
```

## 日志格式

### 控制台输出（人类可读）

```
[10:30:45] 🤖 [AAPL] Michael_Burry → 开始分析
[10:30:46] 📊 [AAPL] Yahoo_Finance → stock_data 成功 (252条记录)
[10:30:47] 🧠 [AAPL] Michael_Burry → gpt-4 调用 (提示词: 1024字符)
[10:30:49] 💭 [AAPL] Michael_Burry → gpt-4 响应 (长度: 512字符 耗时:2.3s)
[10:30:50] 🎯 [AAPL] Michael_Burry → 决策: BUY (置信度: 85.0%)
[10:30:50] ✅ [AAPL] Michael_Burry → 分析完成 (耗时: 5.2秒)
```

### JSONL文件（机器可读）

```jsonl
{"timestamp":"2024-01-15T10:30:45.123Z","session_id":"20240115_103045","type":"agent_start","level":"INFO","agent":"Michael_Burry","ticker":"AAPL","message":"Agent execution started"}
{"timestamp":"2024-01-15T10:30:46.456Z","session_id":"20240115_103045","type":"data_fetch","level":"INFO","agent":"Yahoo_Finance","ticker":"AAPL","message":"Data fetch successful: stock_data (252 items)","data":{"data_type":"stock_data","count":252}}
{"timestamp":"2024-01-15T10:30:47.789Z","session_id":"20240115_103045","type":"model_request","level":"DEBUG","agent":"Michael_Burry","ticker":"AAPL","message":"Model API request sent","model":{"provider":"OpenAI","model":"gpt-4","prompt_length":1024}}
```

## 配置选项

### config.yaml 配置

```yaml
logging:
  enable_console: true        # 启用控制台输出
  enable_file: true          # 启用文件日志
  enable_json: true          # 启用JSONL日志
  console_format: "human"    # 控制台格式: "human" 或 "json"
  console_level: "INFO"      # 日志级别: DEBUG, INFO, WARNING, ERROR
  log_dir: "logs"           # 日志目录
  auto_session_id: true     # 自动生成会话ID
```

### 程序化配置

```python
from src.utils.logger import init_logger

logger = init_logger(
    log_dir="custom_logs",
    console_format="human",
    console_level="DEBUG",
    enable_console=True,
    enable_file=True,
    enable_json=True
)
```

## 装饰器详解

### @log_agent_execution

记录Agent执行的开始和结束，自动计算执行时间。

```python
@log_agent_execution("Michael_Burry")
def analyze_stock(state):
    # 自动记录开始时间
    # 执行分析逻辑
    result = perform_analysis(state)
    # 自动记录结束时间和结果摘要
    return result
```

### @log_llm_call

记录LLM模型调用的详细信息，包括提示词长度、响应时间等。

```python
@log_llm_call(agent_name="Michael_Burry", ticker="AAPL")
def call_openai(prompt, model="gpt-4"):
    # 自动记录请求信息
    response = openai.chat.completions.create(...)
    # 自动记录响应信息和耗时
    return response
```

### @log_data_operation

记录数据获取操作，包括成功/失败状态、数据量等。

```python
@log_data_operation("stock_price", "Yahoo_Finance")
def fetch_stock_data(ticker):
    # 自动记录数据获取开始
    data = yfinance.download(ticker)
    # 自动记录获取结果和数据量
    return data
```

## 日志查看工具

### 命令行查看器

```bash
# 查看所有日志
python tools/log_viewer.py --find

# 查看特定Agent的日志
python tools/log_viewer.py logs/structured_log.jsonl --agent "Michael_Burry"

# 查看最近10条日志
python tools/log_viewer.py logs/structured_log.jsonl --last 10

# 查看错误日志
python tools/log_viewer.py logs/structured_log.jsonl --level ERROR

# 显示详细信息
python tools/log_viewer.py logs/structured_log.jsonl --details

# 显示统计摘要
python tools/log_viewer.py logs/structured_log.jsonl --summary
```

### VS Code 插件推荐

1. **Log File Highlighter** - 自动高亮日志文件
2. **JSON Lines** - 专门处理JSONL格式
3. **Rainbow CSV** - 如果需要CSV格式查看

### VS Code 设置

在 `settings.json` 中添加：

```json
{
  "files.associations": {
    "*.jsonl": "jsonl",
    "*.log": "log"
  },
  "logFileHighlighter.customPatterns": [
    {
      "pattern": "\"level\":\\s*\"ERROR\"",
      "foreground": "#ff6b6b"
    },
    {
      "pattern": "\"agent\":\\s*\"([^\"]+)\"",
      "foreground": "#4ecdc4"
    }
  ]
}
```

## 日志分析

### 使用 jq 查询JSONL

```bash
# 查看所有错误
cat logs/structured_log.jsonl | jq 'select(.level == "ERROR")'

# 统计各Agent的调用次数
cat logs/structured_log.jsonl | jq '.agent' | sort | uniq -c

# 查看LLM调用的平均耗时
cat logs/structured_log.jsonl | jq 'select(.type == "model_response") | .duration_ms' | jq -s 'add/length'

# 查看特定ticker的所有操作
cat logs/structured_log.jsonl | jq 'select(.ticker == "AAPL")'
```

### Python 分析脚本

```python
import json
import pandas as pd

# 加载日志数据
logs = []
with open('logs/structured_log.jsonl', 'r') as f:
    for line in f:
        logs.append(json.loads(line))

df = pd.DataFrame(logs)

# 分析LLM调用性能
llm_calls = df[df['type'] == 'model_response']
print(f"平均响应时间: {llm_calls['duration_ms'].mean():.2f}ms")

# 分析Agent执行时间
agent_executions = df[df['type'] == 'agent_end']
print(f"平均执行时间: {agent_executions['duration_ms'].mean():.2f}ms")
```

## 最佳实践

### 1. 日志级别使用

- **DEBUG** - 详细的调试信息，包括所有LLM调用
- **INFO** - 一般信息，Agent开始/结束、数据获取
- **WARNING** - 警告信息，数据获取失败但可恢复
- **ERROR** - 错误信息，需要关注的问题

### 2. 性能考虑

- 生产环境建议使用 `INFO` 级别
- 开发调试时可以使用 `DEBUG` 级别
- JSONL文件会随时间增长，建议定期归档

### 3. 错误处理

```python
try:
    result = risky_operation()
except Exception as e:
    logger.log_error("Agent_Name", f"Operation failed: {str(e)}", ticker="AAPL", exception=e)
    raise
```

### 4. 自定义日志

```python
from src.utils.logger import get_logger

logger = get_logger()
logger.log_system("Custom system event", {"custom_data": "value"})
```

## 故障排除

### 常见问题

1. **日志文件过大** - 实施日志轮转或定期清理
2. **权限问题** - 确保日志目录有写入权限
3. **编码问题** - 所有文件使用UTF-8编码

### 调试技巧

```python
# 临时启用详细日志
logger = setup_logging(console_level="DEBUG")

# 只启用控制台输出进行快速调试
logger = setup_logging(enable_file=False, enable_json=False)
```

## 示例项目

查看 `examples/logging_example.py` 获取完整的使用示例。

```bash
python examples/logging_example.py
```

这将演示所有日志功能，并在 `logs/` 目录生成示例日志文件。