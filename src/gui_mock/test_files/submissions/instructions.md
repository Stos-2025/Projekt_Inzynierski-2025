# Instrukcje Użycia Złośliwego Kodu

## Wprowadzenie

Ten folder zawiera przykłady złośliwego kodu w językach Python i C, które mogą być użyte do przetestowania bezpieczeństwa systemu STOS. Każdy z tych skryptów jest zaprojektowany do symulowania innego rodzaju ataku.

## Struktura Folderów

*   `/py`: Zawiera złośliwy kod w Pythonie i jego dokumentację.
*   `/c`: Zawiera złośliwy kod w C i jego dokumentację.

## Jak Użyć

1.  **Umieść w Kolejce:** Aby przetestować, jak system STOS radzi sobie z tymi zagrożeniami, umieść jeden z tych plików w kolejce do oceny. Możesz to zrobić, modyfikując plik `src/gui_mock/src/gui_mock.py`, aby wskazywał na te pliki.

2.  **Obserwuj Wyniki:** Po umieszczeniu pliku w kolejce, obserwuj zachowanie systemu. Sprawdź logi workera, użycie zasobów systemowych i wszelkie nieoczekiwane wyniki w interfejsie GUI (lub w folderze `received_results`, jeśli używasz `gui_mock`).

## Scenariusze Testowe

### Python (`/py`)

*   **`malicious_code_1.py`:** Sprawdź, czy system uniemożliwia odczyt wrażliwych plików. W logach workera powinieneś zobaczyć błąd dostępu do pliku.

*   **`malicious_code_2.py`:** Ten skrypt spowoduje fork bombe. Obserwuj, czy system jest w stanie ograniczyć zużycie zasobów i zapobiec awarii całego systemu.

*   **`malicious_code_3.py`:** Ten skrypt próbuje utworzyć odwrotną powłokę. Sprawdź, czy reguły sieciowe systemu blokują to połączenie.

### C (`/c`)

*   **`malicious_code_1.c`:** Podobnie jak w przypadku wersji w Pythonie, sprawdź, czy system uniemożliwia odczyt wrażliwych plików.

*   **`malicious_code_2.c`:** Ten program spowoduje fork bombe. Obserwuj, czy system jest w stanie ograniczyć zużycie zasobów.

*   **`malicious_code_3.c`:** Ten program próbuje utworzyć odwrotną powłokę. Sprawdź, czy reguły sieciowe systemu blokują to połączenie.
