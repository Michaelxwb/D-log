from abc import ABC, abstractmethod
from typing import Dict, Any


class NotificationProvider(ABC):
    """抽象通知提供者基类"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
    
    @abstractmethod
    def send(self, title: str, message: str, **kwargs) -> bool:
        """发送通知
        
        Args:
            title: 通知标题
            message: 通知内容
            **kwargs: 额外参数
            
        Returns:
            bool: 发送是否成功
        """
        pass
    
    @abstractmethod
    def validate_config(self) -> bool:
        """验证配置是否有效"""
        pass
    
    @abstractmethod
    def get_name(self) -> str:
        """获取提供者名称"""
        pass