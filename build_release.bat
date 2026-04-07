@echo off
setlocal

cd /d "%~dp0"

set "ROOT_DIR=%CD%"
set "DIST_DIR=%ROOT_DIR%\dist\gui_app"
set "EXE_NAME=BPSR-AutoModules_JP.exe"
set "BUILD_DIR=%ROOT_DIR%\build"
set "OUTPUT_DIR=%ROOT_DIR%\Output"
set "ISCC_PATH="
set "PYTHON_CMD=python"

where python >nul 2>nul
if errorlevel 1 (
    echo [ERROR] Python was not found in PATH.
    exit /b 1
)

call %PYTHON_CMD% -c "import PyInstaller" >nul 2>nul
if errorlevel 1 (
    echo [ERROR] PyInstaller is not installed. Run: pip install pyinstaller
    exit /b 1
)

if exist "%BUILD_DIR%" (
    echo [INFO] Removing existing build directory...
    powershell -NoProfile -Command "if (Test-Path '%BUILD_DIR%') { Remove-Item -LiteralPath '%BUILD_DIR%' -Recurse -Force -ErrorAction SilentlyContinue }" >nul 2>nul
)

if exist "%ROOT_DIR%\dist" (
    echo [INFO] Removing existing dist directory...
    powershell -NoProfile -Command "if (Test-Path '%ROOT_DIR%\dist') { Remove-Item -LiteralPath '%ROOT_DIR%\dist' -Recurse -Force -ErrorAction SilentlyContinue }" >nul 2>nul
)

if exist "%OUTPUT_DIR%" (
    echo [INFO] Removing existing Output directory...
    powershell -NoProfile -Command "if (Test-Path '%OUTPUT_DIR%') { Remove-Item -LiteralPath '%OUTPUT_DIR%' -Recurse -Force -ErrorAction SilentlyContinue }" >nul 2>nul
)

echo [INFO] Building exe with PyInstaller...
call %PYTHON_CMD% -m PyInstaller --noconfirm gui_app.spec
if errorlevel 1 (
    echo [ERROR] Exe build failed.
    exit /b 1
)

if not exist "%DIST_DIR%\%EXE_NAME%" (
    echo [ERROR] "%DIST_DIR%\%EXE_NAME%" was not created.
    exit /b 1
)

for /f "delims=" %%I in ('where ISCC.exe 2^>nul') do (
    if not defined ISCC_PATH set "ISCC_PATH=%%I"
)

if not defined ISCC_PATH if exist "%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe" (
    set "ISCC_PATH=%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe"
)

if not defined ISCC_PATH if exist "%ProgramFiles%\Inno Setup 6\ISCC.exe" (
    set "ISCC_PATH=%ProgramFiles%\Inno Setup 6\ISCC.exe"
)

if exist "%ROOT_DIR%\npcap-1.83.exe" (
    echo [INFO] npcap-1.83.exe found. Installer will bundle it.
) else (
    echo [WARN] npcap-1.83.exe was not found. Installer will be built without bundled Npcap.
)

if defined ISCC_PATH (
    echo [INFO] Building installer with Inno Setup...
    "%ISCC_PATH%" "installer_script.iss"
    if errorlevel 1 (
        echo [ERROR] Installer build failed.
        exit /b 1
    )
    echo [OK] Installer created: "%OUTPUT_DIR%\BPSR Module Optimizer Setup.exe"
) else (
    echo [WARN] ISCC.exe was not found. Installer build was skipped.
    echo [WARN] Install Inno Setup 6 if you also want an installer.
)

echo [OK] Exe created: "%DIST_DIR%\%EXE_NAME%"
exit /b 0
