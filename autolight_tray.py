import json
import os
import subprocess
import sys
import threading
import time
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

import pystray
import requests
from PIL import Image, ImageDraw
from pystray import MenuItem as item

# ================= 配置文件路径 =================
CONFIG_FILE = Path.home() / "AutoDisplayLight_config.json"

# ================= 默认配置 =================
DEFAULT_CONFIG = {
    "sensor_url": "http://temt6000-sensor.local/sensor/temt6000_percentage",
    "tt_path": r"C:\Users\13963\AppData\Local\Programs\twinkle-tray\Twinkle Tray.exe",
    "interval": 5,
    "min_brightness": 0,
    "max_brightness": 100,
    "threshold": 3,
    "smooth_transition": True,
    "transition_step": 2,
    "transition_delay": 0.05,
    "enabled": True,
    "start_minimized": True
}

class AutostartManager:
    """开机自启动管理器"""
    
    TASK_NAME = "AutoDisplayLight"
    
    @staticmethod
    def get_exe_path():
        """获取当前 exe 路径"""
        if getattr(sys, 'frozen', False):
            # 打包后的 exe
            return sys.executable
        else:
            # 开发模式
            return os.path.abspath(__file__)
    
    @staticmethod
    def is_enabled():
        """检查是否已设置开机自启动"""
        try:
            result = subprocess.run(
                ['powershell', '-Command', 
                 f'Get-ScheduledTask -TaskName "{AutostartManager.TASK_NAME}" -ErrorAction SilentlyContinue'],
                capture_output=True,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            return result.returncode == 0 and AutostartManager.TASK_NAME in result.stdout
        except:
            return False
    
    @staticmethod
    def enable():
        """启用开机自启动"""
        exe_path = AutostartManager.get_exe_path()
        username = os.environ.get('USERNAME', '')
        
        # PowerShell 脚本
        ps_script = f"""
$action = New-ScheduledTaskAction -Execute '{exe_path}'
$trigger = New-ScheduledTaskTrigger -AtLogOn -User '{username}'
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -RunOnlyIfNetworkAvailable -ExecutionTimeLimit (New-TimeSpan -Days 0)
$principal = New-ScheduledTaskPrincipal -UserId '{username}' -LogonType Interactive
Register-ScheduledTask -TaskName '{AutostartManager.TASK_NAME}' -Action $action -Trigger $trigger -Settings $settings -Principal $principal -Description '自动调节屏幕亮度' -Force
"""
        
        try:
            result = subprocess.run(
                ['powershell', '-Command', ps_script],
                capture_output=True,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            return result.returncode == 0
        except Exception as e:
            print(f"启用自启动失败: {e}")
            return False
    
    @staticmethod
    def disable():
        """禁用开机自启动"""
        try:
            result = subprocess.run(
                ['powershell', '-Command', 
                 f'Unregister-ScheduledTask -TaskName "{AutostartManager.TASK_NAME}" -Confirm:$false'],
                capture_output=True,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            return result.returncode == 0
        except Exception as e:
            print(f"禁用自启动失败: {e}")
            return False

class ConfigManager:
    """配置管理器"""
    
    @staticmethod
    def load():
        """加载配置"""
        if CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    return {**DEFAULT_CONFIG, **config}
            except Exception as e:
                print(f"加载配置失败: {e}")
        return DEFAULT_CONFIG.copy()
    
    @staticmethod
    def save(config):
        """保存配置"""
        try:
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"保存配置失败: {e}")
            return False

class BrightnessController:
    """亮度控制器"""
    
    def __init__(self, config):
        self.config = config
        self.running = False
        self.thread = None
        self.last_brightness = -1
        self.status_callback = None
        self.current_sensor_value = None
        self.current_screen_value = None
        
    def set_status_callback(self, callback):
        """设置状态更新回调"""
        self.status_callback = callback
    
    def update_status(self, message):
        """更新状态信息"""
        if self.status_callback:
            self.status_callback(message)
    
    def get_sensor_value(self):
        """获取传感器数据"""
        try:
            response = requests.get(self.config['sensor_url'], timeout=3)
            response.raise_for_status()
            data = response.json()
            
            if 'value' in data:
                val = float(data['value'])
                self.current_sensor_value = val
                return val
        except Exception as e:
            self.update_status(f"传感器错误: {str(e)[:50]}")
            return None
        return None
    
    def set_screen_brightness(self, level, smooth=None):
        """设置屏幕亮度"""
        safe_level = max(self.config['min_brightness'], 
                        min(self.config['max_brightness'], level))
        safe_level = int(safe_level)
        
        # 判断是否使用平滑过渡
        use_smooth = smooth if smooth is not None else self.config.get('smooth_transition', True)
        
        if use_smooth and self.last_brightness >= 0:
            # 平滑过渡
            return self._smooth_transition(safe_level)
        else:
            # 直接设置
            return self._set_brightness_direct(safe_level)
    
    def _set_brightness_direct(self, level):
        """直接设置亮度（无过渡）"""
        cmd = [self.config['tt_path'], "--All", f"--Set={level}"]
        
        try:
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            subprocess.run(cmd, startupinfo=startupinfo, timeout=2)
            self.current_screen_value = level
            return True
        except FileNotFoundError:
            self.update_status("错误: 找不到 Twinkle Tray")
            return False
        except Exception as e:
            self.update_status(f"亮度设置错误: {str(e)[:30]}")
            return False
    
    def _smooth_transition(self, target_level):
        """平滑过渡到目标亮度"""
        current = int(self.last_brightness)
        step = self.config.get('transition_step', 2)
        delay = self.config.get('transition_delay', 0.05)
        
        if current == target_level:
            return True
        
        # 计算步进方向
        direction = 1 if target_level > current else -1
        
        # 逐步调整
        while abs(target_level - current) > 0:
            if not self.running:  # 如果服务停止，中断过渡
                break
            
            # 计算下一步的值
            remaining = abs(target_level - current)
            if remaining <= step:
                current = target_level
            else:
                current += direction * step
            
            # 设置亮度
            if not self._set_brightness_direct(current):
                return False
            
            # 如果还没到目标值，短暂延迟
            if current != target_level:
                time.sleep(delay)
        
        return True
    
    def run_loop(self):
        """主循环"""
        self.update_status("服务运行中...")
        
        while self.running:
            if self.config.get('enabled', True):
                sensor_val = self.get_sensor_value()
                
                if sensor_val is not None:
                    target_brightness = sensor_val
                    
                    # 初次运行或超过阈值时调整
                    if self.last_brightness < 0 or abs(target_brightness - self.last_brightness) > self.config['threshold']:
                        if self.set_screen_brightness(target_brightness):
                            self.last_brightness = target_brightness
                            mode = "平滑" if self.config.get('smooth_transition', True) else "直接"
                            self.update_status(f"环境: {sensor_val:.1f}% → 屏幕: {int(target_brightness)}% [{mode}]")
            
            time.sleep(self.config['interval'])
    
    def start(self):
        """启动服务"""
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self.run_loop, daemon=True)
            self.thread.start()
            self.update_status("服务已启动")
    
    def stop(self):
        """停止服务"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=2)
        self.update_status("服务已停止")
    
    def reload_config(self, new_config):
        """重新加载配置"""
        self.config = new_config

class SettingsWindow:
    """设置窗口"""
    
    def __init__(self, parent, config, on_save):
        self.window = tk.Toplevel(parent)
        self.window.title("自动亮度设置")
        self.window.geometry("600x750")
        self.window.resizable(False, False)
        
        self.config = config.copy()
        self.on_save = on_save
        
        self.create_widgets()
        
        # 居中显示
        self.center_window()
        self.window.transient(parent)
        self.window.grab_set()
    
    def center_window(self):
        """窗口居中"""
        self.window.update_idletasks()
        width = self.window.winfo_width()
        height = self.window.winfo_height()
        x = (self.window.winfo_screenwidth() // 2) - (width // 2)
        y = (self.window.winfo_screenheight() // 2) - (height // 2)
        self.window.geometry(f'{width}x{height}+{x}+{y}')
    
    def create_widgets(self):
        """创建界面组件"""
        # 主容器
        main_frame = ttk.Frame(self.window, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 传感器设置
        sensor_frame = ttk.LabelFrame(main_frame, text="传感器设置", padding="10")
        sensor_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(sensor_frame, text="传感器地址:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.sensor_url_var = tk.StringVar(value=self.config['sensor_url'])
        ttk.Entry(sensor_frame, textvariable=self.sensor_url_var, width=50).grid(row=0, column=1, pady=5)
        
        # Twinkle Tray 设置
        tt_frame = ttk.LabelFrame(main_frame, text="Twinkle Tray 设置", padding="10")
        tt_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(tt_frame, text="程序路径:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.tt_path_var = tk.StringVar(value=self.config['tt_path'])
        path_entry = ttk.Entry(tt_frame, textvariable=self.tt_path_var, width=40)
        path_entry.grid(row=0, column=1, pady=5, padx=(0, 5))
        ttk.Button(tt_frame, text="浏览...", command=self.browse_tt_path).grid(row=0, column=2, pady=5)
        
        # 运行参数
        params_frame = ttk.LabelFrame(main_frame, text="运行参数", padding="10")
        params_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 刷新间隔
        ttk.Label(params_frame, text="刷新间隔 (秒):").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.interval_var = tk.IntVar(value=self.config['interval'])
        ttk.Spinbox(params_frame, from_=1, to=60, textvariable=self.interval_var, width=10).grid(row=0, column=1, sticky=tk.W, pady=5)
        
        # 最小亮度
        ttk.Label(params_frame, text="最小亮度 (%):").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.min_brightness_var = tk.IntVar(value=self.config['min_brightness'])
        ttk.Spinbox(params_frame, from_=0, to=100, textvariable=self.min_brightness_var, width=10).grid(row=1, column=1, sticky=tk.W, pady=5)
        
        # 最大亮度
        ttk.Label(params_frame, text="最大亮度 (%):").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.max_brightness_var = tk.IntVar(value=self.config['max_brightness'])
        ttk.Spinbox(params_frame, from_=0, to=100, textvariable=self.max_brightness_var, width=10).grid(row=2, column=1, sticky=tk.W, pady=5)
        
        # 灵敏度阈值
        ttk.Label(params_frame, text="灵敏度阈值 (%):").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.threshold_var = tk.IntVar(value=self.config['threshold'])
        ttk.Spinbox(params_frame, from_=1, to=20, textvariable=self.threshold_var, width=10).grid(row=3, column=1, sticky=tk.W, pady=5)
        ttk.Label(params_frame, text="(变化超过此值才调节)", font=('', 8)).grid(row=3, column=2, sticky=tk.W, padx=(5, 0))
        
        # 平滑过渡设置
        smooth_frame = ttk.LabelFrame(main_frame, text="平滑过渡", padding="10")
        smooth_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.smooth_transition_var = tk.BooleanVar(value=self.config.get('smooth_transition', True))
        ttk.Checkbutton(smooth_frame, text="启用平滑过渡", variable=self.smooth_transition_var, 
                       command=self.toggle_smooth_options).pack(anchor=tk.W, pady=(0, 5))
        
        smooth_params_frame = ttk.Frame(smooth_frame)
        smooth_params_frame.pack(fill=tk.X, padx=(20, 0))
        self.smooth_params_frame = smooth_params_frame
        
        ttk.Label(smooth_params_frame, text="过渡步长 (%):").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.transition_step_var = tk.IntVar(value=self.config.get('transition_step', 2))
        ttk.Spinbox(smooth_params_frame, from_=1, to=10, textvariable=self.transition_step_var, width=10).grid(row=0, column=1, sticky=tk.W, pady=5)
        ttk.Label(smooth_params_frame, text="(每步调整的亮度)", font=('', 8)).grid(row=0, column=2, sticky=tk.W, padx=(5, 0))
        
        ttk.Label(smooth_params_frame, text="过渡延迟 (秒):").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.transition_delay_var = tk.DoubleVar(value=self.config.get('transition_delay', 0.05))
        ttk.Spinbox(smooth_params_frame, from_=0.01, to=0.5, increment=0.01, 
                   textvariable=self.transition_delay_var, width=10, format="%.2f").grid(row=1, column=1, sticky=tk.W, pady=5)
        ttk.Label(smooth_params_frame, text="(每步之间的间隔)", font=('', 8)).grid(row=1, column=2, sticky=tk.W, padx=(5, 0))
        
        self.toggle_smooth_options()
        
        # 界面选项
        ui_frame = ttk.LabelFrame(main_frame, text="界面选项", padding="10")
        ui_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.start_minimized_var = tk.BooleanVar(value=self.config.get('start_minimized', True))
        ttk.Checkbutton(ui_frame, text="启动时最小化到托盘", variable=self.start_minimized_var).pack(anchor=tk.W)
        
        # 开机自启动
        autostart_frame = ttk.LabelFrame(main_frame, text="开机自启动", padding="10")
        autostart_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 显示当前状态
        self.autostart_status_var = tk.StringVar()
        self.update_autostart_status()
        status_label = ttk.Label(autostart_frame, textvariable=self.autostart_status_var)
        status_label.pack(anchor=tk.W, pady=(0, 5))
        
        # 开关按钮
        autostart_btn_frame = ttk.Frame(autostart_frame)
        autostart_btn_frame.pack(fill=tk.X)
        
        self.enable_autostart_btn = ttk.Button(
            autostart_btn_frame, 
            text="启用开机自启动", 
            command=self.enable_autostart,
            width=20
        )
        self.enable_autostart_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        self.disable_autostart_btn = ttk.Button(
            autostart_btn_frame,
            text="禁用开机自启动",
            command=self.disable_autostart,
            width=20
        )
        self.disable_autostart_btn.pack(side=tk.LEFT)
        
        self.update_autostart_buttons()
        
        # 按钮
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Button(button_frame, text="保存", command=self.save_settings, width=15).pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(button_frame, text="取消", command=self.window.destroy, width=15).pack(side=tk.RIGHT)
        ttk.Button(button_frame, text="测试连接", command=self.test_connection, width=15).pack(side=tk.LEFT)
    
    def browse_tt_path(self):
        """浏览选择 Twinkle Tray 路径"""
        filename = filedialog.askopenfilename(
            title="选择 Twinkle Tray.exe",
            filetypes=[("可执行文件", "*.exe"), ("所有文件", "*.*")]
        )
        if filename:
            self.tt_path_var.set(filename)
    
    def test_connection(self):
        """测试传感器连接"""
        url = self.sensor_url_var.get()
        try:
            response = requests.get(url, timeout=3)
            response.raise_for_status()
            data = response.json()
            if 'value' in data:
                val = float(data['value'])
                messagebox.showinfo("连接成功", f"传感器当前值: {val:.2f}%")
            else:
                messagebox.showerror("连接失败", "无法解析传感器数据")
        except Exception as e:
            messagebox.showerror("连接失败", f"错误: {e}")
    
    def update_autostart_status(self):
        """更新开机自启动状态显示"""
        if AutostartManager.is_enabled():
            self.autostart_status_var.set("✅ 已启用开机自启动")
        else:
            self.autostart_status_var.set("❌ 未启用开机自启动")
    
    def update_autostart_buttons(self):
        """更新开机自启动按钮状态"""
        is_enabled = AutostartManager.is_enabled()
        if is_enabled:
            self.enable_autostart_btn.config(state=tk.DISABLED)
            self.disable_autostart_btn.config(state=tk.NORMAL)
        else:
            self.enable_autostart_btn.config(state=tk.NORMAL)
            self.disable_autostart_btn.config(state=tk.DISABLED)
    
    def enable_autostart(self):
        """启用开机自启动"""
        if AutostartManager.enable():
            messagebox.showinfo("成功", "已启用开机自启动\n下次登录时程序将自动启动")
            self.update_autostart_status()
            self.update_autostart_buttons()
        else:
            messagebox.showerror("失败", "启用开机自启动失败\n请检查是否有足够的权限")
    
    def disable_autostart(self):
        """禁用开机自启动"""
        if AutostartManager.disable():
            messagebox.showinfo("成功", "已禁用开机自启动")
            self.update_autostart_status()
            self.update_autostart_buttons()
        else:
            messagebox.showerror("失败", "禁用开机自启动失败")
    
    def toggle_smooth_options(self):
        """切换平滑过渡选项的启用状态"""
        state = tk.NORMAL if self.smooth_transition_var.get() else tk.DISABLED
        for child in self.smooth_params_frame.winfo_children():
            if isinstance(child, (ttk.Spinbox, ttk.Label)):
                child.configure(state=state)
    
    def save_settings(self):
        """保存设置"""
        self.config['sensor_url'] = self.sensor_url_var.get()
        self.config['tt_path'] = self.tt_path_var.get()
        self.config['interval'] = self.interval_var.get()
        self.config['min_brightness'] = self.min_brightness_var.get()
        self.config['max_brightness'] = self.max_brightness_var.get()
        self.config['threshold'] = self.threshold_var.get()
        self.config['smooth_transition'] = self.smooth_transition_var.get()
        self.config['transition_step'] = self.transition_step_var.get()
        self.config['transition_delay'] = self.transition_delay_var.get()
        self.config['start_minimized'] = self.start_minimized_var.get()
        
        if self.on_save(self.config):
            messagebox.showinfo("成功", "设置已保存")
            self.window.destroy()
        else:
            messagebox.showerror("错误", "保存设置失败")

class MainWindow:
    """主窗口"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("自动屏幕亮度调节")
        self.root.geometry("500x350")
        self.root.resizable(False, False)
        
        # 加载配置
        self.config = ConfigManager.load()
        
        # 创建控制器
        self.controller = BrightnessController(self.config)
        self.controller.set_status_callback(self.update_status)
        
        # 托盘图标
        self.tray_icon = None
        self.is_hidden = False
        
        self.create_widgets()
        
        # 窗口关闭事件 - 最小化到托盘而不是退出
        self.root.protocol("WM_DELETE_WINDOW", self.hide_window)
        
        # 如果配置启用，自动启动
        if self.config.get('enabled', True):
            self.start_service()
        
        # 创建托盘图标
        self.create_tray_icon()
        
        # 如果设置了启动时最小化
        if self.config.get('start_minimized', True):
            self.root.after(100, self.hide_window)
    
    def create_tray_icon(self):
        """创建系统托盘图标"""
        # 创建图标图像
        image = self.create_icon_image()
        
        # 创建菜单
        menu = pystray.Menu(
            item('显示主窗口', self.show_window),
            item('启动服务', self.start_service_from_tray, 
                 enabled=lambda _: not self.controller.running),
            item('停止服务', self.stop_service_from_tray,
                 enabled=lambda _: self.controller.running),
            pystray.Menu.SEPARATOR,
            item('设置', self.open_settings_from_tray),
            pystray.Menu.SEPARATOR,
            item('退出', self.quit_app)
        )
        
        # 创建托盘图标
        self.tray_icon = pystray.Icon(
            "AutoDisplayLight",
            image,
            "自动屏幕亮度调节",
            menu
        )
        
        # 在后台线程运行
        threading.Thread(target=self.tray_icon.run, daemon=True).start()
    
    def create_icon_image(self):
        """创建托盘图标图像"""
        # 创建一个简单的太阳图标
        width = 64
        height = 64
        image = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        dc = ImageDraw.Draw(image)
        
        # 绘制圆形
        padding = 10
        dc.ellipse(
            [padding, padding, width - padding, height - padding],
            fill='orange',
            outline='darkorange',
            width=3
        )
        
        # 绘制光线
        center = width // 2
        for angle in range(0, 360, 45):
            import math
            rad = math.radians(angle)
            x1 = center + int((width // 4) * math.cos(rad))
            y1 = center + int((height // 4) * math.sin(rad))
            x2 = center + int((width // 2 - 5) * math.cos(rad))
            y2 = center + int((height // 2 - 5) * math.sin(rad))
            dc.line([x1, y1, x2, y2], fill='orange', width=3)
        
        return image
    
    def create_widgets(self):
        """创建界面组件"""
        # 主容器
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 标题
        title_label = ttk.Label(main_frame, text="自动屏幕亮度调节", font=('', 16, 'bold'))
        title_label.pack(pady=(0, 20))
        
        # 状态显示
        status_frame = ttk.LabelFrame(main_frame, text="运行状态", padding="10")
        status_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 20))
        
        self.status_label = ttk.Label(status_frame, text="未启动", font=('', 10))
        self.status_label.pack()
        
        # 控制按钮
        control_frame = ttk.Frame(main_frame)
        control_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.start_button = ttk.Button(control_frame, text="启动服务", command=self.start_service, width=15)
        self.start_button.pack(side=tk.LEFT, padx=(0, 5))
        
        self.stop_button = ttk.Button(control_frame, text="停止服务", command=self.stop_service, width=15, state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(control_frame, text="设置", command=self.open_settings, width=15).pack(side=tk.LEFT)
        
        ttk.Button(control_frame, text="最小化到托盘", command=self.hide_window, width=15).pack(side=tk.RIGHT)
        
        # 信息显示
        info_frame = ttk.LabelFrame(main_frame, text="当前配置", padding="10")
        info_frame.pack(fill=tk.X)
        
        self.info_text = tk.Text(info_frame, height=6, wrap=tk.WORD, state=tk.DISABLED)
        self.info_text.pack(fill=tk.X)
        
        self.update_info_display()
    
    def update_status(self, message):
        """更新状态显示"""
        self.status_label.config(text=message)
        # 更新托盘图标提示
        if self.tray_icon:
            status = "运行中" if self.controller.running else "已停止"
            self.tray_icon.title = f"自动屏幕亮度调节 - {status}\n{message}"
    
    def update_info_display(self):
        """更新配置信息显示"""
        info = f"""传感器: {self.config['sensor_url']}
刷新间隔: {self.config['interval']} 秒
亮度范围: {self.config['min_brightness']}% - {self.config['max_brightness']}%
灵敏度: {self.config['threshold']}%"""
        
        self.info_text.config(state=tk.NORMAL)
        self.info_text.delete(1.0, tk.END)
        self.info_text.insert(1.0, info)
        self.info_text.config(state=tk.DISABLED)
    
    def start_service(self):
        """启动服务"""
        self.controller.start()
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
    
    def stop_service(self):
        """停止服务"""
        self.controller.stop()
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
    
    def start_service_from_tray(self):
        """从托盘启动服务"""
        self.root.after(0, self.start_service)
    
    def stop_service_from_tray(self):
        """从托盘停止服务"""
        self.root.after(0, self.stop_service)
    
    def open_settings(self):
        """打开设置窗口"""
        def on_save(new_config):
            if ConfigManager.save(new_config):
                self.config = new_config
                self.controller.reload_config(new_config)
                self.update_info_display()
                return True
            return False
        
        SettingsWindow(self.root, self.config, on_save)
    
    def open_settings_from_tray(self):
        """从托盘打开设置"""
        self.root.after(0, self.show_window)
        self.root.after(100, self.open_settings)
    
    def hide_window(self):
        """隐藏窗口到托盘"""
        self.root.withdraw()
        self.is_hidden = True
    
    def show_window(self):
        """显示窗口"""
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()
        self.is_hidden = False
    
    def quit_app(self):
        """退出应用"""
        if self.controller.running:
            self.controller.stop()
        if self.tray_icon:
            self.tray_icon.stop()
        self.root.quit()
    
    def run(self):
        """运行主循环"""
        self.root.mainloop()

if __name__ == "__main__":
    app = MainWindow()
    app.run()
