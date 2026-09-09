@echo off
rem 静默启动(无黑框): 用pythonw后台跑, 或直接调exe
cd /d "%~dp0"
if exist "宿舍温湿度管家.exe" (
  start "" "宿舍温湿度管家.exe"
) else (
  start "" "D:\AI-Env\web-automation\.venv\Scripts\pythonw.exe" "%~dp0app.py"
)
exit
