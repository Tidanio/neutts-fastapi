#!/usr/bin/env bash
set -euo pipefail

# ─── Colors ───────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

ok()   { echo -e "${GREEN}[OK]${NC} $*"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $*"; }
err()  { echo -e "${RED}[ERROR]${NC} $*"; }
info() { echo -e "${CYAN}[INFO]${NC} $*"; }

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# ─── Detect OS ────────────────────────────────
OS="$(uname -s)"
case "$OS" in
    Linux*)  PLATFORM="linux" ;;
    Darwin*) PLATFORM="mac" ;;
    *)       echo "[ERROR] Unsupported OS. Use start.bat for Windows."; exit 1 ;;
esac

# ─── Detect system language ───────────────────
detect_lang() {
    local locale="${LANG:-${LC_ALL:-${LC_MESSAGES:-en_US.UTF-8}}}"
    case "${locale,,}" in
        de*) echo "de" ;;
        fr*) echo "fr" ;;
        es*) echo "es" ;;
        *)   echo "en" ;;
    esac
}
UI_LANG="$(detect_lang)"

# ─── i18n messages ────────────────────────────
# Usage: m <key> → prints localized message
# Falls back to English if key not found for current lang
declare -A MSG

# English (default / fallback)
MSG[en_title]="NeuTTS-FastAPI - One-Click Launcher"
MSG[en_python_not_found]="Python 3.10+ not found!"
MSG[en_python_install_mac]="Install Python with Homebrew:\n  brew install python@3.12"
MSG[en_python_install_linux]="Install Python:\n  sudo apt install python3.12 python3.12-venv   # Debian/Ubuntu\n  sudo dnf install python3.12                    # Fedora\n  sudo pacman -S python                          # Arch"
MSG[en_python_found]="Python %s found (%s)"
MSG[en_espeak_missing]="espeak-ng not found - required for phonemization."
MSG[en_espeak_install_brew]="Install espeak-ng with Homebrew? [Y/n]"
MSG[en_espeak_install_apt]="Install espeak-ng with apt? (requires sudo) [Y/n]"
MSG[en_espeak_install_dnf]="Install espeak-ng with dnf? (requires sudo) [Y/n]"
MSG[en_espeak_install_pacman]="Install espeak-ng with pacman? (requires sudo) [Y/n]"
MSG[en_espeak_installed]="espeak-ng installed."
MSG[en_espeak_install_failed]="espeak-ng installation failed. Continuing anyway."
MSG[en_espeak_skip]="Continuing without espeak-ng (TTS errors possible)."
MSG[en_espeak_found]="espeak-ng found."
MSG[en_espeak_manual]="Please install espeak-ng manually:\n  https://github.com/espeak-ng/espeak-ng/releases"
MSG[en_espeak_continue]="Continue anyway? [y/N]"
MSG[en_brew_missing]="Install Homebrew (https://brew.sh) then:\n  brew install espeak-ng"
MSG[en_venv_creating]="Creating virtual environment..."
MSG[en_venv_missing_pkg]="python3-venv is missing. Installing..."
MSG[en_venv_failed]="Could not create virtual environment."
MSG[en_venv_install_hint]="Install the venv module for Python %s."
MSG[en_venv_created]="Virtual environment created."
MSG[en_venv_activated]="Virtual environment activated."
MSG[en_gpu_detected]="GPU detected: %s"
MSG[en_gpu_blackwell]="Blackwell GPU detected - using CUDA 12.8 (cu128)"
MSG[en_gpu_install_prompt]="Install GPU version? [Y/n]"
MSG[en_gpu_none_mac]="macOS detected - using CPU mode (MPS used automatically if available)."
MSG[en_gpu_none]="No NVIDIA GPU detected - using CPU mode."
MSG[en_deps_installing]="Installing dependencies (%s)..."
MSG[en_deps_first_time]="This may take a few minutes on first run."
MSG[en_deps_installed]="Dependencies installed."
MSG[en_server_starting]="NeuTTS-FastAPI starting..."
MSG[en_server_open]="Open %s in your browser"
MSG[en_server_stop]="Press Ctrl+C to stop"

# Deutsch
MSG[de_title]="NeuTTS-FastAPI - Ein-Klick-Starter"
MSG[de_python_not_found]="Python 3.10+ nicht gefunden!"
MSG[de_python_install_mac]="Installiere Python mit Homebrew:\n  brew install python@3.12"
MSG[de_python_install_linux]="Installiere Python:\n  sudo apt install python3.12 python3.12-venv   # Debian/Ubuntu\n  sudo dnf install python3.12                    # Fedora\n  sudo pacman -S python                          # Arch"
MSG[de_python_found]="Python %s gefunden (%s)"
MSG[de_espeak_missing]="espeak-ng nicht gefunden - wird fuer Phonemisierung benoetigt."
MSG[de_espeak_install_brew]="espeak-ng mit Homebrew installieren? [J/n]"
MSG[de_espeak_install_apt]="espeak-ng mit apt installieren? (benoetigt sudo) [J/n]"
MSG[de_espeak_install_dnf]="espeak-ng mit dnf installieren? (benoetigt sudo) [J/n]"
MSG[de_espeak_install_pacman]="espeak-ng mit pacman installieren? (benoetigt sudo) [J/n]"
MSG[de_espeak_installed]="espeak-ng installiert."
MSG[de_espeak_install_failed]="espeak-ng Installation fehlgeschlagen. Fahre trotzdem fort."
MSG[de_espeak_skip]="Fahre ohne espeak-ng fort (TTS-Fehler moeglich)."
MSG[de_espeak_found]="espeak-ng gefunden."
MSG[de_espeak_manual]="Bitte installiere espeak-ng manuell:\n  https://github.com/espeak-ng/espeak-ng/releases"
MSG[de_espeak_continue]="Trotzdem fortfahren? [j/N]"
MSG[de_brew_missing]="Installiere Homebrew (https://brew.sh) und dann:\n  brew install espeak-ng"
MSG[de_venv_creating]="Erstelle virtuelle Umgebung..."
MSG[de_venv_missing_pkg]="python3-venv fehlt. Installiere..."
MSG[de_venv_failed]="Konnte virtuelle Umgebung nicht erstellen."
MSG[de_venv_install_hint]="Installiere das venv-Modul fuer Python %s."
MSG[de_venv_created]="Virtuelle Umgebung erstellt."
MSG[de_venv_activated]="Virtuelle Umgebung aktiviert."
MSG[de_gpu_detected]="GPU erkannt: %s"
MSG[de_gpu_blackwell]="Blackwell-GPU erkannt - verwende CUDA 12.8 (cu128)"
MSG[de_gpu_install_prompt]="GPU-Version installieren? [J/n]"
MSG[de_gpu_none_mac]="macOS erkannt - verwende CPU-Modus (MPS wird automatisch genutzt falls verfuegbar)."
MSG[de_gpu_none]="Keine NVIDIA GPU erkannt - verwende CPU-Modus."
MSG[de_deps_installing]="Installiere Abhaengigkeiten (%s)..."
MSG[de_deps_first_time]="Dies kann beim ersten Mal einige Minuten dauern."
MSG[de_deps_installed]="Abhaengigkeiten installiert."
MSG[de_server_starting]="NeuTTS-FastAPI startet..."
MSG[de_server_open]="Oeffne %s im Browser"
MSG[de_server_stop]="Druecke Strg+C zum Beenden"

# Francais
MSG[fr_title]="NeuTTS-FastAPI - Lanceur en un clic"
MSG[fr_python_not_found]="Python 3.10+ introuvable !"
MSG[fr_python_install_mac]="Installez Python avec Homebrew :\n  brew install python@3.12"
MSG[fr_python_install_linux]="Installez Python :\n  sudo apt install python3.12 python3.12-venv   # Debian/Ubuntu\n  sudo dnf install python3.12                    # Fedora\n  sudo pacman -S python                          # Arch"
MSG[fr_python_found]="Python %s trouve (%s)"
MSG[fr_espeak_missing]="espeak-ng introuvable - requis pour la phonemisation."
MSG[fr_espeak_install_brew]="Installer espeak-ng avec Homebrew ? [O/n]"
MSG[fr_espeak_install_apt]="Installer espeak-ng avec apt ? (sudo requis) [O/n]"
MSG[fr_espeak_install_dnf]="Installer espeak-ng avec dnf ? (sudo requis) [O/n]"
MSG[fr_espeak_install_pacman]="Installer espeak-ng avec pacman ? (sudo requis) [O/n]"
MSG[fr_espeak_installed]="espeak-ng installe."
MSG[fr_espeak_install_failed]="Installation de espeak-ng echouee. On continue quand meme."
MSG[fr_espeak_skip]="On continue sans espeak-ng (erreurs TTS possibles)."
MSG[fr_espeak_found]="espeak-ng trouve."
MSG[fr_espeak_manual]="Veuillez installer espeak-ng manuellement :\n  https://github.com/espeak-ng/espeak-ng/releases"
MSG[fr_espeak_continue]="Continuer quand meme ? [o/N]"
MSG[fr_brew_missing]="Installez Homebrew (https://brew.sh) puis :\n  brew install espeak-ng"
MSG[fr_venv_creating]="Creation de l'environnement virtuel..."
MSG[fr_venv_missing_pkg]="python3-venv manquant. Installation..."
MSG[fr_venv_failed]="Impossible de creer l'environnement virtuel."
MSG[fr_venv_install_hint]="Installez le module venv pour Python %s."
MSG[fr_venv_created]="Environnement virtuel cree."
MSG[fr_venv_activated]="Environnement virtuel active."
MSG[fr_gpu_detected]="GPU detecte : %s"
MSG[fr_gpu_blackwell]="GPU Blackwell detecte - utilisation de CUDA 12.8 (cu128)"
MSG[fr_gpu_install_prompt]="Installer la version GPU ? [O/n]"
MSG[fr_gpu_none_mac]="macOS detecte - mode CPU (MPS utilise automatiquement si disponible)."
MSG[fr_gpu_none]="Aucun GPU NVIDIA detecte - mode CPU."
MSG[fr_deps_installing]="Installation des dependances (%s)..."
MSG[fr_deps_first_time]="Cela peut prendre quelques minutes la premiere fois."
MSG[fr_deps_installed]="Dependances installees."
MSG[fr_server_starting]="NeuTTS-FastAPI demarre..."
MSG[fr_server_open]="Ouvrez %s dans votre navigateur"
MSG[fr_server_stop]="Appuyez sur Ctrl+C pour arreter"

# Espanol
MSG[es_title]="NeuTTS-FastAPI - Lanzador de un clic"
MSG[es_python_not_found]="Python 3.10+ no encontrado!"
MSG[es_python_install_mac]="Instala Python con Homebrew:\n  brew install python@3.12"
MSG[es_python_install_linux]="Instala Python:\n  sudo apt install python3.12 python3.12-venv   # Debian/Ubuntu\n  sudo dnf install python3.12                    # Fedora\n  sudo pacman -S python                          # Arch"
MSG[es_python_found]="Python %s encontrado (%s)"
MSG[es_espeak_missing]="espeak-ng no encontrado - necesario para la fonemizacion."
MSG[es_espeak_install_brew]="Instalar espeak-ng con Homebrew? [S/n]"
MSG[es_espeak_install_apt]="Instalar espeak-ng con apt? (requiere sudo) [S/n]"
MSG[es_espeak_install_dnf]="Instalar espeak-ng con dnf? (requiere sudo) [S/n]"
MSG[es_espeak_install_pacman]="Instalar espeak-ng con pacman? (requiere sudo) [S/n]"
MSG[es_espeak_installed]="espeak-ng instalado."
MSG[es_espeak_install_failed]="Instalacion de espeak-ng fallida. Continuando de todos modos."
MSG[es_espeak_skip]="Continuando sin espeak-ng (posibles errores de TTS)."
MSG[es_espeak_found]="espeak-ng encontrado."
MSG[es_espeak_manual]="Por favor instala espeak-ng manualmente:\n  https://github.com/espeak-ng/espeak-ng/releases"
MSG[es_espeak_continue]="Continuar de todos modos? [s/N]"
MSG[es_brew_missing]="Instala Homebrew (https://brew.sh) y luego:\n  brew install espeak-ng"
MSG[es_venv_creating]="Creando entorno virtual..."
MSG[es_venv_missing_pkg]="python3-venv falta. Instalando..."
MSG[es_venv_failed]="No se pudo crear el entorno virtual."
MSG[es_venv_install_hint]="Instala el modulo venv para Python %s."
MSG[es_venv_created]="Entorno virtual creado."
MSG[es_venv_activated]="Entorno virtual activado."
MSG[es_gpu_detected]="GPU detectada: %s"
MSG[es_gpu_blackwell]="GPU Blackwell detectada - usando CUDA 12.8 (cu128)"
MSG[es_gpu_install_prompt]="Instalar version GPU? [S/n]"
MSG[es_gpu_none_mac]="macOS detectado - modo CPU (MPS se usa automaticamente si esta disponible)."
MSG[es_gpu_none]="No se detecto GPU NVIDIA - modo CPU."
MSG[es_deps_installing]="Instalando dependencias (%s)..."
MSG[es_deps_first_time]="Esto puede tardar unos minutos la primera vez."
MSG[es_deps_installed]="Dependencias instaladas."
MSG[es_server_starting]="NeuTTS-FastAPI iniciando..."
MSG[es_server_open]="Abre %s en tu navegador"
MSG[es_server_stop]="Presiona Ctrl+C para detener"

# Message helper: m <key> [printf args...]
m() {
    local key="${UI_LANG}_$1"
    local fallback="en_$1"
    local template="${MSG[$key]:-${MSG[$fallback]:-$1}}"
    shift
    # shellcheck disable=SC2059
    printf "$template" "$@"
}

# Yes/no prompt helper (accepts Y/y/J/j/O/o/S/s based on locale)
yn_yes() {
    local answer="$1"
    [[ "${answer:-Y}" =~ ^[YyJjOoSs]$ ]]
}
yn_no() {
    local answer="$1"
    [[ "${answer:-N}" =~ ^[NnNn]$ ]]
}

# ─── Header ──────────────────────────────────
echo -e "${BOLD}"
echo "============================================"
echo "  $(m title)"
echo "  $(uname -s) / $(uname -m)"
echo "============================================"
echo -e "${NC}"

# ─── Check Python ─────────────────────────────
PYTHON=""
for cmd in python3 python; do
    if command -v "$cmd" &>/dev/null; then
        ver=$("$cmd" -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>/dev/null || echo "0.0")
        major=$(echo "$ver" | cut -d. -f1)
        minor=$(echo "$ver" | cut -d. -f2)
        if [ "$major" -gt 3 ] || { [ "$major" -eq 3 ] && [ "$minor" -ge 10 ]; }; then
            PYTHON="$cmd"
            break
        fi
    fi
done

if [ -z "$PYTHON" ]; then
    err "$(m python_not_found)"
    echo ""
    if [ "$PLATFORM" = "mac" ]; then
        echo -e "$(m python_install_mac)"
    else
        echo -e "$(m python_install_linux)"
    fi
    exit 1
fi

PYVER=$("$PYTHON" -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
ok "$(m python_found "$PYVER" "$PYTHON")"

# ─── Check / Install espeak-ng ────────────────
if ! command -v espeak-ng &>/dev/null; then
    warn "$(m espeak_missing)"
    echo ""
    if [ "$PLATFORM" = "mac" ]; then
        if command -v brew &>/dev/null; then
            read -rp "$(m espeak_install_brew) " answer
            if yn_yes "${answer:-Y}"; then
                if brew install espeak-ng; then
                    ok "$(m espeak_installed)"
                else
                    warn "$(m espeak_install_failed)"
                fi
            else
                warn "$(m espeak_skip)"
            fi
        else
            echo -e "$(m brew_missing)"
            echo ""
            read -rp "$(m espeak_continue) " answer
            yn_yes "$answer" || exit 1
        fi
    else
        # Linux
        if command -v apt-get &>/dev/null; then
            read -rp "$(m espeak_install_apt) " answer
            if yn_yes "${answer:-Y}"; then
                if sudo apt-get update && sudo apt-get install -y espeak-ng; then
                    ok "$(m espeak_installed)"
                else
                    warn "$(m espeak_install_failed)"
                fi
            else
                warn "$(m espeak_skip)"
            fi
        elif command -v dnf &>/dev/null; then
            read -rp "$(m espeak_install_dnf) " answer
            if yn_yes "${answer:-Y}"; then
                if sudo dnf install -y espeak-ng; then
                    ok "$(m espeak_installed)"
                else
                    warn "$(m espeak_install_failed)"
                fi
            fi
        elif command -v pacman &>/dev/null; then
            read -rp "$(m espeak_install_pacman) " answer
            if yn_yes "${answer:-Y}"; then
                if sudo pacman -S --noconfirm espeak-ng; then
                    ok "$(m espeak_installed)"
                else
                    warn "$(m espeak_install_failed)"
                fi
            fi
        else
            echo -e "$(m espeak_manual)"
            read -rp "$(m espeak_continue) " answer
            yn_yes "$answer" || exit 1
        fi
    fi
else
    ok "$(m espeak_found)"
fi

# ─── Create / activate venv ───────────────────
VENV_DIR="$SCRIPT_DIR/.venv"
if [ ! -f "$VENV_DIR/bin/activate" ]; then
    echo ""
    info "$(m venv_creating)"
    if ! "$PYTHON" -m venv "$VENV_DIR" 2>/dev/null; then
        # On Debian/Ubuntu, python3-venv is often missing
        if [ "$PLATFORM" = "linux" ] && command -v apt-get &>/dev/null; then
            warn "$(m venv_missing_pkg)"
            sudo apt-get install -y "python${PYVER}-venv" || sudo apt-get install -y python3-venv
            "$PYTHON" -m venv "$VENV_DIR"
        else
            err "$(m venv_failed)"
            err "$(m venv_install_hint "$PYVER")"
            exit 1
        fi
    fi
    ok "$(m venv_created)"
fi
# shellcheck disable=SC1091
source "$VENV_DIR/bin/activate"
ok "$(m venv_activated)"

# ─── Detect GPU ───────────────────────────────
INSTALL_MODE="cpu"
GPU_NAME=""

if command -v nvidia-smi &>/dev/null; then
    GPU_NAME=$(nvidia-smi --query-gpu=name --format=csv,noheader,nounits 2>/dev/null | head -n 1) || true
fi

if [ -n "$GPU_NAME" ]; then
    echo ""
    info "$(m gpu_detected "$GPU_NAME")"
    echo ""

    # Check for Blackwell (RTX 50xx)
    if echo "$GPU_NAME" | grep -iqE "RTX 50|RTX50|Blackwell"; then
        info "$(m gpu_blackwell)"
        INSTALL_MODE="gpu-blackwell"
    else
        INSTALL_MODE="gpu"
    fi

    read -rp "$(m gpu_install_prompt) " answer
    if [[ "${answer:-Y}" =~ ^[NnNn]$ ]]; then
        INSTALL_MODE="cpu"
    fi
else
    if [ "$PLATFORM" = "mac" ]; then
        info "$(m gpu_none_mac)"
    else
        info "$(m gpu_none)"
    fi
fi

# ─── Install dependencies ─────────────────────
echo ""
info "$(m deps_installing "$INSTALL_MODE")"
echo "$(m deps_first_time)"
echo ""

pip install --upgrade pip --quiet

case "$INSTALL_MODE" in
    gpu-blackwell)
        pip install -e ".[gpu]" --index-url https://download.pytorch.org/whl/cu128 --extra-index-url https://pypi.org/simple/
        ;;
    gpu)
        pip install -e ".[gpu]" --index-url https://download.pytorch.org/whl/cu124 --extra-index-url https://pypi.org/simple/
        ;;
    cpu)
        pip install -e ".[cpu]"
        ;;
esac

ok "$(m deps_installed)"

# ─── Start server ─────────────────────────────
URL="http://localhost:8880"
echo ""
echo -e "${BOLD}============================================${NC}"
echo -e "  $(m server_starting)"
echo -e "  $(m server_open "$URL")"
echo -e "  $(m server_stop)"
echo -e "${BOLD}============================================${NC}"
echo ""

python -m uvicorn api.src.main:app --host 0.0.0.0 --port 8880 --log-level info
