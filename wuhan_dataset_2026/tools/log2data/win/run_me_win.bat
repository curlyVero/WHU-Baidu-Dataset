@echo off
setlocal

set "TARGET=%~1"
if "%TARGET%"=="" (
  set /p TARGET=Input data folder path: 
)

if "%TARGET%"=="" (
  echo No folder provided.
  pause
  exit /b 1
)

if not exist "%TARGET%" (
  echo Folder not found:
  echo %TARGET%
  pause
  exit /b 1
)

set "PYTHON_CMD="
where py >nul 2>nul
if not errorlevel 1 set "PYTHON_CMD=py -3"
if not defined PYTHON_CMD (
  where python >nul 2>nul
  if not errorlevel 1 set "PYTHON_CMD=python"
)

if not defined PYTHON_CMD (
  echo Python is not installed or not in PATH.
  pause
  exit /b 1
)

call %PYTHON_CMD% "%~dp0convert_android_logs.py" --root-dir "%TARGET%"
set "ERR=%ERRORLEVEL%"

if not "%ERR%"=="0" (
  echo.
  echo Conversion failed with error code %ERR%.
  pause
  exit /b %ERR%
)

echo.
echo Output written under:
echo %TARGET%
pause
