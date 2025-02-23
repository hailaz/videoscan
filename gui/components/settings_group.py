"""设置组件"""
from PyQt5.QtWidgets import (QGroupBox, QHBoxLayout, QVBoxLayout, 
                           QLabel, QSpinBox, QDoubleSpinBox, QCheckBox)

class SettingsGroup(QGroupBox):
    def __init__(self, hardware, parent=None):
        super().__init__("检测设置", parent)
        self.hardware = hardware
        self._init_ui()

    def _init_ui(self):
        layout = QHBoxLayout()
        layout.setSpacing(30)

        # 左侧设置
        left_layout = QVBoxLayout()
        self.threshold_spin = self._create_spin_box(
            left_layout, "检测阈值:", 1, 100, 25)
        self.min_area_spin = self._create_spin_box(
            left_layout, "最小检测区域:", 100, 10000, 1000)
        layout.addLayout(left_layout)

        # 中间设置
        middle_layout = QVBoxLayout()
        self.scale_spin = self._create_double_spin_box(
            middle_layout, "预览窗口比例:", 0.1, 1.0, 0.4, 0.1)
        self.speed_spin = self._create_double_spin_box(
            middle_layout, "处理速度:", 0.1, 16.0, 2.0, 0.1)
        layout.addLayout(middle_layout)

        # 右侧设置
        right_layout = QVBoxLayout()
        self.use_gpu = QCheckBox("使用GPU加速")
        self.use_gpu.setChecked(self.hardware.has_gpu)
        self.use_gpu.setEnabled(self.hardware.has_gpu)
        right_layout.addWidget(self.use_gpu)
        layout.addLayout(right_layout)

        self.setLayout(layout)

    def _create_spin_box(self, layout, label, min_val, max_val, default):
        """创建整数输入框"""
        layout.addWidget(QLabel(label))
        spin = QSpinBox()
        spin.setRange(min_val, max_val)
        spin.setValue(default)
        layout.addWidget(spin)
        return spin

    def _create_double_spin_box(self, layout, label, min_val, max_val, default, step):
        """创建浮点数输入框"""
        layout.addWidget(QLabel(label))
        spin = QDoubleSpinBox()
        spin.setRange(min_val, max_val)
        spin.setValue(default)
        spin.setSingleStep(step)
        layout.addWidget(spin)
        return spin

    def get_settings(self):
        """获取当前设置值"""
        return {
            'threshold': self.threshold_spin.value(),
            'min_area': self.min_area_spin.value(),
            'scale': self.scale_spin.value(),
            'speed': self.speed_spin.value(),
            'use_gpu': self.use_gpu.isChecked()
        }