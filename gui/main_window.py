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
from gui.components.log_group import LogGroup
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
        self.video_processor = VideoProcessor(self.hardware)
        self.detection_threads = {}  # 存储所有检测线程
        self.segments = {}  # 存储每个视频的片段信息
        self.completed_count = 0  # 已完成的视频数量
        
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
        file_paths = self.file_group.get_file_paths()
        if not file_paths:
            QMessageBox.warning(self, '警告', '请先选择视频文件！')
            self.operations_group.detect_btn.setText('开始检测')
            self.operations_group.detect_btn.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
            self.operations_group.is_detecting = False
            return

        # 重置状态
        self.completed_count = 0
        self.segments.clear()
        self.detection_threads.clear()
        
        # 更新UI状态
        self.operations_group.progress_bar.setValue(0)
        self.operations_group.split_progress_bar.setValue(0)
        self.log_message(f"开始检测 {len(file_paths)} 个视频文件中的动作...")

        # 获取设置参数
        settings = self.settings_group.get_settings()

        # 为每个视频创建检测线程
        for file_path in file_paths:
            thread = DetectionThread(
                file_path,
                self.hardware,
                self.video_processor.window_scale,
                settings['threshold'],
                settings['min_area'],
                self.video_processor.playback_speed,
                self
            )
            thread.progress.connect(lambda value, path=file_path: self.update_detection_progress(value, path))
            thread.finished.connect(lambda segs, path=file_path: self.detection_finished(segs, path))
            thread.error.connect(lambda msg, path=file_path: self.detection_error(msg, path))
            thread.auto_split_requested.connect(lambda: self.split_video(auto=True))
            
            self.detection_threads[file_path] = thread
            thread.start()
            self.log_message(f"开始处理: {os.path.basename(file_path)}")

    def stop_detection(self):
        """停止所有检测"""
        if self.detection_threads:
            self.log_message("正在停止所有检测...")
            for thread in self.detection_threads.values():
                if thread.isRunning():
                    thread.stop()
                    thread.quit()
                    thread.wait()
            self.detection_threads.clear()
            self.log_message("所有检测已停止")
            
            # 如果已经检测到了片段，则启用切割按钮
            if self.segments:
                self.operations_group.split_btn.setEnabled(True)
                self.log_message("可以进行视频切割操作")

    def update_detection_progress(self, value, file_path):
        """更新检测进度
        
        Args:
            value: 进度值(0-100)
            file_path: 视频文件路径
        """
        # 计算总体进度
        total_progress = 0
        active_threads = 0
        for thread in self.detection_threads.values():
            if thread.isRunning():
                active_threads += 1
                if thread.video_path == file_path:
                    total_progress += value
                else:
                    total_progress += thread.current_progress
        
        if active_threads > 0:
            avg_progress = total_progress / len(self.detection_threads)
            self.operations_group.progress_bar.setValue(int(avg_progress))

        # 检查是否所有线程都已完成
        if active_threads == 0:
            self.operations_group.detect_btn.setText('开始检测')
            self.operations_group.detect_btn.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
            self.operations_group.is_detecting = False
            # 如果有检测到片段，启用切割按钮
            if self.segments:
                self.operations_group.split_btn.setEnabled(True)

    def detection_finished(self, segments, file_path):
        """检测完成处理
        
        Args:
            segments: 检测到的片段列表
            file_path: 视频文件路径
        """
        if segments:  # 只在有检测到片段时添加
            self.segments[file_path] = segments
            
        self.completed_count += 1
        
        # 显示当前视频的片段信息
        self.log_message(f'\n视频 {os.path.basename(file_path)} 检测完成！找到 {len(segments)} 个动作片段')
        if segments:
            segments_info, total_duration = self.splitter.get_segment_info(segments)
            for info in segments_info:
                self.log_message(
                    f'片段 {info["index"]}: {info["start"]} - {info["end"]} '
                    f'(时长: {info["duration"]})'
                )
        
        # 检查是否所有视频都处理完成
        if self.completed_count == len(self.detection_threads):
            self.log_message(f"\n所有视频处理完成！共处理 {len(self.detection_threads)} 个视频")
            self.operations_group.detect_btn.setText('开始检测')
            self.operations_group.detect_btn.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
            self.operations_group.is_detecting = False
            self.operations_group.progress_bar.setValue(100)
            # 如果有检测到片段，启用切割按钮
            if self.segments:
                self.operations_group.split_btn.setEnabled(True)
                self.log_message("可以进行视频切割操作")

    def detection_error(self, error_msg, file_path):
        """处理检测错误"""
        QMessageBox.critical(self, '错误', f'视频 {os.path.basename(file_path)} 检测出错：{error_msg}')
        self.log_message(f'错误: 处理 {os.path.basename(file_path)} 时出错: {error_msg}')
        
        # 如果所有视频都已完成或出错
        remaining_threads = sum(1 for thread in self.detection_threads.values() if thread.isRunning())
        if remaining_threads == 0:
            self.operations_group.detect_btn.setText('开始检测')
            self.operations_group.detect_btn.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
            self.operations_group.is_detecting = False
            
            # 如果有任何成功检测的片段，启用切割按钮
            if self.segments:
                self.operations_group.split_btn.setEnabled(True)
                self.log_message("可以对成功检测的视频进行切割操作")

    def split_video(self, auto=False):
        """切割视频
        
        Args:
            auto (bool): 是否是自动切割模式，如果是则使用配置的输出目录，不弹出选择对话框
        """
        if not self.segments:
            QMessageBox.warning(self, '警告', '请先进行动作检测！')
            return

        output_dir = self.file_group.get_output_directory()
        
        if not auto and not output_dir:
            output_dir = QFileDialog.getExistingDirectory(self, '选择保存目录')
            if (output_dir):
                self.file_group.output_dir_edit.setText(output_dir)
                self.file_group.config_manager.set_output_directory(output_dir)
        
        if output_dir:
            success_count = 0
            total_videos = len(self.segments)
            
            for file_path, segments in self.segments.items():
                try:
                    self.log_message(f"\n开始切割视频: {os.path.basename(file_path)}...")
                    self.operations_group.split_progress_bar.setValue(0)
                    self.splitter.set_progress_callback(self.update_split_progress)
                    
                    video_output_dir = os.path.join(output_dir, os.path.splitext(os.path.basename(file_path))[0])
                    os.makedirs(video_output_dir, exist_ok=True)
                    
                    output_files = self.splitter.split_video(
                        file_path,
                        segments,
                        video_output_dir,
                        self.hardware.ffmpeg_path
                    )
                    
                    if output_files:
                        success_count += 1
                        self.log_message(f"视频切割完成！保存在: {video_output_dir}")
                    else:
                        raise Exception("没有生成任何输出文件")
                        
                except Exception as e:
                    error_msg = f'视频 {os.path.basename(file_path)} 切割失败：{str(e)}'
                    QMessageBox.critical(self, '错误', error_msg)
                    self.log_message(f"错误: {error_msg}")
            
            if success_count > 0:
                if not auto:
                    QMessageBox.information(self, '成功', 
                                         f'视频切割完成！成功处理 {success_count}/{total_videos} 个视频')
                self.log_message(f"\n所有视频切割完成！成功率: {success_count}/{total_videos}")
            
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