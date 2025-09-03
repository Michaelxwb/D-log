# Docker Log Monitor

A Python script for monitoring Docker container logs with configurable filtering and Mattermost notifications.

## Features

- Monitor specific Docker containers or all running containers
- Filter logs by log levels (INFO, WARN, ERROR)
- Filter logs by keywords
- Real-time notifications via Mattermost
- Configurable via JSON configuration file

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Create configuration file:
```bash
python docker_log_monitor.py --setup
```

## Configuration

Edit `config.json` to customize monitoring:

```json
{
  "containers": ["container1", "container2"],
  "log_levels": ["ERROR", "WARN"],
  "keywords": ["exception", "failed", "timeout"],
  "mattermost": {
    "server_url": "dim2.sangfor.com",
    "token": "your-token-here",
    "channel_id": "your-channel-id",
    "scheme": "https",
    "port": 443,
    "userid": "your-user-id"
  },
  "check_interval": 5,
  "error_threshold": 3,
  "cooldown_minutes": 30,
  "deduplication_window": 300,
  "blacklist": {
    "keywords": ["debug", "trace", "test"],
    "patterns": [".*\.tmp\..*", ".*\.log\..*"],
    "containers": ["temp-container", "debug-container"]
  }
}

## Usage

Run the monitor:
```bash
python docker_log_monitor.py
```

Use custom configuration file:
```bash
python docker_log_monitor.py --config custom_config.json
```

## Configuration Options & Usage Guide

### 📦 containers
**用途**: 指定要监控的Docker容器名称列表
**示例**:
```json
"containers": ["nginx", "mysql", "redis"]
// 空数组表示监控所有运行中的容器
"containers": []
```

### 🎯 log_levels
**用途**: 设置触发通知的日志级别
**可选值**: `["INFO", "WARN", "ERROR"]`
**示例**:
```json
// 只监控ERROR级别
"log_levels": ["ERROR"]
// 监控WARN和ERROR级别
"log_levels": ["WARN", "ERROR"]
// 监控所有级别
"log_levels": ["INFO", "WARN", "ERROR"]
```

### 🔍 keywords
**用途**: 设置关键字过滤，只有包含这些关键字的日志才会触发通知
**示例**:
```json
// 监控包含异常相关关键字的日志
"keywords": ["exception", "error", "failed", "timeout", "crash"]
// 不设置关键字过滤（监控所有匹配级别的日志）
"keywords": []
```

### ⏱️ check_interval
**用途**: 设置检查日志的时间间隔（秒）
**建议值**: 5-30秒
**示例**:
```json
// 每5秒检查一次
"check_interval": 5
// 每30秒检查一次（减少系统负载）
"check_interval": 30
```

### 🔢 error_threshold
**用途**: 设置相同错误触发通知的阈值次数
**示例**:
```json
// 相同错误出现3次才通知（避免误报）
"error_threshold": 3
// 立即通知（每次错误都发送）
"error_threshold": 1
// 高阈值（减少通知频率）
"error_threshold": 10
```

### 🕒 cooldown_minutes
**用途**: 设置相同错误通知的冷却时间（分钟）
**示例**:
```json
// 30分钟内不重复发送相同错误通知
"cooldown_minutes": 30
// 1小时内不重复发送
"cooldown_minutes": 60
// 关闭冷却（不推荐）
"cooldown_minutes": 0
```

### 🧠 Memory Management

#### deduplication_window
**用途**: 错误去重的时间窗口（秒）
**示例**:
```json
// 5分钟内相同的错误视为同一个
"deduplication_window": 300
// 1小时内相同的错误视为同一个
"deduplication_window": 3600
```

#### max_memory_entries
**用途**: 内存中最大错误条目数，防止内存泄漏
**示例**:
```json
// 最多保留1000个错误记录
"max_memory_entries": 1000
// 高内存环境可增大
"max_memory_entries": 5000
```

#### cleanup_interval
**用途**: 内存清理周期（秒）
**示例**:
```json
// 每小时清理一次过期数据
"cleanup_interval": 3600
// 每6小时清理一次
"cleanup_interval": 21600
```

### 🚫 blacklist
**用途**: 设置日志黑名单，匹配的内容将被忽略

#### keywords
**用途**: 关键字黑名单，日志中包含这些关键字将被忽略
**示例**:
```json
"keywords": [
  "debug",
  "trace",
  "test",
  "CPendingDeprecationWarning",
  "broker_connection_retry"
]
```

#### patterns
**用途**: 正则表达式黑名单，更灵活的匹配规则
**示例**:
```json
"patterns": [
  ".*WARNING/MainProcess.*celery.*consumer.*",
  ".*app.utils.database.*WARNING.*索引已存在.*",
  ".*IndexOptionsConflict.*expireAfterSeconds.*",
  ".*An equivalent index already exists.*"
]
```

#### containers
**用途**: 容器黑名单，完全跳过这些容器的监控
**示例**:
```json
"containers": [
  "temp-container",
  "debug-container",
  "test-mysql"
]
```

### 📱 mattermost
**用途**: Mattermost通知配置

#### 完整配置示例:
```json
"mattermost": {
  "server_url": "your-mattermost-server.com",
  "token": "your-bot-token",
  "channel_id": "your-channel-id",
  "scheme": "https",
  "port": 443,
  "userid": "your-user-id"
}
```

#### 获取配置值的方法:
1. **server_url**: Mattermost服务器域名（不含https://）
2. **token**: 在Mattermost中创建Bot用户后获取的访问令牌
3. **channel_id**: 频道URL中的ID或通过API获取
4. **userid**: Bot用户的ID

## 📋 配置模板

### 生产环境配置
```json
{
  "containers": ["production-app", "production-db"],
  "log_levels": ["ERROR"],
  "keywords": ["critical", "fatal", "panic"],
  "error_threshold": 1,
  "cooldown_minutes": 5,
  "blacklist": {
    "keywords": ["debug", "info"],
    "patterns": [".*healthcheck.*", ".*metrics.*"]
  }
}
```

### 开发环境配置
```json
{
  "containers": [],
  "log_levels": ["WARN", "ERROR"],
  "keywords": [],
  "error_threshold": 3,
  "cooldown_minutes": 30,
  "blacklist": {
    "keywords": ["debug", "trace"],
    "containers": ["temp-*", "test-*"]
  }
}
```

### 监控特定服务
```json
{
  "containers": ["nginx", "mysql", "redis"],
  "log_levels": ["ERROR", "WARN"],
  "keywords": ["connection refused", "timeout", "memory", "disk"],
  "blacklist": {
    "patterns": [".*slow query.*", ".*performance_schema.*"]
  }
}
```