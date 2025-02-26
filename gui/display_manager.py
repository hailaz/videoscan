"""显示管理器模块"""
import cv2
from typing import Dict, Any

class DisplayManager:
    """负责视频帧的显示和窗口管理"""
    
    def __init__(self, window_scale=1.0):
        """初始化显示管理器"""
        self.window_scale = window_scale
        self.windows = {}  # 存储所有窗口信息 {window_id: window_info}
        self.last_info = {}  # 存储上一次显示的信息

    def draw_overlay_text(self, frame, info_text, position='top-right'):
        """在帧上绘制叠加文本"""
        # 如果是 UMat 对象，需要先转换回 CPU
        if isinstance(frame, cv2.UMat):
            frame = frame.get()
            
        # 设置字体参数
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 1.2
        thickness = 2
        
        # 获取文本大小
        (text_width, text_height), baseline = cv2.getTextSize(
            info_text, font, font_scale, thickness)
            
        # 计算文本位置
        if position == 'top-right':
            x = frame.shape[1] - text_width - 20
            y = text_height + 20
            
        # 创建文本背景
        padding = 8
        overlay = frame.copy()
        cv2.rectangle(overlay, 
                     (x - padding, y - text_height - padding),
                     (x + text_width + padding, y + padding),
                     (0, 0, 0), -1)
                     
        # 添加半透明背景
        alpha = 0.7
        frame = cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0)
        
        # 添加文本（带描边）
        cv2.putText(frame, info_text, (x, y), font, font_scale, 
                   (0, 0, 0), thickness + 2)  # 黑色描边
        cv2.putText(frame, info_text, (x, y), font, font_scale, 
                   (255, 255, 255), thickness)  # 白色文字
                   
        return frame

    def get_window_position(self, window_id: str) -> tuple:
        """计算窗口位置
        
        Args:
            window_id: 窗口ID
        
        Returns:
            tuple: (x, y) 窗口位置
        """
        screen_width = 1920  # 假设屏幕宽度
        window_width = 640   # 假设窗口宽度
        window_height = 480  # 假设窗口高度
        windows_per_row = 3  # 每行显示的窗口数
        
        # 计算窗口索引
        index = len(self.windows)
        row = index // windows_per_row
        col = index % windows_per_row
        
        # 计算位置
        x = col * (window_width + 20)  # 20像素间隔
        y = row * (window_height + 40)  # 40像素间隔，给标题栏留空间
        
        return (x, y)

    def display_frame(self, frame, info=None, title="Motion Detection", window_id=None):
        """显示帧和相关信息
        
        Args:
            frame: 要显示的帧
            info: 要显示的信息字典，包含：
                - text: 要显示的文本
                - position: 文本位置 ('top-right', 'top-left' 等)
            title: 窗口标题
            window_id: 窗口唯一标识符，用于多窗口显示
        """
        if frame is None:
            return False
            
        # 生成窗口ID
        if window_id is None:
            window_id = title

        # 如果是 UMat 对象，需要先转换回 CPU
        if isinstance(frame, cv2.UMat):
            frame = frame.get()
        
        # 添加文本叠加
        if info and info.get('text'):
            frame = self.draw_overlay_text(
                frame, 
                info['text'], 
                info.get('position', 'top-right')
            )
        
        # 缩放显示帧
        if self.window_scale != 1.0:
            display_frame = cv2.resize(
                frame, None,
                fx=self.window_scale,
                fy=self.window_scale
            )
        else:
            display_frame = frame
            
        # 创建和定位窗口
        if window_id not in self.windows:
            cv2.namedWindow(window_id, cv2.WINDOW_NORMAL)
            x, y = self.get_window_position(window_id)
            cv2.moveWindow(window_id, x, y)
            self.windows[window_id] = {'position': (x, y)}
            
        # 显示帧
        cv2.imshow(window_id, display_frame)
        
        # 处理键盘事件
        key = cv2.waitKey(1) & 0xFF
        return key == ord('q')

    def close_window(self, window_id):
        """关闭指定的窗口"""
        if window_id in self.windows:
            cv2.destroyWindow(window_id)
            del self.windows[window_id]

    def close_all_windows(self):
        """关闭所有显示窗口"""
        cv2.destroyAllWindows()
        self.windows.clear()