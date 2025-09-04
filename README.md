# Docker日志监控器

一个功能强大的Python脚本，用于监控Docker容器日志，支持可配置过滤和Mattermost通知。专为中文用户优化，确保错误日志完整不截断。

## 🌟 核心特性

- ✅ **零截断监控**：确保连续错误日志完整捕获，不丢失任何调试信息
- 🔍 **智能上下文聚合**：自动识别堆栈跟踪，聚合多行错误上下文
- 📊 **高并发处理**：内置缓冲机制，应对高频错误日志流
- 🎯 **精准过滤**：支持按日志级别、关键词、容器名称过滤
- 📱 **实时通知**：通过Mattermost即时推送错误警报
- ⚙️ **灵活配置**：JSON配置文件，支持运行时调整
- 🧠 **智能去重**：基于错误内容智能去重，避免重复通知
- 🎨 **中文优化**：完整中文界面和文档，本土化体验

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 创建配置文件

```bash
python src/main.py --setup
```

### 3. 启动监控

```bash
python src/main.py
```

## 📋 使用方式

### 基本命令
```bash
# 启动监控
python src/main.py

# 创建默认配置文件
python src/main.py --setup

# 使用自定义配置文件
python src/main.py --config custom_config.json

# 查看帮助
python src/main.py --help
```

### 基础配置示例

```json
{
  "containers": ["nginx", "mysql", "redis"],
  "log_levels": ["ERROR", "WARN"],
  "keywords": ["异常", "错误", "失败", "超时", "崩溃"],
  "check_interval": 5,
  "error_threshold": 3,
  "cooldown_minutes": 30
}
```

### 高级上下文配置

```json
{
  "context_settings": {
    "max_context_lines": 25,
    "stack_trace_lines": 15,
    "include_surrounding_lines": 5,
    "max_log_length": 8000,
    "buffer_size": 1000,
    "enable_smart_truncation": true
  }
}
```

## ⚙️ 配置参数详解

### 📦 容器配置 (`containers`)
- **用途**: 指定要监控的Docker容器
- **示例**:
  ```json
  // 监控特定容器
  "containers": ["nginx", "mysql", "redis"]
  
  // 监控所有运行中的容器
  "containers": []
  ```

### 🎯 日志级别 (`log_levels`)
- **可选值**: `["INFO", "WARN", "ERROR"]`
- **推荐配置**:
  ```json
  // 生产环境：只监控ERROR
  "log_levels": ["ERROR"]
  
  // 开发环境：监控WARN和ERROR
  "log_levels": ["WARN", "ERROR"]
  
  // 调试模式：监控所有级别
  "log_levels": ["INFO", "WARN", "ERROR"]
  ```

### 🔍 关键词过滤 (`keywords`)
- **用途**: 只监控包含指定关键词的日志
- **中文关键词示例**:
  ```json
  "keywords": [
    "异常", "错误", "失败", "超时", "崩溃", 
    "exception", "error", "failed", "timeout", "panic"
  ]
  ```

### 🚫 黑名单配置 (`blacklist`)

#### 关键词黑名单
```json
"blacklist": {
  "keywords": [
    "debug", "调试", "测试", "test",
    "CPendingDeprecationWarning", "broker_connection_retry"
  ]
}
```

#### 正则表达式黑名单
```json
"blacklist": {
  "patterns": [
    ".*WARNING/MainProcess.*celery.*consumer.*",
    ".*健康检查.*", 
    ".*性能指标.*",
    ".*慢查询.*", 
    ".*performance_schema.*"
  ]
}
```

#### 容器黑名单
```json
"blacklist": {
  "containers": ["temp-*", "debug-*", "test-*"]
}
```

### 📱 通知配置 (`notifications`)

#### 多通知类型支持
现在支持多种通知类型，可以同时启用多个：

**Mattermost通知：**
```json
"notifications": {
  "mattermost": {
    "enabled": true,
    "server_url": "your-mattermost-server.com",
    "token": "your-bot-token",
    "channel_id": "your-channel-id",
    "scheme": "https",
    "port": 443,
    "userid": "your-user-id"
  }
}
```

**邮件通知：**
```json
"notifications": {
  "email": {
    "enabled": true,
    "smtp_server": "smtp.gmail.com",
    "smtp_port": 465,
    "username": "your-email@gmail.com",
    "password": "your-app-password",
    "from_email": "your-email@gmail.com",
    "to_emails": ["admin@example.com", "dev-team@example.com"],
    "ssl": true
  }
}
```

**多通知组合：**
```json
"notifications": {
  "mattermost": {
    "enabled": true,
    "server_url": "your-mattermost-server.com",
    "token": "your-bot-token",
    "channel_id": "your-channel-id",
    "scheme": "https",
    "port": 443,
    "userid": "your-user-id"
  },
  "email": {
    "enabled": true,
    "smtp_server": "smtp.gmail.com",
    "smtp_port": 465,
    "username": "your-email@gmail.com",
    "password": "your-app-password",
    "from_email": "your-email@gmail.com",
    "to_emails": ["admin@example.com"],
    "ssl": true
  }
}
```

### ⏱️ 时间相关配置

| 参数 | 说明 | 推荐值 |
|---|---|---|
| `check_interval` | 检查间隔（秒） | 5-30 |
| `error_threshold` | 错误触发阈值 | 1-10 |
| `cooldown_minutes` | 冷却时间（分钟） | 5-60 |
| `deduplication_window` | 去重时间窗口（秒） | 300-3600 |

### 🧠 内存管理配置

| 参数 | 说明 | 推荐值 |
|---|---|---|
| `max_memory_entries` | 最大内存条目数 | 1000-5000 |
| `cleanup_interval` | 清理周期（秒） | 3600-21600 |

### 🎯 上下文配置 (`context_settings`)

#### 核心参数
```json
{
  "context_settings": {
    "max_context_lines": 25,        // 最大上下文行数
    "stack_trace_lines": 15,        // 堆栈跟踪行数
    "include_surrounding_lines": 5, // 前后文行数
    "max_log_length": 8000,         // 最大日志长度
    "buffer_size": 1000,            // 缓冲区大小
    "enable_smart_truncation": true // 智能截断
  }
}
```

#### 上下文优化建议
- **开发环境**: 增大`max_context_lines`和`stack_trace_lines`便于调试
- **生产环境**: 适当减小避免通知过长
- **高并发**: 增大`buffer_size`防止日志丢失

## 📁 项目结构

重构后的项目采用模块化设计：

```
D-log/
├── src/                      # 源代码目录
│   ├── core/                # 核心功能
│   │   ├── config.py        # 配置管理
│   │   └── monitor.py       # 监控逻辑
│   ├── notifications/       # 通知系统
│   │   ├── base.py          # 通知基类
│   │   ├── factory.py       # 通知工厂
│   │   ├── mattermost.py    # Mattermost通知
│   │   └── email.py         # 邮件通知
│   ├── utils/               # 工具类
│   │   └── logger.py        # 日志工具
│   ├── config/              # 配置模块
│   └── main.py              # 主应用
├── tests/                   # 测试目录
├── docs/                    # 文档目录
├── examples/                # 示例配置
├── src/main.py              # 统一入口脚本
├── config.json              # 配置文件
└── requirements.txt         # 依赖列表
```

## 📊 使用场景配置模板

### 🏭 生产环境配置
```json
{
  "containers": ["production-app", "production-db"],
  "log_levels": ["ERROR"],
  "keywords": ["critical", "fatal", "panic", "异常", "崩溃"],
  "error_threshold": 1,
  "cooldown_minutes": 5,
  "context_settings": {
    "max_context_lines": 15,
    "stack_trace_lines": 10,
    "max_log_length": 4000
  },
  "blacklist": {
    "keywords": ["debug", "info", "调试", "信息"],
    "patterns": [".*healthcheck.*", ".*metrics.*", ".*健康检查.*"]
  },
  "notifications": {
    "mattermost": {
      "enabled": true,
      "server_url": "your-mattermost-server.com",
      "token": "your-bot-token",
      "channel_id": "alerts-channel",
      "scheme": "https",
      "port": 443,
      "userid": "your-bot-userid"
    },
    "email": {
      "enabled": true,
      "smtp_server": "smtp.company.com",
      "smtp_port": 587,
      "username": "alerts@company.com",
      "password": "your-password",
      "from_email": "alerts@company.com",
      "to_emails": ["devops@company.com", "admin@company.com"],
      "ssl": false
    }
  }
}
```

### 🔧 开发环境配置
```json
{
  "containers": [],
  "log_levels": ["WARN", "ERROR"],
  "keywords": [],
  "error_threshold": 3,
  "cooldown_minutes": 30,
  "context_settings": {
    "max_context_lines": 30,
    "stack_trace_lines": 20,
    "max_log_length": 10000
  },
  "notifications": {
    "mattermost": {
      "enabled": true,
      "server_url": "localhost",
      "token": "dev-token",
      "channel_id": "dev-alerts",
      "scheme": "http",
      "port": 8065,
      "userid": "dev-bot"
    }
  }
}
```

### 🎯 特定服务监控
```json
{
  "containers": ["nginx", "mysql", "redis", "elasticsearch"],
  "log_levels": ["ERROR", "WARN"],
  "keywords": [
    "连接被拒绝", "超时", "内存", "磁盘", "连接失败",
    "connection refused", "timeout", "memory", "disk", "oom"
  ],
  "blacklist": {
    "patterns": [
      ".*慢查询.*", 
      ".*performance_schema.*",
      ".*slow query.*", 
      ".*performance_schema.*"
    ]
  }
}
```

## 🎨 通知格式示例

### 标准错误通知
```
## 🚨 Docker Alert

**📦 Container:** `web-app`
**🔢 Count:** `3/3` ✅
**⏰ Time:** `2024-09-04 15:30:25 CST`
**📊 Context Lines:** `12`

**📄 Complete Error Context:
```
⬆️  [INFO] Starting application...
⬆️  [INFO] Database connection established
🔴 [ERROR] Database connection failed: Connection timeout after 30s
📍   File "/app/db.py", line 45, in connect
📍     raise ConnectionError("Timeout connecting to database")
📍   File "/app/main.py", line 23, in <module>
📍     db = connect()
⬇️  [WARN] Retrying connection in 5 seconds...
```
```

### 堆栈跟踪通知
```
## 🚨 Docker Alert - Stack Trace

**📦 Container:** `api-service`
**🔢 Count:** `1/1` ✅
**⏰ Time:** `2024-09-04 15:35:42 CST`
**📊 Context Lines:** `18`

**📄 Complete Error Context:
```
🔴 Exception in thread "main" java.lang.NullPointerException
📍   at com.example.ApiController.handleRequest(ApiController.java:156)
📍   at com.example.ApiController.processData(ApiController.java:89)
📍   at com.example.Main.main(Main.java:23)
⬇️  [ERROR] Application terminated with exit code 1
```
```

## 🔧 高级功能

### 1. 零截断保证
- **智能缓冲**: 自动检测高频错误并启用缓冲模式
- **上下文聚合**: 自动识别并聚合相关错误行
- **内存保护**: 防止内存泄漏的自动清理机制

### 2. 错误去重算法
- **内容哈希**: 基于错误内容生成唯一标识
- **时间窗口**: 可配置的去重时间窗口
- **智能合并**: 相似错误智能合并通知

### 3. 性能优化
- **增量检查**: 只检查新产生的日志
- **内存管理**: 定期清理过期数据
- **并发安全**: 支持多容器并发监控

## 🐛 故障排除

### 常见问题

#### 1. 容器连接失败
```bash
# 检查Docker服务状态
sudo systemctl status docker

# 检查用户权限
sudo usermod -aG docker $USER
```

#### 2. Mattermost通知失败
```bash
# 检查网络连通性
curl -I https://your-mattermost-server.com

# 验证token权限
python -c "from mattermostdriver import Driver; Driver({'url': 'your-server', 'token': 'your-token'}).login()"
```

#### 3. 邮件通知配置
**Gmail配置示例：**
```json
"email": {
  "enabled": true,
  "smtp_server": "smtp.gmail.com",
  "smtp_port": 465,
  "username": "your-email@gmail.com",
  "password": "your-app-password",
  "from_email": "your-email@gmail.com",
  "to_emails": ["recipient@example.com"],
  "ssl": true
}
```

**企业邮箱配置示例：**
```json
"email": {
  "enabled": true,
  "smtp_server": "smtp.company.com",
  "smtp_port": 587,
  "username": "alerts@company.com",
  "password": "your-password",
  "from_email": "alerts@company.com",
  "to_emails": ["team@company.com"],
  "ssl": false
}
```

#### 4. 内存使用过高
```json
// 调整内存配置
{
  "max_memory_entries": 500,
  "cleanup_interval": 1800,
  "context_settings": {
    "max_context_lines": 10,
    "max_log_length": 2000
  }
}
```

## 📈 性能指标

### 监控指标
- **内存使用**: 当前内存中的错误条目数
- **处理延迟**: 从错误产生到通知的平均延迟
- **成功率**: 通知发送成功率
- **去重效率**: 重复错误过滤率

### 性能调优
```json
{
  "check_interval": 10,      // 降低检查频率减少CPU使用
  "error_threshold": 5,      // 提高阈值减少通知频率
  "max_memory_entries": 500, // 减少内存占用
  "cleanup_interval": 1800   // 增加清理间隔
}
```

## 🤝 贡献指南

欢迎提交Issue和Pull Request！

### 开发环境设置
```bash
git clone https://github.com/your-repo/docker-log-monitor.git
cd docker-log-monitor
pip install -r requirements.txt
python src/main.py --config dev_config.json
```

## 📄 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件

## 📞 联系方式

- **Issues**: [GitHub Issues](https://github.com/your-repo/issues)
- **讨论**: [GitHub Discussions](https://github.com/your-repo/discussions)
- **文档**: [Wiki](https://github.com/your-repo/wiki)

---

**🎯 专为中文用户优化的Docker日志监控解决方案**