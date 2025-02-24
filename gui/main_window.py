"""主窗口实现"""
import sys
import os
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QMessageBox, QFileDialog, QStyle
from core.hardware import HardwareAccelerator
from core.splitter import VideoSplitter
from gui.detection_thread import DetectionThread
from gui.components.file_group import FileGroup
from gui.components.settings_group import SettingsGroup
from gui.components.operations_group import OperationsGroup
from gui.components.log_group import LogGroup  # 添加日志组件导入
from gui.components.styles import get_main_styles
from gui.video_processor import VideoProcessor

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('智能视频切割工具')
        self.setGeometry(100, 100, 1000, 800)
        
        # 初始化核心组件
        self.hardware = HardwareAccelerator()
        self.splitter = VideoSplitter()
        self.video_processor = VideoProcessor(self.hardware)  # 创建视频处理器
        self.detection_thread = None
        self.segments = []
        
        # 设置日志回调
        self.splitter.set_log_callback(self.log_message)
        
        self._initialize_ui()
        self._apply_styles()

    def _initialize_ui(self):
        """初始化UI布局"""
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # 创建并添加UI组件
        self.log_group = LogGroup(self)
        self.settings_group = SettingsGroup(self.hardware, self)
        self.operations_group = OperationsGroup(self)
        self.file_group = FileGroup(self)
        
        
        layout.addWidget(self.file_group)
        layout.addWidget(self.settings_group)
        layout.addWidget(self.operations_group)
        layout.addWidget(self.log_group)
        

    def _apply_styles(self):
        """应用UI样式"""
        self.setStyleSheet(get_main_styles())

    def log_message(self, message):
        """添加日志消息"""
        self.log_group.log_message(message)

    def start_detection(self):
        """开始检测"""
        if not self.file_group.get_file_path():
            QMessageBox.warning(self, '警告', '请先选择视频文件！')
            self.operations_group.detect_btn.setText('开始检测')
            self.operations_group.detect_btn.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
            self.operations_group.is_detecting = False
            return

        # 更新UI状态
        self.operations_group.progress_bar.setValue(0)
        self.operations_group.split_progress_bar.setValue(0)
        self.log_message("开始检测视频中的动作...")

        # 获取设置参数
        settings = self.settings_group.get_settings()

        # 使用已有的视频处理器创建检测线程
        self.detection_thread = DetectionThread(
            self.file_group.get_file_path(),
            self.hardware,
            self.video_processor.window_scale,
            settings['threshold'],
            settings['min_area'],
            self.video_processor.playback_speed,
            self
        )
        self.detection_thread.progress.connect(self.update_detection_progress)
        self.detection_thread.finished.connect(self.detection_finished)
        self.detection_thread.error.connect(self.detection_error)
        self.detection_thread.auto_split_requested.connect(lambda: self.split_video(auto=True))  # 使用 lambda 传递 auto 参数
        self.detection_thread.start()

    def stop_detection(self):
        """停止检测"""
        if self.detection_thread and self.detection_thread.isRunning():
            self.log_message("正在停止检测...")
            self.detection_thread.stop()
            self.detection_thread.quit()
            self.detection_thread.wait()
            self.log_message("检测已停止")

    def update_detection_progress(self, value):
        """更新检测进度"""
        self.operations_group.progress_bar.setValue(int(value))

    def detection_finished(self, segments):
        """检测完成处理"""
        self.segments = segments
        self.operations_group.progress_bar.setValue(100)
        self.log_message(f'检测完成！找到 {len(segments)} 个动作片段')
        
        # 显示片段信息
        segments_info, total_duration = self.splitter.get_segment_info(segments)
        for info in segments_info:
            self.log_message(
                f'片段 {info["index"]}: {info["start"]} - {info["end"]} '
                f'(时长: {info["duration"]})'
            )
        
        # 重置检测按钮状态
        self.operations_group.detect_btn.setText('开始检测')
        self.operations_group.detect_btn.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
        self.operations_group.is_detecting = False
        self.operations_group.split_btn.setEnabled(True)

    def detection_error(self, error_msg):
        """处理检测错误"""
        QMessageBox.critical(self, '错误', f'检测过程出错：{error_msg}')
        self.log_message(f'错误: {error_msg}')
        
        # 重置检测按钮状态
        self.operations_group.detect_btn.setText('开始检测')
        self.operations_group.detect_btn.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
        self.operations_group.is_detecting = False
        self.operations_group.progress_bar.setValue(0)

    def split_video(self, auto=False):
        """切割视频
        
        Args:
            auto (bool): 是否是自动切割模式，如果是则使用配置的输出目录，不弹出选择对话框
        """
        if not self.segments:
            QMessageBox.warning(self, '警告', '请先进行动作检测！')
            return

        # 获取配置的输出目录
        output_dir = self.file_group.get_output_directory()
        
        # 如果不是自动切割模式，且没有配置输出目录，弹出选择对话框
        if not auto and not output_dir:
            output_dir = QFileDialog.getExistingDirectory(self, '选择保存目录')
            if output_dir:
                # 保存选择的目录到配置
                self.file_group.output_dir_edit.setText(output_dir)
                self.file_group.config_manager.set_output_directory(output_dir)
        
        if output_dir:
            try:
                self.log_message("开始切割视频...")
                self.operations_group.split_progress_bar.setValue(0)
                self.splitter.set_progress_callback(self.update_split_progress)
                
                output_files = self.splitter.split_video(
                    self.file_group.get_file_path(),
                    self.segments,
                    output_dir,
                    self.hardware.ffmpeg_path
                )
                
                if output_files:
                    if not auto:  # 只在手动切割时显示完成提示
                        QMessageBox.information(self, '成功', '视频切割完成！')
                    self.log_message(f"视频切割完成！保存在: {output_dir}")
                else:
                    raise Exception("没有生成任何输出文件")
                    
            except Exception as e:
                error_msg = f'视频切割失败：{str(e)}'
                QMessageBox.critical(self, '错误', error_msg)
                self.log_message(f"错误: {error_msg}")
        elif auto:
            self.log_message("自动切割失败：未配置输出目录")

    def update_split_progress(self, value):
        """更新切割进度"""
        self.operations_group.split_progress_bar.setValue(int(value))

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())