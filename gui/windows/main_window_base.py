"""主窗口基类"""
from PyQt5.QtWidgets import QMainWindow, QWidget, QVBoxLayout
from gui.components.file_group import FileGroup
from gui.components.settings_group import SettingsGroup
from gui.components.operations_group import OperationsGroup
from gui.components.log_group import LogGroup
from gui.components.playback_group import PlaybackGroup
from gui.components.styles import get_main_styles

class MainWindowBase(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('监控视频切割工具')
        self.setGeometry(100, 100, 1000, 800)
        self._initialize_ui()
        self._apply_styles()

    def _initialize_ui(self):
        """初始化UI布局"""
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)
        layout.setSpacing(8)  # 减小组件间距
        layout.setContentsMargins(15, 15, 15, 15)  # 调整边距

        # 创建并按顺序添加UI组件
        self.log_group = LogGroup(self)  # 先创建日志组件
        self.settings_group = SettingsGroup(self.hardware, self)
        self.playback_group = PlaybackGroup(self)  # 添加播放控制组件
        self.operations_group = OperationsGroup(self)
        self.file_group = FileGroup(self)  # 最后创建文件组件
        
        # 调整组件高度策略
        self.file_group.setMaximumHeight(400)  # 限制文件列表最大高度
        self.settings_group.setMaximumHeight(150)  # 限制设置区域最大高度
        self.playback_group.setMaximumHeight(80)  # 限制播放控制区域高度
        self.operations_group.setMaximumHeight(80)  # 限制操作区域最大高度
        
        # 添加组件到布局
        layout.addWidget(self.file_group, 2)  # 分配相对空间
        layout.addWidget(self.settings_group, 1)
        layout.addWidget(self.playback_group, 1)  # 添加播放控制组件
        layout.addWidget(self.operations_group, 1)
        layout.addWidget(self.log_group, 2)

    def _apply_styles(self):
        """应用UI样式"""
        self.setStyleSheet(get_main_styles())

    def log_message(self, message):
        """添加日志消息"""
        self.log_group.log_message(message)