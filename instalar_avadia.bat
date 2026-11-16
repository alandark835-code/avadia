@echo off
setlocal EnableExtensions
chcp 65001 >nul
title Instalador de Avadia 1.2
echo.
echo ==========================================
echo          INSTALADOR DE AVADIA 1.2
echo ==========================================
echo.

set "ORIGEN=%~dp0"
set "DESTINO=%LOCALAPPDATA%\Programs\Avadia"

where py >nul 2>&1
if %errorlevel%==0 (
    set "MODO=py"
    set "COMANDO=py -3"
) else (
    where python >nul 2>&1
    if errorlevel 1 (
        echo [ERROR] No se encontro Python.
        echo Instala Python 3.10 o superior desde https://www.python.org/downloads/
        echo Durante la instalacion activa la opcion para agregar Python al PATH.
        echo Asegurate de incluir Tcl/Tk para poder abrir ventanas de juegos 2D.
        pause
        exit /b 1
    )
    set "MODO=python"
    set "COMANDO=python"
)

%COMANDO% -c "import sys; raise SystemExit(0 if sys.version_info >= (3,10) else 1)"
if errorlevel 1 (
    echo [ERROR] Avadia necesita Python 3.10 o superior.
    %COMANDO% --version
    pause
    exit /b 1
)

%COMANDO% -c "import tkinter" >nul 2>&1
if errorlevel 1 (
    echo [AVISO] Python funciona, pero tkinter no esta disponible.
    echo La biblioteca de juegos 2D necesita Tcl/Tk.
    echo Puedes reinstalar Python desde python.org e incluir Tcl/Tk.
)

if not exist "%DESTINO%" mkdir "%DESTINO%"
if errorlevel 1 (
    echo [ERROR] No se pudo crear la carpeta de instalacion:
    echo %DESTINO%
    pause
    exit /b 1
)

for %%F in (lexer.py ast_nodos.py parser.py interprete.py principal.py AvadiaCreator.pyw) do (
    copy /Y "%ORIGEN%%%F" "%DESTINO%\%%F" >nul
    if errorlevel 1 (
        echo [ERROR] No se pudo copiar %%F
        pause
        exit /b 1
    )
)

for %%D in (nucleo bibliotecas programas pruebas editor herramientas plantillas) do (
    if exist "%ORIGEN%%%D" (
        if exist "%DESTINO%\%%D" rmdir /S /Q "%DESTINO%\%%D"
        xcopy "%ORIGEN%%%D" "%DESTINO%\%%D\" /E /I /Y >nul
        if errorlevel 1 (
            echo [ERROR] No se pudo copiar la carpeta %%D
            pause
            exit /b 1
        )
    )
)

for %%F in (LEEME.md MANUAL.md VERSION requirements.txt) do if exist "%ORIGEN%%%F" copy /Y "%ORIGEN%%%F" "%DESTINO%\%%F" >nul

(
    echo @echo off
    if "%MODO%"=="py" (
        echo py -3 "%%~dp0principal.py" %%*
    ) else (
        echo python "%%~dp0principal.py" %%*
    )
) > "%DESTINO%\avadia.bat"

set "AVADIA_DEST=%DESTINO%"
powershell -NoProfile -ExecutionPolicy Bypass -Command "$d=$env:AVADIA_DEST; $p=[Environment]::GetEnvironmentVariable('Path','User'); $partes=@($p -split ';' | Where-Object { $_ }); if ($partes -notcontains $d) { $nuevo=if ([string]::IsNullOrWhiteSpace($p)) { $d } else { $p.TrimEnd(';') + ';' + $d }; [Environment]::SetEnvironmentVariable('Path',$nuevo,'User') }"
if errorlevel 1 (
    echo [AVISO] Avadia se copio, pero Windows no permitio actualizar PATH.
    echo Puedes ejecutarlo con: "%DESTINO%\avadia.bat" programas\hola.av
) else (
    echo [OK] Se agrego la carpeta de Avadia al PATH del usuario.
)

echo.
echo [LISTO] Avadia 1.2 se instalo en:
echo %DESTINO%
echo.
echo Cierra esta ventana, abre una NUEVA terminal y escribe:
echo avadia --version
echo.
echo Para ejecutar el ejemplo web:
echo avadia "%DESTINO%\programas\web\crear_sitio.av"
echo Para ejecutar el ejemplo 2D:
echo avadia "%DESTINO%\programas\juego\mover_cuadro.av"
echo.
echo Python sigue siendo necesario. Los juegos 2D necesitan Tcl/Tk.
echo ==========================================
pause
exit /b 0

rem Acceso directo "Avadia Creator" en el escritorio (opcional)
powershell -NoProfile -ExecutionPolicy Bypass -Command "$w=New-Object -ComObject WScript.Shell; $s=$w.CreateShortcut([Environment]::GetFolderPath('Desktop')+'\Avadia Creator.lnk'); $s.TargetPath='%DESTINO%\AvadiaCreator.pyw'; $s.WorkingDirectory='%DESTINO%'; $s.Save()" >nul 2>&1
if not errorlevel 1 echo [OK] Acceso directo "Avadia Creator" creado en el escritorio.
