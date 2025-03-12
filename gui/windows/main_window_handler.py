"""主窗口处理器"""
from PyQt5.QtWidgets import QMessageBox, QStyle, QFileDialog
import os
from collections import deque
from .main_window_base import MainWindowBase
from core.hardware import HardwareAccelerator
from core.splitter.video_splitter import VideoSplitter  # 更新导入路径
from core.detector.motion_detector import MotionDetector  # 更新导入路径
from core.config_manager import ConfigManager
from gui.video_processor import VideoProcessor
from gui.detection_thread import DetectionThread
from gui.managers.progress_manager import ProgressManager, TaskStatus

class MainWindowHandler(MainWindowBase):
    def __init__(self):
        # 初始化核心组件
        self.config_manager = ConfigManager()
        self.hardware = HardwareAccelerator()
        self.splitter = VideoSplitter()
        self.video_processor = VideoProcessor(self.hardware)
        self.progress_manager = ProgressManager()  # 添加进度管理器
        
        # 调用父类初始化
        super().__init__()
        
        # 初始化状态变量
        self.detection_threads = {}
        self.segments = {}
        self.completed_count = 0
        self.total_videos = 0
        self.video_queue = deque()
        self.active_threads = 0
        
        # 设置回调
        self.splitter.set_log_callback(self.log_message)
        self.video_processor.on_time_update = self.playback_group.update_time
        
        # 设置进度管理器回调
        self.progress_manager.set_callbacks(
            self.file_group.update_file_status,
            self._on_status_update
        )
        
        # 加载配置和记录硬件信息
        self.file_group._load_recent_videos()
        self._log_hardware_info()
        
        # 连接预览显示设置信号
        if hasattr(self, 'video_processor'):
            self.settings_group.show_preview.stateChanged.connect(
                lambda state: setattr(self.video_processor, 'show_preview', bool(state)))
                
    def _on_status_update(self, counts, progress, completed, total):
        """处理状态更新"""
        info = []
        for status, count in counts.items():
            if count > 0:
                info.append(f"{status.value}: {count}")
                
        status_text = " | ".join(info)
        self.operations_group.update_status(
            f"进度: {progress:.1f}% ({completed}/{total}) {status_text}")

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

    def open_video(self, video_path):
        """打开视频文件"""
        try:
            first_frame = self.video_processor.open_video(video_path)
            if first_frame is not None:
                self.playback_group.setEnabled(True)  # 启用播放控制
                return True
        except Exception as e:
            QMessageBox.critical(self, '错误', f'打开视频失败：{str(e)}')
        return False

    def start_detection(self):
        """开始检测所有视频"""
        # 停止当前播放
        self.video_processor.set_playing(False)
        self.playback_group.is_playing = False
        self.playback_group.play_btn.setIcon(
            self.style().standardIcon(QStyle.SP_MediaPlay))
        
        file_paths = self.file_group.get_file_paths()
        if not file_paths:
            QMessageBox.warning(self, '警告', '请先选择视频文件！')
            self._reset_detection_button()
            return
            
        # 重置进度管理器
        self.progress_manager.clear()
        self._initialize_detection(file_paths)
        self.process_next_videos(self.config_manager.get_max_concurrent_videos())

    def _initialize_detection(self, file_paths):
        """初始化检测状态"""
        self.completed_count = 0
        self.segments.clear()
        self.detection_threads.clear()
        self.video_queue.clear()
        self.active_threads = 0
        self.total_videos = len(file_paths)
        
        self.log_message(f"开始检测 {len(file_paths)} 个视频文件中的动作...")
        
        for file_path in file_paths:
            self.video_queue.append(file_path)
            self.progress_manager.add_task(file_path)

    def _reset_detection_button(self):
        """重置检测按钮状态"""
        self.operations_group.detect_btn.setText('开始检测')
        self.operations_group.detect_btn.setIcon(
            self.style().standardIcon(QStyle.SP_MediaPlay))
        self.operations_group.is_detecting = False

    def process_next_videos(self, count=1):
        """处理队列中的下一批视频
        
        Args:
            count: 要启动的视频处理数量
        """
        settings = self.settings_group.get_settings()
        
        started_count = 0
        while started_count < count and self.video_queue:
            file_path = self.video_queue.popleft()
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
            for file_path, thread in self.detection_threads.items():
                if thread.isRunning():
                    thread.stop()
                    thread.quit()
                    thread.wait()
                    self.progress_manager.update_progress(
                        file_path, 0,
                        status=TaskStatus.STOPPED
                    )
                    
            self.detection_threads.clear()
            self.video_queue.clear()
            self.active_threads = 0
            self.log_message("所有检测已停止")
            
            if self.segments:
                self.operations_group.split_btn.setEnabled(True)
                self.log_message("可以进行视频切割操作")

    def update_detection_progress(self, value, file_path):
        """更新检测进度
        
        Args:
            value: 进度值(0-100)
            file_path: 视频文件路径
        """
        self.progress_manager.update_progress(
            file_path, value,
            status=TaskStatus.PROCESSING
        )
        
        if self.active_threads == 0 and len(self.video_queue) == 0:
            self._reset_detection_button()
            if self.segments:
                self.operations_group.split_btn.setEnabled(True)

    def detection_finished(self, segments, file_path):
        """检测完成处理
        
        Args:
            segments: 检测到的片段列表
            file_path: 视频文件路径
        """
        self.active_threads -= 1
        
        if segments:
            self.segments[file_path] = segments
            self.progress_manager.update_progress(
                file_path, 100,
                status=TaskStatus.COMPLETED,
                message=f"完成 ({len(segments)}个片段)"
            )
        else:
            self.progress_manager.update_progress(
                file_path, 100,
                status=TaskStatus.COMPLETED,
                message="无动作片段"
            )
            
        self.completed_count += 1
        
        # 显示片段信息
        self.log_message(f'\n视频 {os.path.basename(file_path)} 检测完成！找到 {len(segments)} 个动作片段')
        if segments:
            segments_info, total_duration = self.splitter.get_segment_info(segments)
            for info in segments_info:
                self.log_message(
                    f'片段 {info["index"]}: {info["start"]} - {info["end"]} '
                    f'(时长: {info["duration"]})'
                )
        
        # 处理下一个视频或完成检测
        if self.video_queue:
            self.process_next_videos(1)
            
        if self.completed_count == self.total_videos:
            self.log_message(f"\n所有视频处理完成！共处理 {self.completed_count} 个视频")
            self._reset_detection_button()
            if self.segments:
                self.operations_group.split_btn.setEnabled(True)
                self.log_message("可以进行视频切割操作")

    def detection_error(self, error_msg, file_path):
        """处理检测错误
        
        Args:
            error_msg: 错误信息
            file_path: 视频文件路径
        """
        self.active_threads -= 1
        self.progress_manager.update_progress(
            file_path, 0,
            status=TaskStatus.FAILED,
            message=f"错误: {error_msg}"
        )
        
        QMessageBox.critical(self, '错误', 
                           f'视频 {os.path.basename(file_path)} 检测出错：{error_msg}')
        self.log_message(f'错误: 处理 {os.path.basename(file_path)} 时出错: {error_msg}')
        
        if self.video_queue:
            self.process_next_videos(1)
        
        remaining_threads = sum(1 for thread in self.detection_threads.values() 
                              if thread.isRunning())
        if remaining_threads == 0 and len(self.video_queue) == 0:
            self._reset_detection_button()
            if self.segments:
                self.operations_group.split_btn.setEnabled(True)
                self.log_message("可以对成功检测的视频进行切割操作")

    def split_video(self, auto=False):
        """切割视频
        
        Args:
            auto (bool): 是否是自动切割模式
        """
        if not self.segments:
            QMessageBox.warning(self, '警告', '请先进行动作检测！')
            return

        output_dir = self.file_group.get_output_directory()
        
        if not auto and not output_dir:
            output_dir = QFileDialog.getExistingDirectory(self, '选择保存目录')
            if output_dir:
                self.file_group.output_dir_edit.setText(output_dir)
                self.file_group.config_manager.set_output_directory(output_dir)
        
        if output_dir:
            self._process_video_splitting(output_dir, auto)
        elif auto:
            self.log_message("自动切割失败：未配置输出目录")

    def _process_video_splitting(self, output_dir, auto=False):
        """处理视频切割过程
        
        Args:
            output_dir: 输出目录路径
            auto: 是否是自动切割模式
        """
        success_count = 0
        total_videos = len(self.segments)
        
        for file_path, segments in self.segments.items():
            try:
                self.log_message(f"\n开始切割视频: {os.path.basename(file_path)}...")
                
                def update_split_progress(value, fp=file_path):
                    """更新切割进度"""
                    self.progress_manager.update_progress(
                        fp, value,
                        status=TaskStatus.PROCESSING,
                        message="切割中"
                    )
                
                self.splitter.set_progress_callback(update_split_progress)
                
                output_files = self.splitter.split_video(
                    file_path,
                    segments,
                    output_dir,
                    self.hardware.ffmpeg_path
                )
                
                if output_files:
                    success_count += 1
                    self.progress_manager.update_progress(
                        file_path, 100,
                        status=TaskStatus.COMPLETED,
                        message="切割完成"
                    )
                    self.log_message(f"视频切割完成！保存在: {output_dir}")
                else:
                    raise Exception("没有生成任何输出文件")
                    
            except Exception as e:
                error_msg = f'视频 {os.path.basename(file_path)} 切割失败：{str(e)}'
                QMessageBox.critical(self, '错误', error_msg)
                self.log_message(f"错误: {error_msg}")
                self.progress_manager.update_progress(
                    file_path, 0,
                    status=TaskStatus.FAILED,
                    message="切割失败"
                )
        
        if success_count > 0:
            if not auto:
                QMessageBox.information(
                    self, '成功', 
                    f'视频切割完成！成功处理 {success_count}/{total_videos} 个视频'
                )
            self.log_message(f"\n所有视频切割完成！成功率: {success_count}/{total_videos}")

    def close(self):
        """关闭窗口前的清理操作"""
        self.stop_detection()
        self.video_processor.close()
        super().close()