import os
import cv2
import subprocess
from pathlib import Path

class VideoSplitter:
    def __init__(self):
        self.progress_callback = None
        self.motion_segments = []

    def set_progress_callback(self, callback):
        """设置进度回调函数"""
        self.progress_callback = callback

    def merge_segments(self, segments, buffer_time=3):
        """合并重叠的视频片段"""
        if not segments:
            return []
            
        # 按开始时间排序
        segments.sort(key=lambda x: x['start'])
        merged = []
        current = segments[0]
        
        for next_seg in segments[1:]:
            current_end = current['end'] + buffer_time
            next_start = next_seg['start'] - buffer_time
            
            if next_start <= current_end:
                current['end'] = max(current['end'], next_seg['end'])
            else:
                current['start'] = max(0, current['start'] - buffer_time)
                current['end'] = current['end'] + buffer_time
                merged.append(current)
                current = next_seg
        
        current['start'] = max(0, current['start'] - buffer_time)
        current['end'] = current['end'] + buffer_time
        merged.append(current)
        
        return merged

    def format_time(self, seconds):
        """将秒数转换为可读的时间格式"""
        m, s = divmod(seconds, 60)
        h, m = divmod(m, 60)
        return f"{int(h):02d}:{int(m):02d}:{s:05.2f}"

    def get_segment_info(self, segments):
        """获取片段信息统计"""
        total_duration = sum(seg['end'] - seg['start'] for seg in segments)
        info = []
        for i, segment in enumerate(segments):
            duration = segment['end'] - segment['start']
            info.append({
                'index': i + 1,
                'start': self.format_time(segment['start']),
                'end': self.format_time(segment['end']),
                'duration': self.format_time(duration)
            })
        return info, self.format_time(total_duration)

    def split_video(self, video_path, segments, output_dir="切割视频", ffmpeg_path=None):
        """按时间切割视频"""
        if not segments:
            print("没有检测到需要切割的片段！")
            return []
            
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

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
                start_str = self.format_time(start_time).replace(":", "_")
                end_str = self.format_time(end_time).replace(":", "_")
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
            
        return output_files