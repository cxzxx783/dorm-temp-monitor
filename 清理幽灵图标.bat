@echo off
chcp 65001 >nul
title 清理桌面图标缓存(刷新残留图标)
echo ============================================
echo   清理 Windows 图标缓存 (用于移除
echo   "看得见但打不开/删不掉"的幽灵图标)
echo ============================================
echo.
echo 步骤1: 结束资源管理器(桌面会闪一下, 正常)
taskkill /f /im explorer.exe >nul 2>&1
echo 步骤2: 删除图标缓存
del /f /q "%LOCALAPPDATA%\IconCache.db" >nul 2>&1
del /f /q "%LOCALAPPDATA%\Microsoft\Windows\Explorer\iconcache_*.db" >nul 2>&1
echo 步骤3: 重启资源管理器
start explorer.exe
echo.
echo 完成! 桌面图标已刷新, 幽灵图标应消失.
echo 若个别图标仍在, 重启电脑即可彻底清掉.
pause