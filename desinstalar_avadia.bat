@echo off
setlocal EnableExtensions
chcp 65001 >nul
set "DESTINO=%LOCALAPPDATA%\Programs\Avadia"
echo.
echo Desinstalacion de Avadia 1.2
echo Se eliminara: %DESTINO%
choice /C SN /M "¿Deseas continuar?"
if errorlevel 2 exit /b 0
set "AVADIA_DEST=%DESTINO%"
powershell -NoProfile -ExecutionPolicy Bypass -Command "$d=$env:AVADIA_DEST; $p=[Environment]::GetEnvironmentVariable('Path','User'); $partes=@($p -split ';' | Where-Object { $_ -and $_ -ne $d }); [Environment]::SetEnvironmentVariable('Path',($partes -join ';'),'User')"
if exist "%DESTINO%" rmdir /S /Q "%DESTINO%"
echo Avadia se ha eliminado. Abre una nueva terminal para actualizar el PATH.
pause

rem Quitar el acceso directo del escritorio
del "%USERPROFILE%\Desktop\Avadia Creator.lnk" >nul 2>&1
