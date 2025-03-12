"""FFmpeg工具模块"""
import subprocess
from pathlib import Path

class FFmpegUtils:
    def __init__(self):
        self.ffprobe_path = str(Path(__file__).parent.parent.parent / "bin" / "ffprobe.exe")

    def get_fps(self, video_path):
        """使用ffprobe获取准确的视频帧率
        
        Args:
            video_path: 视频文件路径
            
        Returns:
            float: 帧率，失败返回None
        """
        try:
            cmd = [
                self.ffprobe_path,
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

    def get_duration(self, video_path):
        """使用ffprobe获取准确的视频时长
        
        Args:
            video_path: 视频文件路径
            
        Returns:
            float: 时长(秒)，失败返回None
        """
        try:
            cmd = [
                self.ffprobe_path,
                "-v", "error",
                "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1",
                video_path
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                return float(result.stdout.strip())
            return None
        except Exception as e:
            print(f"获取视频时长失败: {str(e)}")
            return None