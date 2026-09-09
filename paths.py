# -*- coding: utf-8 -*-
"""路径管理: 兼容源码运行与 PyInstaller 打包(exe)两种情况"""
import os, sys

def is_frozen():
    return getattr(sys, "frozen", False)

def app_dir():
    """程序主目录(源码=脚本目录, exe=exe所在目录)"""
    if is_frozen():
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))

def resource_dir():
    """只读资源目录(打包后为解压临时目录)"""
    if is_frozen():
        return sys._MEIPASS
    return os.path.dirname(os.path.abspath(__file__))

def data_dir():
    """数据目录(始终在app目录旁边, 方便一起搬运/删除)"""
    d = os.path.join(app_dir(), "data")
    os.makedirs(d, exist_ok=True)
    return d

def mac_file():
    return os.path.join(app_dir(), "data", "device_mac.txt")

def load_saved_mac():
    try:
        if os.path.exists(mac_file()):
            with open(mac_file(), "r", encoding="utf-8") as f:
                m = f.read().strip().upper()
                if m:
                    return m
    except Exception:
        pass
    return None

def save_mac(mac):
    try:
        os.makedirs(os.path.dirname(mac_file()), exist_ok=True)
        with open(mac_file(), "w", encoding="utf-8") as f:
            f.write(mac.strip().upper())
    except Exception:
        pass