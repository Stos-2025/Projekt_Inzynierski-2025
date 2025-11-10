## Instrukcja manualnej instalacji

### Wymagania:

- docker (zalecana wersja: 27.3.1)
- system operacyjny: Linux (najlepiej amd64)


## Konfiguracja

Konfiguracja odbywa się przez plik `src/.env`.
Przykładowa konfiguracja systemu Stos2025:

```bash
COMPOSE_PROJECT_NAME=stos2025    # nazwa projektu używana przez docker-compose
STOS_FILES=/home/stos/Projekt_Inzynierski-2025/stos_files    # katalog roboczy (stos_files)

GUI_URL=http://172.20.3.170    # adres interfejsu GUI

DOCKER_SOCK=/var/run/docker.sock    # ścieżka gniazda Dockera
DOCKER_GID=994    # ID grupy docker - uprawnienia do socketu (getent group docker | cut -d: -f3)
STOS_GID=993    # ID grupy stos2025 - uprawnienia do katalogu roboczego

# obrazy Docker
EXEC_IMAGE_NAME=d4m14n/stos:exec-1.0.0    # obraz do uruchamiania zadań
JUDGE_IMAGE_NAME=d4m14n/stos:judge-1.0.0    # obraz do oceniania
QUEUE_COMPILER_DICT={"stos2025": "d4m14n/stos:gpp_comp-1.0.0", "stos2025-python": "d4m14n/stos:python3_comp-1.0.0"}    # mapowanie kolejek -> obrazy kompilatorów

IS_DEBUG_MODE_ENABLED=true
```

## Stworzenie grupy systemowej i katalogu roboczego

Poniżej przykładowe polecenia do utworzenia grupy systemowej `stos2025`, katalogu roboczego oraz nadania niezbędnych uprawnień.

```bash
# (1) utwórz grupę 'stos2025' - jeśli grupa już istnieje, polecenie nic nie zrobi, np.
sudo groupadd -f stos2025

# (2) utwórz katalog roboczy projektu, np.
sudo mkdir -p /home/stos/Projekt_Inzynierski-2025/stos_files

# (3) przypisz grupę 'stos2025' do katalogu i ustaw prawa (2 = setgid, zapewnia dziedziczenie grupy dla nowych plików), np.
sudo chown -R :stos2025 /home/stos/Projekt_Inzynierski-2025/stos_files

# (4) sprawdź ID grupy 'stos2025'
getent group stos2025 | cut -d: -f3    # wyświetli GID grupy 'stos2025'
```

## Budowa obrazów

```bash
docker compose -f ./src/compose.yml up --build
```

lub

```bash
docker compose -f ./src/compose.yml build
```
