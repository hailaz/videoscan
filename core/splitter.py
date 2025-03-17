"""视频分割模块"""
import os
import cv2
import subprocess
from pathlib import Path
from datetime import datetime
from .segment_manager import SegmentManager
from .merger import VideoMerger

class VideoSplitter:
    def __init__(self):
        self.progress_callback = None
        self.segment_manager = SegmentManager()
        self.merger = VideoMerger()
        self.log_callback = None

    def set_progress_callback(self, callback):
        """设置进度回调函数"""
        self.progress_callback = callback
        self.merger.set_progress_callback(callback)

    def set_log_callback(self, callback):
        """设置日志回调函数"""
        self.log_callback = callback
        self.segment_manager.set_logger(callback)
        self.merger.set_log_callback(callback)

    def get_segment_info(self, segments):
        """获取片段信息统计"""
        return self.segment_manager.get_segment_info(segments)

    def split_video(self, video_path, segments, output_dir="切割视频", ffmpeg_path=None):
        """按时间切割视频"""
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

        for i, segment in enumerate(segments):
            try:
                current_progress = round(((i + 1) / total_segments) * 100, 2)
                if self.progress_callback:
                    self.progress_callback(current_progress)

                start_time = segment['start']
                end_time = segment['end']
                start_str = self.segment_manager.format_time(start_time).replace(":", "_")
                end_str = self.segment_manager.format_time(end_time).replace(":", "_")
                duration = end_time - start_time

                output_filename = f"{base_filename}_片段{i+1}_{start_str}到{end_str}.mp4"
                output_path = os.path.join(output_dir, output_filename)
                output_files.append(output_path)

                if ffmpeg_path:
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
                else:
                    # 使用OpenCV进行切割
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

            except Exception as e:
                print(f"处理片段 {i+1}/{total_segments} 时出错: {str(e)}")
                continue

        if self.progress_callback:
            self.progress_callback(100)
            
        # 如果成功切割了视频片段，自动进行合并
        if output_files:
            if self.log_callback:
                self.log_callback("开始合并所有视频片段...")
            
            self.log_callback(f"output_dir 666: {output_dir}")
            
            # 生成输出文件名，直接放在输出目录下
            merged_output_filename = f"{base_filename}_out.mp4"
            merged_output_path = os.path.join(output_dir, merged_output_filename)
            
            # 合并视频
            result = self.merger.merge_videos(output_files, merged_output_path, ffmpeg_path)
            
            # 如果合并成功，删除临时片段文件
            if result:
                if self.log_callback:
                    self.log_callback("正在清理临时文件...")
                for temp_file in output_files:
                    try:
                        os.remove(temp_file)
                        if self.log_callback:
                            self.log_callback(f"已删除临时文件: {os.path.basename(temp_file)}")
                    except Exception as e:
                        if self.log_callback:
                            self.log_callback(f"删除临时文件时出错: {str(e)}")
                
                # 返回合并后的文件路径
                return [merged_output_path]
            
        return output_files