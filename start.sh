#!/bin/bash

echo "正在检查Python环境..."
if ! command -v python3 &> /dev/null; then
    echo "Python未安装！请安装Python 3.x"
    exit 1
fi

echo "正在安装/更新依赖包..."
python3 -m pip install -r requirements.txt

echo "正在启动应用程序..."
python3 main.py