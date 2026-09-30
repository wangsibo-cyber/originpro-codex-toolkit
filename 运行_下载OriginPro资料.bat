@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0"

where py >nul 2>nul
if %errorlevel%==0 (
    py -3 download_originpro_kb.py
) else (
    python download_originpro_kb.py
)

echo.
echo 按任意键关闭窗口……
pause >nul
