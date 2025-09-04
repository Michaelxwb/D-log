import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any
from .base import NotificationProvider
from .message_formatter import MessageFormatter


class EmailProvider(NotificationProvider):
    """邮件通知提供者"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.format_type = config.get('format', 'markdown')  # 'markdown' or 'text'
    
    def send(self, title: str, message: str, **kwargs) -> bool:
        """发送邮件通知"""
        try:
            msg = MIMEMultipart()
            msg['From'] = self.config['from_email']
            msg['To'] = ', '.join(self.config['to_emails'])
            msg['Subject'] = f"[Docker监控] {title}"
            
            # 使用格式化器生成消息内容
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
            
            if self.format_type == 'markdown':
                # 创建HTML格式的邮件内容
                html_content = f"""
                <html>
                <body style="font-family: Arial, sans-serif;">
                    <h2 style="color: #d32f2f;">{title}</h2>
                    <div style="background-color: #f5f5f5; padding: 15px; border-radius: 5px;">
                        <pre style="white-space: pre-wrap; word-wrap: break-word;">{formatted_message}</pre>
                    </div>
                </body>
                </html>
                """
                msg.attach(MIMEText(html_content, 'html', 'utf-8'))
            else:
                # 创建纯文本格式的邮件内容
                text_content = f"""{title}

{formatted_message}

---
发送时间: {kwargs.get('timestamp', 'N/A')}
容器: {kwargs.get('container', 'N/A')}"""
                msg.attach(MIMEText(text_content, 'plain', 'utf-8'))
            
            # 连接SMTP服务器并发送
            if self.config.get('ssl', True):
                server = smtplib.SMTP_SSL(self.config['smtp_server'], self.config.get('smtp_port', 465))
            else:
                server = smtplib.SMTP(self.config['smtp_server'], self.config.get('smtp_port', 587))
                server.starttls()
            
            if 'username' in self.config and 'password' in self.config:
                server.login(self.config['username'], self.config['password'])
            
            server.send_message(msg)
            server.quit()
            return True
            
        except Exception as e:
            print(f"❌ 邮件通知失败: {e}")
            return False
    
    def validate_config(self) -> bool:
        """验证邮件配置"""
        required_keys = ['smtp_server', 'from_email', 'to_emails']
        return all(key in self.config for key in required_keys)
    
    def get_name(self) -> str:
        return "email"