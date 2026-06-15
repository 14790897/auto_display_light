import requests
import subprocess
import time
import os
import json
import tkinter as tk
from tkinter import filedialog

CONFIG_FILE = os.path.join(os.path.expanduser("~"), "AutoDisplayLight_config.json")

DEFAULT_CONFIG = {
    "sensor_url": "http://temt6000-sensor.local/sensor/temt6000_percentage",
    "tt_path": "",
    "interval": 5,
    "min_brightness": 10,
    "max_brightness": 100,
    "threshold": 3,
}

def load_config():
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return dict(DEFAULT_CONFIG)

def save_config(config):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)

def find_twinkle_tray():
    candidates = [
        os.path.expandvars(r"%LOCALAPPDATA%\Programs\twinkle-tray\Twinkle Tray.exe"),
        os.path.expandvars(r"%PROGRAMFILES%\Twinkle Tray\Twinkle Tray.exe"),
        os.path.expandvars(r"%PROGRAMFILES(X86)%\Twinkle Tray\Twinkle Tray.exe"),
        r"C:\Program Files\Twinkle Tray\Twinkle Tray.exe",
        r"C:\Program Files (x86)\Twinkle Tray\Twinkle Tray.exe",
    ]
    for path in candidates:
        if path and os.path.exists(path):
            return path
    return ""

# ── 传感器读取 ─────────────────────────────────────────────

def get_sensor_value(sensor_url):
    try:
        resp = requests.get(sensor_url, timeout=3)
        resp.raise_for_status()
        data = resp.json()
        if "value" in data:
            val = float(data["value"])
            print(f"当前环境亮度: {val:.2f}%")
            return val
    except Exception as e:
        print(f"获取传感器数据失败: {e}")
    return None

# ── 亮度调节 ───────────────────────────────────────────────

def set_brightness(level, config):
    tt = config["tt_path"]
    if not tt or not os.path.exists(tt):
        print(f"错误: 找不到 Twinkle Tray: {tt}")
        return
    safe = max(config["min_brightness"], min(config["max_brightness"], int(level)))
    try:
        si = subprocess.STARTUPINFO()
        si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        subprocess.run([tt, "--All", f"--Set={safe}"], startupinfo=si)
        print(f"→ 屏幕亮度已设为 {safe}%")
    except Exception as e:
        print(f"调节亮度失败: {e}")

# ── 主循环 ─────────────────────────────────────────────────

def main_loop(config):
    print("--- AutoDisplayLight 运行中 (Ctrl+C 停止) ---")
    last = -999
    while True:
        val = get_sensor_value(config["sensor_url"])
        if val is not None:
            if abs(val - last) > config["threshold"]:
                set_brightness(val, config)
                last = val
        time.sleep(config["interval"])

# ── 配置界面 ───────────────────────────────────────────────

class ConfigWindow:
    def __init__(self, config):
        self.config = config
        self.result = None
        self.root = tk.Tk()
        self.root.title("AutoDisplayLight 配置")
        self.root.geometry("520x380")
        self.build_ui()
        self.root.mainloop()

    def build_ui(self):
        cf = self.config
        row = 0

        def add_row(label, var_key, width=45):
            nonlocal row
            tk.Label(self.root, text=label).grid(row=row, column=0, sticky="w", padx=10, pady=5)
            var = tk.StringVar(value=str(cf.get(var_key, "")))
            setattr(self, f"{var_key}_var", var)
            tk.Entry(self.root, textvariable=var, width=width).grid(row=row, column=1, padx=10, pady=5, columnspan=2, sticky="w")
            row += 1

        add_row("传感器 URL:", "sensor_url")
        row -= 1

        tk.Label(self.root, text="Twinkle Tray 路径:").grid(row=row, column=0, sticky="w", padx=10, pady=5)
        self.tt_path_var = tk.StringVar(value=cf.get("tt_path", ""))
        tk.Entry(self.root, textvariable=self.tt_path_var, width=36).grid(row=row, column=1, padx=(10,0), pady=5, sticky="w")
        tk.Button(self.root, text="浏览...", command=self.browse, width=8).grid(row=row, column=2, padx=5, pady=5)
        row += 1

        for label, key in [
            ("刷新间隔 (秒):", "interval"),
            ("最小亮度 (%):", "min_brightness"),
            ("最大亮度 (%):", "max_brightness"),
            ("灵敏度阈值 (%):", "threshold"),
        ]:
            tk.Label(self.root, text=label).grid(row=row, column=0, sticky="w", padx=10, pady=5)
            var = tk.StringVar(value=str(cf.get(key, "")))
            setattr(self, f"{key}_var", var)
            tk.Entry(self.root, textvariable=var, width=12).grid(row=row, column=1, sticky="w", padx=10, pady=5)
            row += 1

        tk.Button(self.root, text="💾 保存并启动", command=self.on_save,
                  bg="#4CAF50", fg="white", height=2, width=25).grid(
                      row=row, column=0, columnspan=3, pady=20)

    def browse(self):
        p = filedialog.askopenfilename(title="选择 Twinkle Tray.exe", filetypes=[("EXE", "*.exe")])
        if p:
            self.tt_path_var.set(p)

    def on_save(self):
        try:
            self.config = {
                "sensor_url": self.sensor_url_var.get().strip(),
                "tt_path": self.tt_path_var.get().strip(),
                "interval": int(self.interval_var.get()),
                "min_brightness": int(self.min_brightness_var.get()),
                "max_brightness": int(self.max_brightness_var.get()),
                "threshold": int(self.threshold_var.get()),
            }
        except ValueError:
            import tkinter.messagebox as mb
            mb.showerror("错误", "请填写正确的数值")
            return
        save_config(self.config)
        self.result = self.config
        self.root.quit()
        self.root.destroy()

# ── 入口 ───────────────────────────────────────────────────

def main():
    config = load_config()

    # 自动查找 Twinkle Tray
    if not config.get("tt_path") or not os.path.exists(config["tt_path"]):
        found = find_twinkle_tray()
        if found:
            config["tt_path"] = found
            save_config(config)

    # 配置不完整 → 弹窗
    need_config = (
        not config.get("tt_path") or
        not os.path.exists(config["tt_path"]) or
        not config.get("sensor_url")
    )

    if need_config:
        print("首次运行，请填写配置...")
        win = ConfigWindow(config)
        result = win.result
        if not result:
            print("未保存配置，退出。")
            return
        config = result

    main_loop(config)

if __name__ == "__main__":
    main()
