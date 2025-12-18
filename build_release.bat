@echo off
setlocal

REM Build Windows release: create EXE then zip dist into release\ai-novel.zip
cd /d "%~dp0"

echo [1/5] Activating venv (if present)...
if exist "venv\Scripts\activate.bat" (
    call "venv\Scripts\activate.bat"
) else (
    echo venv not found, using system Python...
)

echo [2/5] Cleaning old build artifacts...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

echo [3/5] Building exe with PyInstaller...
pyinstaller --clean --noconfirm main.spec
if errorlevel 1 goto :error

echo [4/5] Syncing config into dist\config...
if not exist dist\config mkdir dist\config
xcopy "config\*.ini*" "dist\config\" /Y /I >nul

echo [5/5] Creating release\ai-novel.zip...
if not exist release mkdir release
powershell -NoLogo -NoProfile -Command "Compress-Archive -Path 'dist\\*' -DestinationPath 'release\\ai-novel.zip' -Force"
if errorlevel 1 goto :error

echo Build and packaging completed. Output: release\ai-novel.zip
exit /b 0

:error
echo Build failed with code %errorlevel%.
exit /b %errorlevel%

