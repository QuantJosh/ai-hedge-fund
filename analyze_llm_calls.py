#!/usr/bin/env python3
"""
分析JSONL日志中的LLM调用模式
"""

import json
import sys
from pathlib import Path
from collections import defaultdict

def analyze_llm_calls(jsonl_file):
    """分析LLM调用模式"""
    
    if not Path(jsonl_file).exists():
        print(f"❌ 文件不存在: {jsonl_file}")
        return
    
    print(f"🔍 分析日志文件: {jsonl_file}")
    print("=" * 80)
    
    # 统计数据
    agent_calls = defaultdict(list)
    request_response_pairs = defaultdict(list)
    
    with open(jsonl_file, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            try:
                entry = json.loads(line.strip())
                
                if entry.get('type') in ['model_request', 'model_response']:
                    agent = entry.get('agent', 'Unknown')
                    timestamp = entry.get('timestamp', '')
                    entry_type = entry.get('type')
                    ticker = entry.get('ticker', 'Unknown')
                    
                    agent_calls[agent].append({
                        'type': entry_type,
                        'timestamp': timestamp,
                        'ticker': ticker,
                        'line': line_num
                    })
                    
            except json.JSONDecodeError as e:
                print(f"❌ 第{line_num}行JSON解析错误: {e}")
                continue
    
    # 分析结果
    print(f"📊 发现 {len(agent_calls)} 个Agent的LLM调用")
    print()
    
    for agent, calls in agent_calls.items():
        print(f"🤖 Agent: {agent}")
        print(f"   总调用数: {len(calls)}")
        
        # 按类型分组
        requests = [c for c in calls if c['type'] == 'model_request']
        responses = [c for c in calls if c['type'] == 'model_response']
        
        print(f"   📤 请求数: {len(requests)}")
        print(f"   📥 响应数: {len(responses)}")
        
        # 检查请求-响应配对
        if len(requests) == len(responses):
            print("   ✅ 请求-响应配对正确")
        else:
            print(f"   ❌ 请求-响应不匹配！请求{len(requests)}个，响应{len(responses)}个")
        
        # 显示调用详情
        print("   📋 调用详情:")
        for i, call in enumerate(calls, 1):
            call_type = "📤 请求" if call['type'] == 'model_request' else "📥 响应"
            print(f"      {i}. {call_type} | {call['ticker']} | {call['timestamp'][:19]}")
        
        print("-" * 60)
    
    # 总结
    total_requests = sum(len([c for c in calls if c['type'] == 'model_request']) for calls in agent_calls.values())
    total_responses = sum(len([c for c in calls if c['type'] == 'model_response']) for calls in agent_calls.values())
    
    print(f"📈 总计:")
    print(f"   📤 总请求数: {total_requests}")
    print(f"   📥 总响应数: {total_responses}")
    print(f"   🤖 使用LLM的Agent数: {len(agent_calls)}")
    
    # 检查是否有多次调用的agent
    multi_call_agents = [agent for agent, calls in agent_calls.items() 
                        if len([c for c in calls if c['type'] == 'model_request']) > 1]
    
    if multi_call_agents:
        print(f"\n🔄 多次调用LLM的Agent:")
        for agent in multi_call_agents:
            requests = [c for c in agent_calls[agent] if c['type'] == 'model_request']
            print(f"   - {agent}: {len(requests)} 次调用")
    else:
        print(f"\n✅ 所有Agent都只调用LLM一次")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        jsonl_file = sys.argv[1]
    else:
        # 查找最新的日志文件
        logs_dir = Path("logs")
        if logs_dir.exists():
            log_dirs = [d for d in logs_dir.iterdir() if d.is_dir()]
            if log_dirs:
                latest_dir = max(log_dirs, key=lambda x: x.name)
                jsonl_file = latest_dir / "structured_log.jsonl"
            else:
                print("❌ 没有找到日志目录")
                sys.exit(1)
        else:
            print("❌ logs目录不存在")
            sys.exit(1)
    
    analyze_llm_calls(jsonl_file)