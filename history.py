# -*- coding: utf-8 -*-
"""历史数据管理: 读取所有天的CSV, 按天查询/统计"""
import csv, os, glob, datetime

def list_days(log_dir):
    """返回所有有记录的天, 倒序: ['2026-09-09', ...]"""
    days = []
    for f in glob.glob(os.path.join(log_dir, "temp_log_*.csv")):
        name = os.path.basename(f)
        try:
            day = name[len("temp_log_"):-4]
            datetime.datetime.strptime(day, "%Y-%m-%d")
            days.append(day)
        except Exception:
            continue
    return sorted(days, reverse=True)

def load_day(log_dir, day):
    """加载某天全部记录: [{t:epoch, temp, hum}, ...]"""
    f = os.path.join(log_dir, f"temp_log_{day}.csv")
    if not os.path.exists(f):
        return []
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
    return out

def day_stats(points):
    if not points:
        return None
    temps = [p["temp"] for p in points]
    hums = [p["hum"] for p in points]
    tmax = max(temps); tmin = min(temps)
    def clock(ts):
        d = datetime.datetime.fromtimestamp(ts)
        return f"{d:%H:%M}"
    return {"count": len(points),
            "avg": round(sum(temps)/len(temps), 1),
            "tmax": round(tmax, 1), "tmax_at": clock(points[temps.index(tmax)]["t"]),
            "tmin": round(tmin, 1), "tmin_at": clock(points[temps.index(tmin)]["t"]),
            "havg": round(sum(hums)/len(hums), 1),
            "hmax": round(max(hums), 1), "hmin": round(min(hums), 1)}