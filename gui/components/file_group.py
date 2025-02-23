"""文件选择组件"""
import os
from PyQt5.QtWidgets import (QGroupBox, QHBoxLayout, QLineEdit, 
                           QPushButton, QFileDialog)

class FileGroup(QGroupBox):
    def __init__(self, parent=None):
        super().__init__("视频文件", parent)
        self.parent = parent
        self._init_ui()

    def _init_ui(self):
        layout = QHBoxLayout()
        
        self.file_path = QLineEdit()
        self.file_path.setReadOnly(True)
        self.file_path.setPlaceholderText("请选择要处理的视频文件...")
        
        select_file_btn = QPushButton('选择视频文件')
        select_file_btn.setIcon(self.style().standardIcon(self.style().SP_DialogOpenButton))
        select_file_btn.clicked.connect(self._select_file)
        
        layout.addWidget(self.file_path)
        layout.addWidget(select_file_btn)
        self.setLayout(layout)

    def _select_file(self):
        """选择视频文件"""
        file_name, _ = QFileDialog.getOpenFileName(
            self, '选择视频文件', '', 
            'Video Files (*.mp4 *.avi *.mkv *.mov);;All Files (*.*)'
        )
        if file_name:
            self.file_path.setText(file_name)
            self.parent.log_message(f'已选择视频文件: {os.path.basename(file_name)}')
            self.parent.operations_group.detect_btn.setEnabled(True)

    def get_file_path(self):
        """获取当前选择的文件路径"""
        return self.file_path.text()