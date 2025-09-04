from typing import Dict, Any
from mattermostdriver import Driver
from .base import NotificationProvider
from .message_formatter import MessageFormatter


class MattermostProvider(NotificationProvider):
    """Mattermost通知提供者"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.driver = None
        self.format_type = config.get('format', 'markdown')  # 'markdown' or 'text'
    
    def _get_driver(self):
        """获取Mattermost驱动实例"""
        if self.driver is None:
            self.driver = Driver({
                'url': self.config['server_url'],
                'token': self.config['token'],
                'scheme': self.config.get('scheme', 'https'),
                'port': self.config.get('port', 443)
            })
            self.driver.client.token = self.config['token']
            self.driver.client.userid = self.config['userid']
        return self.driver
    
    def send(self, title: str, message: str, **kwargs) -> bool:
        """发送Mattermost通知"""
        try:
            driver = self._get_driver()
            
            # 使用格式化器生成消息
            formatted_message = MessageFormatter.format_message(
                self.format_type,
                title=title,
                container=kwargs.get('container', 'unknown'),
                count=kwargs.get('count', 1),
                threshold=kwargs.get('threshold', 1),
                timestamp=kwargs.get('timestamp', 'unknown'),
                context_lines=len(message.split('\n')) if message else 0,
                context=message or "无上下文"
            )
            
            # 对于Mattermost，始终使用markdown格式标题
            if self.format_type == 'markdown':
                full_message = f"## {title}\n\n{formatted_message}"
            else:
                full_message = f"**{title}**\n\n{formatted_message}"
            
            driver.posts.create_post({
                'channel_id': self.config['channel_id'],
                'message': full_message
            })
            return True
        except Exception as e:
            print(f"❌ Mattermost通知失败: {e}")
            return False
    
    def validate_config(self) -> bool:
        """验证Mattermost配置"""
        required_keys = ['server_url', 'token', 'channel_id', 'userid']
        return all(key in self.config for key in required_keys)
    
    def get_name(self) -> str:
        return "mattermost"