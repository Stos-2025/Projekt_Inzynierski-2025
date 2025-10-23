# Testy STOS

Testy integracyjne dla systemu STOS z użyciem gui_mock.

## Pliki

- `test_gui_mock.py` - Test integracyjny API
- `clear_results.sh` - Skrypt do czyszczenia wyników
- `requirements.txt` - Zależności Python

## Uruchamianie testów

### 1. Uruchom gui_mock (Terminal 1)
```bash
cd src/gui_mock
./start_gui_mock.sh
```

### 2. Uruchom test (Terminal 2)
```bash
cd tests
python3 test_gui_mock.py
```

## Czyszczenie wyników

Aby usunąć wyniki poprzednich testów:

```bash
cd tests
./clear_results.sh
```

Skrypt zapyta o potwierdzenie przed usunięciem plików.

Aby usunąć bez potwierdzenia:
```bash
./clear_results.sh --force
```

## Zobacz wyniki

Wyniki testów można zobaczyć w przeglądarce:
```
http://localhost:8080/results
```
