/*
 * modarith.c - 64-bit modular arithmetic, Montgomery multiplication,
 * primality testing and factoring.
 */
#include "cryptanalysis/ca_modarith.h"
#include "ca_internal.h"
#include "dlog_checkpoint_internal.h"

#include <inttypes.h>
#include <math.h>
#include <stddef.h>
#include <stdlib.h>
#include <string.h>

uint64_t ca_powmod(uint64_t base, uint64_t exp, uint64_t m)
{
    if (m == 1) return 0;
    /* Odd modulus and more than a few squarings: Montgomery form, whose
     * multiply has no 128-bit division.  Setting it up costs three, so
     * short exponents stay on the plain ladder.  Same residue either way. */
    if ((m & 1) && exp >= 16) {
        ca_mont mo;
        ca_mont_init(&mo, m);
        return ca_mont_from(&mo, ca_mont_pow(&mo, ca_mont_to(&mo, base), exp));
    }
    uint64_t r = 1;
    base %= m;
    while (exp) {
        if (exp & 1) r = ca_mulmod(r, base, m);
        base = ca_mulmod(base, base, m);
        exp >>= 1;
    }
    return r;
}

uint64_t ca_gcd(uint64_t a, uint64_t b)
{
    while (b) {
        uint64_t t = a % b;
        a = b;
        b = t;
    }
    return a;
}

uint64_t ca_invmod(uint64_t a, uint64_t m)
{
    /* Extended Euclid with signed 128-bit coefficients so any 64-bit
     * modulus is safe. */
    if (m == 0) return 0;
    a %= m;
    if (a == 0) return 0;
    ca_i128 t = 0, newt = 1;
    uint64_t r = m, newr = a;
    while (newr) {
        uint64_t q = r / newr;
        ca_i128 tmp = t - (ca_i128)q * newt;
        t = newt;
        newt = tmp;
        uint64_t tr = r - q * newr;
        r = newr;
        newr = tr;
    }
    if (r != 1) return 0;
    if (t < 0) t += (ca_i128)m;
    return (uint64_t)t;
}

uint64_t ca_isqrt(uint64_t n)
{
    if (n == 0) return 0;
    uint64_t x = (uint64_t)__builtin_sqrtl((long double)n);
    /* fix up floating point error */
    while ((ca_u128)x * x > n) x--;
    while ((ca_u128)(x + 1) * (x + 1) <= n) x++;
    return x;
}

uint64_t ca_iroot(uint64_t n, unsigned k)
{
    if (k == 0) return 0;
    if (k == 1) return n;
    if (k == 2) return ca_isqrt(n);
    if (n < 2) return n;
    /* binary search on x^k <= n with overflow guard */
    uint64_t lo = 1, hi = 1;
    while (1) {
        /* compute hi^k with overflow detection */
        ca_u128 p = 1;
        int over = 0;
        for (unsigned i = 0; i < k; i++) {
            p *= hi;
            if (p > n) { over = 1; break; }
        }
        if (over) break;
        lo = hi;
        if (hi >= (1ULL << 32)) { hi = UINT64_MAX; break; }
        hi *= 2;
    }
    while (lo < hi) {
        uint64_t mid = lo + (hi - lo + 1) / 2;
        ca_u128 p = 1;
        int over = 0;
        for (unsigned i = 0; i < k; i++) {
            p *= mid;
            if (p > n) { over = 1; break; }
        }
        if (over) hi = mid - 1; else lo = mid;
    }
    return lo;
}

int ca_legendre(uint64_t a, uint64_t p)
{
    a %= p;
    if (a == 0) return 0;
    uint64_t r = ca_powmod(a, (p - 1) / 2, p);
    if (r == 1) return 1;
    if (r == p - 1) return -1;
    return 0; /* p not prime */
}

int ca_sqrtmod_prime(uint64_t a, uint64_t p, uint64_t *root)
{
    a %= p;
    if (a == 0) { *root = 0; return 1; }
    if (p == 2) { *root = a & 1; return 1; }
    if (ca_legendre(a, p) != 1) return 0;
    if ((p & 3) == 3) {
        *root = ca_powmod(a, (p + 1) / 4, p);
        return 1;
    }
    /* Tonelli-Shanks */
    uint64_t q = p - 1;
    unsigned s = 0;
    while ((q & 1) == 0) { q >>= 1; s++; }
    uint64_t z = 2;
    while (ca_legendre(z, p) != -1) z++;
    uint64_t c = ca_powmod(z, q, p);
    uint64_t r = ca_powmod(a, (q + 1) / 2, p);
    uint64_t t = ca_powmod(a, q, p);
    unsigned m = s;
    while (t != 1) {
        unsigned i = 0;
        uint64_t tt = t;
        while (tt != 1) {
            tt = ca_mulmod(tt, tt, p);
            i++;
            if (i == m) return 0;
        }
        uint64_t b = c;
        for (unsigned j = 0; j + i + 1 < m; j++) b = ca_mulmod(b, b, p);
        r = ca_mulmod(r, b, p);
        c = ca_mulmod(b, b, p);
        t = ca_mulmod(t, c, p);
        m = i;
    }
    *root = r;
    return 1;
}

uint64_t ca_crt2(uint64_t r1, uint64_t m1, uint64_t r2, uint64_t m2)
{
    /* x = r1 + m1 * ((r2 - r1) * m1^{-1} mod m2), with r1 reduced first:
     * an unreduced r1 gave a result outside [0, m1 m2). */
    r1 %= m1;
    uint64_t inv = ca_invmod(m1 % m2, m2);
    uint64_t d = ca_submod(r2 % m2, r1 % m2, m2);
    uint64_t k = ca_mulmod(d, inv, m2);
    return r1 + m1 * k;
}

/* ---- Montgomery ------------------------------------------------------- */

int ca_mont_init(ca_mont *m, uint64_t p)
{
    if ((p & 1) == 0 || p < 3) return 0;
    m->p = p;
    /* Newton iteration for p^{-1} mod 2^64 */
    uint64_t inv = p; /* correct to 3 bits since p odd: p*p == 1 mod 8 */
    for (int i = 0; i < 6; i++) inv *= 2 - p * inv;
    m->pinv = (uint64_t)0 - inv;
    /* R mod p where R = 2^64 */
    m->r1 = (uint64_t)((((ca_u128)1) << 64) % p);
    m->r2 = (uint64_t)(((ca_u128)m->r1 * m->r1) % p);
    m->r3 = (uint64_t)(((ca_u128)m->r2 * m->r1) % p);
    return 1;
}

uint64_t ca_mont_pow(const ca_mont *m, uint64_t a, uint64_t e)
{
    uint64_t r = m->r1;
    while (e) {
        if (e & 1) r = ca_mont_mul(m, r, a);
        a = ca_mont_sqr(m, a);
        e >>= 1;
    }
    return r;
}

uint64_t ca_mont_inv(const ca_mont *m, uint64_t a)
{
    /* a = x*R; invmod gives x^{-1} R^{-1}; multiply by R^3 with one REDC:
     * x^{-1} R^{-1} * R^3 * R^{-1} = x^{-1} R. */
    uint64_t inv = ca_invmod(a, m->p);
    if (inv == 0) return 0;
    return ca_mont_mul(m, inv, m->r3);
}

/* ---- primality -------------------------------------------------------- */

/* One Miller-Rabin round in Montgomery form: 1 is r1 = R mod n there, and
 * n - 1 is n - r1. */
static int mr_witness(const ca_mont *m, uint64_t a, uint64_t d, unsigned s)
{
    const uint64_t one = m->r1, minus_one = m->p - m->r1;
    uint64_t x = ca_mont_pow(m, ca_mont_to(m, a), d);
    if (x == one || x == minus_one) return 0;
    for (unsigned r = 1; r < s; r++) {
        x = ca_mont_sqr(m, x);
        if (x == minus_one) return 0;
    }
    return 1; /* composite */
}

int ca_is_prime(uint64_t n)
{
    if (n < 2) return 0;
    static const uint64_t small[] = {2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37};
    for (size_t i = 0; i < sizeof(small) / sizeof(small[0]); i++) {
        if (n == small[i]) return 1;
        if (n % small[i] == 0) return 0;
    }
    uint64_t d = n - 1;
    unsigned s = 0;
    while ((d & 1) == 0) { d >>= 1; s++; }
    /* n is odd here.  These 12 bases are deterministic for all n < 2^64. */
    ca_mont m;
    ca_mont_init(&m, n);
    for (size_t i = 0; i < sizeof(small) / sizeof(small[0]); i++) {
        if (mr_witness(&m, small[i], d, s)) return 0;
    }
    return 1;
}

uint64_t ca_next_prime(uint64_t n)
{
    /* 18446744073709551557 = 2^64 - 59 is the largest 64-bit prime. */
    if (n < 2) return 2;
    if (n >= 18446744073709551557ULL) return 0;
    n++;
    if ((n & 1) == 0) n++;
    while (!ca_is_prime(n)) n += 2;
    return n;
}

/* ---- factoring -------------------------------------------------------- */

static uint64_t pollard_brent(uint64_t n, uint64_t c, uint64_t seed)
{
    /* Brent's variant of Pollard rho with Montgomery arithmetic, batched gcd. */
    ca_mont m;
    if (!ca_mont_init(&m, n)) return 0;
    uint64_t cm = ca_mont_to(&m, c);
    uint64_t y = ca_mont_to(&m, seed), q = m.r1, g = 1;
    uint64_t x, ys; /* both are set before first use inside the loop */
    uint64_t r = 1;
    const uint64_t batch = 128;
    do {
        x = y;
        for (uint64_t i = 0; i < r; i++) y = ca_addmod(ca_mont_sqr(&m, y), cm, n);
        uint64_t k = 0;
        do {
            ys = y;
            uint64_t lim = (batch < r - k) ? batch : r - k;
            for (uint64_t i = 0; i < lim; i++) {
                y = ca_addmod(ca_mont_sqr(&m, y), cm, n);
                q = ca_mont_mul(&m, q, x > y ? x - y : y - x);
            }
            g = ca_gcd(ca_mont_from(&m, q), n);
            k += lim;
        } while (k < r && g == 1);
        r <<= 1;
        if (r > (1ULL << 40)) return 0;
    } while (g == 1);
    if (g == n) {
        do {
            ys = ca_addmod(ca_mont_sqr(&m, ys), cm, n);
            g = ca_gcd(ca_mont_from(&m, x > ys ? x - ys : ys - x), n);
        } while (g == 1);
    }
    return g;
}

static void add_factor(ca_factorization *out, uint64_t p)
{
    for (unsigned i = 0; i < out->count; i++) {
        if (out->f[i].p == p) { out->f[i].e++; return; }
    }
    if (out->count < CA_MAX_FACTORS) {
        out->f[out->count].p = p;
        out->f[out->count].e = 1;
        out->count++;
    }
}

static void factor_rec(uint64_t n, ca_factorization *out, unsigned depth)
{
    if (n == 1) return;
    if (ca_is_prime(n)) { add_factor(out, n); return; }
    if (depth > 64) { add_factor(out, n); return; }
    uint64_t d = 0;
    for (uint64_t c = 1; c < 100 && (d == 0 || d == n); c++) {
        d = pollard_brent(n, c, 2 + c);
    }
    if (d == 0 || d == n) {
        /* fall back to trial division - should be unreachable for 64-bit */
        for (uint64_t q = 3; (ca_u128)q * q <= n; q += 2) {
            if (n % q == 0) { d = q; break; }
        }
        if (d == 0 || d == n) { add_factor(out, n); return; }
    }
    factor_rec(d, out, depth + 1);
    factor_rec(n / d, out, depth + 1);
}

static int cmp_factor(const void *a, const void *b)
{
    const ca_factor *fa = a, *fb = b;
    return fa->p < fb->p ? -1 : fa->p > fb->p;
}

ca_status ca_factorize(uint64_t n, ca_factorization *out)
{
    /* The factorisation of n is unique and returned sorted, so the last
     * one per thread can be handed out again.  Callers factor the same
     * group order repeatedly (element orders, then Pohlig-Hellman, per
     * target), and Pollard-Brent dominated those calls. */
    static _Thread_local uint64_t memo_n;
    static _Thread_local ca_factorization memo_f;
    if (n > 1 && n == memo_n) {
        *out = memo_f;
        return CA_OK;
    }
    const uint64_t n_in = n;
    memset(out, 0, sizeof(*out));
    if (n == 0) return CA_ERR_INVALID;
    if (n == 1) return CA_OK;
    /* strip small primes first */
    static const uint32_t small[] = {2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37,
                                     41, 43, 47, 53, 59, 61, 67, 71, 73, 79, 83,
                                     89, 97};
    for (size_t i = 0; i < sizeof(small) / sizeof(small[0]); i++) {
        while (n % small[i] == 0) { add_factor(out, small[i]); n /= small[i]; }
    }
    factor_rec(n, out, 0);
    qsort(out->f, out->count, sizeof(ca_factor), cmp_factor);
    memo_n = n_in;
    memo_f = *out;
    return CA_OK;
}

enum { FACTOR_IDLE = 0, FACTOR_ADVANCE = 1, FACTOR_BATCH = 2,
       FACTOR_RECOVER = 3, FACTOR_TRIAL = 4, FACTOR_DONE = 5 };

typedef struct factor_checkpoint {
    char magic[8];
    uint64_t n;
    uint32_t version, phase, pending_count, reserved;
    uint64_t pending[64];
    ca_factorization factors;
    uint64_t active, c, x, y, ys, q, g, r, k, remaining, batch_remaining, trial;
    uint64_t steps, gcds;
    double seconds;
    uint64_t checksum;
} factor_checkpoint;

static int factor_state_valid(const factor_checkpoint *s, uint64_t n)
{
    if (memcmp(s->magic, "CAFACT01", 8) || s->version != 1 || s->n != n ||
        s->reserved || s->phase > FACTOR_DONE || s->pending_count > 64 ||
        s->factors.count > CA_MAX_FACTORS || !isfinite(s->seconds) || s->seconds < 0)
        return 0;
    ca_u128 product = 1;
    for (unsigned i = 0; i < s->factors.count; i++) {
        uint64_t p = s->factors.f[i].p;
        if (p < 2 || !ca_is_prime(p) || !s->factors.f[i].e) return 0;
        for (unsigned e = 0; e < s->factors.f[i].e; e++) {
            if (product > n / p) return 0;
            product *= p;
        }
    }
    for (unsigned i = 0; i < s->pending_count; i++) {
        if (s->pending[i] < 2) return 0;
        if (product > n / s->pending[i]) return 0;
        product *= s->pending[i];
    }
    if (s->active) {
        if (s->active < 3 || (s->active & 1) == 0) return 0;
        if (product > n / s->active) return 0;
        product *= s->active;
    }
    if (product != n || (s->phase == FACTOR_IDLE && s->active) ||
        (s->phase > FACTOR_IDLE && s->phase < FACTOR_DONE && !s->active) ||
        (s->phase == FACTOR_DONE && (s->active || s->pending_count))) return 0;
    if (s->phase >= FACTOR_ADVANCE && s->phase <= FACTOR_RECOVER) {
        if (s->c < 1 || s->c >= 100 || s->r == 0 || s->r > (1ULL << 40) ||
            (s->r & (s->r - 1)) || s->k > s->r || s->remaining > s->r ||
            s->batch_remaining > 128 || s->x >= s->active ||
            s->y >= s->active || s->ys >= s->active || s->q >= s->active)
            return 0;
        if ((s->phase == FACTOR_ADVANCE && !s->remaining) ||
            (s->phase == FACTOR_BATCH && s->k >= s->r)) return 0;
    }
    if (s->phase == FACTOR_TRIAL && (s->trial < 3 || (s->trial & 1) == 0)) return 0;
    return 1;
}

static int factor_checkpoint_save(const char *path, factor_checkpoint *s)
{
    if (!path) return 1;
    s->checksum = 0;
    s->checksum = dlog_ckpt_hash(s, sizeof(*s), UINT64_C(14695981039346656037));
    dlog_ckpt_file w;
    int ok = dlog_ckpt_begin(&w, path);
    if (ok) ok = fwrite(s, 1, sizeof(*s), w.f) == sizeof(*s);
    ok = dlog_ckpt_finish(&w, ok);
    if (!ok) ca_set_error("factor: cannot persist checkpoint");
    return ok;
}

/* 1 = restored, 0 = fresh, -1 = invalid or unreadable. */
static int factor_checkpoint_load(const char *path, uint64_t n, factor_checkpoint *s)
{
    if (!path) return 0;
    FILE *f = fopen(path, "rb");
    if (!f) {
        if (errno == ENOENT) return 0;
        ca_set_error("factor: cannot open checkpoint");
        return -1;
    }
    factor_checkpoint got = {0};
    int ok = fread(&got, 1, sizeof(got), f) == sizeof(got) && fgetc(f) == EOF;
    if (ferror(f)) ok = 0;
    fclose(f);
    uint64_t checksum = got.checksum;
    got.checksum = 0;
    if (!ok || dlog_ckpt_hash(&got, sizeof(got), UINT64_C(14695981039346656037)) != checksum ||
        !factor_state_valid(&got, n)) {
        ca_set_error("factor: checkpoint identity, length or checksum failed");
        return -1;
    }
    got.checksum = checksum;
    *s = got;
    return 1;
}

ca_status ca_factor_checkpoint_validate(uint64_t n, const char *checkpoint_path)
{
    if (!n || !checkpoint_path) {
        ca_set_error("factor: positive input and checkpoint path required");
        return CA_ERR_INVALID;
    }
    factor_checkpoint s;
    int loaded = factor_checkpoint_load(checkpoint_path, n, &s);
    if (loaded == 1) return CA_OK;
    if (!loaded) ca_set_error("factor: checkpoint is missing");
    return CA_ERR_INVALID;
}

static const char *factor_phase_name(uint32_t phase)
{
    if (phase == FACTOR_IDLE) return "queue";
    if (phase == FACTOR_TRIAL) return "trial";
    if (phase == FACTOR_DONE) return "complete";
    return "rho";
}

static int factor_progress_write(const char *path, const factor_checkpoint *s,
                                  const char *status, int verbose)
{
    if (verbose) fprintf(stderr, "[factor] %s n=%" PRIu64 " active=%" PRIu64
                         " c=%" PRIu64 " steps=%" PRIu64 " gcds=%" PRIu64
                         " primes=%u pending=%u %.1fs\n", factor_phase_name(s->phase),
                         s->n, s->active, s->c, s->steps, s->gcds,
                         s->factors.count, s->pending_count, s->seconds);
    if (!path) return 1;
    char *out = dlog_ckpt_path(path, ".progress.json");
    if (!out) return 0;
    dlog_ckpt_file w;
    int ok = dlog_ckpt_begin(&w, out);
    if (ok) ok = fprintf(w.f,
        "{\"status\":\"%s\",\"phase\":\"%s\",\"n\":%" PRIu64
        ",\"active\":%" PRIu64 ",\"seed\":%" PRIu64
        ",\"steps\":%" PRIu64 ",\"gcds\":%" PRIu64
        ",\"prime_factors\":%u,\"pending\":%u,\"elapsed_seconds\":%.3f}\n",
        status, factor_phase_name(s->phase), s->n, s->active, s->c,
        s->steps, s->gcds, s->factors.count, s->pending_count, s->seconds) > 0;
    ok = dlog_ckpt_finish(&w, ok);
    free(out);
    if (!ok) ca_set_error("factor: cannot persist progress");
    return ok;
}

static int factor_report(const char *path, factor_checkpoint *s, double seconds,
                          const char *status, int verbose, int save)
{
    s->seconds = seconds;
    return (!save || factor_checkpoint_save(path, s)) &&
           factor_progress_write(path, s, status, verbose);
}

static int factor_push(factor_checkpoint *s, uint64_t v)
{
    if (s->pending_count >= 64) return 0;
    s->pending[s->pending_count++] = v;
    return 1;
}

static void factor_begin_attempt(factor_checkpoint *s)
{
    ca_mont m;
    ca_mont_init(&m, s->active);
    s->x = s->ys = 0;
    s->y = ca_mont_to(&m, 2 + s->c);
    s->q = m.r1;
    s->g = 1;
    s->r = 1;
    s->k = s->batch_remaining = 0;
    s->remaining = s->r;
    s->x = s->y;
    s->phase = FACTOR_ADVANCE;
}

static void factor_next_attempt(factor_checkpoint *s)
{
    s->c++;
    if (s->c >= 100) {
        s->phase = FACTOR_TRIAL;
        s->trial = 3;
    } else factor_begin_attempt(s);
}

ca_status ca_factorize_checkpointed(uint64_t n, const char *checkpoint_path,
                                    uint32_t progress_interval, uint32_t checkpoint_interval,
                                    int verbose, uint64_t max_steps, ca_factorization *out,
                                    ca_factor_progress *progress)
{
    if (!n || !out) {
        ca_set_error("factor: positive input and output required");
        return CA_ERR_INVALID;
    }
    factor_checkpoint s = {0};
    memcpy(s.magic, "CAFACT01", 8);
    s.n = n; s.version = 1;
    if (n > 1) factor_push(&s, n);
    else s.phase = FACTOR_DONE;
    double t0 = ca_now(), elapsed_prior = 0;
    int loaded = factor_checkpoint_load(checkpoint_path, n, &s);
    ca_status rc = CA_ERR_INTERNAL;
    if (loaded < 0) { rc = CA_ERR_INVALID; goto done; }
    elapsed_prior = s.seconds;
    if (!progress_interval) progress_interval = 5;
    if (!checkpoint_interval) checkpoint_interval = 60;
    double next_progress = t0 + progress_interval;
    double next_checkpoint = t0 + checkpoint_interval;
    ca_mont mont;
    uint64_t mont_n = 0, mont_c = 0, cm = 0;
    if ((checkpoint_path || verbose) &&
        !factor_report(checkpoint_path, &s, elapsed_prior, "running", verbose, !loaded)) {
        rc = CA_ERR_INTERNAL; goto done;
    }
    while (s.phase != FACTOR_DONE) {
        if (s.phase == FACTOR_IDLE) {
            if (!s.pending_count) { s.phase = FACTOR_DONE; break; }
            uint64_t v = s.pending[--s.pending_count];
            static const uint32_t small[] = {2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37,
                                             41, 43, 47, 53, 59, 61, 67, 71, 73, 79, 83,
                                             89, 97};
            for (size_t i = 0; i < sizeof(small) / sizeof(*small); i++)
                while (v % small[i] == 0) { add_factor(&s.factors, small[i]); v /= small[i]; }
            if (v > 1) {
                if (ca_is_prime(v)) add_factor(&s.factors, v);
                else {
                    s.active = v; s.c = 1;
                    factor_begin_attempt(&s);
                }
            }
            if ((checkpoint_path || verbose) &&
                !factor_report(checkpoint_path, &s, elapsed_prior + ca_now() - t0,
                               "running", verbose, 1)) {
                rc = CA_ERR_INTERNAL; goto done;
            }
            continue;
        }
        if (max_steps && s.steps >= max_steps) {
            ca_set_error("factor: step cap reached; raise --max-steps to resume");
            rc = CA_ERR_LIMIT; goto finish;
        }
        uint64_t found = 0;
        if (s.phase == FACTOR_TRIAL) {
            if ((ca_u128)s.trial * s.trial > s.active) {
                ca_set_error("factor: exhausted trial divisors without a factor");
                rc = CA_ERR_NOT_FOUND; goto finish;
            }
            if (s.active % s.trial == 0) found = s.trial;
            else s.trial += 2;
            s.steps++;
        } else {
            if (mont_n != s.active) {
                ca_mont_init(&mont, s.active);
                mont_n = s.active;
                mont_c = 0;
            }
            if (mont_c != s.c) { cm = ca_mont_to(&mont, s.c); mont_c = s.c; }
            if (s.phase == FACTOR_ADVANCE) {
                s.y = ca_addmod(ca_mont_sqr(&mont, s.y), cm, s.active);
                s.remaining--; s.steps++;
                if (!s.remaining) { s.phase = FACTOR_BATCH; s.k = s.batch_remaining = 0; }
            } else if (s.phase == FACTOR_BATCH) {
                if (!s.batch_remaining) {
                    s.ys = s.y;
                    s.batch_remaining = s.r - s.k < 128 ? s.r - s.k : 128;
                }
                s.y = ca_addmod(ca_mont_sqr(&mont, s.y), cm, s.active);
                s.q = ca_mont_mul(&mont, s.q, s.x > s.y ? s.x - s.y : s.y - s.x);
                s.k++; s.batch_remaining--; s.steps++;
                if (!s.batch_remaining) {
                    s.g = ca_gcd(ca_mont_from(&mont, s.q), s.active);
                    s.gcds++;
                    if (s.g == 1 && s.k == s.r) {
                        if (s.r == (1ULL << 40)) factor_next_attempt(&s);
                        else {
                            s.r <<= 1; s.x = s.y; s.remaining = s.r;
                            s.phase = FACTOR_ADVANCE;
                        }
                    } else if (s.g == s.active) s.phase = FACTOR_RECOVER;
                    else if (s.g > 1) found = s.g;
                }
            } else if (s.phase == FACTOR_RECOVER) {
                s.ys = ca_addmod(ca_mont_sqr(&mont, s.ys), cm, s.active);
                s.g = ca_gcd(ca_mont_from(&mont, s.x > s.ys ? s.x - s.ys : s.ys - s.x), s.active);
                s.steps++; s.gcds++;
                if (s.g == s.active) factor_next_attempt(&s);
                else if (s.g > 1) found = s.g;
            }
        }
        if (found) {
            if (found >= s.active || s.active % found || s.pending_count > 62) {
                ca_set_error("factor: invalid split or pending stack exhausted");
                rc = CA_ERR_INTERNAL; goto finish;
            }
            factor_push(&s, found);
            factor_push(&s, s.active / found);
            s.active = 0; s.phase = FACTOR_IDLE;
            if ((checkpoint_path || verbose) &&
                !factor_report(checkpoint_path, &s, elapsed_prior + ca_now() - t0,
                               "running", verbose, 1)) {
                rc = CA_ERR_INTERNAL; goto done;
            }
        }
        if ((s.steps & 255) == 0 || found) {
            double now = ca_now();
            if ((checkpoint_path || verbose) && now >= next_progress) {
                if (!factor_report(checkpoint_path, &s, elapsed_prior + now - t0,
                                   "running", verbose, 0)) {
                    rc = CA_ERR_INTERNAL; goto done;
                }
                next_progress = now + progress_interval;
            }
            if (checkpoint_path && now >= next_checkpoint) {
                s.seconds = elapsed_prior + now - t0;
                if (!factor_checkpoint_save(checkpoint_path, &s)) {
                    rc = CA_ERR_INTERNAL; goto done;
                }
                next_checkpoint = now + checkpoint_interval;
            }
        }
    }
    qsort(s.factors.f, s.factors.count, sizeof(ca_factor), cmp_factor);
    rc = CA_OK;
finish:
    if ((checkpoint_path || verbose) &&
        !factor_report(checkpoint_path, &s, elapsed_prior + ca_now() - t0,
                       rc == CA_OK ? "complete" : "stopped", verbose, 1))
        rc = CA_ERR_INTERNAL;
done:
    *out = s.factors;
    if (progress) {
        progress->steps = s.steps; progress->gcds = s.gcds;
        progress->active = s.active; progress->pending = s.pending_count;
        progress->seconds = elapsed_prior + ca_now() - t0;
    }
    return rc;
}

uint64_t ca_mult_order(uint64_t a, uint64_t p)
{
    a %= p;
    if (a == 0) return 0;
    ca_factorization f;
    ca_factorize(p - 1, &f);
    uint64_t ord = p - 1;
    for (unsigned i = 0; i < f.count; i++) {
        for (unsigned e = 0; e < f.f[i].e; e++) {
            uint64_t cand = ord / f.f[i].p;
            if (ca_powmod(a, cand, p) == 1) ord = cand; else break;
        }
    }
    return ord;
}

uint64_t ca_primitive_root(uint64_t p)
{
    if (!ca_is_prime(p)) return 0;
    if (p == 2) return 1;
    ca_factorization f;
    ca_factorize(p - 1, &f);
    for (uint64_t g = 2; g < p; g++) {
        int ok = 1;
        for (unsigned i = 0; i < f.count; i++) {
            if (ca_powmod(g, (p - 1) / f.f[i].p, p) == 1) { ok = 0; break; }
        }
        if (ok) return g;
    }
    return 0;
}

size_t ca_sieve_primes(uint64_t bound, uint32_t *primes, size_t cap)
{
    if (bound < 2) return 0;
    size_t n = (size_t)bound + 1;
    uint8_t *comp = calloc(n, 1);
    if (!comp) return 0;
    size_t count = 0;
    for (size_t i = 2; i < n; i++) {
        if (comp[i]) continue;
        if (primes) {
            if (count < cap) primes[count] = (uint32_t)i;
        }
        count++;
        for (size_t j = i * i; j < n; j += i) comp[j] = 1;
    }
    free(comp);
    return count;
}
