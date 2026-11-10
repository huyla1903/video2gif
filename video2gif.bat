@rem @title        video2gif (launcher)
@rem @version      0.1.0
@rem @author       La Gia Huy
@rem @since        2026-10-05
@rem @updated      2026-10-05
@rem @engine       Windows batch (cmd.exe)
@rem @target       Windows; Python 3, ffmpeg
@rem @about        Drop .mov/.mp4 files on it: asks for a size limit, then runs video2gif.py.
@rem
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
