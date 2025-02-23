"""视频片段管理模块"""
from datetime import datetime

class SegmentManager:
    """视频片段管理类"""
    def __init__(self):
        self.segments = []

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