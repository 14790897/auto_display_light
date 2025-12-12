# 打包成 EXE 说明文档

## 快速打包

### 方法 1: 使用自动脚本（推荐）

直接运行打包脚本：

```powershell
.\build.ps1
```

### 方法 2: 手动打包

#### 1. 安装依赖

```powershell
pip install -r requirements.txt
```

#### 2. 使用 PyInstaller 打包

**简单打包（单个 exe 文件）：**
```powershell
pyinstaller --onefile --name AutoDisplayLight autolight.py
```

**使用配置文件打包：**
```powershell
pyinstaller autolight.spec
```

#### 3. 找到生成的 exe

打包完成后，exe 文件位于：
- `dist\AutoDisplayLight.exe`

## 打包参数说明

- `--onefile`: 打包成单个 exe 文件
- `--name`: 指定生成的 exe 名称
- `--noconsole`: 无控制台窗口（适合后台运行，但会看不到日志）
- `--console`: 保留控制台窗口（推荐，方便调试）
- `--icon=icon.ico`: 指定图标文件

## 使用打包后的程序

1. 将 `dist\AutoDisplayLight.exe` 复制到任意位置
2. 双击运行即可
3. 按 `Ctrl+C` 停止程序

## 注意事项

⚠️ **首次运行前请修改配置：**

打包后的 exe 内嵌了代码，配置项在源代码的顶部：

```python
# 传感器地址
SENSOR_URL = "http://temt6000-sensor.local/sensor/temt6000_percentage"

# Twinkle Tray 的安装路径
TT_PATH = r"C:\Users\13963\AppData\Local\Programs\twinkle-tray\Twinkle Tray.exe"

# 刷新间隔 (秒)
INTERVAL = 5

# 屏幕亮度限制
MIN_BRIGHTNESS = 10 
MAX_BRIGHTNESS = 100

# 灵敏度阈值
THRESHOLD = 3
```

如需修改配置，请：
1. 修改 `autolight.py` 中的配置
2. 重新打包

## 设置开机自启动

### 方法 1: 任务计划程序（推荐）

1. 按 `Win + R`，输入 `taskschd.msc`
2. 点击"创建基本任务"
3. 触发器选择"登录时"
4. 操作选择"启动程序"，浏览选择 `AutoDisplayLight.exe`
5. 完成

### 方法 2: 启动文件夹

1. 按 `Win + R`，输入 `shell:startup`
2. 创建 `AutoDisplayLight.exe` 的快捷方式
3. 将快捷方式放入打开的文件夹

## 常见问题

### Q: 杀毒软件报毒怎么办？
A: PyInstaller 打包的程序可能被误报，添加到白名单即可。

### Q: 打包后文件太大？
A: 单文件模式会包含 Python 运行时，大约 10-20MB 是正常的。

### Q: 如何隐藏控制台窗口？
A: 修改 `autolight.spec` 文件，将 `console=True` 改为 `console=False`，然后重新打包。

### Q: 如何添加图标？
A: 
1. 准备一个 `.ico` 格式的图标文件
2. 在打包命令中添加 `--icon=your_icon.ico`
3. 或在 `autolight.spec` 中修改 `icon=None` 为 `icon='your_icon.ico'`

## 文件结构

```
auto_display_light/
├── autolight.py          # 源代码
├── autolight.spec        # PyInstaller 配置文件
├── requirements.txt      # Python 依赖
├── build.ps1            # 自动打包脚本
├── BUILD.md             # 本文档
└── dist/                # 打包输出目录
    └── AutoDisplayLight.exe
```
