"""播放控制组件"""
from PyQt5.QtWidgets import (QGroupBox, QHBoxLayout, QPushButton, QSlider,
                           QStyle, QLabel)
from PyQt5.QtCore import Qt

class PlaybackGroup(QGroupBox):
    def __init__(self, parent=None):
        super().__init__("播放控制", parent)
        self.parent = parent
        self.is_playing = False
        self._init_ui()
        
    def _init_ui(self):
        """初始化UI"""
        layout = QHBoxLayout()
        layout.setSpacing(10)
        
        # 创建控制按钮
        self.prev_frame_btn = QPushButton()
        self.prev_frame_btn.setIcon(self.style().standardIcon(QStyle.SP_MediaSkipBackward))
        self.prev_frame_btn.setToolTip("上一帧")
        self.prev_frame_btn.clicked.connect(self._prev_frame)
        
        self.play_btn = QPushButton()
        self.play_btn.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
        self.play_btn.setToolTip("播放/暂停")
        self.play_btn.clicked.connect(self._toggle_playback)
        
        self.next_frame_btn = QPushButton()
        self.next_frame_btn.setIcon(self.style().standardIcon(QStyle.SP_MediaSkipForward))
        self.next_frame_btn.setToolTip("下一帧")
        self.next_frame_btn.clicked.connect(self._next_frame)
        
        # 创建进度条
        self.progress_slider = QSlider(Qt.Horizontal)
        self.progress_slider.setRange(0, 100)
        self.progress_slider.setValue(0)
        self.progress_slider.setTracking(False)  # 只在释放时更新值
        self.progress_slider.sliderReleased.connect(self._seek_position)
        
        # 创建时间标签
        self.time_label = QLabel("00:00:00 / 00:00:00")
        self.time_label.setMinimumWidth(150)
        self.time_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        
        # 添加到布局
        layout.addWidget(self.prev_frame_btn)
        layout.addWidget(self.play_btn)
        layout.addWidget(self.next_frame_btn)
        layout.addWidget(self.progress_slider)
        layout.addWidget(self.time_label)
        
        self.setLayout(layout)
        
        # 初始状态为禁用
        self.setEnabled(False)
        
    def _toggle_playback(self):
        """切换播放/暂停状态"""
        self.is_playing = not self.is_playing
        icon = QStyle.SP_MediaPause if self.is_playing else QStyle.SP_MediaPlay
        self.play_btn.setIcon(self.style().standardIcon(icon))
        
        if hasattr(self.parent, 'video_processor'):
            self.parent.video_processor.set_playing(self.is_playing)
    
    def _prev_frame(self):
        """显示上一帧"""
        if hasattr(self.parent, 'video_processor'):
            self.parent.video_processor.prev_frame()
    
    def _next_frame(self):
        """显示下一帧"""
        if hasattr(self.parent, 'video_processor'):
            self.parent.video_processor.next_frame()
    
    def _seek_position(self):
        """跳转到指定位置"""
        if hasattr(self.parent, 'video_processor'):
            position = self.progress_slider.value() / 100.0
            self.parent.video_processor.seek_position(position)
            
    def update_time(self, current_time, total_time):
        """更新时间显示
        
        Args:
            current_time: 当前时间(秒)
            total_time: 总时长(秒)
        """
        time_text = f"{self._format_time(current_time)} / {self._format_time(total_time)}"
        self.time_label.setText(time_text)
        
        # 更新进度条，避免循环更新
        if not self.progress_slider.isSliderDown():
            progress = (current_time / total_time * 100) if total_time > 0 else 0
            self.progress_slider.setValue(int(progress))
            
    def _format_time(self, seconds):
        """格式化时间
        
        Args:
            seconds: 秒数
            
        Returns:
            str: HH:MM:SS 格式的时间字符串
        """
        if seconds is None or seconds == 0:
            return "00:00:00"
            
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"