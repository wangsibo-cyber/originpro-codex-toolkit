@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0"
title OriginPro + Codex 配置安装
echo 请先安装并登录 Codex，安装已授权的 OriginPro 和 64 位 Python 3.11。
echo 首次依赖安装需要网络，请不要在安装完成前关闭窗口。
py -3.11 -c "import sys; assert sys.version_info[:2] == (3,11)" >nul 2>nul
if not errorlevel 1 (
    py -3.11 setup_bundle.py
    goto done
)
python -c "import sys; assert sys.version_info[:2] == (3,11)" >nul 2>nul
if not errorlevel 1 (
    python setup_bundle.py
    goto done
)
echo 没有找到 Python 3.11。请安装 Windows 64 位 Python 3.11 后重试。
echo 安装时启用 Python Launcher 或将 Python 加入 PATH。
:done
echo.
echo 请阅读上方结果。按任意键关闭窗口。
pause >nul
