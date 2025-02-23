import cv2
import numpy as np

class MotionDetector:
    def __init__(self, threshold=25, min_area=1000):
        self.threshold = threshold
        self.min_area = min_area
        self.prev_frame = None
        self.exclude_regions = []  # 用于存储自动计算的排除区域
        self.default_exclude_regions = [
            # 默认排除左上角区域 (x, y, width, height)
            {'x': 550, 'y': 46, 'w': 340, 'h': 55}
        ]
        
    def adjust_exclude_regions(self, frame_width, frame_height):
        """调整排除区域"""
        # 自动计算视频边缘的排除区域
        edge_width = int(frame_width * 0.02)  # 2%的边缘区域
        edge_height = int(frame_height * 0.02)
        
        self.exclude_regions = [
            # 左边缘
            {'x': 0, 'y': 0, 'width': edge_width, 'height': frame_height},
            # 右边缘
            {'x': frame_width - edge_width, 'y': 0, 'width': edge_width, 'height': frame_height},
            # 上边缘
            {'x': 0, 'y': 0, 'width': frame_width, 'height': edge_height},
            # 下边缘
            {'x': 0, 'y': frame_height - edge_height, 'width': frame_width, 'height': edge_height}
        ]
        
        # 添加默认排除区域
        for region in self.default_exclude_regions:
            # 确保区域参数名称一致
            self.exclude_regions.append({
                'x': region['x'],
                'y': region['y'],
                'width': region['w'],
                'height': region['h']
            })
        
    def _apply_regions(self, frame):
        """在帧上应用排除区域"""
        # 应用自动计算的排除区域
        for region in self.exclude_regions:
            x, y = region['x'], region['y']
            w, h = region['width'], region['height']
            # 确保坐标不超出图像边界
            if y + h > frame.shape[0] or x + w > frame.shape[1]:
                continue
            frame[y:y+h, x:x+w] = 0
        return frame

    def _draw_exclude_regions(self, frame):
        """绘制排除区域"""
        overlay = frame.copy()
        for region in self.exclude_regions:
            cv2.rectangle(overlay, 
                        (region['x'], region['y']), 
                        (region['x'] + region['width'], region['y'] + region['height']), 
                        (0, 0, 255), 
                        -1)
        cv2.addWeighted(overlay, 0.3, frame, 0.7, 0, frame)
        return frame
        
    def process_frame(self, frame, use_gpu=False):
        """处理单帧并检测动作"""
        # 转换为灰度图
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (21, 21), 0)
        
        # 应用排除区域
        gray = self._apply_regions(gray)
        
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
        
        # 使用新的方法绘制半透明的排除区域
        self._draw_exclude_regions(display_frame)
        
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