# 命令使用教程

## 安装依赖
```bash
pip install -r requirements.txt
```

## 使用说明

### 1. 基础命令
```bash
python main.py --help  # 查看帮助信息
python main.py run     # 运行主程序
```

### 2. 参数说明
- `--config`: 指定配置文件路径
- `--output`: 指定输出目录
- `--verbose`: 显示详细日志

### 3. 示例
```bash
# 使用自定义配置文件运行
python main.py run --config custom_config.yaml

# 指定输出目录
python main.py run --output ./results
```

## 注意事项
1. 请确保 Python 版本 >= 3.8
2. 运行前请先安装所需依赖
3. 配置文件必须符合 YAML 格式
