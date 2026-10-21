/*
 * group_ec.c - short Weierstrass curves y^2 = x^3 + ax + b over F_p,
 * affine coordinates with Montgomery field arithmetic.
 *
 * Point layout: w[0] = x, w[1] = y (both Montgomery form), w[2] = 1 for
 * the point at infinity.
 */
#include "cryptanalysis/ca_group.h"
#include "ca_internal.h"
#include "dlog_checkpoint_internal.h"

#include <inttypes.h>
#include <math.h>

#define FX(e) ((e)->w[0])
#define FY(e) ((e)->w[1])
#define FINF(e) ((e)->w[2])

static inline uint64_t fadd(const ca_group *g, uint64_t a, uint64_t b) { return ca_addmod(a, b, g->p); }
static inline uint64_t fsub(const ca_group *g, uint64_t a, uint64_t b) { return ca_submod(a, b, g->p); }
static inline uint64_t fmul(const ca_group *g, uint64_t a, uint64_t b) { return ca_mont_mul(&g->mont, a, b); }
static inline uint64_t fsqr(const ca_group *g, uint64_t a) { return ca_mont_sqr(&g->mont, a); }
static inline uint64_t finv(const ca_group *g, uint64_t a) { return ca_mont_inv(&g->mont, a); }

static void ec_identity(const ca_group *g, ca_elem *r)
{
    (void)g;
    r->w[0] = r->w[1] = 0;
    r->w[2] = 1;
    r->w[3] = 0;
}

static int ec_is_identity(const ca_group *g, const ca_elem *a)
{
    (void)g;
    return FINF(a) != 0;
}

/* r = a + b given the already-inverted denominator (lambda numerator/denominator split). */
static inline void ec_add_with_inv(const ca_group *g, ca_elem *r, const ca_elem *a,
                                   const ca_elem *b, uint64_t lam)
{
    uint64_t x3 = fsub(g, fsub(g, fsqr(g, lam), FX(a)), FX(b));
    uint64_t y3 = fsub(g, fmul(g, lam, fsub(g, FX(a), x3)), FY(a));
    FX(r) = x3;
    FY(r) = y3;
    FINF(r) = 0;
    r->w[3] = 0;
}

static void ec_dbl(const ca_group *g, ca_elem *r, const ca_elem *a)
{
    if (FINF(a) || FY(a) == 0) { ec_identity(g, r); return; }
    uint64_t x2 = fsqr(g, FX(a));
    uint64_t num = fadd(g, fadd(g, fadd(g, x2, x2), x2), g->a_mont);
    uint64_t den = fadd(g, FY(a), FY(a));
    uint64_t lam = fmul(g, num, finv(g, den));
    ec_add_with_inv(g, r, a, a, lam);
}

static void ec_op(const ca_group *g, ca_elem *r, const ca_elem *a, const ca_elem *b)
{
    if (FINF(a)) { *r = *b; return; }
    if (FINF(b)) { *r = *a; return; }
    if (FX(a) == FX(b)) {
        if (FY(a) == FY(b)) { ec_dbl(g, r, a); return; }
        ec_identity(g, r);
        return;
    }
    uint64_t lam = fmul(g, fsub(g, FY(b), FY(a)), finv(g, fsub(g, FX(b), FX(a))));
    ec_add_with_inv(g, r, a, b, lam);
}

static void ec_inv(const ca_group *g, ca_elem *r, const ca_elem *a)
{
    if (FINF(a)) { *r = *a; return; }
    FX(r) = FX(a);
    FY(r) = FY(a) ? g->p - FY(a) : 0;
    FINF(r) = 0;
    r->w[3] = 0;
}

static int ec_equal(const ca_group *g, const ca_elem *a, const ca_elem *b)
{
    (void)g;
    if (FINF(a) || FINF(b)) return FINF(a) == FINF(b);
    return FX(a) == FX(b) && FY(a) == FY(b);
}

static uint64_t ec_hash(const ca_group *g, const ca_elem *a)
{
    (void)g;
    if (FINF(a)) return 0x9e3779b97f4a7c15ULL;
    return ca_mix64(FX(a) * 0x9E3779B97F4A7C15ULL ^ ca_mix64(FY(a)));
}

/* Montgomery product with the modulus and -(-p^{-1}) = p^{-1} passed in
 * registers; the reduction of ca_mont_redc, so the same result. */
static inline uint64_t bmul(uint64_t a, uint64_t b, uint64_t p, uint64_t pinv_pos)
{
    ca_u128 t = (ca_u128)a * b;
    uint64_t u = (uint64_t)t * pinv_pos;
    uint64_t hi = (uint64_t)(t >> 64);
    uint64_t mh = (uint64_t)(((ca_u128)u * p) >> 64);
    uint64_t rr = hi - mh;
    if (hi < mh) rr += p;
    return rr;
}

/*
 * Batched affine addition with Montgomery's simultaneous inversion trick:
 * one field inversion for n additions at the cost of 3(n-1) extra
 * multiplications.  Special cases (infinity, doubling, inverse pairs)
 * are handled inline so that the common path stays branch-light.
 */
static void ec_batch_op(const ca_group *g, ca_elem *r, const ca_elem *a, const ca_elem *b,
                        size_t n, uint64_t *scratch)
{
    if (n == 0) return;
    /* The field constants go into locals first.  The stores below (r, and
     * den/pre in scratch) are all uint64_t lvalues, so the compiler must
     * assume each may overwrite g->p or g->mont and would reload them, and
     * recompute -pinv, at every multiplication.  Same Montgomery reduction as
     * ca_mont_redc, so the same residues. */
    const uint64_t P = g->p, NPI = (uint64_t)0 - g->mont.pinv, AM = g->a_mont;
    const uint64_t one = g->mont.r1;
#define BM(x, y) bmul((x), (y), P, NPI)
#define BA(x, y) ca_addmod((x), (y), P)
#define BS(x, y) ca_submod((x), (y), P)
    uint64_t *den = scratch;       /* n denominators */
    uint64_t *pre = scratch + n;   /* n prefix products */
    for (size_t i = 0; i < n; i++) {
        uint64_t d;
        if (FINF(&a[i]) || FINF(&b[i])) d = one;
        else if (FX(&a[i]) == FX(&b[i])) {
            if (FY(&a[i]) == FY(&b[i]) && FY(&a[i]) != 0)
                d = BA(FY(&a[i]), FY(&a[i]));
            else d = one;
        } else
            d = BS(FX(&b[i]), FX(&a[i]));
        den[i] = d;
        pre[i] = i ? BM(pre[i - 1], d) : d;
    }
    uint64_t inv = finv(g, pre[n - 1]);
    for (size_t i = n; i-- > 0;) {
        uint64_t di = i ? BM(inv, pre[i - 1]) : inv; /* den[i]^{-1} */
        inv = BM(inv, den[i]);
        const ca_elem *A = &a[i], *B = &b[i];
        if (FINF(A)) { r[i] = *B; continue; }
        if (FINF(B)) { r[i] = *A; continue; }
        const uint64_t ax = FX(A), ay = FY(A);
        uint64_t lam;
        if (ax == FX(B)) {
            if (ay == FY(B) && ay != 0) {
                uint64_t x2 = bmul(ax, ax, P, NPI);
                uint64_t num = BA(BA(BA(x2, x2), x2), AM);
                lam = BM(num, di);
            } else {
                ec_identity(g, &r[i]);
                continue;
            }
        } else {
            lam = BM(BS(FY(B), ay), di);
        }
        const uint64_t bx = FX(B);
        uint64_t x3 = BS(BS(bmul(lam, lam, P, NPI), ax), bx);
        uint64_t y3 = BS(BM(lam, BS(ax, x3)), ay);
        FX(&r[i]) = x3;
        FY(&r[i]) = y3;
        FINF(&r[i]) = 0;
        r[i].w[3] = 0;
    }
#undef BM
#undef BA
#undef BS
}

static int ec_on_curve_words(const ca_group *g, uint64_t x, uint64_t y)
{
    uint64_t xm = ca_mont_to(&g->mont, x), ym = ca_mont_to(&g->mont, y);
    uint64_t lhs = fsqr(g, ym);
    uint64_t rhs = fadd(g, fmul(g, fadd(g, fsqr(g, xm), g->a_mont), xm), g->b_mont);
    return lhs == rhs;
}

static int ec_encode(const ca_group *g, ca_elem *r, const uint64_t *words)
{
    if (words[2]) { ec_identity(g, r); return 1; }
    if (words[0] >= g->p || words[1] >= g->p) return 0;
    if (!ec_on_curve_words(g, words[0], words[1])) return 0;
    FX(r) = ca_mont_to(&g->mont, words[0]);
    FY(r) = ca_mont_to(&g->mont, words[1]);
    FINF(r) = 0;
    r->w[3] = 0;
    return 1;
}

static void ec_decode(const ca_group *g, uint64_t *words, const ca_elem *a)
{
    if (FINF(a)) { words[0] = words[1] = 0; words[2] = 1; words[3] = 0; return; }
    words[0] = ca_mont_from(&g->mont, FX(a));
    words[1] = ca_mont_from(&g->mont, FY(a));
    words[2] = 0;
    words[3] = 0;
}

static int ec_is_valid(const ca_group *g, const ca_elem *a)
{
    if (FINF(a)) return 1;
    if (FX(a) >= g->p || FY(a) >= g->p) return 0;
    uint64_t lhs = fsqr(g, FY(a));
    uint64_t rhs = fadd(g, fmul(g, fadd(g, fsqr(g, FX(a)), g->a_mont), FX(a)), g->b_mont);
    return lhs == rhs;
}

/* Canonical representative of {P, -P}: the one whose (Montgomery) y is
 * the smaller of y and p - y.  Montgomery form is a bijection commuting
 * with negation, so this is a valid canonical choice. */
static int ec_canonicalize(const ca_group *g, ca_elem *a)
{
    if (FINF(a) || FY(a) == 0) return 0;
    uint64_t ny = g->p - FY(a);
    if (ny < FY(a)) { FY(a) = ny; return 1; }
    return 0;
}

static const ca_group_vtable ec_vt = {
    ec_op, ec_dbl, ec_inv, ec_identity, ec_is_identity, ec_equal, ec_hash,
    ec_batch_op, ec_encode, ec_decode, ec_is_valid, ec_canonicalize,
};

/*
 * Scalar multiplication in Jacobian coordinates (X : Y : Z), affine
 * (X/Z^2, Y/Z^3), all in Montgomery form.  An affine step costs a field
 * inversion (an extended gcd, ~660 of an affine add's ~880 instructions);
 * a Jacobian step costs a dozen multiplications, and one inversion at the
 * end returns the same canonical affine point.  The special cases match
 * ec_op/ec_dbl: Y = 0 doubles to the identity, and P + Q with equal
 * abscissae is a double or the identity.
 */
typedef struct ec_jac {
    uint64_t x, y, z;
    int inf;
} ec_jac;

/* 2P (dbl-2007-bl, general a). */
static void ec_jac_dbl(const ca_group *g, ec_jac *r)
{
    if (r->inf) return;
    if (r->y == 0) {
        r->inf = 1;
        return;
    }
    uint64_t xx = fsqr(g, r->x), yy = fsqr(g, r->y), yyyy = fsqr(g, yy), zz = fsqr(g, r->z);
    uint64_t t = fadd(g, r->x, yy);
    uint64_t s = fsub(g, fsub(g, fsqr(g, t), xx), yyyy);
    s = fadd(g, s, s);
    uint64_t m = fadd(g, fadd(g, fadd(g, xx, xx), xx), fmul(g, g->a_mont, fsqr(g, zz)));
    uint64_t x3 = fsub(g, fsub(g, fsqr(g, m), s), s);
    uint64_t y8 = fadd(g, yyyy, yyyy);
    y8 = fadd(g, y8, y8);
    y8 = fadd(g, y8, y8);
    uint64_t y3 = fsub(g, fmul(g, m, fsub(g, s, x3)), y8);
    uint64_t yz = fadd(g, r->y, r->z);
    uint64_t z3 = fsub(g, fsub(g, fsqr(g, yz), yy), zz);
    r->x = x3;
    r->y = y3;
    r->z = z3;
}

/* P + (x2, y2) for a finite affine (x2, y2) (madd-2007-bl). */
static void ec_jac_add_affine(const ca_group *g, ec_jac *r, uint64_t x2, uint64_t y2)
{
    if (r->inf) {
        r->x = x2;
        r->y = y2;
        r->z = g->mont.r1;
        r->inf = 0;
        return;
    }
    uint64_t z1z1 = fsqr(g, r->z);
    uint64_t u2 = fmul(g, x2, z1z1);
    uint64_t s2 = fmul(g, fmul(g, y2, r->z), z1z1);
    uint64_t h = fsub(g, u2, r->x);
    uint64_t rr = fsub(g, s2, r->y);
    if (h == 0) {
        if (rr == 0)
            ec_jac_dbl(g, r);
        else
            r->inf = 1;
        return;
    }
    rr = fadd(g, rr, rr);
    uint64_t hh = fsqr(g, h);
    uint64_t i = fadd(g, hh, hh);
    i = fadd(g, i, i);
    uint64_t j = fmul(g, h, i);
    uint64_t v = fmul(g, r->x, i);
    uint64_t x3 = fsub(g, fsub(g, fsub(g, fsqr(g, rr), j), v), v);
    uint64_t y1j = fmul(g, r->y, j);
    uint64_t y3 = fsub(g, fsub(g, fmul(g, rr, fsub(g, v, x3)), y1j), y1j);
    uint64_t zh = fadd(g, r->z, h);
    uint64_t z3 = fsub(g, fsub(g, fsqr(g, zh), z1z1), hh);
    r->x = x3;
    r->y = y3;
    r->z = z3;
}

int ca_ec_group_mul(const ca_group *g, ca_elem *r, const ca_elem *a, uint64_t k)
{
    if (g->vt != &ec_vt) return 0; /* a caller's own vtable: use it */
    const uint64_t ax = FX(a), ay = FY(a);
    const int ainf = FINF(a) != 0;
    ec_jac acc = {0, 0, 0, 1};
    if (!ainf) {
        for (int bit = 63 - (k ? __builtin_clzll(k) : 63); k && bit >= 0; bit--) {
            ec_jac_dbl(g, &acc);
            if ((k >> bit) & 1) ec_jac_add_affine(g, &acc, ax, ay);
        }
    }
    if (acc.inf) {
        ec_identity(g, r);
        return 1;
    }
    uint64_t zi = finv(g, acc.z), zi2 = fsqr(g, zi);
    FX(r) = fmul(g, acc.x, zi2);
    FY(r) = fmul(g, acc.y, fmul(g, zi2, zi));
    FINF(r) = 0;
    r->w[3] = 0;
    return 1;
}

ca_status ca_group_ec_init(ca_group *g, uint64_t p, uint64_t a, uint64_t b, uint64_t order)
{
    memset(g, 0, sizeof(*g));
    if (p < 5 || !ca_is_prime(p)) {
        ca_set_error("p=%llu is not a prime > 3", (unsigned long long)p);
        return CA_ERR_INVALID;
    }
    a %= p;
    b %= p;
    /* discriminant 4a^3 + 27b^2 != 0 */
    uint64_t d = ca_addmod(ca_mulmod(4, ca_powmod(a, 3, p), p),
                           ca_mulmod(27, ca_mulmod(b, b, p), p), p);
    if (d == 0) {
        ca_set_error("curve is singular");
        return CA_ERR_INVALID;
    }
    g->vt = &ec_vt;
    g->kind = CA_GROUP_EC;
    g->p = p;
    g->a = a;
    g->b = b;
    g->order = order;
    ca_mont_init(&g->mont, p);
    g->a_mont = ca_mont_to(&g->mont, a);
    g->b_mont = ca_mont_to(&g->mont, b);
    g->cofactor = 0;
    return CA_OK;
}

void ca_ec_endo(const ca_group *g, ca_elem *r, const ca_elem *a)
{
    if (g->endo_kind == 0 || FINF(a)) {
        *r = *a;
        return;
    }
    if (g->endo_kind == 1) {
        /* j = 0: psi(x, y) = (beta * x, -y), beta a cube root of unity */
        FX(r) = fmul(g, g->endo_c_mont, FX(a));
        FY(r) = FY(a) ? g->p - FY(a) : 0;
    } else {
        /* j = 1728: psi(x, y) = (-x, i * y), i = sqrt(-1) */
        FX(r) = FX(a) ? g->p - FX(a) : 0;
        FY(r) = fmul(g, g->endo_c_mont, FY(a));
    }
    FINF(r) = 0;
    r->w[3] = 0;
}

int ca_ec_lift_x(const ca_group *g, ca_elem *r, uint64_t x)
{
    x %= g->p;
    uint64_t rhs = ca_addmod(ca_mulmod(ca_addmod(ca_mulmod(x, x, g->p), g->a, g->p), x, g->p),
                             g->b, g->p);
    uint64_t y;
    if (!ca_sqrtmod_prime(rhs, g->p, &y)) return 0;
    if (y > g->p - y) y = g->p - y;
    const uint64_t w[4] = {x, y, 0, 0};
    return ec_encode(g, r, w);
}

void ca_ec_random_point(const ca_group *g, ca_elem *r, uint64_t seed)
{
    ca_rng rng;
    ca_rng_seed(&rng, ca_seed_or_random(seed));
    while (1) {
        uint64_t x = ca_rng_below(&rng, g->p);
        if (ca_ec_lift_x(g, r, x)) {
            if (ca_rng_next(&rng) & 1) ec_inv(g, r, r);
            return;
        }
    }
}

/* ---- Mestre's point counting ------------------------------------------ */

typedef struct ec_count_watch {
    int (*report)(void *context, const char *phase, uint64_t done,
                  uint64_t total, uint64_t group_ops);
    void *context;
    int failed;
} ec_count_watch;

static int ec_count_emit(ec_count_watch *watch, const char *phase, uint64_t done,
                         uint64_t total, uint64_t current_ops)
{
    if (watch && !watch->failed &&
        !watch->report(watch->context, phase, done, total, current_ops))
        watch->failed = 1;
    return !watch || !watch->failed;
}

/* Fill consecutive multiples with one batched inversion per prefix
 * expansion, plus its offset doubling.  Preserve affine-addition order. */
static void ec_multiples(const ca_group *g, ca_elem *out, const ca_elem *base,
                         size_t count, uint64_t *scratch)
{
    ec_identity(g, &out[0]);
    if (count == 1) return;
    out[1] = *base;
    ca_elem addends[64];
    for (size_t span = 2; span < count; span *= 2) {
        ca_elem offset;
        ec_dbl(g, &offset, &out[span / 2]);
        size_t n = count - span < span ? count - span : span;
        for (size_t i = 0; i < n; i++) addends[i] = offset;
        ec_batch_op(g, out + span, out, addends, n, scratch);
    }
}

/* All k in [lo, lo+width) with k*P == T, appended to out (up to cap).
 * Returns the number found (may exceed cap; only cap are stored). */
static size_t ec_interval_all(const ca_group *g, const ca_elem *P, const ca_elem *T, uint64_t lo,
                              uint64_t width, uint64_t *out, size_t cap, ca_stats *st,
                              ec_count_watch *watch)
{
    uint64_t m = ca_isqrt(width) + 1;
    ca_htab1 tab;
    if (ca_htab1_init(&tab, (size_t)m) != CA_OK) {
        if (watch) watch->failed = 2;
        return 0;
    }
    /* Baby and giant steps go EC_LANES at a time through ec_batch_op, one
     * field inversion per block; hashing, insertion, lookup and every
     * count follow the one-step loops, and elements a block computes past
     * the last one used are not charged. */
    enum { EC_LANES = 64 };
    ca_elem lane[EC_LANES], stride[EC_LANES];
    uint64_t scratch[2 * EC_LANES];
    ca_elem cur;
    uint64_t small_order = 0;
    {
        const uint64_t first = m < EC_LANES ? m : EC_LANES;
        ec_multiples(g, lane, P, (size_t)first, scratch);
        if (m > EC_LANES) {
            ec_dbl(g, &stride[0], &lane[EC_LANES / 2]);
            for (int c = 1; c < EC_LANES; c++) stride[c] = stride[0];
        }
        uint64_t steps_done = m;
        for (uint64_t j0 = 0; j0 < m && !small_order; j0 += EC_LANES) {
            const uint64_t n = m - j0 < EC_LANES ? m - j0 : EC_LANES;
            for (uint64_t c = 0; c < n; c++) {
                uint64_t old;
                int inserted = ca_htab1_insert(&tab, ec_hash(g, &lane[c]), j0 + c, &old);
                if (inserted < 0) {
                    if (watch) watch->failed = 2;
                    ca_htab1_free(&tab);
                    return 0;
                }
                if (inserted == 1) {
                    /* (j0 + c) P == old P: P has small order j0 + c - old */
                    small_order = j0 + c - old;
                    steps_done = j0 + c;
                    break;
                }
            }
            if (!small_order && j0 + EC_LANES < m) {
                const uint64_t next = m - j0 - EC_LANES;
                ec_batch_op(g, lane, lane, stride, next < EC_LANES ? next : EC_LANES, scratch);
            }
            if (!ec_count_emit(watch, "baby", small_order ? steps_done : j0 + n,
                               m, st ? st->group_ops + (small_order ? steps_done : j0 + n) : 0)) {
                ca_htab1_free(&tab);
                return 0;
            }
        }
        if (st) st->group_ops += steps_done;
    }
    size_t found = 0;
    if (small_order) {
        /* k*P == T: find k0 < small_order with k0*P == T then enumerate. */
        ec_identity(g, &cur);
        uint64_t k0 = small_order;
        for (uint64_t j = 0; j < small_order; j++) {
            if (ec_equal(g, &cur, T)) {
                k0 = j;
                break;
            }
            ec_op(g, &cur, &cur, P);
            if ((j & 255) == 255 &&
                !ec_count_emit(watch, "small-order", j + 1, small_order,
                               st ? st->group_ops : 0)) {
                ca_htab1_free(&tab);
                return 0;
            }
        }
        if (k0 < small_order) {
            /* smallest k >= lo with k == k0 (mod small_order) */
            uint64_t so = small_order;
            ca_u128 k = (ca_u128)lo + (k0 + so - lo % so) % so;
            for (; k < (ca_u128)lo + width; k += so) {
                if (found < cap) out[found] = (uint64_t)k;
                found++;
            }
        }
        ca_htab1_free(&tab);
        return found;
    }
    /* giant steps: R = T - (lo + i m) P; if R == jP then k = lo + i m + j */
    ca_elem mP, negmP, base, R;
    ca_group_mul(g, &mP, P, m, st ? &st->group_ops : NULL);
    ec_inv(g, &negmP, &mP);
    /* base = -lo * P */
    ca_group_mul(g, &base, P, lo, NULL);
    ec_inv(g, &base, &base);
    ec_op(g, &R, T, &base); /* T - lo P */
    uint64_t steps = m ? width / m + 1 : 1;
    /* giant[k] = k (-m P); a block is R + giant[k] for k < EC_LANES */
    ca_elem giant[EC_LANES], block_step, Rrep[EC_LANES];
    ec_multiples(g, giant, &negmP, (size_t)(steps < EC_LANES ? steps : EC_LANES), scratch);
    if (steps > EC_LANES) ec_dbl(g, &block_step, &giant[EC_LANES / 2]);
    for (uint64_t i0 = 0; i0 < steps; i0 += EC_LANES) {
        const uint64_t n = steps - i0 < EC_LANES ? steps - i0 : EC_LANES;
        for (uint64_t k = 0; k < n; k++) Rrep[k] = R;
        ec_batch_op(g, lane, Rrep, giant, n, scratch);
        for (uint64_t k = 0; k < n; k++) {
            const uint64_t i = i0 + k;
            uint64_t j;
            if (ca_htab1_find(&tab, ec_hash(g, &lane[k]), &j)) {
                /* verify */
                ca_elem chk;
                ca_group_mul(g, &chk, P, j, NULL);
                if (ec_equal(g, &chk, &lane[k])) {
                    ca_u128 kk = (ca_u128)lo + (ca_u128)i * m + j;
                    if (kk < (ca_u128)lo + width) {
                        if (found < cap) out[found] = (uint64_t)kk;
                        found++;
                    }
                }
            }
        }
        if (st) st->group_ops += n;
        if (!ec_count_emit(watch, "giant", i0 + n, steps,
                           st ? st->group_ops : 0)) {
            ca_htab1_free(&tab);
            return 0;
        }
        if (n == EC_LANES) ec_op(g, &R, &R, &block_step);
    }
    ca_htab1_free(&tab);
    return found;
}

static ca_status ec_count_once(const ca_group *g, uint64_t *order, ca_stats *st,
                               uint64_t seed, int *ambiguous)
{
    /* Hasse interval [p + 1 - 2 sqrt(p), p + 1 + 2 sqrt(p)], computed in
     * 128 bits so that primes up to 2^64 - 59 (whose p + 1 still fits a
     * uint64_t) are handled without overflow. */
    uint64_t p = g->p;
    uint64_t s = ca_isqrt(p);
    while ((ca_u128)s * s < p) s++; /* ceil(sqrt(p)) */
    ca_u128 lo128 = (ca_u128)p + 1 - 2 * (ca_u128)s;
    uint64_t lo = lo128 < 1 ? 1 : (uint64_t)lo128;
    uint64_t width = 4 * s + 1;
    /* Near 2^64 the top of the Hasse interval does not fit a uint64_t:
     * search only the part that does (the walk would otherwise wrap and
     * return the order modulo 2^64), and report an order above 2^64 as
     * not found rather than truncated. */
    if (width - 1 > UINT64_MAX - lo) width = UINT64_MAX - lo + 1;
    ca_rng rng;
    ca_rng_seed(&rng, seed);
    enum { CAP = 4096 };
    uint64_t *cands = malloc(CAP * sizeof(uint64_t));
    uint64_t *cur = malloc(CAP * sizeof(uint64_t));
    if (!cands || !cur) { free(cands); free(cur); return CA_ERR_NOMEM; }
    size_t ncand = 0;
    int have = 0;
    *ambiguous = 0;
    ca_status rc = CA_ERR_NOT_FOUND;
    for (int tries = 0; tries < 24; tries++) {
        ca_elem P, T;
        ca_ec_random_point(g, &P, ca_rng_next(&rng));
        ec_identity(g, &T);
        size_t n = ec_interval_all(g, &P, &T, lo, width, cur, CAP, st, NULL);
        if (n == 0 || n > CAP) continue;
        if (!have) {
            memcpy(cands, cur, n * sizeof(uint64_t));
            ncand = n;
            have = 1;
        } else {
            size_t w = 0;
            for (size_t i = 0; i < ncand; i++) {
                for (size_t j = 0; j < n; j++) {
                    if (cands[i] == cur[j]) { cands[w++] = cands[i]; break; }
                }
            }
            ncand = w;
        }
        if (ncand == 1) {
            *order = cands[0];
            rc = CA_OK;
            break;
        }
        if (ncand == 0) { rc = CA_ERR_INTERNAL; break; }
    }
    if (rc != CA_OK && have && ncand > 1) *ambiguous = 1;
    free(cands);
    free(cur);
    return rc;
}

ca_status ca_ec_count_points(uint64_t p, uint64_t a, uint64_t b, uint64_t *order, ca_stats *st)
{
    ca_group g;
    ca_status rc = ca_group_ec_init(&g, p, a, b, 0);
    if (rc != CA_OK) return rc;
    ca_stats local = {0};
    if (!st) st = &local;
    double t0 = ca_now();
    if (p < 2000) {
        /* brute force: count x with x^3+ax+b a square */
        uint64_t cnt = 1;
        for (uint64_t x = 0; x < p; x++) {
            uint64_t rhs = ca_addmod(ca_mulmod(ca_addmod(ca_mulmod(x, x, p), a % p, p), x, p), b % p, p);
            int l = ca_legendre(rhs, p);
            cnt += (uint64_t)(1 + l);
        }
        *order = cnt;
        st->seconds += ca_now() - t0;
        return CA_OK;
    }
    int amb = 0;
    rc = ec_count_once(&g, order, st, 0x5eed5eedULL ^ p, &amb);
    if (rc != CA_OK && amb) {
        /* Use the quadratic twist: #E + #E' = 2p + 2. */
        uint64_t d = 2;
        while (ca_legendre(d, p) != -1) d++;
        uint64_t d2 = ca_mulmod(d, d, p), d3 = ca_mulmod(d2, d, p);
        ca_group tw;
        if (ca_group_ec_init(&tw, p, ca_mulmod(a, d2, p), ca_mulmod(b, d3, p), 0) == CA_OK) {
            uint64_t ot;
            int amb2 = 0;
            if (ec_count_once(&tw, &ot, st, 0x7715ULL ^ p, &amb2) == CA_OK) {
                /* #E + #E' = 2p + 2; 128-bit so p > 2^63 does not wrap,
                 * and an order that does not fit 64 bits is refused. */
                ca_u128 o = (ca_u128)2 * p + 2 - ot;
                if (o <= (ca_u128)UINT64_MAX) {
                    *order = (uint64_t)o;
                    rc = CA_OK;
                }
            }
        }
    }
    st->seconds += ca_now() - t0;
    if (rc != CA_OK && (ca_u128)p + 1 + 2 * ((ca_u128)ca_isqrt(p) + 1) > (ca_u128)UINT64_MAX)
        ca_set_error("p = %llu: #E(F_p) may exceed 64 bits and was not found below 2^64",
                     (unsigned long long)p);
    return rc;
}

enum { EC_COUNT_SMALL = 0, EC_COUNT_ORIGINAL = 1,
       EC_COUNT_TWIST = 2, EC_COUNT_DONE = 3, EC_COUNT_FAILED = 4,
       EC_COUNT_CAP = 4096 };

typedef struct ec_count_checkpoint {
    char magic[8];
    uint32_t version, phase;
    uint64_t p, a, b, next_x, small_count, order;
    ca_rng rng;
    uint32_t tries, have, ncand, reserved;
    uint64_t candidates[EC_COUNT_CAP];
    uint64_t work_units, group_ops;
    double seconds;
    uint64_t checksum;
} ec_count_checkpoint;

static const char *ec_count_phase_name(uint32_t phase)
{
    if (phase == EC_COUNT_SMALL) return "field-scan";
    if (phase == EC_COUNT_ORIGINAL) return "original";
    if (phase == EC_COUNT_TWIST) return "twist";
    if (phase == EC_COUNT_FAILED) return "not-found";
    return "complete";
}

static int ec_count_state_valid(const ec_count_checkpoint *s,
                                uint64_t p, uint64_t a, uint64_t b)
{
    if (memcmp(s->magic, "CAECORD1", 8) || s->version != 1 ||
        s->p != p || s->a != a || s->b != b || s->reserved ||
        s->phase > EC_COUNT_FAILED || s->tries > 24 || s->have > 1 ||
        s->ncand > EC_COUNT_CAP || (!s->have && s->ncand) ||
        (s->have && !s->ncand) ||
        !isfinite(s->seconds) || s->seconds < 0 || s->next_x > p ||
        (p < 2000 && s->phase != EC_COUNT_SMALL && s->phase != EC_COUNT_DONE) ||
        (p >= 2000 && s->phase == EC_COUNT_SMALL) ||
        (s->phase == EC_COUNT_DONE && !s->order)) return 0;
    if (p < 2000) {
        if (s->work_units != s->next_x || s->group_ops ||
            s->small_count < 1 || s->small_count > 2 * s->next_x + 1 ||
            (s->phase == EC_COUNT_DONE &&
             (s->next_x != p || s->order != s->small_count))) return 0;
    } else if (s->next_x || s->work_units != s->group_ops) return 0;
    if (s->phase == EC_COUNT_DONE) {
        ca_u128 center = (ca_u128)p + 1;
        ca_u128 radius = 2 * ((ca_u128)ca_isqrt(p) + 1);
        if ((ca_u128)s->order + radius < center ||
            (ca_u128)s->order > center + radius) return 0;
    }
    return 1;
}

static int ec_count_checkpoint_save(const char *path, ec_count_checkpoint *s)
{
    if (!path) return 1;
    s->checksum = 0;
    s->checksum = dlog_ckpt_hash(s, sizeof(*s), UINT64_C(14695981039346656037));
    dlog_ckpt_file w;
    int ok = dlog_ckpt_begin(&w, path);
    if (ok) ok = fwrite(s, 1, sizeof(*s), w.f) == sizeof(*s);
    ok = dlog_ckpt_finish(&w, ok);
    if (!ok) ca_set_error("ec-order: cannot persist checkpoint");
    return ok;
}

/* 1 = restored, 0 = fresh, -1 = invalid or unreadable. */
static int ec_count_checkpoint_load(const char *path, uint64_t p, uint64_t a,
                                     uint64_t b, ec_count_checkpoint *s)
{
    if (!path) return 0;
    FILE *f = fopen(path, "rb");
    if (!f) {
        if (errno == ENOENT) return 0;
        ca_set_error("ec-order: cannot open checkpoint");
        return -1;
    }
    ec_count_checkpoint got = {0};
    int ok = fread(&got, 1, sizeof(got), f) == sizeof(got) && fgetc(f) == EOF;
    if (ferror(f)) ok = 0;
    fclose(f);
    uint64_t checksum = got.checksum;
    got.checksum = 0;
    if (!ok || dlog_ckpt_hash(&got, sizeof(got), UINT64_C(14695981039346656037)) != checksum ||
        !ec_count_state_valid(&got, p, a, b)) {
        ca_set_error("ec-order: checkpoint identity, length or checksum failed");
        return -1;
    }
    got.checksum = checksum;
    *s = got;
    return 1;
}

ca_status ca_ec_count_checkpoint_validate(uint64_t p, uint64_t a, uint64_t b,
                                          const char *checkpoint_path,
                                          uint64_t *completed_order)
{
    if (!p || !checkpoint_path) return CA_ERR_INVALID;
    ec_count_checkpoint s;
    int loaded = ec_count_checkpoint_load(checkpoint_path, p, a, b, &s);
    if (loaded == 1) {
        if (completed_order) *completed_order = s.phase == EC_COUNT_DONE ? s.order : 0;
        return CA_OK;
    }
    if (!loaded) ca_set_error("ec-order: checkpoint is missing");
    return CA_ERR_INVALID;
}

typedef struct ec_count_runtime {
    ec_count_checkpoint *state;
    const char *checkpoint_path;
    double start, prior, next_progress, next_checkpoint;
    uint32_t progress_interval, checkpoint_interval;
    int verbose;
} ec_count_runtime;

static int ec_count_progress_write(ec_count_runtime *run, const char *status,
                                   const char *detail, uint64_t done, uint64_t total,
                                   uint64_t current_ops)
{
    ec_count_checkpoint *s = run->state;
    double seconds = run->prior + ca_now() - run->start;
    char phase[40];
    int pl = snprintf(phase, sizeof(phase), "%s%s%s", ec_count_phase_name(s->phase),
                      detail ? "-" : "", detail ? detail : "");
    if (pl < 0 || (size_t)pl >= sizeof(phase)) return 0;
    if (run->verbose) {
        if (s->phase == EC_COUNT_SMALL || (s->phase == EC_COUNT_DONE && !s->tries))
            fprintf(stderr, "[ec-order] %s x=%" PRIu64 "/%" PRIu64
                            " work=%" PRIu64 " %.1fs\n",
                    phase, s->next_x, s->p, s->work_units, seconds);
        else fprintf(stderr, "[ec-order] %s trial=%u/24 batch=%" PRIu64
                             "/%" PRIu64 " work=%" PRIu64 " ops=%" PRIu64
                             " candidates=%u %.1fs\n",
                     phase, s->tries, done, total, s->work_units + current_ops,
                     s->group_ops + current_ops, s->ncand, seconds);
    }
    if (!run->checkpoint_path) return 1;
    char *path = dlog_ckpt_path(run->checkpoint_path, ".progress.json");
    if (!path) {
        ca_set_error("ec-order: cannot allocate progress path");
        return 0;
    }
    dlog_ckpt_file w;
    int ok = dlog_ckpt_begin(&w, path);
    if (ok) ok = fprintf(w.f,
        "{\"status\":\"%s\",\"phase\":\"%s\",\"p\":%" PRIu64
        ",\"a\":%" PRIu64 ",\"b\":%" PRIu64
        ",\"batch_done\":%" PRIu64 ",\"batch_total\":%" PRIu64
        ",\"completed_trials\":%u,\"candidates\":%u,\"field_x\":%" PRIu64
        ",\"work_units\":%" PRIu64 ",\"group_ops\":%" PRIu64
        ",\"elapsed_seconds\":%.3f}\n",
        status, phase, s->p, s->a, s->b, done, total, s->tries, s->ncand,
        s->next_x, s->work_units + current_ops, s->group_ops + current_ops,
        seconds) > 0;
    ok = dlog_ckpt_finish(&w, ok);
    free(path);
    if (!ok) ca_set_error("ec-order: cannot persist progress");
    return ok;
}

static int ec_count_report(ec_count_runtime *run, const char *status,
                            const char *detail, uint64_t done, uint64_t total,
                            uint64_t current_ops, int save)
{
    if (save) {
        run->state->seconds = run->prior + ca_now() - run->start;
        if (!ec_count_checkpoint_save(run->checkpoint_path, run->state)) return 0;
    }
    return ec_count_progress_write(run, status, detail, done, total, current_ops);
}

static int ec_count_watch_report(void *context, const char *phase, uint64_t done,
                                  uint64_t total, uint64_t current_ops)
{
    ec_count_runtime *run = context;
    double now = ca_now();
    if (now >= run->next_checkpoint && run->checkpoint_path) {
        run->state->seconds = run->prior + now - run->start;
        if (!ec_count_checkpoint_save(run->checkpoint_path, run->state)) return 0;
        run->next_checkpoint = now + run->checkpoint_interval;
    }
    if (now < run->next_progress) return 1;
    if (!ec_count_progress_write(run, "running", phase, done, total, current_ops)) return 0;
    run->next_progress = now + run->progress_interval;
    return 1;
}

static void ec_count_fill_progress(const ec_count_checkpoint *s,
                                    ca_ec_count_progress *progress, double seconds)
{
    if (!progress) return;
    progress->work_units = s->work_units;
    progress->group_ops = s->group_ops;
    progress->field_x = s->next_x;
    progress->completed_trials = s->tries;
    progress->candidates = s->ncand;
    progress->seconds = seconds;
    progress->phase = ec_count_phase_name(s->phase);
}

ca_status ca_ec_count_points_checkpointed(uint64_t p, uint64_t a, uint64_t b,
                                          const char *checkpoint_path,
                                          uint32_t progress_interval,
                                          uint32_t checkpoint_interval, int verbose,
                                          uint64_t max_work, uint64_t *order,
                                          ca_stats *st, ca_ec_count_progress *progress)
{
    if (!order) return CA_ERR_INVALID;
    ca_group g;
    ca_status rc = ca_group_ec_init(&g, p, a, b, 0);
    if (rc != CA_OK) return rc;
    ec_count_checkpoint s = {0};
    memcpy(s.magic, "CAECORD1", 8);
    s.version = 1; s.p = p; s.a = a; s.b = b;
    s.phase = p < 2000 ? EC_COUNT_SMALL : EC_COUNT_ORIGINAL;
    s.small_count = 1;
    if (p >= 2000) ca_rng_seed(&s.rng, 0x5eed5eedULL ^ p);
    double t0 = ca_now();
    int loaded = ec_count_checkpoint_load(checkpoint_path, p, a, b, &s);
    if (loaded < 0) return CA_ERR_INVALID;
    ec_count_runtime run = {0};
    run.state = &s; run.checkpoint_path = checkpoint_path;
    run.start = t0; run.prior = s.seconds;
    run.progress_interval = progress_interval ? progress_interval : 5;
    run.checkpoint_interval = checkpoint_interval ? checkpoint_interval : 60;
    run.next_progress = t0 + run.progress_interval;
    run.next_checkpoint = t0 + run.checkpoint_interval;
    run.verbose = verbose;
    if ((checkpoint_path || verbose) &&
        !ec_count_report(&run, "running", NULL, 0, 0, 0, !loaded))
        return CA_ERR_INTERNAL;
    rc = s.phase == EC_COUNT_FAILED ? CA_ERR_NOT_FOUND : CA_OK;
    if (rc == CA_ERR_NOT_FOUND)
        ca_set_error("ec-order: saved point search ended without a 64-bit order");
    while (s.phase != EC_COUNT_DONE && s.phase != EC_COUNT_FAILED) {
        if (max_work && s.work_units >= max_work) {
            ca_set_error("ec-order: work cap reached; raise --max-work to resume");
            rc = CA_ERR_LIMIT;
            break;
        }
        if (s.phase == EC_COUNT_SMALL) {
            uint64_t x = s.next_x;
            uint64_t rhs = ca_addmod(ca_mulmod(ca_addmod(ca_mulmod(x, x, p), a % p, p), x, p), b % p, p);
            s.small_count += (uint64_t)(1 + ca_legendre(rhs, p));
            s.next_x++; s.work_units++;
            if (s.next_x == p) { s.order = s.small_count; s.phase = EC_COUNT_DONE; }
            double now = ca_now();
            if ((checkpoint_path || verbose) && s.phase != EC_COUNT_DONE &&
                (now >= run.next_progress ||
                 now >= run.next_checkpoint || (max_work && s.work_units >= max_work))) {
                if (!ec_count_report(&run, "running", NULL, s.next_x, p, 0, 1)) {
                    rc = CA_ERR_INTERNAL;
                    break;
                }
                run.next_progress = now + run.progress_interval;
                run.next_checkpoint = now + run.checkpoint_interval;
            }
            continue;
        }
        ca_group active = g;
        if (s.phase == EC_COUNT_TWIST) {
            uint64_t d = 2;
            while (ca_legendre(d, p) != -1) d++;
            uint64_t d2 = ca_mulmod(d, d, p), d3 = ca_mulmod(d2, d, p);
            rc = ca_group_ec_init(&active, p, ca_mulmod(a, d2, p), ca_mulmod(b, d3, p), 0);
            if (rc != CA_OK) break;
        }
        uint64_t sq = ca_isqrt(p);
        while ((ca_u128)sq * sq < p) sq++;
        ca_u128 lo128 = (ca_u128)p + 1 - 2 * (ca_u128)sq;
        uint64_t lo = lo128 < 1 ? 1 : (uint64_t)lo128;
        uint64_t width = 4 * sq + 1;
        if (width - 1 > UINT64_MAX - lo) width = UINT64_MAX - lo + 1;
        uint64_t *cur = malloc(EC_COUNT_CAP * sizeof(*cur));
        if (!cur) { rc = CA_ERR_NOMEM; break; }
        ca_rng next_rng = s.rng;
        ca_elem P, T;
        uint64_t point_seed = ca_rng_next(&next_rng);
        ca_ec_random_point(&active, &P, point_seed ? point_seed : 1);
        ec_identity(&active, &T);
        ca_stats trial = {0};
        ec_count_watch watch = {ec_count_watch_report, &run, 0};
        size_t n = ec_interval_all(&active, &P, &T, lo, width, cur,
                                    EC_COUNT_CAP, &trial, &watch);
        if (watch.failed) {
            free(cur);
            rc = watch.failed == 2 ? CA_ERR_NOMEM : CA_ERR_INTERNAL;
            break;
        }
        s.rng = next_rng; s.tries++;
        s.group_ops += trial.group_ops;
        s.work_units += trial.group_ops;
        if (n && n <= EC_COUNT_CAP) {
            if (!s.have) {
                memcpy(s.candidates, cur, n * sizeof(*cur));
                s.ncand = (uint32_t)n; s.have = 1;
            } else {
                uint32_t kept = 0;
                for (uint32_t i = 0; i < s.ncand; i++)
                    for (size_t j = 0; j < n; j++)
                        if (s.candidates[i] == cur[j]) {
                            s.candidates[kept++] = s.candidates[i];
                            break;
                        }
                s.ncand = kept;
            }
        }
        free(cur);
        if (s.have && s.ncand == 0) { rc = CA_ERR_INTERNAL; break; }
        if (s.ncand == 1) {
            if (s.phase == EC_COUNT_ORIGINAL) {
                s.order = s.candidates[0]; s.phase = EC_COUNT_DONE;
            } else {
                ca_u128 result = (ca_u128)2 * p + 2 - s.candidates[0];
                if (result <= UINT64_MAX) {
                    s.order = (uint64_t)result; s.phase = EC_COUNT_DONE;
                } else {
                    ca_set_error("ec-order: curve order exceeds 64 bits");
                    rc = CA_ERR_NOT_FOUND;
                }
            }
        } else if (s.tries == 24) {
            if (s.phase == EC_COUNT_ORIGINAL && s.have && s.ncand > 1) {
                s.phase = EC_COUNT_TWIST; s.tries = s.have = s.ncand = 0;
                ca_rng_seed(&s.rng, 0x7715ULL ^ p);
            } else {
                ca_set_error("ec-order: completed point trials without a unique order");
                rc = CA_ERR_NOT_FOUND;
            }
        }
        if (rc == CA_ERR_NOT_FOUND) s.phase = EC_COUNT_FAILED;
        if ((checkpoint_path || verbose) && s.phase != EC_COUNT_DONE &&
            !ec_count_report(&run, rc == CA_OK ? "running" : "stopped",
                             NULL, s.tries, 24, 0, 1)) {
            rc = CA_ERR_INTERNAL;
            break;
        }
        if (rc != CA_OK) break;
    }
    if ((checkpoint_path || verbose) &&
        !ec_count_report(&run, rc == CA_OK ? "complete" : "stopped",
                         NULL, s.phase == EC_COUNT_SMALL ? s.next_x : s.tries,
                         s.phase == EC_COUNT_SMALL ? p : 24, 0,
                         rc == CA_OK || rc == CA_ERR_LIMIT || rc == CA_ERR_NOT_FOUND))
        rc = CA_ERR_INTERNAL;
    if (rc == CA_OK) *order = s.order;
    double elapsed = run.prior + ca_now() - t0;
    if (st) { st->group_ops += s.group_ops; st->seconds += elapsed; }
    ec_count_fill_progress(&s, progress, elapsed);
    return rc;
}
