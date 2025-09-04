#!/usr/bin/env python3
"""
Docker日志监控器启动脚本
统一的项目入口点
"""
import sys
import os
from pathlib import Path

# 确保src目录在Python路径中
src_path = str(Path(__file__).parent / 'src')
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from main import main

if __name__ == "__main__":
    main()