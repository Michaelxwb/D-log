from .base import NotificationProvider


class TerminalNotificationProvider(NotificationProvider):
    """终端打印通知提供者"""
    
    def __init__(self, config: dict):
        super().__init__(config)
        self.enabled = config.get('enabled', True)
    
    def get_name(self) -> str:
        return "终端打印"
    
    def validate_config(self) -> bool:
        """终端通知配置始终有效"""
        return True
    
    def send(self, title: str, message: str, container: str = None, 
             timestamp: str = None, count: int = 1) -> bool:
        """发送终端打印通知"""
        if not self.enabled:
            return False
            
        try:
            print(f"\n{title}")
            print("=" * 50)
            print(message)
            print("=" * 50)
            return True
        except Exception as e:
            print(f"终端打印通知失败: {e}")
            return False