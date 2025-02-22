"""运动检测区域管理模块"""
import cv2
import numpy as np

class RegionManager:
    """检测区域管理类"""
    def __init__(self):
        self.exclude_regions = []
        self.default_exclude_regions = [
            # 默认排除左上角区域 (x, y, width, height)
            {'x': 550, 'y': 46, 'w': 340, 'h': 55}
        ]

    def adjust_exclude_regions(self, frame_width, frame_height):
        """调整排除区域"""
        self.exclude_regions = []
        
        # 添加默认排除区域
        for region in self.default_exclude_regions:
            self.exclude_regions.append({
                'x': region['x'],
                'y': region['y'],
                'width': region['w'],
                'height': region['h']
            })

    def apply_regions(self, frame):
        """在帧上应用排除区域"""
        for region in self.exclude_regions:
            x, y = region['x'], region['y']
            w, h = region['width'], region['height']
            # 确保坐标不超出图像边界
            if y + h > frame.shape[0] or x + w > frame.shape[1]:
                continue
            frame[y:y+h, x:x+w] = 0
        return frame

    def draw_regions(self, frame):
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