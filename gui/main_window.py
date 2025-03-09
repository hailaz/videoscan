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
from core.config_manager import ConfigManager
from collections import deque

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('智能视频切割工具')
        self.setGeometry(100, 100, 1000, 800)
        
        # 初始化核心组件
        self.config_manager = ConfigManager()  # 移到最前面初始化
        self.hardware = HardwareAccelerator()
        # 使用硬件检测获取最优并行处理数
        optimal_workers = self.hardware.get_optimal_workers()
        self.config_manager.set_max_concurrent_videos(optimal_workers)
        
        self.splitter = VideoSplitter()
        self.video_processor = VideoProcessor(self.hardware)
        self.detection_threads = {}  # 存储所有检测线程
        self.segments = {}  # 存储每个视频的片段信息
        self.completed_count = 0  # 已完成的视频数量
        self.total_videos = 0  # 视频总数
        self.video_queue = deque()  # 等待处理的视频队列
        self.active_threads = 0  # 当前活动的线程数
        
        # 设置日志回调
        self.splitter.set_log_callback(self.log_message)
        
        self._initialize_ui()
        self._apply_styles()
        
        # 记录硬件信息
        self._log_hardware_info()

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

    def _log_hardware_info(self):
        """记录硬件信息"""
        self.log_message("\n硬件信息:")
        if self.hardware.has_gpu:
            gpu_type = "Intel Arc" if self.hardware.gpu_info['intel_arc'] else \
                      "Intel GPU" if self.hardware.gpu_info['intel_gpu'] else \
                      "CUDA GPU"
            self.log_message(f"- GPU加速: {gpu_type}")
        else:
            self.log_message("- GPU加速: 未启用")
            
        workers = self.config_manager.get_max_concurrent_videos()
        self.log_message(f"- CPU核心数: {self.hardware.detector.cpu_count}")
        self.log_message(f"- 最优并行处理数: {workers}")
        self.log_message(f"- FFmpeg: {'可用' if self.hardware.has_ffmpeg else '未找到'}\n")

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
        self.video_queue.clear()
        self.active_threads = 0
        self.total_videos = len(file_paths)
        
        # 更新UI状态
        self.operations_group.progress_bar.setValue(0)
        self.operations_group.split_progress_bar.setValue(0)
        self.log_message(f"开始检测 {len(file_paths)} 个视频文件中的动作...")
        
        # 将所有视频文件添加到队列中
        for file_path in file_paths:
            self.video_queue.append(file_path)
        
        # 根据配置的最大并行处理数量启动视频处理
        max_concurrent = self.config_manager.get_max_concurrent_videos()
        self.log_message(f"当前设置同时处理 {max_concurrent} 个视频")
        self.process_next_videos(max_concurrent)

    def process_next_videos(self, count=1):
        """处理队列中的下一批视频
        
        Args:
            count: 要启动的视频处理数量
        """
        # 获取设置参数
        settings = self.settings_group.get_settings()
        
        # 启动指定数量的视频处理线程，不超过队列中视频数量
        started_count = 0
        while started_count < count and self.video_queue:
            file_path = self.video_queue.popleft()  # 从队列取出下一个视频
            self.start_video_processing(file_path, settings)
            started_count += 1
            self.active_threads += 1

    def start_video_processing(self, file_path, settings):
        """开始处理单个视频
        
        Args:
            file_path: 视频文件路径
            settings: 处理设置
        """
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
            self.video_queue.clear()  # 清空队列
            self.active_threads = 0
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
        
        # 计算已完成的视频进度
        completed_progress = (self.completed_count / self.total_videos) * 100 if self.total_videos > 0 else 0
        
        if active_threads > 0:
            # 当前活动线程的进度
            active_progress = total_progress / len(self.detection_threads)
            # 总体进度 = 已完成视频进度 + 当前处理视频的加权进度
            weighted_progress = completed_progress + (active_progress * (len(self.detection_threads) / self.total_videos))
            self.operations_group.progress_bar.setValue(int(weighted_progress))
        
        # 检查是否所有线程都已完成
        if active_threads == 0 and len(self.video_queue) == 0:
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
        self.active_threads -= 1
        
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
        
        # 检查队列中是否还有视频需要处理
        if self.video_queue:
            # 处理下一个视频
            self.process_next_videos(1)
            
        # 检查是否所有视频都处理完成
        if self.completed_count == self.total_videos:
            self.log_message(f"\n所有视频处理完成！共处理 {self.completed_count} 个视频")
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
        self.active_threads -= 1
        
        QMessageBox.critical(self, '错误', f'视频 {os.path.basename(file_path)} 检测出错：{error_msg}')
        self.log_message(f'错误: 处理 {os.path.basename(file_path)} 时出错: {error_msg}')
        
        # 尝试处理队列中的下一个视频
        if self.video_queue:
            self.process_next_videos(1)
        
        # 如果所有视频都已完成或出错
        remaining_threads = sum(1 for thread in self.detection_threads.values() if thread.isRunning())
        if remaining_threads == 0 and len(self.video_queue) == 0:
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
                    
                    output_files = self.splitter.split_video(
                        file_path,
                        segments,
                        output_dir,
                        self.hardware.ffmpeg_path
                    )
                    
                    if output_files:
                        success_count += 1
                        self.log_message(f"视频切割完成！保存在: {output_dir}")
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