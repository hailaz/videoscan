import sys
import os
from PyQt5.QtWidgets import (QApplication, QMainWindow, QPushButton, QFileDialog,
                           QLabel, QVBoxLayout, QHBoxLayout, QWidget, QLineEdit,
                           QSpinBox, QDoubleSpinBox, QCheckBox, QGroupBox, 
                           QProgressBar, QMessageBox, QTextEdit, QFrame)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from gui.detection_thread import DetectionThread
from core.hardware import HardwareAccelerator
from core.splitter import VideoSplitter

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('智能视频切割工具')
        self.setGeometry(100, 100, 1000, 700)
        self.hardware = HardwareAccelerator()
        self.splitter = VideoSplitter()
        self.detection_thread = None
        self.segments = []
        self._initialize_ui()
        self._apply_styles()

    def _initialize_ui(self):
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # 添加各个组件
        layout.addWidget(self._create_file_group())
        layout.addWidget(self._create_settings_group())
        layout.addWidget(self._create_actions_group())
        layout.addWidget(self._create_status_group())

    def _create_file_group(self):
        group = QGroupBox("视频文件")
        layout = QHBoxLayout()
        
        self.file_path = QLineEdit()
        self.file_path.setReadOnly(True)
        self.file_path.setPlaceholderText("请选择要处理的视频文件...")
        
        select_file_btn = QPushButton('选择视频文件')
        select_file_btn.setIcon(self.style().standardIcon(QApplication.style().SP_DialogOpenButton))
        select_file_btn.clicked.connect(self.select_file)
        
        layout.addWidget(self.file_path)
        layout.addWidget(select_file_btn)
        group.setLayout(layout)
        return group

    def _create_settings_group(self):
        group = QGroupBox("检测设置")
        layout = QHBoxLayout()
        layout.setSpacing(30)

        # 左侧设置
        left_layout = QVBoxLayout()
        self.threshold_spin = self._create_spin_box(left_layout, "检测阈值:", 1, 100, 25)
        self.min_area_spin = self._create_spin_box(left_layout, "最小检测区域:", 100, 10000, 1000)
        layout.addLayout(left_layout)

        # 中间设置
        middle_layout = QVBoxLayout()
        self.scale_spin = self._create_double_spin_box(middle_layout, "预览窗口比例:", 0.1, 1.0, 0.4, 0.1)
        self.speed_spin = self._create_double_spin_box(middle_layout, "处理速度:", 0.1, 16.0, 2.0, 0.1)
        layout.addLayout(middle_layout)

        # 右侧设置
        right_layout = QVBoxLayout()
        self.use_gpu = QCheckBox("使用GPU加速")
        self.use_gpu.setChecked(self.hardware.has_gpu)
        self.use_gpu.setEnabled(self.hardware.has_gpu)
        right_layout.addWidget(self.use_gpu)
        layout.addLayout(right_layout)

        group.setLayout(layout)
        return group

    def _create_actions_group(self):
        group = QGroupBox("操作")
        layout = QHBoxLayout()
        layout.setSpacing(20)
        
        self.detect_btn = QPushButton('开始检测')
        self.detect_btn.setIcon(self.style().standardIcon(QApplication.style().SP_MediaPlay))
        self.detect_btn.clicked.connect(self.start_detection)
        layout.addWidget(self.detect_btn)

        self.stop_btn = QPushButton('停止')
        self.stop_btn.setIcon(self.style().standardIcon(QApplication.style().SP_MediaStop))
        self.stop_btn.clicked.connect(self.stop_detection)
        self.stop_btn.setEnabled(False)
        layout.addWidget(self.stop_btn)

        self.split_btn = QPushButton('切割视频')
        self.split_btn.setIcon(self.style().standardIcon(QApplication.style().SP_MediaSeekForward))
        self.split_btn.clicked.connect(self.split_video)
        self.split_btn.setEnabled(False)
        layout.addWidget(self.split_btn)
        
        group.setLayout(layout)
        return group

    def _create_status_group(self):
        group = QGroupBox("处理状态")
        layout = QVBoxLayout()
        
        # 检测进度
        layout.addWidget(QLabel("检测进度:"))
        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.progress_bar)

        # 切割进度
        layout.addWidget(QLabel("切割进度:"))
        self.split_progress_bar = QProgressBar()
        self.split_progress_bar.setTextVisible(True)
        self.split_progress_bar.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.split_progress_bar)

        # 分隔线
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        layout.addWidget(line)

        # 日志区域
        layout.addWidget(QLabel("处理日志:"))
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(150)
        layout.addWidget(self.log_text)
        
        group.setLayout(layout)
        return group

    def _create_spin_box(self, layout, label, min_val, max_val, default):
        layout.addWidget(QLabel(label))
        spin = QSpinBox()
        spin.setRange(min_val, max_val)
        spin.setValue(default)
        layout.addWidget(spin)
        return spin

    def _create_double_spin_box(self, layout, label, min_val, max_val, default, step):
        layout.addWidget(QLabel(label))
        spin = QDoubleSpinBox()
        spin.setRange(min_val, max_val)
        spin.setValue(default)
        spin.setSingleStep(step)
        layout.addWidget(spin)
        return spin

    def _apply_styles(self):
        # 设置全局样式
        self.setStyleSheet("""
            QMainWindow { background-color: #f5f5f5; }
            QGroupBox {
                border: 2px solid #cccccc;
                border-radius: 6px;
                margin-top: 1em;
                padding: 15px;
                background-color: white;
                font-weight: bold;
            }
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                padding: 8px 15px;
                border-radius: 4px;
                min-width: 100px;
            }
            QLineEdit {
                padding: 5px;
                border: 2px solid #cccccc;
                border-radius: 4px;
            }
            QProgressBar {
                border: 2px solid #cccccc;
                border-radius: 5px;
                text-align: center;
                height: 25px;
            }
            QProgressBar::chunk {
                background-color: #2196F3;
                border-radius: 3px;
            }
        """)

        # 设置停止按钮特殊样式
        self.stop_btn.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
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

    def log_message(self, message):
        """添加日志消息"""
        self.log_text.append(message)
        self.log_text.verticalScrollBar().setValue(
            self.log_text.verticalScrollBar().maximum()
        )

    def select_file(self):
        """选择视频文件"""
        file_name, _ = QFileDialog.getOpenFileName(
            self, '选择视频文件', '', 
            'Video Files (*.mp4 *.avi *.mkv *.mov);;All Files (*.*)'
        )
        if file_name:
            self.file_path.setText(file_name)
            self.log_message(f'已选择视频文件: {os.path.basename(file_name)}')
            self.detect_btn.setEnabled(True)

    def start_detection(self):
        """开始检测"""
        if not self.file_path.text():
            QMessageBox.warning(self, '警告', '请先选择视频文件！')
            return

        # 更新界面状态
        self.detect_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.split_btn.setEnabled(False)
        self.progress_bar.setValue(0)
        self.split_progress_bar.setValue(0)
        self.log_message("开始检测视频中的动作...")

        # 创建并启动检测线程
        self.detection_thread = DetectionThread(
            self.file_path.text(),
            self.hardware,
            self.scale_spin.value(),
            self.threshold_spin.value(),
            self.min_area_spin.value(),
            self.speed_spin.value()
        )
        self.detection_thread.progress.connect(self.update_detection_progress)
        self.detection_thread.finished.connect(self.detection_finished)
        self.detection_thread.error.connect(self.detection_error)
        self.detection_thread.start()

    def stop_detection(self):
        """停止检测"""
        if self.detection_thread and self.detection_thread.isRunning():
            self.log_message("正在停止检测...")
            self.stop_btn.setEnabled(False)
            self.detection_thread.stop()
            self.detection_thread.quit()
            self.detection_thread.wait()
            self.detect_btn.setEnabled(True)
            self.log_message("检测已停止")

    def update_detection_progress(self, value):
        """更新检测进度"""
        self.progress_bar.setValue(int(value))

    def detection_finished(self, segments):
        """检测完成处理"""
        self.segments = segments
        self.progress_bar.setValue(100)
        self.log_message(f'检测完成！找到 {len(segments)} 个动作片段')
        
        # 显示片段信息
        segments_info, total_duration = self.splitter.get_segment_info(segments)
        for info in segments_info:
            self.log_message(
                f'片段 {info["index"]}: {info["start"]} - {info["end"]} '
                f'(时长: {info["duration"]})'
            )
        
        self.stop_btn.setEnabled(False)
        self.detect_btn.setEnabled(True)
        self.split_btn.setEnabled(True)

    def detection_error(self, error_msg):
        """处理检测错误"""
        QMessageBox.critical(self, '错误', f'检测过程出错：{error_msg}')
        self.log_message(f'错误: {error_msg}')
        self.detect_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.progress_bar.setValue(0)

    def split_video(self):
        """切割视频"""
        if not self.segments:
            QMessageBox.warning(self, '警告', '请先进行动作检测！')
            return

        output_dir = QFileDialog.getExistingDirectory(self, '选择保存目录')
        if output_dir:
            try:
                self.log_message("开始切割视频...")
                self.split_progress_bar.setValue(0)
                self.splitter.set_progress_callback(self.update_split_progress)
                
                output_files = self.splitter.split_video(
                    self.file_path.text(),
                    self.segments,
                    output_dir,
                    self.hardware.ffmpeg_path
                )
                
                if output_files:
                    QMessageBox.information(self, '成功', '视频切割完成！')
                    self.log_message(f"视频切割完成！保存在: {output_dir}")
                else:
                    raise Exception("没有生成任何输出文件")
                    
            except Exception as e:
                error_msg = f'视频切割失败：{str(e)}'
                QMessageBox.critical(self, '错误', error_msg)
                self.log_message(f"错误: {error_msg}")

    def update_split_progress(self, value):
        """更新切割进度"""
        self.split_progress_bar.setValue(int(value))

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())