@echo off
setlocal

rem Make sure ffmpeg/ffprobe and the installed Python are reachable regardless
rem of what's on the normal user PATH.
set "PATH=C:\ffmpeg\bin;%LOCALAPPDATA%\Microsoft\WindowsApps;%PATH%"

if "%~1"=="" (
    echo Drag and drop one or more .mov / .mp4 files onto this .bat file to convert them to GIF.
    pause
    exit /b
)

set "MAXKB="
set /p "MAXKB=Size limit in KB (e.g. 1000 = 1 MB, leave blank for no limit / match source): "

if defined MAXKB (
    python "%~dp0video2gif.py" --max-kb %MAXKB% %*
) else (
    python "%~dp0video2gif.py" %*
)

echo.
echo Done.
pause
