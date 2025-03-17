"""程序入口"""
import os
from pathlib import Path
from gui.main_window import main

def initialize_app():
    """初始化应用程序"""
    # 确保配置目录存在
    config_dir = Path('.') / 'config'
    if not config_dir.exists():
        config_dir.mkdir(parents=True)

if __name__ == '__main__':
    initialize_app()
    main()