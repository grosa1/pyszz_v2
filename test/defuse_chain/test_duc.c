int main() {
    int a;
    int c = 5;
    int d = c;
    a = 0;
    a = sum(a, c);
    int b = sum(a, c);
    for (int i=0; i<5; i++) {
        d += 1;
    }
    do {
        printf("%d\n", d);
        d--;
    } while(d > 0);
    if (d > 0) {
        return d;
    } else {
        return a;
    }
}
