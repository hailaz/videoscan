import cv2
import numpy as np
from datetime import datetime
import os
import argparse  # 新增导入

class MotionDetector:
    """运动检测器类，用于视频动作检测和录制"""
    
    def __init__(self, threshold=30, min_area=500, window_scale=0.7, static_frames_threshold=30):
        """
        初始化运动检测器
        :param threshold: 像素差异阈值，用于确定移动检测的敏感度
        :param min_area: 最小检测区域，小于此面积的移动将被忽略
        :param window_scale: 窗口缩放比例
        :param static_frames_threshold: 停止录制所需的静止帧数
        """
        self.threshold = threshold
        self.min_area = min_area
        self.prev_frame = None  # 存储前一帧图像
        self.is_recording = False  # 录制状态标志
        self.out = None  # 视频写入对象
        self.start_time = None  # 录制开始时间
        self.window_scale = window_scale  # 添加窗口缩放比例参数
        self.font = cv2.FONT_HERSHEY_SIMPLEX  # 添加字体设置
        self.static_frame_count = 0  # 静止帧计数器
        self.static_frames_threshold = static_frames_threshold  # 停止录制所需的静止帧数
        self.video_bitrate = None  # 添加码率属性
        
    def process_video(self, video_source=0, output_dir="检测视频"):
        """
        处理视频并检测运动
        :param video_source: 视频来源，可以是摄像头索引或视频文件路径
        :param output_dir: 检测到运动后保存视频片段的目录
        """
        # 打开视频源
        cap = cv2.VideoCapture(video_source)
        
        # 确保输出目录存在
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
        # 获取视频基本信息
        fps = int(cap.get(cv2.CAP_PROP_FPS))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        # 获取视频码率（对于摄像头，使用默认码率）
        if isinstance(video_source, str):
            # 如果是视频文件，获取其码率
            self.video_bitrate = int(cap.get(cv2.CAP_PROP_BITRATE))
        else:
            # 如果是摄像头，设置一个默认码率（8Mbps）
            self.video_bitrate = 8000000
            
        while True:
            # 读取视频帧
            ret, frame = cap.read()
            if not ret:
                break
                
            # 图像预处理：转灰度并进行高斯模糊
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            gray = cv2.GaussianBlur(gray, (21, 21), 0)
            
            # 首帧处理
            if self.prev_frame is None:
                self.prev_frame = gray
                continue
                
            # 计算当前帧与前一帧的差异
            frame_delta = cv2.absdiff(self.prev_frame, gray)
            # 对差异图像进行阈值处理
            thresh = cv2.threshold(frame_delta, self.threshold, 255, cv2.THRESH_BINARY)[1]
            # 扩展白色区域以连接临近运动区域
            thresh = cv2.dilate(thresh, None, iterations=2)
            
            # 寻找运动物体的轮廓
            contours, _ = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            # 检测是否存在足够大的运动区域，并标记运动物体
            motion_detected = False
            for contour in contours:
                area = cv2.contourArea(contour)
                if area > self.min_area:
                    motion_detected = True
                    # 获取边界框
                    (x, y, w, h) = cv2.boundingRect(contour)
                    # 绘制边界框
                    cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                    # 显示运动物体面积
                    cv2.putText(frame, f"Area: {int(area)}px", 
                              (x, y - 10), self.font, 0.5, (0, 255, 0), 2)

            # 更新静止帧计数
            if motion_detected:
                self.static_frame_count = 0
            else:
                self.static_frame_count += 1

            # 添加时间戳
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cv2.putText(frame, timestamp, (10, 30), self.font, 1, (0, 255, 0), 2)
            
            # 如果检测到运动，显示"Motion Detected"
            if motion_detected:
                cv2.putText(frame, "Motion Detected", (10, 60), 
                           self.font, 1, (0, 0, 255), 2)

            # 根据检测结果开始或停止录制
            if motion_detected and not self.is_recording:
                self.start_recording(output_dir, fps, width, height)
            elif self.is_recording and self.static_frame_count >= self.static_frames_threshold:
                self.stop_recording()

            # 如果正在录制，写入当前帧并显示录制状态
            if self.is_recording:
                self.out.write(frame)
                cv2.putText(frame, "Recording...", (10, 90), 
                           self.font, 1, (0, 0, 255), 2)
                
            # 更新前一帧
            self.prev_frame = gray
            
            # 在显示之前缩放图像
            display_frame = cv2.resize(frame, None, 
                                    fx=self.window_scale, 
                                    fy=self.window_scale, 
                                    interpolation=cv2.INTER_AREA)
            
            # 显示实时画面
            cv2.imshow("Security Feed", display_frame)
            # 按'q'键退出
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
                
        # 清理资源
        if self.is_recording:
            self.stop_recording()
            
        cap.release()
        cv2.destroyAllWindows()
        
    def start_recording(self, output_dir, fps, width, height):
        """
        开始录制视频
        :param output_dir: 输出目录
        :param fps: 帧率
        :param width: 视频宽度
        :param height: 视频高度
        """
        self.start_time = datetime.now()
        filename = f"{output_dir}/动作检测_{self.start_time.strftime('%Y%m%d_%H%M%S')}.mp4"
        # 使用 H.264 编码器，支持设置码率
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        self.out = cv2.VideoWriter(filename, fourcc, fps, (width, height), True)
        
        # 设置输出视频的码率
        if self.video_bitrate:
            self.out.set(cv2.VIDEOWRITER_PROP_QUALITY, 100)  # 设置最高质量
            # 某些OpenCV版本支持直接设置码率
            try:
                self.out.set(cv2.VIDEOWRITER_PROP_BITRATE, self.video_bitrate)
            except:
                pass  # 如果不支持设置码率，就使用默认码率
        
        self.is_recording = True
        
    def stop_recording(self):
        """停止录制视频并释放资源"""
        self.is_recording = False
        self.out.release()
        self.out = None

if __name__ == "__main__":
    # 创建参数解析器
    parser = argparse.ArgumentParser(description='视频动作检测工具')
    parser.add_argument('--video', type=str, help='输入视频文件的路径，如果不指定则使用摄像头')
    parser.add_argument('--output', type=str, default='检测视频', help='输出视频保存目录')
    parser.add_argument('--threshold', type=int, default=25, help='检测阈值')
    parser.add_argument('--min-area', type=int, default=1000, help='最小检测区域')
    parser.add_argument('--scale', type=float, default=0.4, help='显示窗口缩放比例')
    parser.add_argument('--static-frames', type=int, default=30, help='停止录制所需的连续静止帧数（默认：30，约1秒）')
    
    # 解析参数
    args = parser.parse_args()
    
    # 创建检测器实例
    detector = MotionDetector(
        threshold=args.threshold,
        min_area=args.min_area,
        window_scale=args.scale,
        static_frames_threshold=args.static_frames
    )
    
    # 如果指定了视频文件就使用视频文件，否则使用摄像头
    video_source = args.video if args.video else 0
    detector.process_video(video_source=video_source, output_dir=args.output)
