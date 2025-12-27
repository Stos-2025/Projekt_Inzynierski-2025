#!/bin/bash
# Skrypt do czyszczenia wyników testowych z gui_mock

# Kolory
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Ścieżka do katalogu z wynikami
RESULTS_DIR="../src/gui_mock/src/received_results"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  Czyszczenie wyników testowych${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Sprawdź czy katalog istnieje
if [ ! -d "$RESULTS_DIR" ]; then
    echo -e "${YELLOW}Katalog $RESULTS_DIR nie istnieje.${NC}"
    echo "Nic do usunięcia."
    exit 0
fi

# Policz pliki
FILE_COUNT=$(find "$RESULTS_DIR" -type f | wc -l | tr -d ' ')

if [ "$FILE_COUNT" -eq 0 ]; then
    echo -e "${YELLOW}Katalog jest pusty.${NC}"
    echo "Nic do usunięcia."
    exit 0
fi

# Pokaż co zostanie usunięte
echo -e "Znaleziono ${YELLOW}$FILE_COUNT${NC} plików w katalogu:"
echo -e "${BLUE}$RESULTS_DIR${NC}"
echo ""

# Zapytaj o potwierdzenie (chyba że przekazano flagę -f)
if [ "$1" != "-f" ] && [ "$1" != "--force" ]; then
    read -p "Czy na pewno chcesz usunąć wszystkie pliki? (t/N): " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[TtYy]$ ]]; then
        echo -e "${YELLOW}Anulowano.${NC}"
        exit 0
    fi
fi

# Usuń pliki
echo ""
echo "Usuwanie plików..."
rm -f "$RESULTS_DIR"/*

# Sprawdź wynik
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Usunięto $FILE_COUNT plików${NC}"
    echo ""
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}  Katalog został wyczyszczony${NC}"
    echo -e "${GREEN}========================================${NC}"
else
    echo -e "${RED}✗ Wystąpił błąd podczas usuwania plików${NC}"
    exit 1
fi

