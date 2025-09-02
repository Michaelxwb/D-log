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

- **containers**: List of container names to monitor (empty = all containers)
- **log_levels**: Log levels to trigger notifications (INFO, WARN, ERROR)
- **keywords**: Keywords to filter log messages
- **check_interval**: Seconds between log checks (default: 5)
- **error_threshold**: Number of occurrences before notification (default: 3)
- **cooldown_minutes**: Minutes to wait before sending duplicate notifications (default: 30)
- **deduplication_window**: Seconds to keep error history for deduplication (default: 300)
- **max_memory_entries**: Maximum number of error entries to keep in memory (default: 1000)
- **cleanup_interval**: Seconds between memory cleanup cycles (default: 3600)
- **blacklist**: Blacklist configuration
  - **keywords**: List of keywords to exclude from notifications
  - **patterns**: List of regex patterns to exclude from notifications
  - **containers**: List of container names to exclude from monitoring
- **mattermost**: Mattermost notification settings