@echo off
chcp 65001 >nul
net session >nul 2>&1
if %errorlevel% neq 0 (
  echo 需要管理员权限运行. 请右键本文件选择"以管理员身份运行".
  pause
  exit /b
)

echo ============================================
echo   关闭蓝牙/USB 省电策略 (让连接更持久)
echo --------------------------------------------
echo   原理: Windows 会断开空闲的蓝牙设备连接来
echo   省电. 关闭后温湿度计连接应答更持久.
echo   修改: USB选择性暂停 设为"禁用"
echo ============================================
echo.

:: USB 选择性暂停 -> 0 = 已禁用 (之前误设成1=启用, 这里修正)
powercfg /setacvalueindex SCHEME_CURRENT 2a737441-1930-4402-8d77-b2bebba308a3 48e6b7a6-50f5-4782-a5d4-53bb8f07e226 0
powercfg /setdcvalueindex SCHEME_CURRENT 2a737441-1930-4402-8d77-b2bebba308a3 48e6b7a6-50f5-4782-a5d4-53bb8f07e226 0

:: 蓝牙无线电电源管理 -> 设为0 (允许更持久)  (此GUID可能存在机型差异, 失败则忽略)
powercfg /setacvalueindex SCHEME_CURRENT 19cbb8fa-5279-450e-9fac-8a3d5fedd0c1 00000000-0000-0000-0000-0000000000 0 >nul 2>&1
powercfg /setdcvalueindex SCHEME_CURRENT 19cbb8fa-5279-450e-9fac-8a3d5fedd0c1 00000000-0000-0000-0000-0000000000 0 >nul 2>&1

:: 应用当前电源方案
powercfg /S SCHEME_CURRENT >nul 2>&1

echo 完成. USB选择性暂停已设为"禁用".
echo 验证: 设置-系统-电源, 或运行 powercfg /q 查看.
echo.
echo 提示: 想24小时不睡, 再把系统电源改成"从不休眠"(可仅关屏幕).
pause