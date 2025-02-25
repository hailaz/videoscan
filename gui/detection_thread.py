"""视频检测线程模块"""
from PyQt5.QtCore import QThread, pyqtSignal
from core.detector import MotionDetector
from core.splitter import VideoSplitter
from core.config_manager import ConfigManager
from .video_processor import VideoProcessor
import math

class DetectionThread(QThread):
    progress = pyqtSignal(float)
    finished = pyqtSignal(list)
    error = pyqtSignal(str)
    auto_split_requested = pyqtSignal()  # 添加自动切割请求信号

    def __init__(self, video_path, hardware, window_scale=0.7, threshold=30, 
                 min_area=1000, playback_speed=1.0, parent=None):
        super().__init__(parent)
        self.video_path = video_path
        self.video_processor = VideoProcessor(hardware, window_scale, playback_speed)
        # 设置静止时间阈值为1秒
        self.detector = MotionDetector(threshold, min_area, static_time_threshold=1.0)
        self.config_manager = ConfigManager()
        self.parent = parent
        self._is_running = True

    def stop(self):
        """停止检测线程"""
        self._is_running = False

    def _align_time(self, time_value, round_up=False):
        """对齐时间到整秒
        
        Args:
            time_value (float): 原始时间值（秒）
            round_up (bool): 是否向上取整，默认False表示向下取整
        
        Returns:
            float: 对齐后的时间值
        """
        if round_up:
            return math.ceil(time_value)
        return math.floor(time_value)

    def run(self):
        """运行检测线程"""
        try:
            # 打开视频并初始化
            self.video_processor.open_video(self.video_path)
            self.detector.adjust_exclude_regions(
                self.video_processor.frame_width,
                self.video_processor.frame_height
            )
            self.detector.set_fps(self.video_processor.fps)

            # 初始化检测状态
            frame_count = 0
            segments = []

            while self._is_running:
                # 读取视频帧
                ret, frame = self.video_processor.read_frame()
                if not ret:
                    # 处理最后一个未完成的片段
                    final_segment = self.detector.get_current_segment()
                    if final_segment:
                        segments.append(final_segment)
                    break

                # 更新进度
                self.progress.emit(
                    round((frame_count / self.video_processor.total_frames) * 100, 2)
                )

                # 检测动作
                motion_detected, display_frame, segment = self.detector.process_frame(
                    frame,
                    frame_count,
                    use_gpu=self.video_processor.hardware.has_gpu
                )

                # 如果产生了新的片段，添加到列表中
                if segment:
                    segments.append(segment)

                # 显示处理后的帧
                if self.video_processor.display_frame(display_frame):
                    self.stop()
                    # 处理未完成的片段
                    final_segment = self.detector.get_current_segment()
                    if final_segment:
                        segments.append(final_segment)
                    break

                frame_count += 1

            # 清理资源
            self.video_processor.close()
            
            # 发出完成信号
            self.finished.emit(segments)
            
            # 如果开启了自动切割，发送自动切割请求信号
            if self.config_manager.get_auto_split() and segments:
                self.auto_split_requested.emit()
                
        except Exception as e:
            if self._is_running:
                self.error.emit(str(e))