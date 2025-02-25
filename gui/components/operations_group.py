"""操作组件"""
from PyQt5.QtWidgets import (QGroupBox, QHBoxLayout, QVBoxLayout, 
                           QPushButton, QProgressBar, QStyle)
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication

class OperationsGroup(QGroupBox):
    def __init__(self, parent=None):
        super().__init__("操作", parent)
        self.parent = parent
        self.is_detecting = False
        self._init_ui()

    def _init_ui(self):
        """初始化UI"""
        main_layout = QVBoxLayout()
        main_layout.setSpacing(10)

        # 按钮行
        btn_layout = QHBoxLayout()
        self.detect_btn = QPushButton("开始检测")
        self.detect_btn.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
        self.detect_btn.clicked.connect(self._toggle_detection)
        self.detect_btn.setEnabled(False)  # 初始禁用，等待选择文件后启用

        self.split_btn = QPushButton("切割视频")
        self.split_btn.setIcon(self.style().standardIcon(QStyle.SP_DialogSaveButton))
        self.split_btn.clicked.connect(self._split_video)
        self.split_btn.setEnabled(False)  # 初始禁用，等待检测完成后启用

        btn_layout.addWidget(self.detect_btn)
        btn_layout.addWidget(self.split_btn)

        # 检测进度条
        progress_layout = QVBoxLayout()
        self.progress_bar = QProgressBar()
        self.progress_bar.setFormat("检测进度: %p%")
        self.progress_bar.setTextVisible(True)
        progress_layout.addWidget(self.progress_bar)

        # 切割进度条
        self.split_progress_bar = QProgressBar()
        self.split_progress_bar.setFormat("切割进度: %p%")
        self.split_progress_bar.setTextVisible(True)
        progress_layout.addWidget(self.split_progress_bar)

        # 添加到主布局
        main_layout.addLayout(btn_layout)
        main_layout.addLayout(progress_layout)
        self.setLayout(main_layout)

    def _toggle_detection(self):
        """切换检测状态"""
        if not self.is_detecting:
            # 开始检测
            self.detect_btn.setText("停止检测")
            self.detect_btn.setIcon(self.style().standardIcon(QStyle.SP_MediaStop))
            self.split_btn.setEnabled(False)
            self.is_detecting = True
            # 重置进度条
            self.progress_bar.setValue(0)
            self.split_progress_bar.setValue(0)
            self.parent.start_detection()
        else:
            # 停止检测
            self.detect_btn.setText("开始检测")
            self.detect_btn.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
            self.is_detecting = False
            self.parent.stop_detection()

    def _split_video(self):
        """执行视频切割"""
        if self.split_btn.isEnabled():
            self.parent.split_video()