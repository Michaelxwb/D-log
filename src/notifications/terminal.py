from .base import NotificationProvider
from .message_formatter import MessageFormatter


class TerminalNotificationProvider(NotificationProvider):
    """终端打印通知提供者"""
    
    def __init__(self, config: dict):
        super().__init__(config)
        self.enabled = config.get('enabled', True)
        self.format_type = config.get('format', 'text')  # 'text' or 'markdown'
    
    def get_name(self) -> str:
        return "终端打印"
    
    def validate_config(self) -> bool:
        """终端通知配置始终有效"""
        return True
    
    def send(self, title: str, message: str, container: str = None, 
             timestamp: str = None, count: int = 1, **kwargs) -> bool:
        """发送终端打印通知"""
        if not self.enabled:
            return False
            
        try:
            # 使用格式化器生成消息
            formatted_message = MessageFormatter.format_message(
                self.format_type,
                title=title,
                container=container or "unknown",
                count=count,
                threshold=kwargs.get('threshold', count),
                timestamp=timestamp or "unknown",
                context_lines=len(message.split('\n')) if message else 0,
                context=message or "无上下文"
            )

            print(f"\n{formatted_message}")
            return True
        except Exception as e:
            print(f"终端打印通知失败: {e}")
            return False