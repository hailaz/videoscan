"""操作和进度条组件"""
from PyQt5.QtWidgets import (QGroupBox, QVBoxLayout, QHBoxLayout, 
                           QPushButton, QLabel, QProgressBar, QStyle)
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication

class OperationsGroup(QGroupBox):
    def __init__(self, parent=None):
        super().__init__("操作与进度", parent)
        self.parent = parent
        self.is_detecting = False
        self._init_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setSpacing(10)
        
        # 检测布局
        detection_layout = QHBoxLayout()
        detection_layout.setSpacing(10)
        
        # 先添加进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setAlignment(Qt.AlignCenter)
        detection_layout.addWidget(self.progress_bar, stretch=1)
        
        # 再添加检测按钮
        self.detect_btn = QPushButton('开始检测')
        self.detect_btn.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
        self.detect_btn.clicked.connect(self._toggle_detection)
        detection_layout.addWidget(self.detect_btn)
        
        main_layout.addLayout(detection_layout)

        # 切割布局
        split_layout = QHBoxLayout()
        split_layout.setSpacing(10)
        
        # 先添加进度条
        self.split_progress_bar = QProgressBar()
        self.split_progress_bar.setTextVisible(True)
        self.split_progress_bar.setAlignment(Qt.AlignCenter)
        split_layout.addWidget(self.split_progress_bar, stretch=1)
        
        # 再添加切割按钮
        self.split_btn = QPushButton('切割视频')
        self.split_btn.setIcon(self.style().standardIcon(QApplication.style().SP_MediaSeekForward))
        self.split_btn.clicked.connect(self.parent.split_video)
        self.split_btn.setEnabled(False)
        split_layout.addWidget(self.split_btn)

        main_layout.addLayout(split_layout)
        self.setLayout(main_layout)

    def _toggle_detection(self):
        if not self.is_detecting:
            # 开始检测
            self.parent.start_detection()
            self.detect_btn.setText('停止检测')
            self.detect_btn.setIcon(self.style().standardIcon(QStyle.SP_MediaStop))
            self.is_detecting = True
            self.split_btn.setEnabled(False)
        else:
            # 停止检测
            self.parent.stop_detection()
            self.detect_btn.setText('开始检测')
            self.detect_btn.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
            self.is_detecting = False