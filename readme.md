# 智能视频处理工具

## 项目说明

这是一个基于视频动作检测的智能视频处理工具，主要用于自动检测和切割视频中的动作片段。

### 核心功能

1. 视频动作检测
   - 运动检测算法
   - 可配置的检测参数
   - GPU加速支持
   - 多视频并行处理

2. 视频切割处理
   - 基于动作片段的智能切割
   - FFmpeg集成
   - 自动合并相近片段
   - 批量视频处理

3. 用户界面
   - 可视化检测过程
   - 实时进度显示
   - 参数配置界面
   - 文件管理功能

4. 配置管理
   - JSON配置文件
   - 最近文件记录
   - 自定义输出目录
   - 处理参数持久化

## Go重构计划

### 1. 项目结构
```
motioncut/
├── cmd/                    # 命令行入口
│   └── motioncut/
├── internal/              # 内部实现
│   ├── config/           # 配置管理
│   ├── detector/         # 运动检测
│   ├── processor/        # 视频处理
│   └── gui/             # 图形界面
├── pkg/                  # 公共包
│   ├── ffmpeg/          # FFmpeg封装
│   └── utils/           # 工具函数
└── resources/           # 资源文件
    └── bin/            # FFmpeg二进制
```

### 2. 核心模块

#### A. 配置管理(internal/config)
- 配置结构定义
- JSON配置读写
- 默认配置管理

#### B. 运动检测(internal/detector)
- 视频帧分析
- GPU加速支持
- 运动区域识别
- 参数优化

#### C. 视频处理(internal/processor)
- 视频切割
- 片段合并
- 并行处理
- 进度管理

#### D. 图形界面(internal/gui)
- Fyne GUI框架
- 实时预览
- 进度展示
- 参数配置

### 3. 技术栈

1. 基础框架：
   - Go 1.22+
   - GoCV (OpenCV封装)
   - FFmpeg-go
   - Fyne (GUI框架)

2. 核心依赖：
   - OpenCV
   - FFmpeg
   - SQLite (配置存储)

### 4. 优化重点

1. 性能优化：
   - Go协程并行处理
   - GPU加速支持
   - 内存使用优化
   - I/O效率提升

2. 功能增强：
   - 更精确的检测算法
   - 更多视频格式支持
   - 批处理能力提升
   - 网络处理支持

3. 用户体验：
   - 更现代的GUI设计
   - 更友好的操作流程
   - 更详细的处理日志
   - 更灵活的配置选项

## 安装说明

### 环境要求
1. Go 1.22+
2. OpenCV 4.x
3. FFmpeg
4. GPU支持（可选）

### 安装步骤

1. 克隆项目
```bash
git clone https://github.com/username/motioncut.git
```

2. 安装依赖
```bash
go mod download
```

3. 编译运行
```bash
go run cmd/motioncut/main.go
```

## 使用说明

### 1. 命令行模式
```bash
motioncut -i input.mp4 -o output/ --gpu
```

### 2. GUI模式
```bash
motioncut gui
```

### 3. 配置参数
- `--config`: 指定配置文件
- `--output`: 指定输出目录
- `--gpu`: 启用GPU加速
- `--workers`: 并行处理数量

## 注意事项
1. 确保已正确安装所有依赖
2. GPU加速需要CUDA支持
3. 建议使用SSD存储以提高处理速度
