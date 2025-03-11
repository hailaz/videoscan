"""文件选择组件"""
from PyQt5.QtWidgets import (QGroupBox, QHBoxLayout, QVBoxLayout, QLabel, 
                         QPushButton, QFileDialog, QLineEdit, QListWidget,
                         QMenu, QAction, QTreeWidget, QTreeWidgetItem,
                         QHeaderView)
from PyQt5.QtCore import Qt
import os
from core.config_manager import ConfigManager

class FileGroup(QGroupBox):
    def __init__(self, parent=None):
        super().__init__("文件选择", parent)
        self.parent = parent
        self.config_manager = ConfigManager()
        self._init_ui()
        # 将加载历史记录的调用移到外部

    def _safe_log(self, message):
        """安全的日志记录方法"""
        if hasattr(self.parent, 'log_message'):
            self.parent.log_message(message)

    def _init_ui(self):
        """初始化UI"""
        main_layout = QVBoxLayout()
        main_layout.setSpacing(10)
        
        # 文件列表 - 使用QTreeWidget替代QListWidget
        self.file_list = QTreeWidget()
        self.file_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.file_list.customContextMenuRequested.connect(self._show_context_menu)
        
        # 设置列
        self.file_list.setHeaderLabels(["文件路径", "状态", "进度"])
        self.file_list.setMinimumHeight(300)  # 增加最小高度
        
        # 调整列宽
        header = self.file_list.header()
        header.setSectionResizeMode(0, QHeaderView.Stretch)  # 文件路径列自适应宽度
        header.setSectionResizeMode(1, QHeaderView.Fixed)    # 状态列固定宽度
        header.setSectionResizeMode(2, QHeaderView.Fixed)    # 进度列固定宽度
        header.resizeSection(1, 100)  # 设置状态列宽度
        header.resizeSection(2, 80)   # 设置进度列宽度
        
        # 按钮行
        btn_layout = QHBoxLayout()
        self.add_btn = QPushButton("添加文件")
        self.add_btn.clicked.connect(self._select_files)
        self.clear_btn = QPushButton("清空列表")
        self.clear_btn.clicked.connect(self._clear_files)
        
        btn_layout.addWidget(self.add_btn)
        btn_layout.addWidget(self.clear_btn)
        
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
        main_layout.addWidget(self.file_list)
        main_layout.addLayout(btn_layout)
        main_layout.addLayout(output_layout)
        
        self.setLayout(main_layout)

    def _load_recent_videos(self):
        """加载最近使用的视频列表"""
        recent_videos = self.config_manager.get_recent_videos()
        valid_videos = []
        
        for video_path in recent_videos:
            if os.path.exists(video_path):
                self._add_file_item(video_path)
                valid_videos.append(video_path)
                self._safe_log(f'已加载视频文件: {os.path.basename(video_path)}')
        
        # 更新有效的视频列表
        if valid_videos:
            self.config_manager.config['recent_video_list'] = valid_videos
            self.config_manager.save_config()
            # 启用检测按钮也需要安全检查
            if hasattr(self.parent, 'operations_group'):
                self.parent.operations_group.detect_btn.setEnabled(True)

    def _add_file_item(self, file_path):
        """添加一个文件项到列表"""
        item = QTreeWidgetItem()
        item.setText(0, file_path)  # 文件路径
        item.setText(1, "等待处理")  # 初始状态
        item.setText(2, "0%")       # 初始进度
        self.file_list.addTopLevelItem(item)

    def update_file_status(self, file_path, status, progress=None):
        """更新文件状态和进度
        Args:
            file_path: 文件路径
            status: 状态文本
            progress: 进度值(0-100)，可选
        """
        for i in range(self.file_list.topLevelItemCount()):
            item = self.file_list.topLevelItem(i)
            if item.text(0) == file_path:
                item.setText(1, status)
                if progress is not None:
                    item.setText(2, f"{progress:.1f}%")
                break

    def _select_files(self):
        """选择多个视频文件"""
        last_path = self.config_manager.get_last_video_path()
        initial_dir = os.path.dirname(last_path) if last_path else ''

        files, _ = QFileDialog.getOpenFileNames(
            self, '选择视频文件', initial_dir,
            'Video Files (*.mp4 *.avi *.mkv *.mov);;All Files (*.*)'
        )
        if files:
            for file_path in files:
                # 检查文件是否已存在于列表中
                exists = False
                for i in range(self.file_list.topLevelItemCount()):
                    if self.file_list.topLevelItem(i).text(0) == file_path:
                        exists = True
                        break
                
                if not exists:
                    self._add_file_item(file_path)
                    self.config_manager.add_to_recent_videos(file_path)
                    self._safe_log(f'已添加视频文件: {os.path.basename(file_path)}')
            
            # 设置最后一个文件为最近使用
            if files:
                self.config_manager.set_last_video_path(files[-1])
            if hasattr(self.parent, 'operations_group'):
                self.parent.operations_group.detect_btn.setEnabled(True)

    def _clear_files(self):
        """清空文件列表"""
        self.file_list.clear()
        self.config_manager.clear_recent_videos()
        if hasattr(self.parent, 'operations_group'):
            self.parent.operations_group.detect_btn.setEnabled(False)
        self._safe_log("已清空文件列表")

    def _show_context_menu(self, position):
        """显示右键菜单"""
        menu = QMenu()
        delete_action = QAction("删除", self)
        delete_action.triggered.connect(self._delete_selected_file)
        menu.addAction(delete_action)
        menu.exec_(self.file_list.mapToGlobal(position))

    def _delete_selected_file(self):
        """删除选中的文件"""
        current_item = self.file_list.currentItem()
        if current_item:
            file_path = current_item.text(0)  # 获取文件路径列的值
            self.file_list.takeTopLevelItem(self.file_list.indexOfTopLevelItem(current_item))
            self.config_manager.remove_from_recent_videos(file_path)
            
            if self.file_list.topLevelItemCount() == 0:
                if hasattr(self.parent, 'operations_group'):
                    self.parent.operations_group.detect_btn.setEnabled(False)
            self._safe_log(f"已移除视频文件: {os.path.basename(file_path)}")

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

    def get_file_paths(self):
        """获取所有选择的文件路径"""
        return [self.file_list.topLevelItem(i).text(0) 
                for i in range(self.file_list.topLevelItemCount())]

    def get_output_directory(self):
        """获取当前输出目录"""
        return self.output_dir_edit.text()