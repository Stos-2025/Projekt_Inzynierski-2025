#!/bin/bash
# Skrypt do uruchamiania gui_mock

# Przejdź do katalogu src gui_mock
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR/src"

# Kolory
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Uruchamianie gui_mock...${NC}"

# Sprawdź czy venv istnieje w głównym katalogu projektu
VENV_PATH="$SCRIPT_DIR/../../.venv"
if [ ! -d "$VENV_PATH" ]; then
    echo -e "${YELLOW}Virtual environment nie istnieje. Tworzę...${NC}"
    cd "$SCRIPT_DIR/../.."
    python3 -m venv .venv
    cd "$SCRIPT_DIR/src"
fi

# Aktywuj venv
source "$VENV_PATH/bin/activate"

# Zainstaluj zależności jeśli potrzeba
if ! python3 -c "import uvicorn" 2>/dev/null; then
    echo -e "${YELLOW}Instaluję zależności...${NC}"
    pip install --quiet fastapi uvicorn python-multipart requests jinja2
fi

echo -e "${GREEN}gui_mock uruchomiony na http://localhost:8080${NC}"
echo -e "${YELLOW}Naciśnij Ctrl+C aby zatrzymać${NC}"
echo ""

uvicorn gui_mock:app --host 0.0.0.0 --port 8080

