from typing import Dict, Any
from mattermostdriver import Driver
from .base import NotificationProvider


class MattermostProvider(NotificationProvider):
    """Mattermost通知提供者"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.driver = None
    
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
            full_message = f"## {title}\n\n{message}"
            
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