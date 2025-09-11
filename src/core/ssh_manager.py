import paramiko
import time
import threading
from typing import Dict, List, Optional, Tuple
from contextlib import contextmanager
from utils.logger import setup_logger


class SSHConnectionPool:
    """SSH连接池管理"""
    
    def __init__(self, max_connections: int = 5, pool_size: int = 3):
        self.max_connections = max_connections
        self.pool_size = pool_size
        self.pools: Dict[str, List[paramiko.SSHClient]] = {}
        self.locks: Dict[str, threading.Lock] = {}
        self.logger = setup_logger()
    
    def _create_connection(self, host: str, username: str, password: str = None, 
                          key_file: str = None, port: int = 22, timeout: int = 10) -> paramiko.SSHClient:
        """创建新的SSH连接"""
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        try:
            if key_file:
                ssh.connect(hostname=host, username=username, key_filename=key_file, 
                           port=port, timeout=timeout)
            else:
                ssh.connect(hostname=host, username=username, password=password, 
                           port=port, timeout=timeout)
            
            return ssh
        except Exception as e:
            self.logger.error(f"SSH连接失败 {host}: {e}")
            ssh.close()
            raise
    
    def _get_pool_key(self, host: str, username: str, port: int = 22) -> str:
        """获取连接池键"""
        return f"{username}@{host}:{port}"
    
    @contextmanager
    def get_connection(self, host: str, username: str, password: str = None, 
                      key_file: str = None, port: int = 22, timeout: int = 10):
        """获取SSH连接（上下文管理器）"""
        pool_key = self._get_pool_key(host, username, port)
        
        if pool_key not in self.locks:
            self.locks[pool_key] = threading.Lock()
        
        with self.locks[pool_key]:
            if pool_key not in self.pools:
                self.pools[pool_key] = []
            
            # 从池中获取可用连接
            ssh = None
            for conn in self.pools[pool_key]:
                if conn.get_transport() and conn.get_transport().is_active():
                    ssh = conn
                    self.pools[pool_key].remove(conn)
                    break
                else:
                    conn.close()
                    self.pools[pool_key].remove(conn)
            
            # 如果没有可用连接，创建新连接
            if not ssh:
                ssh = self._create_connection(host, username, password, key_file, port, timeout)
        
        try:
            yield ssh
        finally:
            # 归还连接到池中
            with self.locks[pool_key]:
                if len(self.pools[pool_key]) < self.pool_size:
                    self.pools[pool_key].append(ssh)
                else:
                    ssh.close()
    
    def close_all_connections(self):
        """关闭所有连接"""
        for pool_key, connections in self.pools.items():
            for conn in connections:
                try:
                    conn.close()
                except:
                    pass
        self.pools.clear()


class RemoteDockerManager:
    """远程Docker管理器"""
    
    def __init__(self, ssh_pool: SSHConnectionPool):
        self.ssh_pool = ssh_pool
        self.logger = setup_logger()
    
    def get_container_logs(self, server_config: Dict, container_name: str, 
                          since: Optional[str] = None, tail: int = 500) -> List[str]:
        """获取远程容器日志"""
        host = server_config['host']
        username = server_config['username']
        password = server_config.get('password')
        key_file = server_config.get('key_file')
        port = server_config.get('port', 22)
        timeout = server_config.get('timeout', 10)
        
        try:
            with self.ssh_pool.get_connection(host, username, password, key_file, port, timeout) as ssh:
                # 构建docker logs命令
                cmd_parts = ['docker logs', f'--tail {tail}']
                
                if since:
                    cmd_parts.append(f'--since {since}')
                
                cmd_parts.append(container_name)
                cmd = ' '.join(cmd_parts)
                
                stdin, stdout, stderr = ssh.exec_command(cmd, timeout=timeout)
                
                # 读取标准输出和错误输出
                output = stdout.read().decode('utf-8', errors='ignore').strip()
                error_output = stderr.read().decode('utf-8', errors='ignore').strip()
                
                # 检查容器是否存在
                if error_output and 'No such container' in error_output:
                    self.logger.warning(f"容器 {container_name} 在 {host} 上不存在")
                    return []
                
                # 合并标准输出和错误输出作为日志内容
                # Docker logs命令有时会将日志输出到stderr而不是stdout
                combined_output = output
                if error_output and not output:
                    combined_output = error_output
                elif error_output and output:
                    combined_output = f"{output}\n{error_output}"
                
                if not combined_output:
                    return []
                
                # 保留原始Docker日志格式（包含时间戳）
                lines = combined_output.split('\n')
                return [line for line in lines if line.strip()]
        
        except Exception as e:
            self.logger.error(f"获取远程容器日志失败 {host}:{container_name} - {e}")
            return []
    
    def get_running_containers(self, server_config: Dict) -> List[str]:
        """获取远程服务器上运行的容器列表"""
        host = server_config['host']
        username = server_config['username']
        password = server_config.get('password')
        key_file = server_config.get('key_file')
        port = server_config.get('port', 22)
        timeout = server_config.get('timeout', 10)
        
        try:
            with self.ssh_pool.get_connection(host, username, password, key_file, port, timeout) as ssh:
                cmd = "docker ps --format '{{.Names}}'"
                stdin, stdout, stderr = ssh.exec_command(cmd, timeout=timeout)
                
                output = stdout.read().decode('utf-8', errors='ignore').strip()
                if not output:
                    return []
                
                return output.split('\n')
        
        except Exception as e:
            self.logger.error(f"获取远程容器列表失败 {host} - {e}")
            return []
    
    def check_docker_availability(self, server_config: Dict) -> bool:
        """检查远程服务器Docker可用性"""
        host = server_config['host']
        username = server_config['username']
        password = server_config.get('password')
        key_file = server_config.get('key_file')
        port = server_config.get('port', 22)
        timeout = server_config.get('timeout', 10)
        
        try:
            with self.ssh_pool.get_connection(host, username, password, key_file, port, timeout) as ssh:
                cmd = "docker --version"
                stdin, stdout, stderr = ssh.exec_command(cmd, timeout=timeout)
                
                output = stdout.read().decode('utf-8', errors='ignore').strip()
                return 'Docker version' in output
        
        except Exception as e:
            self.logger.error(f"检查Docker可用性失败 {host} - {e}")
            return False