/*
 * indexcalc.c - index calculus in (Z/pZ)^*, p < 2^64.
 */
#include "cryptanalysis/ca_indexcalc.h"
#include "cryptanalysis/ca_group.h"
#include "cryptanalysis/ca_pohlig.h"
#include "linalg.h"
#include "ca_internal.h"
#include "ic_trial.h"
#include "ic_rational.h"
#include "ic_trial32.h"
#include <limits.h>

#include <math.h>
#include <pthread.h>
#include <stdatomic.h>
#include <stdarg.h>
#include <stdio.h>

#define IC_SMALL_Q (1ULL << 24)   /* prime factors of p-1 up to this: Pohlig-Hellman */
#define IC_MAX_REL_COLS 96
#define IC_STEP_POWERS 4096
#define IC_STEP_POWERS  4096

/* Exact division by an odd factor-base prime q without a divide
 * instruction: with inv = q^{-1} mod 2^64 and lim = floor((2^64 - 1) / q),
 * q divides v iff v * inv <= lim (mod 2^64), and then v / q = v * inv.
 * The multiples of q are exactly the preimages of 0..lim under the
 * bijection v -> v * inv.  Unused for q = 2, which is a shift. */
typedef struct ic_fbdiv {
    uint64_t inv, lim;
} ic_fbdiv;

struct ca_ic_ctx {
    uint64_t p, zeta;             /* modulus and internal primitive root */
    uint64_t g, log_g;            /* user base and its log w.r.t. zeta */
    int g_known;
    uint64_t ord_g;
    uint32_t nfb;
    uint32_t *fb;                 /* factor base primes */
    ca_ic_divisor *fb_div;         /* fixed-divisor smoothness arithmetic */
    uint64_t *step_power;         /* reusable zeta^s, Montgomery form */
    ic_fbdiv *fb_div;             /* their exact-division constants */
    uint64_t *step_power;         /* reusable zeta^s in Montgomery form */
    uint32_t *fb_inv32, *fb_lim32; /* optional bounded-integer scan */
    ca_ic_scan32_fn scan32;
    uint64_t *fb_log;             /* logs mod p-1 */
    uint8_t *fb_known;
    ca_ic_params params;
    ca_rng rng;
    pthread_mutex_t rng_lock;
};

void ca_ic_params_default(ca_ic_params *p)
{
    memset(p, 0, sizeof(*p));
    p->method = CA_IC_LINEAR_SIEVE;
    p->threads = 1;
}

void ca_ic_auto_params(unsigned bits, uint32_t *B, uint32_t *C)
{
    /* Tuned on the ca_bench tool; grows roughly like L_p[1/2, 1/2]. */
    static const struct { unsigned bits; uint32_t B, C; } tab[] = {
        {20, 60, 40},   {24, 100, 60},   {28, 150, 100},  {32, 250, 150},
        {36, 400, 250}, {40, 700, 400},  {44, 1200, 700}, {48, 2000, 1100},
        {52, 3200, 1800}, {56, 5000, 2800}, {60, 8000, 4500}, {64, 13000, 7000},
    };
    size_t n = sizeof(tab) / sizeof(tab[0]);
    if (bits <= tab[0].bits) { *B = tab[0].B; *C = tab[0].C; return; }
    for (size_t i = 1; i < n; i++) {
        if (bits <= tab[i].bits) {
            double f = (double)(bits - tab[i - 1].bits) / (double)(tab[i].bits - tab[i - 1].bits);
            *B = (uint32_t)(tab[i - 1].B + f * (double)(tab[i].B - tab[i - 1].B));
            *C = (uint32_t)(tab[i - 1].C + f * (double)(tab[i].C - tab[i - 1].C));
            return;
        }
    }
    *B = tab[n - 1].B;
    *C = tab[n - 1].C;
}

static unsigned bitlen(uint64_t v) { unsigned b = 0; while (v) { v >>= 1; b++; } return b; }

/* ---- relation storage --------------------------------------------------- */

typedef struct relation {
    uint32_t n;
    uint32_t col[IC_MAX_REL_COLS];
    int32_t val[IC_MAX_REL_COLS];
    uint64_t rhs;                 /* known constant (mod p-1), moved to the right-hand side */
} relation;

typedef struct rel_list {
    relation *r;
    uint32_t n, cap;
} rel_list;

static int rel_push(rel_list *l, const relation *r)
{
    if (l->n == l->cap) {
        uint32_t nc = l->cap ? l->cap * 2 : 1024;
        /* malloc/copy/free rather than realloc: the growth is amortised and
         * rare, and the explicit handover keeps the old buffer's lifetime
         * unambiguous; calloc so a partly filled buffer is never copied from
         * uninitialised storage. */
        relation *nr = calloc(nc, sizeof(relation));
        if (!nr) return -1;
        if (l->n) memcpy(nr, l->r, (size_t)l->n * sizeof(relation));
        free(l->r);
        l->r = nr;
        l->cap = nc;
    }
    l->r[l->n++] = *r;
    return 0;
}

/* ---- smoothness test by trial division ---------------------------------- */

/* Factor v over the primes fb[0..nfb) ; writes exponents to (col,val) with
 * column offset col0.  Returns 1 if fully smooth. */
static int trial_factor(uint64_t v, const uint32_t *fb, const ca_ic_divisor *div,
                        uint32_t nfb, uint32_t col0,
                        relation *rel, uint32_t *cnt)
{
    uint32_t n = *cnt;
    for (uint32_t i = 0; i < nfb && v > 1; i++) {
        /* Most large residuals miss several consecutive primes. Test four
         * independent products together so the CPU can overlap them and
         * retire one branch per block. The largest square preserves the
         * prime-residual shortcut; any hit falls through to exact removal.
         * q=2 has inverse zero and therefore cannot be skipped here. */
        if (nfb - i >= 4 && (uint64_t)fb[i + 3] * fb[i + 3] <= v) {
            unsigned miss = (v * div[i].inverse > div[i].limit)
                          & (v * div[i + 1].inverse > div[i + 1].limit)
                          & (v * div[i + 2].inverse > div[i + 2].limit)
                          & (v * div[i + 3].inverse > div[i + 3].limit);
            if (miss) { i += 3; continue; }
        }
        uint32_t q = fb[i];
        if ((uint64_t)q * q > v) {
            /* v is prime: in the base iff <= fb[nfb-1] */
            if (v <= fb[nfb - 1]) {
                /* find index by binary search */
                uint32_t lo = i, hi = nfb;
                while (lo < hi) {
                    uint32_t mid = (lo + hi) / 2;
                    if (fb[mid] < v) lo = mid + 1; else hi = mid;
                }
                if (lo < nfb && fb[lo] == v) {
                    if (n >= IC_MAX_REL_COLS) return 0;
                    rel->col[n] = col0 + lo;
                    rel->val[n] = 1;
                    n++;
                    v = 1;
                    break;
                }
            }
            *cnt = n;
            return 0;
        }
        int32_t e = ca_ic_remove_prime(&v, q, &div[i]);
        if (e) {
            if (n >= IC_MAX_REL_COLS) return 0;
            rel->col[n] = col0 + i;
            rel->val[n] = e;
            n++;
        }
        i = 1;
    }
    uint32_t stop = v > 1 ? tf_square_bound(fb, i, nfb, v) : i;
    while (v > 1) {
        /* eight primes a step, one branch for the eight tests; a hit is
         * located by the scalar loop below */
        for (; i + 8 <= stop; i += 8) {
            const ic_fbdiv *d = div + i;
            const unsigned h0 = v * d[0].inv <= d[0].lim, h1 = v * d[1].inv <= d[1].lim;
            const unsigned h2 = v * d[2].inv <= d[2].lim, h3 = v * d[3].inv <= d[3].lim;
            const unsigned h4 = v * d[4].inv <= d[4].lim, h5 = v * d[5].inv <= d[5].lim;
            const unsigned h6 = v * d[6].inv <= d[6].lim, h7 = v * d[7].inv <= d[7].lim;
            if (h0 | h1 | h2 | h3 | h4 | h5 | h6 | h7) break;
        }
        for (; i + 4 <= stop; i += 4) {
            const ic_fbdiv *d = div + i;
            const unsigned h0 = v * d[0].inv <= d[0].lim, h1 = v * d[1].inv <= d[1].lim;
            const unsigned h2 = v * d[2].inv <= d[2].lim, h3 = v * d[3].inv <= d[3].lim;
            if (h0 | h1 | h2 | h3) break;
        }
        for (; i < stop; i++)
            if (v * div[i].inv <= div[i].lim) break;
        if (i == stop) break;
        const uint64_t inv = div[i].inv, lim = div[i].lim;
        int32_t e = 0;
        while (v * inv <= lim) {
            v *= inv;
            e++;
        }
        if (n >= IC_MAX_REL_COLS) return 0;
        rel->col[n] = col0 + i;
        rel->val[n] = e;
        n++;
        i++;
        stop = v > 1 ? tf_square_bound(fb, i, stop, v) : i;
    }
    if (v > 1 && i < nfb) {
        /* fb[i]^2 > v: v is prime, in the base iff <= fb[nfb-1] */
        if (v <= fb[nfb - 1]) {
            uint32_t lo = i, hi = nfb;
            while (lo < hi) {
                uint32_t mid = (lo + hi) / 2;
                if (fb[mid] < v)
                    lo = mid + 1;
                else
                    hi = mid;
            }
            if (lo < nfb && fb[lo] == v) {
                if (n >= IC_MAX_REL_COLS) return 0;
                rel->col[n] = col0 + lo;
                rel->val[n] = 1;
                n++;
                *cnt = n;
                return 1;
            }
        }
        *cnt = n;
        return 0;
    }
    *cnt = n;
    return v == 1;
}

/* Same output contract for rational trial integers bounded by UINT32_MAX. */
static int trial_factor32(uint32_t v, const ca_ic_ctx *ctx, uint32_t col0, relation *rel,
                          uint32_t *cnt)
{
    const uint32_t *fb = ctx->fb;
    const uint32_t *inverse = ctx->fb_inv32, *limit = ctx->fb_lim32;
    const uint32_t nfb = ctx->nfb;
    uint32_t n = *cnt;
    uint32_t i = 0;
    if (v > 1 && nfb > 0 && fb[0] == 2 && (uint64_t)4 <= v) {
        /* q = 2, a shift; the only even prime, so fb[0] if present */
        int32_t e = __builtin_ctz(v);
        v >>= e;
        if (e) {
            if (n >= IC_MAX_REL_COLS) return 0;
            rel->col[n] = col0;
            rel->val[n] = e;
            n++;
        }
        i = 1;
    }
    uint32_t stop = v > 1 ? tf_square_bound(fb, i, nfb, v) : i;
    while (v > 1) {
        i = ctx->scan32(v, inverse, limit, i, stop);
        if (i == stop) break;
        const uint32_t inv = inverse[i], lim = limit[i];
        int32_t e = 0;
        while (v * inv <= lim) {
            v *= inv;
            e++;
        }
        if (n >= IC_MAX_REL_COLS) return 0;
        rel->col[n] = col0 + i;
        rel->val[n] = e;
        n++;
        i++;
        stop = v > 1 ? tf_square_bound(fb, i, stop, v) : i;
    }
    if (v > 1 && i < nfb) {
        /* fb[i]^2 > v: v is prime, in the base iff <= fb[nfb-1] */
        if (v <= fb[nfb - 1]) {
            uint32_t lo = i, hi = nfb;
            while (lo < hi) {
                uint32_t mid = (lo + hi) / 2;
                if (fb[mid] < v)
                    lo = mid + 1;
                else
                    hi = mid;
            }
            if (lo < nfb && fb[lo] == v) {
                if (n >= IC_MAX_REL_COLS) return 0;
                rel->col[n] = col0 + lo;
                rel->val[n] = 1;
                n++;
                *cnt = n;
                return 1;
            }
        }
        *cnt = n;
        return 0;
    }
    *cnt = n;
    return v == 1;
}

/* ---- linear sieve ------------------------------------------------------- */

/* Barrett / Lemire residue for x < 2^64 using mu = floor((2^64 - 1) / q)
 * (the same constant stored in ic_fbdiv.lim).  Exact for every q > 1. */
static inline uint64_t ic_mod_u64(uint64_t x, uint64_t q, uint64_t mu)
{
    if (x < q) return x;
    uint64_t quo = (uint64_t)(((ca_u128)x * mu) >> 64);
    uint64_t r = x - quo * q;
    return r >= q ? r - q : r;
}

/* Canonical x mod q for a signed sieve coordinate. */
static inline uint64_t ic_mod_i64(int64_t x, uint64_t q, uint64_t mu)
{
    if (x >= 0) return ic_mod_u64((uint64_t)x, q, mu);
    uint64_t r = ic_mod_u64((uint64_t)(-x), q, mu);
    return r ? q - r : 0;
}

/* a^{-1} mod q for an odd factor-base prime q < 2^32 and 0 < a < q.
 * Same value as ca_invmod(a, q): a 32-bit binary almost-inverse (no 64-bit
 * division, no u128 Newton cleanup) because every fb prime fits in 32 bits
 * and the sieve's root setup is one inversion per prime per unit. */
static inline uint32_t ic_invmod_fb(uint32_t a, uint32_t q)
{
    uint32_t ninv = (q * 3u) ^ 2u;
    ninv *= 2u - q * ninv;
    ninv *= 2u - q * ninv;
    ninv *= 2u - q * ninv;
    ninv *= 2u - q * ninv; /* q^{-1} mod 2^32 */
    const uint32_t neg_ninv = 0u - ninv;

    uint32_t u = q, v = a, s = 1, r = 0, flip = 0;
    unsigned k = (unsigned)__builtin_ctz(v);
    v >>= k;
    for (;;) {
        const uint32_t d = u - v;
        if (d == 0) break;
        const int lt = u < v;
        const uint32_t sw = 0u - (uint32_t)lt;
        const unsigned z = (unsigned)__builtin_ctz(d);
        const uint32_t big = lt ? (v - u) : d;
        const uint32_t small = lt ? u : v;
        const uint32_t cb = (s & ~sw) | (r & sw);
        const uint32_t cs = (r & ~sw) | (s & sw);
        u = big >> z;
        v = small;
        s = cb << z;
        r = cs + cb;
        flip ^= sw;
        k += z;
    }
    if (u != 1) return 0;
    uint32_t x = flip ? r : s;
    while (k) {
        const unsigned j = k > 31 ? 31 : k;
        const uint32_t t = (x * neg_ninv) & ((1u << j) - 1u);
        uint64_t xx = ((uint64_t)t * q + x) >> j;
        if (xx >= q) xx -= q;
        x = (uint32_t)xx;
        k -= j;
    }
    return x;
}

typedef struct sieve_shared {
    uint64_t p, H, J;             /* H = ceil(sqrt p), J = H^2 - p */
    uint32_t B, C;
    const uint32_t *fb;
    const ca_ic_divisor *fb_div;
    const ic_fbdiv *fb_div;
    uint32_t nfb;
    const uint8_t *fb_log2;       /* rounded log2 of each prime */
    uint32_t col_prime0, col_h0;  /* column layout: factor base, then H+c */
    uint32_t ncols;
    uint32_t target_rels;
    atomic_int next_c1;           /* c1 = -C + index */
    atomic_int done;
    pthread_mutex_t lock;
    rel_list *rels;
    atomic_uint_fast64_t candidates;
    ca_status status;
} sieve_shared;

/* value V(c1, c2) = J + (c1 + c2) H + c1 c2 as a signed 128-bit integer */
static inline ca_i128 sieve_value(const sieve_shared *s, int64_t c1, int64_t c2)
{
    return (ca_i128)s->J + (ca_i128)(c1 + c2) * (ca_i128)s->H + (ca_i128)c1 * c2;
}

static void *sieve_thread(void *arg)
{
    sieve_shared *s = arg;
    /* The shared setup is written once before the threads start; copy the
     * values this thread indexes with so that the bounds are provably the
     * ones the buffers were sized for. */
    const uint32_t nfb = s->nfb;
    int64_t C = s->C;
    size_t len = (size_t)(2 * C + 1);
    uint8_t *arr = malloc(len);
    uint64_t *hmod = malloc(nfb * sizeof(uint64_t)); /* H mod q */
    uint64_t *jmod = malloc(nfb * sizeof(uint64_t)); /* J mod q */
    rel_list local = {0};
    if (!arr || !hmod || !jmod) {
        free(arr); free(hmod); free(jmod);
        pthread_mutex_lock(&s->lock);
        s->status = CA_ERR_NOMEM;
        atomic_store(&s->done, 1);
        pthread_mutex_unlock(&s->lock);
        return NULL;
    }
    for (uint32_t i = 0; i < nfb; i++) {
        hmod[i] = s->H % s->fb[i];
        jmod[i] = s->J % s->fb[i];
    }
    uint64_t cand_count = 0;
    while (!atomic_load(&s->done)) {
        int idx = atomic_fetch_add(&s->next_c1, 1);
        if (idx > 2 * C) break;
        int64_t c1 = idx - C;
        /* sieve c2 in [c1, C] */
        int64_t c2lo = c1, c2hi = C;
        size_t n = (size_t)(c2hi - c2lo + 1);
        memset(arr, 0, n);
        for (uint32_t i = 0; i < nfb; i++) {
            uint64_t q = s->fb[i];
            uint64_t mu = s->fb_div[i].lim; /* floor((2^64-1)/q) */
            /* a = (H + c1) mod q, b = (J + c1 H) mod q ; root: c2 = -b / a */
            uint64_t c1m = ic_mod_i64(c1, q, mu);
            uint64_t a = hmod[i] + c1m;
            if (a >= q) a -= q;
            if (a == 0) continue;
            /* c1m,hmod < q ⇒ product + jmod < q^2; Barrett closes it. */
            uint64_t b = ic_mod_u64(jmod[i] + c1m * hmod[i], q, mu);
            /* Factor-base primes are uint32_t; 32-bit inv matches ca_invmod.
             * q = 2 is even: a is 1 and its inverse is 1. */
            uint64_t inv = q == 2 ? 1 : ic_invmod_fb((uint32_t)a, (uint32_t)q);
            uint64_t prod = ic_mod_u64(b * inv, q, mu);
            uint64_t root = prod ? q - prod : 0; /* c2 == root (mod q) */
            /* first c2 >= c2lo with c2 == root mod q */
            uint64_t c2lo_m = ic_mod_i64(c2lo, q, mu);
            uint64_t gap = root >= c2lo_m ? root - c2lo_m : root + q - c2lo_m;
            int64_t start = c2lo + (int64_t)gap;
            uint8_t lg = s->fb_log2[i];
            for (int64_t c2 = start; c2 <= c2hi; c2 += (int64_t)q) arr[c2 - c2lo] += lg;
        }
        /* scan candidates: reject by log-sieve surplus without bitlen —
         * av >= 2^lim ⇒ bitlen(av) > lim = arr[k]+6, same filter as before. */
        for (size_t k = 0; k < n; k++) {
            unsigned lim = (unsigned)arr[k] + 6;
            int64_t c2 = c2lo + (int64_t)k;
            ca_i128 v = sieve_value(s, c1, c2);
            uint64_t av = v < 0 ? (uint64_t)(-v) : (uint64_t)v;
            if (av == 0) continue;
            if (lim < 64 && (av >> lim)) continue;
            cand_count++;
            relation rel;
            memset(&rel, 0, sizeof(rel));
            uint32_t cnt = 0;
            if (!trial_factor(av, s->fb, s->fb_div, s->nfb, s->col_prime0, &rel, &cnt)) continue;
            /* (H+c1)(H+c2) == sign * prod q^e  =>
             *   log(H+c1) + log(H+c2) - sum e log q = log(sign) */
            for (uint32_t i = 0; i < cnt; i++) rel.val[i] = -rel.val[i];
            if (cnt + 2 > IC_MAX_REL_COLS) continue;
            if (c1 == c2) {
                rel.col[cnt] = s->col_h0 + (uint32_t)(c1 + C);
                rel.val[cnt] = 2;
                cnt++;
            } else {
                rel.col[cnt] = s->col_h0 + (uint32_t)(c1 + C);
                rel.val[cnt] = 1;
                cnt++;
                rel.col[cnt] = s->col_h0 + (uint32_t)(c2 + C);
                rel.val[cnt] = 1;
                cnt++;
            }
            rel.n = cnt;
            rel.rhs = v < 0 ? (s->p - 1) / 2 : 0; /* log(-1) = (p-1)/2 */
            if (rel_push(&local, &rel) < 0) break;
        }
        if (local.n >= 256) {
            pthread_mutex_lock(&s->lock);
            for (uint32_t i = 0; i < local.n; i++) rel_push(s->rels, &local.r[i]);
            if (s->rels->n >= s->target_rels) atomic_store(&s->done, 1);
            pthread_mutex_unlock(&s->lock);
            local.n = 0;
        }
    }
    pthread_mutex_lock(&s->lock);
    for (uint32_t i = 0; i < local.n; i++) rel_push(s->rels, &local.r[i]);
    if (s->rels->n >= s->target_rels) atomic_store(&s->done, 1);
    pthread_mutex_unlock(&s->lock);
    atomic_fetch_add(&s->candidates, cand_count);
    free(local.r);
    free(arr); free(hmod); free(jmod);
    return NULL;
}

/* ---- random exponent collector ----------------------------------------- */

typedef struct rexp_shared {
    uint64_t p, zeta;
    const uint64_t *step_power;
    const uint32_t *fb;
    const ca_ic_divisor *fb_div;
    const ic_fbdiv *fb_div;
    uint32_t nfb;
    uint32_t col_prime0;
    uint32_t target_rels;
    uint64_t max_tries;
    atomic_int done;
    pthread_mutex_t lock;
    rel_list *rels;
    atomic_uint_fast64_t tests;
    uint64_t seed;
    atomic_int tid;
} rexp_shared;

static void *rexp_thread(void *arg)
{
    rexp_shared *s = arg;
    ca_rng rng;
    ca_rng_seed(&rng, s->seed ^ (0x9E3779B97F4A7C15ULL * (uint64_t)(atomic_fetch_add(&s->tid, 1) + 1)));
    ca_mont m;
    ca_mont_init(&m, s->p);
    uint64_t zm = ca_mont_to(&m, s->zeta);
    uint64_t e = 1 + ca_rng_below(&rng, s->p - 2);
    uint64_t cur = ca_mont_pow(&m, zm, e);
    uint64_t tests = 0;
    rel_list local = {0};
    while (!atomic_load(&s->done)) {
        /* step e by a random small amount to keep exponentiation cheap */
        uint64_t step = 1 + ca_rng_below(&rng, 255);
        cur = ca_mont_mul(&m, cur, s->step_power[step]);
        e = (e + step) % (s->p - 1);
        uint64_t v = ca_mont_from(&m, cur);
        tests++;
        relation rel;
        memset(&rel, 0, sizeof(rel));
        uint32_t cnt = 0;
        if (trial_factor(v, s->fb, s->fb_div, s->nfb, s->col_prime0, &rel, &cnt)) {
            rel.n = cnt;
            rel.rhs = e; /* sum e_q log q == e */
            rel_push(&local, &rel);
            if (local.n >= 64) {
                pthread_mutex_lock(&s->lock);
                for (uint32_t i = 0; i < local.n; i++) rel_push(s->rels, &local.r[i]);
                if (s->rels->n >= s->target_rels) atomic_store(&s->done, 1);
                pthread_mutex_unlock(&s->lock);
                local.n = 0;
            }
        }
        if (s->max_tries && tests > s->max_tries) break;
    }
    pthread_mutex_lock(&s->lock);
    for (uint32_t i = 0; i < local.n; i++) rel_push(s->rels, &local.r[i]);
    if (s->rels->n >= s->target_rels) atomic_store(&s->done, 1);
    pthread_mutex_unlock(&s->lock);
    atomic_fetch_add(&s->tests, tests);
    free(local.r);
    return NULL;
}

/* ---- solving ------------------------------------------------------------ */

/* Logs of the factor base modulo the "small" part of p-1 via Pohlig-Hellman. */
static ca_status small_part_logs(const ca_ic_ctx *ctx, uint64_t m_small, uint64_t *out)
{
    if (m_small == 1) { memset(out, 0, ctx->nfb * sizeof(uint64_t)); return CA_OK; }
    uint64_t p = ctx->p;
    ca_group g;
    ca_status rc = ca_group_zp_init(&g, p, m_small);
    if (rc != CA_OK) return rc;
    /* base = zeta^((p-1)/m_small), target = q^((p-1)/m_small) */
    uint64_t cof = (p - 1) / m_small;
    ca_elem base, target;
    uint64_t w[4] = {ca_powmod(ctx->zeta, cof, p), 0, 0, 0};
    ca_group_encode(&g, &base, w);
    ca_dlog_params dp;
    ca_dlog_params_default(&dp);
    dp.solver = CA_SOLVER_BSGS;
    for (uint32_t i = 0; i < ctx->nfb; i++) {
        w[0] = ca_powmod(ctx->fb[i], cof, p);
        ca_group_encode(&g, &target, w);
        rc = ca_pohlig_hellman(&g, &base, &target, &dp, &out[i], NULL);
        if (rc != CA_OK) return rc;
    }
    return CA_OK;
}

/* Build the sparse matrix from relations, moving known columns to the rhs. */
static ca_status build_matrix(const rel_list *rels, uint32_t ncols, uint64_t pm1, ca_spmat *A,
                              uint64_t **b_out)
{
    ca_status rc = ca_spmat_init(A, ncols, rels->n, rels->n * 16);
    if (rc != CA_OK) return rc;
    /* calloc: zero is the harmless rhs for any entry that is never written. */
    uint64_t *b = calloc(rels->n ? rels->n : 1, sizeof(uint64_t));
    if (!b) { ca_spmat_free(A); return CA_ERR_NOMEM; }
    for (uint32_t i = 0; i < rels->n; i++) {
        const relation *r = &rels->r[i];
        rc = ca_spmat_add_row(A, r->col, r->val, r->n);
        if (rc != CA_OK) { free(b); ca_spmat_free(A); return rc; }
        b[i] = r->rhs % pm1;
    }
    /* The solvers read b[0..A->rows) and x/known[0..A->cols), and those
     * buffers are sized from rels->n and ncols here: check that the matrix
     * agrees rather than trust bookkeeping done on the other side of the
     * sparse-matrix module boundary. */
    if (A->rows != rels->n || A->cols != ncols) {
        free(b);
        ca_spmat_free(A);
        return CA_ERR_INTERNAL;
    }
    *b_out = b;
    return CA_OK;
}

/* Exact elimination for linear-sieve relations. Included after relation's
 * definition. Auxiliary columns occur as h_u+h_v or 2*h_u. */

#include <limits.h>

static ca_status build_graph_matrix(const rel_list *rels, uint32_t ncols,
                                    uint32_t nfb, uint64_t modulus,
                                    ca_spmat *A, uint64_t **b_out)
{
    const uint32_t none = UINT32_MAX;
    uint32_t nv = ncols - nfb;
    /* Bound the dense expression workspace; larger instances use CSR as
     * before. All persistent relation output remains sparse. */
    if (!nv || !nfb || (size_t)nv > (64u * 1024u * 1024u) / sizeof(int32_t) / nfb ||
        rels->n > UINT32_MAX / 2) return CA_ERR_INVALID;
    ca_status rc = CA_ERR_NOMEM;
    uint32_t *u = malloc((size_t)rels->n * sizeof(*u));
    uint32_t *v = malloc((size_t)rels->n * sizeof(*v));
    uint32_t *head = malloc((size_t)nv * sizeof(*head));
    uint32_t *next = malloc((size_t)rels->n * 2 * sizeof(*next));
    uint32_t *queue = malloc((size_t)nv * sizeof(*queue));
    uint32_t *component = malloc((size_t)nv * sizeof(*component));
    /* per-component vertex/edge counts and compact column ids: components that
     * are trees contribute only 0 = 0 rows, so they need no auxiliary column */
    uint32_t *vcount = calloc(nv ? nv : 1, sizeof(*vcount));
    uint32_t *ecount = calloc(nv ? nv : 1, sizeof(*ecount));
    uint32_t *comp_col = malloc((nv ? nv : 1) * sizeof(*comp_col));
    int8_t *sign = calloc(nv, sizeof(*sign));
    int32_t *expr = calloc((size_t)nv * nfb, sizeof(*expr));
    uint64_t *constant = calloc(nv, sizeof(*constant));
    int64_t *row = calloc(nfb, sizeof(*row));
    uint32_t *cols = malloc(((size_t)nfb + 1) * sizeof(*cols));
    int32_t *vals = malloc(((size_t)nfb + 1) * sizeof(*vals));
    uint64_t *rhs = calloc(rels->n ? rels->n : 1, sizeof(*rhs));
    int initialized = 0;
    if (!u || !v || !head || !next || !queue || !component || !sign || !expr ||
        !constant || !row || !cols || !vals || !rhs) goto done;
    for (uint32_t j = 0; j < nv; ++j) head[j] = none;
    for (uint32_t i = 0; i < rels->n; ++i) {
        const relation *r = &rels->r[i];
        u[i] = v[i] = none;
        unsigned count = 0;
        for (uint32_t k = 0; k < r->n; ++k) {
            if (r->col[k] < nfb) continue;
            if (r->col[k] >= ncols || ++count > 2) { rc = CA_ERR_INVALID; goto done; }
            uint32_t node = r->col[k] - nfb;
            if (r->val[k] == 2 && count == 1) u[i] = v[i] = node;
            else if (r->val[k] == 1) {
                if (count == 1) u[i] = node;
                else if (v[i] == none) v[i] = node;
                else { rc = CA_ERR_INVALID; goto done; }
            } else { rc = CA_ERR_INVALID; goto done; }
        }
        if (!count) continue;
        if (u[i] == none || v[i] == none) { rc = CA_ERR_INVALID; goto done; }
        next[2 * i] = head[u[i]]; head[u[i]] = 2 * i;
        next[2 * i + 1] = head[v[i]]; head[v[i]] = 2 * i + 1;
    }
    uint32_t nc = 0;
    for (uint32_t root = 0; root < nv; ++root) {
        if (sign[root] || head[root] == none) continue;
        uint32_t first = 0, end = 0;
        uint32_t cid = nc++;
        sign[root] = 1;
        component[root] = cid;
        queue[end++] = root;
        while (first < end) {
            uint32_t parent = queue[first++];
            vcount[cid]++;
            for (uint32_t edge = head[parent]; edge != none; edge = next[edge]) {
                ecount[cid]++; /* half-edge: each edge is seen from both ends */
                uint32_t i = edge / 2;
                uint32_t child = u[i] == parent ? v[i] : u[i];
                if (sign[child]) continue;
                sign[child] = (int8_t)-sign[parent];
                component[child] = component[parent];
                constant[child] = ca_submod(rels->r[i].rhs % modulus, constant[parent], modulus);
                int32_t *dst = expr + (size_t)child * nfb;
                const int32_t *src = expr + (size_t)parent * nfb;
                for (uint32_t j = 0; j < nfb; ++j) {
                    if (src[j] == INT32_MIN) { rc = CA_ERR_INVALID; goto done; }
                    dst[j] = -src[j];
                }
                const relation *r = &rels->r[i];
                for (uint32_t k = 0; k < r->n; ++k) {
                    uint32_t j = r->col[k];
                    if (j >= nfb) continue;
                    int64_t value = (int64_t)dst[j] - r->val[k];
                    if (value <= INT32_MIN || value > INT32_MAX) { rc = CA_ERR_INVALID; goto done; }
                    dst[j] = (int32_t)value;
                queue[end++] = child;
            }
    rc = ca_spmat_init(A, nfb + nc, rels->n, rels->n * 16);
    if (rc != CA_OK) goto done;
    initialized = 1;
        memset(row, 0, (size_t)nfb * sizeof(*row));
        uint64_t b = r->rhs % modulus;
        int root_coef = 0;
        if (u[i] != none) {
            const int32_t *eu = expr + (size_t)u[i] * nfb;
            const int32_t *ev = expr + (size_t)v[i] * nfb;
            for (uint32_t j = 0; j < nfb; ++j) row[j] = (int64_t)eu[j] + ev[j];
            root_coef = sign[u[i]] + sign[v[i]];
            b = ca_submod(ca_submod(b, constant[u[i]], modulus), constant[v[i]], modulus);
        for (uint32_t k = 0; k < r->n; ++k)
            if (r->col[k] < nfb) row[r->col[k]] += r->val[k];
        uint32_t count = 0;
        for (uint32_t j = 0; j < nfb; ++j) {
            if (!row[j]) continue;
            if (row[j] <= INT32_MIN || row[j] > INT32_MAX) { rc = CA_ERR_INVALID; goto done; }
            cols[count] = j; vals[count++] = (int32_t)row[j];
        if (root_coef) {
            cols[count] = nfb + component[u[i]];
            vals[count++] = root_coef;
        if (!count && !b) continue; /* spanning-tree equations become 0=0 */
        rhs[A->rows] = b;
        rc = ca_spmat_add_row(A, cols, vals, count);
        if (rc != CA_OK) goto done;
    *b_out = rhs;
    rhs = NULL;
    rc = CA_OK;
done:
    if (rc != CA_OK && initialized) ca_spmat_free(A);
    free(u); free(v); free(head); free(next); free(queue); free(component);
    free(sign); free(expr); free(constant); free(row); free(cols); free(vals); free(rhs);
    return rc;
}


static ca_status build_graph_matrix(const rel_list *rels, uint32_t ncols, uint32_t nfb,
                                    uint64_t modulus, ca_spmat *A, uint64_t **b_out)
    if (!nv || !nfb || (size_t)nv > ((size_t)64 * 1024 * 1024) / sizeof(int32_t) / nfb ||
        rels->n > UINT32_MAX / 2)
        return CA_ERR_INVALID;
    if (!u || !v || !head || !next || !queue || !component || !sign || !expr || !constant || !row ||
        !cols || !vals || !rhs)
        goto done;
        const uint32_t len = rel_len(rels, i);
        const uint32_t *rcol = rel_cols(rels, i);
        const int32_t *rval = rel_vals(rels, i);
        for (uint32_t k = 0; k < len; ++k) {
            if (rcol[k] < nfb) continue;
            if (rcol[k] >= ncols || ++count > 2) {
                rc = CA_ERR_INVALID;
                goto done;
            uint32_t node = rcol[k] - nfb;
            if (rval[k] == 2 && count == 1)
                u[i] = v[i] = node;
            else if (rval[k] == 1) {
                if (count == 1)
                    u[i] = node;
                else if (v[i] == none)
                    v[i] = node;
                else {
                    rc = CA_ERR_INVALID;
                    goto done;
            } else {
        if (u[i] == none || v[i] == none) {
            rc = CA_ERR_INVALID;
            goto done;
        next[(size_t)2 * i] = head[u[i]];
        head[u[i]] = 2 * i;
        next[(size_t)2 * i + 1] = head[v[i]];
        head[v[i]] = 2 * i + 1;
                constant[child] = ca_submod(rels->rhs[i] % modulus, constant[parent], modulus);
                    if (src[j] == INT32_MIN) {
                        rc = CA_ERR_INVALID;
                        goto done;
                    }
                const uint32_t len = rel_len(rels, i);
                const uint32_t *rcol = rel_cols(rels, i);
                const int32_t *rval = rel_vals(rels, i);
                for (uint32_t k = 0; k < len; ++k) {
                    uint32_t j = rcol[k];
                    int64_t value = (int64_t)dst[j] - rval[k];
                    if (value <= INT32_MIN || value > INT32_MAX) {
        uint64_t b = rels->rhs[i] % modulus;
        for (uint32_t k = 0; k < len; ++k)
            if (rcol[k] < nfb) row[rcol[k]] += rval[k];
            if (row[j] <= INT32_MIN || row[j] > INT32_MAX) {
            cols[count] = j;
            vals[count++] = (int32_t)row[j];
    free(u);
    free(v);
    free(head);
    free(next);
    free(queue);
    free(component);
    free(sign);
    free(expr);
    free(constant);
    free(row);
    free(cols);
    free(vals);
    free(rhs);

/* Solve the matrix modulo q^e for a large prime q: Lanczos mod q + Hensel. */
static ca_status large_part_logs(const ca_spmat *A, const uint64_t *b, uint64_t q, unsigned e,
                                 uint64_t *x, uint8_t *known, uint64_t seed,
                                 ca_linsolve_report *rep)
{
    /* b has rows entries and x/known have cols: fix the dimensions here, once,
     * rather than re-reading them through A across the solver calls. */
    const uint32_t rows = A->rows, cols = A->cols;
    ca_status rc = ca_linsolve_mod_prime(A, b, q, x, known, seed, rep);
    if (rc != CA_OK) return rc;
    uint64_t qk = q;
    for (unsigned k = 1; k < e; k++) {
        /* residual r_i = (b_i - A_i x) / q^k  (exact integer division) */
        /* calloc, not malloc: nothing may read an entry the solver leaves
         * untouched, and zero is the harmless value if one ever did. */
        uint64_t *r = calloc(rows, sizeof(uint64_t));
        uint64_t *x1 = calloc(cols, sizeof(uint64_t));
        uint8_t *kn1 = calloc(cols, 1);
        if (!r || !x1 || !kn1) { free(r); free(x1); free(kn1); return CA_ERR_NOMEM; }
        uint64_t qk1 = qk * q;
        for (uint32_t i = 0; i < rows; i++) {
            ca_i128 acc = (ca_i128)(b[i] % qk1);
            for (uint32_t kk = A->row_ptr[i]; kk < A->row_ptr[i + 1]; kk++) {
                uint32_t j = A->col[kk];
                /* j < cols by construction; the bound is checked anyway so
                 * that a malformed matrix cannot index out of the solution. */
                if (j >= cols || !known[j]) {
                    acc = 0;
                    break;
                }
                acc -= (ca_i128)A->val[kk] * (ca_i128)x[j];
            }
            ca_i128 m = (ca_i128)qk1;
            acc %= m;
            if (acc < 0) acc += m;
            /* acc should be divisible by qk when x is a solution mod qk */
            uint64_t a = (uint64_t)acc;
            r[i] = (a % qk == 0) ? (a / qk) % q : 0;
        }
        rc = ca_linsolve_mod_prime(A, r, q, x1, kn1, seed + k, NULL);
        if (rc != CA_OK) { free(r); free(x1); free(kn1); return rc; }
        for (uint32_t j = 0; j < cols; j++) {
            if (known[j] && kn1[j]) x[j] = (x[j] + qk * x1[j]) % qk1;
            else known[j] = 0;
        }
        qk = qk1;
        free(r); free(x1); free(kn1);
    }
    return CA_OK;
}

static void vlog(const ca_ic_params *pr, const char *fmt, ...)
{
    /* va_start unconditionally, so the list is always started and ended on
     * every path (and the static analyser can see that it is). */
    va_list ap;
    va_start(ap, fmt);
    if (pr->verbose) vfprintf(stderr, fmt, ap);
    va_end(ap);
}

ca_status ca_ic_precompute(uint64_t p, uint64_t g, const ca_ic_params *params, ca_ic_ctx **out,
                           ca_ic_stats *st)
{
    ca_ic_params def;
    if (!params) { ca_ic_params_default(&def); params = &def; }
    ca_ic_stats lst;
    memset(&lst, 0, sizeof(lst));
    if (!st) st = &lst;
    memset(st, 0, sizeof(*st));
    double t_start = ca_now();
    if (p < 7 || !ca_is_prime(p)) {
        ca_set_error("index calculus needs an odd prime modulus");
        return CA_ERR_INVALID;
    }
    g %= p;
    if (g == 0) return CA_ERR_INVALID;
    if (p >> 63) {
        ca_set_error("index calculus supports p < 2^63");
        return CA_ERR_UNSUPPORTED;
    }
    ca_ic_ctx *ctx = calloc(1, sizeof(*ctx));
    if (!ctx) return CA_ERR_NOMEM;
    ctx->p = p;
    ctx->g = g;
    ctx->params = *params;
    ctx->zeta = ca_primitive_root(p);
    ca_rng_seed(&ctx->rng, ca_seed_or_random(params->seed));
    pthread_mutex_init(&ctx->rng_lock, NULL);
    uint64_t seed = ca_rng_next(&ctx->rng);
    uint32_t B, C;
    ca_ic_auto_params(bitlen(p), &B, &C);
    if (params->factor_base_bound) B = params->factor_base_bound;
    if (params->sieve_radius) C = params->sieve_radius;
    if (params->method == CA_IC_RANDOM_EXPONENT && !params->factor_base_bound) B = B * 3 / 2;
    if (B < 5) B = 5;
    uint32_t threads = params->threads ? params->threads : 1;
    st->threads = threads;

    /* factor base */
    size_t nfb = ca_sieve_primes(B, NULL, 0);
    ctx->fb = malloc(nfb * sizeof(uint32_t));
    ctx->fb_div = malloc(nfb * sizeof(ca_ic_divisor));
    ctx->fb_log = calloc(nfb, sizeof(uint64_t));
    ctx->fb_known = calloc(nfb, 1);
    uint8_t *fb_log2 = malloc(nfb);
    if (!ctx->fb || !ctx->fb_div || !ctx->fb_log || !ctx->fb_known || !fb_log2) { free(fb_log2); ca_ic_free(ctx); return CA_ERR_NOMEM; }
    ca_sieve_primes(B, ctx->fb, nfb);
    ctx->nfb = (uint32_t)nfb;
    /* Both random-step walks use this target-independent table. Keep the
     * same step distribution and RNG consumption while replacing repeated
     * short exponentiation with one lookup and one Montgomery multiply. */
    ctx->step_power = malloc(IC_STEP_POWERS * sizeof(uint64_t));
    if (!ctx->step_power) { free(fb_log2); ca_ic_free(ctx); return CA_ERR_NOMEM; }
    ca_mont step_mont;
    ca_mont_init(&step_mont, p);
    uint64_t step_zeta = ca_mont_to(&step_mont, ctx->zeta);
    ctx->step_power[0] = step_mont.r1;
    for (uint32_t i = 1; i < IC_STEP_POWERS; ++i)
        ctx->step_power[i] = ca_mont_mul(&step_mont, ctx->step_power[i - 1], step_zeta);
    for (size_t i = 0; i < nfb; i++) {
        fb_log2[i] = (uint8_t)(log2((double)ctx->fb[i]) + 0.5);
        ctx->fb_div[i] = ca_ic_divisor_init(ctx->fb[i]);
    }
    st->factor_base_size = ctx->nfb;

    /* column layout: [primes][H+c ...] ; -1 handled on the rhs */
    uint32_t col_prime0 = 0;
    uint32_t col_h0 = ctx->nfb;
    uint32_t ncols = params->method == CA_IC_LINEAR_SIEVE ? ctx->nfb + 2 * C + 1 : ctx->nfb;
    st->unknowns = ncols;
    uint32_t extra = params->extra_relations ? params->extra_relations : 64 + ncols / 20;
    uint32_t target = ncols + extra;

    /* ---- relation collection ---- */
    rel_list rels = {0};
    double t0 = ca_now();
    /* an explicit relation for zeta (usually itself a factor-base prime):
     * sum e_q log q == 1 */
    {
        relation rel;
        memset(&rel, 0, sizeof(rel));
        uint32_t cnt = 0;
        if (trial_factor(ctx->zeta, ctx->fb, ctx->fb_div, ctx->nfb, col_prime0, &rel, &cnt)) {
            rel.n = cnt;
            rel.rhs = 1;
            rel_push(&rels, &rel);
        } else {
            ca_set_error("primitive root %llu is not smooth over the factor base",
                         (unsigned long long)ctx->zeta);
            free(fb_log2);
            ca_ic_free(ctx);
            return CA_ERR_INTERNAL;
        }
    }
    pthread_t *tids = calloc(threads, sizeof(pthread_t));
    if (!tids) { free(fb_log2); ca_ic_free(ctx); free(rels.r); return CA_ERR_NOMEM; }
    if (params->method == CA_IC_LINEAR_SIEVE) {
        sieve_shared s;
        memset(&s, 0, sizeof(s));
        s.p = p;
        uint64_t H = ca_isqrt(p);
        if ((ca_u128)H * H < p) H++;
        s.H = H;
        s.J = (uint64_t)((ca_u128)H * H - p);
        s.B = B;
        s.C = C;
        s.fb = ctx->fb;
        s.fb_div = ctx->fb_div;
        s.nfb = ctx->nfb;
        s.fb_log2 = fb_log2;
        s.col_prime0 = col_prime0;
        s.col_h0 = col_h0;
        s.ncols = ncols;
        s.target_rels = target;
        s.rels = &rels;
        s.status = CA_OK;
        atomic_store(&s.next_c1, 0);
        atomic_store(&s.done, 0);
        pthread_mutex_init(&s.lock, NULL);
        vlog(params, "[ic] p=%llu (%u bits) linear sieve B=%u (%u primes) C=%u unknowns=%u target=%u threads=%u\n",
             (unsigned long long)p, bitlen(p), B, ctx->nfb, C, ncols, target, threads);
        uint32_t started = 0;
        for (uint32_t t = 0; t < threads; t++) {
            if (threads == 1) sieve_thread(&s);
            else if (pthread_create(&tids[t], NULL, sieve_thread, &s) == 0) started++;
        }
        if (threads > 1 && started == 0) sieve_thread(&s);
        for (uint32_t t = 0; t < started; t++) pthread_join(tids[t], NULL);
        pthread_mutex_destroy(&s.lock);
        st->sieve_candidates = atomic_load(&s.candidates);
        if (s.status != CA_OK) { free(tids); free(fb_log2); free(rels.r); ca_ic_free(ctx); return s.status; }
    } else {
        rexp_shared s;
        memset(&s, 0, sizeof(s));
        s.p = p;
        s.zeta = ctx->zeta;
        s.step_power = ctx->step_power;
        s.fb = ctx->fb;
        s.fb_div = ctx->fb_div;
        s.nfb = ctx->nfb;
        s.col_prime0 = col_prime0;
        s.target_rels = target;
        s.max_tries = params->max_relation_tries;
        s.rels = &rels;
        s.seed = seed;
        atomic_store(&s.done, 0);
        atomic_store(&s.tid, 0);
        pthread_mutex_init(&s.lock, NULL);
        vlog(params, "[ic] p=%llu (%u bits) random exponents B=%u (%u primes) target=%u threads=%u\n",
             (unsigned long long)p, bitlen(p), B, ctx->nfb, target, threads);
        uint32_t started = 0;
        for (uint32_t t = 0; t < threads; t++) {
            if (threads == 1) rexp_thread(&s);
            else if (pthread_create(&tids[t], NULL, rexp_thread, &s) == 0) started++;
        }
        if (threads > 1 && started == 0) rexp_thread(&s);
        for (uint32_t t = 0; t < started; t++) pthread_join(tids[t], NULL);
        pthread_mutex_destroy(&s.lock);
        st->smooth_tests = atomic_load(&s.tests);
    }
    free(tids);
    free(fb_log2);
    st->relations = rels.n;
    st->sieve_seconds = ca_now() - t0;
    vlog(params, "[ic] %u relations in %.2fs (%llu candidates)\n", rels.n, st->sieve_seconds,
         (unsigned long long)st->sieve_candidates);
    if (rels.n < ncols / 2) {
        ca_set_error("too few relations (%u for %u unknowns); increase C or B", rels.n, ncols);
        free(rels.r);
        ca_ic_free(ctx);
        return CA_ERR_NOT_FOUND;
    }

    /* ---- linear algebra ---- */
    t0 = ca_now();
    uint64_t pm1 = p - 1;
    ca_factorization f;
    ca_factorize(pm1, &f);
    uint64_t m_small = 1;
    for (unsigned i = 0; i < f.count; i++) {
        if (f.f[i].p <= IC_SMALL_Q) {
            for (unsigned e = 0; e < f.f[i].e; e++) m_small *= f.f[i].p;
        }
    }
    uint64_t *logs = calloc(ncols, sizeof(uint64_t));
    uint8_t *known = malloc(ncols);
    uint64_t *small_logs = calloc(ctx->nfb, sizeof(uint64_t));
    ca_status rc = CA_OK;
    if (!logs || !known || !small_logs) { rc = CA_ERR_NOMEM; goto done; }
    memset(known, 1, ncols);
    rc = small_part_logs(ctx, m_small, small_logs);
    if (rc != CA_OK) goto done;
    vlog(params, "[ic] small part of p-1: %llu (Pohlig-Hellman), large primes: %u\n",
         (unsigned long long)m_small, (unsigned)(f.count));
    {
        uint64_t modulus = m_small;
        for (uint32_t i = 0; i < ctx->nfb; i++) logs[i] = small_logs[i];
        ca_spmat A;
        uint64_t *b = NULL;
        int have_matrix = 0;
        for (unsigned i = 0; i < f.count; i++) {
            uint64_t q = f.f[i].p;
            if (q <= IC_SMALL_Q) continue;
            if (!have_matrix) {
                rc = CA_ERR_INVALID;
                if (params->method == CA_IC_LINEAR_SIEVE)
                    rc = build_graph_matrix(&rels, ncols, ctx->nfb, pm1, &A, &b);
                if (rc != CA_OK) rc = build_matrix(&rels, ncols, pm1, &A, &b);
                if (rc != CA_OK) goto done;
                vlog(params, "[ic] relation matrix: %u rows, %u columns, %u entries (original %u columns)\n",
                     A.rows, A.cols, A.nnz, ncols);
                have_matrix = 1;
                st->matrix_used = 1;
            }
            uint64_t qe = 1;
            for (unsigned e = 0; e < f.f[i].e; e++) qe *= q;
            uint64_t *xq = calloc(ncols, sizeof(uint64_t));
            uint8_t *kq = calloc(ncols, 1);
            ca_linsolve_report rep;
            if (!xq || !kq) { free(xq); free(kq); rc = CA_ERR_NOMEM; break; }
            rc = large_part_logs(&A, b, q, f.f[i].e, xq, kq, seed + i, &rep);
            st->lanczos_iterations += rep.lanczos_iters;
            vlog(params, "[ic] mod %llu^%u: %ux%u active, %u Lanczos iterations, %u attempts%s, %.2fs\n",
                 (unsigned long long)q, f.f[i].e, rep.active_rows, rep.active_cols, rep.lanczos_iters,
                 rep.attempts, rep.used_dense ? " (dense fallback)" : "", rep.seconds);
            if (rc != CA_OK) { free(xq); free(kq); break; }
            for (uint32_t j = 0; j < ncols; j++) {
                if (!kq[j]) { known[j] = 0; continue; }
                logs[j] = ca_crt2(logs[j] % modulus, modulus, xq[j] % qe, qe);
            }
            modulus *= qe;
            free(xq); free(kq);
        }
        if (have_matrix) { ca_spmat_free(&A); free(b); }
        if (rc != CA_OK) goto done;
    }
    /* verify factor base logs */
    {
        ca_mont m;
        ca_mont_init(&m, p);
        uint64_t zm = ca_mont_to(&m, ctx->zeta);
        uint32_t ok = 0;
        for (uint32_t i = 0; i < ctx->nfb; i++) {
            if (!known[i]) continue;
            uint64_t v = ca_mont_from(&m, ca_mont_pow(&m, zm, logs[i] % pm1));
            if (v == ctx->fb[i]) {
                ctx->fb_log[i] = logs[i] % pm1;
                ctx->fb_known[i] = 1;
                ok++;
            }
        }
        st->verified_logs = ok;
        vlog(params, "[ic] %u of %u factor-base logs verified\n", ok, ctx->nfb);
        if (ok < ctx->nfb / 2) {
            ca_set_error("only %u of %u factor-base logarithms verified", ok, ctx->nfb);
            rc = CA_ERR_SINGULAR;
        }
    }
done:
    st->linalg_seconds = ca_now() - t0;
    free(logs); free(known); free(small_logs); free(rels.r);
    if (rc != CA_OK) { ca_ic_free(ctx); return rc; }
    /* log of the user's base */
    ctx->ord_g = ca_mult_order(g, p);
    if (g == ctx->zeta) { ctx->log_g = 1; ctx->g_known = 1; }
    st->total_seconds = ca_now() - t_start;
    *out = ctx;
    return CA_OK;
}

void ca_ic_free(ca_ic_ctx *ctx)
{
    if (!ctx) return;
    free(ctx->fb);
    free(ctx->fb_div);
    free(ctx->step_power);
    free(ctx->fb_log);
    free(ctx->fb_known);
    free(ctx->fb_div);
    free(ctx->step_power);
    free(ctx->fb_log);
    free(ctx->fb_known);
    pthread_mutex_destroy(&ctx->rng_lock);
    free(ctx);
}

/* Euclidean rational reconstruction: a = signed_b * value (mod p).
 * Stop when the numerator is at most floor(sqrt(p)); the corresponding
 * denominator has magnitude at most p/(floor(sqrt(p))+1). All coefficient
 * arithmetic is signed 128-bit; the Euclidean remainders stay in a word. */
static void rational_split(uint64_t value, uint64_t p, uint64_t bound,
                            uint64_t *numerator, uint64_t *denominator, int *negative)
{
    uint64_t r0 = p, r1 = value;
    ca_i128 t0 = 0, t1 = 1;
    while (r1 > bound) {
        uint64_t q = r0 / r1;
        uint64_t r2 = r0 - q * r1;
        ca_i128 t2 = t0 - (ca_i128)q * t1;
        r0 = r1; r1 = r2;
        t0 = t1; t1 = t2;
    }
    *numerator = r1;
    *negative = t1 < 0;
    *denominator = (uint64_t)(t1 < 0 ? -t1 : t1);
}

/* log_zeta(h) via simultaneous smoothness of a/b = h*zeta^e. */
static ca_status individual_log_zeta(ca_ic_ctx *ctx, uint64_t h, uint64_t *out, uint64_t *tries)
{
    uint64_t p = ctx->p, pm1 = p - 1;
    uint64_t bound = ca_isqrt(p);
    ca_mont m;
    ca_mont_init(&m, p);
    uint64_t zm = ca_mont_to(&m, ctx->zeta);
    uint64_t hm = ca_mont_to(&m, h % p);
    pthread_mutex_lock(&ctx->rng_lock);
    uint64_t e = ca_rng_below(&ctx->rng, pm1);
    uint64_t rs = ca_rng_next(&ctx->rng);
    pthread_mutex_unlock(&ctx->rng_lock);
    ca_rng rng;
    ca_rng_seed(&rng, rs);
    uint64_t cur = ca_mont_mul(&m, hm, ca_mont_pow(&m, zm, e));
    uint64_t limit = 50000000ULL;
    for (uint64_t t = 0; t < limit; t++) {
        uint64_t v = ca_mont_from(&m, cur);
        relation numerator_rel, denominator_rel;
        uint32_t numerator_count = 0, denominator_count = 0;
        uint64_t numerator, denominator;
        int negative;
        rational_split(v, p, bound, &numerator, &denominator, &negative);
        (*tries)++;
        if (trial_factor(numerator, ctx->fb, ctx->fb_div, ctx->nfb, 0, &numerator_rel, &numerator_count) &&
            trial_factor(denominator, ctx->fb, ctx->fb_div, ctx->nfb, 0, &denominator_rel, &denominator_count)) {
            /* log h = log(a) - log(|b|) - log(sign(b)) - e. */
            int ok = 1;
            uint64_t acc = 0;
            for (uint32_t i = 0; i < numerator_count; i++) {
                uint32_t j = numerator_rel.col[i];
                if (!ctx->fb_known[j]) { ok = 0; break; }
                acc = ca_addmod(acc, ca_mulmod((uint64_t)numerator_rel.val[i], ctx->fb_log[j], pm1), pm1);
            }
            for (uint32_t i = 0; ok && i < denominator_count; i++) {
                uint32_t j = denominator_rel.col[i];
                if (!ctx->fb_known[j]) { ok = 0; break; }
                acc = ca_submod(acc, ca_mulmod((uint64_t)denominator_rel.val[i], ctx->fb_log[j], pm1), pm1);
            }
            if (ok) {
                if (negative) acc = ca_submod(acc, pm1 / 2, pm1);
                acc = ca_submod(acc, e % pm1, pm1);
                /* verify */
                if (ca_mont_from(&m, ca_mont_pow(&m, zm, acc)) == h % p) { *out = acc; return CA_OK; }
            }
        }
        uint64_t step = 1 + ca_rng_below(&rng, 4095);
        cur = ca_mont_mul(&m, cur, ctx->step_power[step]);
        e = (e + step) % pm1;
    }
    return CA_ERR_LIMIT;
}

ca_status ca_ic_log(ca_ic_ctx *ctx, uint64_t h, uint64_t *x, ca_stats *st)
{
    double t0 = ca_now();
    uint64_t p = ctx->p, pm1 = p - 1;
    h %= p;
    if (h == 0) return CA_ERR_INVALID;
    uint64_t tries = 0;
    if (!ctx->g_known) {
        ca_status rc = individual_log_zeta(ctx, ctx->g, &ctx->log_g, &tries);
        if (rc != CA_OK) return rc;
        ctx->g_known = 1;
    }
    uint64_t lh;
    ca_status rc = individual_log_zeta(ctx, h, &lh, &tries);
    if (rc != CA_OK) return rc;
    /* solve log_g * x == lh (mod p-1) */
    uint64_t d = ca_gcd(ctx->log_g, pm1);
    if (lh % d) {
        ca_set_error("h is not in the subgroup generated by g");
        return CA_ERR_NOT_FOUND;
    }
    uint64_t nn = pm1 / d; /* == ord(g) */
    uint64_t sol = ca_mulmod((lh / d) % nn, ca_invmod((ctx->log_g / d) % nn, nn), nn);
    if (ca_powmod(ctx->g, sol, p) != h) return CA_ERR_INTERNAL;
    *x = sol;
    if (st) {
        st->iterations += tries;
        st->seconds += ca_now() - t0;
    }
    return CA_OK;
}

ca_status ca_ic_solve(uint64_t p, uint64_t g, uint64_t h, const ca_ic_params *params, uint64_t *x,
                      ca_ic_stats *st)
{
    ca_ic_ctx *ctx;
    ca_ic_stats local;
    if (!st) st = &local;
    ca_status rc = ca_ic_precompute(p, g, params, &ctx, st);
    if (rc != CA_OK) return rc;
    double t0 = ca_now();
    rc = ca_ic_log(ctx, h, x, NULL);
    st->total_seconds += ca_now() - t0;
    ca_ic_free(ctx);
    return rc;
}

uint64_t ca_ic_modulus(const ca_ic_ctx *ctx) { return ctx->p; }
uint32_t ca_ic_factor_base_size(const ca_ic_ctx *ctx) { return ctx->nfb; }
uint64_t ca_ic_primitive_root(const ca_ic_ctx *ctx) { return ctx->zeta; }
uint64_t ca_ic_factor_base_log(const ca_ic_ctx *ctx, uint32_t i, uint32_t *prime, int *known)
{
    if (i >= ctx->nfb) { if (known) *known = 0; return 0; }
    if (prime) *prime = ctx->fb[i];
    if (known) *known = ctx->fb_known[i];
    return ctx->fb_known[i] ? ctx->fb_log[i] : 0;
}
