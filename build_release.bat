@echo off
setlocal enabledelayedexpansion

REM ==========================================
REM AI 小说生成器 - 自动化发版脚本
REM ==========================================

cd /d "%~dp0"

echo [1/5] 正在激活虚拟环境 (venv)...
if exist "venv\Scripts\activate.bat" (
    call "venv\Scripts\activate.bat"
) else (
    echo [警告] 未检测到 venv，将尝试直接使用系统 Python 环境。
)

echo [2/5] 清理旧的构建垃圾...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if not exist release mkdir release

echo [3/5] 使用 PyInstaller 编译为 EXE (单文件模式)...
pyinstaller --clean --noconfirm main.spec
if errorlevel 1 goto :error

echo [4/5] 同步配置文件到发布目录...
if not exist dist\config mkdir dist\config
if exist config (
    copy "config\config.ini.example" "dist\config\" /Y >nul
)

echo [5/5] 正在自动打包为 ZIP 压缩包...
set ZIP_NAME=ai-novel.zip
if exist "release\%ZIP_NAME%" del "release\%ZIP_NAME%"
tar -a -c -f "release\%ZIP_NAME%" -C dist .
if errorlevel 1 goto :error

echo.
echo ==========================================
echo ✅ 发版打包完成！
echo 产物位置: release\%ZIP_NAME%
echo ==========================================
exit /b 0

:error
echo.
echo ❌ 编译或打包过程中发生错误，错误代码: %errorlevel%。
pause
exit /b %errorlevel%

