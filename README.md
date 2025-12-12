# TEMT6000 光照传感器固件上传教程

## 固件文件位置



### 固件文件说明

| 文件名 | 大小 | 用途 | 上传方式 |
|--------|------|------|----------|
| **firmware.factory.bin** | 1,198,816 字节 | ✅ **完整固件（推荐首次烧录）** | USB串口 |
| firmware.bin | 1,133,280 字节 | 应用程序（OTA更新用） | OTA |
| firmware.ota.bin | 1,133,280 字节 | OTA更新专用 | OTA |
| bootloader.bin | 18,656 字节 | 引导程序 | 手动分区烧录 |
| partitions.bin | 3,072 字节 | 分区表 | 手动分区烧录 |

---

## 方法1：ESPHome 自动上传（最简单）

### 前提条件
- ESP32-C3 通过 USB 连接到电脑
- 已安装 ESPHome

### 步骤

```powershell
# 在项目根目录执行
cd C:\git-program\Embedded\MY-ESPHOME

# 自动编译并上传
esphome run .\configs\environmental-sensors\temt6000-esp32c3.yaml
```

ESPHome 会自动：
1. 编译固件
2. 检测串口
3. 上传固件
4. 显示日志

---

## 方法2：使用 esptool.py 手动烧录（推荐备份）

### 安装 esptool

```powershell
pip install esptool
```

### 查找串口号

```powershell
# Windows
mode
# 或者在设备管理器中查看 "端口(COM 和 LPT)"
```

假设是 **COM3**

### 烧录完整固件（首次使用）

```powershell
esptool.py --chip esp32c3 --port COM3 --baud 460800 write_flash 0x0 "C:\git-program\Embedded\MY-ESPHOME\configs\environmental-sensors\.esphome\build\temt6000-sensor\.pioenvs\temt6000-sensor\firmware.factory.bin"
```

**参数说明：**
- `--chip esp32c3`：芯片型号
- `--port COM3`：串口号（根据实际情况修改）
- `--baud 460800`：波特率（可选：115200, 230400, 460800, 921600）
- `write_flash 0x0`：从地址 0x0 开始写入
- 最后是固件路径

### 擦除 Flash（可选，遇到问题时使用）

```powershell
esptool.py --chip esp32c3 --port COM3 erase_flash
```

---

## 方法3：使用 Flash Download Tool（图形界面）

### 下载工具
https://www.espressif.com.cn/zh-hans/support/download/other-tools

### 烧录步骤

1. **打开 Flash Download Tool**
2. **选择芯片类型**：ESP32-C3
3. **配置烧录文件**：

   | 文件路径 | 地址 | 勾选 |
   |---------|------|-----|
   | `firmware.factory.bin` | 0x0 | ✅ |

4. **配置串口**：
   - COM Port: COM3（根据实际修改）
   - Baud: 460800

5. **点击 START** 开始烧录

---

## 方法4：OTA 无线更新（已烧录过固件）

### 前提条件
- ESP32 已连接 WiFi
- 已烧录过包含 OTA 功能的固件

### 步骤

```powershell
# 通过 WiFi 更新（设备名：temt6000-sensor）
esphome run .\configs\environmental-sensors\temt6000-esp32c3.yaml --device temt6000-sensor.local
```

或者在 ESPHome Dashboard 中点击 "UPLOAD" → "Wirelessly"

---

## 烧录后验证

### 1. 串口日志

```powershell
# ESPHome 日志
esphome logs .\configs\environmental-sensors\temt6000-esp32c3.yaml

# 或使用 Arduino Serial Monitor / PuTTY / minicom
# 波特率：115200
```

应该看到：
```
[I][temt6000:xxx]: Voltage: 1.234V, Percentage: 37.4%
[I][udp:xxx]: Broadcast: {"device":"temt6000","percentage":37.4,"lux":520.3,"voltage":1.234}
```

### 2. Web 界面

浏览器访问：
```
http://temt6000-sensor.local
```


### 3. HTTP API 测试

```powershell
# 获取光照百分比
curl http://temt6000-sensor.local/sensor/temt6000_percentage

# 获取 Lux 值
curl http://temt6000-sensor.local/sensor/temt6000_lux
```

### 4. UDP 广播测试

使用 Python 脚本监听：

```python
import socket
import json

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(("0.0.0.0", 8888))

print("等待 UDP 广播...")
while True:
    data, addr = sock.recvfrom(1024)
    msg = json.loads(data.decode())
    print(f"[{addr[0]}] 光照: {msg['percentage']:.1f}%, {msg['lux']:.1f} lx")
```

---

## 常见问题

### 1. 找不到串口

**原因**：
- 未安装 USB 转 UART 驱动（CH340/CP2102）

**解决**：
- 下载驱动：https://www.wch.cn/downloads/CH341SER_EXE.html

### 2. 烧录失败："Failed to connect"

**解决**：
1. 按住 ESP32-C3 的 **BOOT 按钮**
2. 点击 **RST 按钮** 复位
3. 松开 RST，保持 BOOT 按住
4. 开始烧录
5. 烧录开始后松开 BOOT

### 3. WiFi 连接失败

**检查**：
- `secrets.yaml` 中 `wifi_ssid` 和 `wifi_password` 是否正确
- WiFi 是否为 2.4GHz（ESP32 不支持 5GHz）

**备用方案**：
设备会自动创建热点：
- SSID: `TEMT6000-Sensor`
- 密码: `12345678`

连接后访问 `http://192.168.4.1` 配置 WiFi


## 硬件接线

```
ESP32-C3 3.3V  → TEMT6000 VCC (V)
ESP32-C3 GND   → TEMT6000 GND (G)
ESP32-C3 GPIO3 ← TEMT6000 OUT (S)
```

---

## 固件版本信息

- **设备名称**：temt6000-sensor
- **芯片型号**：ESP32-C3 (AirM2M CORE)
- **Flash 使用**：61.1% (1,120,528 / 1,835,008 字节)
- **RAM 使用**：11.3% (36,920 / 327,680 字节)
- **编译日期**：2025-12-11 17:43:16
- **ESPHome 版本**：2025.9.1

---

## 进阶功能

### 修改 UDP 端口

编辑 `temt6000-esp32c3.yaml`，修改：
```yaml
udp:
  id: udp_broadcast
  port: 9999  # 改为新端口
```

然后重新编译上传。

### 调整广播频率

传感器每秒更新一次，如需降低频率，修改：
```yaml
sensor:
  - platform: template
    name: "TEMT6000 Percentage"
    update_interval: 5s  # 改为 5 秒
```

### 添加 MQTT 支持

如果需要 MQTT，在配置中添加：
```yaml
mqtt:
  broker: 192.168.1.100
  port: 1883
  username: !secret mqtt_user
  password: !secret mqtt_password
```

---

**祝烧录顺利！** 🚀
