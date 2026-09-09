# -*- coding: utf-8 -*-
"""
宿舍温湿度管家 - 桌面版 v1.1
运行: python app.py
"""
import os, threading, datetime
import webview
from sensor import Sensor, DEFAULT_LOG_DIR
from paths import resource_dir, load_saved_mac

DEVICE_NAME = "MJWSD06MMC"         # 温湿度计型号名
DEVICE_MAC = load_saved_mac()      # 从本地记忆读取(隐私: 不入代码/不入库)
DATA_DIR = DEFAULT_LOG_DIR

class Api:
    def __init__(self):
        self.history = []
        self._lock = threading.Lock()
        self._window = None
        self._start_time = None
        self.sensor = Sensor(device_name=DEVICE_NAME, mac=DEVICE_MAC,
                             interval=30.0, log_dir=DATA_DIR,
                             on_event=self._on_event)

    def set_window(self, w):
        self._window = w

    def _on_event(self, ev):
        if ev.get("status") == "data":
            row = ev["row"]
            try:
                epoch = datetime.datetime.strptime(row[0], "%Y-%m-%d %H:%M:%S").timestamp()
            except Exception:
                epoch = datetime.datetime.now().timestamp()
            with self._lock:
                self.history.append({"t": epoch, "temp": float(row[1]), "hum": float(row[2])})
                if len(self.history) > 20000:
                    del self.history[: len(self.history) - 20000]

    def get_snapshot(self):
        st = self.sensor.snapshot()
        last = st.get("last")
        with self._lock:
            hist = self.history[-300:]
        temps = [p["temp"] for p in hist] or [0]
        hums = [p["hum"] for p in hist] or [0]
        def stat(vals):
            return {"avg": round(sum(vals)/len(vals), 1),
                    "max": round(max(vals), 1),
                    "min": round(min(vals), 1)}
        # 运行时长
        uptime = None
        if self.sensor._state.get("session_start"):
            try:
                st0 = datetime.datetime.strptime(
                    self.sensor._state["session_start"], "%H:%M:%S").replace(
                    year=datetime.date.today().year,
                    month=datetime.date.today().month,
                    day=datetime.date.today().day)
                uptime = int((datetime.datetime.now() - st0).total_seconds())
            except Exception:
                uptime = None
        return {
            "status": st.get("status"),
            "connected": st.get("connected"),
            "addr": st.get("addr"),
            "rssi": st.get("rssi"),
            "count": st.get("count", 0),
            "lost": st.get("lost", 0),
            "last": last,
            "interval": self.sensor.interval,
            "history": hist,
            "temp_stat": stat(temps),
            "hum_stat": stat(hums),
            "uptime": uptime,
            "csv": st.get("csv"),
        }

    def start(self):
        if not self.sensor.is_alive():
            self._restart_sensor()
        return "ok"

    def set_interval(self, seconds):
        self.sensor.set_interval(float(seconds))
        return "ok"

    def reconnect(self):
        self._restart_sensor()
        return "ok"

    def _restart_sensor(self):
        self.sensor.stop()
        self.sensor = Sensor(device_name=DEVICE_NAME, mac=DEVICE_MAC,
                             interval=self.sensor.interval or 30.0,
                             log_dir=DATA_DIR, on_event=self._on_event)
        self.sensor.start()

    def quit(self):
        self.sensor.stop()
        if self._window:
            self._window.destroy()

def main():
    base = resource_dir()   # 打包后自动指向解压资源目录
    api = Api()
    window = webview.create_window(
        "宿舍温湿度管家",
        os.path.join(base, "index.html"),
        width=1160, height=780, min_size=(1000, 680),
        js_api=api, background_color="#0a0e1a")
    api.set_window(window)
    webview.start(gui="edgechromium")

if __name__ == "__main__":
    main()