#!/usr/bin/env python3
import docker
import json
import time
import re
import argparse
import sys
from datetime import datetime
from mattermostdriver import Driver

# 强制无缓冲输出
sys.stdout.reconfigure(line_buffering=True)
sys.stderr.reconfigure(line_buffering=True)

class DockerLogMonitor:
    def __init__(self, config_file='config.json'):
        self.config = self.load_config(config_file)
        self.docker_client = docker.from_env()
        self.last_log_timestamps = {}
        self.error_counts = {}
        self.last_notification_time = {}
        self.last_cleanup_time = time.time()
        self.cleanup_counter = 0
        
    def load_config(self, config_file):
        try:
            with open(config_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return self.get_default_config()
    
    def get_default_config(self):
        return {
            "containers": [],
            "log_levels": ["ERROR", "WARN"],
            "keywords": [],
            "blacklist": {
                "keywords": [],
                "patterns": [],
                "containers": []
            },
            "mattermost": {
                "server_url": "dim2.sangfor.com",
                "token": "hnq1yj4yx3833nk9pn53srhtze",
                "channel_id": "1kaj86kbkpgtzn6gaoybepqp7w",
                "scheme": "https",
                "port": 443,
                "userid": "ddabaxgumvfidnhbwwnehpgjaq"
            },
            "check_interval": 5,
            "error_threshold": 3,
            "cooldown_minutes": 30,
            "deduplication_window": 300,
            "max_memory_entries": 1000,
            "cleanup_interval": 3600
        }
    
    def save_config(self, config_file='config.json'):
        with open(config_file, 'w') as f:
            json.dump(self.config, f, indent=2)
    
    def new_driver(self):
        driver = Driver({
            'url': self.config['mattermost']['server_url'],
            'token': self.config['mattermost']['token'],
            'scheme': self.config['mattermost']['scheme'],
            'port': self.config['mattermost']['port']
        })
        driver.client.token = self.config['mattermost']['token']
        driver.client.userid = self.config['mattermost']['userid']
        return driver
    
    def send_msg(self, msg):
        try:
            driver = self.new_driver()
            driver.posts.create_post({
                'channel_id': self.config['mattermost']['channel_id'],
                'message': msg
            })
            print("📢 Notification sent successfully!")
        except Exception as e:
            print(f"❌ Failed to send notification: {e}")
    
    def matches_log_level(self, log_line):
        log_levels = self.config.get('log_levels', [])
        if not log_levels:
            return True
        
        log_line_upper = log_line.upper()
        for level in log_levels:
            if level.upper() in log_line_upper:
                return True
        return False
    
    def matches_keywords(self, log_line):
        keywords = self.config.get('keywords', [])
        if not keywords:
            return True
        
        log_line_lower = log_line.lower()
        for keyword in keywords:
            if keyword.lower() in log_line_lower:
                return True
        return False
    
    def is_blacklisted(self, container_name, log_line):
        blacklist = self.config.get('blacklist', {})
        
        # Check blacklisted containers
        blacklisted_containers = blacklist.get('containers', [])
        if container_name in blacklisted_containers:
            return True
        
        # Check blacklisted keywords
        blacklisted_keywords = blacklist.get('keywords', [])
        log_line_lower = log_line.lower()
        for keyword in blacklisted_keywords:
            if keyword.lower() in log_line_lower:
                return True
        
        # Check blacklisted patterns (regex)
        blacklisted_patterns = blacklist.get('patterns', [])
        for pattern in blacklisted_patterns:
            try:
                if re.search(pattern, log_line, re.IGNORECASE):
                    return True
            except re.error:
                # Invalid regex pattern, skip it
                continue
        
        return False
    
    def should_notify(self, container_name, log_line):
        if self.is_blacklisted(container_name, log_line):
            return False
        return self.matches_log_level(log_line) and self.matches_keywords(log_line)
    
    def get_error_key(self, container_name, log_line):
        """Generate a unique key for error deduplication"""
        # Extract the log message without timestamp
        parts = log_line.split(' ', 1)
        if len(parts) > 1:
            message = parts[1]
        else:
            message = log_line
        
        # Normalize the message for deduplication
        message = re.sub(r'\d+', 'X', message)  # Replace numbers with X
        message = re.sub(r'[a-f0-9]{8,}', 'HASH', message)  # Replace hashes
        message = message.strip()
        
        return f"{container_name}:{message[:100]}"  # Truncate for memory efficiency
    
    def can_send_notification(self, error_key):
        """Check if we should send notification based on threshold and cooldown"""
        current_time = time.time()
        
        # Initialize error count if not exists
        if error_key not in self.error_counts:
            self.error_counts[error_key] = 0
        
        # Check cooldown period
        last_notification = self.last_notification_time.get(error_key, 0)
        cooldown_seconds = self.config.get('cooldown_minutes', 30) * 60
        
        if current_time - last_notification < cooldown_seconds:
            # Still increment count during cooldown, but don't notify
            self.error_counts[error_key] += 1
            return False
        
        # Increment error count
        self.error_counts[error_key] += 1
        
        # Check if threshold is reached
        threshold = self.config.get('error_threshold', 3)
        if self.error_counts[error_key] >= threshold:
            self.last_notification_time[error_key] = current_time
            # Reset count after notification
            self.error_counts[error_key] = 0
            return True
        
        return False
    
    def cleanup_old_errors(self):
        """Clean up old error entries to prevent memory growth"""
        current_time = time.time()
        window = self.config.get('deduplication_window', 300)  # 5 minutes default
        max_entries = self.config.get('max_memory_entries', 1000)
        
        # Clean up error counts older than window
        keys_to_remove = []
        for key, count in self.error_counts.items():
            last_time = self.last_notification_time.get(key, current_time)
            if current_time - last_time > window and count == 0:
                keys_to_remove.append(key)
        
        for key in keys_to_remove:
            self.error_counts.pop(key, None)
            self.last_notification_time.pop(key, None)
        
        # If still too many entries, remove oldest ones
        if len(self.error_counts) > max_entries:
            # Sort by last notification time and remove oldest
            sorted_keys = sorted(self.last_notification_time.keys(), 
                               key=lambda k: self.last_notification_time.get(k, 0))
            keys_to_remove = sorted_keys[:len(self.error_counts) - max_entries]
            for key in keys_to_remove:
                self.error_counts.pop(key, None)
                self.last_notification_time.pop(key, None)
        
        # Clean up old container timestamps for non-existent containers
        current_containers = {c.name for c in self.docker_client.containers.list()}
        containers_to_remove = []
        for container_name in self.last_log_timestamps:
            if container_name not in current_containers:
                containers_to_remove.append(container_name)
        
        for container_name in containers_to_remove:
            self.last_log_timestamps.pop(container_name, None)
    
    def should_cleanup(self):
        """Check if it's time for periodic cleanup"""
        current_time = time.time()
        cleanup_interval = self.config.get('cleanup_interval', 3600)  # 1 hour default
        
        # Cleanup every N iterations or every cleanup_interval seconds
        self.cleanup_counter += 1
        if (self.cleanup_counter >= 100 or 
            current_time - self.last_cleanup_time > cleanup_interval):
            self.last_cleanup_time = current_time
            self.cleanup_counter = 0
            return True
        return False
    
    def get_container_logs(self, container_name, since=None):
        try:
            container = self.docker_client.containers.get(container_name)
            if container.status != 'running':
                return []
            
            logs = container.logs(
                timestamps=True,
                since=since,
                tail=100
            ).decode('utf-8').strip().split('\n')
            
            return [line for line in logs if line.strip()]
        except Exception as e:
            print(f"Error getting logs for {container_name}: {e}")
            return []
    
    def parse_log_timestamp(self, log_line):
        try:
            timestamp_str = log_line.split(' ')[0]
            return datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        except:
            return None
    
    def monitor_containers(self):
        containers = self.config.get('containers', [])
        if not containers:
            containers = [c.name for c in self.docker_client.containers.list()]
        
        # Filter out blacklisted containers
        blacklist = self.config.get('blacklist', {})
        blacklisted_containers = blacklist.get('containers', [])
        containers = [c for c in containers if c not in blacklisted_containers]
        
        for container_name in containers:
            last_time = self.last_log_timestamps.get(container_name)
            
            logs = self.get_container_logs(container_name, since=last_time)
            
            for log_line in logs:
                if self.should_notify(container_name, log_line):
                    timestamp = self.parse_log_timestamp(log_line)
                    if timestamp:
                        self.last_log_timestamps[container_name] = timestamp
                    
                    error_key = self.get_error_key(container_name, log_line)
                    
                    if self.can_send_notification(error_key):
                        threshold = self.config.get('error_threshold', 3)
                        
                        # Extract clean log message without timestamp
                        log_parts = log_line.split(' ', 1)
                        clean_log = log_parts[1] if len(log_parts) > 1 else log_line
                        
                        # Format timestamp
                        timestamp_str = ""
                        if len(log_parts) > 1:
                            try:
                                ts = datetime.fromisoformat(log_parts[0].replace('Z', '+00:00'))
                                timestamp_str = ts.strftime('%Y-%m-%d %H:%M:%S')
                            except:
                                timestamp_str = log_parts[0]
                        
                        message = f"""## 🚨 Docker Alert

**📦 Container:** `{container_name}`
**🔢 Count:** `{threshold}/{threshold}` ✅
**⏰ Time:** `{timestamp_str}`

**📄 Log Message:
```
{clean_log}
```"""
                        self.send_msg(message)
        
        # Clean up old error entries periodically
        self.cleanup_old_errors()
    
    def run(self):
        print("🚀 Starting Docker log monitor...")
        print("=" * 50)
        print(f"📦 Monitoring: {self.config.get('containers', 'all containers')}")
        print(f"🎯 Log levels: {', '.join(self.config.get('log_levels', ['all']))}")
        print(f"🔍 Keywords: {', '.join(self.config.get('keywords', ['none']))}")
        print(f"⏱️  Check interval: {self.config.get('check_interval', 5)}s")
        print(f"🔢 Error threshold: {self.config.get('error_threshold', 3)} occurrences")
        print(f"🕒 Cooldown: {self.config.get('cooldown_minutes', 30)}min")
        print(f"🧠 Memory limit: {self.config.get('max_memory_entries', 1000)} entries")
        print("=" * 50)
        
        notification_count = 0
        
        while True:
            try:
                self.monitor_containers()
                
                # Periodic cleanup to prevent memory leaks
                if self.should_cleanup():
                    self.cleanup_old_errors()
                    print(f"🧹 Memory cleanup: {len(self.error_counts)} active entries")
                
                time.sleep(self.config.get('check_interval', 5))
            except KeyboardInterrupt:
                print("\n👋 Stopping monitor...")
                break
            except Exception as e:
                print(f"❌ Error: {e}")
                time.sleep(10)

def main():
    parser = argparse.ArgumentParser(description='Docker Log Monitor')
    parser.add_argument('--config', default='config.json', help='Configuration file path')
    parser.add_argument('--setup', action='store_true', help='Create default configuration file')
    
    args = parser.parse_args()
    
    if args.setup:
        monitor = DockerLogMonitor()
        monitor.save_config(args.config)
        print(f"Default configuration created at {args.config}")
        return
    
    monitor = DockerLogMonitor(args.config)
    monitor.run()

if __name__ == "__main__":
    main()