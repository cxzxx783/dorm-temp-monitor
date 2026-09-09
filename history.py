# -*- coding: utf-8 -*-
"""历史数据管理: 读取所有天的CSV, 按天查询/统计
带 mtime 缓存: 文件没变就复用解析结果, 避免每30秒全量重读几十万行
"""
import csv, os, glob, datetime, time

# ---------- 简单缓存: 文件 mtime 变化才重新解析 ----------
_cache = {}     # key -> (mtime, result)

def _cache_get(key):
    """返回缓存值, 无/失效返回None"""
    ent = _cache.get(key)
    if not ent:
        return None
    mt, val = ent
    # mtime 与缓存一致才算有效(文件未变)
    if _mtime(key) == mt:
        return val
    return None

def _cache_put(key, val):
    _cache[key] = (_mtime(key), val)

def _mtime(path):
    try:
        return os.path.getmtime(path)
    except OSError:
        return 0

def _key_for(log_dir, day):
    f = os.path.join(log_dir, f"temp_log_{day}.csv")
    return f

def _list_cache(log_dir):
    key = ("days", log_dir)
    days = None
    # 目录是否有新文件: 用目录mtime不行, 直接扫描(glob很快)
    files = glob.glob(os.path.join(log_dir, "temp_log_*.csv"))
    entry = _cache.get(key)
    if entry and entry[0] == len(files):
        return entry[1]
    days = []
    for f in files:
        name = os.path.basename(f)
        try:
            day = name[len("temp_log_"):-4]
            datetime.datetime.strptime(day, "%Y-%m-%d")
            days.append(day)
        except Exception:
            continue
    days.sort(reverse=True)
    _cache[key] = (len(files), days)
    return days

def list_days(log_dir):
    """返回所有有记录的天, 倒序: ['2026-09-09', ...]"""
    return _list_cache(log_dir)

def load_day_points(log_dir, day):
    """真·读取某天全部点(带mtime缓存)"""
    f = os.path.join(log_dir, f"temp_log_{day}.csv")
    if not os.path.exists(f):
        return []
    hit = _cache_get(f)
    if hit is not None:
        return hit
    out = []
    try:
        with open(f, encoding="utf-8-sig") as fp:
            for row in csv.DictReader(fp):
                try:
                    t = datetime.datetime.strptime(row["时间"], "%Y-%m-%d %H:%M:%S").timestamp()
                    out.append({"t": t, "temp": float(row["温度℃"]),
                                "hum": float(row["湿度%"])})
                except Exception:
                    continue
    except Exception:
        pass
    _cache_put(f, out)
    return out

def load_day(log_dir, day):
    """加载某天全部记录(带缓存版本)"""
    return load_day_points(log_dir, day)

def day_stats(points):
    if not points:
        return None
    n = len(points)
    # 单点直接算, 避免无谓遍历
    if n == 1:
        p = points[0]
        def c(ts):
            return datetime.datetime.fromtimestamp(ts).strftime("%H:%M")
        return {"count": 1, "avg": round(p["temp"], 1),
                "tmax": round(p["temp"], 1), "tmax_at": c(p["t"]),
                "tmin": round(p["temp"], 1), "tmin_at": c(p["t"]),
                "havg": round(p["hum"], 1),
                "hmax": round(p["hum"], 1), "hmin": round(p["hum"], 1)}
    temps = [p["temp"] for p in points]
    hums = [p["hum"] for p in points]
    tmax = max(temps); tmin = min(temps)
    hmx = max(hums); hmn = min(hums)
    def clock(ts):
        d = datetime.datetime.fromtimestamp(ts)
        return f"{d:%H:%M}"
    # 平均值用一次遍历
    s_t = 0.0; s_h = 0.0
    for p in points:
        s_t += p["temp"]; s_h += p["hum"]
    return {"count": n,
            "avg": round(s_t / n, 1),
            "tmax": round(tmax, 1), "tmax_at": clock(points[temps.index(tmax)]["t"]),
            "tmin": round(tmin, 1), "tmin_at": clock(points[temps.index(tmin)]["t"]),
            "havg": round(s_h / n, 1),
            "hmax": round(hmx, 1), "hmin": round(hmn, 1)}