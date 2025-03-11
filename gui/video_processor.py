"""视频处理模块"""
import cv2
import time
import subprocess
from pathlib import Path
from core.config_manager import ConfigManager
from gui.display_manager import DisplayManager

class VideoProcessor:
    """视频处理类，负责视频帧的读取和控制"""
    def __init__(self, hardware, window_scale=None, playback_speed=None):
        self.hardware = hardware
        self.config_manager = ConfigManager()
        
        # 初始化内部属性
        self._cap = None
        self.total_frames = 0
        self.fps = 0
        self.frame_width = 0
        self.frame_height = 0
        self.video_path = None
        self.duration_seconds = 0  # 视频总时长(秒)
        
        # 设置缩放和播放速度
        self._window_scale = window_scale if window_scale is not None else self.config_manager.get_window_scale()
        self._playback_speed = playback_speed if playback_speed is not None else self.config_manager.get_playback_speed()
        self._show_preview = self.config_manager.get_show_preview()  # 获取预览显示设置
        
        # 创建显示管理器
        self.display_manager = DisplayManager(self._window_scale)
        
        # 帧率控制
        self._frame_interval = 0  # 帧间隔时间（秒）
        self._last_frame_time = 0  # 上一帧的时间

    @property
    def playback_speed(self):
        """获取播放速度"""
        return self._playback_speed

    @playback_speed.setter
    def playback_speed(self, value):
        """设置播放速度"""
        self._playback_speed = round(max(0.1, min(value, 16.0)), 1)
        self._update_frame_interval()
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
        if hasattr(self, 'display_manager'):
            self.display_manager.window_scale = self._window_scale
        # 保存到配置
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
        # 如果禁用预览，关闭所有预览窗口
        if not value:
            self.display_manager.close_all_windows()
        # 保存到配置
        self.config_manager.set_show_preview(value)

    def _update_frame_interval(self):
        """更新帧间隔时间"""
        if self.fps > 0:
            # 根据播放速度调整帧间隔
            self._frame_interval = 1.0 / (self.fps * self.playback_speed)

    def get_current_frame_number(self):
        """获取当前帧号"""
        if self._cap is None:
            return 0
        return int(self._cap.get(cv2.CAP_PROP_POS_FRAMES))

    def format_time(self, seconds):
        """将秒数转换为时间格式 HH:MM:SS.xx"""
        if seconds is None or seconds == 0:
            return "00:00:00.00"
        
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = seconds % 60
        return f"{hours:02d}:{minutes:02d}:{secs:05.2f}"

    def get_time_from_frames(self, frame_number):
        """根据帧号计算时间（秒）"""
        if self.fps <= 0:
            return 0
        return frame_number / self.fps

    def get_accurate_fps(self, video_path):
        """使用ffprobe获取准确的视频帧率"""
        try:
            ffprobe_path = str(Path(__file__).parent.parent / "bin" / "ffprobe.exe")
            cmd = [
                ffprobe_path,
                "-v", "error",
                "-select_streams", "v:0",
                "-show_entries", "stream=r_frame_rate",
                "-of", "default=noprint_wrappers=1:nokey=1",
                video_path
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                num, den = map(int, result.stdout.strip().split('/'))
                return num / den
            return None
        except Exception as e:
            print(f"获取准确帧率失败: {str(e)}")
            return None

    def get_accurate_duration(self, video_path):
        """使用ffprobe获取准确的视频时长（秒）"""
        try:
            ffprobe_path = str(Path(__file__).parent.parent / "bin" / "ffprobe.exe")
            cmd = [
                ffprobe_path,
                "-v", "error",
                "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1",
                video_path
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                duration = float(result.stdout.strip())
                return duration
            return None
        except Exception as e:
            print(f"获取视频时长失败: {str(e)}")
            return None

    def open_video(self, video_path):
        """打开视频文件"""
        self._cap = self.hardware.get_video_capture(video_path)
        if not self._cap.isOpened():
            raise Exception("无法打开视频文件")

        # 保存视频路径
        self.video_path = video_path

        # 获取视频信息，优先使用ffprobe获取准确信息
        self.total_frames = int(self._cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        # 获取准确的视频时长
        accurate_duration = self.get_accurate_duration(video_path)
        self.duration_seconds = accurate_duration if accurate_duration is not None else 0
        
        # 获取准确的帧率
        accurate_fps = self.get_accurate_fps(video_path)
        self.fps = accurate_fps if accurate_fps is not None else self._cap.get(cv2.CAP_PROP_FPS)
        
        # 如果有准确的时长和帧率，重新计算总帧数
        if accurate_duration is not None and accurate_fps is not None:
            self.total_frames = int(accurate_duration * accurate_fps)
        
        # 更新帧间隔时间
        self._update_frame_interval()
        
        # 读取第一帧获取尺寸
        ret, first_frame = self._cap.read()
        if not ret:
            raise Exception("无法读取视频帧")

        # 如果是 UMat 对象，需要先转换回 CPU
        if isinstance(first_frame, cv2.UMat):
            first_frame = first_frame.get()
            
        self.frame_height, self.frame_width = first_frame.shape[:2]
        
        # 重置到视频开始
        self._cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
        self._last_frame_time = time.time()
        return first_frame

    def read_frame(self):
        """读取一帧"""
        if self._cap is None:
            return False, None
        return self._cap.read()

    def should_process_frame(self):
        """检查是否应该处理下一帧"""
        current_time = time.time()
        elapsed = current_time - self._last_frame_time
        
        # 如果经过的时间大于等于帧间隔，则处理下一帧
        if elapsed >= self._frame_interval:
            self._last_frame_time = current_time
            return True
        return False

    def display_frame(self, frame, title=None):
        """显示处理后的帧"""
        if frame is None or not self._show_preview:  # 添加预览显示控制
            return False
            
        # 如果没有指定标题，使用视频文件名
        if title is None and self.video_path:
            title = f"Motion Detection - {Path(self.video_path).name}"
            
        # 准备显示信息
        current_frame = self.get_current_frame_number()
        current_seconds = self.get_time_from_frames(current_frame)
        current_time = self.format_time(current_seconds)
        
        # 为总时长使用准确获取的数值或根据总帧数计算
        total_time = self.format_time(self.duration_seconds if self.duration_seconds > 0 else self.get_time_from_frames(self.total_frames))
        
        progress = (current_frame / self.total_frames * 100) if self.total_frames > 0 else 0
        
        # 显示信息
        info = {
            'text': f"{current_time}/{total_time}({progress:.1f}%) {self.playback_speed}x",
            'position': 'top-right'
        }
        
        return self.display_manager.display_frame(frame, info, title, window_id=self.video_path)

    def close(self):
        """关闭视频和窗口"""
        if self._cap is not None:
            self._cap.release()
            self._cap = None
            
        if self._show_preview and self.video_path:  # 只在预览开启时关闭窗口
            self.display_manager.close_window(self.video_path)
        
        self.video_path = None