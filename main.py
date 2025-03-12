"""程序入口"""
import os
import sys
from pathlib import Path
from PyQt5.QtWidgets import QApplication
from gui.windows.main_window_handler import MainWindowHandler

def initialize_app():
    """初始化应用程序"""
    # 确保配置目录存在
    config_dir = Path('.') / 'config'
    if not config_dir.exists():
        config_dir.mkdir(parents=True)

    # 确保其他必要目录存在
    for dir_name in ['input', 'output']:
        dir_path = Path('.') / dir_name
        if not dir_path.exists():
            dir_path.mkdir(parents=True)

if __name__ == '__main__':
    initialize_app()
    app = QApplication(sys.argv)
    window = MainWindowHandler()
    window.show()
    sys.exit(app.exec_())