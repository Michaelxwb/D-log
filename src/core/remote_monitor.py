import time
import threading
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

from .monitor import DockerLogMonitor
from .ssh_manager import RemoteDockerManager, SSHConnectionPool
from utils.logger import setup_logger


class RemoteDockerLogMonitor(DockerLogMonitor):
    """远程Docker日志监控器"""
    
    def __init__(self, config, server_config: Dict[str, Any]):
        super().__init__(config)
        self.server_config = server_config
        self.server_name = server_config.get('name', server_config['host'])
        self.remote_manager = None
        self.logger = setup_logger()
    
    def set_remote_manager(self, remote_manager: RemoteDockerManager):
        """设置远程管理器"""
        self.remote_manager = remote_manager
    
    def get_container_logs(self, container_name: str, since=None) -> List[str]:
        """获取远程容器日志"""
        if not self.remote_manager:
            return []
        
        # 处理since参数
        since_str = None
        if since:
            if isinstance(since, (int, float)):
                # Unix时间戳转换为相对时间
                since_seconds = int(time.time() - since)
                since_str = f"{since_seconds}s"
            elif isinstance(since, str):
                since_str = since
        
        return self.remote_manager.get_container_logs(
            self.server_config, 
            container_name, 
            since=since_str
        )
    
    def get_monitored_containers(self) -> List[str]:
        """获取需要监控的容器列表"""
        containers = self.server_config.get('containers', [])
        
        if not containers and self.remote_manager:
            # 如果没有指定容器，获取所有运行中的容器
            containers = self.remote_manager.get_running_containers(self.server_config)
        
        # 过滤黑名单容器
        blacklist = self.config.get('blacklist', {})
        blacklisted_containers = blacklist.get('containers', [])
        containers = [c for c in containers if c not in blacklisted_containers]
        
        return containers
    
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
                error_key = f"{self.server_name}:{self.get_error_key(container_name, log_line)}"
                
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
                        'server': self.server_name,
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


class MultiServerMonitor:
    """多服务器监控器"""
    
    def __init__(self, config):
        self.config = config
        self.ssh_pool = SSHConnectionPool(
            max_connections=config.get('ssh_settings.max_connections', 5),
            pool_size=config.get('ssh_settings.connection_pool_size', 3)
        )
        self.remote_manager = RemoteDockerManager(self.ssh_pool)
        self.monitors: Dict[str, RemoteDockerLogMonitor] = {}
        self.logger = setup_logger()
        self._setup_monitors()
    
    def _setup_monitors(self):
        """设置远程监控器"""
        remote_servers = self.config.get('remote_servers', [])
        
        for server_config in remote_servers:
            server_name = server_config.get('name', server_config['host'])
            
            # 检查Docker可用性
            if self.remote_manager.check_docker_availability(server_config):
                monitor = RemoteDockerLogMonitor(self.config, server_config)
                monitor.set_remote_manager(self.remote_manager)
                self.monitors[server_name] = monitor
                self.logger.info(f"✅ 已添加远程服务器监控: {server_name}")
            else:
                self.logger.warning(f"⚠️ 跳过不可用服务器: {server_name}")
    
    def process_all_servers(self) -> List[Dict[str, Any]]:
        """处理所有服务器的日志"""
        all_errors = []
        
        if not self.monitors:
            return all_errors
        
        # 使用线程池并行处理多个服务器
        max_workers = min(len(self.monitors), 5)
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_server = {}
            
            for server_name, monitor in self.monitors.items():
                containers = monitor.get_monitored_containers()
                
                for container_name in containers:
                    future = executor.submit(monitor.process_container_logs, container_name)
                    future_to_server[future] = (server_name, container_name)
            
            for future in as_completed(future_to_server):
                server_name, container_name = future_to_server[future]
                try:
                    errors = future.result()
                    all_errors.extend(errors)
                except Exception as e:
                    self.logger.error(f"处理服务器 {server_name} 容器 {container_name} 日志失败: {e}")
        
        return all_errors
    
    def cleanup(self):
        """清理资源"""
        self.ssh_pool.close_all_connections()
        self.logger.info("🧹 已清理所有SSH连接")