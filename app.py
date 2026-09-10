# -*- coding: utf-8 -*-
"""
宿舍温湿度管家 - 桌面版 v1.2
- 历史数据跨天留存, 启动自动加载, 日期切换查看
- 实时采集 + 界面秒级刷新
- 信号强度: 连接RSSI + 读取延迟毫秒
运行: python app.py  (或打包后的exe)
"""
import os, threading, datetime
import webview
from sensor import Sensor, DEFAULT_LOG_DIR
from paths import resource_dir, app_dir, load_saved_mac
import history as hist

DEVICE_NAME = "MJWSD06MMC"         # 温湿度计型号名
DEVICE_MAC = load_saved_mac()      # 本地记忆(隐私不入代码)
DATA_DIR = DEFAULT_LOG_DIR

class Api:
    def __init__(self):
        self.live = []              # 本次运行的实时点(防重)
        self._lock = threading.Lock()
        self._window = None
        self.sensor = Sensor(device_name=DEVICE_NAME, mac=DEVICE_MAC,
                             interval=6.0, log_dir=DATA_DIR,   # 默认6秒(用户喜欢)
                             on_event=self._on_event)

    def set_window(self, w):
        self._window = w

    def _on_event(self, ev):
        if ev.get("status") == "data":
            row = ev["row"]
            try:
                epoch = datetime.datetime.strptime(row[0], "%Y-%m-%d %H:%M:%S").timestamp()
            except Exception:
                return
            with self._lock:
                self.live.append({"t": epoch, "temp": float(row[1]), "hum": float(row[2])})
                if len(self.live) > 20000:
                    del self.live[: len(self.live) - 20000]

    # ============ 界面接口 ============

    def get_snapshot(self):
        st = self.sensor.snapshot()
        last = st.get("last")
        uptime = None
        if st.get("session_start"):
            try:
                # 完整时间戳(含日期), 跨零点也正确
                s0 = datetime.datetime.strptime(st["session_start"], "%Y-%m-%d %H:%M:%S")
                uptime = int((datetime.datetime.now() - s0).total_seconds())
            except ValueError:
                # 兼容旧格式(仅时间)
                try:
                    s0 = datetime.datetime.strptime(st["session_start"], "%H:%M:%S")
                    now = datetime.datetime.now()
                    s0 = s0.replace(year=now.year, month=now.month, day=now.day)
                    uptime = int((now - s0).total_seconds())
                except Exception:
                    pass
            except Exception:
                pass
        return {
            "status": st.get("status"),
            "connected": st.get("connected"),
            "addr": st.get("addr"),
            "rssi": st.get("rssi"),
            "read_ms": st.get("read_ms"),
            "count": st.get("count", 0),
            "lost": st.get("lost", 0),
            "last": last,
            "interval": self.sensor.interval,
            "uptime": uptime,
            "csv": st.get("csv"),
            "ms_hist": st.get("ms_hist", []),
        }

    def get_days(self):
        """可用历史日期列表(倒序)"""
        return hist.list_days(DATA_DIR)

    def get_day(self, day):
        """某天全部记录点"""
        return hist.load_day(DATA_DIR, day)

    def get_day_stats(self, day):
        return hist.day_stats(self.get_day(day))

    def get_live(self):
        """本次运行的全部点"""
        with self._lock:
            return list(self.live)

    def get_week(self):
        """近7天每日统计(含空缺天)"""
        return self.range_days(7)

    def range_days(self, n):
        """近n天每日统计(含空缺天)"""
        today = datetime.date.today()
        out = []
        for i in range(n - 1, -1, -1):
            d = (today - datetime.timedelta(days=i)).strftime("%Y-%m-%d")
            st = hist.day_stats(hist.load_day(DATA_DIR, d))
            out.append({"day": d[5:], "avg": st["avg"] if st else None,
                        "count": st["count"] if st else 0})
        return out

    def get_range(self, days, end=None):
        """合并最近N天(止于end)的全部记录点, 供跨天曲线绘制
        get_range(days=30) -> 近30天全部点(含今天)
        get_range(days=30, end='2026-09-09') -> 截至指定日的近30天
        """
        today = datetime.date.today()
        if end:
            try:
                today = datetime.datetime.strptime(end, "%Y-%m-%d").date()
            except Exception:
                pass
        start = today - datetime.timedelta(days=days - 1)
        points = []
        d = start
        while d <= today:
            day = d.strftime("%Y-%m-%d")
            points.extend(hist.load_day(DATA_DIR, day))
            d += datetime.timedelta(days=1)
        return points

    def get_range_stats(self, days):
        pts = self.get_range(days)
        return hist.day_stats(pts)

    def get_hours(self, n=24):
        """真·最近n小时的全部点(跨天裁剪正确): 基于当前时间回退n小时"""
        now = datetime.datetime.now()
        start_ts = now.timestamp() - n * 3600
        # 覆盖天数随请求时长动态计算(自定义最长120小时, 不能再硬编码3天)
        days = min(31, int(n // 24) + 2)   # +2 覆盖跨零点边界
        pts = self.get_range(days)
        return [x for x in pts if x["t"] >= start_ts - 1]  # -1s容差

    def get_between(self, start, end):
        """自定义起止时间段的全部记录点(含首尾)
        支持两种格式:
          - '2026-09-09'                整日
          - '2026-09-09 13:00'          精确到分钟
        """
        def parse_between(v):
            v = str(v).strip().replace('T', ' ')   # datetime-local 兼容: 2026-09-09T13:00
            for fmt in ("%Y-%m-%d %H:%M", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
                try:
                    return datetime.datetime.strptime(v, fmt)
                except Exception:
                    continue
            return None
        d = parse_between(start)
        e = parse_between(end)
        if not d or not e:
            return []
        if d > e:
            d, e = e, d
        # 是否含时间(带分钟) -> 决定结束时刻是否覆盖整天
        has_time = (d.hour or d.minute or e.hour or e.minute) != 0
        s_ts = d.timestamp()
        e_ts = e.timestamp() + 86399 if not has_time else e.timestamp()
        points = []
        day = d.date()
        while day <= e.date():
            points.extend(hist.load_day(DATA_DIR, day.strftime("%Y-%m-%d")))
            day += datetime.timedelta(days=1)
        return [x for x in points if s_ts - 1 <= x["t"] <= e_ts + 1]

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

    def quit(self):
        self.sensor.stop()
        if self._window:
            self._window.destroy()

    def _restart_sensor(self):
        old = self.sensor
        old.stop()
        # join 旧线程(限时3秒): 避免旧线程卡在阻塞扫描里与新线程抢BLE
        if old.is_alive():
            old.join(timeout=3.0)
        self.sensor = Sensor(device_name=DEVICE_NAME, mac=DEVICE_MAC,
                             interval=old.interval or 6.0,
                             log_dir=DATA_DIR, on_event=self._on_event)
        self.sensor.start()

def main():
    base = resource_dir()
    api = Api()
    window = webview.create_window(
        "宿舍温湿度管家",
        os.path.join(base, "index.html"),
        width=1280, height=860, min_size=(720, 520),   # 默认大屏舒展, 可拉小到半屏
        js_api=api, background_color="#04060f")
    api.set_window(window)
    webview.start(gui="edgechromium")

if __name__ == "__main__":
    main()