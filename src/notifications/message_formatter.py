from typing import Dict, Any


class MessageFormatter:
    """消息格式化器，支持markdown和纯文本格式"""
    
    @staticmethod
    def format_message(format_type: str, **kwargs) -> str:
        """根据格式类型格式化消息
        
        Args:
            format_type: 'markdown' 或 'text'
            **kwargs: 包含title, container, count, threshold, timestamp, context_lines, context
            
        Returns:
            str: 格式化后的消息
        """
        if format_type == 'markdown':
            return MessageFormatter._format_markdown(**kwargs)
        else:
            return MessageFormatter._format_text(**kwargs)
    
    @staticmethod
    def _format_markdown(title: str, container: str, count: int, threshold: int, 
                        timestamp: str, context_lines: int, context: str) -> str:
        """格式化为markdown格式"""
        return f"""### {title}
**📦 容器:** `{container}`
**🔢 计数:** `{count}/{threshold}` ✅
**⏰ 时间:** `{timestamp}`
**📊 上下文行数:** `{context_lines}`

**📄 完整错误上下文:**
```
{context}
```"""
    
    @staticmethod
    def _format_text(title: str, container: str, count: int, threshold: int, 
                    timestamp: str, context_lines: int, context: str) -> str:
        """格式化为纯文本格式"""
        return f"""{title}
==================================================
📦 容器: {container}
🔢 计数: {count}/{threshold} ✅
⏰ 时间: {timestamp}
📊 上下文行数: {context_lines}

📄 完整错误上下文:
{context}"""