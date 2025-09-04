from typing import Dict, Any, List
from notifications.base import NotificationProvider
from notifications.mattermost import MattermostProvider
from notifications.email import EmailProvider


class NotificationFactory:
    """通知工厂类，用于创建和管理通知提供者"""
    
    _providers = {
        'mattermost': MattermostProvider,
        'email': EmailProvider,
    }
    
    @classmethod
    def create_provider(cls, provider_type: str, config: Dict[str, Any]) -> NotificationProvider:
        """创建通知提供者实例"""
        if provider_type not in cls._providers:
            raise ValueError(f"不支持的通知类型: {provider_type}")
        
        provider_class = cls._providers[provider_type]
        provider = provider_class(config)
        
        if not provider.validate_config():
            raise ValueError(f"{provider_type} 配置无效")
        
        return provider
    
    @classmethod
    def get_supported_types(cls) -> List[str]:
        """获取支持的通知类型列表"""
        return list(cls._providers.keys())
    
    @classmethod
    def register_provider(cls, name: str, provider_class):
        """注册新的通知提供者"""
        cls._providers[name] = provider_class