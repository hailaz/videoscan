"""基础动作检测器"""
import cv2
import numpy as np
import math

class BaseDetector:
    def __init__(self, threshold=25, min_area=1000, static_time_threshold=1.0):
        """初始化动作检测器
        Args:
            threshold: 像素差异阈值
            min_area: 最小检测区域面积
            static_time_threshold: 静止时间阈值(秒)
        """
        self.threshold = threshold
        self.min_area = min_area
        self.static_time_threshold = static_time_threshold
        self.prev_frame = None
        self.fps = None
        self.static_frames_threshold = None
    
    def set_fps(self, fps):
        """设置视频FPS，用于计算静止时间阈值"""
        self.fps = fps
        self.static_frames_threshold = int(self.static_time_threshold * fps)
    
    def _align_time(self, time_value, round_up=False):
        """对齐时间到整秒"""
        return math.ceil(time_value) if round_up else math.floor(time_value)
    
    def detect_motion(self, frame, use_gpu=False):
        """检测帧中的动作
        Args:
            frame: 输入帧
            use_gpu: 是否使用GPU加速
        Returns:
            tuple: (has_motion, display_frame, contours)
        """
        if use_gpu:
            frame_gpu = cv2.UMat(frame)
            gray = cv2.cvtColor(frame_gpu, cv2.COLOR_BGR2GRAY)
            gray = cv2.GaussianBlur(gray, (21, 21), 0)
        else:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            gray = cv2.GaussianBlur(gray, (21, 21), 0)
        
        if self.prev_frame is None:
            self.prev_frame = gray
            return False, frame, []
        
        # 计算差分
        frame_delta = cv2.absdiff(self.prev_frame, gray)
        if use_gpu:
            thresh = cv2.threshold(frame_delta, self.threshold, 255, cv2.THRESH_BINARY)[1]
            thresh = cv2.dilate(thresh, None, iterations=2)
            thresh_cpu = thresh.get()
            contours, _ = cv2.findContours(thresh_cpu, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            display_frame = frame_gpu.get().copy() if isinstance(frame_gpu, cv2.UMat) else frame.copy()
        else:
            thresh = cv2.threshold(frame_delta, self.threshold, 255, cv2.THRESH_BINARY)[1]
            thresh = cv2.dilate(thresh, None, iterations=2)
            contours, _ = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            display_frame = frame.copy()
            
        has_motion = False
        for contour in contours:
            if cv2.contourArea(contour) > self.min_area:
                has_motion = True
                (x, y, w, h) = cv2.boundingRect(contour)
                cv2.rectangle(display_frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                
        self.prev_frame = gray
        return has_motion, display_frame, contours