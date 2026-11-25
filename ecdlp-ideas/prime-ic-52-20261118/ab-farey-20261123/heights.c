/* heights.c — per-target rational height, for the selector experiment.
 *
 *   heights <dump.bin> <out.bin>
 *
 * dump.bin is what ecell writes with its `dump` argument: [n][cnt n][xval n].
 * out.bin is a byte per dlog k: floor(log2 h(x(k))), capped at 255, where
 * h(x) is the smallest B with x = a/b, |a|,|b| <= B, gcd(a,b)=1 — i.e. the
 * smallest factor-base height that contains x.  h(x) is read off the EEA on
 * (p, x): descend until r_i <= sqrt(p), then h = max(r_i, |t_i|).
 *
 * h(x) <= B  <=>  x is in the factor base X(B), so this file also tells us
 * which targets are *already* base elements (the degenerate case).
 */
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>

int main(int argc, char **argv) {
    if (argc < 3) { fprintf(stderr, "usage: %s dump.bin out.bin\n", argv[0]); return 2; }
    FILE *f = fopen(argv[1], "rb");
    if (!f) { perror("open"); return 1; }
    uint32_t n;
    if (fread(&n, 4, 1, f) != 1) return 1;
    uint32_t *cnt = malloc(4 * (size_t)n), *xs = malloc(4 * (size_t)n);
    if (fread(cnt, 4, n, f) != n) return 1;
    if (fread(xs, 4, n, f) != n) return 1;
    fclose(f);

    uint8_t *out = calloc(n, 1);
    uint64_t p = strtoull(getenv("HP") ? getenv("HP") : "0", 0, 10);
    if (!p) { fprintf(stderr, "set HP=<prime>\n"); return 2; }
    /* sqrt(p) by Newton */
    uint64_t lim = p;
    while (lim * lim > p) lim = (lim + p / lim) / 2;

    for (uint32_t k = 0; k < n; k++) {
        uint64_t x = xs[k];
        if (x == 0) { out[k] = 0; continue; }   /* R = O */
        int64_t r0 = (int64_t)p, r1 = (int64_t)x, t0 = 0, t1 = 1;
        while (r1 > (int64_t)lim) {
            int64_t q = r0 / r1;
            int64_t r2 = r0 - q * r1, t2 = t0 - q * t1;
            r0 = r1; r1 = r2; t0 = t1; t1 = t2;
        }
        int64_t a = r1 < 0 ? -r1 : r1;
        int64_t b = t1 < 0 ? -t1 : t1;
        uint64_t h = (uint64_t)(a > b ? a : b);
        uint32_t lvl = 0;
        while (h > 1) { h >>= 1; lvl++; }
        out[k] = lvl > 255 ? 255 : (uint8_t)lvl;
    }
    FILE *g = fopen(argv[2], "wb");
    if (!g) { perror("write"); return 1; }
    fwrite(&n, 4, 1, g);
    fwrite(out, 1, n, g);
    fclose(g);
    fprintf(stderr, "n=%u written\n", n);
    return 0;
}
