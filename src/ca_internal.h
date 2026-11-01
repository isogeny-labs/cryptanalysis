/*
 * ca_internal.h - private helpers shared by the library sources.
 */
#ifndef CA_INTERNAL_H
#define CA_INTERNAL_H

#include "cryptanalysis/ca_types.h"
#include "cryptanalysis/ca_modarith.h"

#include <stdlib.h>
#include <string.h>
#include <time.h>

/* ---- timing ------------------------------------------------------------ */
static inline double ca_now(void)
{
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return (double)ts.tv_sec + (double)ts.tv_nsec * 1e-9;
}

/* ---- xoshiro256** PRNG ------------------------------------------------- */
typedef struct ca_rng {
    uint64_t s[4];
} ca_rng;

static inline uint64_t ca_splitmix64(uint64_t *x)
{
    uint64_t z = (*x += 0x9E3779B97F4A7C15ULL);
    z = (z ^ (z >> 30)) * 0xBF58476D1CE4E5B9ULL;
    z = (z ^ (z >> 27)) * 0x94D049BB133111EBULL;
    return z ^ (z >> 31);
}

static inline void ca_rng_seed(ca_rng *r, uint64_t seed)
{
    uint64_t x = seed;
    r->s[0] = ca_splitmix64(&x);
    r->s[1] = ca_splitmix64(&x);
    r->s[2] = ca_splitmix64(&x);
    r->s[3] = ca_splitmix64(&x);
    if ((r->s[0] | r->s[1] | r->s[2] | r->s[3]) == 0) r->s[0] = 1;
}

static inline uint64_t ca_rotl(uint64_t x, int k) { return (x << k) | (x >> (64 - k)); }

static inline uint64_t ca_rng_next(ca_rng *r)
{
    uint64_t *s = r->s;
    uint64_t result = ca_rotl(s[1] * 5, 7) * 9;
    uint64_t t = s[1] << 17;
    s[2] ^= s[0];
    s[3] ^= s[1];
    s[1] ^= s[2];
    s[0] ^= s[3];
    s[2] ^= t;
    s[3] = ca_rotl(s[3], 45);
    return result;
}

/* uniform in [0, n) */
static inline uint64_t ca_rng_below(ca_rng *r, uint64_t n)
{
    if (n == 0) return ca_rng_next(r);
    ca_u128 m = (ca_u128)ca_rng_next(r) * n;
    uint64_t l = (uint64_t)m;
    if (l < n) {
        uint64_t t = (0 - n) % n;
        while (l < t) {
            m = (ca_u128)ca_rng_next(r) * n;
            l = (uint64_t)m;
        }
    }
    return (uint64_t)(m >> 64);
}

/* Seed from the environment or a user seed; seed==0 means "random". */
uint64_t ca_seed_or_random(uint64_t seed);

/* ---- 64-bit mixing hash ----------------------------------------------- */
static inline uint64_t ca_mix64(uint64_t x)
{
    x ^= x >> 33;
    x *= 0xff51afd7ed558ccdULL;
    x ^= x >> 33;
    x *= 0xc4ceb9fe1a85ec53ULL;
    x ^= x >> 33;
    return x;
}

/* ---- the EC walk step, shared by group_ec.c and rho.c ------------------ */
struct ca_group;
/* Points of a ca_group_ec_init group are w[0] = x, w[1] = y in Montgomery
 * form and w[2] = 1 at infinity (group_ec.c).  The rho walk reads these
 * through the group's vtable in general; for the native EC group it calls
 * the two helpers below directly (ec_hash and ec_canonicalize are these
 * same functions, so every value agrees) and its batched step adds the
 * table entries where they lie instead of copying them first. */

/* ec_hash: equal points hash equal; the walk's index and distinguished-
 * point test read it. */
static inline uint64_t ca_ec_hash_words(uint64_t x, uint64_t y, uint64_t inf)
{
    if (inf) return 0x9e3779b97f4a7c15ULL;
    return ca_mix64(x * 0x9E3779B97F4A7C15ULL ^ ca_mix64(y));
}

/* ec_canonicalize: the representative of {P, -P} with the smaller Montgomery
 * y; 1 when y was replaced by p - y.  The comparison is a coin flip on walk
 * data, so the result is selected rather than branched on.  y == 0 gives
 * p - y = p > y and no flip, so it needs no test of its own; the point at
 * infinity is left as it is. */
static inline int ca_ec_canon_words(uint64_t p, uint64_t *y, uint64_t inf)
{
    uint64_t yy = *y, ny = p - yy;
    uint64_t flip = (uint64_t)(ny < yy) & (uint64_t)(inf == 0);
    *y = flip ? ny : yy;
    return (int)flip;
}

/* Whether g is the native E(F_p) group of ca_group_ec_init (not a user
 * group of the same kind), so that the helpers here describe it. */
int ca_ec_group_is_native(const struct ca_group *g);

/* The field constants the affine group law reads, copied out of the group
 * once per batch.  The stores of a batch (points, denominators, products)
 * are all uint64_t lvalues, so through the group pointer the compiler would
 * have to assume each may overwrite p or the Montgomery context and reload
 * them, recomputing p^{-1}, at every multiplication. */
typedef struct ca_ec_consts {
    uint64_t p;      /* the modulus */
    uint64_t npi;    /* p^{-1} mod 2^64, which is -ca_mont.pinv */
    uint64_t a_mont; /* the curve coefficient a in Montgomery form */
    uint64_t one;    /* 1 in Montgomery form */
} ca_ec_consts;
ca_ec_consts ca_ec_consts_of(const struct ca_group *g);

/* Montgomery product with the modulus and p^{-1} in registers: the
 * reduction of ca_mont_redc, so the same residue. */
static inline uint64_t ca_ec_bmul(uint64_t a, uint64_t b, uint64_t p, uint64_t pinv_pos)
{
    ca_u128 t = (ca_u128)a * b;
    uint64_t u = (uint64_t)t * pinv_pos;
    uint64_t hi = (uint64_t)(t >> 64);
    uint64_t mh = (uint64_t)(((ca_u128)u * p) >> 64);
    uint64_t rr = hi - mh;
    if (hi < mh) rr += p;
    return rr;
}

/* The denominator the affine law a + b inverts: x_b - x_a, or 2 y_a for a
 * doubling, or 1 when no inversion is needed (a point at infinity, an
 * inverse pair), so that Montgomery's trick can invert a batch of them with
 * one field inversion.  No field multiplication is counted here. */
static inline uint64_t ca_ec_add_den(const ca_ec_consts *c, const ca_elem *a, const ca_elem *b)
{
    if (a->w[2] || b->w[2]) return c->one;
    if (a->w[0] == b->w[0]) {
        if (a->w[1] == b->w[1] && a->w[1] != 0) return ca_addmod(a->w[1], a->w[1], c->p);
        return c->one;
    }
    return ca_submod(b->w[0], a->w[0], c->p);
}

/* r = a + b given di, the inverse of ca_ec_add_den(c, a, b): the affine
 * group law with its special cases (the same points ca_group_op gives), its
 * multiplications and squarings counted as ec_batch_op counts them.  r may
 * alias a or b. */
static inline void ca_ec_add_with_di(const ca_ec_consts *c, ca_elem *r, const ca_elem *a,
                                     const ca_elem *b, uint64_t di)
{
    if (a->w[2]) {
        *r = *b;
        return;
    }
    if (b->w[2]) {
        *r = *a;
        return;
    }
    const uint64_t P = c->p, NPI = c->npi;
    const uint64_t ax = a->w[0], ay = a->w[1], bx = b->w[0], by = b->w[1];
    uint64_t lam;
    if (ax == bx) {
        if (ay == by && ay != 0) {
            CA_FC_ADD(CA_FC_SQR, 1);
            uint64_t x2 = ca_ec_bmul(ax, ax, P, NPI);
            uint64_t num = ca_addmod(ca_addmod(ca_addmod(x2, x2, P), x2, P), c->a_mont, P);
            CA_FC_ADD(CA_FC_MUL, 1);
            lam = ca_ec_bmul(num, di, P, NPI);
        } else {
            r->w[0] = r->w[1] = 0; /* the point at infinity */
            r->w[2] = 1;
            r->w[3] = 0;
            return;
        }
    } else {
        CA_FC_ADD(CA_FC_MUL, 1);
        lam = ca_ec_bmul(ca_submod(by, ay, P), di, P, NPI);
    }
    CA_FC_ADD(CA_FC_SQR, 1);
    uint64_t x3 = ca_submod(ca_submod(ca_ec_bmul(lam, lam, P, NPI), ax, P), bx, P);
    CA_FC_ADD(CA_FC_MUL, 1);
    uint64_t y3 = ca_submod(ca_ec_bmul(lam, ca_submod(ax, x3, P), P, NPI), ay, P);
    r->w[0] = x3;
    r->w[1] = y3;
    r->w[2] = 0;
    r->w[3] = 0;
}

/* ---- open addressing hash table: u64 key to two u64 values ------------- */
typedef struct ca_htab_entry {
    uint64_t key; /* 0 = empty */
    uint64_t v0;
    uint64_t v1;
} ca_htab_entry;

typedef struct ca_htab {
    ca_htab_entry *e;
    size_t cap;   /* power of two */
    size_t count;
    size_t max_count; /* resize threshold */
} ca_htab;

ca_status ca_htab_init(ca_htab *t, size_t expected);
void ca_htab_free(ca_htab *t);
/* Insert; if key already present returns 1 and writes the existing values
 * to old0 / old1 (may be NULL) without replacing.  Returns 0 if inserted,
 * -1 on allocation failure. */
int ca_htab_insert(ca_htab *t, uint64_t key, uint64_t v0, uint64_t v1,
                   uint64_t *old0, uint64_t *old1);
/* Lookup; returns 1 if found. */
int ca_htab_find(const ca_htab *t, uint64_t key, uint64_t *v0, uint64_t *v1);
size_t ca_htab_bytes(const ca_htab *t);

/* ---- open addressing hash table: u64 key to one u64 value ------------- */
/* The single-value tables (BSGS, Cheon, Mestre) take 16 bytes an entry
 * instead of 24, so there is a third less to zero and to walk.  Keys are
 * element hashes, already well mixed, so they index the table directly.
 * Semantics as ca_htab: key 0 is stored as 1, and inserting a present key
 * reports its value without replacing it. */
typedef struct ca_htab1_entry {
    uint64_t key; /* 0 = empty */
    uint64_t v0;
} ca_htab1_entry;

typedef struct ca_htab1 {
    ca_htab1_entry *e;
    size_t cap; /* power of two */
    size_t count;
    size_t max_count;
} ca_htab1;

ca_status ca_htab1_init(ca_htab1 *t, size_t expected);
void ca_htab1_free(ca_htab1 *t);
int ca_htab1_insert(ca_htab1 *t, uint64_t key, uint64_t v0, uint64_t *old0);
int ca_htab1_find(const ca_htab1 *t, uint64_t key, uint64_t *v0);
size_t ca_htab1_bytes(const ca_htab1 *t);
/* Start loading the slot a key probes first.  A hint only: the table may
 * be resized or modified before the access that follows, and nothing about
 * the table's contents or the order of operations changes.  Lets a block of
 * independent lookups overlap their cache misses. */
static inline void ca_htab1_prefetch(const ca_htab1 *t, uint64_t key)
{
    if (key == 0) key = 1;
    if (t->cap) __builtin_prefetch(&t->e[(size_t)key & (t->cap - 1)], 0, 1);
}

/* ---- misc -------------------------------------------------------------- */
static inline uint64_t ca_max_u64(uint64_t a, uint64_t b) { return a > b ? a : b; }
static inline uint64_t ca_min_u64(uint64_t a, uint64_t b) { return a < b ? a : b; }

void ca_set_error(const char *fmt, ...);

/* Whether n * base = n * target = O, i.e. both lie in the order-n subgroup.
 * When n is prime and base is not the identity this is exactly target in
 * <base>; a walk started without it never collides and never stops.  Sets
 * the error message and returns 0 on failure. */
struct ca_group;
/* k*a on a curve made by ca_group_ec_init, in Jacobian coordinates with one
 * inversion; returns 0 (and does nothing) for any other vtable. */
/* k*a in a group made by ca_group_zp_init, without the vtable; returns 0
 * (and does nothing) for any other vtable. */
int ca_zp_group_mul(const struct ca_group *g, ca_elem *r, const ca_elem *a, uint64_t k);
int ca_ec_group_mul(const struct ca_group *g, ca_elem *r, const ca_elem *a, uint64_t k);

int ca_check_members(const struct ca_group *g, const ca_elem *base, const ca_elem *target,
                     uint64_t n, const char *solver);

#endif /* CA_INTERNAL_H */
