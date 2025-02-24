"""视频合并模块"""
import os
import subprocess

class VideoMerger:
    def __init__(self):
        self.progress_callback = None
        self.log_callback = None

    def set_progress_callback(self, callback):
        """设置进度回调函数"""
        self.progress_callback = callback

    def set_log_callback(self, callback):
        """设置日志回调函数"""
        self.log_callback = callback

    def merge_videos(self, video_files, output_path, ffmpeg_path=None):
        """合并多个视频文件
        
        Args:
            video_files: 要合并的视频文件列表
            output_path: 输出文件路径
            ffmpeg_path: ffmpeg可执行文件路径
        """
        if not video_files:
            if self.log_callback:
                self.log_callback("没有需要合并的视频文件！")
            return None

        try:
            # 创建临时文件列表
            temp_list_path = os.path.join(os.path.dirname(output_path), "temp_file_list.txt")
            with open(temp_list_path, "w", encoding="utf-8") as f:
                for file in video_files:
                    f.write(f"file '{file}'\n")

            # 使用ffmpeg合并视频
            cmd = [
                ffmpeg_path,
                '-f', 'concat',
                '-safe', '0',
                '-i', temp_list_path,
                '-c', 'copy',
                '-y',
                output_path
            ]
            
            if self.log_callback:
                self.log_callback("开始合并视频...")
            
            subprocess.run(cmd, check=True)
            
            # 删除临时文件
            os.remove(temp_list_path)
            
            if self.log_callback:
                self.log_callback(f"视频合并完成，已保存到: {output_path}")
            
            if self.progress_callback:
                self.progress_callback(100)
                
            return output_path
            
        except Exception as e:
            if self.log_callback:
                self.log_callback(f"合并视频时出错: {str(e)}")
            return None