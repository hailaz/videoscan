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
        # 获取帧的尺寸，处理 UMat 对象
        if isinstance(frame, cv2.UMat):
            frame_height, frame_width = frame.get().shape[:2]
        else:
            frame_height, frame_width = frame.shape[:2]
        
        # 创建掩码
        if isinstance(frame, cv2.UMat):
            mask = cv2.UMat(np.ones(frame.get().shape[:2], dtype=np.uint8))
        else:
            mask = np.ones(frame.shape[:2], dtype=np.uint8)

        # 在掩码上绘制排除区域
        for region in self.exclude_regions:
            x, y = region['x'], region['y']
            w, h = region['width'], region['height']
            # 确保坐标不超出图像边界
            if y + h > frame_height or x + w > frame_width:
                continue
            if isinstance(mask, cv2.UMat):
                # 对于 UMat，我们需要使用 OpenCV 函数
                cv2.rectangle(mask, (x, y), (x + w, y + h), 0, -1)
            else:
                mask[y:y+h, x:x+w] = 0

        # 应用掩码
        return cv2.multiply(frame, cv2.UMat(mask) if isinstance(frame, cv2.UMat) else mask)

    def draw_regions(self, frame):
        """绘制排除区域"""
        # 处理 UMat 对象
        if isinstance(frame, cv2.UMat):
            frame = frame.get()
        
        overlay = frame.copy()
        for region in self.exclude_regions:
            cv2.rectangle(overlay, 
                        (region['x'], region['y']), 
                        (region['x'] + region['width'], region['y'] + region['height']), 
                        (0, 0, 255), 
                        -1)
        cv2.addWeighted(overlay, 0.3, frame, 0.7, 0, frame)
        return frame