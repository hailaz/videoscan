"""UI样式定义模块"""

def get_main_styles():
    """返回主窗口样式"""
    return """
        QMainWindow { 
            background-color: #f5f5f5; 
        }
        QGroupBox {
            border: 2px solid #cccccc;
            border-radius: 6px;
            margin-top: 1em;
            padding: 15px;
            background-color: white;
            font-weight: bold;
        }
        QPushButton {
            background-color: #2196F3;
            color: white;
            border: none;
            padding: 8px 15px;
            border-radius: 4px;
            min-width: 100px;
        }
        QLineEdit {
            padding: 5px;
            border: 2px solid #cccccc;
            border-radius: 4px;
        }
        QProgressBar {
            border: 2px solid #cccccc;
            border-radius: 5px;
            text-align: center;
            height: 25px;
        }
        QProgressBar::chunk {
            background-color: #2196F3;
        }
    """

def get_stop_button_style():
    """返回停止按钮样式"""
    return """
        QPushButton {
            background-color: #f44336;
        }
        QPushButton:hover {
            background-color: #d32f2f;
        }
        QPushButton:pressed {
            background-color: #b71c1c;
        }
        QPushButton:disabled {
            background-color: #BDBDBD;
        }
    """