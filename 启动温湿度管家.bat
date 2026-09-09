@echo off
chcp 65001 >nul
cd /d "%~dp0"
title 宿舍温湿度管家
echo ============================================
echo    宿舍温湿度管家  v1.0
echo    启动后请按一下温度计侧边按键唤醒蓝牙
echo ============================================
echo.
"D:\AI-Env\web-automation\.venv\Scripts\python.exe" app.py
pause