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

## Configuration Options

- **containers**：要监控的容器名称列表（空表示所有容器）
- **log_levels**：触发通知的日志级别（INFO、WARN、ERROR）
- **keywords**：用于过滤日志消息的关键字
- **check_interval**：日志检查间隔（秒）（默认值：5）
- **error_threshold**：通知前的错误发生次数（默认值：3）
- **cooldown_minutes**：发送重复通知前的等待分钟数（默认值：30）
- **deduplication_window**：保留重复数据删除错误历史记录的秒数（默认值：300）
- **max_memory_entries**：内存中保留的最大错误条目数（默认值：1000）
- **cleanup_interval**：内存清理周期间隔（秒）（默认值：3600）
- **blacklist**：黑名单配置
  - **keywords**：要排除的关键字列表来自通知
  - **patterns**：要从通知中排除的正则表达式列表
  - **containers**：要从监控中排除的容器名称列表
- **mattermost**：Mattermost 通知设置