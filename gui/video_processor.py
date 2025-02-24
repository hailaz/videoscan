"""视频处理模块"""
import cv2
import numpy as np
from core.config_manager import ConfigManager

class VideoProcessor:
    """视频处理类，负责视频帧的读取和显示"""
    def __init__(self, hardware, window_scale=None, playback_speed=None):
        self.hardware = hardware
        self.config_manager = ConfigManager()
        
        # 初始化内部属性
        self._cap = None
        self.total_frames = 0
        self.fps = 0
        self.frame_width = 0
        self.frame_height = 0
        
        # 设置缩放和播放速度（会触发属性装饰器）
        self.window_scale = window_scale if window_scale is not None else self.config_manager.get_window_scale()
        self.playback_speed = playback_speed if playback_speed is not None else self.config_manager.get_playback_speed()

    @property
    def playback_speed(self):
        """获取播放速度"""
        return self._playback_speed

    @playback_speed.setter
    def playback_speed(self, value):
        """设置播放速度"""
        self._playback_speed = round(max(0.1, min(value, 16.0)), 1)  # 限制为1位小数
        # 保存到配置
        self.config_manager.config['playback_speed'] = self._playback_speed
        self.config_manager.save_config()

    @property
    def window_scale(self):
        """获取窗口缩放比例"""
        return self._window_scale

    @window_scale.setter
    def window_scale(self, value):
        """设置窗口缩放比例"""
        self._window_scale = max(0.1, min(value, 1.0))
        # 保存到配置
        self.config_manager.config['window_scale'] = self._window_scale
        self.config_manager.save_config()

    def get_current_frame_number(self):
        """获取当前帧号"""
        if self._cap is None:
            return 0
        return int(self._cap.get(cv2.CAP_PROP_POS_FRAMES))

    def format_time(self, frame_number):
        """将帧号转换为时间格式 HH:MM:SS"""
        if self.fps == 0:
            return "00:00:00"
        total_seconds = frame_number / self.fps
        hours = int(total_seconds // 3600)
        minutes = int((total_seconds % 3600) // 60)
        seconds = int(total_seconds % 60)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

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
        # 获取当前帧信息
        current_frame = self.get_current_frame_number()
        current_time = self.format_time(current_frame)
        total_time = self.format_time(self.total_frames)
        progress = (current_frame / self.total_frames * 100) if self.total_frames > 0 else 0

        # 添加信息文本
        info_text = f"{current_time}/{total_time}({progress:.1f}%)-{self.playback_speed}x"
        
        # 增大字体
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 1.2  # 增大字体大小
        thickness = 2     # 增加字体粗细
        (text_width, text_height), baseline = cv2.getTextSize(info_text, font, font_scale, thickness)
        
        # 计算右上角位置，留出更大的边距
        x = frame.shape[1] - text_width - 20  # 增加右边距
        y = text_height + 20                  # 增加上边距

        # 创建文本背景
        padding = 8  # 增加内边距
        overlay = frame.copy()
        cv2.rectangle(overlay, 
                     (x - padding, y - text_height - padding),
                     (x + text_width + padding, y + padding),
                     (0, 0, 0), -1)
        
        # 添加半透明背景
        alpha = 1
        frame = cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0)

        # 添加文本（白色，增加描边使文字更清晰）
        cv2.putText(frame, info_text, (x, y), font, font_scale, (0, 0, 0), thickness + 2)  # 黑色描边
        cv2.putText(frame, info_text, (x, y), font, font_scale, (255, 255, 255), thickness) # 白色文字

        # 缩放显示帧
        display_frame = cv2.resize(
            frame, None,
            fx=self.window_scale,
            fy=self.window_scale
        )
        cv2.imshow(title, display_frame)

        # 根据播放速度计算等待时间（毫秒）
        wait_time = int(1000 / (self.fps * self.playback_speed))
        if wait_time <= 0:  # 对于高速播放，确保至少处理键盘事件
            wait_time = 1
        key = cv2.waitKey(wait_time) & 0xFF
        return key == ord('q')

    def close(self):
        """关闭视频和窗口"""
        if self._cap is not None:
            self._cap.release()
        cv2.destroyAllWindows()