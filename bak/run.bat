@echo off
chcp 65001 > nul
setlocal enabledelayedexpansion

@REM 设置 ffmpeg 路径
set "FFMPEG=%~dp0bin\ffmpeg.exe"

@REM 设置参数
set "input_video=%~1"

@REM 检查输入参数
if "%input_video%"=="" (
  echo "[错误] 未提供视频文件路径"
  echo "使用方法: %~nx0 视频文件路径"
  exit /b 1
)

@REM 检查文件是否存在
if not exist "%input_video%" (
  echo "[错误] 文件 '%input_video%' 不存在"
  exit /b 1
)

@REM 检查是否存在 ffmpeg
if not exist "%FFMPEG%" (
  echo "[错误] 在bin目录中未找到ffmpeg"
  exit /b 1
)

echo "[信息] 正在分析视频文件: '%input_video%'"
echo "[信息] 场景检测阈值: 0.1 (范围0.0-1.0)"
echo "[信息] - 0.1: 检测较小场景变化"
echo "[信息] - 0.2-0.3: 适合普通视频"
echo "[信息] - 0.4: 适合变化剧烈的视频"
echo "--------------------------------------"

@REM 创建 log 目录（如果不存在）
if not exist "log" mkdir "log"

@REM 创建 output 目录（如果不存在）
if not exist "output" mkdir "output"

@REM 创建带时间戳的日志文件名和输出目录名
for /f "tokens=2-4 delims=/ " %%a in ('date /t') do (
  set "datestr=%%a-%%b-%%c"
)
for /f "tokens=1-2 delims=: " %%a in ('time /t') do (
  set "timestr=%%a_%%b"
)
set "log_file=log\video_info_%datestr%_%timestr%.log"
set "output_dir=output\scene_%datestr%_%timestr%"
mkdir "%output_dir%"

@REM 获取视频信息并保存到日志
echo "[信息] 正在获取视频信息..."
"%FFMPEG%" -i "%input_video%" 2> "%log_file%"

@REM 显示视频信息
for /f "tokens=* usebackq" %%a in (`findstr "Duration" "%log_file%"`) do (
    echo "[信息] 时长: %%a"
)
for /f "tokens=* usebackq" %%a in (`findstr "Stream" "%log_file%"`) do (
    echo "[信息] 视频流: %%a"
)

echo "[信息] 视频信息已保存到: '%log_file%'"
echo "--------------------------------------"

@REM 进行场景检测并截图
echo "[信息] 正在进行场景检测并截图..."
"%FFMPEG%" -i "%input_video%" -filter_complex "[0:v]select='gt(scene,0.1)',metadata=print:file='%output_dir%\scenes.txt',scale=640:-1[s0];[s0]uniqueify[s1];[s1]thumbnail=n=1[out]" -map "[out]" -vsync vfr "%output_dir%\scene_%%03d.jpg"

echo "[信息] 场景检测和截图完成"
echo "[信息] 截图保存在: '%output_dir%'"
echo "[信息] 场景时间信息保存在: '%output_dir%\scenes.txt'"
echo "--------------------------------------"

@REM 显示检测到的场景数量
for /f %%a in ('dir /b /a-d "%output_dir%\scene_*.jpg" ^| find /c /v ""') do (
    echo "[信息] 共检测到 %%a 个场景"
)
