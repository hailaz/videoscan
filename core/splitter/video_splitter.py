"""视频切割管理器"""
import os
from pathlib import Path
from .base_splitter import BaseSplitter
from ..segment_manager import SegmentManager

class VideoSplitter:
    def __init__(self):
        self.splitter = BaseSplitter()
        self.segment_manager = SegmentManager()
        self.log_callback = None

    def set_progress_callback(self, callback):
        """设置进度回调函数"""
        self.splitter.set_progress_callback(callback)

    def set_log_callback(self, callback):
        """设置日志回调函数"""
        self.log_callback = callback
        self.segment_manager.set_logger(callback)

    def get_segment_info(self, segments):
        """获取片段信息统计"""
        return self.segment_manager.get_segment_info(segments)

    def split_video(self, video_path, segments, output_dir="切割视频", ffmpeg_path=None):
        """按时间切割视频
        
        Args:
            video_path: 视频文件路径
            segments: 时间片段列表
            output_dir: 输出目录路径
            ffmpeg_path: FFmpeg可执行文件路径

        Returns:
            list: 输出文件路径列表
        """
        if not segments:
            if self.log_callback:
                self.log_callback("没有检测到需要切割的片段！")
            return []
            
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        # 预处理片段，合并重叠部分
        segments = self.segment_manager.merge_segments(segments)

        base_filename = os.path.splitext(os.path.basename(video_path))[0]
        output_files = []
        total_segments = len(segments)

        for i, segment in enumerate(segments, 1):
            try:
                if self.splitter.progress_callback:
                    self.splitter.progress_callback(round((i / total_segments) * 100, 2))

                start_time = segment['start']
                end_time = segment['end']
                start_str = self.segment_manager.format_time(start_time).replace(":", "_")
                end_str = self.segment_manager.format_time(end_time).replace(":", "_")
                duration = end_time - start_time

                output_filename = f"{base_filename}_片段{i}_{start_str}到{end_str}.mp4"
                output_path = os.path.join(output_dir, output_filename)
                output_files.append(output_path)

                if ffmpeg_path:
                    self.splitter.split_with_ffmpeg(
                        video_path, start_time, duration, output_path, ffmpeg_path)
                else:
                    self.splitter.split_with_opencv(
                        video_path, start_time, duration, output_path)

            except Exception as e:
                print(f"处理片段 {i}/{total_segments} 时出错: {str(e)}")
                continue

        if self.splitter.progress_callback:
            self.splitter.progress_callback(100)
            
        return output_files