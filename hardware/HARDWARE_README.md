# ESP32-C3 × TEMT6000 集成版 PCB 硬件设计

本目录是 `auto_display_light` 项目的**硬件设计部分**，提供「集成版 PCB」方案——将 TEMT6000 光敏传感器直接集成到 ESP32-C3 最小系统板上，无需外接杜邦线和独立传感器模块。

> **两种硬件方案对比**
> - **方案 A（主仓库默认）**：ESP32-C3 开发板 + TEMT6000 模块 + 杜邦线连接（接线见[主 README 硬件接线](../README.md#硬件接线)）
> - **方案 B（本目录）**：集成版 PCB，TEMT6000 直接焊在 ESP32-C3 最小系统板上，更小体积、更便携

本目录即方案 B 的完整硬件设计文件。历时一个月自制，相关制造与调试全流程记录见下方各章节。

---

## 硬件设计

基于 [嘉立创开源硬件](https://oshwhub.com/) 上的 ESP32-C3 最小系统板修改，自主添加 TEMT6000 光传感器部分。

### 关键设计点

| 模块 | 设计说明 |
|------|----------|
| **供电** | USB 5V → LDO（SOT-23 封装）→ 3.3V，给单片机供电 |
| **电源滤波** | 电源引脚增加 10μF / 100nF 滤波电容；模拟电源引脚增加 10μF / 10nF / 1μF 滤波 |
| **晶振** | 40MHz，附近增加 12pF 滤波电容才能正常工作 |
| **USB** | GPIO18 / GPIO19 对应 USB D+ / D-，连接到 Type-C 接口 |
| **使能引脚（EN）** | 上拉电阻拉到 3.3V 保持高电平（工作状态）；按下按钮拉到 GND，上拉电阻限制电流防止烧坏引脚 |
| **BOOT（GPIO9）** | 默认高电平，同样接开关，按下后拉到 0V |
| **TX/RX 指示灯** | TX/RX 引脚电压变化时形成电压差，电流流动点亮 LED，用于判断工作状态 |
| **射频天线** | 连接 WiFi / 蓝牙，使用 π 匹配走线 |
| **光传感器** | GPIO3 连接 TEMT6000，读取电压数据判断光照强度（与主仓库 esp32c3.yaml 引脚一致） |

### TEMT6000 光传感器

> ⚠️ 电子设计一定要查阅官方 datasheet，很多东西 AI 并不清楚，必须亲自确认。

- **引脚定义**（查 datasheet 后确认）：1 号、2 号引脚为发射极，3 号引脚为集电极
- **工作原理**：受光照时内部导通 → 接地拉低电压 → GPIO3 感知电压变化
- **第一版教训**：未查 datasheet，被 AI 误导，发射极/集电极接反，导致电路设计错误、无法读取数据。第二版修正后成功。

---

## 焊接工艺

### Type-C 焊接

Type-C 引脚极细，锡浆涂多了会导致中间数据引脚连锡、功能失效。

**方法：**
1. 先涂锡浆，**不放元器件**
2. 加热至锡浆熔化，检查是否连锡
3. 若连锡，趁锡浆熔化时用镊子挑下多余锡浆
4. 确保无连锡后，再放上 Type-C 模块
5. 放上后**用镊子压住引脚**，确保与锡充分接触

### QFN8 芯片焊接

ESP32-C3 采用 QFN-8 封装，底部焊盘 + 四周小引脚。比 Type-C 稍容易，但失败后难排查。

**方法：** 用镊子按住芯片加热，确保完全接触下面的锡。

---

## 调试过程

第二版板子焊好后 LED 不亮、电脑不识别 USB，排查过程：

| 步骤 | 现象 | 判断 |
|------|------|------|
| 检查供电 | 所有供电引脚正常 | 排除供电问题 |
| 怀疑晶振 | 按标准设计 | 排除 |
| 测 TX 引脚电压 | 稳定在 **2.15V** | 正常应为 0V 或 3.3V，2.15V 说明芯片未运行、引脚浮空 |
| 测 IO8/IO9 对地电阻 | 33kΩ | 正常 |
| 重新加热芯片 + 镊子按压 | 电脑识别 USB 但报「设备有问题，已停止」 | 焊接有所改善但仍异常 |
| **更换芯片** | ✅ 成功识别、正常工作 | 原芯片失效 |

> 结论：遇到「设备有问题，已停止」且焊接无问题时，换一颗芯片往往能解决。

---

## 使用方法

1. **下单 PCB**：将 `gerber/` 目录打包发给板厂（如嘉立创）下单
2. **焊接元器件**：参考上方焊接工艺章节
3. **烧录固件**：使用主仓库的 `esp32c3.yaml` 编译固件并烧录（[烧录方法见主 README](../README.md#方法-1esphome-自动上传最简单)）
4. **配置联网**：ESPHome 配置 WiFi，板子直接联网
5. **查看数据**：浏览器打开 `http://temt6000-sensor.local` 即可看到光敏传感器实时数据
6. **自动调光**：配合主仓库的 `AutoDisplayLight.exe` 实现自动调光

---

## 目录结构

```
hardware/
├── gerber/                # PCB 制造文件（可直接发给板厂下单）
│   ├── Gerber_TopLayer.GTL
│   ├── Gerber_BottomLayer.GBL
│   ├── Gerber_TopSilkscreenLayer.GTO
│   ├── Gerber_BottomSilkscreenLayer.GBO
│   ├── Gerber_TopSolderMaskLayer.GTS
│   ├── Gerber_BottomSolderMaskLayer.GBS
│   ├── Gerber_TopPasteMaskLayer.GTP
│   ├── Gerber_TopAssemblyLayer.GTA
│   ├── Gerber_BoardOutlineLayer.GKO
│   ├── Gerber_DocumentLayer.GDL
│   ├── Gerber_DrillDrawingLayer.GDD
│   ├── Drill_PTH_Through.DRL
│   ├── Drill_NPTH_Through.DRL
│   ├── Drill_PTH_Through_Via.DRL
│   ├── FlyingProbeTesting.json
│   └── PCB下单说明.txt
├── project/               # 嘉立创 EDA 工程源文件
│   └── ProPrj_ESP32C3超小版_liuweiqing.epro2
└── HARDWARE_README.md     # 本文档
```

### PCB 下单

`gerber/` 目录下的文件可直接打包发给 PCB 板厂（如嘉立创）下单。
下单说明见 `gerber/PCB下单说明.txt`，或参考 [嘉立创下单文档](https://prodocs.lceda.cn/cn/pcb/order-order-pcb/index.html)。

### 工程文件

`project/ProPrj_ESP32C3超小版_liuweiqing.epro2` 为嘉立创 EDA 专业版工程文件，可用嘉立创 EDA 打开编辑原理图与 PCB。

---

## 开发心得

- **焊接工艺**：Type-C 和 QFN8 贴片焊接的实操技巧
- **调试方法**：用万用表测电压、测对地电阻来定位问题
- **查阅文档**：电子设计一定要查官方 datasheet，不要轻信 AI
- **不要轻言放弃**：多试几次，换芯片也能解决疑难问题

---

## 致谢

基于嘉立创开源硬件上的 ESP32-C3 最小系统板修改而成，感谢原作者的开源设计。
