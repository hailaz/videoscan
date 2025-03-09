"""硬件加速器模块"""
import cv2
import platform
import os
from pathlib import Path
from .hardware_detector import HardwareDetector

class HardwareAccelerator:
    def __init__(self):
        self.detector = HardwareDetector()
        self.gpu_info = self.detector.gpu_info
        self.use_gpu = self.gpu_info['has_gpu']
        self.ffmpeg_path = self._find_ffmpeg()
        self._initialize_gpu()

    def _find_ffmpeg(self):
        """查找 FFmpeg 可执行文件"""
        possible_paths = [
            Path("bin/ffmpeg.exe"),  # 相对路径
            Path(__file__).parent.parent / "bin/ffmpeg.exe",  # 相对于脚本的路径
            Path("C:/ffmpeg/bin/ffmpeg.exe"),  # 常见安装路径
        ]
        
        for path in possible_paths:
            if path.exists():
                print(f"找到 FFmpeg: {path}")
                return str(path)
        
        print("警告: 未找到 FFmpeg，将使用 OpenCV 进行视频处理")
        return None

    def _initialize_gpu(self):
        """初始化GPU加速"""
        try:
            if self.gpu_info['opencl_available']:
                cv2.ocl.setUseOpenCL(True)
                cv2.setUseOptimized(True)
                
                # Intel GPU优化
                if self.gpu_info['intel_gpu']:
                    # 设置Intel优化标志
                    cv2.setNumThreads(self.detector.cpu_count)
                    if self.gpu_info['intel_arc']:
                        # Arc GPU特殊优化
                        os.environ['OPENCV_OPENCL_DEVICE'] = 'GPU'
                        os.environ['OPENCV_OPENCL_WAIT_KERNEL'] = '0'
                
                print(f"GPU加速已启用: {'Intel Arc' if self.gpu_info['intel_arc'] else 'Intel' if self.gpu_info['intel_gpu'] else 'Generic'}")
                return
                
            print("未检测到 GPU 支持，将使用 CPU 处理")
        except Exception as e:
            print(f"GPU 检测出错: {str(e)}")
            self.use_gpu = False

    def get_video_capture(self, video_path):
        """获取适合的视频捕获对象"""
        try:
            # 针对 Intel Arc GPU 使用 D3D11 加速
            if platform.system() == 'Windows' and self.use_gpu:
                cap = cv2.VideoCapture(video_path, cv2.CAP_MSMF)  # 使用 Media Foundation
                if self.gpu_info['intel_arc']:
                    # 设置硬件加速
                    cap.set(cv2.CAP_PROP_HW_ACCELERATION, cv2.VIDEO_ACCELERATION_D3D11)
                    cap.set(cv2.CAP_PROP_HW_DEVICE, 0)
                    cap.set(cv2.CAP_PROP_HW_ACCELERATION_USE_OPENCL, 1)
                elif self.gpu_info['intel_gpu']:
                    # 普通Intel GPU优化
                    cap.set(cv2.CAP_PROP_HW_ACCELERATION, cv2.VIDEO_ACCELERATION_ANY)
                    cap.set(cv2.CAP_PROP_HW_ACCELERATION_USE_OPENCL, 1)
                return cap
                
            # 对于其他情况，使用默认的视频捕获
            return cv2.VideoCapture(video_path)
        except Exception as e:
            print(f"硬件解码初始化失败: {str(e)}")
            return cv2.VideoCapture(video_path)

    @property
    def has_gpu(self):
        """是否启用GPU加速"""
        return self.use_gpu

    @property
    def has_ffmpeg(self):
        """是否有可用的FFmpeg"""
        return self.ffmpeg_path is not None
