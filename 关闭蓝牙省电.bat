@echo off
chcp 65001 >nul
net session >nul 2>&1
if %errorlevel% neq 0 (
  echo 需要管理员权限运行. 请右键本文件选择"以管理员身份运行".
  pause
  exit /b
)

echo ============================================
echo   关闭蓝牙省电策略 (让连接更持久)
echo --------------------------------------------
echo   原理: Windows 会在一段时间后断开
echo   空闲的蓝牙设备连接来省电.
echo   关闭后, 温湿度计连接应答更持久.
echo ============================================
echo.

:: 关闭蓝牙无线电的电源管理(Ultimate/High/Balanced 各电源方案)
powercfg /setdcvalueindex SCHEME_CURRENT 19cbb8fa-5279-450e-9fac-8a3d5fedd0c1 00000000-0000-0000-0000-000000000000 1 >nul 2>&1
powercfg /setacvalueindex SCHEME_CURRENT 19cbb8fa-5279-450e-9fac-8a3d5fedd0c1 00000000-0000-0000-0000-000000000000 1 >nul 2>&1

:: 关闭 USB 选择性暂停(蓝牙适配器常走USB)
powercfg /setacvalueindex SCHEME_CURRENT 2a737441-1930-4402-8d77-b2bebba308a3 48e6b7a6-50f5-4782-a5d4-53bb8f07e226 1 >nul 2>&1
powercfg /setdcvalueindex SCHEME_CURRENT 2a737441-1930-4402-8d77-b2bebba308a3 48e6b7a6-50f5-4782-a5d4-53bb8f07e226 1 >nul 2>&1
powercfg /setacvalueindex SCHEME_CURRENT SCHEME_CURRENT 2a737441-1930-4402-8d77-b2bebba308a3 48e6b7a6-50f5-4782-a5d4-53bb8f07e226 0 >nul 2>&1

echo 已尝试关闭蓝牙省电 + USB选择性暂停.
echo.
echo 提示: 若想 24 小时不睡, 建议再把系统电源改成
echo "从不休眠" (设置-电源-屏幕和睡眠).
pause