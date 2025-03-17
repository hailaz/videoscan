"""运动检测模块"""
import cv2
import numpy as np
import math
from .region_manager import RegionManager

class MotionDetector:
    def __init__(self, threshold=25, min_area=1000, static_time_threshold=1.0):
        """
        初始化动作检测器
        Args:
            threshold (int): 像素差异阈值
            min_area (int): 最小检测区域面积
            static_time_threshold (float): 静止时间阈值(秒)
        """
        self.threshold = threshold
        self.min_area = min_area
        self.static_time_threshold = static_time_threshold
        self.prev_frame = None
        self.region_manager = RegionManager()
        
        # 动作状态管理
        self.is_motion = False
        self.static_frames = 0
        self.static_frames_threshold = None  # 将在设置FPS后初始化
        self.fps = None
        self.segment_start = None
        self.current_time = 0
        self.last_segment_end = 0  # 记录上一个片段的结束时间
        
    def set_fps(self, fps):
        """设置视频FPS，用于计算静止时间阈值"""
        self.fps = fps
        self.static_frames_threshold = int(self.static_time_threshold * fps)
        
    def adjust_exclude_regions(self, frame_width, frame_height):
        """调整排除区域"""
        self.region_manager.adjust_exclude_regions(frame_width, frame_height)
        
    def _align_time(self, time_value, round_up=False):
        """对齐时间到整秒"""
        return math.ceil(time_value) if round_up else math.floor(time_value)
        
    def process_frame(self, frame, frame_count, use_gpu=False):
        """
        处理单帧并检测动作
        Args:
            frame: 输入帧
            frame_count: 当前帧计数
            use_gpu: 是否使用GPU加速
        Returns:
            tuple: (motion_detected, display_frame, segment)
            - motion_detected: 是否检测到动作
            - display_frame: 处理后的显示帧
            - segment: 如果有新的片段，返回片段信息，否则为None
        """
        if self.fps is None:
            raise RuntimeError("必须先调用set_fps设置视频帧率")
            
        # 更新当前时间
        self.current_time = frame_count / self.fps
        
        # 如果启用GPU加速，使用UMat
        if use_gpu:
            frame_gpu = cv2.UMat(frame)
            gray = cv2.cvtColor(frame_gpu, cv2.COLOR_BGR2GRAY)
            gray = cv2.GaussianBlur(gray, (21, 21), 0)
        else:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            gray = cv2.GaussianBlur(gray, (21, 21), 0)
        
        # 应用排除区域
        gray = self.region_manager.apply_regions(gray)
        
        if self.prev_frame is None:
            self.prev_frame = gray
            return False, frame, None
            
        # 计算差分
        frame_delta = cv2.absdiff(self.prev_frame, gray)
        if use_gpu:
            thresh = cv2.threshold(frame_delta, self.threshold, 255, cv2.THRESH_BINARY)[1]
            thresh = cv2.dilate(thresh, None, iterations=2)
            # 对于轮廓检测，需要下载到CPU
            thresh_cpu = thresh.get()
            contours, _ = cv2.findContours(thresh_cpu, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            display_frame = frame_gpu.get().copy() if isinstance(frame_gpu, cv2.UMat) else frame.copy()
        else:
            thresh = cv2.threshold(frame_delta, self.threshold, 255, cv2.THRESH_BINARY)[1]
            thresh = cv2.dilate(thresh, None, iterations=2)
            contours, _ = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            display_frame = frame.copy()
        
        # 处理显示帧
        self.region_manager.draw_regions(display_frame)
        
        # 检测动作
        motion_detected = False
        for contour in contours:
            if cv2.contourArea(contour) > self.min_area:
                motion_detected = True
                (x, y, w, h) = cv2.boundingRect(contour)
                cv2.rectangle(display_frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
        
        # 更新状态和处理片段
        segment = self._update_motion_state(motion_detected)
        
        self.prev_frame = gray
        return motion_detected, display_frame, segment
        
    def _update_motion_state(self, motion_detected):
        """
        更新动作状态并返回片段信息
        Returns:
            dict or None: 如果产生新的片段则返回片段信息，否则返回None
        """
        if motion_detected:
            self.static_frames = 0
            if not self.is_motion:
                # 只有当当前时间大于上一个片段的结束时间才开始新片段
                potential_start = self._align_time(self.current_time)
                if potential_start >= self.last_segment_end:
                    self.is_motion = True
                    self.segment_start = potential_start
            return None
        else:
            self.static_frames += 1
            if self.is_motion and self.static_frames >= self.static_frames_threshold:
                self.is_motion = False
                current_end = self._align_time(self.current_time, round_up=True)
                if self.segment_start is not None and current_end > self.segment_start:
                    segment = {
                        'start': self.segment_start,
                        'end': current_end
                    }
                    self.last_segment_end = current_end  # 更新最后一个片段的结束时间
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
        self.prev_frame = None
        self.is_motion = False
        self.static_frames = 0
        self.segment_start = None
        self.current_time = 0
        self.last_segment_end = 0  # 重置最后一个片段的结束时间