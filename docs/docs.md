# Dokumentacja Systemu STOS

> **System do Testowania Online Studentów - Dokumentacja Techniczna**

---

## Spis treści

1. [Wprowadzenie](#wprowadzenie)
2. [Moduł Common - Wspólne Komponenty](#moduł-common---wspólne-komponenty)
3. [Moduł Worker - Przetwarzanie Zgłoszeń](#moduł-worker---przetwarzanie-zgłoszeń)
4. [Architektura Systemu](#architektura-systemu)

---

## Wprowadzenie

System STOS (System do Testowania Online Studentów) to rozproszona platforma służąca do automatycznego testowania i oceniania zgłoszeń programistycznych studentów. System wykorzystuje technologię kontenerów Docker do izolowanego uruchamiania kodu oraz rozproszoną architekturę worker do skalowania mocy obliczeniowej.

### Główne komponenty systemu

- **Worker** - Moduł procesujący zgłoszenia i wykonujący testy
- **Common** - Wspólne narzędzia, schematy danych i definicje
- **GUI API** - Interfejs komunikacyjny z systemem webowym
- **STOS GUI** - Aplikacja webowa STOS z interfejsem graficznym

---

## Moduł Common - Wspólne Komponenty

Moduł `common` zawiera współdzielone komponenty wykorzystywane przez różne części systemu STOS, w tym schematy danych, enumy, narzędzia pomocnicze i definicje krotek.

### 1. Schematy danych (`schemas.py`)

#### 1.1. TestResultSchema

Reprezentuje wynik pojedynczego testu wykonanego dla zgłoszenia.

**Pola:**

- `test_name: str` - Nazwa/identyfikator testu (domyślnie: "")
- `grade: bool` - Czy test zakończył się sukcesem (domyślnie: False)
- `ret_code: Optional[int]` - Kod wyjścia zwrócony przez proces testowy
- `time: Optional[float]` - Czas wykonania w sekundach
- `memory: Optional[float]` - Zużycie pamięci w bajtach
- `info: Optional[str]` - Dodatkowe informacje lub komunikaty o błędach

**Przykład użycia:**

```python
test_result = TestResultSchema(
    test_name="test_01",
    grade=True,
    ret_code=0,
    time=0.523,
    memory=2048000,
    info="Test passed successfully"
)
```

---

#### 1.2. SubmissionResultSchema

Agreguje wszystkie wyniki testów dla zgłoszenia i zapewnia sformatowane wyjście do wyświetlenia użytkownikowi.

**Pola:**

- `points: int` - Łączna liczba punktów zdobytych za zgłoszenie (domyślnie: 0)
- `info: Optional[str]` - Ogólne informacje lub komunikaty debugowania
- `debug: Optional[str]` - Informacje debugowania dla rozwiązywania problemów
- `test_results: List[TestResultSchema]` - Lista poszczególnych wyników testów

**Metody:**

- `__str__() -> str` - Generuje sformatowaną reprezentację tekstową wyników z kolorową tabelą

**Przykład użycia:**

```python
result = SubmissionResultSchema(
    points=8,
    info="Compilation successful",
    test_results=[test1, test2, test3]
)
print(result)  # Wyświetla kolorową tabelę wyników
```

---

#### 1.3. TestSpecificationSchema

Definiuje limity zasobów i ograniczenia dla pojedynczego testu.

**Pola:**

- `test_name: str` - Nazwa/identyfikator testu (domyślnie: "")
- `time_limit: float` - Maksymalny czas wykonania w sekundach (domyślnie: 2)
- `total_memory_limit: int` - Maksymalne zużycie pamięci w bajtach (domyślnie: 256 MB)
- `stack_size_limit: Optional[int]` - Maksymalny rozmiar stosu w bajtach (opcjonalne)

**Przykład użycia:**

```python
test_spec = TestSpecificationSchema(
    test_name="test_large_data",
    time_limit=5.0,
    total_memory_limit=512 * 1024 * 1024  # 512 MB
)
```

---

#### 1.4. ProblemSpecificationSchema

Reprezentuje kompletną specyfikację problemu wraz z wszystkimi testami.

**Pola:**

- `id: str` - Unikalny identyfikator problemu
- `tests: List[TestSpecificationSchema]` - Lista specyfikacji testów (domyślnie: [])

**Metody:**

- `__str__() -> str` - Generuje sformatowaną tabelę testów z limitami zasobów

**Przykład użycia:**

```python
problem = ProblemSpecificationSchema(
    id="problem_123",
    tests=[test_spec1, test_spec2, test_spec3]
)
```

---

#### 1.5. SubmissionSchema

Reprezentuje kompletne zgłoszenie do ewaluacji.

**Pola:**

- `id: str` - Unikalny identyfikator zgłoszenia
- `comp_image: str` - Nazwa obrazu Docker dla kompilacji/wykonania
- `mainfile: Optional[str]` - Nazwa głównego pliku do kompilacji/wykonania
- `submitted_by: Optional[str]` - Identyfikator studenta, który złożył zgłoszenie
- `problem_specification: ProblemSpecificationSchema` - Specyfikacja rozwiązywanego problemu

**Przykład użycia:**

```python
submission = SubmissionSchema(
    id="sub_456",
    comp_image="python:3.9",
    mainfile="main.py",
    submitted_by="student_789",
    problem_specification=problem_spec
)
```

---

#### 1.6. SubmissionGuiSchema

Uproszczona reprezentacja danych zgłoszenia otrzymanych z interfejsu graficznego.

**Pola:**

- `submission_id: str` - Unikalny identyfikator zgłoszenia
- `problem_id: str` - Identyfikator rozwiązywanego problemu
- `student_id: str` - Identyfikator studenta składającego zgłoszenie

---

#### 1.7. VolumeMappingSchema

Definiuje konfigurację montowania woluminów Docker.

**Pola:**

- `host_path: str` - Ścieżka na maszynie hosta do zamontowania
- `container_path: str` - Ścieżka wewnątrz kontenera, gdzie wolumen będzie zamontowany
- `read_only: bool` - Czy montowanie ma być tylko do odczytu (domyślnie: True)

**Metody:**

- `key() -> str` - Zwraca ścieżkę hosta używaną jako klucz w mapowaniach woluminów Docker
- `value() -> Dict[str, str]` - Zwraca słownik konfiguracyjny dla API Docker

**Przykład użycia:**

```python
volume = VolumeMappingSchema(
    host_path="/host/data",
    container_path="/container/data",
    read_only=False
)
volumes = {volume.key(): volume.value()}
```

---

#### 1.8. ExecOutputSchema

Reprezentuje wyjście z wykonania programu wraz z metrykami wydajności.

**Pola:**

- `return_code: int` - Kod wyjścia zwrócony przez wykonany program
- `signal: Optional[int]` - Numer sygnału jeśli program został zakończony przez sygnał (opcjonalnie)
- `user_time: Optional[float]` - Czas CPU użyty przez program w trybie użytkownika, w sekundach (opcjonalnie)
- `total_memory: Optional[int]` - Całkowita pamięć użyta przez program w bajtach (opcjonalnie)

**Przykład użycia:**

```python
exec_output = ExecOutputSchema(
    return_code=0,
    signal=None,
    user_time=0.234,
    total_memory=4096000
)
```

---

#### 1.9. JudgeOutputSchema

Reprezentuje wynik oceny sędziego (judge) po porównaniu wyjścia programu z oczekiwanym wynikiem.

**Pola:**

- `grade: bool` - Czy test został zaliczony (True) czy nie (False), domyślnie: False
- `info: Optional[str]` - Dodatkowe informacje o wyniku oceny (opcjonalnie)

**Przykład użycia:**

```python
judge_output = JudgeOutputSchema(
    grade=True,
    info="Output matches expected result"
)
```

---

### 2. Enumy (`enums.py`)

#### 2.1. SubmissionStatus

Reprezentuje różne stany zgłoszenia w systemie.

**Wartości:**

- `NONE = 0` - Stan początkowy, zgłoszenie nie zostało utworzone
- `PENDING = 1` - Zgłoszenie utworzone i oczekuje na przetworzenie
- `RUNNING = 2` - Zgłoszenie jest obecnie wykonywane/przetwarzane
- `COMPLETED = 3` - Zgłoszenie zakończone pomyślnie
- `REPORTED = 4` - Wyniki zostały zgłoszone klientowi

**Przykład użycia:**

```python
status = SubmissionStatus.PENDING
if status == SubmissionStatus.RUNNING:
    print("Submission is being processed...")
```

---

#### 2.2. Ansi

Kody escape ANSI do formatowania i kolorowania tekstu w terminalu.

**Kategorie:**

**Style tekstu:**

- `RESET` - Resetuje wszystkie formatowania do domyślnych
- `BOLD` - Pogrubia tekst
- `UNDERLINE` - Podkreśla tekst
- `REVERSED` - Odwraca kolor tła i pierwszego planu

**Kolory tekstu:**

- `BLACK`, `RED`, `GREEN`, `YELLOW`, `BLUE`, `MAGENTA`, `CYAN`, `WHITE`

**Kolory tła:**

- `BG_BLACK`, `BG_RED`, `BG_GREEN`, `BG_YELLOW`, `BG_BLUE`, `BG_MAGENTA`, `BG_CYAN`, `BG_WHITE`

**Przykład użycia:**

```python
print(f"{Ansi.BOLD.value}{Ansi.GREEN.value}Success!{Ansi.RESET.value}")
print(f"{Ansi.RED.value}Error occurred{Ansi.RESET.value}")
```

---

### 3. Named Tuples (`tuples.py`)

#### 3.1. Timeout

Reprezentuje ustawienia timeout dla połączeń sieciowych.

**Pola:**

- `connect: float` - Timeout w sekundach dla nawiązania połączenia
- `read: float` - Timeout w sekundach dla odczytu danych z nawiązanego połączenia

**Przykład użycia:**

```python
timeout = Timeout(connect=5, read=15)
response = requests.get(url, timeout=timeout)
```

---

#### 3.2. StosGuiResultSchema

Reprezentuje dane wyników wysyłane do GUI STOS.

**Pola:**

- `result: str` - Główne dane wyników (zazwyczaj wyniki zgłoszenia w formacie JSON)
- `info: str` - Dodatkowe informacje lub wiadomości o ewaluacji
- `debug: str` - Informacje debugowania dla rozwiązywania problemów i diagnostyki

---

### 4. Funkcje Pomocnicze (`utils.py`)

#### 4.1. size_to_string()

Konwertuje rozmiar w bajtach na czytelną reprezentację tekstową.

```python
def size_to_string(value: float) -> str:
    """
    Konwertuje wartość w bajtach na sformatowany string.

    Args:
        value: Rozmiar w bajtach do konwersji

    Returns:
        Sformatowany string z rozmiarem i odpowiednią jednostką (np. "1.50 MiB")

    Raises:
        ValueError: Jeśli wartość jest ujemna
    """
```

**Jednostki:** B, KiB, MiB, GiB, TiB (jednostki binarne)

**Przykład użycia:**

```python
size = 2560000
print(size_to_string(size))  # "2.44 MiB"
```

---

#### 4.2. is_valid_destination_file_path()

Waliduje, czy ścieżka do pliku jest odpowiednia do zapisu.

```python
def is_valid_destination_file_path(destination_file_path: str) -> bool:
    """
    Sprawdza czy ścieżka może być użyta do zapisu pliku.

    Args:
        destination_file_path: Ścieżka do walidacji

    Returns:
        True jeśli ścieżka jest prawidłowa do zapisu pliku, False w przeciwnym razie
    """
```

**Walidacja obejmuje:**

- Istnienie katalogu nadrzędnego
- Uprawnienia do zapisu
- Sprawdzenie czy ścieżka nie wskazuje na katalog

---

#### 4.3. is_valid_destination_directory_path()

Waliduje, czy ścieżka do katalogu istnieje i jest zapisywalna.

```python
def is_valid_destination_directory_path(destination_directory_path: str) -> bool:
    """
    Sprawdza czy ścieżka wskazuje na istniejący katalog z uprawnieniami do zapisu.

    Args:
        destination_directory_path: Ścieżka katalogu do walidacji

    Returns:
        True jeśli ścieżka jest prawidłowym katalogiem z możliwością zapisu, False w przeciwnym razie
    """
```

---

## Moduł Worker - Przetwarzanie Zgłoszeń

Moduł Worker odpowiada za przetwarzanie zgłoszeń studentów w systemie STOS. Obejmuje integrację z API GUI, przetwarzanie wyników, parsowanie skryptów i logowanie.

### 0. Globals - Konfiguracja Globalna (`globals.py`)

Moduł globals definiuje klasę Globals, która służy jako scentralizowany kontener dla wszystkich globalnych parametrów konfiguracyjnych, instancji klientów i stanu runtime używanych w aplikacji worker.

#### 0.1. Klasa Globals

Kontener dla globalnej konfiguracji i stanu runtime workera STOS.

**Opis:**

Klasa Globals utrzymuje wszystkie globalne parametry konfiguracyjne, instancje klientów i stan runtime jako atrybuty na poziomie klasy. Jest używana do współdzielenia stanu między różnymi modułami aplikacji worker.

**Atrybuty konfiguracyjne:**

- `POOLING_INTERVAL: float` - Czas w sekundach oczekiwania między sprawdzaniem zgłoszeń
- `POOLING_INTERVAL_MAX: float` - Maksymalny czas backoff w sekundach gdy brak dostępnych zgłoszeń
- `FETCH_TIMEOUT: tuple[int, int]` - Krotka (connect, read) timeout w sekundach dla żądań API
- `CONTAINERS_TIMEOUT: int` - Maksymalny czas wykonania w sekundach dla kontenerów Docker
- `CONTAINERS_FILE_SIZE_LIMIT: str` - Limit rozmiaru pliku dla kontenerów (np. "5g")
- `CONTAINERS_MEMORY_LIMIT: str` - Limit pamięci dla kontenerów (np. "512m")

**Atrybuty runtime:**

- `WORKER_LOGGER: Logger` - Instancja loggera dla operacji workera
- `CLIENT: docker.DockerClient` - Klient Docker do zarządzania kontenerami
- `HOSTNAME: str` - Hostname bieżącego kontenera workera
- `STOS_GID: Optional[str]` - Opcjonalne ID grupy dla uprawnień plików STOS
- `NAME: str` - Przyjazna nazwa instancji workera
- `DATA_LOCAL_PATH: str` - Ścieżka lokalnego systemu plików dla danych workera
- `DATA_HOST_PATH: str` - Ścieżka systemu plików hosta dla danych workera
- `IS_DEBUG_MODE_ENABLED: bool` - Czy tryb debugowania jest włączony dla dodatkowego logowania
- `EXEC_IMAGE: str` - Nazwa obrazu Docker dla kontenerów EXEC
- `JUDGE_IMAGE: str` - Nazwa obrazu Docker dla konenerow JUDGE

**Przykład użycia:**

```python
from globals import Globals as G

# Inicjalizacja (wykonywana raz podczas startu)
G.WORKER_LOGGER = get_logger("worker", None, std_enabled=True)
G.CLIENT = docker.from_env()
G.POOLING_INTERVAL = 0.5

# Późniejsze użycie w innych modułach
G.WORKER_LOGGER.info("Processing submission...")
container = G.CLIENT.containers.run(G.EXEC_IMAGE, ...)
```

---

### 1. Adapter (`adapter.py`)

Moduł adaptera zapewnia funkcjonalność dla systemu worker STOS, obsługując komunikację z API GUI STOS w celu pobierania zgłoszeń, problemów i raportowania wyników.

#### 1.1. fetch_submission()

Pobiera zgłoszenie z API GUI STOS.

```python
def fetch_submission(destination_directory: str) -> Optional[SubmissionSchema]:
    """
    Pobiera zgłoszenie z API GUI STOS poprzez odpytywanie dostępnych kolejek.

    Args:
        destination_directory: Ścieżka do katalogu, gdzie pliki zgłoszenia będą rozpakowane

    Returns:
        Obiekt zgłoszenia z metadanymi i rozpakowanymi plikami, lub None jeśli brak zgłoszenia

    Raises:
        ValueError: Jeśli ścieżka docelowa jest nieprawidłowa
    """
```

**Proces:**

1. Iteruje po dostępnych kolejkach
2. Pobiera zgłoszenie jako plik ZIP
3. Rozpakowuje do katalogu docelowego
4. Tworzy obiekt SubmissionSchema z metadanymi

---

#### 1.2. fetch_problem()

Pobiera specyfikację problemu i pliki z API GUI STOS.

```python
def fetch_problem(
    problem_id: str,
    destination_directory: str,
    lib_destination_directory: Optional[str] = None
) -> ProblemSpecificationSchema:
    """
    Pobiera pliki problemu w tym wejścia testowe, oczekiwane wyjścia i specyfikacje skryptu.

    Args:
        problem_id: Unikalny identyfikator problemu
        destination_directory: Ścieżka do katalogu dla plików wejść/wyjść testów
        lib_destination_directory: Ścieżka do katalogu dla plików bibliotecznych

    Returns:
        Specyfikacja problemu z konfiguracjami testów i metadanymi
    """
```

**Pobierane pliki:**

- `*.in` - Pliki wejściowe testów
- `*.out` - Oczekiwane wyjścia testów
- `script.txt` - Specyfikacja testów w formacie STOS
- Dodatkowe pliki biblioteczne (opcjonalnie)

---

#### 1.3. report_result()

Raportuje wynik ewaluacji zgłoszenia do API GUI STOS.

```python
def report_result(submission_id: str, result: SubmissionResultSchema) -> None:
    """
    Formatuje wynik zgłoszenia i wysyła go do API GUI STOS.

    Args:
        submission_id: Unikalny identyfikator zgłoszenia
        result: Wynik ewaluacji zawierający wyniki testów i metadane

    Returns:
        None
    """
```

---

### 2. Klient API GUI (`stos_gui_api_client.py`)

Zapewnia funkcjonalność komunikacji z API GUI STOS.

#### 2.1. post_result()

Wysyła wyniki ewaluacji z powrotem do GUI STOS.

```python
def post_result(
    submission_id: str,
    result: StosGuiResultSchema,
    gui_url: str,
    timeout: Timeout
) -> str:
    """
    Wysyła wyniki ewaluacji (result, info, debug) do endpointu wyników GUI.

    Args:
        submission_id: Unikalny identyfikator zgłoszenia
        result: Wyniki ewaluacji zawierające result, info i debug
        gui_url: Bazowy URL GUI STOS
        timeout: Konfiguracja timeout żądania

    Returns:
        Tekst odpowiedzi z serwera GUI

    Raises:
        requests.HTTPError: Jeśli żądanie HTTP się nie powiedzie
    """
```

---

#### 2.2. get_problems_files_list()

Pobiera listę plików powiązanych z konkretnym problemem.

```python
def get_problems_files_list(problem_id: str, gui_url: str, timeout: Timeout) -> List[str]:
    """
    Pobiera listę plików dostępnych dla danego problemu z API filesystemu GUI STOS.

    Args:
        problem_id: Unikalny identyfikator problemu
        gui_url: Bazowy URL GUI STOS
        timeout: Konfiguracja timeout żądania

    Returns:
        Lista nazw plików powiązanych z problemem

    Raises:
        requests.HTTPError: Jeśli żądanie HTTP się nie powiedzie
    """
```

---

#### 2.3. get_file()

Pobiera konkretny plik z filesystemu problemu.

```python
def get_file(
    file_name: str,
    problem_id: str,
    destination_file_path: str,
    gui_url: str,
    timeout: Timeout
) -> None:
    """
    Pobiera plik z API filesystemu GUI STOS i zapisuje go w określonej lokalizacji.

    Args:
        file_name: Nazwa pliku do pobrania
        problem_id: Unikalny identyfikator problemu
        destination_file_path: Lokalna ścieżka gdzie plik powinien być zapisany
        gui_url: Bazowy URL GUI STOS
        timeout: Konfiguracja timeout żądania

    Returns:
        None

    Raises:
        ValueError: Jeśli ścieżka docelowa jest nieprawidłowa lub plik przekracza limit rozmiaru
        requests.HTTPError: Jeśli żądanie HTTP się nie powiedzie
    """
```

**Limit rozmiaru pliku:** 1 GiB

---

#### 2.4. get_submission()

Pobiera zgłoszenie z kolejki przetwarzania.

```python
def get_submission(
    queue_name: str,
    destination_file_path: str,
    gui_url: str,
    timeout: Timeout
) -> Optional[SubmissionGuiSchema]:
    """
    Pobiera zgłoszenie z API kolejki GUI STOS i zapisuje je w określonej lokalizacji.

    Args:
        queue_name: Nazwa kolejki do pobrania zgłoszenia
        destination_file_path: Lokalna ścieżka gdzie plik zgłoszenia powinien być zapisany
        gui_url: Bazowy URL GUI STOS
        timeout: Konfiguracja timeout żądania

    Returns:
        Dane zgłoszenia jeśli dostępne, None jeśli kolejka jest pusta

    Raises:
        ValueError: Jeśli ścieżka docelowa jest nieprawidłowa, brakuje nagłówków, lub plik przekracza limit
        requests.HTTPError: Jeśli żądanie HTTP się nie powiedzie (poza 404 który zwraca None)
    """
```

**Nagłówki odpowiedzi:**

- `X-Server-Id` - ID zgłoszenia
- `X-Param` - Parametry w formacie `problem_id;student_id`

---

#### 2.5. notify()

Wysyła powiadomienie dla konkretnego zgłoszenia.

```python
def notify(submission_id: str, message: str, gui_url: str, timeout: Timeout) -> None:
    """
    Wysyła wiadomość powiadomienia do API kolejki GUI STOS dla danego zgłoszenia.

    Args:
        submission_id: Unikalny identyfikator zgłoszenia
        message: Wiadomość powiadomienia do wysłania
        gui_url: Bazowy URL GUI STOS
        timeout: Konfiguracja timeout żądania

    Returns:
        None

    Raises:
        requests.HTTPError: Jeśli żądanie HTTP się nie powiedzie
    """
```

---

#### 2.6. mark_as_completed()

Oznacza zgłoszenie jako zakończone w kolejce GUI STOS.

```python
def mark_as_completed(submission_id: str, gui_url: str, timeout: Timeout) -> None:
    """
    Wysyła powiadomienie o zakończeniu do API kolejki GUI STOS, aby oznaczyć
    określone zgłoszenie jako zakończone.

    Args:
        submission_id: Unikalny identyfikator zgłoszenia do oznaczenia jako zakończone
        gui_url: Bazowy URL GUI STOS
        timeout: Konfiguracja timeout żądania

    Returns:
        None

    Raises:
        requests.HTTPError: Jeśli żądanie HTTP się nie powiedzie
    """
```

**Przykład użycia:**

```python
try:
    mark_as_completed("sub_12345", gui_url, timeout)
except requests.HTTPError:
    logger.error("Failed to mark submission as completed")
```

---

### 3. Parser Skryptów (`script_parser.py`)

Zapewnia funkcjonalność parsowania skryptów specyfikacji problemów STOS.

#### 3.1. extract_raw_problem_script()

Wyodrębnia surowe dane skryptu problemu.

```python
def extract_raw_problem_script(script: str) -> Tuple[Dict[int, Dict[str, Any]], List[str]]:
    """
    Parsuje skrypt specyfikacji problemu STOS i wyodrębnia konfiguracje testów.

    Args:
        script: Skrypt specyfikacji problemu STOS do sparsowania

    Returns:
        Krotka zawierająca:
        - Słownik mapujący ID testów na ich słowniki konfiguracyjne
        - Lista dodatkowych plików do włączenia
    """
```

**Obsługiwane komendy:**

- `C`, `CU`, `CO` - Komendy kompilacji
- `TST`, `T`, `TN` - Specyfikacje testów
- `J`, `JN`, `JUB`, `JUN` - Konfiguracje sędziego
- `AH`, `ADDHDR` - Dodatkowe pliki nagłówkowe
- `AS`, `ADDSRC` - Dodatkowe pliki źródłowe

---

#### 3.2. parse_script()

Parsuje skrypt STOS i tworzy obiekt ProblemSpecificationSchema.

```python
def parse_script(script: str, problem_id: str) -> Optional[ProblemSpecificationSchema]:
    """
    Konwertuje skrypt specyfikacji problemu STOS na strukturalny obiekt ProblemSpecificationSchema.

    Args:
        script: Skrypt specyfikacji problemu STOS do sparsowania
        problem_id: Unikalny identyfikator problemu

    Returns:
        Sparsowana specyfikacja problemu lub None jeśli parsowanie się nie powiedzie
    """
```

---

### 4. Formatowanie Wyników (`result_formatter.py`)

Formatuje wyniki ewaluacji zgłoszeń do różnych formatów wyjściowych.

#### 4.1. get_result_score()

Oblicza procentowy wynik dla wyniku zgłoszenia.

```python
def get_result_score(result: SubmissionResultSchema) -> float:
    """
    Oblicza procentowy wynik (0-100) na podstawie zaliczonych testów vs całkowita liczba testów.

    Args:
        result: Wynik zgłoszenia zawierający wyniki testów i punkty

    Returns:
        Wynik procentowy (0-100)
    """
```

---

#### 4.2. get_result_formatted()

Formatuje wynik zgłoszenia do formatu wyniku GUI STOS.

```python
def get_result_formatted(result: SubmissionResultSchema) -> str:
    """
    Tworzy sformatowany string wyniku zawierający wynik, specyfikacje formatu i wiadomość informacyjną.

    Args:
        result: Wynik zgłoszenia do sformatowania

    Returns:
        Sformatowany string wyniku z wynikiem i specyfikacjami formatu
    """
```

**Format wyjściowy:**

```
result=75.0
infoformat=html
debugformat=html
info=All tests passed
```

---

#### 4.3. get_info_formatted()

Formatuje wynik zgłoszenia do szczegółowego wyświetlania HTML.

```python
def get_info_formatted(result: SubmissionResultSchema) -> str:
    """
    Tworzy kompleksową tabelę HTML pokazującą wyniki testów ze stylizacją.

    Args:
        result: Wynik zgłoszenia do sformatowania

    Returns:
        Sformatowany string HTML z tabelą wyników testów i informacją o kompilacji
    """
```

**Funkcje:**

- Kolorowanie dla stanów pass/fail/error
- Tabela z czasem, pamięcią i kodami wyjścia
- Informacja o kompilacji
- Responsywny design z CSS

---

#### 4.4. get_debug_formatted()

Formatuje informacje debugowania do wyświetlania HTML.

```python
def get_debug_formatted(result: SubmissionResultSchema) -> str:
    """
    Konwertuje sekwencje escape ANSI w logach debugowania do formatu HTML.

    Args:
        result: Wynik zgłoszenia zawierający informacje debugowania

    Returns:
        Sformatowana informacja debugowania HTML lub pusty string jeśli brak informacji
    """
```

---

### 5. Logger (`logger.py`)

Zapewnia narzędzia logowania dla systemu worker STOS.

#### 5.1. get_logger()

Tworzy i konfiguruje logger z wyjściem do pliku i opcjonalnie do konsoli.

```python
def get_logger(func_name: str, log_file_path: str, std_enabled: bool) -> logging.Logger:
    """
    Tworzy instancję loggera z właściwym formatowaniem.

    Args:
        func_name: Identyfikator nazwy dla instancji loggera
        log_file_path: Ścieżka do pliku logu
        std_enabled: Czy włączyć logowanie do konsoli/stdout

    Returns:
        Skonfigurowana instancja loggera

    Raises:
        ValueError: Jeśli ścieżka do pliku logu jest nieprawidłowa
    """
```

**Format logu:**

```
%(asctime)s - %(levelname)s - %(message)s
```

---

#### 5.2. flush_logger()

Wymusza zapis wszystkich buforów loggera.

```python
def flush_logger(logger: logging.Logger) -> None:
    """
    Wymusza zapis buforów wszystkich handlerów loggera.

    Args:
        logger: Instancja loggera której handlery powinny być zrzucone

    Returns:
        None
    """
```

---

### 6. Worker Core (`worker.py`)

Główny moduł worker zawierający logikę przetwarzania zgłoszeń i zarządzania cyklem życia workera.

#### 6.1. initialize_globals()

Inicjalizuje globalną konfigurację i stan dla workera.

```python
def initialize_globals() -> None:
    """
    Ustawia globalną konfigurację workera poprzez inicjalizację loggera,
    klienta Docker, limitów zasobów i ustawień specyficznych dla środowiska.

    Funkcja musi być wywołana przed jakimikolwiek innymi operacjami workera,
    aby zapewnić prawidłową konfigurację całego stanu globalnego.

    Returns:
        None

    Raises:
        KeyError: Jeśli wymagane zmienne środowiskowe nie są ustawione
        docker.errors.DockerException: Jeśli klient Docker nie może być zainicjalizowany
            lub połączenie się nie powiedzie
    """
```

**Proces inicjalizacji:**

1. **Logger** - Konfiguruje główny logger workera z wyjściem do stdout
2. **Klient Docker** - Inicjalizuje połączenie z Dockerem i weryfikuje dostępność
3. **Limity zasobów** - Ustawia timeouty, limity pamięci i CPU dla kontenerów
4. **Zmienne środowiskowe** - Wczytuje konfigurację z środowiska (ścieżki, obrazy, tryb debug)

**Przykład użycia:**

```python
def main():
    try:
        initialize_globals()
        G.WORKER_LOGGER.info("Worker initialized successfully")
        mainloop()
    except Exception as e:
        print(f"Failed to initialize worker: {e}")
        exit(1)
```

---

#### 6.2. get_and_handle_submission()

Pobiera i przetwarza pojedyncze zgłoszenie przez kompletny workflow.

```python
def get_and_handle_submission() -> bool:
    """
    Orkiestruje cały cykl życia przetwarzania zgłoszenia.

    Proces obejmuje:
    1. Inicjalizacja struktury katalogów workera
    2. Pobranie zgłoszenia z kolejki
    3. Przetworzenie przez workflow ewaluacji
    4. Zebranie logów debugowania
    5. Raportowanie wyników z powrotem do API
    6. Archiwizacja plików jeśli tryb debugowania jest włączony

    Returns:
        bool: True jeśli zgłoszenie zostało pomyślnie przetworzone i zgłoszone,
            False jeśli żadne zgłoszenie nie było dostępne lub wystąpił błąd

    Raises:
        None: Funkcja obsługuje wszystkie wyjątki wewnętrznie i loguje błędy
    """
```

**Etapy przetwarzania:**

1. **Inicjalizacja plików** - Tworzy strukturę katalogów (bin, std, out, conf, src, lib, logs, tests)
2. **Pobranie zgłoszenia** - Pobiera ZIP zgłoszenia z kolejki i rozpakowuje
3. **Workflow** - Wywołuje `process_submission_workflow()` dla kompilacji, wykonania i oceny
4. **Logi debug** - Zbiera logi z pliku worker.log
5. **Raportowanie** - Wysyła wyniki do API GUI
6. **Archiwizacja** - Kopiuje pliki do katalogu debug (jeśli włączony)

**Obsługa błędów:**

- HTTP 400 - Ignorowany (przestarzałe zgłoszenie)
- Inne błędy - Logowane i zwracany False dla backoff

**Przykład użycia:**

```python
def mainloop():
    backoff = G.POOLING_INTERVAL
    while True:
        if get_and_handle_submission():
            backoff = G.POOLING_INTERVAL  # reset po sukcesie
        else:
            time.sleep(backoff)
            backoff = min(backoff * 2, G.POOLING_INTERVAL_MAX)
```

---

## Architektura Systemu

### Przepływ przetwarzania zgłoszenia

1. **Pobranie zgłoszenia** (`fetch_submission`)

   - Worker odpytuje kolejki
   - Pobiera plik ZIP zgłoszenia
   - Rozpakowanie do workspace'u

2. **Pobranie problemu** (`fetch_problem`)

   - Pobiera pliki testowe (.in, .out)
   - Pobiera skrypt specyfikacji
   - Parsuje konfigurację testów

3. **Kompilacja** (Docker container)

   - Uruchomienie obrazu kompilatora
   - Montowanie plików źródłowych
   - Generowanie plików wykonywalnych

4. **Wykonanie testów** (Docker container)

   - Uruchomienie plików binarnych dla każdego testu
   - Pomiar czasu i pamięci
   - Zapis wyjścia

5. **Ocenianie** (Docker container - Judge)

   - Porównanie wyjścia z oczekiwanym
   - Generowanie ocen testów
   - Tworzenie raportów

6. **Raportowanie** (`report_result`)
   - Formatowanie wyników do HTML
   - Wysłanie do API GUI
   - Archiwizacja (tryb debug)

### Izolacja i bezpieczeństwo

- **Kontenery Docker** - Izolacja procesów
- **Limity zasobów** - CPU, pamięć, czas
- **Sieć wyłączona** - Brak dostępu do internetu
- **Ulimits** - Limit rozmiaru plików, deskryptorów

### Skalowanie

- **Wiele workerów** - Równoległe przetwarzanie
- **Kolejki** - Podział według języków/kompilatorów
- **Docker** - Łatwe wdrażanie na wielu maszynach

---

## Podsumowanie

System STOS to kompletne rozwiązanie do automatycznego testowania zgłoszeń programistycznych. Wykorzystuje nowoczesne technologie konteneryzacji i rozproszonej architektury do zapewnienia:

- **Bezpieczeństwa** - Izolacja kodu w kontenerach
- **Skalowalności** - Łatwe dodawanie workerów
- **Niezawodności** - Obsługa błędów i timeoutów
- **Elastyczności** - Wsparcie dla wielu języków programowania

Dokumentacja ta zawiera pełny opis API i architektury systemu, umożliwiając zrozumienie i rozbudowę platformy STOS.

---

_Dokumentacja wygenerowana automatycznie z docstringów kodu źródłowego._
