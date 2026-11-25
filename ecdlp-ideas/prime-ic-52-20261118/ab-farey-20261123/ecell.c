/* ecell.c — exact relation-yield cell for a prime-field factor base.
 *
 *   ecell <p> <N> <m> <shape> <seed> <out.json>
 *
 * shape: 0 interval  x = 1,2,3,...
 *        1 farey     x = +-a/b, +-b/a over 1 <= a <= b <= B, gcd=1
 *        2 random    splitmix64 x values (distinct)
 *
 * The curve is E: y^2 = x^3 + 7 with #E(F_p) prime, so E ~ Z/n and every point
 * has a discrete log.  We build the table x -> k with k*G = (x, .), which turns
 * point addition into integer addition mod n.  Then for the base F (N points:
 * the dlog k and -k of every x on the curve) we enumerate ALL m-multisets and
 * accumulate the exact representation function
 *
 *        r(R) = #{ unordered m-multisets of F summing to R }.
 *
 * Sum over R of r(R) is C(N+m-1, m) for every shape; the experiment's question
 * is what the distribution does.  No sampling: every tuple is counted.
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <math.h>

typedef unsigned __int128 u128;
static uint64_t P;          /* field prime  */
static uint32_t NORD;       /* group order  */

static inline uint64_t mm(uint64_t a, uint64_t b) { return (uint64_t)((u128)a * b % P); }
static inline uint64_t madd(uint64_t a, uint64_t b) { uint64_t s = a + b; return s >= P ? s - P : s; }
static inline uint64_t msub(uint64_t a, uint64_t b) { return a >= b ? a - b : a + P - b; }

static uint64_t mpow(uint64_t a, uint64_t e) {
    uint64_t r = 1;
    while (e) { if (e & 1) r = mm(r, a); a = mm(a, a); e >>= 1; }
    return r;
}
static uint64_t minv(uint64_t a) { return mpow(a, P - 2); }

/* ---------- Jacobian arithmetic, y^2 = x^3 + 7 ---------- */
typedef struct { uint64_t X, Y, Z; } jac;

static jac jdbl(jac p) {
    if (p.Z == 0 || p.Y == 0) { return (jac){0, 0, 0}; }
    uint64_t A = mm(p.X, p.X), B = mm(p.Y, p.Y), C = mm(B, B);
    uint64_t t = madd(p.X, B), D = msub(msub(mm(t, t), A), C);
    D = madd(D, D);
    uint64_t E = madd(A, madd(A, A));
    uint64_t F = mm(E, E);
    uint64_t X3 = msub(F, madd(D, D));
    uint64_t c8 = mm(C, 8);                   /* 8C */
    uint64_t Y3 = msub(mm(E, msub(D, X3)), c8);
    uint64_t Z3 = mm(madd(p.Y, p.Y), p.Z);
    return (jac){X3, Y3, Z3};
}

static jac jadd_affine(jac p, uint64_t x2, uint64_t y2) {
    if (p.Z == 0) { return (jac){x2, y2, 1}; }
    uint64_t Z1Z1 = mm(p.Z, p.Z);
    uint64_t U2 = mm(x2, Z1Z1);
    uint64_t S2 = mm(y2, mm(p.Z, Z1Z1));
    uint64_t H = msub(U2, p.X);
    uint64_t R = msub(S2, p.Y);
    if (H == 0) {
        if (R == 0) return jdbl(p);
        return (jac){0, 0, 0};
    }
    uint64_t r = madd(R, R);                 /* r = 2(S2 - Y1) */
    uint64_t HH = mm(H, H);
    uint64_t I = madd(HH, HH); I = madd(I, I);   /* I = 4 H^2 */
    uint64_t J = mm(H, I);
    uint64_t V = mm(p.X, I);
    uint64_t X3 = msub(msub(mm(r, r), J), madd(V, V));
    uint64_t Y3 = msub(mm(r, msub(V, X3)), mm(madd(p.Y, p.Y), J));
    uint64_t Z3 = msub(msub(mm(madd(p.Z, H), madd(p.Z, H)), Z1Z1), HH);
    return (jac){X3, Y3, Z3};
}

static int is_prime32(uint32_t n) {
    if (n < 2) return 0;
    for (uint32_t d = 2; (uint64_t)d * d <= n; d++) if (n % d == 0) return 0;
    return 1;
}

/* ---------- rng ---------- */
static uint64_t sm_state;
static uint64_t sm(void) {
    uint64_t z = (sm_state += 0x9E3779B97F4A7C15ULL);
    z = (z ^ (z >> 30)) * 0xBF58476D1CE4E5B9ULL;
    z = (z ^ (z >> 27)) * 0x94D049BB133111EBULL;
    return z ^ (z >> 31);
}

/* ---------- factor base ---------- */
static uint32_t *base;       /* dlogs, size N */
static uint32_t nb;

static int push_dlog(uint32_t k) {
    base[nb++] = k;
    base[nb++] = (NORD - k) % NORD;
    return 1;
}

/* farey: enumerate pairs (a,b), 1<=a<=b<=B, by mediant recurrence.
 * x = +-a/b, +-b/a; the pair (1,1) yields only +-1.  Restart with a bigger
 * B until the requested number of POINTS is reached, then truncate. */
static void build_farey(uint32_t want, uint32_t *tab, uint32_t *Bout) {
    uint32_t B = 1;
    for (;;) {
        nb = 0;
        if (tab[0]) { base[nb++] = tab[0]; base[nb++] = (NORD - tab[0]) % NORD; }
        uint64_t a = 0, b = 1, c = 1, d = B;
        while (c <= B) {
            uint64_t ia = minv(a), ib = minv(b);
            uint64_t u = mm(a, ib), v = mm(b, ia);
            uint32_t xs[4]; int nx = 0;
            xs[nx++] = (uint32_t)u;
            xs[nx++] = (uint32_t)msub(0, u);
            if (a != b) { xs[nx++] = (uint32_t)v; xs[nx++] = (uint32_t)msub(0, v); }
            for (int j = 0; j < nx; j++) {
                uint32_t k = tab[xs[j]];
                if (k && nb + 2 <= want) push_dlog(k);
            }
            if (nb + 2 > want) break;
            uint64_t kk = (B + b) / d;
            uint64_t nc = kk * c - a, nd = kk * d - b;
            a = c; b = d; c = nc; d = nd;
        }
        if (nb + 2 > want || B > (1u << 22)) break;
        B = B * 2;
    }
    *Bout = B;
}

int main(int argc, char **argv) {
    if (argc < 7) { fprintf(stderr, "usage: %s p N m shape seed out\n", argv[0]); return 2; }
    P = strtoull(argv[1], 0, 10);
    uint32_t wantN = (uint32_t)atoi(argv[2]);
    int m = atoi(argv[3]);
    int shape = atoi(argv[4]);
    sm_state = strtoull(argv[5], 0, 10);
    const char *outpath = argv[6];

    /* 1. find a point and its order */
    uint64_t gx = 0, gy = 0;
    for (uint64_t x = 1; x < P; x++) {
        uint64_t rhs = madd(mm(x, mm(x, x)), 7);
        uint64_t y = mpow(rhs, (P + 1) / 4);         /* P = 3 mod 4 */
        if (mm(y, y) == rhs) { gx = x; gy = y; break; }
    }
    if (gx == 0) { fprintf(stderr, "no point found\n"); return 1; }
    if (argc > 7 && !strcmp(argv[7], "walk")) {
        jac c0 = (jac){gx, gy, 1};
        for (int i = 0; i < 10; i++) {
            uint64_t iz = minv(c0.Z), z2 = mm(iz, iz), z3 = mm(z2, iz);
            printf("%2d  Z=%llu  x=%llu  y=%llu\n", i + 1,
                   (unsigned long long)c0.Z,
                   (unsigned long long)mm(c0.X, z2), (unsigned long long)mm(c0.Y, z3));
            c0 = jadd_affine(c0, gx, gy);
        }
        return 0;
    }

    /* walk k*G, record x -> k in blocks with a batch inversion */
    uint32_t *tab = calloc(P, sizeof(uint32_t));
    if (!tab) { fprintf(stderr, "alloc tab failed\n"); return 1; }
    uint32_t n = 0;
    {
        jac p = (jac){0, 0, 0};                       /* O */
        jac *buf = malloc((size_t)(1 << 18) * sizeof(jac));
        uint64_t *zinv = malloc((size_t)(1 << 18) * sizeof(uint64_t));
        jac cur = (jac){gx, gy, 1};
        uint64_t k = 1;
        int done = 0;
        while (!done) {
            int cnt = 0;
            while (cnt < (1 << 18)) {
                if (cur.Z == 0) { done = 1; break; }
                buf[cnt++] = cur;
                cur = jadd_affine(cur, gx, gy);
                k++;
                if (k > 4 * P) { done = 1; break; }
            }
            /* Montgomery batch inversion of the Z column */
            uint64_t acc = 1;
            for (int i = 0; i < cnt; i++) { zinv[i] = acc; acc = mm(acc, buf[i].Z); }
            uint64_t inv = minv(acc);
            for (int i = cnt - 1; i >= 0; i--) {
                uint64_t zi = mm(inv, zinv[i]);
                inv = mm(inv, buf[i].Z);
                uint64_t z2 = mm(zi, zi), z3 = mm(z2, zi);
                uint64_t xa = mm(buf[i].X, z2);
                tab[xa] = n + (uint32_t)(i + 1);
            }
            n += cnt;
            if (done) break;
        }
        free(buf); free(zinv);
        (void)p;
    }
    /* n counts the stored points 1G..(ord-1)G; the walk stops at ord*G = O */
    n += 1;
    NORD = n;
    if (!is_prime32(n)) { fprintf(stderr, "order %u not prime\n", n); return 1; }

    /* 2. base */
    base = malloc((size_t)wantN * sizeof(uint32_t));
    uint32_t Bused = 0;
    if (shape == 0) {
        nb = 0;
        for (uint64_t x = 1; x < P && nb + 2 <= wantN; x++) {
            uint32_t k = tab[x];
            if (k) push_dlog(k);
        }
    } else if (shape == 1) {
        build_farey(wantN, tab, &Bused);
    } else {
        nb = 0;
        uint8_t *used = calloc(P, 1);
        while (nb < wantN) {
            uint64_t x = sm() % P;
            if (used[x]) continue;
            used[x] = 1;
            uint32_t k = tab[x];
            if (k && nb + 2 <= wantN) push_dlog(k);
        }
        free(used);
    }
    if (nb < wantN) { fprintf(stderr, "base short: %u < %u\n", nb, wantN); wantN = nb; }
    uint32_t N = wantN;

    /* 3. exact multiset enumeration */
    uint32_t *cnt = calloc(n, sizeof(uint32_t));
    if (!cnt) { fprintf(stderr, "alloc cnt failed\n"); return 1; }
    uint64_t tuples = 0;
    if (m == 2) {
        for (uint32_t i = 0; i < N; i++) {
            for (uint32_t j = i; j < N; j++) {
                uint32_t s = base[i] + base[j];
                if (s >= n) s -= n;
                cnt[s]++; tuples++;
            }
        }
    } else if (m == 3) {
        for (uint32_t i = 0; i < N; i++) {
            for (uint32_t j = i; j < N; j++) {
                uint32_t sij = base[i] + base[j];
                if (sij >= n) sij -= n;
                for (uint32_t k = j; k < N; k++) {
                    uint32_t s = sij + base[k];
                    if (s >= n) s -= n;
                    cnt[s]++; tuples++;
                }
            }
        }
    } else { fprintf(stderr, "m=%d unsupported\n", m); return 2; }

    /* 4. statistics */
    uint64_t sum = 0, sumsq = 0; uint32_t mx = 0; uint64_t nz = 0, ge2 = 0;
    uint64_t sum_x = 0, sumsq_x = 0; uint32_t mx_x = 0, nz_x = 0, ge2_x = 0;
    for (uint32_t r = 0; r < n; r++) {
        uint32_t c = cnt[r];
        if (c) { sum += c; sumsq += (uint64_t)c * c; nz++; if (c >= 2) ge2++; }
        if (c > mx) mx = c;
        if (r != 0) {                              /* R != O: the targets that matter */
            sum_x += c;
            sumsq_x += (uint64_t)c * c;
            if (c) { nz_x++; if (c >= 2) ge2_x++; }
            if (c > mx_x) mx_x = c;
        }
    }
    /* optional dump for post-hoc feature analysis: [n][cnt[n]][xval[n]] */
    if (argc > 8 && !strcmp(argv[7], "dump")) {
        uint32_t *xval = calloc(n, sizeof(uint32_t));
        for (uint64_t x = 1; x < P; x++) {
            uint32_t k = tab[x];
            if (k && k < n) {                       /* x(P) = x(-P) */
                xval[k] = (uint32_t)x;
                xval[(n - k) % n] = (uint32_t)x;
            }
        }
        FILE *g = fopen(argv[8], "wb");
        if (!g) { fprintf(stderr, "cannot dump %s\n", argv[8]); return 1; }
        fwrite(&n, 4, 1, g);
        fwrite(cnt, 4, n, g);
        fwrite(xval, 4, n, g);
        fclose(g);
        free(xval);
    }
    /* histogram of r */
    uint32_t hmax = mx + 2;
    uint64_t *hist = calloc(hmax, sizeof(uint64_t));
    for (uint32_t r = 0; r < n; r++) hist[cnt[r]]++;
    /* shape info: the height B for farey, the max x for interval */
    FILE *f = fopen(outpath, "w");
    if (!f) { fprintf(stderr, "cannot write %s\n", outpath); return 1; }
    fprintf(f, "{\"p\":%llu,\"n\":%u,\"N\":%u,\"m\":%d,\"shape\":%d,\"seed\":%s,\n",
            (unsigned long long)P, n, N, m, shape, argv[5]);
    fprintf(f, " \"B_used\":%u,\"tuples\":%llu,\"sum_r\":%llu,\"sum_r2\":%llu,\"max_r\":%u,\n",
            Bused, (unsigned long long)tuples, (unsigned long long)sum,
            (unsigned long long)sumsq, mx);
    fprintf(f, " \"distinct_R_with_relation\":%llu,\"distinct_R_ge2\":%llu,\n",
            (unsigned long long)nz, (unsigned long long)ge2);
    fprintf(f, " \"r_at_O\":%u,\"sum_r_exclO\":%llu,\"sum_r2_exclO\":%llu,\"max_r_exclO\":%u,"
               "\"nz_exclO\":%u,\"ge2_exclO\":%u,\n",
            cnt[0], (unsigned long long)sum_x, (unsigned long long)sumsq_x,
            mx_x, nz_x, ge2_x);
    fprintf(f, " \"hist\":[");
    int first = 1;
    for (uint32_t r = 0; r < hmax; r++) {
        if (hist[r] == 0) continue;
        fprintf(f, "%s[%u,%llu]", first ? "" : ",", r, (unsigned long long)hist[r]);
        first = 0;
    }
    fprintf(f, "],\"base_head\":[");
    for (uint32_t i = 0; i < (N < 8 ? N : 8); i++)
        fprintf(f, "%u%s", base[i], i + 1 < (N < 8 ? N : 8) ? "," : "");
    fprintf(f, "]}\n");
    fclose(f);
    printf("p=%llu n=%u N=%u m=%d shape=%d tuples=%llu sum=%llu (C=%llu) max=%u nz=%llu\n",
           (unsigned long long)P, n, N, m, shape,
           (unsigned long long)tuples, (unsigned long long)sum,
           (unsigned long long)tuples, mx, (unsigned long long)nz);
    return 0;
}
