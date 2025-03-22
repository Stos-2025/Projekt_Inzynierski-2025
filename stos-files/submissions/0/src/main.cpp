#include <iostream>
#include <stdio.h>
#include "add.h"

using namespace std;


void sum(){
    int n, a, sum = 0;
    cin >> n;
    for(int i = 0; i < n; i++) {
        cin >> a;
        sum +=a;
    }
    cout << sum << endl;
}

int main() {
    int neverUsed;
    sum();
    return 0;
}
