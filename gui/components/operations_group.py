"""操作和进度条组件"""
from PyQt5.QtWidgets import (QGroupBox, QVBoxLayout, QHBoxLayout, 
                           QPushButton, QLabel, QProgressBar)
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication

class OperationsGroup(QGroupBox):
    def __init__(self, parent=None):
        super().__init__("操作与进度", parent)
        self.parent = parent
        self._init_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setSpacing(10)
        
        # 按钮布局
        button_layout = QHBoxLayout()
        button_layout.setSpacing(20)
        
        self.detect_btn = QPushButton('开始检测')
        self.detect_btn.setIcon(self.style().standardIcon(QApplication.style().SP_MediaPlay))
        self.detect_btn.clicked.connect(self.parent.start_detection)
        button_layout.addWidget(self.detect_btn)

        self.stop_btn = QPushButton('停止')
        self.stop_btn.setIcon(self.style().standardIcon(QApplication.style().SP_MediaStop))
        self.stop_btn.clicked.connect(self.parent.stop_detection)
        self.stop_btn.setEnabled(False)
        button_layout.addWidget(self.stop_btn)

        self.split_btn = QPushButton('切割视频')
        self.split_btn.setIcon(self.style().standardIcon(QApplication.style().SP_MediaSeekForward))
        self.split_btn.clicked.connect(self.parent.split_video)
        self.split_btn.setEnabled(False)
        button_layout.addWidget(self.split_btn)
        
        main_layout.addLayout(button_layout)

        # 进度条布局
        progress_layout = QVBoxLayout()
        progress_layout.setSpacing(10)
        
        # 检测进度
        detection_progress_layout = QHBoxLayout()
        detection_progress_layout.addWidget(QLabel("检测进度:"))
        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setAlignment(Qt.AlignCenter)
        detection_progress_layout.addWidget(self.progress_bar)
        progress_layout.addLayout(detection_progress_layout)

        # 切割进度
        split_progress_layout = QHBoxLayout()
        split_progress_layout.addWidget(QLabel("切割进度:"))
        self.split_progress_bar = QProgressBar()
        self.split_progress_bar.setTextVisible(True)
        self.split_progress_bar.setAlignment(Qt.AlignCenter)
        split_progress_layout.addWidget(self.split_progress_bar)
        progress_layout.addLayout(split_progress_layout)

        main_layout.addLayout(progress_layout)
        self.setLayout(main_layout)