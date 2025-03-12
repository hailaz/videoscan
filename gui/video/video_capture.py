"""视频捕获模块"""
import cv2
from pathlib import Path
from .ffmpeg_utils import FFmpegUtils

class VideoCaptureManager:
    def __init__(self, hardware):
        self.hardware = hardware
        self.ffmpeg = FFmpegUtils()
        self._cap = None
        self.video_info = {
            'path': None,
            'total_frames': 0,
            'fps': 0,
            'width': 0,
            'height': 0,
            'duration': 0
        }

    def open_video(self, video_path):
        """打开视频文件
        
        Args:
            video_path: 视频文件路径
            
        Returns:
            tuple: (success, first_frame)
        """
        self._cap = self.hardware.get_video_capture(video_path)
        if not self._cap.isOpened():
            raise Exception("无法打开视频文件")
            
        # 保存视频信息
        self.video_info['path'] = video_path
        self._update_video_info()
        
        # 读取第一帧
        ret, first_frame = self._cap.read()
        if not ret:
            raise Exception("无法读取视频帧")
            
        # 获取帧尺寸
        if isinstance(first_frame, cv2.UMat):
            first_frame = first_frame.get()
        self.video_info['height'], self.video_info['width'] = first_frame.shape[:2]
        
        # 重置到开始位置
        self._cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
        return True, first_frame

    def _update_video_info(self):
        """更新视频信息"""
        video_path = self.video_info['path']
        
        # 获取基本信息
        self.video_info['total_frames'] = int(self._cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        # 获取准确的时长
        duration = self.ffmpeg.get_duration(video_path)
        self.video_info['duration'] = duration if duration is not None else 0
        
        # 获取准确的帧率
        fps = self.ffmpeg.get_fps(video_path)
        self.video_info['fps'] = fps if fps is not None else self._cap.get(cv2.CAP_PROP_FPS)
        
        # 如果有准确的时长和帧率，重新计算总帧数
        if duration is not None and fps is not None:
            self.video_info['total_frames'] = int(duration * fps)

    def read_frame(self):
        """读取一帧视频"""
        if self._cap is None:
            return False, None
        return self._cap.read()

    def get_current_frame_number(self):
        """获取当前帧号"""
        if self._cap is None:
            return 0
        return int(self._cap.get(cv2.CAP_PROP_POS_FRAMES))

    def close(self):
        """关闭视频"""
        if self._cap is not None:
            self._cap.release()
            self._cap = None
            self.video_info['path'] = None