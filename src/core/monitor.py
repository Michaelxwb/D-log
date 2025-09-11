import docker
import re
import time
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional
from utils.logger import setup_logger


class DockerLogMonitor:
    """Docker日志监控核心类"""
    
    def __init__(self, config):
        self.config = config
        self.docker_client = docker.from_env()
        self.logger = setup_logger()
        
        # 状态管理
        self.last_log_timestamps = {}
        self.error_counts = {}
        self.last_notification_time = {}
        self.last_cleanup_time = time.time()
        self.cleanup_counter = 0
        self.error_contexts = {}
        self.log_buffer = {}
        self.buffer_size = config.get('context_settings.buffer_size', 1000)
    
    def get_container_logs(self, container_name: str, since=None) -> List[str]:
        """获取容器日志"""
        try:
            container = self.docker_client.containers.get(container_name)
            if container.status != 'running':
                return []
            
            # 处理since参数，确保格式正确
            since_param = None
            if since:
                if isinstance(since, str):
                    try:
                        # 将字符串时间戳转换为datetime对象
                        since_dt = datetime.fromisoformat(since.replace('Z', '+00:00'))
                        since_param = since_dt
                    except ValueError:
                        # 如果解析失败，使用None（获取所有日志）
                        since_param = None
                else:
                    since_param = since
            
            logs = container.logs(
                timestamps=True,
                since=since_param,
                tail=500,
                stream=False
            ).decode('utf-8', errors='ignore').strip().split('\n')
            
            return [line for line in logs if line.strip()]
        except Exception as e:
            self.logger.error(f"获取容器 {container_name} 日志失败: {e}")
            return []
    
    def should_notify(self, container_name: str, log_line: str) -> bool:
        """判断是否应该发送通知"""
        # 检查黑名单
        blacklist = self.config.get('blacklist', {})
        
        # 检查容器黑名单
        blacklisted_containers = blacklist.get('containers', [])
        if container_name in blacklisted_containers:
            return False
        
        # 检查关键词黑名单
        blacklisted_keywords = blacklist.get('keywords', [])
        log_line_lower = log_line.lower()
        for keyword in blacklisted_keywords:
            if keyword.lower() in log_line_lower:
                return False
        
        # 检查正则表达式黑名单
        blacklisted_patterns = blacklist.get('patterns', [])
        for pattern in blacklisted_patterns:
            try:
                if re.search(pattern, log_line, re.IGNORECASE):
                    return False
            except re.error:
                continue
        
        # 检查日志级别
        log_levels = self.config.get('log_levels', [])
        if log_levels:
            log_line_upper = log_line.upper()
            level_matched = any(level.upper() in log_line_upper for level in log_levels)
            if not level_matched:
                return False
        
        # 检查关键词
        keywords = self.config.get('keywords', [])
        if keywords:
            log_line_lower = log_line.lower()
            keyword_matched = any(keyword.lower() in log_line_lower for keyword in keywords)
            if not keyword_matched:
                return False
        
        return True
    
    def get_error_key(self, container_name: str, log_line: str) -> str:
        """生成错误唯一标识"""
        parts = log_line.split(' ', 1)
        message = parts[1] if len(parts) > 1 else log_line
        
        # 标准化消息用于去重
        message = re.sub(r'\d+', 'X', message)
        message = re.sub(r'[a-f0-9]{8,}', 'HASH', message)
        message = message.strip()
        
        return f"{container_name}:{message[:100]}"
    
    def can_send_notification(self, error_key: str) -> tuple:
        """检查是否可以发送通知，返回(should_send, current_count)"""
        current_time = time.time()
        
        if error_key not in self.error_counts:
            self.error_counts[error_key] = 0
        
        # 检查冷却时间
        last_notification = self.last_notification_time.get(error_key, 0)
        cooldown_seconds = self.config.get('cooldown_minutes', 30) * 60
        
        if current_time - last_notification < cooldown_seconds:
            self.error_counts[error_key] += 1
            return False, self.error_counts[error_key]
        
        self.error_counts[error_key] += 1
        threshold = self.config.get('error_threshold', 3)
        current_count = self.error_counts[error_key]
        
        if current_count >= threshold:
            self.last_notification_time[error_key] = current_time
            self.error_counts[error_key] = 0
            return True, current_count
        
        return False, current_count
    
    def find_error_boundaries(self, logs: List[str], error_index: int) -> tuple:
        """查找错误边界"""
        start_idx = error_index
        for i in range(error_index, max(-1, error_index - 10), -1):
            line = logs[i].lower()
            if any(keyword in line for keyword in ['error', 'exception', 'failed', 'traceback']):
                start_idx = i
            else:
                break
        
        end_idx = error_index + 1
        for i in range(error_index + 1, min(len(logs), error_index + 50)):
            if self.is_stack_trace_line(logs[i]):
                end_idx = i + 1
            else:
                if not logs[i].startswith(' ') and not logs[i].startswith('\t'):
                    break
                end_idx = i + 1
        
        return start_idx, end_idx
    
    def is_stack_trace_line(self, line: str) -> bool:
        """判断是否为堆栈跟踪行"""
        stack_indicators = [
            'Traceback (most recent call last):',
            'File "',
            'at ',
            'Caused by:',
            'Exception:',
            'Error:',
            '    at ',
            '\tat ',
            'Error in',
            'Exception in'
        ]
        line_lower = line.lower()
        return any(indicator.lower() in line_lower for indicator in stack_indicators)
    
    def aggregate_error_context(self, container_name: str, logs: List[str], error_index: int) -> str:
        """聚合错误上下文"""
        context_settings = self.config.get('context_settings', {})
        max_length = context_settings.get('max_log_length', 8000)
        
        start_idx, end_idx = self.find_error_boundaries(logs, error_index)
        
        context_lines = []
        for i in range(start_idx, min(end_idx, len(logs))):
            if i < len(logs):
                line = logs[i]
                # 保留完整的时间戳和日志内容
                clean_line = line.split(' ', 1)[1] if ' ' in line else line
                
                prefix = "  "
                if i == error_index:
                    prefix = "🔴 "
                elif self.is_stack_trace_line(clean_line):
                    prefix = "📍 "
                elif i < error_index:
                    prefix = "⬆️  "
                else:
                    prefix = "⬇️  "
                
                context_lines.append(f"{prefix}{clean_line}")
        
        full_context = '\n'.join(context_lines)
        if len(full_context) > max_length:
            half_length = max_length // 2
            full_context = full_context[:half_length] + "\n... [上下文截断] ...\n" + full_context[-half_length:]
        
        return full_context
    
    def get_monitored_containers(self) -> List[str]:
        """获取需要监控的容器列表"""
        containers = self.config.get('containers', [])
        if not containers:
            containers = [c.name for c in self.docker_client.containers.list()]
        
        # 过滤黑名单容器
        blacklist = self.config.get('blacklist', {})
        blacklisted_containers = blacklist.get('containers', [])
        containers = [c for c in containers if c not in blacklisted_containers]
        
        return containers
    
    def cleanup_old_errors(self):
        """清理旧错误数据"""
        current_time = time.time()
        window = self.config.get('deduplication_window', 300)
        max_entries = self.config.get('max_memory_entries', 1000)
        
        # 清理过期错误
        keys_to_remove = []
        for key, count in self.error_counts.items():
            last_time = self.last_notification_time.get(key, current_time)
            if current_time - last_time > window and count == 0:
                keys_to_remove.append(key)
        
        for key in keys_to_remove:
            self.error_counts.pop(key, None)
            self.last_notification_time.pop(key, None)
        
        # 内存限制清理
        if len(self.error_counts) > max_entries:
            sorted_keys = sorted(self.last_notification_time.keys(), 
                               key=lambda k: self.last_notification_time.get(k, 0))
            keys_to_remove = sorted_keys[:len(self.error_counts) - max_entries]
            for key in keys_to_remove:
                self.error_counts.pop(key, None)
                self.last_notification_time.pop(key, None)
    
    def should_cleanup(self) -> bool:
        """检查是否需要清理"""
        current_time = time.time()
        cleanup_interval = self.config.get('cleanup_interval', 3600)
        
        self.cleanup_counter += 1
        if (self.cleanup_counter >= 100 or 
            current_time - self.last_cleanup_time > cleanup_interval):
            self.last_cleanup_time = current_time
            self.cleanup_counter = 0
            return True
        return False
    
    def get_container_logs_since(self, container_name: str) -> List[str]:
        """获取容器自上次检查以来的日志"""
        last_timestamp = self.last_log_timestamps.get(container_name)
        
        logs = self.get_container_logs(container_name, since=last_timestamp)
        
        # 更新最后检查时间 - 使用Unix时间戳
        if logs:
            last_log = logs[-1]
            try:
                timestamp_str = last_log.split(' ')[0]
                # 解析Docker时间戳并转换为Unix时间戳
                dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                self.last_log_timestamps[container_name] = dt.timestamp()
            except:
                # 如果解析失败，使用当前时间
                self.last_log_timestamps[container_name] = time.time()
        
        return logs
    
    def process_container_logs(self, container_name: str) -> List[Dict[str, Any]]:
        """处理容器日志并返回错误信息"""
        logs = self.get_container_logs_since(container_name)
        if not logs:
            return []
        
        # 添加到缓冲区
        if container_name not in self.log_buffer:
            self.log_buffer[container_name] = []
        
        self.log_buffer[container_name].extend(logs)
        
        # 限制缓冲区大小
        if len(self.log_buffer[container_name]) > self.buffer_size:
            self.log_buffer[container_name] = self.log_buffer[container_name][-self.buffer_size:]
        
        errors = []
        processed_indices = set()
        
        for i, log_line in enumerate(self.log_buffer[container_name]):
            if i in processed_indices:
                continue
                
            if self.should_notify(container_name, log_line):
                error_key = self.get_error_key(container_name, log_line)
                
                should_send, current_count = self.can_send_notification(error_key)
                if should_send:
                    start_idx, end_idx = self.find_error_boundaries(
                        self.log_buffer[container_name], i
                    )
                    
                    error_context = self.aggregate_error_context(
                        container_name, self.log_buffer[container_name], start_idx
                    )
                    
                    # 标记已处理
                    for idx in range(start_idx, min(end_idx, len(self.log_buffer[container_name]))):
                        processed_indices.add(idx)
                    
                    threshold = self.config.get('error_threshold', 3)
                    
                    errors.append({
                        'container': container_name,
                        'context': error_context,
                        'count': current_count,
                        'threshold': threshold,
                        'timestamp': datetime.now(timezone(timedelta(hours=8))).strftime('%Y-%m-%d %H:%M:%S CST')
                    })
        
        # 清理已处理的日志
        self.log_buffer[container_name] = [
            log for i, log in enumerate(self.log_buffer[container_name]) 
            if i not in processed_indices
        ]
        
        return errors