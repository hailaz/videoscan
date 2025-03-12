"""进度管理模块"""
from dataclasses import dataclass
from typing import Dict, Optional, Callable
from enum import Enum

class TaskStatus(Enum):
    WAITING = "等待处理"
    PROCESSING = "处理中"
    COMPLETED = "已完成"
    FAILED = "失败"
    STOPPED = "已停止"

@dataclass
class TaskProgress:
    """任务进度信息"""
    status: TaskStatus
    progress: float = 0.0
    message: Optional[str] = None

class ProgressManager:
    """进度管理器"""
    def __init__(self):
        self.tasks: Dict[str, TaskProgress] = {}
        self._progress_callback = None
        self._status_callback = None
        self.total_tasks = 0
        self.completed_tasks = 0
        
    def set_callbacks(self, progress_callback: Callable, status_callback: Callable):
        """设置回调函数
        
        Args:
            progress_callback: 进度更新回调
            status_callback: 状态更新回调
        """
        self._progress_callback = progress_callback
        self._status_callback = status_callback
        
    def add_task(self, task_id: str):
        """添加任务
        
        Args:
            task_id: 任务ID
        """
        self.tasks[task_id] = TaskProgress(TaskStatus.WAITING)
        self.total_tasks += 1
        self._notify_status()
        
    def remove_task(self, task_id: str):
        """移除任务
        
        Args:
            task_id: 任务ID
        """
        if task_id in self.tasks:
            if self.tasks[task_id].status == TaskStatus.COMPLETED:
                self.completed_tasks -= 1
            del self.tasks[task_id]
            self.total_tasks -= 1
            self._notify_status()
            
    def update_progress(self, task_id: str, progress: float, 
                       status: Optional[TaskStatus] = None,
                       message: Optional[str] = None):
        """更新任务进度
        
        Args:
            task_id: 任务ID
            progress: 进度值(0-100)
            status: 任务状态
            message: 状态消息
        """
        if task_id not in self.tasks:
            return
            
        task = self.tasks[task_id]
        
        # 更新进度
        task.progress = progress
        
        # 更新状态
        if status is not None:
            old_status = task.status
            task.status = status
            
            # 更新完成任务计数
            if old_status != TaskStatus.COMPLETED and status == TaskStatus.COMPLETED:
                self.completed_tasks += 1
            elif old_status == TaskStatus.COMPLETED and status != TaskStatus.COMPLETED:
                self.completed_tasks -= 1
                
        # 更新消息
        if message is not None:
            task.message = message
            
        self._notify_progress(task_id)
        self._notify_status()
        
    def get_task_progress(self, task_id: str) -> Optional[TaskProgress]:
        """获取任务进度
        
        Args:
            task_id: 任务ID
            
        Returns:
            TaskProgress: 任务进度信息
        """
        return self.tasks.get(task_id)
        
    def get_overall_progress(self) -> float:
        """获取总体进度
        
        Returns:
            float: 总体进度(0-100)
        """
        if not self.tasks:
            return 0.0
            
        total_progress = sum(task.progress for task in self.tasks.values())
        return total_progress / len(self.tasks)
        
    def get_status_counts(self) -> Dict[TaskStatus, int]:
        """获取各状态的任务数量
        
        Returns:
            Dict[TaskStatus, int]: 状态计数字典
        """
        counts = {status: 0 for status in TaskStatus}
        for task in self.tasks.values():
            counts[task.status] += 1
        return counts
        
    def _notify_progress(self, task_id: str):
        """通知进度更新"""
        if self._progress_callback is not None:
            task = self.tasks[task_id]
            status_text = task.message or task.status.value
            self._progress_callback(task_id, status_text, task.progress)
            
    def _notify_status(self):
        """通知状态更新"""
        if self._status_callback is not None:
            counts = self.get_status_counts()
            progress = self.get_overall_progress()
            self._status_callback(counts, progress, self.completed_tasks, self.total_tasks)
            
    def clear(self):
        """清除所有任务"""
        self.tasks.clear()
        self.total_tasks = 0
        self.completed_tasks = 0
        self._notify_status()