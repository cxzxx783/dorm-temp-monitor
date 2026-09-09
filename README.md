# 宿舍温湿度管家 (Dorm Temp Monitor)

一个 Windows 桌面软件，通过电脑自带蓝牙直读 **小米温湿度计 3 mini**（`MJWSD06MMC`）的实时温湿度，自动不间断记录，实时绘制温度/湿度曲线。**无需小米网关、无需米家云、数据不出本机**，明文协议免绑定。

## ✨ 功能

- 🌡️ 实时温度 + 湿度双曲线（ECharts 深空霓虹主题）
- 📅 **时间范围切换**：近24小时 / 近7天 / 近30天 / 自定义起止日期
- 🧩 **可拖拽部件化布局**：面板自由移动/缩放/开关，布局自动记忆（gridstack）
- 🗂️ **历史跨天留存**：每天一个 CSV，重启自动加载，日期回看
- 📊 范围统计：平均/极差/最高最低/时刻/样本/活跃天数
- 🔋 电池三档警示：充足(≥3V) / 偏低⚠(2.7-3) / 需更换(<2.7)
- 📶 信号强度(RSSI 四格) + 读取延迟(ms)
- 😊 舒适度表情 + 近7天/近30天日均温概览
- ⚙️ 采样间隔可调 6s~5min，掉线自动记忆MAC找回，跨天自动切文件
- 💻 深空渐变 + 星点 + 霓虹辉光玻璃拟态界面，可缩半屏

## 🚀 快速开始

1. 需求：Windows 10/11、本机蓝牙、小米温湿度计 3 mini
2. 源码运行：`pip install bleak pywebview` → `python app.py`
3. 打包 exe：`python -m PyInstaller --onefile --windowed --add-data "index.html;." --add-data "assets;assets" --collect-all webview --hidden-import webview.platforms.edgechromium app.py`
4. 双击 exe（或桌面对应快捷方式）→ **按一下温度计侧键**唤醒 → 连接成功自动持续采集

> 温度计平时省电休眠，每次电脑重启/软件重开时需要按一次侧键唤醒建立首次连接，之后持续采集不断线。

## 📂 数据文件

`data/temp_log_YYYY-MM-DD.csv`（每天一个，UTF-8，可用Excel打开），格式：`时间,温度℃,湿度%,电压V`

## 🔍 工作原理

- BLE 扫描识别设备名 `MJWSD06MMC`（小米 MiBeacon 协议），首次连接自动记忆 MAC 到本地 `data/device_mac.txt`
- 连接后同时**订阅通知（每6秒推）**与**定时主动读取**（保活+双保险），掉线用记忆MAC直连找回
- 特征 `ebe0ccc1-7a0a-4b0c-8a1a-6ff2997da3a6`，数据5字节小端：温度(2B÷100)+湿度(1B)+电压(2B÷1000)

## 📁 项目结构

```
app.py          主程序(pywebview 窗口 + 前后端桥接 + 范围聚合接口)
sensor.py       蓝牙采集核心(独立线程, 自动重连, 跨天切文件)
history.py      历史数据按天读取/统计
paths.py        兼容源码与打包的路径管理
index.html      部件化界面(ECharts + gridstack)
assets/         echarts.min.js + gridstack-all.js/css
data/           记录输出(不入库)
install_shortcut.py  创建桌面快捷方式
启动温湿度管家.bat    静默启动
卸载管家.bat          一键删除
关闭蓝牙省电.bat      管理员运行, 关系统蓝牙省电
```

## 🔒 隐私

数据全程本地保存，不上传任何云端；设备 MAC 自动记忆到本地文件，**仓库不含任何个人信息**。

## 📝 License

MIT
