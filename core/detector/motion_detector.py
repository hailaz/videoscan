"""动作检测器"""
from .base_detector import BaseDetector
from ..region_manager import RegionManager

class MotionDetector:
    def __init__(self, threshold=25, min_area=1000, static_time_threshold=1.0):
        self.detector = BaseDetector(threshold, min_area, static_time_threshold)
        self.region_manager = RegionManager()
        
        # 动作状态管理
        self.is_motion = False
        self.static_frames = 0
        self.segment_start = None
        self.current_time = 0
        self.last_segment_end = 0

    def set_fps(self, fps):
        """设置视频FPS"""
        self.detector.set_fps(fps)
        
    def adjust_exclude_regions(self, frame_width, frame_height):
        """调整排除区域"""
        self.region_manager.adjust_exclude_regions(frame_width, frame_height)
        
    def process_frame(self, frame, frame_count, use_gpu=False):
        """处理单帧并检测动作
        Args:
            frame: 输入帧
            frame_count: 当前帧计数
            use_gpu: 是否使用GPU加速
        Returns:
            tuple: (motion_detected, display_frame, segment)
        """
        if self.detector.fps is None:
            raise RuntimeError("必须先调用set_fps设置视频帧率")
            
        # 更新当前时间
        self.current_time = frame_count / self.detector.fps
        
        # 应用排除区域
        frame = self.region_manager.apply_regions(frame)
        
        # 检测动作
        motion_detected, display_frame, _ = self.detector.detect_motion(frame, use_gpu)
        
        # 绘制排除区域
        display_frame = self.region_manager.draw_regions(display_frame)
        
        # 处理片段
        segment = self._update_motion_state(motion_detected)
        
        return motion_detected, display_frame, segment
        
    def _update_motion_state(self, motion_detected):
        """更新动作状态并返回片段信息
        Returns:
            dict or None: 如果产生新的片段则返回片段信息，否则返回None
        """
        if motion_detected:
            self.static_frames = 0
            if not self.is_motion:
                # 只有当当前时间大于上一个片段的结束时间才开始新片段
                potential_start = self.detector._align_time(self.current_time)
                if potential_start >= self.last_segment_end:
                    self.is_motion = True
                    self.segment_start = potential_start
            return None
        else:
            self.static_frames += 1
            if self.is_motion and self.static_frames >= self.detector.static_frames_threshold:
                self.is_motion = False
                current_end = self.detector._align_time(self.current_time, round_up=True)
                if self.segment_start is not None and current_end > self.segment_start:
                    segment = {
                        'start': self.segment_start,
                        'end': current_end
                    }
                    self.last_segment_end = current_end
                    self.segment_start = None
                    return segment
            return None
            
    def get_current_segment(self):
        """获取当前未完成的片段"""
        if self.is_motion and self.segment_start is not None:
            return {
                'start': self.segment_start,
                'end': self.current_time
            }
        return None

    def reset(self):
        """重置检测器状态"""
        self.detector.prev_frame = None
        self.is_motion = False
        self.static_frames = 0
        self.segment_start = None
        self.current_time = 0
        self.last_segment_end = 0