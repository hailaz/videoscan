"""视频检测线程模块"""
from PyQt5.QtCore import QThread, pyqtSignal
from core.detector import MotionDetector
from gui.video_processor import VideoProcessor

class DetectionThread(QThread):
    progress = pyqtSignal(float)
    finished = pyqtSignal(list)
    error = pyqtSignal(str)

    def __init__(self, video_path, hardware, window_scale=0.7, threshold=30, 
                 min_area=1000, playback_speed=1.0):
        super().__init__()
        self.video_path = video_path
        self.video_processor = VideoProcessor(hardware, window_scale, playback_speed)
        self.detector = MotionDetector(threshold, min_area)
        self._is_running = True

    def stop(self):
        """停止检测线程"""
        self._is_running = False

    def run(self):
        """运行检测线程"""
        try:
            # 打开视频并初始化
            first_frame = self.video_processor.open_video(self.video_path)
            self.detector.adjust_exclude_regions(
                self.video_processor.frame_width,
                self.video_processor.frame_height
            )

            # 初始化检测状态
            frame_count = 0
            static_count = 0
            is_motion = False
            segment_start = None
            segments = []

            while self._is_running:
                # 读取视频帧
                ret, frame = self.video_processor.read_frame()
                if not ret:
                    # 处理最后一个未完成的片段
                    if is_motion and segment_start is not None:
                        segments.append({
                            'start': segment_start,
                            'end': frame_count / self.video_processor.fps
                        })
                    break

                # 更新进度
                current_time = frame_count / self.video_processor.fps
                self.progress.emit(
                    round((frame_count / self.video_processor.total_frames) * 100, 2)
                )

                # 检测动作
                motion_detected, display_frame = self.detector.process_frame(
                    frame,
                    use_gpu=self.video_processor.hardware.has_gpu
                )

                # 更新动作状态
                if motion_detected:
                    static_count = 0
                    if not is_motion:
                        is_motion = True
                        segment_start = current_time
                else:
                    static_count += 1
                    adjusted_threshold = int(30 / self.video_processor.playback_speed)
                    if is_motion and static_count >= adjusted_threshold:
                        is_motion = False
                        segments.append({
                            'start': segment_start,
                            'end': current_time
                        })
                        segment_start = None

                # 显示处理后的帧
                if self.video_processor.display_frame(display_frame):
                    self.stop()
                    # 处理未完成的片段
                    if is_motion and segment_start is not None:
                        segments.append({
                            'start': segment_start,
                            'end': current_time
                        })
                    break

                frame_count += 1

            # 清理资源
            self.video_processor.close()
            
            # 发出完成信号
            self.finished.emit(segments)
                
        except Exception as e:
            if self._is_running:
                self.error.emit(str(e))