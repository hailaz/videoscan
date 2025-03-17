"""操作组件"""
from PyQt5.QtWidgets import (QGroupBox, QHBoxLayout, QPushButton, QStyle)
from PyQt5.QtCore import Qt

class OperationsGroup(QGroupBox):
    def __init__(self, parent=None):
        super().__init__("操作", parent)
        self.parent = parent
        self.is_detecting = False
        self._init_ui()

    def _init_ui(self):
        """初始化UI"""
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(15)  # 增加按钮间距
        btn_layout.setContentsMargins(10, 10, 10, 10)

        # 开始/停止检测按钮
        self.detect_btn = QPushButton("开始检测")
        self.detect_btn.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
        self.detect_btn.clicked.connect(self._toggle_detection)
        self.detect_btn.setEnabled(False)
        self.detect_btn.setMinimumWidth(120)  # 设置最小宽度

        # 切割视频按钮
        self.split_btn = QPushButton("切割视频")
        self.split_btn.setIcon(self.style().standardIcon(QStyle.SP_DialogSaveButton))
        self.split_btn.clicked.connect(self._split_video)
        self.split_btn.setEnabled(False)
        self.split_btn.setMinimumWidth(120)  # 设置最小宽度

        btn_layout.addWidget(self.detect_btn)
        btn_layout.addWidget(self.split_btn)
        btn_layout.addStretch()  # 添加弹性空间

        self.setLayout(btn_layout)

    def _toggle_detection(self):
        """切换检测状态"""
        if not self.is_detecting:
            # 开始检测
            self.detect_btn.setText("停止检测")
            self.detect_btn.setIcon(self.style().standardIcon(QStyle.SP_MediaStop))
            self.split_btn.setEnabled(False)
            self.is_detecting = True
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