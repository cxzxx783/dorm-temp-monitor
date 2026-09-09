@echo off
chcp 65001 >nul
title 卸载 - 宿舍温湿度管家

echo ============================================
echo   即将卸载「宿舍温湿度管家」
echo   将删除: 本文件夹全部内容(含记录数据) + 桌面快捷方式
echo ============================================
echo.
set /p confirm=确认删除? 输入 yes 回车执行, 其他任意键取消:
if /i not "%confirm%"=="yes" (
  echo 已取消, 未删除任何东西.
  pause
  exit /b
)

echo.
echo 正在关闭运行中的软件...
taskkill /f /im python.exe >nul 2>&1

echo 正在删除桌面快捷方式...
del "%USERPROFILE%\Desktop\宿舍温湿度管家.lnk" >nul 2>&1

echo 正在删除软件文件夹...
cd /d "%TEMP%"
start "" /b cmd /c "timeout /t 2 >nul & rd /s /q ""%~dp0"""

echo 已在后台执行删除, 稍后本文件夹会自动消失.
echo 若还有残留, 手动删除此文件夹即可.
pause