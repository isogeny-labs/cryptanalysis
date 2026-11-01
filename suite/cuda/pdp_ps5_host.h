/*
 * pdp_ps5_host.h - the host side of the PS-5 replay: GF(2^n) for n <= 63 as
 * 64-bit words, the curve y^2 + xy = x^3 + x^2 + 1, the exact reference group
 * law, base points, and the PS-0 corpus reader.  A C port of the pieces of
 * `crypto`'s examples/pdp_speedup (group.rs, corpus.rs) that the replay needs;
 * deliberately slow and simple (shift-and-add multiplication), because it
 * only builds rows and confirms hits.  Host tools only.
 */
#ifndef PDP_PS5_HOST_H
#define PDP_PS5_HOST_H

#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#ifndef PS5_UNUSED
#    if defined(__GNUC__)
#        define PS5_UNUSED __attribute__((unused))
#    else
#        define PS5_UNUSED
#    endif
#endif

typedef struct {
    int n;
    uint64_t mod; /* the modulus as an integer, bit n set */
} Ps5Gf;

static PS5_UNUSED uint64_t ps5_gf_mul(const Ps5Gf *f, uint64_t a, uint64_t b)
{
    uint64_t r = 0;
    while (b) {
        if (b & 1u) r ^= a;
        b >>= 1;
        a <<= 1;
        if ((a >> f->n) & 1u) a ^= f->mod;
    }
    return r;
}

static PS5_UNUSED uint64_t ps5_gf_sqr(const Ps5Gf *f, uint64_t a) { return ps5_gf_mul(f, a, a); }

/* a^(2^n - 2) = prod_{i=1}^{n-1} a^(2^i); 0 maps to 0. */
static PS5_UNUSED uint64_t ps5_gf_inv(const Ps5Gf *f, uint64_t a)
{
    uint64_t r = 1, t = a;
    for (int i = 1; i < f->n; ++i) {
        t = ps5_gf_sqr(f, t);
        r = ps5_gf_mul(f, r, t);
    }
    return r;
}

/* ── z^2 + z = c by elimination on the F2-linear map z -> z^2 + z ───────── */

typedef struct {
    int have[64];
    uint64_t val[64], pre[64];
} Ps5As;

static PS5_UNUSED int ps5_clz_hi(uint64_t v) { return 63 - __builtin_clzll(v); }

static PS5_UNUSED void ps5_as_init(Ps5As *s, const Ps5Gf *f)
{
    memset(s, 0, sizeof *s);
    for (int i = 0; i < f->n; ++i) {
        uint64_t e = 1ull << i, v = ps5_gf_sqr(f, e) ^ e, w = e;
        while (v) {
            int b = ps5_clz_hi(v);
            if (s->have[b]) {
                v ^= s->val[b];
                w ^= s->pre[b];
            } else {
                s->have[b] = 1;
                s->val[b] = v;
                s->pre[b] = w;
                break;
            }
        }
    }
}

/* Returns 1 and sets *z, or 0 when Tr(c) = 1. */
static PS5_UNUSED int ps5_as_solve(const Ps5As *s, uint64_t c, uint64_t *z)
{
    uint64_t v = c, w = 0;
    while (v) {
        int b = ps5_clz_hi(v);
        if (!s->have[b]) return 0;
        v ^= s->val[b];
        w ^= s->pre[b];
    }
    *z = w;
    return 1;
}

/* ── the curve ───────────────────────────────────────────────────────── */

typedef struct {
    int inf;
    uint64_t x, y;
} Ps5Pt;

static PS5_UNUSED Ps5Pt ps5_neg(Ps5Pt p)
{
    if (!p.inf) p.y ^= p.x;
    return p;
}

/* Exact group law, every special case (identity, P + (-P), doubling, the
 * 2-torsion point (0, 1)); one inversion per call. */
static PS5_UNUSED Ps5Pt ps5_add(const Ps5Gf *f, Ps5Pt p, Ps5Pt q)
{
    Ps5Pt inf = {1, 0, 0};
    if (p.inf) return q;
    if (q.inf) return p;
    if (p.x == q.x) {
        if ((p.y ^ q.y) == p.x) return inf;
        /* p.y == q.y and p.x != 0: doubling */
        uint64_t lam = p.x ^ ps5_gf_mul(f, p.y, ps5_gf_inv(f, p.x));
        uint64_t x3 = ps5_gf_sqr(f, lam) ^ lam ^ 1u;
        uint64_t y3 = ps5_gf_sqr(f, p.x) ^ ps5_gf_mul(f, lam ^ 1u, x3);
        Ps5Pt r = {0, x3, y3};
        return r;
    }
    uint64_t lam = ps5_gf_mul(f, p.y ^ q.y, ps5_gf_inv(f, p.x ^ q.x));
    uint64_t x3 = ps5_gf_sqr(f, lam) ^ lam ^ p.x ^ q.x ^ 1u;
    uint64_t y3 = ps5_gf_mul(f, lam, p.x ^ x3) ^ x3 ^ p.y;
    Ps5Pt r = {0, x3, y3};
    return r;
}

static PS5_UNUSED int ps5_on_curve(const Ps5Gf *f, uint64_t x, uint64_t y)
{
    uint64_t x2 = ps5_gf_sqr(f, x);
    return (ps5_gf_sqr(f, y) ^ ps5_gf_mul(f, x, y)) == (ps5_gf_mul(f, x2, x) ^ x2 ^ 1u);
}

/* The smaller rational y for abscissa x, or 0 when x lifts to no point. */
static PS5_UNUSED int ps5_lift(const Ps5Gf *f, const Ps5As *as, uint64_t x, uint64_t *y)
{
    if (x == 0) {
        *y = 1;
        return 1;
    }
    uint64_t c = x ^ 1u ^ ps5_gf_sqr(f, ps5_gf_inv(f, x)), z;
    if (!ps5_as_solve(as, c, &z)) return 0;
    uint64_t yy = ps5_gf_mul(f, x, z);
    *y = yy < (yy ^ x) ? yy : (yy ^ x);
    return 1;
}

/* The four candidate third abscissae of the pair (P1, P2) and target R:
 * x(P1+P2+R), x(P1+P2-R), x(P1-P2+R), x(P1-P2-R); ok[k] = 0 where the sum is
 * the point at infinity. */
static PS5_UNUSED void ps5_thirds(const Ps5Gf *f, Ps5Pt p1, Ps5Pt p2, Ps5Pt r, uint64_t t[4],
                                  int ok[4])
{
    Ps5Pt zs[2] = {ps5_add(f, p1, p2), ps5_add(f, p1, ps5_neg(p2))};
    Ps5Pt rs[2] = {r, ps5_neg(r)};
    for (int k = 0; k < 2; ++k)
        for (int m = 0; m < 2; ++m) {
            Ps5Pt s = ps5_add(f, zs[k], rs[m]);
            ok[2 * k + m] = !s.inf;
            t[2 * k + m] = s.inf ? 0 : s.x;
        }
}

/* A target for which the group-law formulation can disagree with the
 * baseline: x_R = 0, x_R in V, or 1/x_R in V. */
static PS5_UNUSED int ps5_degenerate(const Ps5Gf *f, int l, uint64_t xr)
{
    return xr == 0 || xr < (1ull << l) || ps5_gf_inv(f, xr) < (1ull << l);
}

/* ── the frozen generator and the corpus ─────────────────────────────── */

typedef struct {
    uint64_t s;
} Ps5Rng;

static PS5_UNUSED uint64_t ps5_rng_next(Ps5Rng *r)
{
    uint64_t z = (r->s += 0x9E3779B97F4A7C15ull);
    z = (z ^ (z >> 30)) * 0xBF58476D1CE4E5B9ull;
    z = (z ^ (z >> 27)) * 0x94D049BB133111EBull;
    return z ^ (z >> 31);
}

typedef struct {
    int planted;
    uint32_t idx;
    uint64_t xr, yr;
    int found; /* the corpus verdict */
    size_t n_roots;
    uint64_t (*roots)[3]; /* sorted triples, lexicographically sorted list */
} Ps5Target;

typedef struct {
    int l, n;
    uint64_t modulus;
    size_t n_targets;
    Ps5Target *t;
    char digest_verdicts[65], digest_roots[65];
} Ps5Corpus;

static PS5_UNUSED int ps5_cmp3(const void *a, const void *b)
{
    const uint64_t *x = (const uint64_t *)a, *y = (const uint64_t *)b;
    for (int i = 0; i < 3; ++i) {
        if (x[i] != y[i]) return x[i] < y[i] ? -1 : 1;
    }
    return 0;
}

/* Reads the text format of corpus.rs `write_corpus`.  0 on success. */
static PS5_UNUSED int ps5_read_corpus(const char *text, Ps5Corpus *c)
{
    memset(c, 0, sizeof *c);
    size_t cap_t = 128;
    c->t = (Ps5Target *)calloc(cap_t, sizeof(Ps5Target));
    const char *p = text;
    while (*p) {
        const char *eol = strchr(p, '\n');
        size_t len = eol ? (size_t)(eol - p) : strlen(p);
        char line[512];
        if (len >= sizeof line) return -1;
        memcpy(line, p, len);
        line[len] = 0;
        p = eol ? eol + 1 : p + len;
        char a[64], b[64], d[64], e[64], g[64], h[64], i[64], j[64];
        unsigned u0;
        if (strncmp(line, "l ", 2) == 0)
            c->l = atoi(line + 2);
        else if (strncmp(line, "n ", 2) == 0)
            c->n = atoi(line + 2);
        else if (strncmp(line, "modulus ", 8) == 0)
            c->modulus = strtoull(line + 8, NULL, 16);
        else if (strncmp(line, "digest_verdicts ", 16) == 0)
            strncpy(c->digest_verdicts, line + 16, 64);
        else if (strncmp(line, "digest_roots ", 13) == 0)
            strncpy(c->digest_roots, line + 13, 64);
        else if (line[0] == 'T' && line[1] == ' ') {
            if (sscanf(line, "T %u %63s %63s %63s %63s %63s %63s %63s", &u0, a, b, d, e, g, h, i) <
                8)
                return -2;
            if (c->n_targets == cap_t) {
                cap_t *= 2;
                c->t = (Ps5Target *)realloc(c->t, cap_t * sizeof(Ps5Target));
                memset(c->t + c->n_targets, 0, (cap_t - c->n_targets) * sizeof(Ps5Target));
            }
            Ps5Target *t = &c->t[c->n_targets++];
            t->idx = u0;
            t->planted = a[0] == 'p';
            t->xr = strtoull(b, NULL, 16);
            t->yr = strtoull(d, NULL, 16);
            t->found = atoi(e);
            size_t nr = (size_t)atol(g);
            t->roots = (uint64_t(*)[3])calloc(nr ? nr : 1, sizeof(uint64_t[3]));
            (void)h;
            (void)j;
        } else if (line[0] == 'R' && line[1] == ' ') {
            Ps5Target *t = &c->t[c->n_targets - 1];
            unsigned long long r0, r1, r2;
            if (sscanf(line, "R %llx %llx %llx", &r0, &r1, &r2) != 3) return -3;
            t->roots[t->n_roots][0] = r0;
            t->roots[t->n_roots][1] = r1;
            t->roots[t->n_roots][2] = r2;
            t->n_roots++;
        }
    }
    return c->l > 0 && c->n > 0 && c->modulus ? 0 : -4;
}

static PS5_UNUSED void ps5_free_corpus(Ps5Corpus *c)
{
    for (size_t i = 0; i < c->n_targets; ++i) free(c->t[i].roots);
    free(c->t);
    memset(c, 0, sizeof *c);
}

#endif /* PDP_PS5_HOST_H */
