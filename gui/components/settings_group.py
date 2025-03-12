"""设置组件"""
from PyQt5.QtWidgets import (QGroupBox, QGridLayout, QHBoxLayout, QVBoxLayout, QLabel, 
                           QSpinBox, QDoubleSpinBox, QCheckBox, QWidget, QComboBox,
                           QPushButton, QInputDialog)
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
        main_layout = QVBoxLayout()
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # 创建三行布局
        top_row = QHBoxLayout()
        middle_row = QHBoxLayout()
        bottom_row = QHBoxLayout()
        
        # 第一行：基本检测参数
        params = self.config_manager.get_detection_params()
        self.threshold_spin = self._create_spin_box(
            top_row, "检测阈值", 1, 100, params.get('threshold', 25))
        
        self.min_area_spin = self._create_spin_box(
            top_row, "最小区域", 100, 10000, params.get('min_area', 1000))
            
        self.static_time_spin = self._create_double_spin_box(
            top_row, "静止时间", 0.1, 5.0, params.get('static_time', 1.0), 0.1)
            
        top_row.addStretch()
        
        # 第二行：显示和控制参数
        self.scale_spin = self._create_double_spin_box(
            middle_row, "预览比例", 0.1, 1.0, 
            self.config_manager.get_window_scale(), 0.1)
            
        self.speed_spin = self._create_double_spin_box(
            middle_row, "处理速度", 0.1, 16.0, 
            self.config_manager.get_playback_speed(), 0.1)
        self.speed_spin.setDecimals(1)
            
        self.concurrent_videos_spin = self._create_spin_box(
            middle_row, "并行处理", 1, 10,
            self.config_manager.get_max_concurrent_videos())
            
        middle_row.addStretch()
        
        # 第三行：预设和复选框
        preset_layout = QHBoxLayout()
        preset_layout.setSpacing(5)
        
        preset_label = QLabel("参数预设:")
        preset_label.setFixedWidth(70)
        self.preset_combo = QComboBox()
        self.preset_combo.setFixedWidth(100)
        self._load_presets()
        
        save_preset_btn = QPushButton("保存预设")
        save_preset_btn.setFixedWidth(80)
        save_preset_btn.clicked.connect(self._save_current_preset)
        
        del_preset_btn = QPushButton("删除预设")
        del_preset_btn.setFixedWidth(80)
        del_preset_btn.clicked.connect(self._delete_current_preset)
        
        preset_layout.addWidget(preset_label)
        preset_layout.addWidget(self.preset_combo)
        preset_layout.addWidget(save_preset_btn)
        preset_layout.addWidget(del_preset_btn)
        
        # 复选框组
        checkbox_layout = QHBoxLayout()
        checkbox_layout.setSpacing(20)
        
        self.use_gpu = QCheckBox("GPU加速")
        self.use_gpu.setChecked(self.hardware.has_gpu)
        self.use_gpu.setEnabled(self.hardware.has_gpu)
        checkbox_layout.addWidget(self.use_gpu)

        self.auto_split = QCheckBox("自动切割")
        self.auto_split.setChecked(self.config_manager.get_auto_split())
        checkbox_layout.addWidget(self.auto_split)
        
        self.show_preview = QCheckBox("显示预览")
        self.show_preview.setChecked(self.config_manager.get_show_preview())
        checkbox_layout.addWidget(self.show_preview)
        
        bottom_row.addLayout(preset_layout)
        bottom_row.addSpacing(20)
        bottom_row.addLayout(checkbox_layout)
        bottom_row.addStretch()
        
        # 添加到主布局
        main_layout.addLayout(top_row)
        main_layout.addLayout(middle_row)
        main_layout.addLayout(bottom_row)
        
        self.setLayout(main_layout)
        
        # 连接信号
        self._connect_signals()

    def _connect_signals(self):
        """连接信号到槽"""
        if hasattr(self.parent, 'video_processor'):
            self.scale_spin.valueChanged.connect(
                lambda v: setattr(self.parent.video_processor, 'window_scale', v))
            self.speed_spin.valueChanged.connect(
                lambda v: setattr(self.parent.video_processor, 'playback_speed', v))
            
        self.auto_split.stateChanged.connect(
            lambda state: self.config_manager.set_auto_split(bool(state)))
        self.concurrent_videos_spin.valueChanged.connect(
            lambda v: self.config_manager.set_max_concurrent_videos(v))
        self.show_preview.stateChanged.connect(
            lambda state: self.config_manager.set_show_preview(bool(state)))
            
        self.preset_combo.currentTextChanged.connect(self._load_preset)
        
        # 参数变更时保存
        self.threshold_spin.valueChanged.connect(self._save_current_params)
        self.min_area_spin.valueChanged.connect(self._save_current_params)
        self.static_time_spin.valueChanged.connect(self._save_current_params)

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

    def _load_presets(self):
        """加载参数预设列表"""
        self.preset_combo.clear()
        presets = self.config_manager.get_detection_presets()
        self.preset_combo.addItems(presets.keys())

    def _load_preset(self, preset_name):
        """加载指定的参数预设"""
        if not preset_name:
            return
            
        presets = self.config_manager.get_detection_presets()
        if preset_name in presets:
            params = presets[preset_name]
            self.threshold_spin.setValue(params['threshold'])
            self.min_area_spin.setValue(params['min_area'])
            self.static_time_spin.setValue(params['static_time'])

    def _save_current_preset(self):
        """保存当前参数为新预设"""
        name, ok = QInputDialog.getText(self, '保存预设', '请输入预设名称:')
        if ok and name:
            params = {
                'threshold': self.threshold_spin.value(),
                'min_area': self.min_area_spin.value(),
                'static_time': self.static_time_spin.value()
            }
            self.config_manager.add_detection_preset(name, params)
            self._load_presets()
            self.preset_combo.setCurrentText(name)

    def _delete_current_preset(self):
        """删除当前选中的预设"""
        preset_name = self.preset_combo.currentText()
        if preset_name and preset_name != '默认':
            self.config_manager.remove_detection_preset(preset_name)
            self._load_presets()

    def _save_current_params(self):
        """保存当前参数设置"""
        params = {
            'threshold': self.threshold_spin.value(),
            'min_area': self.min_area_spin.value(),
            'static_time': self.static_time_spin.value()
        }
        self.config_manager.set_detection_params(params)

    def get_settings(self):
        """获取当前设置值"""
        return {
            'threshold': self.threshold_spin.value(),
            'min_area': self.min_area_spin.value(),
            'static_time': self.static_time_spin.value(),
            'scale': self.scale_spin.value(),
            'speed': self.speed_spin.value(),
            'use_gpu': self.use_gpu.isChecked(),
            'auto_split': self.auto_split.isChecked(),
            'max_concurrent_videos': self.concurrent_videos_spin.value(),
            'show_preview': self.show_preview.isChecked()
        }