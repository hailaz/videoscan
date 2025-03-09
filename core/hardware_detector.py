"""硬件资源检测模块"""
import os
import psutil
import cv2
import numpy as np

class HardwareDetector:
    def __init__(self):
        self.cpu_count = psutil.cpu_count(logical=False)  # 物理CPU核心数
        self.total_cpu_count = psutil.cpu_count(logical=True)  # 总CPU线程数
        self.memory = psutil.virtual_memory()
        self.gpu_info = self._detect_gpu()
        
    def _detect_gpu(self):
        """检测GPU信息"""
        gpu_info = {
            'has_gpu': False,
            'intel_gpu': False,
            'intel_arc': False,
            'cuda_available': False,
            'opencl_available': False
        }
        
        # 检测OpenCL支持
        if cv2.ocl.haveOpenCL():
            gpu_info['opencl_available'] = True
            device = cv2.ocl.Device_getDefault()
            if device is not None:
                vendor = device.vendorName()
                device_name = device.name()
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
        
    def get_optimal_workers(self):
        """获取最优的并行工作进程数"""
        # 基础工作进程数为物理CPU核心数
        optimal_workers = self.cpu_count
        
        # 如果有GPU，可以增加工作进程数
        if self.gpu_info['has_gpu']:
            if self.gpu_info['cuda_available']:
                optimal_workers = min(optimal_workers + 2, self.total_cpu_count)
            elif self.gpu_info['intel_gpu']:
                optimal_workers = min(optimal_workers + 1, self.total_cpu_count)
                
        # 考虑系统内存情况
        memory_percent = self.memory.percent
        if memory_percent > 80:  # 内存使用率高时减少工作进程
            optimal_workers = max(1, optimal_workers - 1)
            
        return optimal_workers