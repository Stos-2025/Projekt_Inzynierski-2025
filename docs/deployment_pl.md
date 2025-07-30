# Instrukcja wdrożenia systemu STOS

## 1. Przygotowanie obecnego systemu GUI

### Tworzenie nowych kolejek zgłoszeń
Opracowywany system zakłada użycie osobnych kolejek w celu zachowania kompatybilnosci wstecznej. W celu dodania nowych kolejek, w pliku `config.inc` należy dodać nowe wpisy osobno dla każdego języka do zmiennej `$availableQueues` (linia 31):

```php
array("stos2025", false, $cppNamePatterns),
array("stos2025-python", true, $pyNamePatterns)
```
- Pierwszy argument: nazwa kolejki.
- Drugi argument: czy wymagany jest wybór pliku głównego przy uruchomieniu.
- Trzeci argument: tablica wzorców plików do wysłania na serwer.

Przykład wzorców plików dla C/C++:
```php
array("*.c", "*.cpp", "*.cxx", "*.h", "*.hpp", "*.hxx");
```
### Dodanie tłumaczenia nazw kolejek
Domyślnie nowe kolejki są wyświetlane przez GUI jako "qname_" + nazwa kolejki.
Aby ustawić czytelne nazwy kolejek, należy w pliku `dict.inc` dodać do słownika `$dictData` (linia 20) odpowiednie tłumaczenia:
```php
"qname_stos2025" => array("pl" => "Stos 2025", "en" => "Stos 2025")
```


### Rozszerzenie listy dozwolonych adresów
Kolejnym krokiem, niezbędnym do poprawnego działania systemu, jest dodanie adresu do listy dozwolonych (whitelisty).
W tym celu, w pliku `configlocal.inc` należy dopisać do zmiennej `$globalACL` (linia 23) wpis z adresem hosta.


### Naprawa błędu związanego z wyborem głównego pliku (funkcjonalność wymagana np. dla pythona)
Ocenianie zadań w językach takich jak Python wymaga wskazania głównego pliku. Obecna wersja GUI zawiera taką funkcjonalność, jednak jej implementacja zawiera błąd.

W celu ich naprawy, w pliku `problem/put_pre.inc` w linii 319 należy usuńąć wywołanie funkcji `intval()`, ponieważ oczekiwany typ zmiennej `$mainfile` to string:

**Przed:**
```php
if(isset($pliki[""]) && isset($pliki[""]["mainfile"])) $mainfile = intval($pliki[""]["mainfile"]);
```
**Po:**
```php
if(isset($pliki[""]) && isset($pliki[""]["mainfile"])) $mainfile = $pliki[""]["mainfile"];
```

Dodatkowo, należy ustawić wartość `$pliki[""]["mainfile"]` np. w linii 525:

```php
$pliki[""]["mainfile"] = $mainfile;
```

---


## 2. Instalacja systemu
### Wymagania
Przed rozpoczęciem instalacji w docelowym środowisku wymagane są:

- **Docker**
- **Git** 


### Instalacja
Aby zainstalować system, można posłużyć się skryptem `install.sh`.
Skrypt odpowiada m.in. za dodanie użytkownika i grupy, zainstalowanie usługi systemd oraz stworzenie struktury katalogów.
Domyślną lokalizacją instalacji jest folder `/srv/stos2025`.

Uruchomienie skryptu (zdalne pobranie i wykonanie):
```sh
curl -s https://raw.githubusercontent.com/Stos-2025/Projekt_Inzynierski-2025/develop/src/deploy/install.sh | /bin/bash
```

### Konfiguracja
W kolejnym kroku należy zaktualizować plik konfiguracyjny `.env` (oraz opcjonalnie plik `compose.yml`), znajdujące się w folderze głownym np. `/srv/stos2025`. Plik `.env` w przypadku użycia skryptu instalacyjnego został wstępnie uzupełniony, należy go jednak dodatkowo uzupełnić ręcznie o pola: 
- GUI_URL
- QUEUE_NAMES
- QUEUE_LANG_DICT
```sh
#adress of the STOS GUI
GUI_URL=http://172.20.3.170 

#section set by install.sh
STOS_FILES=/srv/stos_files/data
DOCKER_SOCK=/var/run/docker.sock
DOCKER_GID=994 #getent group docker | cut -d: -f3
STOS_GID=1000 #getent group stos | cut -d: -f3


MASTER_API_KEY=STOS_API_KEY # only for development; production setup assumes endpoints are not exposed publicly

QUEUE_NAMES=stos2025,stos2025-python # names of the queues from STOS GUI
QUEUE_LANG_DICT={"stos2025": "c++", "stos2025-python": "python"} # internal names of code processing pipelines

#names of docker images from dockerhub
EXEC_IMAGE_NAME=d4m14n/stos:exec-latest
JUDGE_IMAGE_NAME=d4m14n/stos:judge-latest
LANG_COMPILER_DICT={"c++": "d4m14n/stos:gpp_comp-latest", "python": "d4m14n/stos:python3_comp-latest"}
```