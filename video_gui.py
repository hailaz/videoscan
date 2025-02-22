import sys
import os
from PyQt5.QtWidgets import (QApplication, QMainWindow, QPushButton, QFileDialog,
                           QLabel, QVBoxLayout, QHBoxLayout, QWidget, QLineEdit,
                           QSpinBox, QDoubleSpinBox, QCheckBox, QGroupBox, 
                           QProgressBar, QMessageBox, QTextEdit, QFrame)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont, QPalette, QColor
from video_splitter import VideoSplitter

class DetectionThread(QThread):
    # 确保信号定义在类级别
    progress = pyqtSignal(float)
    finished = pyqtSignal(list)
    error = pyqtSignal(str)

    def __init__(self, splitter, video_path):
        super().__init__()
        self.splitter = splitter
        self.video_path = video_path
        self._is_running = True
        # 移动到这里，确保在初始化时设置回调
        if hasattr(self.splitter, 'set_progress_callback'):
            self.splitter.set_progress_callback(self.update_progress)

    def stop(self):
        self._is_running = False
        if hasattr(self.splitter, 'stop_detection'):
            self.splitter.stop_detection()

    def update_progress(self, value):
        if not self._is_running:
            return
        self.progress.emit(value)

    def run(self):
        try:
            self.splitter.detect_motion_points(self.video_path)
            if self._is_running:
                self.finished.emit(self.splitter.motion_segments)
        except Exception as e:
            if self._is_running:
                self.error.emit(str(e))

class VideoSplitterGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('智能视频切割工具')
        self.setGeometry(100, 100, 1000, 700)
        self.splitter = None
        self.detection_thread = None
        self._is_stopping = False
        self.setupUI()
        
        # 设置窗口和控件样式
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f5f5;
            }
            QGroupBox {
                border: 2px solid #cccccc;
                border-radius: 6px;
                margin-top: 1em;
                padding: 15px;
                background-color: white;
                font-weight: bold;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
                color: #333333;
                background-color: white;
            }
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                padding: 8px 15px;
                border-radius: 4px;
                min-width: 100px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:pressed {
                background-color: #0D47A1;
            }
            QPushButton:disabled {
                background-color: #BDBDBD;
            }
            QLineEdit {
                padding: 5px;
                border: 2px solid #cccccc;
                border-radius: 4px;
                background-color: white;
            }
            QLineEdit:focus {
                border-color: #2196F3;
            }
            QLabel {
                color: #333333;
            }
            QProgressBar {
                text-align: center;
                font-weight: bold;
            }
            QSpinBox, QDoubleSpinBox {
                padding: 5px;
                border: 2px solid #cccccc;
                border-radius: 4px;
            }
            QSpinBox:focus, QDoubleSpinBox:focus {
                border-color: #2196F3;
            }
            QCheckBox {
                spacing: 8px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border: 2px solid #cccccc;
                border-radius: 3px;
            }
            QCheckBox::indicator:checked {
                background-color: #2196F3;
                border-color: #2196F3;
            }
            QCheckBox::indicator:hover {
                border-color: #2196F3;
            }
        """)

    def setupUI(self):
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # 文件选择部分
        file_group = QGroupBox("视频文件")
        file_layout = QHBoxLayout()
        self.file_path = QLineEdit()
        self.file_path.setReadOnly(True)
        self.file_path.setPlaceholderText("请选择要处理的视频文件...")
        select_file_btn = QPushButton('选择视频文件')
        select_file_btn.setIcon(self.style().standardIcon(QApplication.style().SP_DialogOpenButton))
        select_file_btn.clicked.connect(self.select_file)
        file_layout.addWidget(self.file_path)
        file_layout.addWidget(select_file_btn)
        file_group.setLayout(file_layout)
        layout.addWidget(file_group)

        # 设置部分
        settings_group = QGroupBox("检测设置")
        settings_layout = QHBoxLayout()
        settings_layout.setSpacing(30)

        # 左侧设置
        left_settings = QVBoxLayout()
        self.threshold_spin = self.createSettingItem(left_settings, "检测阈值:", QSpinBox(), 1, 100, 25)
        self.min_area_spin = self.createSettingItem(left_settings, "最小检测区域:", QSpinBox(), 100, 10000, 1000)
        settings_layout.addLayout(left_settings)

        # 中间设置
        middle_settings = QVBoxLayout()
        self.scale_spin = self.createSettingItem(middle_settings, "预览窗口比例:", QDoubleSpinBox(), 0.1, 1.0, 0.4, 0.1, double=True)
        self.speed_spin = self.createSettingItem(middle_settings, "处理速度:", QDoubleSpinBox(), 0.1, 16.0, 2.0, 0.1, double=True)
        settings_layout.addLayout(middle_settings)

        # 右侧设置
        right_settings = QVBoxLayout()
        self.use_gpu = QCheckBox("使用GPU加速")
        self.use_gpu.setChecked(True)
        right_settings.addWidget(self.use_gpu)

        self.exclude_timestamp = QCheckBox("排除时间戳区域")
        self.exclude_timestamp.setChecked(True)
        right_settings.addWidget(self.exclude_timestamp)
        settings_layout.addLayout(right_settings)

        settings_group.setLayout(settings_layout)
        layout.addWidget(settings_group)

        # 操作按钮
        actions_group = QGroupBox("操作")
        actions_layout = QHBoxLayout()
        actions_layout.setSpacing(20)
        
        self.detect_btn = QPushButton('开始检测')
        self.detect_btn.setIcon(self.style().standardIcon(QApplication.style().SP_MediaPlay))
        self.detect_btn.clicked.connect(self.start_detection)
        actions_layout.addWidget(self.detect_btn)

        self.stop_btn = QPushButton('停止')
        self.stop_btn.setIcon(self.style().standardIcon(QApplication.style().SP_MediaStop))
        self.stop_btn.clicked.connect(self.stop_detection)
        self.stop_btn.setEnabled(False)
        self.stop_btn.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                border: none;
                padding: 8px 15px;
                border-radius: 4px;
                min-width: 100px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #d32f2f;
            }
            QPushButton:pressed {
                background-color: #b71c1c;
            }
            QPushButton:disabled {
                background-color: #BDBDBD;
            }
        """)
        actions_layout.addWidget(self.stop_btn)

        self.split_btn = QPushButton('切割视频')
        self.split_btn.setIcon(self.style().standardIcon(QApplication.style().SP_MediaSeekForward))
        self.split_btn.clicked.connect(self.split_video)
        self.split_btn.setEnabled(False)
        actions_layout.addWidget(self.split_btn)
        
        actions_group.setLayout(actions_layout)
        layout.addWidget(actions_group)

        # 状态显示区域
        status_group = QGroupBox("处理状态")
        status_layout = QVBoxLayout()
        
        # 检测进度条标签和进度条
        detect_progress_label = QLabel("检测进度:")
        detect_progress_label.setStyleSheet("font-weight: bold;")
        status_layout.addWidget(detect_progress_label)
        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setAlignment(Qt.AlignCenter)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #cccccc;
                border-radius: 5px;
                text-align: center;
                height: 25px;
                background-color: #f0f0f0;
                margin: 0 0 10px 0;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #2196F3, stop:1 #64B5F6);
                border-radius: 3px;
            }
        """)
        status_layout.addWidget(self.progress_bar)

        # 切割进度条标签和进度条
        split_progress_label = QLabel("切割进度:")
        split_progress_label.setStyleSheet("font-weight: bold;")
        status_layout.addWidget(split_progress_label)
        self.split_progress_bar = QProgressBar()
        self.split_progress_bar.setTextVisible(True)
        self.split_progress_bar.setAlignment(Qt.AlignCenter)
        self.split_progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #cccccc;
                border-radius: 5px;
                text-align: center;
                height: 25px;
                background-color: #f0f0f0;
                margin: 0 0 10px 0;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #4CAF50, stop:1 #81C784);
                border-radius: 3px;
            }
        """)
        status_layout.addWidget(self.split_progress_bar)

        # 添加分隔线
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        line.setStyleSheet("background-color: #cccccc;")
        status_layout.addWidget(line)

        # 状态文本显示区
        status_label = QLabel("处理日志:")
        status_label.setStyleSheet("font-weight: bold;")
        status_layout.addWidget(status_label)
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(150)
        self.log_text.setStyleSheet("""
            QTextEdit {
                border: 2px solid #cccccc;
                border-radius: 5px;
                background-color: #ffffff;
                padding: 5px;
                font-family: Consolas, Monaco, monospace;
                font-size: 9pt;
            }
        """)
        status_layout.addWidget(self.log_text)
        
        status_group.setLayout(status_layout)
        layout.addWidget(status_group)

        # 设置组件之间的间距
        layout.setSpacing(10)
        status_layout.setSpacing(5)

    def createSettingItem(self, layout, label_text, spin_widget, min_val, max_val, default_val, step=1, double=False):
        label = QLabel(label_text)
        if double:
            spin_widget = QDoubleSpinBox()
        else:
            spin_widget = QSpinBox()
        spin_widget.setRange(min_val, max_val)
        spin_widget.setValue(default_val)
        if double:
            spin_widget.setSingleStep(step)
        layout.addWidget(label)
        layout.addWidget(spin_widget)
        return spin_widget

    def log_message(self, message):
        """添加日志消息到状态显示区"""
        self.log_text.append(message)
        self.log_text.verticalScrollBar().setValue(
            self.log_text.verticalScrollBar().maximum()
        )

    def select_file(self):
        file_name, _ = QFileDialog.getOpenFileName(
            self, '选择视频文件', '', 
            'Video Files (*.mp4 *.avi *.mkv *.mov);;All Files (*.*)'
        )
        if file_name:
            self.file_path.setText(file_name)
            self.log_message(f'已选择视频文件: {os.path.basename(file_name)}')
            self.detect_btn.setEnabled(True)

    def start_detection(self):
        if not self.file_path.text():
            QMessageBox.warning(self, '警告', '请先选择视频文件！')
            return

        # 创建VideoSplitter实例
        self.splitter = VideoSplitter(
            threshold=self.threshold_spin.value(),
            min_area=self.min_area_spin.value(),
            window_scale=self.scale_spin.value(),
            use_gpu=self.use_gpu.isChecked(),
            playback_speed=self.speed_spin.value()
        )

        # 更新界面状态
        self.detect_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.split_btn.setEnabled(False)
        self._is_stopping = False
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.split_progress_bar.setRange(0, 100)
        self.split_progress_bar.setValue(0)
        self.log_message("开始检测视频中的动作...")

        # 创建并启动检测线程
        self.detection_thread = DetectionThread(self.splitter, self.file_path.text())
        self.detection_thread.progress.connect(self.update_progress)
        self.detection_thread.finished.connect(self.detection_finished)
        self.detection_thread.error.connect(self.detection_error)
        self.detection_thread.start()

    def stop_detection(self):
        if self.detection_thread and self.detection_thread.isRunning():
            self._is_stopping = True
            self.log_message("正在停止检测...")
            self.stop_btn.setEnabled(False)
            self.detection_thread.stop()
            self.detection_thread.quit()
            self.detection_thread.wait()
            self.detect_btn.setEnabled(True)
            self.log_message("检测已停止")

    def detection_finished(self, segments):
        if not self._is_stopping:
            self.progress_bar.setValue(100)
            self.log_message(f'检测完成！找到 {len(segments)} 个动作片段')
            for i, segment in enumerate(segments, 1):
                start_time = self.format_time(segment['start'])
                end_time = self.format_time(segment['end'])
                duration = self.format_time(segment['end'] - segment['start'])
                self.log_message(f'片段 {i}: {start_time} - {end_time} (时长: {duration})')
            self.split_btn.setEnabled(True)
        
        self.stop_btn.setEnabled(False)
        self.detect_btn.setEnabled(True)
        self._is_stopping = False

    def detection_error(self, error_msg):
        if not self._is_stopping:
            QMessageBox.critical(self, '错误', f'检测过程出错：{error_msg}')
            self.log_message(f'错误: {error_msg}')
        self.detect_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self._is_stopping = False

    def format_time(self, seconds):
        """将秒数转换为时:分:秒格式"""
        m, s = divmod(seconds, 60)
        h, m = divmod(m, 60)
        return f"{int(h):02d}:{int(m):02d}:{s:05.2f}"

    def split_video(self):
        if not self.splitter or not self.splitter.motion_segments:
            QMessageBox.warning(self, '警告', '请先进行动作检测！')
            return

        output_dir = QFileDialog.getExistingDirectory(self, '选择保存目录')
        if output_dir:
            try:
                self.log_message("开始切割视频...")
                self.split_progress_bar.setRange(0, 100)
                self.split_progress_bar.setValue(0)
                self.splitter.set_progress_callback(self.update_split_progress)
                # 修复这里的方法调用
                self.splitter.split_video(self.file_path.text(), output_dir)
                QMessageBox.information(self, '成功', '视频切割完成！')
                self.log_message(f"视频切割完成！保存在: {output_dir}")
            except Exception as e:
                error_msg = f'视频切割失败：{str(e)}'
                QMessageBox.critical(self, '错误', error_msg)
                self.log_message(f"错误: {error_msg}")
            finally:
                # 恢复进度回调为检测进度
                self.splitter.set_progress_callback(self.detection_thread.update_progress if self.detection_thread else None)

    def update_split_progress(self, value):
        """更新切割进度条显示"""
        self.split_progress_bar.setValue(int(value))
        self.split_progress_bar.setFormat('切割进度: %.1f%%' % value)
        # 根据进度更新进度条颜色
        if value < 30:
            color = "#FFA726"  # 橙色
        elif value < 60:
            color = "#66BB6A"  # 浅绿色
        elif value < 90:
            color = "#43A047"  # 深绿色
        else:
            color = "#2E7D32"  # 更深的绿色
            
        self.split_progress_bar.setStyleSheet(f"""
            QProgressBar {{
                border: 2px solid #cccccc;
                border-radius: 5px;
                text-align: center;
                height: 25px;
                background-color: #f0f0f0;
                margin: 0 0 10px 0;
            }}
            QProgressBar::chunk {{
                background: {color};
                border-radius: 3px;
            }}
        """)

def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')  # 使用Fusion风格获得更现代的外观
    window = VideoSplitterGUI()
    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()