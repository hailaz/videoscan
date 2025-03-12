"""视频显示模块"""
import cv2

class VideoDisplay:
    def __init__(self, window_scale=1.0):
        """初始化显示管理器
        
        Args:
            window_scale: 窗口缩放比例
        """
        self.window_scale = window_scale
        self.windows = {}  # 存储所有窗口信息
        
    def draw_overlay_text(self, frame, text, position='top-right'):
        """在帧上绘制叠加文本
        
        Args:
            frame: 视频帧
            text: 要显示的文本
            position: 文本位置 ('top-right', 'top-left' 等)
        """
        if isinstance(frame, cv2.UMat):
            frame = frame.get()
            
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 1.2
        thickness = 2
        
        (text_width, text_height), baseline = cv2.getTextSize(
            text, font, font_scale, thickness)
            
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
        cv2.putText(frame, text, (x, y), font, font_scale, 
                   (0, 0, 0), thickness + 2)  # 黑色描边
        cv2.putText(frame, text, (x, y), font, font_scale, 
                   (255, 255, 255), thickness)  # 白色文字
                   
        return frame

    def get_window_position(self, window_id):
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
        
        index = len(self.windows)
        row = index // windows_per_row
        col = index % windows_per_row
        
        x = col * (window_width + 20)  # 20像素间隔
        y = row * (window_height + 40)  # 40像素间隔，给标题栏留空间
        
        return (x, y)

    def display_frame(self, frame, info=None, title="Video", window_id=None):
        """显示帧和相关信息
        
        Args:
            frame: 要显示的帧
            info: 显示信息字典，包含 text 和 position
            title: 窗口标题
            window_id: 窗口唯一标识符
        
        Returns:
            bool: 是否按下了退出键
        """
        if frame is None:
            return False

        window_id = window_id or title
            
        if isinstance(frame, cv2.UMat):
            frame = frame.get()
        
        if info and info.get('text'):
            frame = self.draw_overlay_text(
                frame, 
                info['text'], 
                info.get('position', 'top-right')
            )
        
        if self.window_scale != 1.0:
            frame = cv2.resize(
                frame, None,
                fx=self.window_scale,
                fy=self.window_scale
            )
            
        if window_id not in self.windows:
            cv2.namedWindow(window_id, cv2.WINDOW_NORMAL)
            x, y = self.get_window_position(window_id)
            cv2.moveWindow(window_id, x, y)
            self.windows[window_id] = {'position': (x, y)}
            
        cv2.imshow(window_id, frame)
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