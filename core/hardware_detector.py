"""硬件资源检测模块"""
import os
import psutil
import cv2
import numpy as np
import platform
import subprocess
import re

class HardwareDetector:
    def __init__(self):
        self.cpu_count = psutil.cpu_count(logical=False)  # 物理CPU核心数
        self.total_cpu_count = psutil.cpu_count(logical=True)  # 总CPU线程数
        self.memory = psutil.virtual_memory()
        self.gpu_info = self._detect_gpu()
        
    def _detect_windows_gpu(self):
        """使用Windows特定方法检测GPU"""
        try:
            import wmi
            w = wmi.WMI()
            gpu_info = w.Win32_VideoController()[0]
            
            # 获取显存信息
            total_memory = 0
            try:
                # 对于共享显存，我们获取当前可用的显存总量
                total_memory = int(gpu_info.AdapterRAM if gpu_info.AdapterRAM is not None else 0)
                if total_memory == 0:
                    # 使用VideoMemoryType判断是否为共享内存
                    # 3表示共享系统内存
                    if getattr(gpu_info, 'VideoMemoryType', None) == 3:
                        # 如果是共享内存，使用系统总内存的一半作为估计值
                        total_memory = psutil.virtual_memory().total // 2
            except:
                pass
                
            return {
                'name': gpu_info.Name,
                'driver_version': gpu_info.DriverVersion,
                'memory': total_memory,
                'shared_memory': getattr(gpu_info, 'VideoMemoryType', None) == 3
            }
        except Exception as e:
            print(f"WMI GPU检测失败: {str(e)}")
            return None

    def _detect_gpu(self):
        """检测GPU信息"""
        gpu_info = {
            'has_gpu': False,
            'intel_gpu': False,
            'intel_arc': False,
            'cuda_available': False,
            'opencl_available': False,
            'gpu_name': '',
            'driver_version': '',
            'gpu_memory': 0,
            'shared_memory': False
        }
        
        # Windows特定的GPU检测
        if platform.system() == 'Windows':
            win_gpu = self._detect_windows_gpu()
            if win_gpu:
                gpu_info['has_gpu'] = True
                gpu_info['gpu_name'] = win_gpu['name']
                gpu_info['driver_version'] = win_gpu['driver_version']
                gpu_info['gpu_memory'] = win_gpu['memory']
                gpu_info['shared_memory'] = win_gpu['shared_memory']
                
                if 'Intel' in win_gpu['name']:
                    gpu_info['intel_gpu'] = True
                    if 'Arc' in win_gpu['name']:
                        gpu_info['intel_arc'] = True
        
        # 检测OpenCL支持
        if cv2.ocl.haveOpenCL():
            gpu_info['opencl_available'] = True
            cv2.ocl.setUseOpenCL(True)
            device = cv2.ocl.Device_getDefault()
            if device is not None:
                vendor = device.vendorName()
                device_name = device.name()
                if not gpu_info['gpu_name']:
                    gpu_info['gpu_name'] = device_name
                if "Intel" in vendor:
                    gpu_info['has_gpu'] = True
                    gpu_info['intel_gpu'] = True
                    if "Arc" in device_name:
                        gpu_info['intel_arc'] = True
                        
        # 检测CUDA支持
        try:
            count = cv2.cuda.getCudaEnabledDeviceCount()
            if count > 0:
                gpu_info['has_gpu'] = True
                gpu_info['cuda_available'] = True
        except:
            pass
            
        return gpu_info
        