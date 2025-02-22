import cv2
import numpy as np
from datetime import datetime, timedelta
import os
import argparse
import platform
import subprocess
import ctypes
from pathlib import Path

class VideoSplitter:
    def __init__(self, threshold=30, min_area=1000, window_scale=0.7, static_frames_threshold=30, use_gpu=True, buffer_time=3, playback_speed=1.0):
        self.threshold = threshold
        self.min_area = min_area
        self.window_scale = window_scale
        self.prev_frame = None
        self.font = cv2.FONT_HERSHEY_SIMPLEX
        self.motion_points = []  # 只存储动作开始点
        self.static_frames_threshold = static_frames_threshold  # 静止帧阈值
        self.use_gpu = use_gpu
        self.ffmpeg_path = self._find_ffmpeg()
        self.intel_gpu = self._check_intel_gpu()
        self.motion_segments = []  # 存储动作片段的起止时间
        self.early_exit = False  # 保留标志，用于其他功能
        self.buffer_time = buffer_time  # 添加前后缓冲时间（秒）
        self.playback_speed = max(0.1, min(playback_speed, 16.0))  # 限制播放速度范围在 0.1-16 倍之间
        self.exclude_regions = [
            # 默认排除左上角区域 (x, y, width, height)
            {'x': 550, 'y': 46, 'w': 340, 'h': 55}
        ]
        self.progress_callback = None  # 添加进度回调函数
        print("已配置排除左上角时间显示区域")
        print(f"当前播放速度: {self.playback_speed}x")
        
        # 配置 Intel GPU 加速
        if self.intel_gpu and cv2.ocl.haveOpenCL():
            cv2.ocl.setUseOpenCL(True)
            if cv2.ocl.useOpenCL():
                print("已启用 Intel Arc GPU 加速")
                # 设置 Intel GPU 优化参数
                cv2.setUseOptimized(True)
                
                # 获取并打印 OpenCL 设备信息
                device = cv2.ocl.Device.getDefault()
                print(f"OpenCL 设备: {device.name()}")
                print(f"计算单元数量: {device.maxComputeUnits()}")
                print(f"最大工作组大小: {device.maxWorkGroupSize()}")
            else:
                print("Intel GPU 初始化失败，将使用 CPU 处理")
                self.use_gpu = False
        else:
            print("未检测到 Intel GPU 支持，将使用 CPU 处理")
            self.use_gpu = False

    def _find_ffmpeg(self):
        """查找 FFmpeg 可执行文件"""
        possible_paths = [
            Path("bin/ffmpeg.exe"),  # 相对路径
            Path(__file__).parent / "bin/ffmpeg.exe",  # 相对于脚本的路径
            Path("C:/ffmpeg/bin/ffmpeg.exe"),  # 常见安装路径
        ]
        
        for path in possible_paths:
            if path.exists():
                print(f"找到 FFmpeg: {path}")
                return str(path)
        
        print("警告: 未找到 FFmpeg，将使用 OpenCV 进行视频处理")
        return None

    def _check_intel_gpu(self):
        """检查是否有可用的 Intel GPU"""
        try:
            if cv2.ocl.haveOpenCL():
                # 获取默认设备
                device = cv2.ocl.Device_getDefault()
                if device is not None:
                    vendor = device.vendorName()
                    if "Intel" in vendor:
                        print(f"检测到 Intel GPU:")
                        print(f"设备名称: {device.name()}")
                        print(f"供应商: {vendor}")
                        print(f"OpenCL 版本: {device.version()}")
                        return True
            return False
        except Exception as e:
            print(f"GPU 检测出错: {str(e)}")
            return False

    def get_hardware_decoder(self, video_path):
        """获取适合的硬件解码器"""
        try:
            cap = cv2.VideoCapture(video_path, cv2.CAP_ANY)
            # 对于 Intel GPU，使用 MFX (Media SDK) 硬件加速
            if platform.system() == 'Windows':
                cap.set(cv2.CAP_PROP_HW_ACCELERATION, cv2.VIDEO_ACCELERATION_D3D11)
                cap.set(cv2.CAP_PROP_HW_DEVICE, 0)
            return cap
        except Exception as e:
            print(f"硬件解码初始化失败: {str(e)}")
            return cv2.VideoCapture(video_path)

    def format_time(self, seconds):
        """将秒数转换为可读的时间格式"""
        m, s = divmod(seconds, 60)
        h, m = divmod(m, 60)
        return f"{int(h):02d}:{int(m):02d}:{s:05.2f}"

    def merge_overlapping_segments(self):
        """合并重叠的视频片段"""
        if not self.motion_segments:
            return
            
        # 按开始时间排序
        self.motion_segments.sort(key=lambda x: x['start'])
        merged = []
        current = self.motion_segments[0]
        
        for next_seg in self.motion_segments[1:]:
            # 考虑缓冲区后的实际区间
            current_end = current['end'] + self.buffer_time
            next_start = next_seg['start'] - self.buffer_time
            
            # 如果两个片段重叠，合并它们
            if next_start <= current_end:
                current['end'] = max(current['end'], next_seg['end'])
            else:
                # 添加缓冲时间
                current['start'] = max(0, current['start'] - self.buffer_time)
                current['end'] = current['end'] + self.buffer_time
                merged.append(current)
                current = next_seg
        
        # 处理最后一个片段
        current['start'] = max(0, current['start'] - self.buffer_time)
        current['end'] = current['end'] + self.buffer_time
        merged.append(current)
        
        self.motion_segments = merged

        total_duration = 0
        print("\n检测到的动作片段:")
        for i, segment in enumerate(self.motion_segments):
            duration = segment['end'] - segment['start']
            total_duration += duration
            print(f"片段 {i+1}: {self.format_time(segment['start'])} - {self.format_time(segment['end'])} (时长: {self.format_time(duration)})")
        print(f"总时长: {self.format_time(total_duration)}")
        print(f"合并后的片段数量: {len(self.motion_segments)}")

    def set_progress_callback(self, callback):
        """设置进度回调函数"""
        self.progress_callback = callback

    def detect_motion_points(self, video_path):
        """使用 OpenCL 加速的动作检测并显示动作区域，合并连续动作片段"""
        cap = self.get_hardware_decoder(video_path)
        if not cap.isOpened():
            raise Exception("无法打开视频文件")

        # 获取第一帧来确定视频尺寸
        ret, first_frame = cap.read()
        if not ret:
            raise Exception("无法读取视频帧")
        
        # 根据视频尺寸调整排除区域
        frame_height, frame_width = first_frame.shape[:2]
        adjusted_exclude_regions = []
        for region in self.exclude_regions:
            # 确保排除区域不超过视频尺寸
            adj_region = region.copy()
            adj_region['w'] = min(region['w'], frame_width)
            adj_region['h'] = min(region['h'], frame_height)
            adjusted_exclude_regions.append(adj_region)
        self.exclude_regions = adjusted_exclude_regions
        
        cap.set(cv2.CAP_PROP_POS_FRAMES, 0)  # 重置到视频开始

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
                # 视频结束时，如果还有未结束的动作片段，将其添加到列表中
                if segment_start is not None:
                    self.motion_segments.append({
                        'start': segment_start,
                        'end': frame_count / fps
                    })
                break

            # 调整帧计数和时间计算，考虑播放速度
            current_time = (frame_count / fps) * self.playback_speed

            # 更新进度
            progress = (frame_count / total_frames) * 100
            if self.progress_callback:
                self.progress_callback(progress)
    
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
                continue
                
            # 动作检测
            frame_delta = cv2.absdiff(self.prev_frame, gray)
            thresh = cv2.threshold(frame_delta, self.threshold, 255, cv2.THRESH_BINARY)[1]
            thresh = cv2.dilate(thresh, None, iterations=2)
            contours, _ = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            # 在预览窗口中绘制检测到的动作区域和排除区域
            display_frame = frame.copy()
            
            # 绘制排除区域（红色半透明矩形）
            overlay = display_frame.copy()
            for region in self.exclude_regions:
                cv2.rectangle(overlay, 
                            (region['x'], region['y']), 
                            (region['x'] + region['w'], region['y'] + region['h']), 
                            (0, 0, 255), 
                            -1)  # -1 表示填充矩形
            cv2.addWeighted(overlay, 0.3, display_frame, 0.7, 0, display_frame)
            
            motion_detected = False
            
            for contour in contours:
                if cv2.contourArea(contour) > self.min_area:
                    motion_detected = True
                    # 获取轮廓的边界框
                    (x, y, w, h) = cv2.boundingRect(contour)
                    # 绘制绿色矩形框
                    cv2.rectangle(display_frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                    # 添加动作区域标签
                    cv2.putText(display_frame, "Motion", (x, y - 10),
                              cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
            
            # 更新动作状态
            if motion_detected:
                static_count = 0
                if not is_motion:
                    is_motion = True
                    segment_start = current_time
                    cv2.putText(frame, "Recording...", (10, 90), 
                           self.font, 1, (0, 0, 255), 2)
            else:
                static_count += 1
                # 根据播放速度调整静态帧计数阈值
                adjusted_threshold = int(self.static_frames_threshold / self.playback_speed)
                if is_motion and static_count >= adjusted_threshold:
                    is_motion = False
                    self.motion_segments.append({
                        'start': segment_start,
                        'end': current_time
                    })
                    segment_start = None
            
            # 显示处理进度（保留控制台输出）
            if frame_count % fps == 0:
                print(f"\r处理进度: {progress:.1f}%", end="")
            
            # 调整预览窗口大小并显示
            display_frame = cv2.resize(display_frame, None,
                                     fx=self.window_scale,
                                     fy=self.window_scale)
            cv2.imshow("Motion Detection", display_frame)
            
            self.prev_frame = gray
            frame_count += 1
            
            # 调整等待时间以适应播放速度
            wait_time = max(1, int(1000 / (fps * self.playback_speed)))  # 转换为毫秒
            if cv2.waitKey(wait_time) & 0xFF == ord('q'):
                # 如果当前有未结束的动作片段，将其添加到列表中
                if is_motion and segment_start is not None:
                    self.motion_segments.append({
                        'start': segment_start,
                        'end': current_time
                    })
                break
                
        cap.release()
        cv2.destroyAllWindows()
        print("\n动作检测完成！")
        
        # 合并重叠的片段
        print("正在合并重叠片段...")
        self.merge_overlapping_segments()
        
        return True  # 始终返回 True，表示需要进行切割


    def split_video(self, video_path, output_dir="切割视频"):
        """简单地按时间切割视频"""
        if not self.motion_segments:
            print("没有检测到需要切割的片段！")
            return
            
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        # 获取基础文件名（不包含扩展名）
        base_filename = os.path.splitext(os.path.basename(video_path))[0]
        
        total_segments = len(self.motion_segments)
        for i, segment in enumerate(self.motion_segments):
            try:
                # 计算当前进度
                current_progress = ((i + 1) / total_segments) * 100
                if self.progress_callback:
                    self.progress_callback(current_progress)

                # 格式化开始和结束时间
                start_time = segment['start']
                end_time = segment['end']
                start_str = self.format_time(start_time).replace(":", "_")
                end_str = self.format_time(end_time).replace(":", "_")
                duration = end_time - start_time
                
                # 设置新的输出文件名格式
                output_filename = f"{base_filename}_片段{i+1}_{start_str}到{end_str}.mp4"
                output_path = os.path.join(output_dir, output_filename)

                # 添加时间信息输出
                print(f"\n正在切割片段 {i+1}:")
                print(f"开始时间: {self.format_time(start_time)}")
                print(f"结束时间: {self.format_time(end_time)}")
                print(f"片段时长: {self.format_time(duration)}")

                if self.ffmpeg_path:
                    # 使用FFmpeg命令进行切割
                    cmd = [
                        self.ffmpeg_path,
                        '-i', video_path,
                        '-ss', str(start_time),
                        '-t', str(duration),
                        '-c', 'copy',
                        '-y',
                        output_path
                    ]

                    print(f"\n正在切割片段 {i+1}/{total_segments}...")
                    subprocess.run(cmd, check=True)
                    print(f"已保存片段 {i+1}: {output_path}")

            except Exception as e:
                print(f"处理片段 {i+1}/{total_segments} 时出错: {str(e)}")
                continue

        # 完成时设置进度为100%
        if self.progress_callback:
            self.progress_callback(100)
        print("视频切割完成！")

def signal_handler(signum, frame):
    """处理程序退出信号"""
    print("\n检测到退出信号，正在完成剩余工作...")
    if hasattr(signal_handler, 'splitter') and signal_handler.splitter.motion_segments:
        print("正在保存已检测到的视频片段...")
        signal_handler.splitter.split_video(signal_handler.video_path, signal_handler.output_dir)
    cv2.destroyAllWindows()
    sys.exit(0)

if __name__ == "__main__":
    import signal
    import sys
    
    parser = argparse.ArgumentParser(description='视频动作切割工具')
    parser.add_argument('video', type=str, help='输入视频文件的路径')
    parser.add_argument('--output', type=str, default='切割视频', help='输出视频保存目录')
    parser.add_argument('--threshold', type=int, default=25, help='检测阈值')
    parser.add_argument('--min-area', type=int, default=1000, help='最小检测区域')
    parser.add_argument('--scale', type=float, default=0.4, help='预览窗口缩放比例')
    parser.add_argument('--cpu', action='store_true', help='强制使用 CPU 处理')
    parser.add_argument('--speed', type=float, default=2.0, 
                      help='视频处理速度倍率 (0.1-16.0，默认1.0)')
    
    args = parser.parse_args()  # 修复这里的错误
    
    splitter = VideoSplitter(
        threshold=args.threshold,
        min_area=args.min_area,
        window_scale=args.scale,
        use_gpu=not args.cpu,  # 默认使用 GPU，除非指定 --cpu
        playback_speed=args.speed  # 添加播放速度参数
    )
    
    # 设置信号处理
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # 保存参数到信号处理器，以便在退出时使用
    signal_handler.splitter = splitter
    signal_handler.video_path = args.video
    signal_handler.output_dir = args.output
    
    try:
        # 检测动作点
        print("开始检测动作...")
        splitter.detect_motion_points(args.video)  # 不再需要获取返回值
        
        # 切割视频
        print("开始切割视频...")
        splitter.split_video(args.video, args.output)
    except KeyboardInterrupt:
        # 处理 Ctrl+C
        signal_handler(signal.SIGINT, None)
    except Exception as e:
        print(f"发生错误: {str(e)}")
        # 如果有未处理的片段，尝试保存
        if splitter.motion_segments:
            print("尝试保存已检测到的片段...")
            splitter.split_video(args.video, args.output)
        sys.exit(1)
