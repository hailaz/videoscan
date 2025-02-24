"""设置组件"""
from PyQt5.QtWidgets import (QGroupBox, QGridLayout, QHBoxLayout, QLabel, 
                           QSpinBox, QDoubleSpinBox, QCheckBox, QWidget)
from PyQt5.QtCore import Qt
from core.config_manager import ConfigManager

class WheelSpinBox(QSpinBox):
    """支持滚轮操作的整数输入框"""
    def wheelEvent(self, event):
        if self.hasFocus():
            super().wheelEvent(event)
        else:
            event.ignore()

class WheelDoubleSpinBox(QDoubleSpinBox):
    """支持滚轮操作的浮点数输入框"""
    def wheelEvent(self, event):
        if self.hasFocus():
            super().wheelEvent(event)
        else:
            event.ignore()

class SettingsGroup(QGroupBox):
    def __init__(self, hardware, parent=None):
        super().__init__("检测设置", parent)
        self.hardware = hardware
        self.parent = parent
        self.config_manager = ConfigManager()
        self._init_ui()

    def _init_ui(self):
        main_layout = QHBoxLayout()
        main_layout.setSpacing(12)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # 参数控件布局
        self.threshold_spin = self._create_spin_box(
            main_layout, "检测阈值", 1, 100, 25)
        
        self.min_area_spin = self._create_spin_box(
            main_layout, "最小区域", 100, 10000, 1000)
            
        self.scale_spin = self._create_double_spin_box(
            main_layout, "预览比例", 0.1, 1.0, 
            self.config_manager.get_window_scale(), 0.1)
            
        self.speed_spin = self._create_double_spin_box(
            main_layout, "处理速度", 0.1, 16.0, 
            self.config_manager.get_playback_speed(), 0.1)

        # GPU选项
        self.use_gpu = QCheckBox("使用GPU加速")
        self.use_gpu.setChecked(self.hardware.has_gpu)
        self.use_gpu.setEnabled(self.hardware.has_gpu)
        main_layout.addWidget(self.use_gpu)

        main_layout.addStretch()
        self.setLayout(main_layout)
        
        # 连接信号
        if hasattr(self.parent, 'video_processor'):
            self.scale_spin.valueChanged.connect(
                lambda v: setattr(self.parent.video_processor, 'window_scale', v))
            self.speed_spin.valueChanged.connect(
                lambda v: setattr(self.parent.video_processor, 'playback_speed', v))

    def _create_spin_box(self, layout, label, min_val, max_val, default):
        """创建整数输入框"""
        container = QWidget()
        container_layout = QHBoxLayout()
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(1)  # 减小标签和数值之间的间距
        
        label_widget = QLabel(f"{label}:")  # 添加冒号
        label_widget.setFixedWidth(70)  # 增加标签宽度确保文本完整显示
        spin = WheelSpinBox()
        spin.setRange(min_val, max_val)
        spin.setValue(default)
        spin.setFixedWidth(50)  # 减小数值输入框宽度
        
        container_layout.addWidget(label_widget)
        container_layout.addWidget(spin)
        container.setLayout(container_layout)
        layout.addWidget(container)
        return spin

    def _create_double_spin_box(self, layout, label, min_val, max_val, default, step):
        """创建浮点数输入框"""
        container = QWidget()
        container_layout = QHBoxLayout()
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(1)  # 减小标签和数值之间的间距
        
        label_widget = QLabel(f"{label}:")  # 添加冒号
        label_widget.setFixedWidth(70)  # 增加标签宽度确保文本完整显示
        spin = WheelDoubleSpinBox()
        spin.setRange(min_val, max_val)
        spin.setValue(default)
        spin.setSingleStep(step)
        spin.setFixedWidth(50)  # 减小数值输入框宽度
        
        container_layout.addWidget(label_widget)
        container_layout.addWidget(spin)
        container.setLayout(container_layout)
        layout.addWidget(container)
        return spin

    def get_settings(self):
        """获取当前设置值"""
        settings = {
            'threshold': self.threshold_spin.value(),
            'min_area': self.min_area_spin.value(),
            'scale': self.scale_spin.value(),
            'speed': self.speed_spin.value(),
            'use_gpu': self.use_gpu.isChecked()
        }
        return settings