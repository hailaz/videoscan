import cv2
import platform
from pathlib import Path

class HardwareAccelerator:
    def __init__(self):
        self.use_gpu = False
        self.intel_gpu = False
        self.intel_arc = False
        self.ffmpeg_path = self._find_ffmpeg()
        self._initialize_gpu()

    def _find_ffmpeg(self):
        """查找 FFmpeg 可执行文件"""
        possible_paths = [
            Path("bin/ffmpeg.exe"),  # 相对路径
            Path(__file__).parent.parent.parent / "bin/ffmpeg.exe",  # 相对于脚本的路径
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
            if cv2.ocl.haveOpenCL():
                device = cv2.ocl.Device_getDefault()
                if device is not None:
                    vendor = device.vendorName()
                    device_name = device.name()
                    if "Intel" in vendor:
                        print(f"检测到 Intel GPU:")
                        print(f"设备名称: {device_name}")
                        print(f"供应商: {vendor}")
                        print(f"OpenCL 版本: {device.version()}")
                        self.intel_gpu = True
                        
                        # 检查是否为 Arc GPU
                        if "Arc" in device_name:
                            print("检测到 Intel Arc GPU，启用特殊优化")
                            self.intel_arc = True
                        
                        self.use_gpu = True
                        cv2.ocl.setUseOpenCL(True)
                        cv2.setUseOptimized(True)
                        return
            print("未检测到 Intel GPU 支持，将使用 CPU 处理")
        except Exception as e:
            print(f"GPU 检测出错: {str(e)}")
            self.use_gpu = False

    def get_video_capture(self, video_path):
        """获取适合的视频捕获对象"""
        try:
            # 针对 Intel Arc GPU 使用 D3D11 加速
            if platform.system() == 'Windows' and self.use_gpu:
                cap = cv2.VideoCapture(video_path, cv2.CAP_MSMF)  # 使用 Media Foundation
                if self.intel_arc:
                    # 设置硬件加速
                    cap.set(cv2.CAP_PROP_HW_ACCELERATION, cv2.VIDEO_ACCELERATION_D3D11)
                    cap.set(cv2.CAP_PROP_HW_DEVICE, 0)
                    # 尝试启用 Intel GPU 解码
                    cap.set(cv2.CAP_PROP_HW_ACCELERATION_USE_OPENCL, 1)
                return cap
            return cv2.VideoCapture(video_path, cv2.CAP_ANY)
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