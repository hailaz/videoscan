"""显示管理器模块"""
import cv2

class DisplayManager:
    """负责视频帧的显示和窗口管理"""
    
    def __init__(self, window_scale=1.0):
        """初始化显示管理器"""
        self.window_scale = window_scale
        self.last_info = {}  # 存储上一次显示的信息
        
    def draw_overlay_text(self, frame, info_text, position='top-right'):
        """在帧上绘制叠加文本"""
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
        
    def display_frame(self, frame, info=None, title="Motion Detection"):
        """显示帧和相关信息
        
        Args:
            frame: 要显示的帧
            info: 要显示的信息字典，包含：
                - text: 要显示的文本
                - position: 文本位置 ('top-right', 'top-left' 等)
            title: 窗口标题
        """
        if frame is None:
            return False
            
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
            
        # 显示帧
        cv2.imshow(title, display_frame)
        
        # 处理键盘事件
        key = cv2.waitKey(1) & 0xFF
        return key == ord('q')
        
    def close_all_windows(self):
        """关闭所有显示窗口"""
        cv2.destroyAllWindows()