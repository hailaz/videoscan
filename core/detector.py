import cv2
import numpy as np

class MotionDetector:
    def __init__(self, threshold=30, min_area=1000, exclude_regions=None):
        self.threshold = threshold
        self.min_area = min_area
        self.prev_frame = None
        self.exclude_regions = exclude_regions or [
            # 默认排除左上角区域 (x, y, width, height)
            {'x': 550, 'y': 46, 'w': 340, 'h': 55}
        ]
        self.motion_segments = []

    def adjust_exclude_regions(self, frame_width, frame_height):
        """根据视频尺寸调整排除区域"""
        adjusted_regions = []
        for region in self.exclude_regions:
            adj_region = region.copy()
            adj_region['w'] = min(region['w'], frame_width)
            adj_region['h'] = min(region['h'], frame_height)
            adjusted_regions.append(adj_region)
        self.exclude_regions = adjusted_regions

    def process_frame(self, frame, use_gpu=False):
        """处理单帧并检测动作"""
        if use_gpu:
            gpu_frame = cv2.UMat(frame)
            gpu_gray = cv2.cvtColor(gpu_frame, cv2.COLOR_BGR2GRAY)
            gpu_blur = cv2.GaussianBlur(gpu_gray, (21, 21), 0)
            gray = gpu_blur.get()
        else:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            gray = cv2.GaussianBlur(gray, (21, 21), 0)

        # 在排除区域内填充黑色
        for region in self.exclude_regions:
            gray[region['y']:region['y']+region['h'], 
                 region['x']:region['x']+region['w']] = 0

        if self.prev_frame is None:
            self.prev_frame = gray
            return False, frame.copy()

        # 动作检测
        frame_delta = cv2.absdiff(self.prev_frame, gray)
        thresh = cv2.threshold(frame_delta, self.threshold, 255, cv2.THRESH_BINARY)[1]
        thresh = cv2.dilate(thresh, None, iterations=2)
        contours, _ = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # 处理显示帧
        display_frame = frame.copy()
        self._draw_exclude_regions(display_frame)
        
        motion_detected = False
        for contour in contours:
            if cv2.contourArea(contour) > self.min_area:
                motion_detected = True
                self._draw_motion_box(display_frame, contour)

        self.prev_frame = gray
        return motion_detected, display_frame

    def _draw_exclude_regions(self, frame):
        """绘制排除区域"""
        overlay = frame.copy()
        for region in self.exclude_regions:
            cv2.rectangle(overlay, 
                        (region['x'], region['y']), 
                        (region['x'] + region['w'], region['y'] + region['h']), 
                        (0, 0, 255), 
                        -1)
        cv2.addWeighted(overlay, 0.3, frame, 0.7, 0, frame)

    def _draw_motion_box(self, frame, contour):
        """绘制动作检测框"""
        (x, y, w, h) = cv2.boundingRect(contour)
        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
        cv2.putText(frame, "Motion", (x, y - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

    def reset(self):
        """重置检测器状态"""
        self.prev_frame = None
        self.motion_segments = []