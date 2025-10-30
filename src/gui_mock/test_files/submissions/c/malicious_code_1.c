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

