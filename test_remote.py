#!/usr/bin/env python3
import sys
import json
from pathlib import Path

# 添加src目录到Python路径
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from core.config import ConfigManager
from core.remote_monitor import MultiServerMonitor
from core.monitor import DockerLogMonitor

def test_config():
    """测试配置加载"""
    print("🧪 测试配置加载...")
    cm = ConfigManager()
    
    # 检查新配置结构
    local_enabled = cm.get('local_monitoring.enabled', True)
    remote_servers = cm.get('remote_servers', [])
    
    print(f"✅ 本地监控开关: {local_enabled}")
    print(f"✅ 远程服务器数量: {len(remote_servers)}")
    
    return True

def test_local_monitor():
    """测试本地监控器"""
    print("🧪 测试本地监控器...")
    cm = ConfigManager()
    
    if cm.get('local_monitoring.enabled', True):
        monitor = DockerLogMonitor(cm.config)
        containers = monitor.get_monitored_containers()
        print(f"✅ 本地监控容器: {containers}")
    else:
        print("⚠️ 本地监控已禁用")
    
    return True

def test_remote_monitor():
    """测试远程监控器"""
    print("🧪 测试远程监控器...")
    cm = ConfigManager()
    
    remote_servers = cm.get('remote_servers', [])
    if remote_servers:
        monitor = MultiServerMonitor(cm.config)
        print(f"✅ 远程监控器已初始化，服务器数量: {len(monitor.monitors)}")
        for server_name in monitor.monitors.keys():
            print(f"   📍 {server_name}")
    else:
        print("ℹ️ 未配置远程服务器")
    
    return True

def main():
    print("🚀 Docker日志远程监控测试")
    print("=" * 50)
    
    try:
        test_config()
        test_local_monitor()
        test_remote_monitor()
        
        print("\n✅ 所有测试通过！")
        print("\n📋 使用说明:")
        print("1. 复制 config.example.json 为 config.json")
        print("2. 根据需要修改配置")
        print("3. 运行: python3 src/main.py")
        print("4. 使用 --setup 参数创建默认配置: python3 src/main.py --setup")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())