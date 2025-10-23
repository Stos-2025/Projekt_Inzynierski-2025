#!/usr/bin/env python3
"""
Test integracyjny dla gui_mock API.

Ten test sprawdza poprawność komunikacji z gui_mock - mockowym serwerem GUI
używanym do testowania systemu STOS bez potrzeby uruchamiania pełnego środowiska.

Test weryfikuje:
- Czy gui_mock odpowiada na żądania HTTP
- Czy endpoint do wysyłania wyników działa poprawnie
- Czy wyniki są prawidłowo zapisywane
"""
import os
import requests


# Konfiguracja
GUI_URL = os.environ.get("GUI_URL", "http://localhost:8080")
TIMEOUT = 5


def test_gui_mock_result_submission():
    """
    Test wysyłania wyników ewaluacji do gui_mock.
    
    Ten test symuluje proces wysyłania wyników ewaluacji submisji przez worker
    do serwera GUI. Sprawdza:
    
    1. Czy gui_mock jest uruchomiony i odpowiada
    2. Czy endpoint /io-result.php przyjmuje wyniki w prawidłowym formacie
    3. Czy serwer zwraca poprawny status odpowiedzi
    
    Format wysyłanych danych:
    - id: identyfikator submisji
    - result: plik z wynikami testów (result.txt)
    - info: plik z informacjami o kompilacji i wykonaniu (info.txt)
    - debug: plik z logami debugowania (debug.txt)
    
    Oczekiwany wynik:
    - Status HTTP 200
    - Odpowiedź JSON: {"status": "ok"}
    """
    
    # KROK 1: Sprawdź czy gui_mock jest dostępny
    print(f"\n[1/3] Sprawdzanie dostępności gui_mock na {GUI_URL}...")
    try:
        health_response = requests.get(f"{GUI_URL}/results", timeout=TIMEOUT)
        assert health_response.status_code == 200, (
            f"gui_mock nie odpowiada poprawnie. "
            f"Oczekiwano status 200, otrzymano {health_response.status_code}"
        )
        print(f"      ✓ gui_mock jest dostępny")
    except requests.exceptions.RequestException as e:
        raise AssertionError(
            f"Nie można połączyć się z gui_mock pod adresem {GUI_URL}.\n"
            f"Upewnij się, że gui_mock jest uruchomiony.\n"
            f"Błąd: {e}"
        )
    
    # KROK 2: Przygotuj dane testowe
    print("\n[2/3] Przygotowywanie danych testowych...")
    
    test_submission_id = "test_integration_001"
    
    # Symulacja wyników z workera
    result_content = """WYNIKI TESTÓW:
Test 1: PASSED ✓
Test 2: PASSED ✓
Test 3: FAILED ✗
Test 4: PASSED ✓

PODSUMOWANIE: 3/4 testów zaliczonych
Punkty: 75/100
"""
    
    info_content = """INFORMACJE O KOMPILACJI I WYKONANIU:

Kompilacja: SUCCESS
Czas kompilacji: 1.2s
Ostrzeżenia: 0

Wykonanie:
- Test 1: 0.5s, 10MB pamięci
- Test 2: 0.3s, 8MB pamięci
- Test 3: Timeout (przekroczono limit czasu)
- Test 4: 0.4s, 9MB pamięci
"""
    
    debug_content = """DEBUG LOG:

[00:00.000] Worker started
[00:00.100] Submission received: test_integration_001
[00:00.150] Starting compilation...
[00:01.350] Compilation successful
[00:01.400] Running tests...
[00:01.900] Test 1: PASSED
[00:02.200] Test 2: PASSED
[00:04.200] Test 3: TIMEOUT
[00:04.600] Test 4: PASSED
[00:04.700] All tests completed
[00:04.750] Sending results to GUI...
"""
    
    # Przygotowanie danych do wysłania
    files = {
        'result': ('result.txt', result_content, 'text/plain'),
        'info': ('info.txt', info_content, 'text/plain'),
        'debug': ('debug.txt', debug_content, 'text/plain'),
    }
    
    data = {
        'id': test_submission_id
    }
    
    print(f"      ✓ ID submisji: {test_submission_id}")
    print(f"      ✓ Przygotowano 3 pliki wyników")
    
    # KROK 3: Wyślij wyniki do gui_mock
    print("\n[3/3] Wysyłanie wyników do gui_mock...")
    
    result_url = f"{GUI_URL}/io-result.php"
    
    try:
        response = requests.post(
            result_url,
            data=data,
            files=files,
            timeout=TIMEOUT
        )
    except requests.exceptions.RequestException as e:
        raise AssertionError(
            f"Błąd podczas wysyłania wyników do {result_url}.\n"
            f"Błąd: {e}"
        )
    
    # KROK 4: Weryfikacja odpowiedzi
    print(f"      ✓ Otrzymano odpowiedź HTTP {response.status_code}")
    
    # Sprawdź status HTTP
    assert response.status_code == 200, (
        f"Nieprawidłowy status odpowiedzi. "
        f"Oczekiwano 200, otrzymano {response.status_code}.\n"
        f"Odpowiedź serwera: {response.text}"
    )
    
    # Sprawdź format odpowiedzi JSON
    try:
        json_response = response.json()
    except ValueError:
        raise AssertionError(
            f"Odpowiedź nie jest w formacie JSON.\n"
            f"Otrzymana odpowiedź: {response.text}"
        )
    
    # Sprawdź status w odpowiedzi
    assert json_response.get("status") == "ok", (
        f"Nieprawidłowy status w odpowiedzi JSON.\n"
        f"Oczekiwano: {{'status': 'ok'}}\n"
        f"Otrzymano: {json_response}"
    )
    
    print(f"      ✓ Status odpowiedzi: OK")
    print(f"\n" + "="*70)
    print(f"TEST ZAKOŃCZONY POMYŚLNIE ✓")
    print(f"="*70)
    print(f"\nWyniki można zobaczyć pod adresem: {GUI_URL}/results")
    print(f"Szukaj submisji: {test_submission_id}")


if __name__ == "__main__":
    """
    Uruchomienie bezpośrednie (bez pytest).
    
    Użycie:
        python test_gui_mock.py
    """
    print("="*70)
    print("TEST INTEGRACYJNY: gui_mock API")
    print("="*70)
    
    try:
        test_gui_mock_result_submission()
    except AssertionError as e:
        print(f"\n" + "="*70)
        print(f"TEST NIEUDANY ✗")
        print(f"="*70)
        print(f"\nBłąd: {e}")
        exit(1)
    except Exception as e:
        print(f"\n" + "="*70)
        print(f"NIEOCZEKIWANY BŁĄD ✗")
        print(f"="*70)
        print(f"\nBłąd: {e}")
        import traceback
        traceback.print_exc()
        exit(1)

