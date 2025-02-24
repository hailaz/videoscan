@echo off
chcp 65001>nul
echo 正在检查Python环境...
python --version || (
    echo Python未安装！请安装Python 3.x并添加到系统PATH
    pause
    exit /b 1
)

@REM echo 正在安装/更新依赖包...
@REM python -m pip install -r requirements.txt

echo 正在启动应用程序...
python main.py

@REM pause