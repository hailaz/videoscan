"""视频处理模块"""
import time
from pathlib import Path
from PyQt5.QtCore import QTimer
from core.config_manager import ConfigManager
from gui.video.video_capture import VideoCaptureManager
from gui.video.video_display import VideoDisplay

class VideoProcessor:
    """视频处理类，负责视频帧的读取和控制"""
    def __init__(self, hardware, window_scale=None, playback_speed=None):
        self.hardware = hardware
        self.config_manager = ConfigManager()
        
        # 设置基本参数
        self._window_scale = window_scale if window_scale is not None else self.config_manager.get_window_scale()
        self._playback_speed = playback_speed if playback_speed is not None else self.config_manager.get_playback_speed()
        self._show_preview = self.config_manager.get_show_preview()
        
        # 创建组件
        self.capture = VideoCaptureManager(self.hardware)
        self.display = VideoDisplay(self._window_scale)
        
        # 播放控制相关
        self._is_playing = False
        self._play_timer = QTimer()
        self._play_timer.timeout.connect(self._on_play_timer)
        self._frame_interval = 0
        self._last_frame_time = 0

    @property
    def playback_speed(self):
        """获取播放速度"""
        return self._playback_speed

    @playback_speed.setter
    def playback_speed(self, value):
        """设置播放速度"""
        self._playback_speed = round(max(0.1, min(value, 16.0)), 1)
        self._update_frame_interval()
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
        self.display.window_scale = self._window_scale
        self.config_manager.config['window_scale'] = self._window_scale
        self.config_manager.save_config()

    @property
    def show_preview(self):
        """获取是否显示预览"""
        return self._show_preview

    @show_preview.setter
    def show_preview(self, value):
        """设置是否显示预览"""
        self._show_preview = value
        if not value:
            self.display.close_all_windows()
        self.config_manager.set_show_preview(value)

    def _update_frame_interval(self):
        """更新帧间隔时间"""
        if self.capture.video_info['fps'] > 0:
            self._frame_interval = 1.0 / (self.capture.video_info['fps'] * self.playback_speed)

    def set_playing(self, playing):
        """设置播放状态
        
        Args:
            playing: 是否播放
        """
        self._is_playing = playing
        if playing:
            self._update_frame_interval()
            self._play_timer.start(int(self._frame_interval * 1000))
        else:
            self._play_timer.stop()
            
    def _on_play_timer(self):
        """播放定时器回调"""
        if self._is_playing:
            self.next_frame()
            
    def next_frame(self):
        """显示下一帧"""
        if self.capture._cap is None:
            return False
            
        ret, frame = self.capture.read_frame()
        if ret:
            self.display_frame(frame)
            return True
        else:
            self.set_playing(False)
            return False
            
    def prev_frame(self):
        """显示上一帧"""
        if self.capture._cap is None:
            return False
            
        current_pos = max(0, self.capture.get_current_frame_number() - 2)
        self.capture._cap.set(cv2.CAP_PROP_POS_FRAMES, current_pos)
        return self.next_frame()
        
    def seek_position(self, position):
        """跳转到指定位置
        
        Args:
            position: 位置百分比(0-1)
        """
        if self.capture._cap is None:
            return False
            
        target_frame = int(position * self.capture.video_info['total_frames'])
        self.capture._cap.set(cv2.CAP_PROP_POS_FRAMES, target_frame)
        return self.next_frame()

    def open_video(self, video_path):
        """打开视频文件"""
        success, first_frame = self.capture.open_video(video_path)
        if success:
            self._last_frame_time = time.time()
            self._update_frame_interval()
            self._is_playing = False
            self._play_timer.stop()
        return first_frame

    def read_frame(self):
        """读取一帧"""
        return self.capture.read_frame()

    def should_process_frame(self):
        """检查是否应该处理下一帧"""
        current_time = time.time()
        elapsed = current_time - self._last_frame_time
        
        if elapsed >= self._frame_interval:
            self._last_frame_time = current_time
            return True
        return False

    def format_time(self, seconds):
        """将秒数转换为时间格式 HH:MM:SS.xx"""
        if seconds is None or seconds == 0:
            return "00:00:00.00"
        
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = seconds % 60
        return f"{hours:02d}:{minutes:02d}:{secs:05.2f}"

    def display_frame(self, frame, title=None):
        """显示处理后的帧"""
        if frame is None or not self._show_preview:
            return False
            
        if title is None and self.capture.video_info['path']:
            title = f"Motion Detection - {Path(self.capture.video_info['path']).name}"
            
        # 准备显示信息
        current_frame = self.capture.get_current_frame_number()
        current_time = current_frame / self.capture.video_info['fps']
        total_time = self.capture.video_info['duration']
        progress = (current_frame / self.capture.video_info['total_frames'] * 100
                   if self.capture.video_info['total_frames'] > 0 else 0)
        
        info = {
            'text': f"{self.format_time(current_time)}/{self.format_time(total_time)}({progress:.1f}%) {self.playback_speed}x",
            'position': 'top-right'
        }
        
        # 通知UI更新时间
        if hasattr(self, 'on_time_update'):
            self.on_time_update(current_time, total_time)
        
        return self.display.display_frame(frame, info, title, 
                                        window_id=self.capture.video_info['path'])

    def close(self):
        """关闭视频和窗口"""
        self._play_timer.stop()
        self._is_playing = False
        self.capture.close()
        if self._show_preview and self.capture.video_info['path']:
            self.display.close_window(self.capture.video_info['path'])