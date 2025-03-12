"""视频切割基类"""
import os
import cv2
import subprocess
from pathlib import Path

class BaseSplitter:
    def __init__(self):
        self.progress_callback = None
    
    def set_progress_callback(self, callback):
        """设置进度回调函数"""
        self.progress_callback = callback
        
    def split_with_ffmpeg(self, video_path, start_time, duration, output_path, ffmpeg_path):
        """使用FFmpeg切割视频
        
        Args:
            video_path: 输入视频路径
            start_time: 开始时间(秒)
            duration: 持续时间(秒)
            output_path: 输出文件路径
            ffmpeg_path: FFmpeg可执行文件路径
        """
        cmd = [
            ffmpeg_path,
            '-i', video_path,
            '-ss', str(start_time),
            '-t', str(duration),
            '-c', 'copy',
            '-y',
            output_path
        ]
        subprocess.run(cmd, check=True)
        
    def split_with_opencv(self, video_path, start_time, duration, output_path):
        """使用OpenCV切割视频
        
        Args:
            video_path: 输入视频路径
            start_time: 开始时间(秒)
            duration: 持续时间(秒)
            output_path: 输出文件路径
        """
        cap = cv2.VideoCapture(video_path)
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        fps = int(cap.get(cv2.CAP_PROP_FPS))
        frame_size = (
            int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
            int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        )
        out = cv2.VideoWriter(output_path, fourcc, fps, frame_size)
        
        cap.set(cv2.CAP_PROP_POS_FRAMES, int(start_time * fps))
        frames_to_save = int(duration * fps)
        frame_count = 0
        
        while frame_count < frames_to_save:
            ret, frame = cap.read()
            if not ret:
                break
            out.write(frame)
            frame_count += 1
            
        cap.release()
        out.release()