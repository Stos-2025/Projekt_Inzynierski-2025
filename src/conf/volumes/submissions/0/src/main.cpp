#include <iostream>
#include <stdio.h>
#include "add.h"

using namespace std;

void echo() {
    int n;
    cin >> n;
    for(int i = 0; i < n; i++) {
        cout << '1' << endl;
    }
}

void sum(){
    int n, a, sum = 0;
    cin >> n;
    for(int i = 0; i < n; i++) {
        cin >> a;
        sum = add(sum, a);
    }
    cout << sum << endl;
}

int main() {
    int neverUsed;
    int tab[] = {1, 2, 3};
    tab[3]=2;
    neverUsed++;
    // echo();
    sum();
    return 0;
}
