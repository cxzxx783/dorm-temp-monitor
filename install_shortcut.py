# -*- coding: utf-8 -*-
"""创建/更新桌面快捷方式 -> 指向本文件夹里的exe"""
import os
from win32com.client import Dispatch

BASE = os.path.dirname(os.path.abspath(__file__))
DESKTOP = os.path.join(os.path.expanduser("~"), "Desktop")

def main():
    exe = os.path.join(BASE, "宿舍温湿度管家.exe")
    if not os.path.exists(exe):
        print("! 未找到 exe, 请先打包"); return
    shell = Dispatch("WScript.Shell")
    lnk = os.path.join(DESKTOP, "宿舍温湿度管家.lnk")
    sc = shell.CreateShortcut(lnk)
    sc.TargetPath = exe
    sc.WorkingDirectory = BASE
    sc.Description = "宿舍温湿度管家 - 小米温湿度计3mini记录器"
    sc.Save()
    print("快捷方式 ->", exe)

if __name__ == "__main__":
    main()
