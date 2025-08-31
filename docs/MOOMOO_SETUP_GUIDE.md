# Moomoo OpenD 设置指南

本指南将帮助您设置Moomoo OpenD，以便与AI对冲基金系统集成。

## 📋 前置要求

### 1. Moomoo账户
- 注册Moomoo账户: https://www.moomoo.com/
- 完成身份验证
- 开通模拟交易功能

### 2. 系统要求
- Windows 10/11 或 macOS 10.14+ 或 Ubuntu 18.04+
- Python 3.8+
- 稳定的网络连接

## 🚀 安装步骤

### 步骤1: 下载Moomoo OpenD

1. 访问 [Moomoo OpenAPI官网](https://openapi.moomoo.com/)
2. 点击"下载OpenD"
3. 选择适合您操作系统的版本:
   - Windows: `MoomooOpenD_Win.exe`
   - macOS: `MoomooOpenD_Mac.dmg`
   - Linux: `MoomooOpenD_Linux.tar.gz`

### 步骤2: 安装OpenD

#### Windows:
1. 运行下载的 `MoomooOpenD_Win.exe`
2. 按照安装向导完成安装
3. 默认安装路径: `C:\Program Files\Moomoo\OpenD`

#### macOS:
1. 打开下载的 `MoomooOpenD_Mac.dmg`
2. 将OpenD拖拽到Applications文件夹
3. 首次运行时允许安全权限

#### Linux:
```bash
tar -xzf MoomooOpenD_Linux.tar.gz
cd MoomooOpenD_Linux
chmod +x MoomooOpenD
```

### 步骤3: 启动OpenD

#### Windows:
1. 从开始菜单启动"Moomoo OpenD"
2. 或者双击桌面快捷方式

#### macOS:
1. 从Applications文件夹启动OpenD
2. 或者使用Spotlight搜索"OpenD"

#### Linux:
```bash
./MoomooOpenD
```

### 步骤4: 配置OpenD

1. **首次启动配置**:
   - 端口设置: 保持默认 `11111`
   - API密钥: 如果需要，在Moomoo开发者中心获取
   - 日志级别: 建议设置为 `INFO`

2. **登录账户**:
   - 使用您的Moomoo账户登录
   - 确保账户已开通模拟交易功能

3. **验证连接**:
   - OpenD启动后，状态栏应显示"已连接"
   - 端口11111应该处于监听状态

## 🔧 验证安装

### 方法1: 使用我们的检查脚本
```bash
python check_moomoo_api.py
```

### 方法2: 手动验证
1. 打开命令行/终端
2. 运行以下命令检查端口:

**Windows:**
```cmd
netstat -an | findstr :11111
```

**macOS/Linux:**
```bash
netstat -an | grep :11111
```

如果看到类似 `TCP 127.0.0.1:11111 LISTENING` 的输出，说明OpenD正在运行。

### 方法3: 浏览器测试
在浏览器中访问: `http://127.0.0.1:11111`
如果看到OpenD的状态页面，说明服务正常运行。

## 🛠️ 常见问题解决

### 问题1: 端口被占用
**错误**: `Address already in use: 11111`

**解决方案**:
1. 检查是否有其他OpenD实例在运行
2. 重启计算机
3. 更改OpenD端口设置

### 问题2: 无法连接到服务器
**错误**: `Connection refused`

**解决方案**:
1. 确保OpenD正在运行
2. 检查防火墙设置
3. 验证网络连接

### 问题3: 登录失败
**错误**: `Login failed`

**解决方案**:
1. 验证Moomoo账户凭据
2. 确保账户已激活
3. 检查网络连接
4. 联系Moomoo客服

### 问题4: 模拟交易不可用
**错误**: `Paper trading not available`

**解决方案**:
1. 在Moomoo应用中开通模拟交易
2. 等待账户审核通过
3. 确保使用正确的交易环境

## 📊 OpenD状态监控

### 检查OpenD状态
```python
import socket

def check_opend_status():
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(3)
        result = sock.connect_ex(('127.0.0.1', 11111))
        sock.close()
        return result == 0
    except:
        return False

if check_opend_status():
    print("✅ OpenD is running")
else:
    print("❌ OpenD is not running")
```

### OpenD日志位置
- **Windows**: `%APPDATA%\Moomoo\OpenD\logs\`
- **macOS**: `~/Library/Application Support/Moomoo/OpenD/logs/`
- **Linux**: `~/.moomoo/opend/logs/`

## 🔐 安全设置

### 1. 网络安全
- OpenD默认只监听本地地址(127.0.0.1)
- 不要将OpenD暴露到公网
- 使用防火墙限制访问

### 2. 账户安全
- 使用强密码
- 启用两步验证
- 定期更换API密钥

### 3. 交易安全
- 优先使用模拟交易测试
- 设置合理的仓位限制
- 监控交易活动

## 📱 移动端配置

如果您需要在移动设备上监控:

1. **Moomoo手机应用**:
   - 下载官方Moomoo应用
   - 登录同一账户
   - 可以查看OpenD执行的交易

2. **远程访问** (高级用户):
   - 配置VPN或SSH隧道
   - 确保安全连接
   - 不建议直接暴露OpenD端口

## 🎯 下一步

OpenD设置完成后，您可以:

1. **运行API测试**:
   ```bash
   python check_moomoo_api.py
   ```

2. **测试集成**:
   ```bash
   python test_moomoo_integration.py
   ```

3. **运行完整系统**:
   ```bash
   python run_with_moomoo.py --config config_moomoo.yaml
   ```

## 📞 获取帮助

如果遇到问题:

1. **官方文档**: https://openapi.moomoo.com/docs/
2. **开发者社区**: https://community.moomoo.com/
3. **技术支持**: 通过Moomoo应用联系客服
4. **GitHub Issues**: 在我们的项目中提交问题

---

**重要提醒**: 
- 本集成仅用于教育和研究目的
- 模拟交易不涉及真实资金
- 实盘交易请谨慎操作并充分了解风险