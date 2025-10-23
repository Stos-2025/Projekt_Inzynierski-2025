#!/bin/bash
# Skrypt do uruchamiania testu integracyjnego gui_mock

set -e

# Przejdź do katalogu gdzie jest skrypt
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# Kolory dla outputu
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  Test integracyjny gui_mock${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Sprawdź czy GUI_URL jest ustawiony
if [ -z "$GUI_URL" ]; then
    export GUI_URL="http://localhost:8080"
    echo -e "${YELLOW}GUI_URL nie jest ustawiony, używam domyślnego: $GUI_URL${NC}"
else
    echo -e "GUI_URL: $GUI_URL"
fi

echo ""

# Sprawdź czy gui_mock jest dostępny
echo "Sprawdzanie dostępności gui_mock..."
if curl -s -f -o /dev/null "$GUI_URL/results"; then
    echo -e "${GREEN}✓ gui_mock jest dostępny${NC}"
else
    echo -e "${RED}✗ gui_mock nie jest dostępny pod adresem $GUI_URL${NC}"
    echo ""
    echo "Aby uruchomić gui_mock, w NOWYM TERMINALU wpisz:"
    echo ""
    echo -e "${BLUE}  cd src/gui_mock${NC}"
    echo -e "${BLUE}  ./start_gui_mock.sh${NC}"
    echo ""
    echo "Następnie ponownie uruchom ten test."
    echo ""
    exit 1
fi

echo ""

# Sprawdź czy jest pytest
if command -v pytest &> /dev/null; then
    echo "Uruchamianie testu przez pytest..."
    echo -e "${BLUE}========================================${NC}"
    pytest test_gui_mock.py -v -s
else
    echo "pytest nie jest zainstalowany, uruchamianie testu bezpośrednio..."
    echo -e "${BLUE}========================================${NC}"
    python3 test_gui_mock.py
fi

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  Test zakończony${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "Zobacz wyniki na: ${BLUE}$GUI_URL/results${NC}"

