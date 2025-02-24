"""配置管理模块"""
import json
import os
from pathlib import Path

class ConfigManager:
    """配置管理类"""
    def __init__(self):
        self.config_dir = Path('.') / 'config'  # 改为当前目录下的 config 文件夹
        self.config_file = self.config_dir / 'config.json'
        self.config = self._load_config()

    def _load_config(self):
        """加载配置文件"""
        if not self.config_dir.exists():
            self.config_dir.mkdir(parents=True)
        
        if not self.config_file.exists():
            return self._get_default_config()
            
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"加载配置文件失败: {str(e)}")
            return self._get_default_config()

    def _get_default_config(self):
        """获取默认配置"""
        return {
            'last_video_path': '',
            'window_scale': 0.4,  # 调整默认缩放比例为 0.4
            'playback_speed': 1.0,
            'output_directory': '',  # 添加输出目录配置项
            'auto_split': False  # 添加自动切割配置项
        }

    def save_config(self):
        """保存配置到文件"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"保存配置文件失败: {str(e)}")

    def get_last_video_path(self):
        """获取上次打开的视频路径"""
        return self.config.get('last_video_path', '')

    def set_last_video_path(self, path):
        """设置上次打开的视频路径"""
        self.config['last_video_path'] = path
        self.save_config()

    def get_window_scale(self):
        """获取窗口缩放比例"""
        return self.config.get('window_scale', 0.4)

    def get_playback_speed(self):
        """获取播放速度"""
        return self.config.get('playback_speed', 1.0)

    def get_output_directory(self):
        """获取输出目录"""
        return self.config.get('output_directory', '')

    def set_output_directory(self, path):
        """设置输出目录"""
        self.config['output_directory'] = path
        self.save_config()

    def get_auto_split(self):
        """获取是否自动切割视频"""
        return self.config.get('auto_split', False)

    def set_auto_split(self, auto_split):
        """设置是否自动切割视频"""
        self.config['auto_split'] = auto_split
        self.save_config()