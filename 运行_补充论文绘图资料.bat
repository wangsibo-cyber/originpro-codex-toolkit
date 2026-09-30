@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0"

where py >nul 2>nul
if %errorlevel%==0 (
    py -3 download_publication_graphing_supplement.py --kb-root "%~dp0OriginPro_Codex_KB"
) else (
    python download_publication_graphing_supplement.py --kb-root "%~dp0OriginPro_Codex_KB"
)

echo.
echo 按任意键关闭窗口……
pause >nul
