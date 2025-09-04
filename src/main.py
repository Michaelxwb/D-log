#!/usr/bin/env python3
import time
import argparse
import sys
from pathlib import Path

# 添加src目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

from core.config import ConfigManager
from core.monitor import DockerLogMonitor
from notifications.factory import NotificationFactory
from utils.logger import setup_logger


class DockerLogMonitorApp:
    """Docker日志监控应用主类"""
    
    def __init__(self, config_file: str = 'config.json'):
        self.config_manager = ConfigManager(config_file)
        self.monitor = DockerLogMonitor(self.config_manager.config)
        self.logger = setup_logger()
        self.notification_providers = []
        self._setup_notifications()
    
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
    
    def send_notifications(self, errors: list):
        """发送通知到所有配置的提供者"""
        if not errors:
            return
        
        for error in errors:
            title = f"🚨 Docker错误 - {error['container']}"
            message = f"""**📦 容器:** `{error['container']}`
**🔢 计数:** `{error['count']}/{error['threshold']}` ✅
**⏰ 时间:** `{error['timestamp']}`
**📊 上下文行数:** `{len(error['context'].split(chr(10)))}`

**📄 完整错误上下文:**
```
{error['context']}
```"""
            for provider in self.notification_providers:
                try:
                    success = provider.send(
                        title=title,
                        message=message,
                        container=error['container'],
                        timestamp=error['timestamp'],
                        count=error['count']
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
        self.logger.info("=" * 50)
        
        containers = self.monitor.get_monitored_containers()
        self.logger.info(f"📦 监控容器: {containers or '所有运行中的容器'}")
        self.logger.info(f"🎯 日志级别: {', '.join(self.config_manager.get('log_levels', ['所有']))}")
        self.logger.info(f"🔍 关键词: {', '.join(self.config_manager.get('keywords', ['无']))}")
        self.logger.info(f"⏱️ 检查间隔: {self.config_manager.get('check_interval', 5)}秒")
        self.logger.info(f"🔢 错误阈值: {self.config_manager.get('error_threshold', 3)}次")
        self.logger.info(f"🕒 冷却时间: {self.config_manager.get('cooldown_minutes', 30)}分钟")
        self.logger.info(f"📧 通知提供者: {[p.get_name() for p in self.notification_providers]}")
        self.logger.info("=" * 50)
        
        while True:
            try:
                all_errors = []
                containers = self.monitor.get_monitored_containers()
                
                for container_name in containers:
                    errors = self.monitor.process_container_logs(container_name)
                    all_errors.extend(errors)
                
                # 发送通知
                if all_errors:
                    self.send_notifications(all_errors)
                
                # 定期清理
                if self.monitor.should_cleanup():
                    self.monitor.cleanup_old_errors()
                    self.logger.info(f"🧹 内存清理完成，当前活跃条目: {len(self.monitor.error_counts)}")
                
                time.sleep(self.config_manager.get('check_interval', 5))
                
            except KeyboardInterrupt:
                self.logger.info("\n👋 正在停止监控器...")
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