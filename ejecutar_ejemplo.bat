@echo off
chcp 65001 >nul
set "BASE=%~dp0"
if exist "%LOCALAPPDATA%\Programs\Avadia\avadia.bat" (
  call "%LOCALAPPDATA%\Programs\Avadia\avadia.bat" "%BASE%programas\hola.av"
) else (
  where py >nul 2>&1 && py -3 "%BASE%principal.py" "%BASE%programas\hola.av" || python "%BASE%principal.py" "%BASE%programas\hola.av"
)
pause
