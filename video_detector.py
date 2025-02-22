import cv2
import numpy as np
from hardware_utils import get_hardware_decoder
from utils import format_time, merge_overlapping_segments

class VideoDetector:
    def __init__(self, threshold=30, min_area=1000, window_scale=0.7, 
                 static_frames_threshold=30, use_gpu=True, buffer_time=3, 
                 playback_speed=1.0):
        self.threshold = threshold
        self.min_area = min_area
        self.window_scale = window_scale
        self.prev_frame = None
        self.font = cv2.FONT_HERSHEY_SIMPLEX
        self.static_frames_threshold = static_frames_threshold
        self.use_gpu = use_gpu
        self.buffer_time = buffer_time
        self.playback_speed = max(0.1, min(playback_speed, 16.0))
        self.exclude_regions = [
            {'x': 550, 'y': 46, 'w': 340, 'h': 55}  # 默认排除左上角区域
        ]
        self.progress_callback = None
        self.motion_segments = []

    def set_progress_callback(self, callback):
        """设置进度回调函数"""
        self.progress_callback = callback

    def detect_motion(self, video_path):
        """使用 OpenCL 加速的动作检测并显示动作区域"""
        cap = get_hardware_decoder(video_path)
        if not cap.isOpened():
            raise Exception("无法打开视频文件")

        # 初始化视频参数
        ret, first_frame = cap.read()
        if not ret:
            raise Exception("无法读取视频帧")
        
        # 调整排除区域
        self._adjust_exclude_regions(first_frame)
        cap.set(cv2.CAP_PROP_POS_FRAMES, 0)

        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = int(cap.get(cv2.CAP_PROP_FPS))
        frame_count = 0
        static_count = 0
        is_motion = False
        segment_start = None

        print("开始检测动作...")

        while True:
            ret, frame = cap.read()
            if not ret:
                if segment_start is not None:
                    self.motion_segments.append({
                        'start': segment_start,
                        'end': frame_count / fps
                    })
                break

            current_time = (frame_count / fps) * self.playback_speed
            self._update_progress(frame_count, total_frames)
            
            # 处理当前帧
            motion_detected = self._process_frame(frame)
            
            # 更新动作状态
            if motion_detected:
                static_count = 0
                if not is_motion:
                    is_motion = True
                    segment_start = current_time
            else:
                static_count += 1
                adjusted_threshold = int(self.static_frames_threshold / self.playback_speed)
                if is_motion and static_count >= adjusted_threshold:
                    is_motion = False
                    self.motion_segments.append({
                        'start': segment_start,
                        'end': current_time
                    })
                    segment_start = None
            
            if cv2.waitKey(max(1, int(1000 / (fps * self.playback_speed)))) & 0xFF == ord('q'):
                break

            frame_count += 1

        cap.release()
        cv2.destroyAllWindows()
        print("\n动作检测完成！")
        
        # 合并重叠片段
        self.motion_segments = merge_overlapping_segments(self.motion_segments, self.buffer_time)
        return True

    def _adjust_exclude_regions(self, frame):
        """根据视频尺寸调整排除区域"""
        frame_height, frame_width = frame.shape[:2]
        adjusted_regions = []
        for region in self.exclude_regions:
            adj_region = region.copy()
            adj_region['w'] = min(region['w'], frame_width)
            adj_region['h'] = min(region['h'], frame_height)
            adjusted_regions.append(adj_region)
        self.exclude_regions = adjusted_regions

    def _process_frame(self, frame):
        """处理单个视频帧并检测动作"""
        if self.use_gpu:
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
            return False
            
        # 动作检测
        frame_delta = cv2.absdiff(self.prev_frame, gray)
        thresh = cv2.threshold(frame_delta, self.threshold, 255, cv2.THRESH_BINARY)[1]
        thresh = cv2.dilate(thresh, None, iterations=2)
        contours, _ = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # 显示检测结果
        self._display_detection_results(frame, contours)
        
        self.prev_frame = gray
        return any(cv2.contourArea(contour) > self.min_area for contour in contours)

    def _display_detection_results(self, frame, contours):
        """显示检测结果"""
        display_frame = frame.copy()
        
        # 绘制排除区域
        overlay = display_frame.copy()
        for region in self.exclude_regions:
            cv2.rectangle(overlay, 
                        (region['x'], region['y']), 
                        (region['x'] + region['w'], region['y'] + region['h']), 
                        (0, 0, 255), 
                        -1)
        cv2.addWeighted(overlay, 0.3, display_frame, 0.7, 0, display_frame)
        
        # 绘制动作区域
        for contour in contours:
            if cv2.contourArea(contour) > self.min_area:
                (x, y, w, h) = cv2.boundingRect(contour)
                cv2.rectangle(display_frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                cv2.putText(display_frame, "Motion", (x, y - 10),
                          cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        
        # 显示预览
        display_frame = cv2.resize(display_frame, None,
                                 fx=self.window_scale,
                                 fy=self.window_scale)
        cv2.imshow("Motion Detection", display_frame)

    def _update_progress(self, frame_count, total_frames):
        """更新处理进度"""
        progress = (frame_count / total_frames) * 100
        if self.progress_callback:
            self.progress_callback(progress)