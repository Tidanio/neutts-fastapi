@echo off
setlocal enabledelayedexpansion
title NeuTTS-FastAPI Launcher
chcp 65001 >nul 2>&1

:: Navigate to script directory (needed if launched from elsewhere)
cd /d "%~dp0"

:: ── Detect system language ──────────────────
:: Read Windows locale from registry (e.g. de-DE, fr-FR, es-ES, en-US)
set "UI_LANG=en"
for /f "tokens=3" %%l in ('reg query "HKCU\Control Panel\International" /v LocaleName 2^>nul') do set "WIN_LOCALE=%%l"
if defined WIN_LOCALE (
    if /i "!WIN_LOCALE:~0,2!"=="de" set "UI_LANG=de"
    if /i "!WIN_LOCALE:~0,2!"=="fr" set "UI_LANG=fr"
    if /i "!WIN_LOCALE:~0,2!"=="es" set "UI_LANG=es"
)

:: ── i18n messages ───────────────────────────
:: Use {1}, {2} as placeholders for dynamic values

:: English
set "en_title=NeuTTS-FastAPI - One-Click Launcher"
set "en_python_not_found=[ERROR] Python 3.10+ not found!"
set "en_python_install=Please install Python 3.10+ from:"
set "en_python_path=Make sure 'Add Python to PATH' is checked."
set "en_python_version_fail=[ERROR] Could not determine Python version."
set "en_python_store_hint=Make sure Python is properly installed (not the Microsoft Store stub)."
set "en_python_too_old=[ERROR] Python {1} is too old. Minimum 3.10 required."
set "en_python_found=[OK] Python {1} found."
set "en_espeak_missing=[WARN] espeak-ng not found - required for phonemization."
set "en_espeak_install=Install espeak-ng with one of these commands:"
set "en_espeak_manual=Or download manually:"
set "en_espeak_continue=Continue anyway (TTS errors possible)?"
set "en_espeak_found=[OK] espeak-ng found."
set "en_venv_creating=Creating virtual environment..."
set "en_venv_failed=[ERROR] Could not create virtual environment."
set "en_venv_created=[OK] Virtual environment created."
set "en_venv_activated=[OK] Virtual environment activated."
set "en_gpu_detected=[GPU] {1} detected!"
set "en_gpu_blackwell=[INFO] Blackwell GPU detected - using CUDA 12.8 (cu128)"
set "en_gpu_prompt=Install [G]PU or [C]PU version?"
set "en_gpu_none=[INFO] No NVIDIA GPU detected - using CPU mode."
set "en_deps_installing=Installing dependencies ({1})..."
set "en_deps_first_time=This may take a few minutes on first run."
set "en_deps_failed=[ERROR] Installation failed!"
set "en_deps_fallback=Try: pip install -e .[cpu]"
set "en_deps_installed=[OK] Dependencies installed."
set "en_server_starting=NeuTTS-FastAPI starting..."
set "en_server_open=Open http://localhost:8880 in your browser"
set "en_server_stop=Press Ctrl+C to stop"

:: Deutsch
set "de_title=NeuTTS-FastAPI - Ein-Klick-Starter"
set "de_python_not_found=[ERROR] Python 3.10+ nicht gefunden!"
set "de_python_install=Bitte installiere Python 3.10+ von:"
set "de_python_path=Stelle sicher, dass 'Add Python to PATH' aktiviert ist."
set "de_python_version_fail=[ERROR] Konnte Python-Version nicht ermitteln."
set "de_python_store_hint=Stelle sicher, dass Python korrekt installiert ist (kein Microsoft Store Stub)."
set "de_python_too_old=[ERROR] Python {1} ist zu alt. Mindestens 3.10 erforderlich."
set "de_python_found=[OK] Python {1} gefunden."
set "de_espeak_missing=[WARN] espeak-ng nicht gefunden - wird fuer Phonemisierung benoetigt."
set "de_espeak_install=Installiere espeak-ng mit einem der folgenden Befehle:"
set "de_espeak_manual=Oder lade es manuell herunter:"
set "de_espeak_continue=Trotzdem fortfahren (Fehler bei TTS moeglich)?"
set "de_espeak_found=[OK] espeak-ng gefunden."
set "de_venv_creating=Erstelle virtuelle Umgebung..."
set "de_venv_failed=[ERROR] Konnte venv nicht erstellen."
set "de_venv_created=[OK] Virtuelle Umgebung erstellt."
set "de_venv_activated=[OK] Virtuelle Umgebung aktiviert."
set "de_gpu_detected=[GPU] {1} erkannt!"
set "de_gpu_blackwell=[INFO] Blackwell-GPU erkannt - verwende CUDA 12.8 (cu128)"
set "de_gpu_prompt=Installiere [G]PU oder [C]PU Version?"
set "de_gpu_none=[INFO] Keine NVIDIA GPU erkannt - verwende CPU-Modus."
set "de_deps_installing=Installiere Abhaengigkeiten ({1})..."
set "de_deps_first_time=Dies kann beim ersten Mal einige Minuten dauern."
set "de_deps_failed=[ERROR] Installation fehlgeschlagen!"
set "de_deps_fallback=Versuche: pip install -e .[cpu]"
set "de_deps_installed=[OK] Abhaengigkeiten installiert."
set "de_server_starting=NeuTTS-FastAPI startet..."
set "de_server_open=Oeffne http://localhost:8880 im Browser"
set "de_server_stop=Druecke Strg+C zum Beenden"

:: Francais
set "fr_title=NeuTTS-FastAPI - Lanceur en un clic"
set "fr_python_not_found=[ERROR] Python 3.10+ introuvable !"
set "fr_python_install=Veuillez installer Python 3.10+ depuis :"
set "fr_python_path=Assurez-vous que 'Add Python to PATH' est coche."
set "fr_python_version_fail=[ERROR] Impossible de determiner la version de Python."
set "fr_python_store_hint=Assurez-vous que Python est correctement installe (pas le stub Microsoft Store)."
set "fr_python_too_old=[ERROR] Python {1} est trop ancien. Minimum 3.10 requis."
set "fr_python_found=[OK] Python {1} trouve."
set "fr_espeak_missing=[WARN] espeak-ng introuvable - requis pour la phonemisation."
set "fr_espeak_install=Installez espeak-ng avec une de ces commandes :"
set "fr_espeak_manual=Ou telechargez manuellement :"
set "fr_espeak_continue=Continuer quand meme (erreurs TTS possibles) ?"
set "fr_espeak_found=[OK] espeak-ng trouve."
set "fr_venv_creating=Creation de l'environnement virtuel..."
set "fr_venv_failed=[ERROR] Impossible de creer l'environnement virtuel."
set "fr_venv_created=[OK] Environnement virtuel cree."
set "fr_venv_activated=[OK] Environnement virtuel active."
set "fr_gpu_detected=[GPU] {1} detecte !"
set "fr_gpu_blackwell=[INFO] GPU Blackwell detecte - utilisation de CUDA 12.8 (cu128)"
set "fr_gpu_prompt=Installer la version [G]PU ou [C]PU ?"
set "fr_gpu_none=[INFO] Aucun GPU NVIDIA detecte - mode CPU."
set "fr_deps_installing=Installation des dependances ({1})..."
set "fr_deps_first_time=Cela peut prendre quelques minutes la premiere fois."
set "fr_deps_failed=[ERROR] Installation echouee !"
set "fr_deps_fallback=Essayez : pip install -e .[cpu]"
set "fr_deps_installed=[OK] Dependances installees."
set "fr_server_starting=NeuTTS-FastAPI demarre..."
set "fr_server_open=Ouvrez http://localhost:8880 dans votre navigateur"
set "fr_server_stop=Appuyez sur Ctrl+C pour arreter"

:: Espanol
set "es_title=NeuTTS-FastAPI - Lanzador de un clic"
set "es_python_not_found=[ERROR] Python 3.10+ no encontrado!"
set "es_python_install=Por favor instala Python 3.10+ desde:"
set "es_python_path=Asegurate de que 'Add Python to PATH' este marcado."
set "es_python_version_fail=[ERROR] No se pudo determinar la version de Python."
set "es_python_store_hint=Asegurate de que Python este correctamente instalado (no el stub de Microsoft Store)."
set "es_python_too_old=[ERROR] Python {1} es muy antiguo. Minimo 3.10 requerido."
set "es_python_found=[OK] Python {1} encontrado."
set "es_espeak_missing=[WARN] espeak-ng no encontrado - necesario para la fonemizacion."
set "es_espeak_install=Instala espeak-ng con uno de estos comandos:"
set "es_espeak_manual=O descargalo manualmente:"
set "es_espeak_continue=Continuar de todos modos (posibles errores de TTS)?"
set "es_espeak_found=[OK] espeak-ng encontrado."
set "es_venv_creating=Creando entorno virtual..."
set "es_venv_failed=[ERROR] No se pudo crear el entorno virtual."
set "es_venv_created=[OK] Entorno virtual creado."
set "es_venv_activated=[OK] Entorno virtual activado."
set "es_gpu_detected=[GPU] {1} detectada!"
set "es_gpu_blackwell=[INFO] GPU Blackwell detectada - usando CUDA 12.8 (cu128)"
set "es_gpu_prompt=Instalar version [G]PU o [C]PU?"
set "es_gpu_none=[INFO] No se detecto GPU NVIDIA - modo CPU."
set "es_deps_installing=Instalando dependencias ({1})..."
set "es_deps_first_time=Esto puede tardar unos minutos la primera vez."
set "es_deps_failed=[ERROR] Instalacion fallida!"
set "es_deps_fallback=Intenta: pip install -e .[cpu]"
set "es_deps_installed=[OK] Dependencias instaladas."
set "es_server_starting=NeuTTS-FastAPI iniciando..."
set "es_server_open=Abre http://localhost:8880 en tu navegador"
set "es_server_stop=Presiona Ctrl+C para detener"

:: ── Header ──────────────────────────────────
echo ============================================
call :msg title
echo   Windows
echo ============================================
echo.

:: ── Check Python ────────────────────────────
:: Try py launcher first (most reliable on Windows), then python, then python3
set "PYTHON="
where py >nul 2>&1
if not errorlevel 1 (
    py -3 --version >nul 2>&1
    if not errorlevel 1 set "PYTHON=py -3"
)
if not defined PYTHON (
    where python >nul 2>&1
    if not errorlevel 1 (
        python --version >nul 2>&1
        if not errorlevel 1 set "PYTHON=python"
    )
)
if not defined PYTHON (
    where python3 >nul 2>&1
    if not errorlevel 1 (
        python3 --version >nul 2>&1
        if not errorlevel 1 set "PYTHON=python3"
    )
)
if not defined PYTHON (
    call :msg python_not_found
    echo.
    call :msg python_install
    echo   https://www.python.org/downloads/
    echo.
    call :msg python_path
    pause
    exit /b 1
)

:: Verify version >= 3.10 (use chr(46) for dot to avoid single-quote issues in FOR)
set "PYVER="
for /f "tokens=*" %%v in ('%PYTHON% -c "import sys;v=sys.version_info;print(str(v.major)+chr(46)+str(v.minor))"') do set "PYVER=%%v"
if not defined PYVER (
    call :msg python_version_fail
    call :msg python_store_hint
    pause
    exit /b 1
)
for /f "tokens=1,2 delims=." %%a in ("%PYVER%") do (
    if %%a LSS 3 (
        call :msg python_too_old !PYVER!
        pause
        exit /b 1
    )
    if %%a EQU 3 if %%b LSS 10 (
        call :msg python_too_old !PYVER!
        pause
        exit /b 1
    )
)
call :msg python_found !PYVER!

:: ── Check espeak-ng ─────────────────────────
where espeak-ng >nul 2>&1
if errorlevel 1 (
    echo.
    call :msg espeak_missing
    echo.
    call :msg espeak_install
    echo   winget install espeak-ng.espeak-ng
    echo   choco install espeak-ng
    echo.
    call :msg espeak_manual
    echo   https://github.com/espeak-ng/espeak-ng/releases
    echo.
    call :msg_prompt espeak_continue
    if errorlevel 2 exit /b 1
) else (
    call :msg espeak_found
)

:: ── Create / activate venv ──────────────────
set "VENV_DIR=%~dp0.venv"
if not exist "%VENV_DIR%\Scripts\activate.bat" (
    echo.
    call :msg venv_creating
    %PYTHON% -m venv "%VENV_DIR%"
    if errorlevel 1 (
        call :msg venv_failed
        pause
        exit /b 1
    )
    call :msg venv_created
)
call "%VENV_DIR%\Scripts\activate.bat"
call :msg venv_activated

:: ── Detect GPU ──────────────────────────────
set "INSTALL_MODE=cpu"
set "GPU_NAME="
where nvidia-smi >nul 2>&1
if not errorlevel 1 (
    for /f "tokens=*" %%g in ('nvidia-smi --query-gpu=name --format=csv,noheader,nounits 2^>nul') do (
        set "GPU_NAME=%%g"
    )
)
if defined GPU_NAME (
    echo.
    call :msg gpu_detected "!GPU_NAME!"
    echo.
    :: Check if Blackwell (RTX 50xx) - use /c: for literal string matching
    echo !GPU_NAME! | findstr /i /c:"RTX 50" /c:"RTX50" /c:"Blackwell" >nul
    if not errorlevel 1 (
        call :msg gpu_blackwell
        set "INSTALL_MODE=gpu-blackwell"
    ) else (
        set "INSTALL_MODE=gpu"
    )
    call :msg_choice gpu_prompt
    if errorlevel 2 set "INSTALL_MODE=cpu"
) else (
    call :msg gpu_none
)

:: ── Install dependencies ────────────────────
echo.
call :msg deps_installing !INSTALL_MODE!
call :msg deps_first_time
echo.

pip install --upgrade pip >nul 2>&1

if "!INSTALL_MODE!"=="gpu-blackwell" (
    pip install -e ".[gpu]" --index-url https://download.pytorch.org/whl/cu128 --extra-index-url https://pypi.org/simple/
) else if "!INSTALL_MODE!"=="gpu" (
    pip install -e ".[gpu]" --index-url https://download.pytorch.org/whl/cu124 --extra-index-url https://pypi.org/simple/
) else (
    pip install -e ".[cpu]"
)

if errorlevel 1 (
    echo.
    call :msg deps_failed
    call :msg deps_fallback
    pause
    exit /b 1
)
call :msg deps_installed

:: ── Start server ────────────────────────────
echo.
echo ============================================
call :msg server_starting
call :msg server_open
call :msg server_stop
echo ============================================
echo.

python -m uvicorn api.src.main:app --host 0.0.0.0 --port 8880 --log-level info

pause
exit /b 0

:: ── Helper functions ────────────────────────
:msg
:: Print localized message with optional {1},{2} substitution
:: Usage: call :msg <key> [arg1] [arg2]
set "_msg_key=!UI_LANG!_%~1"
set "_msg_val=!%_msg_key%!"
if not defined _msg_val (
    set "_msg_key=en_%~1"
    set "_msg_val=!%_msg_key%!"
)
if not defined _msg_val (
    echo %~1
    exit /b 0
)
if not "%~2"=="" set "_msg_val=!_msg_val:{1}=%~2!"
if not "%~3"=="" set "_msg_val=!_msg_val:{2}=%~3!"
echo   !_msg_val!
exit /b 0

:msg_prompt
:: Print localized message then choice Y/N
:: Usage: call :msg_prompt <key>
set "_msg_key=!UI_LANG!_%~1"
set "_msg_val=!%_msg_key%!"
if not defined _msg_val (
    set "_msg_key=en_%~1"
    set "_msg_val=!%_msg_key%!"
)
choice /c YN /m "!_msg_val!"
exit /b %errorlevel%

:msg_choice
:: Print localized message then choice G/C
:: Usage: call :msg_choice <key>
set "_msg_key=!UI_LANG!_%~1"
set "_msg_val=!%_msg_key%!"
if not defined _msg_val (
    set "_msg_key=en_%~1"
    set "_msg_val=!%_msg_key%!"
)
choice /c GC /m "!_msg_val!"
exit /b %errorlevel%
