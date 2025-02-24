"""文件选择组件"""
from PyQt5.QtWidgets import (QGroupBox, QHBoxLayout, QVBoxLayout, QLabel, 
                         QPushButton, QFileDialog, QLineEdit)
import os
from core.config_manager import ConfigManager

class FileGroup(QGroupBox):
    def __init__(self, parent=None):
        super().__init__("文件选择", parent)
        self.parent = parent
        self.config_manager = ConfigManager()
        self._init_ui()
        self._load_last_video()

    def _init_ui(self):
        """初始化UI"""
        main_layout = QVBoxLayout()  # 改为垂直布局
        main_layout.setSpacing(10)
        
        # 视频文件选择行
        file_layout = QHBoxLayout()
        self.file_label = QLabel("视频文件:")
        self.file_path = QLineEdit()
        self.file_path.setReadOnly(True)
        self.select_btn = QPushButton("选择文件")
        self.select_btn.clicked.connect(self._select_file)
        
        file_layout.addWidget(self.file_label)
        file_layout.addWidget(self.file_path)
        file_layout.addWidget(self.select_btn)
        
        # 输出目录设置行
        output_layout = QHBoxLayout()
        self.output_dir_label = QLabel("输出目录:")
        self.output_dir_edit = QLineEdit()
        self.output_dir_edit.setReadOnly(True)
        self.output_dir_edit.setText(self.config_manager.get_output_directory())
        self.output_dir_button = QPushButton("选择目录")
        self.output_dir_button.clicked.connect(self._select_output_directory)
        
        output_layout.addWidget(self.output_dir_label)
        output_layout.addWidget(self.output_dir_edit)
        output_layout.addWidget(self.output_dir_button)
        
        # 添加到主布局
        main_layout.addLayout(file_layout)
        main_layout.addLayout(output_layout)
        
        self.setLayout(main_layout)

    def _load_last_video(self):
        """加载上次使用的视频路径"""
        last_path = self.config_manager.get_last_video_path()
        if last_path and os.path.exists(last_path):
            self.file_path.setText(last_path)
            self.parent.log_message(f'已加载上次的视频文件: {os.path.basename(last_path)}')
            self.parent.operations_group.detect_btn.setEnabled(True)

    def _select_file(self):
        """选择视频文件"""
        # 使用上次的目录作为初始目录
        last_path = self.config_manager.get_last_video_path()
        initial_dir = os.path.dirname(last_path) if last_path else ''

        file_name, _ = QFileDialog.getOpenFileName(
            self, '选择视频文件', initial_dir,
            'Video Files (*.mp4 *.avi *.mkv *.mov);;All Files (*.*)'
        )
        if file_name:
            self.file_path.setText(file_name)
            self.config_manager.set_last_video_path(file_name)
            self.parent.log_message(f'已选择视频文件: {os.path.basename(file_name)}')
            self.parent.operations_group.detect_btn.setEnabled(True)

    def _select_output_directory(self):
        """选择输出目录"""
        current_dir = self.config_manager.get_output_directory()
        if not current_dir:
            current_dir = "."
            
        directory = QFileDialog.getExistingDirectory(
            self,
            "选择输出目录",
            current_dir,
            QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks
        )
        
        if directory:
            self.output_dir_edit.setText(directory)
            self.config_manager.set_output_directory(directory)

    def get_file_path(self):
        """获取当前选择的文件路径"""
        return self.file_path.text()

    def get_output_directory(self):
        """获取当前输出目录"""
        return self.output_dir_edit.text()