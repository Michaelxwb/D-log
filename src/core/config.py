import json
import os
from typing import Dict, Any


class ConfigManager:
    """配置管理器"""
    
    def __init__(self, config_file: str = 'config.json'):
        self.config_file = config_file
        self.config = self.load_config()
    
    def load_config(self) -> Dict[str, Any]:
        """加载配置文件"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return self.get_default_config()
        except Exception as e:
            print(f"❌ 加载配置文件失败: {e}")
            return self.get_default_config()
    
    def get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        return {
            "containers": [],
            "log_levels": ["ERROR", "WARN"],
            "keywords": [],
            "blacklist": {
                "keywords": [],
                "patterns": [],
                "containers": []
            },
            "notifications": {
                "terminal": {
                    "enabled": True
                },
                "mattermost": {
                    "enabled": False,
                    "server_url": "",
                    "token": "",
                    "channel_id": "",
                    "scheme": "https",
                    "port": 443,
                    "userid": ""
                },
                "email": {
                    "enabled": False,
                    "smtp_server": "",
                    "smtp_port": 465,
                    "username": "",
                    "password": "",
                    "from_email": "",
                    "to_emails": [],
                    "ssl": True
                }
            },
            "check_interval": 5,
            "error_threshold": 5,
            "cooldown_minutes": 30,
            "deduplication_window": 300,
            "max_memory_entries": 1000,
            "cleanup_interval": 3600,
            "context_settings": {
                "max_context_lines": 25,
                "stack_trace_lines": 15,
                "include_surrounding_lines": 5,
                "max_log_length": 8000,
                "buffer_size": 1000,
                "enable_smart_truncation": True
            }
        }
    
    def save_config(self, config: Dict[str, Any] = None):
        """保存配置到文件"""
        if config is None:
            config = self.config
        
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"❌ 保存配置文件失败: {e}")
    
    def get(self, key: str, default=None):
        """获取配置值"""
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def set(self, key: str, value: Any):
        """设置配置值"""
        keys = key.split('.')
        config = self.config
        
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        config[keys[-1]] = value