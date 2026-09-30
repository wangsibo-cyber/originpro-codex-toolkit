@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0"
title OriginPro 离线资料导入
py -3.11 -c "import sys; assert sys.version_info[:2] == (3,11)" >nul 2>nul
if not errorlevel 1 (
    py -3.11 import_offline_kb.py
    goto done
)
python -c "import sys; assert sys.version_info[:2] == (3,11)" >nul 2>nul
if not errorlevel 1 (
    python import_offline_kb.py
    goto done
)
echo 请先安装 64 位 Python 3.11。
:done
echo.
echo 请阅读上方结果。按任意键关闭窗口。
pause >nul
