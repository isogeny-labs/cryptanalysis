#include "m31.h"
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <time.h>

static double now(void) {
    struct timespec t;
    clock_gettime(CLOCK_MONOTONIC, &t);
    return t.tv_sec + t.tv_nsec * 1e-9;
}
int main(void) {
    enum { n = 65536, repeats = 8 };
    uint32_t *x = malloc(n * sizeof(*x));
    uint32_t *y = malloc(n * sizeof(*y));
    assert(x && y);
    uint32_t state = 291154;
    for (size_t j = 0; j < n; ++j) {
        state = state * 1664525u + 1013904223u;
        x[j] = state;
    }
    size_t sizes[] = {1,17,20,63,64,65,1024,n};
    for (size_t round = 0; round < 16; ++round) {
        for (size_t slot = 0; slot < 8; ++slot) {
            size_t chunk = sizes[(slot + round) % 8];
            double start = now();
            for (int r = 0; r < repeats; ++r)
                for (size_t j = 0; j < n; j += chunk)
                    m31_batch_inverse(x+j, y+j, chunk < n-j ? chunk : n-j);
            double ns = (now()-start)*1e9/(n*repeats);
            for (size_t j = 0; j < n; ++j) {
                uint32_t residue = x[j] % 2147483647u;
                assert(y[j] < 2147483647u);
                assert(residue ? ((uint64_t)residue*y[j])%2147483647u == 1 : y[j] == 0);
            }
            printf("%zu,%zu,%.4f\n", round, chunk, ns);
        }
    }
    free(x);
    free(y);
}
