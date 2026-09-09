# -*- coding: utf-8 -*-
"""
小米温湿度计3mini 蓝牙采集核心(独立线程) v1.1
特性:
- 记住设备MAC, 断开后用地址直接重连(不依赖广播, 掉线秒回)
- 若MAC连接失败再回退到扫描设备名
- 跨天自动切换到新CSV文件
- 保持连接期间持续订阅notify+主动读取(保活)
- 连接存活时间统计
"""
import csv, datetime, os, threading, time, asyncio, collections
from bleak import BleakScanner, BleakClient
from paths import data_dir, load_saved_mac, save_mac

DEFAULT_LOG_DIR = data_dir()

class Sensor(threading.Thread):
    TARGET = None
    DATA_CHAR = "ebe0ccc1-7a0a-4b0c-8a1a-6ff2997da3a6"

    def __init__(self, device_name="MJWSD06MMC", mac=None, interval=30.0,
                 log_dir=DEFAULT_LOG_DIR, on_event=None):
        super().__init__(daemon=True)
        self.device_name = device_name
        # 优先显式传入, 其次读上次保存的MAC(隐私: 不入代码)
        mac = mac or load_saved_mac()
        self.mac = (mac or "").upper()
        self.interval = interval
        self.log_dir = log_dir
        self.on_event = on_event or (lambda *a, **k: None)
        self._stop = threading.Event()
        self._state = {"status": "idle", "addr": None, "rssi": None,
                       "last": None, "count": 0, "connected": False,
                       "session_start": None, "lost": 0, "csv": None}
        self._lock = threading.Lock()
        self._csv_path = None
        self._csv_day = None
        self._ms_hist = collections.deque(maxlen=600)   # 延迟毫秒历史
        self._ever_connected = False                    # 本次进程是否曾连上

    # ---------- 状态读取(供UI轮询) ----------
    def snapshot(self):
        with self._lock:
            st = dict(self._state)
            st["ms_hist"] = list(self._ms_hist)
            return st

    def set_interval(self, seconds):
        self.interval = max(1.0, float(seconds))

    def stop(self):
        self._stop.set()

    # ---------- 内部 ----------
    def _set(self, **kw):
        with self._lock:
            self._state.update(kw)
        self.on_event(kw)

    def _log(self, msg):
        self.on_event({"status": "log", "msg": msg})

    def run(self):
        while not self._stop.is_set():
            try:
                self._session()
            except asyncio.CancelledError:
                break
            except Exception as e:
                self._log(f"会话异常: {e}")
            if self._stop.is_set():
                return
            was_connected = self._ever_connected
            self._set(connected=False, status="reconnecting")
            # 掉线找回计数: 曾连上过但现在掉线 -> lost+1
            if was_connected:
                with self._lock:
                    self._state["lost"] = self._state.get("lost", 0) + 1
            # 快速重连(共30秒, 0.5s粒度)
            for _ in range(60):
                if self._stop.is_set():
                    return
                time.sleep(0.5)

    def _session(self):
        addr = self._locate()
        if not addr:
            self._log("找不到设备, 继续努力尝试中...")
            return

        now = datetime.date.today()
        self._csv_day = now
        self._csv_path = os.path.join(self.log_dir, f"temp_log_{now}.csv")
        os.makedirs(self.log_dir, exist_ok=True)
        with self._lock:
            self._state["csv"] = self._csv_path

        asyncio.run(self._connected(addr))

    def _locate(self):
        """优先用记住的MAC直连, 失败再扫设备名"""
        async def try_mac(mac):
            async with BleakClient(mac, timeout=10.0) as c:
                if c.is_connected:
                    self._set(status="found", addr=mac, rssi=None)
                    self._log(f"用记忆的MAC直连成功 {mac}")
                    return mac
            return None

        async def scan():
            devices = await BleakScanner.discover(timeout=8.0, return_adv=True)
            for a, (dev, adv) in devices.items():
                if (dev.name or "") == self.device_name:
                    self._set(status="found", addr=a, rssi=adv.rssi)
                    self._log(f"扫描找到 {self.device_name} ({a}) RSSI {adv.rssi}")
                    if not self.mac or self.mac != a:
                        self.mac = a
                        save_mac(a)   # 自动记忆, 下次秒连
                    return a
            return None

        def run_attempt():
            loop = asyncio.new_event_loop()
            try:
                if self.mac:
                    try:
                        r = loop.run_until_complete(try_mac(self.mac))
                        if r: return r
                    except Exception as e:
                        self._log(f"MAC直连失败({e}), 改扫描...")
                return loop.run_until_complete(scan())
            finally:
                loop.close()

        self._set(status="waiting")
        self._log(f"尝试连接 {self.mac or self.device_name} ...")
        r = run_attempt()
        if r:
            return r
        self._log("暂未连上, 正在轮询(请确认温度计已按过侧键且距离在5米内)...")
        # 轮询最多120秒, 每分钟扫一次+每10秒MAC直连一次
        deadline = time.time() + 120
        while not self._stop.is_set() and time.time() < deadline:
            r = run_attempt()
            if r:
                return r
            for _ in range(10):
                if self._stop.is_set():
                    return None
                time.sleep(1.0)
        return None

    async def _connected(self, addr):
        stop_ev = self._stop
        self._set(status="connecting", addr=addr)
        self._log(f"连接建立 {addr}")
        session_start = datetime.datetime.now()
        async with BleakClient(addr, timeout=20.0) as client:
            self._ever_connected = True
            self._set(connected=True, status="connected",
                      session_start=session_start.strftime("%Y-%m-%d %H:%M:%S"))
            self._log("已连接! 开始持续采集 (断开后会自动找回)")
            newest = {"v": None}

            def on_data(_, data):
                v = parse(bytes(data))
                if v:
                    newest["v"] = v

            try:
                await client.start_notify(self.DATA_CHAR, on_data)
            except Exception:
                pass

            last_rssi_refresh = time.time() - 61   # 首次进入循环立即刷一次RSSI
            while not stop_ev.is_set():
                # 定期刷新信号强度RSSI(连接期间设备停止广播, 扫描常失败)
                if time.time() - last_rssi_refresh >= 60:
                    last_rssi_refresh = time.time()
                    try:
                        rssi_dev = await BleakScanner.find_device_by_address(
                            addr, timeout=2.0)
                        if rssi_dev and rssi_dev.rssi is not None:
                            with self._lock:
                                self._state["rssi"] = rssi_dev.rssi
                        else:
                            # 扫不到=设备停广播, RSSI不可用, 置None(前端回退到延迟ms)
                            with self._lock:
                                self._state["rssi"] = None
                    except Exception:
                        with self._lock:
                            self._state["rssi"] = None
                # 数据轮询(优先通知缓存, 再主动读保活)
                v = newest.get("v")
                try:
                    t0 = time.perf_counter()
                    raw = await client.read_gatt_char(self.DATA_CHAR)
                    got = parse(bytes(raw))
                    if got:
                        v = got
                    _ms = int((time.perf_counter() - t0) * 1000)
                    with self._lock:
                        self._state["read_ms"] = _ms
                    self._ms_hist.append({"_t": time.time(), "_v": _ms})
                except Exception:
                    if not client.is_connected:
                        break
                if v:
                    self._record(v, newest)
                    newest.clear()
                for _ in range(max(1, int(self.interval * 2))):
                    if stop_ev.is_set() or not client.is_connected:
                        return
                    await asyncio.sleep(0.5)

    def _record(self, v, newest):
        ts = datetime.datetime.now()
        # 跨天切换CSV
        if ts.date() != self._csv_day:
            self._csv_day = ts.date()
            self._csv_path = os.path.join(self.log_dir, f"temp_log_{ts.date()}.csv")
            with self._lock:
                self._state["csv"] = self._csv_path
        row = [ts.strftime("%Y-%m-%d %H:%M:%S"), round(v[0],1), v[1], round(v[2],3)]
        new = not os.path.exists(self._csv_path)
        try:
            # Excel 打开文件会加锁 -> 写失败不能crash会话(否则无限重连风暴), 跳过本轮即可
            with open(self._csv_path, "a", encoding="utf-8-sig", newline="") as f:
                w = csv.writer(f)
                if new:
                    w.writerow(["时间","温度℃","湿度%","电压V"])
                w.writerow(row)
        except PermissionError:
            self._log(f"CSV写入被占用(可能在Excel中打开), 本轮跳过: {self._csv_path}")
        except Exception as e:
            self._log(f"CSV写入失败: {e}")
        with self._lock:
            self._state["last"] = {"ts": ts.strftime("%H:%M:%S"),
                                   "temp": v[0], "hum": v[1], "volt": v[2]}
            self._state["count"] += 1
        self.on_event({"status": "data", "row": row})


def parse(data: bytes):
    """小端解析: 温度2字节有符号int16/100, 湿度1字节, 电压2字节/1000"""
    if len(data) >= 5:
        temp = int.from_bytes(data[0:2], "little", signed=True) / 100.0   # 有符号! 支持负温
        hum = data[2]
        volt = int.from_bytes(data[3:5], "little") / 1000.0
        if -40 <= temp < 60 and 0 <= hum <= 100 and 1.0 < volt < 4.0:
            return temp, hum, volt
    return None