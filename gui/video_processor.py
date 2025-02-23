"""视频处理模块"""
import cv2

class VideoProcessor:
    """视频处理类，负责视频帧的读取和显示"""
    def __init__(self, hardware, window_scale=0.7, playback_speed=1.0):
        self.hardware = hardware
        self.window_scale = window_scale
        self.playback_speed = max(0.1, min(playback_speed, 16.0))
        self._cap = None
        self.total_frames = 0
        self.fps = 0
        self.frame_width = 0
        self.frame_height = 0

    def open_video(self, video_path):
        """打开视频文件"""
        self._cap = self.hardware.get_video_capture(video_path)
        if not self._cap.isOpened():
            raise Exception("无法打开视频文件")

        # 获取视频信息
        self.total_frames = int(self._cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.fps = int(self._cap.get(cv2.CAP_PROP_FPS))
        
        # 读取第一帧获取尺寸
        ret, first_frame = self._cap.read()
        if not ret:
            raise Exception("无法读取视频帧")
        self.frame_height, self.frame_width = first_frame.shape[:2]
        
        # 重置到视频开始
        self._cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
        return first_frame

    def read_frame(self):
        """读取一帧"""
        if self._cap is None:
            return False, None
        return self._cap.read()

    def display_frame(self, frame, title="Motion Detection"):
        """显示处理后的帧"""
        # 缩放显示帧
        display_frame = cv2.resize(
            frame, None,
            fx=self.window_scale,
            fy=self.window_scale
        )
        cv2.imshow(title, display_frame)

        # 根据播放速度计算等待时间
        wait_time = max(1, int(1000 / (self.fps * self.playback_speed)))
        key = cv2.waitKey(wait_time) & 0xFF
        return key == ord('q')

    def close(self):
        """关闭视频和窗口"""
        if self._cap is not None:
            self._cap.release()
        cv2.destroyAllWindows()