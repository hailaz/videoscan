"""日志组件"""
from PyQt5.QtWidgets import QGroupBox, QVBoxLayout, QTextEdit

class LogGroup(QGroupBox):
    def __init__(self, parent=None):
        super().__init__("处理日志", parent)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout()
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMinimumHeight(250)
        layout.addWidget(self.log_text)
        
        self.setLayout(layout)

    def log_message(self, message):
        """添加日志消息"""
        self.log_text.append(message)
        self.log_text.verticalScrollBar().setValue(
            self.log_text.verticalScrollBar().maximum()
        )