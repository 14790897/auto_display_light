# 打包成 EXE 说明文档

## 快速打包

### 本地打包

直接运行打包脚本：

```powershell
.\build.ps1
```

### 自动化打包（GitHub Actions）

项目已配置自动化构建流程：

**触发方式：**
1. **发布 Release** - 在 GitHub 创建新的 Release 时自动构建
2. **手动触发** - 在 Actions 页面手动运行工作流
   - 打开仓库 → Actions → "Build and Release AutoDisplayLight"
   - 点击 "Run workflow"
   - 输入版本标签（如 `v1.0.0`）

**构建产物：**
- `AutoDisplayLight.exe` - Windows 可执行文件
- `AutoDisplayLight-v*.*.*.Windows.zip` - 完整发布包
- `VERSION.txt` - 版本信息
- `README.txt` - 使用说明

所有构建产物会自动附加到 GitHub Release 中，也可在 Actions 页面下载 Artifacts。

## 手动打包步骤

### 1. 安装依赖

```powershell
pip install -r requirements.txt
```

### 2. 使用 PyInstaller 打包

```powershell
pyinstaller autolight_tray.spec
```

### 3. 找到生成的 exe

打包完成后，exe 文件位于：
- `dist\AutoDisplayLight.exe`

## 功能特点

✅ **系统托盘图标** - 程序运行在系统托盘，不占用任务栏空间  
✅ **右键菜单控制** - 右键托盘图标即可控制所有功能  
✅ **最小化到托盘** - 关闭窗口不退出程序，而是最小化到托盘  
✅ **图形化设置界面** - 无需编辑代码，所有配置都可视化设置  
✅ **配置自动保存** - 设置保存到用户目录，重启后自动加载  
✅ **开机自启动** - 在设置界面一键启用/禁用开机自启动  
✅ **传感器测试** - 一键测试传感器连接状态

## 使用打包后的程序

1. 双击运行 `dist\AutoDisplayLight.exe`
2. 程序会自动最小化到系统托盘（右下角）
3. 右键托盘图标可进行以下操作：
   - 显示主窗口 - 查看详细信息和状态
   - 启动/停止服务 - 控制自动亮度调节
   - 设置 - 打开配置界面
   - 退出 - 完全关闭程序

## 首次使用配置

1. 右键托盘图标 → **设置**
2. 配置以下信息：
   - **传感器地址**：你的 ESPHome 传感器 URL
   - **Twinkle Tray 路径**：浏览选择 Twinkle Tray.exe
   - **刷新间隔**：多久检测一次环境亮度（推荐 5 秒）
   - **亮度范围**：屏幕最小和最大亮度限制
   - **灵敏度阈值**：亮度变化超过多少才调节（防止频繁闪烁）
3. 点击 **测试连接** 确认传感器正常
4. 点击 **保存**

## 设置开机自启动

在设置界面中：
1. 滚动到"开机自启动"区域
2. 点击 **启用开机自启动** 按钮
3. 确认成功提示
4. 下次登录时程序会自动启动

取消自启动：
- 在设置中点击 **禁用开机自启动**

## 配置文件位置

配置保存在：`%USERPROFILE%\AutoDisplayLight_config.json`

示例路径：`C:\Users\你的用户名\AutoDisplayLight_config.json`

## 常见问题

### Q: 杀毒软件报毒怎么办？
A: PyInstaller 打包的程序可能被误报，添加到白名单即可。

### Q: 打包后文件太大？
A: 单文件模式会包含 Python 运行时和所有依赖库，大约 30-40MB 是正常的。

### Q: 托盘图标不显示？
A: 检查系统托盘设置，确保允许显示所有图标。Windows 11 在任务栏设置中可以配置。

### Q: 如何完全卸载？
A: 
1. 右键托盘图标 → 设置 → 禁用开机自启动
2. 右键托盘图标 → 退出
3. 删除 exe 文件
4. 删除配置文件：`%USERPROFILE%\AutoDisplayLight_config.json`

### Q: 如何查看任务计划？
A: 
1. 按 `Win + R`，输入 `taskschd.msc`
2. 在任务列表中找到 `AutoDisplayLight`

## 文件结构

```
auto_display_light/
├── autolight_tray.py     # 源代码（托盘版）
├── autolight_tray.spec   # PyInstaller 配置文件
├── requirements.txt      # Python 依赖
├── build.ps1            # 自动打包脚本
├── BUILD.md             # 本文档
└── dist/                # 打包输出目录
    └── AutoDisplayLight.exe  # 最终的可执行文件
```

## 技术说明

- **GUI 框架**：Tkinter（Python 内置）
- **托盘图标**：pystray
- **图像处理**：Pillow
- **HTTP 请求**：requests
- **打包工具**：PyInstaller
- **任务计划**：Windows Task Scheduler

