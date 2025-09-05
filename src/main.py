#!/usr/bin/env python3
import time
import argparse
import sys
from pathlib import Path

# 添加src目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

from core.config import ConfigManager
from core.monitor import DockerLogMonitor
from core.remote_monitor import MultiServerMonitor
from notifications.factory import NotificationFactory
from utils.logger import setup_logger


class DockerLogMonitorApp:
    """Docker日志监控应用主类"""
    
    def __init__(self, config_file: str = 'config.json'):
        self.config_manager = ConfigManager(config_file)
        self.logger = setup_logger()
        self.notification_providers = []
        self.local_monitor = None
        self.remote_monitor = None
        self._setup_notifications()
        self._setup_monitors()
    
    def _setup_notifications(self):
        """设置通知提供者"""
        notifications_config = self.config_manager.get('notifications', {})
        
        for provider_type, config in notifications_config.items():
            if config.get('enabled', False):
                try:
                    provider = NotificationFactory.create_provider(provider_type, config)
                    self.notification_providers.append(provider)
                    self.logger.info(f"✅ 已启用 {provider.get_name()} 通知")
                except Exception as e:
                    self.logger.error(f"❌ 初始化 {provider_type} 通知失败: {e}")
    
    def _setup_monitors(self):
        """设置监控器"""
        # 本地监控
        if self.config_manager.get('local_monitoring.enabled', True):
            self.local_monitor = DockerLogMonitor(self.config_manager.config)
            self.logger.info("✅ 已启用本地Docker监控")
        else:
            self.logger.info("⚠️ 本地Docker监控已禁用")
        
        # 远程监控
        remote_servers = self.config_manager.get('remote_servers', [])
        if remote_servers:
            self.remote_monitor = MultiServerMonitor(self.config_manager.config)
            self.logger.info(f"✅ 已启用远程服务器监控 ({len(remote_servers)}台)")
        else:
            self.logger.info("ℹ️ 未配置远程服务器监控")
    
    def send_notifications(self, errors: list):
        """发送通知到所有配置的提供者"""
        if not errors:
            return
        
        for error in errors:
            server_name = error.get('server', '本地')
            container_name = error['container']
            
            title = f"🚨 Docker错误 - {server_name}:{container_name}"
            context = error['context']
            
            for provider in self.notification_providers:
                try:
                    success = provider.send(
                        title=title,
                        message=context,
                        container=container_name,
                        timestamp=error['timestamp'],
                        count=error['count'],
                        threshold=error['threshold']
                    )
                    if success:
                        self.logger.info(f"✅ {provider.get_name()} 通知发送成功")
                    else:
                        self.logger.warning(f"⚠️ {provider.get_name()} 通知发送失败")
                except Exception as e:
                    self.logger.error(f"❌ {provider.get_name()} 通知异常: {e}")
    
    def run(self):
        """运行监控应用"""
        self.logger.info("🚀 启动Docker日志监控器...")
        self.logger.info("=" * 60)
        
        # 显示配置信息
        if self.local_monitor:
            local_containers = self.local_monitor.get_monitored_containers()
            self.logger.info(f"📦 本地监控容器: {local_containers or '所有运行中的容器'}")
        
        if self.remote_monitor:
            server_count = len(self.remote_monitor.monitors)
            self.logger.info(f"🌐 远程服务器数量: {server_count}台")
            for server_name in self.remote_monitor.monitors.keys():
                self.logger.info(f"   📍 {server_name}")
        
        self.logger.info(f"🎯 日志级别: {', '.join(self.config_manager.get('log_levels', ['所有']))}")
        self.logger.info(f"🔍 关键词: {', '.join(self.config_manager.get('keywords', ['无']))}")
        self.logger.info(f"⏱️ 检查间隔: {self.config_manager.get('check_interval', 5)}秒")
        self.logger.info(f"🔢 错误阈值: {self.config_manager.get('error_threshold', 3)}次")
        self.logger.info(f"🕒 冷却时间: {self.config_manager.get('cooldown_minutes', 30)}分钟")
        self.logger.info(f"📧 通知提供者: {[p.get_name() for p in self.notification_providers]}")
        self.logger.info("=" * 60)
        
        while True:
            try:
                all_errors = []
                
                # 处理本地监控
                if self.local_monitor:
                    containers = self.local_monitor.get_monitored_containers()
                    for container_name in containers:
                        errors = self.local_monitor.process_container_logs(container_name)
                        all_errors.extend(errors)
                
                # 处理远程监控
                if self.remote_monitor:
                    remote_errors = self.remote_monitor.process_all_servers()
                    all_errors.extend(remote_errors)
                
                # 发送通知
                if all_errors:
                    self.send_notifications(all_errors)
                
                # 定期清理
                if self.local_monitor and self.local_monitor.should_cleanup():
                    self.local_monitor.cleanup_old_errors()
                    self.logger.info(f"🧹 本地内存清理完成，当前活跃条目: {len(self.local_monitor.error_counts)}")
                
                time.sleep(self.config_manager.get('check_interval', 5))
                
            except KeyboardInterrupt:
                self.logger.info("\n👋 正在停止监控器...")
                if self.remote_monitor:
                    self.remote_monitor.cleanup()
                break
            except Exception as e:
                self.logger.error(f"❌ 监控异常: {e}")
                time.sleep(10)
    
    def setup_config(self):
        """创建默认配置文件"""
        self.config_manager.save_config()
        self.logger.info(f"✅ 默认配置文件已创建: {self.config_manager.config_file}")


def main():
    parser = argparse.ArgumentParser(description='Docker日志监控器')
    parser.add_argument('--config', default='config.json', help='配置文件路径')
    parser.add_argument('--setup', action='store_true', help='创建默认配置文件')
    
    args = parser.parse_args()
    
    if args.setup:
        app = DockerLogMonitorApp(args.config)
        app.setup_config()
        return
    
    app = DockerLogMonitorApp(args.config)
    app.run()


if __name__ == "__main__":
    main()