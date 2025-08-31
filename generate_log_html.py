#!/usr/bin/env python3
"""
生成包含日志数据的HTML文件
直接将JSONL日志嵌入到HTML中，无需处理文件加载问题
"""

import json
import sys
from pathlib import Path
from datetime import datetime
import webbrowser


def find_latest_log_file():
    """查找最新的日志文件"""
    log_dir = Path("logs")
    if not log_dir.exists():
        return None
    
    # 查找所有JSONL文件
    jsonl_files = list(log_dir.glob("*/structured_log.jsonl"))
    if not jsonl_files:
        return None
    
    # 按修改时间排序，返回最新的
    jsonl_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
    return jsonl_files[0]


def load_logs(file_path):
    """加载日志文件"""
    logs = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if line:
                    try:
                        log_entry = json.loads(line)
                        logs.append(log_entry)
                    except json.JSONDecodeError as e:
                        print(f"警告: 第{line_num}行JSON格式错误: {e}")
    except Exception as e:
        print(f"错误: 无法读取日志文件: {e}")
        return []
    
    return logs


def generate_html(logs, log_file_path):
    """生成包含日志数据的HTML文件"""
    
    # 将日志数据转换为JavaScript格式
    logs_json = json.dumps(logs, ensure_ascii=False, indent=2)
    
    html_content = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI对冲基金日志查看器 - {log_file_path.parent.name}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: 'Microsoft YaHei', 'Segoe UI', sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #fff;
            min-height: 100vh;
        }}

        .container {{
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
        }}

        .header {{
            text-align: center;
            margin-bottom: 30px;
            background: rgba(255, 255, 255, 0.1);
            padding: 30px;
            border-radius: 15px;
            backdrop-filter: blur(10px);
        }}

        .header h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
            background: linear-gradient(45deg, #ff6b6b, #4ecdc4);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }}

        .header .session-info {{
            background: rgba(0,0,0,0.2);
            padding: 10px 20px;
            border-radius: 20px;
            display: inline-block;
            margin-top: 10px;
        }}

        .controls {{
            background: rgba(255, 255, 255, 0.1);
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 20px;
            display: flex;
            gap: 15px;
            flex-wrap: wrap;
            align-items: center;
            backdrop-filter: blur(10px);
        }}

        .controls input, .controls select {{
            background: rgba(255, 255, 255, 0.2);
            border: 1px solid rgba(255, 255, 255, 0.3);
            color: #fff;
            padding: 10px 15px;
            border-radius: 8px;
            font-size: 14px;
        }}

        .controls input::placeholder {{
            color: rgba(255, 255, 255, 0.7);
        }}

        .controls button {{
            background: linear-gradient(45deg, #ff6b6b, #ee5a24);
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 8px;
            cursor: pointer;
            font-weight: bold;
            transition: all 0.3s;
        }}

        .controls button:hover {{
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(0,0,0,0.3);
        }}

        .stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}

        .stat-card {{
            background: rgba(255, 255, 255, 0.1);
            padding: 20px;
            border-radius: 10px;
            text-align: center;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.2);
        }}

        .stat-value {{
            font-size: 2em;
            font-weight: bold;
            margin-bottom: 5px;
            background: linear-gradient(45deg, #4ecdc4, #44a08d);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }}

        .stat-label {{
            color: rgba(255, 255, 255, 0.8);
            font-size: 0.9em;
        }}

        .log-container {{
            background: rgba(255, 255, 255, 0.05);
            border-radius: 15px;
            padding: 20px;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.1);
        }}

        .log-entry {{
            background: rgba(255, 255, 255, 0.1);
            margin-bottom: 15px;
            border-radius: 10px;
            overflow: hidden;
            border-left: 4px solid #4ecdc4;
            transition: all 0.3s;
        }}

        .log-entry:hover {{
            transform: translateX(5px);
            box-shadow: 0 5px 20px rgba(0,0,0,0.2);
        }}

        .log-entry.system {{ border-left-color: #3498db; }}
        .log-entry.agent_start {{ border-left-color: #2ecc71; }}
        .log-entry.agent_end {{ border-left-color: #27ae60; }}
        .log-entry.model_request {{ border-left-color: #9b59b6; }}
        .log-entry.model_response {{ border-left-color: #8e44ad; }}
        .log-entry.data_fetch {{ border-left-color: #f39c12; }}
        .log-entry.decision {{ border-left-color: #e74c3c; }}
        .log-entry.error {{ border-left-color: #c0392b; }}

        .log-header {{
            padding: 15px 20px;
            display: flex;
            align-items: center;
            gap: 15px;
            cursor: pointer;
        }}

        .log-icon {{
            font-size: 24px;
            width: 30px;
            text-align: center;
        }}

        .log-timestamp {{
            font-family: 'Courier New', monospace;
            font-size: 12px;
            background: rgba(0,0,0,0.3);
            padding: 5px 10px;
            border-radius: 5px;
            min-width: 100px;
            text-align: center;
        }}

        .log-level {{
            padding: 5px 12px;
            border-radius: 15px;
            font-size: 11px;
            font-weight: bold;
            min-width: 70px;
            text-align: center;
        }}

        .log-level.DEBUG {{ background: #6c757d; }}
        .log-level.INFO {{ background: #17a2b8; }}
        .log-level.WARNING {{ background: #ffc107; color: #000; }}
        .log-level.ERROR {{ background: #dc3545; }}

        .log-agent {{
            font-weight: bold;
            background: rgba(78, 205, 196, 0.2);
            padding: 5px 10px;
            border-radius: 5px;
        }}

        .log-ticker {{
            background: rgba(52, 152, 219, 0.3);
            padding: 3px 8px;
            border-radius: 5px;
            font-size: 12px;
            font-weight: bold;
        }}

        .log-message {{
            flex: 1;
            margin-left: 10px;
            font-size: 14px;
        }}

        .log-duration {{
            background: rgba(0,0,0,0.3);
            padding: 3px 8px;
            border-radius: 5px;
            font-size: 12px;
            font-family: 'Courier New', monospace;
        }}

        .log-details {{
            padding: 20px;
            background: rgba(0,0,0,0.2);
            border-top: 1px solid rgba(255,255,255,0.1);
            display: none;
        }}

        .log-details.expanded {{
            display: block;
            animation: slideDown 0.3s ease;
        }}

        @keyframes slideDown {{
            from {{ opacity: 0; transform: translateY(-10px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}

        .detail-section {{
            margin-bottom: 15px;
        }}

        .detail-title {{
            color: #4ecdc4;
            font-weight: bold;
            margin-bottom: 8px;
            font-size: 14px;
        }}

        .detail-content {{
            background: rgba(0,0,0,0.3);
            padding: 15px;
            border-radius: 8px;
            font-family: 'Courier New', monospace;
            font-size: 12px;
            white-space: pre-wrap;
            overflow-x: auto;
            border: 1px solid rgba(255,255,255,0.1);
        }}

        .no-logs {{
            text-align: center;
            padding: 60px;
            color: rgba(255,255,255,0.7);
            font-size: 18px;
        }}

        @media (max-width: 768px) {{
            .controls {{
                flex-direction: column;
                align-items: stretch;
            }}
            
            .controls input, .controls select, .controls button {{
                width: 100%;
            }}
            
            .log-header {{
                flex-direction: column;
                align-items: flex-start;
                gap: 10px;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🤖 AI对冲基金日志查看器</h1>
            <div class="session-info">
                📁 会话: {log_file_path.parent.name} | 📊 共 {len(logs)} 条日志 | 🕒 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            </div>
        </div>

        <div class="controls">
            <input type="text" id="searchInput" placeholder="🔍 搜索日志内容..." />
            <select id="levelFilter">
                <option value="">所有级别</option>
                <option value="DEBUG">调试</option>
                <option value="INFO">信息</option>
                <option value="WARNING">警告</option>
                <option value="ERROR">错误</option>
            </select>
            <select id="typeFilter">
                <option value="">所有类型</option>
                <option value="system">系统</option>
                <option value="agent_start">Agent开始</option>
                <option value="agent_end">Agent结束</option>
                <option value="model_request">模型请求</option>
                <option value="model_response">模型响应</option>
                <option value="data_fetch">数据获取</option>
                <option value="decision">决策</option>
                <option value="error">错误</option>
            </select>
            <input type="text" id="agentFilter" placeholder="Agent名称..." />
            <button onclick="clearFilters()">清除筛选</button>
            <button onclick="exportLogs()">导出日志</button>
        </div>

        <div class="stats" id="stats">
            <div class="stat-card">
                <div class="stat-value" id="totalLogs">0</div>
                <div class="stat-label">总日志数</div>
            </div>
            <div class="stat-card">
                <div class="stat-value" id="filteredLogs">0</div>
                <div class="stat-label">筛选结果</div>
            </div>
            <div class="stat-card">
                <div class="stat-value" id="errorCount">0</div>
                <div class="stat-label">错误数量</div>
            </div>
            <div class="stat-card">
                <div class="stat-value" id="avgDuration">0ms</div>
                <div class="stat-label">平均耗时</div>
            </div>
        </div>

        <div class="log-container">
            <div id="logContent">
                <div class="no-logs">
                    <p>📭 正在加载日志...</p>
                </div>
            </div>
        </div>
    </div>

    <script>
        // 嵌入的日志数据
        const allLogs = {logs_json};
        let filteredLogs = [];

        const iconMap = {{
            'system': '⚙️',
            'agent_start': '🚀',
            'agent_end': '✅',
            'model_request': '🧠',
            'model_response': '💭',
            'data_fetch': '📊',
            'decision': '🎯',
            'error': '❌'
        }};

        const levelNames = {{
            'DEBUG': '调试',
            'INFO': '信息',
            'WARNING': '警告',
            'ERROR': '错误'
        }};

        // 页面加载时初始化
        window.addEventListener('load', function() {{
            // 设置筛选器事件
            document.getElementById('searchInput').addEventListener('input', applyFilters);
            document.getElementById('levelFilter').addEventListener('change', applyFilters);
            document.getElementById('typeFilter').addEventListener('change', applyFilters);
            document.getElementById('agentFilter').addEventListener('input', applyFilters);
            
            // 初始化显示
            applyFilters();
        }});

        function applyFilters() {{
            const search = document.getElementById('searchInput').value.toLowerCase();
            const level = document.getElementById('levelFilter').value;
            const type = document.getElementById('typeFilter').value;
            const agent = document.getElementById('agentFilter').value.toLowerCase();

            filteredLogs = allLogs.filter(log => {{
                const matchesSearch = !search || 
                    log.message?.toLowerCase().includes(search) ||
                    log.agent?.toLowerCase().includes(search) ||
                    log.ticker?.toLowerCase().includes(search);
                
                const matchesLevel = !level || log.level === level;
                const matchesType = !type || log.type === type;
                const matchesAgent = !agent || log.agent?.toLowerCase().includes(agent);

                return matchesSearch && matchesLevel && matchesType && matchesAgent;
            }});

            renderLogs();
            updateStats();
        }}

        function renderLogs() {{
            const logContent = document.getElementById('logContent');
            
            if (filteredLogs.length === 0) {{
                logContent.innerHTML = '<div class="no-logs"><p>📭 没有找到匹配的日志条目</p></div>';
                return;
            }}

            const html = filteredLogs.map((log, index) => {{
                const timestamp = formatTimestamp(log.timestamp);
                const icon = iconMap[log.type] || '📝';
                const duration = log.duration_ms ? formatDuration(log.duration_ms) : '';
                const levelName = levelNames[log.level] || log.level;
                
                return `
                    <div class="log-entry ${{log.type}}" data-index="${{index}}">
                        <div class="log-header" onclick="toggleDetails(${{index}})">
                            <span class="log-icon">${{icon}}</span>
                            <span class="log-timestamp">${{timestamp}}</span>
                            <span class="log-level ${{log.level}}">${{levelName}}</span>
                            ${{log.ticker ? `<span class="log-ticker">${{log.ticker}}</span>` : ''}}
                            <span class="log-agent">${{log.agent}}</span>
                            <span class="log-message">${{log.message}}</span>
                            ${{duration ? `<span class="log-duration">${{duration}}</span>` : ''}}
                        </div>
                        <div class="log-details" id="details-${{index}}">
                            ${{renderLogDetails(log)}}
                        </div>
                    </div>
                `;
            }}).join('');

            logContent.innerHTML = html;
        }}

        function renderLogDetails(log) {{
            let html = '';

            if (log.model) {{
                html += `
                    <div class="detail-section">
                        <div class="detail-title">🧠 模型信息</div>
                        <div class="detail-content">${{JSON.stringify(log.model, null, 2)}}</div>
                    </div>
                `;
            }}

            if (log.data) {{
                // 特殊处理prompt和response
                if (log.data.full_prompt) {{
                    html += `
                        <div class="detail-section">
                            <div class="detail-title">📝 完整Prompt (${{log.data.prompt_lines || 0}} 行)</div>
                            <div class="detail-content" style="max-height: 400px; overflow-y: auto;">${{escapeHtml(log.data.full_prompt)}}</div>
                        </div>
                    `;
                }}
                
                if (log.data.full_response) {{
                    html += `
                        <div class="detail-section">
                            <div class="detail-title">💭 完整响应 (${{log.data.response_lines || 0}} 行)</div>
                            <div class="detail-content" style="max-height: 400px; overflow-y: auto;">${{escapeHtml(log.data.full_response)}}</div>
                        </div>
                    `;
                }}
                
                // 显示其他数据（排除已单独显示的prompt和response）
                const otherData = {{}};
                for (const [key, value] of Object.entries(log.data)) {{
                    if (key !== 'full_prompt' && key !== 'full_response') {{
                        otherData[key] = value;
                    }}
                }}
                
                if (Object.keys(otherData).length > 0) {{
                    html += `
                        <div class="detail-section">
                            <div class="detail-title">📊 其他数据</div>
                            <div class="detail-content">${{JSON.stringify(otherData, null, 2)}}</div>
                        </div>
                    `;
                }}
            }}

            if (log.error) {{
                html += `
                    <div class="detail-section">
                        <div class="detail-title">❌ 错误信息</div>
                        <div class="detail-content">${{JSON.stringify(log.error, null, 2)}}</div>
                    </div>
                `;
            }}

            return html || '<div class="detail-content">暂无详细信息</div>';
        }}
        
        function escapeHtml(text) {{
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }}

        function toggleDetails(index) {{
            const details = document.getElementById(`details-${{index}}`);
            details.classList.toggle('expanded');
        }}

        function formatTimestamp(timestamp) {{
            try {{
                const date = new Date(timestamp);
                return date.toLocaleTimeString('zh-CN');
            }} catch {{
                return timestamp;
            }}
        }}

        function formatDuration(ms) {{
            if (ms >= 1000) {{
                return `${{(ms / 1000).toFixed(1)}}秒`;
            }}
            return `${{Math.round(ms)}}毫秒`;
        }}

        function updateStats() {{
            document.getElementById('totalLogs').textContent = allLogs.length;
            document.getElementById('filteredLogs').textContent = filteredLogs.length;
            
            const errorCount = filteredLogs.filter(log => log.level === 'ERROR').length;
            document.getElementById('errorCount').textContent = errorCount;

            const durationsMs = filteredLogs
                .filter(log => log.duration_ms)
                .map(log => log.duration_ms);
            
            if (durationsMs.length > 0) {{
                const avgMs = durationsMs.reduce((a, b) => a + b, 0) / durationsMs.length;
                document.getElementById('avgDuration').textContent = formatDuration(avgMs);
            }} else {{
                document.getElementById('avgDuration').textContent = '无数据';
            }}
        }}

        function clearFilters() {{
            document.getElementById('searchInput').value = '';
            document.getElementById('levelFilter').value = '';
            document.getElementById('typeFilter').value = '';
            document.getElementById('agentFilter').value = '';
            applyFilters();
        }}

        function exportLogs() {{
            const jsonl = filteredLogs.map(log => JSON.stringify(log)).join('\\n');
            const blob = new Blob([jsonl], {{ type: 'application/json' }});
            const url = URL.createObjectURL(blob);
            
            const a = document.createElement('a');
            a.href = url;
            a.download = `filtered_logs_${{new Date().toISOString().slice(0, 19).replace(/:/g, '-')}}.jsonl`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
        }}
    </script>
</body>
</html>'''
    
    return html_content


def main():
    """主函数"""
    # 查找日志文件
    if len(sys.argv) > 1:
        log_file = Path(sys.argv[1])
    else:
        log_file = find_latest_log_file()
    
    if not log_file or not log_file.exists():
        print("Log file not found")
        print("Usage: python generate_log_html.py [log_file_path]")
        print("Or ensure structured_log.jsonl exists in logs/ directory")
        return
    
    print(f"Processing log file: {log_file}")
    
    # 加载日志
    logs = load_logs(log_file)
    if not logs:
        print("Error: Log file is empty or invalid format")
        return
    
    print(f"Loaded {len(logs)} log entries")
    
    # 生成HTML
    html_content = generate_html(logs, log_file)
    
    # 保存HTML文件
    output_file = Path(f"log_viewer_{log_file.parent.name}.html")
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"HTML file generated: {output_file}")
    
    # 自动打开浏览器
    try:
        webbrowser.open(f"file://{output_file.absolute()}")
        print("Opened log viewer in browser")
    except Exception as e:
        print(f"Cannot auto-open browser: {e}")
        print(f"Please open manually: {output_file.absolute()}")


if __name__ == "__main__":
    main()