from PyQt5.QtCore import QThread, pyqtSignal
from core.detector import MotionDetector
import cv2
import time

class DetectionThread(QThread):
    progress = pyqtSignal(float)
    finished = pyqtSignal(list)
    error = pyqtSignal(str)

    def __init__(self, video_path, hardware, window_scale=0.7, threshold=30, 
                 min_area=1000, playback_speed=1.0):
        super().__init__()
        self.video_path = video_path
        self.hardware = hardware
        self.window_scale = window_scale
        self.detector = MotionDetector(threshold, min_area)
        self.playback_speed = max(0.1, min(playback_speed, 16.0))
        self._is_running = True

    def stop(self):
        self._is_running = False

    def run(self):
        try:
            cap = self.hardware.get_video_capture(self.video_path)
            if not cap.isOpened():
                raise Exception("无法打开视频文件")

            # 初始化参数
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            fps = int(cap.get(cv2.CAP_PROP_FPS))
            frame_count = 0
            static_count = 0
            is_motion = False
            segment_start = None
            segments = []

            # 调整排除区域
            ret, first_frame = cap.read()
            if not ret:
                raise Exception("无法读取视频帧")
            frame_height, frame_width = first_frame.shape[:2]
            self.detector.adjust_exclude_regions(frame_width, frame_height)
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)

            while self._is_running:
                ret, frame = cap.read()
                if not ret:
                    if segment_start is not None:
                        segments.append({
                            'start': segment_start,
                            'end': frame_count / fps
                        })
                    break

                current_time = (frame_count / fps) * self.playback_speed
                self.progress.emit(round((frame_count / total_frames) * 100, 2))

                # 检测动作
                motion_detected, display_frame = self.detector.process_frame(
                    frame, 
                    use_gpu=self.hardware.has_gpu
                )

                # 更新动作状态
                if motion_detected:
                    static_count = 0
                    if not is_motion:
                        is_motion = True
                        segment_start = current_time
                else:
                    static_count += 1
                    adjusted_threshold = int(30 / self.playback_speed)
                    if is_motion and static_count >= adjusted_threshold:
                        is_motion = False
                        segments.append({
                            'start': segment_start,
                            'end': current_time
                        })
                        segment_start = None

                # 显示预览
                display_frame = cv2.resize(
                    display_frame, None,
                    fx=self.window_scale,
                    fy=self.window_scale
                )
                cv2.imshow("Motion Detection", display_frame)

                frame_count += 1
                wait_time = max(1, int(1000 / (fps * self.playback_speed)))
                key = cv2.waitKey(wait_time) & 0xFF
                if key == ord('q'):
                    self.stop()
                    # 如果有未完成的片段，添加到segments中
                    if is_motion and segment_start is not None:
                        segments.append({
                            'start': segment_start,
                            'end': current_time
                        })
                    break

            cap.release()
            cv2.destroyAllWindows()
            
            # 无论是正常完成还是被停止，都发出完成信号
            self.finished.emit(segments)
                
        except Exception as e:
            if self._is_running:
                self.error.emit(str(e))