"""运动检测模块"""
import cv2
import numpy as np
from .region_manager import RegionManager

class MotionDetector:
    def __init__(self, threshold=25, min_area=1000):
        self.threshold = threshold
        self.min_area = min_area
        self.prev_frame = None
        self.region_manager = RegionManager()

    def adjust_exclude_regions(self, frame_width, frame_height):
        """调整排除区域"""
        self.region_manager.adjust_exclude_regions(frame_width, frame_height)

    def process_frame(self, frame, use_gpu=False):
        """处理单帧并检测动作"""
        # 转换为灰度图
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (21, 21), 0)
        
        # 应用排除区域
        gray = self.region_manager.apply_regions(gray)
        
        if self.prev_frame is None:
            self.prev_frame = gray
            return False, frame
            
        # 计算差分
        frame_delta = cv2.absdiff(self.prev_frame, gray)
        thresh = cv2.threshold(frame_delta, self.threshold, 255, cv2.THRESH_BINARY)[1]
        thresh = cv2.dilate(thresh, None, iterations=2)
        contours, _ = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # 处理显示帧
        display_frame = frame.copy()
        self.region_manager.draw_regions(display_frame)
        
        motion_detected = False
        for contour in contours:
            if cv2.contourArea(contour) > self.min_area:
                motion_detected = True
                (x, y, w, h) = cv2.boundingRect(contour)
                cv2.rectangle(display_frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                
        self.prev_frame = gray
        return motion_detected, display_frame

    def reset(self):
        """重置检测器状态"""
        self.prev_frame = None