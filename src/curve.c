/*
 * curve.c - curve-aware dispatch and the GLV endomorphism-accelerated rho.
 *
 * ca_curve_detect / ca_curve_group recognise the two prime-field families
 * with an efficiently computable endomorphism psi(P) = lambda * P:
 *
 *   j = 0     (a = 0, p = 1 mod 3):  psi(x, y) = (beta x, -y), <psi> order 6
 *   j = 1728  (b = 0, p = 1 mod 4):  psi(x, y) = (-x, i y),    <psi> order 4
 *
 * beta is a cube root of unity mod p, i a square root of -1 mod p; lambda is
 * the matching root of unity mod the subgroup order (picked by testing
 * psi(P) == lambda * P on a subgroup point, so the sign branch cannot be
 * wrong).  glv_rho_solve then folds the Pollard rho walk by <psi>: it walks
 * canonical representatives of the automorphism classes, which shrinks the
 * search space by the class size m and the operation count by sqrt(m).
 */
#include "cryptanalysis/ca_curve.h"
#include "cryptanalysis/ca_rho.h"
#include "curve_internal.h"
#include "dlog_internal.h"
#include "dlog_checkpoint_internal.h"
#include "ec_tau_internal.h"

#include <math.h>
#include <inttypes.h>

#define GLV_MAX_WALKS 4096

static int glv_ilog2(uint64_t v)
{
    int l = -1;
    while (v) {
        v >>= 1;
        l++;
    }
    return l;
}

/* nontrivial cube root of unity mod p (p = 1 mod 3) */
static uint64_t cube_root_unity(uint64_t p)
{
    uint64_t e = (p - 1) / 3;
    for (uint64_t base = 2; base < p; base++) {
        uint64_t w = ca_powmod(base, e, p);
        if (w != 1) return w;
    }
    return 1;
}

/* Enable the endomorphism on an already-initialised EC group `g` (order set)
 * and fill *info.  Falls back to the negation-only structure when the curve
 * is generic or the subgroup order is incompatible. */
static void curve_enable(ca_group *g, ca_curve_info *info)
{
    memset(info, 0, sizeof(*info));
    g->endo_kind = 0;
    g->aut_order = 0;
    g->endo_lambda = 0;
    g->endo_c_mont = 0;
    info->endo = CA_CURVE_ENDO_NONE;
    info->aut_order = 2; /* the negation map is always available on a curve */
    info->rho_speedup = sqrt(2.0);

    uint64_t p = g->p;
    int kind = 0;
    if (g->a == 0 && g->b != 0 && p % 3 == 1)
        kind = CA_CURVE_ENDO_J0;
    else if (g->b == 0 && g->a != 0 && p % 4 == 1)
        kind = CA_CURVE_ENDO_J1728;
    if (kind == 0) return;

    uint64_t c;
    if (kind == CA_CURVE_ENDO_J0)
        c = cube_root_unity(p);
    else if (!ca_sqrtmod_prime(p - 1, p, &c))
        return;
    info->beta = c;
    uint32_t m = (kind == CA_CURVE_ENDO_J0) ? 6u : 4u;
    info->endo = (ca_curve_endo)kind;
    info->aut_order = m;
    info->rho_speedup = sqrt((double)m);

    uint64_t n = g->order;
    if (n == 0) return; /* structure only; no lambda without an order */
    if ((kind == CA_CURVE_ENDO_J0 && n % 3 != 1) || (kind == CA_CURVE_ENDO_J1728 && n % 4 != 1)) {
        info->endo = CA_CURVE_ENDO_NONE;
        info->beta = 0;
        info->aut_order = 2;
        info->rho_speedup = sqrt(2.0);
        return;
    }

    /* Point the group's endomorphism at psi so ca_ec_endo can apply it. */
    g->endo_kind = (uint32_t)kind;
    g->aut_order = m;
    g->endo_c_mont = ca_mont_to(&g->mont, c);

    /* A subgroup point to fix the eigenvalue on: cofactor * random point. */
    if (g->cofactor == 0) {
        uint64_t full;
        if (ca_ec_count_points(p, g->a, g->b, &full, NULL) != CA_OK || full % n != 0) {
            g->endo_kind = 0;
            g->aut_order = 0;
            info->endo = CA_CURVE_ENDO_NONE;
            info->beta = 0;
            info->aut_order = 2;
            info->rho_speedup = sqrt(2.0);
            return;
        }
        g->cofactor = full / n;
    }
    ca_elem P;
    if (ca_group_find_generator(g, &P, 1) != CA_OK) {
        g->endo_kind = 0;
        g->aut_order = 0;
        info->endo = CA_CURVE_ENDO_NONE;
        info->beta = 0;
        info->aut_order = 2;
        info->rho_speedup = sqrt(2.0);
        return;
    }
    ca_elem psiP;
    ca_ec_endo(g, &psiP, &P);

    /* Candidate eigenvalues: roots of x^2 - x + 1 (j0) or x^2 + 1 (j1728). */
    uint64_t cand[2];
    int nc = 0;
    if (kind == CA_CURVE_ENDO_J0) {
        uint64_t s;
        if (ca_sqrtmod_prime(n - 3, n, &s)) {
            uint64_t inv2 = ca_invmod(2, n);
            cand[nc++] = ca_mulmod(ca_addmod(1 % n, s, n), inv2, n);
            cand[nc++] = ca_mulmod(ca_submod(1 % n, s, n), inv2, n);
        }
    } else {
        uint64_t s;
        if (ca_sqrtmod_prime(n - 1, n, &s)) {
            cand[nc++] = s;
            cand[nc++] = n - s;
        }
    }
    for (int k = 0; k < nc; k++) {
        if (cand[k] <= 1) continue;
        ca_elem Q;
        ca_group_mul(g, &Q, &P, cand[k], NULL);
        if (ca_group_equal(g, &Q, &psiP)) {
            g->endo_lambda = cand[k];
            break;
        }
    }
    if (g->endo_lambda == 0) {
        g->endo_kind = 0;
        g->aut_order = 0;
        info->endo = CA_CURVE_ENDO_NONE;
        info->beta = 0;
        info->aut_order = 2;
        info->rho_speedup = sqrt(2.0);
        return;
    }
    info->lambda = g->endo_lambda;
}

ca_status ca_curve_detect(uint64_t p, uint64_t a, uint64_t b, uint64_t order, ca_curve_info *out)
{
    ca_group g;
    ca_status rc = ca_group_ec_init(&g, p, a, b, order);
    if (rc != CA_OK) return rc;
    ca_curve_info info;
    curve_enable(&g, &info);
    if (out) *out = info;
    return CA_OK;
}

/* ---- named registry --------------------------------------------------- */

typedef struct curve_entry {
    const char *name;
    uint64_t p, a, b, order;
} curve_entry;

/* Example curves with a large prime-order subgroup of the right congruence,
 * one small (for tests) and one ~2^32 (for benchmarks) per family, plus a
 * generic curve that has only the negation map. */
static const curve_entry CURVES[] = {
    {"glv-j0-26", 67108933, 0, 7, 16773703},
    {"glv-j1728-26", 67108933, 6, 0, 6712457},
    {"glv-j0-32", 4294967377, 0, 15, 23729779},
    {"glv-j1728-32", 4294967377, 3, 0, 37025581},
    {"generic-26", 67108879, 2, 3, 3355777},
    /* Open instances from challenges/elliptic.  Subgroup orders stay at most
     * ~2^16 so `ca_bench glv` (20 rho walks per name) finishes with the
     * existing curves.  Larger rows live in challenges/elliptic/c_registry.txt. */
    {"pf-anomalous-b9", 757, 537, 465, 757},
    {"pf-generic-b7", 191, 139, 97, 31},
    {"pf-ssj0-b7", 227, 0, 1, 228},
    {"pf-ssj1728-b7", 227, 1, 0, 228},
    {"pf-mov-b15", 41609, 0, 1, 41610},
    {"pf-twist-smooth-b19", 778579, 603144, 500010, 97},
    {"pf-j0-twist-b27", 161882863, 0, 27, 433},
    {"volcano-l2-h3-p73-d3-floor", 73, 37, 49, 80},
};

ca_status ca_curve_by_name(const char *name, uint64_t *p, uint64_t *a, uint64_t *b, uint64_t *order)
{
    for (size_t i = 0; i < sizeof(CURVES) / sizeof(CURVES[0]); i++) {
        if (strcmp(name, CURVES[i].name) == 0) {
            if (p) *p = CURVES[i].p;
            if (a) *a = CURVES[i].a;
            if (b) *b = CURVES[i].b;
            if (order) *order = CURVES[i].order;
            return CA_OK;
        }
    }
    ca_set_error("unknown curve name '%s'", name);
    return CA_ERR_NOT_FOUND;
}

size_t ca_curve_list(const char **names, size_t cap)
{
    size_t n = sizeof(CURVES) / sizeof(CURVES[0]);
    for (size_t i = 0; i < n && i < cap; i++) names[i] = CURVES[i].name;
    return n;
}

ca_status ca_curve_group(ca_group *g, uint64_t p, uint64_t a, uint64_t b, uint64_t order,
                         ca_curve_info *info)
{
    ca_status rc = ca_group_ec_init(g, p, a, b, order);
    if (rc != CA_OK) return rc;
    /* Resolve the cofactor so find_generator (and thus every solver) works on
     * the requested subgroup, for generic and CM curves alike. */
    if (order) {
        uint64_t full;
        if (ca_ec_count_points(p, a, b, &full, NULL) == CA_OK && full % order == 0)
            g->cofactor = full / order;
    }
    ca_curve_info local;
    curve_enable(g, &local);
    if (info) *info = local;
    return CA_OK;
}

/* ---- GLV endomorphism-accelerated rho --------------------------------- */

uint32_t ca_ec_j0_coord_canonicalize(const ca_group *g, ca_elem *Y)
{
    if (!g || !Y || g->endo_kind != 1 || g->aut_order != 6 || Y->w[2]) return 0;
    /* In the sixfold j=0 orbit, x takes three beta rotations and y
     * takes two signs.  Choose the minimum encoded coordinate in each
     * orbit independently.  Montgomery encoding is a bijection, so this
     * gives one deterministic point per orbit without six point hashes. */
    uint64_t xs[3];
    xs[0] = Y->w[0];
    xs[1] = ca_mont_mul(&g->mont, xs[0], g->endo_c_mont);
    xs[2] = ca_mont_mul(&g->mont, xs[1], g->endo_c_mont);
    uint32_t x_power = 0;
    if (xs[1] < xs[x_power]) x_power = 1;
    if (xs[2] < xs[x_power]) x_power = 2;
    uint64_t neg_y = Y->w[1] ? g->p - Y->w[1] : 0;
    uint32_t negate = neg_y < Y->w[1];
    Y->w[0] = xs[x_power];
    if (negate) Y->w[1] = neg_y;
    /* psi^k applies beta^(k mod 3) to x and (-1)^k to y. */
    return ((x_power & 1u) == negate) ? x_power : x_power + 3;
}

/* Reduce Y to the canonical representative of its automorphism class {Y,
 * psi(Y), ..., psi^{m-1}(Y)} and return the power k of psi applied. */
static uint32_t glv_class_reduce(const ca_group *g, ca_elem *Y, uint32_t m)
{
#ifdef CA_RHO_J0_COORDINATE_ORBIT
    if (g->endo_kind == CA_CURVE_ENDO_J0 && m == 6)
        return ca_j0_coordinate_class_reduce(g, Y);
#elif defined(CA_RHO_J0_FACTORED_HASH)
    if (g->endo_kind == CA_CURVE_ENDO_J0 && m == 6)
        return ca_j0_factored_hash_class_reduce(g, Y);
#endif

#ifdef CA_J0_RHO_COORD_CANON
    if (g->endo_kind == 1 && m == 6) return ca_ec_j0_coord_canonicalize(g, Y);
#endif
    ca_elem cur = *Y, best = *Y;
    uint64_t best_h = ca_group_hash(g, Y);
    uint32_t best_k = 0;
    for (uint32_t k = 1; k < m; k++) {
        ca_elem nx;
        ca_ec_endo(g, &nx, &cur);
        cur = nx;
        uint64_t h = ca_group_hash(g, &cur);
        if (h < best_h) {
            best_h = h;
            best = cur;
            best_k = k;
        }
    }
    *Y = best;
    return best_k;
}

static int glv_recover(const ca_group *g, const ca_elem *base, const ca_elem *target, uint64_t n,
                       uint64_t a1, uint64_t b1, uint64_t a2, uint64_t b2, uint64_t *x)
{
    uint64_t c = ca_submod(b1, b2, n);
    uint64_t d = ca_submod(a2, a1, n);
    if (c == 0) return 0;
    uint64_t gg = ca_gcd(c, n);
    if (d % gg) return 0;
    uint64_t nn = n / gg;
    uint64_t x0 = ca_mulmod((d / gg) % nn, ca_invmod((c / gg) % nn, nn), nn);
    uint64_t reps = gg > 65536 ? 65536 : gg;
    for (uint64_t k = 0; k < reps; k++) {
        uint64_t cand = x0 + k * nn;
        if (cand >= n) break;
        if (ca_verify_log(g, base, target, cand)) {
            *x = cand;
            return 1;
        }
    }
    return 0;
}

#ifdef CA_GLV_TRACE
#    include <stdio.h>
#    include <stdlib.h>
#    include <assert.h>
#    include "glv_trace_accounting.h"
#    define GLV_RING 64
/* Where glv_rho_solve's group operations go, written as one JSON line per
 * solve to $CA_GLV_TRACE_FILE.  Diagnostic builds only (-DCA_GLV_TRACE); the
 * walk itself is unchanged. */
typedef struct glv_trace {
    uint64_t table_ops, start_ops, restart_ops, step_ops;
    uint64_t useful_steps, retry_steps, iterations;
    uint64_t dps, coll_total, coll_same_ab, coll_recover_fail;
    uint64_t abandons, abandon_wasted, abandon_cycle, abandon_nocycle;
    uint64_t cycle_len[GLV_RING + 1];
    uint64_t cycle2_same_idx, cycle2_after_retry; /* 2-cycles whose two steps used one multiplier;
                                                     of those, entered through a retry */
    uint64_t escape2, escape4; /* cycles left by the deterministic escape (CA_GLV_CYCLE_ESCAPE) */
} glv_trace;
#endif

typedef struct glv_walk {
    ca_elem Y;
    uint64_t a, b;
    uint64_t since_dp;
#ifdef CA_GLV_TRACE
    uint64_t trace_wasted_since_dp;
#endif
    uint32_t idx;
    uint32_t first; /* the multiplier Y's own hash selects (a function of Y alone) */
    uint32_t tries; /* look-ahead advances taken from this Y */
    uint8_t retry;
#ifdef CA_GLV_CYCLE_ESCAPE
    /* the last four committed points, newest first, for 2- and 4-cycle detection */
    ca_elem hY[4];
    uint64_t ha[4], hb[4], hh[4];
    uint32_t hn;
#    ifdef CA_GLV_BATCH_ESCAPE
    /* set while the walk's next batched slot doubles Y (a, b already those of
     * the cycle member Y) instead of adding a multiplier */
    uint8_t esc;
#    endif
#endif
#ifdef CA_GLV_TRACE
    uint64_t ring[GLV_RING];
    uint32_t ring_idx[GLV_RING];
    uint8_t ring_retry[GLV_RING];
    uint32_t ring_pos;
    uint8_t retried;
#endif
} glv_walk;

/* base/target and the multiplier table travel with the walk in this context
 * rather than in each glv_walk. */
typedef struct glv_ctx {
    const ca_group *g;
    ca_elem base, target;
    uint32_t r;
    ca_elem *M;
    uint64_t *alpha, *beta;
    uint32_t m;
    uint64_t lam_pow[6];
    int dp_bits;
    uint64_t dp_mask;
    uint64_t abandon;
    const ca_tau4_joint_precomp *joint_pre;
    const ca_tau4_joint_plane_precomp *joint_plane;
    int free_gauge;
    int tau_pair_steered;
    ca_curve_startup_stats *startup;
} glv_ctx;

/* A native snapshot includes the exact lane state. The size fields reject
 * snapshots made with a different diagnostic or cycle-escape build. */
typedef struct glv_checkpoint_header {
    char magic[8];
    uint64_t p, a, b, order, cofactor, endo_lambda, endo_c_mont;
    uint64_t base[4], target[4];
    uint32_t kind, endo_kind, aut_order, r, walks, dp_bits;
    uint32_t walk_size, entry_size, walk_flags;
    uint64_t seed, rng[4], ops, steps, entries, result;
    double elapsed_seconds;
    uint32_t solved;
    uint64_t checksum;
} glv_checkpoint_header;

static void glv_checkpoint_identity(glv_checkpoint_header *h, const glv_ctx *c,
                                    uint32_t walks)
{
    const ca_group *g = c->g;
    memset(h, 0, sizeof(*h));
    memcpy(h->magic, "CAGLV001", 8);
    h->p = g->p; h->a = g->a; h->b = g->b; h->order = g->order;
    h->cofactor = g->cofactor; h->endo_lambda = g->endo_lambda;
    h->endo_c_mont = g->endo_c_mont;
    ca_group_decode(g, h->base, &c->base);
    ca_group_decode(g, h->target, &c->target);
    h->kind = g->kind; h->endo_kind = g->endo_kind;
    h->aut_order = g->aut_order; h->r = c->r; h->walks = walks;
    h->dp_bits = (uint32_t)c->dp_bits;
    h->walk_size = sizeof(glv_walk); h->entry_size = sizeof(ca_htab_entry);
#ifdef CA_GLV_LOOKAHEAD_LEGACY
    h->walk_flags |= 1;
#endif
#ifdef CA_GLV_CYCLE_ESCAPE
    h->walk_flags |= 2;
#endif
#ifdef CA_GLV_TRACE
    h->walk_flags |= 4;
#endif
#ifdef CA_GLV_BATCH_ESCAPE
    h->walk_flags |= 8;
#endif
}

static int glv_checkpoint_same_run(const glv_checkpoint_header *a,
                                    const glv_checkpoint_header *b)
{
    return memcmp(a->magic, b->magic, 8) == 0 && a->p == b->p &&
           a->a == b->a && a->b == b->b && a->order == b->order &&
           a->cofactor == b->cofactor && a->endo_lambda == b->endo_lambda &&
           a->endo_c_mont == b->endo_c_mont &&
           memcmp(a->base, b->base, sizeof(a->base)) == 0 &&
           memcmp(a->target, b->target, sizeof(a->target)) == 0 &&
           a->kind == b->kind && a->endo_kind == b->endo_kind &&
           a->aut_order == b->aut_order && a->r == b->r &&
           a->walks == b->walks && a->dp_bits == b->dp_bits &&
           a->walk_size == b->walk_size && a->entry_size == b->entry_size &&
           a->walk_flags == b->walk_flags;
}

static int glv_checkpoint_probe(const char *path, const glv_checkpoint_header *identity,
                                 uint64_t requested_seed, glv_checkpoint_header *saved)
{
    if (!path) return 0;
    FILE *f = fopen(path, "rb");
    if (!f) {
        if (errno == ENOENT) return 0;
        ca_set_error("glv: cannot open checkpoint");
        return -1;
    }
    int ok = fread(saved, 1, sizeof(*saved), f) == sizeof(*saved) &&
             glv_checkpoint_same_run(saved, identity) && saved->seed &&
             (!requested_seed || requested_seed == saved->seed) &&
             saved->entries <= SIZE_MAX / sizeof(ca_htab_entry) &&
             saved->elapsed_seconds >= 0;
    fclose(f);
    if (!ok) ca_set_error("glv: checkpoint identity, format or seed does not match");
    return ok ? 1 : -1;
}

static int glv_checkpoint_load(const char *path, const glv_checkpoint_header *expected,
                                glv_walk *walks, ca_htab *tab, ca_rng *rng,
                                uint64_t *ops, uint64_t *steps, double *elapsed,
                                uint64_t *result, int *solved, const glv_ctx *c)
{
    FILE *f = fopen(path, "rb");
    if (!f) { ca_set_error("glv: cannot reopen checkpoint"); return 0; }
    glv_checkpoint_header h = {0};
    int ok = fread(&h, 1, sizeof(h), f) == sizeof(h) &&
             /* Both headers are raw fread() bytes of the same file, including padding. */
             // NOLINTNEXTLINE(bugprone-suspicious-memory-comparison,cert-exp42-c,cert-flp37-c)
             memcmp(&h, expected, sizeof(h)) == 0;
    uint64_t checksum = h.checksum;
    h.checksum = 0;
    uint64_t hash = dlog_ckpt_hash(&h, sizeof(h), UINT64_C(14695981039346656037));
    size_t lanes_bytes = (size_t)h.walks * sizeof(glv_walk);
    if (ok) ok = fread(walks, 1, lanes_bytes, f) == lanes_bytes;
    if (ok) hash = dlog_ckpt_hash(walks, lanes_bytes, hash);
    for (uint64_t i = 0; ok && i < h.entries; i++) {
        ca_htab_entry e;
        ok = fread(&e, 1, sizeof(e), f) == sizeof(e);
        if (ok) {
            hash = dlog_ckpt_hash(&e, sizeof(e), hash);
            ok = e.key && e.v0 < c->g->order && e.v1 < c->g->order &&
                 ca_htab_insert(tab, e.key, e.v0, e.v1, NULL, NULL) == 0;
        }
    }
    if (ok) ok = fgetc(f) == EOF && hash == checksum && tab->count == h.entries;
    fclose(f);
    for (uint32_t i = 0; ok && i < h.walks; i++)
        ok = walks[i].a < c->g->order && walks[i].b < c->g->order &&
             walks[i].idx < c->r && walks[i].first < c->r &&
             walks[i].tries < c->r && walks[i].retry <= 1;
    if (ok && h.solved)
        ok = ca_verify_log(c->g, &c->base, &c->target, h.result);
    if (!ok) { ca_set_error("glv: checkpoint is damaged or incompatible"); return 0; }
    memcpy(rng->s, h.rng, sizeof(h.rng));
    *ops = h.ops; *steps = h.steps; *elapsed = h.elapsed_seconds;
    *result = h.result;
    *solved = h.solved != 0;
    return 1;
}

static int glv_checkpoint_save(const char *path, const glv_checkpoint_header *identity,
                                const glv_walk *walks, const ca_htab *tab,
                                const ca_rng *rng, uint64_t seed, uint64_t ops,
                                uint64_t steps, double elapsed, uint64_t result, int solved)
{
    if (!path) return 1;
    dlog_ckpt_file w;
    if (!dlog_ckpt_begin(&w, path)) {
        ca_set_error("glv: cannot create checkpoint"); return 0;
    }
    glv_checkpoint_header h = *identity;
    h.seed = seed; memcpy(h.rng, rng->s, sizeof(h.rng));
    h.ops = ops; h.steps = steps; h.entries = tab->count;
    h.elapsed_seconds = elapsed; h.result = result; h.solved = solved;
    size_t lanes_bytes = (size_t)h.walks * sizeof(glv_walk);
    uint64_t hash = dlog_ckpt_hash(&h, sizeof(h), UINT64_C(14695981039346656037));
    int ok = fwrite(&h, 1, sizeof(h), w.f) == sizeof(h) &&
             fwrite(walks, 1, lanes_bytes, w.f) == lanes_bytes;
    hash = dlog_ckpt_hash(walks, lanes_bytes, hash);
    for (size_t i = 0; ok && i < tab->cap; i++) {
        const ca_htab_entry *e = &tab->e[i];
        if (!e->key) continue;
        hash = dlog_ckpt_hash(e, sizeof(*e), hash);
        ok = fwrite(e, 1, sizeof(*e), w.f) == sizeof(*e);
    }
    if (ok) {
        h.checksum = hash;
        ok = fseek(w.f, 0, SEEK_SET) == 0 && fwrite(&h, 1, sizeof(h), w.f) == sizeof(h);
    }
    ok = dlog_ckpt_finish(&w, ok);
    if (!ok) ca_set_error("glv: cannot persist checkpoint");
    return ok;
}

static uint64_t glv_generic_mul_budget(uint64_t scalar)
{
    uint64_t ops = 0;
    while (scalar) {
        ops += scalar & 1;
        scalar >>= 1;
        ops += scalar != 0;
    }
    return ops;
}

/* Audit the exact affine startup points in table order and restart order.
 * These fields are diagnostic fingerprints, not cryptographic hashes. */
static void glv_record_startup_point(ca_curve_startup_stats *startup,
                                      const ca_elem *point)
{
    if (!startup) return;
    uint64_t index = ++startup->startup_point_count;
    uint64_t left = ca_mix64(UINT64_C(0x55958df12b04e7c3) ^ index ^ point->w[0]);
    left = ca_mix64(left ^ ca_mix64(point->w[1]) ^ point->w[2]);
    uint64_t right = ca_mix64(UINT64_C(0xa34c6f1075e2d9b8) ^
                              (index << 1) ^ point->w[1]);
    right = ca_mix64(right ^ ca_mix64(point->w[0]) ^ point->w[2]);
    startup->startup_point_digest_lo = ca_mix64(startup->startup_point_digest_lo ^ left);
    startup->startup_point_digest_hi = ca_mix64(startup->startup_point_digest_hi ^ right);
}

static void glv_account_tau_startup(ca_curve_startup_stats *startup,
                                     const ca_tau4_joint_counts *one)
{
    startup->eval_tau += one->tau_steps;
    startup->eval_mixed_adds += one->mixed_adds;
    startup->eval_rotations += one->rotations;
    startup->eval_inversions += one->inversions;
    startup->eval_recode_attempts += one->recode_attempts;
    startup->eval_pair_scores += one->pair_scores;
    startup->eval_lattice_points_checked += one->lattice_points_checked;
    startup->eval_free_gauge_transitions += one->free_gauge_transitions;
    startup->eval_tau_pairs += one->tau_pairs;
    startup->eval_tau_pair_cheap_z += one->tau_pair_cheap_z;
    startup->eval_gauge_table_lookups += one->gauge_table_lookups;
}

static int glv_startup_combination(const glv_ctx *c, ca_elem *out,
                                   uint64_t a, uint64_t b, int restart, uint64_t *ops)
{
    uint64_t before = *ops;
    double start = c->startup ? ca_now() : 0.0;
    if (c->joint_pre) {
        ca_tau4_joint_counts one = {0};
        int ok = c->joint_plane
            ? ca_ec_tau4_paired_two_plane_mul_profile(c->g, c->joint_plane,
                                                        out, a, b, &one)
            : c->tau_pair_steered
            ? ca_ec_tau4_paired_two_free_gauge_tau_pair_steered_mul_profile(
                c->g, c->joint_pre, out, a, b, &one)
            : c->free_gauge
            ? ca_ec_tau4_paired_two_free_gauge_mul_profile(c->g, c->joint_pre,
                                                            out, a, b, &one)
            : ca_ec_tau4_paired_two_mul_profile(c->g, c->joint_pre,
                                                 out, a, b, &one);
        if (!ok)
            return 0;
        *ops += glv_generic_mul_budget(a) + glv_generic_mul_budget(b) + 1;
        if (c->startup) {
            glv_account_tau_startup(c->startup, &one);
            if (restart) c->startup->restart_output_inversions += one.inversions;
            else c->startup->table_output_inversions += one.inversions;
        }
    } else {
        ca_elem t1, t2;
        ca_group_mul(c->g, &t1, &c->base, a, ops);
        ca_group_mul(c->g, &t2, &c->target, b, ops);
        ca_group_op(c->g, out, &t1, &t2);
        (*ops)++;
    }
    glv_record_startup_point(c->startup, out);
    if (c->startup) {
        c->startup->evaluation_seconds += ca_now() - start;
        c->startup->budget_equivalent_group_ops += *ops - before;
        if (restart) c->startup->restart_evaluations++;
        else c->startup->table_evaluations++;
    }
    return 1;
}

static int glv_restart(const glv_ctx *c, glv_walk *w, ca_rng *rng, uint64_t *ops)
{
    const ca_group *g = c->g;
#ifdef CA_GLV_FIELD_COUNT
    const uint32_t fc_saved_phase = ca_fc_phase;
    if (fc_saved_phase != CA_FC_SETUP) {
        ca_fc_phase = CA_FC_RESTART;
        ca_fc_ev[CA_FC_EV_RESTARTS]++;
    }
#endif
    uint64_t n = g->order;
    w->a = ca_rng_below(rng, n);
    w->b = ca_rng_below(rng, n);
    if (!glv_startup_combination(c, &w->Y, w->a, w->b, 1, ops)) return 0;
    uint32_t k = glv_class_reduce(g, &w->Y, c->m);
    if (k) {
        w->a = ca_mulmod(w->a, c->lam_pow[k], n);
        w->b = ca_mulmod(w->b, c->lam_pow[k], n);
    }
    w->since_dp = 0;
#ifdef CA_GLV_TRACE
    ca_glv_trace_reset_since_dp(&w->trace_wasted_since_dp);
#endif
    w->retry = 0;
#ifdef CA_GLV_CYCLE_ESCAPE
    w->hn = 0;
#    ifdef CA_GLV_BATCH_ESCAPE
    w->esc = 0;
#    endif
#endif
#ifdef CA_GLV_FIELD_COUNT
    ca_fc_phase = fc_saved_phase;
#endif
    return 1;
}

static ca_status glv_rho_solve(const ca_group *g, const ca_elem *base, const ca_elem *target,
                               uint64_t seed, uint64_t *x, ca_stats *st,
                               int paired2, int batch_table, int plane_format,
                               int free_gauge, int tau_pair_steered,
                               ca_curve_startup_stats *startup,
                               const char *checkpoint_path, uint32_t progress_interval,
                               uint32_t checkpoint_interval, int verbose,
                               uint64_t max_ops)
{
    double t0 = ca_now();
    uint64_t n = g->order;
    if (ca_group_is_identity(g, target)) {
        *x = 0;
        return CA_OK;
    }
    if (n < 64) {
        ca_elem cur;
        ca_group_identity(g, &cur);
        for (uint64_t k = 0; k < n; k++) {
            if (ca_group_equal(g, &cur, target)) {
                *x = k;
                if (st) st->group_ops += k;
                return CA_OK;
            }
            ca_group_op(g, &cur, &cur, base);
        }
        return CA_ERR_NOT_FOUND;
    }

    glv_ctx c;
    memset(&c, 0, sizeof(c));
#ifdef CA_GLV_FIELD_COUNT
    ca_fc_phase = CA_FC_SETUP;
#endif
    c.g = g;
    c.base = *base;
    c.target = *target;
    c.startup = startup;
    c.free_gauge = free_gauge;
    c.tau_pair_steered = tau_pair_steered;
    c.m = g->aut_order;
    c.lam_pow[0] = 1 % n;
    for (uint32_t k = 1; k < c.m; k++)
        c.lam_pow[k] = ca_mulmod(c.lam_pow[k - 1], g->endo_lambda, n);
    ca_tau4_joint_plane_precomp plane_pre;
    if (paired2) {
        ca_tau4_joint_counts prep = {0};
        double prepare_start = ca_now();
        int ok = plane_format
            ? ca_ec_tau4_joint_plane_prepare(g, base, target, &plane_pre, &prep)
            : ca_ec_tau4_joint_prepare(g, base, target, &plane_pre.base, &prep);
        if (!ok)
            return CA_ERR_INTERNAL;
        c.joint_pre = &plane_pre.base;
        c.joint_plane = plane_format ? &plane_pre : NULL;
        if (startup) {
            startup->prepare_tau = prep.tau_steps;
            startup->prepare_doubles = prep.doubles;
            startup->prepare_mixed_adds = prep.mixed_adds;
            startup->prepare_inversions = prep.inversions;
            startup->prepare_rotations = prep.rotations;
            startup->prepare_bytes = plane_format ? sizeof(plane_pre) : sizeof(plane_pre.base);
            startup->prepare_seconds = ca_now() - prepare_start;
        }
    }

    /* The folded search space has size n/m, so all budgets scale with
     * sqrt(n/m).  Keep the r-multiplier table and the W walk start-ups (each
     * about 3 log2(n) operations) to a small fraction of it, exactly as rho
     * does, so that the setup never dominates on small groups.  The table
     * grows sooner than the walk budget: a small table makes walks fall into
     * fruitless cycles and retry the look-ahead far more often, which costs
     * more than the extra table entries from about 28 bits up
     * (experiments/glv-table-rule-20261022).  The cap is 32 below 40 bits and
     * 128 from 40 bits up: a 128-entry table saved group operations from 40
     * bits (experiments/glv-cap-selection-20261105) and was worse at 34-36 bits
     * (experiments/glv-table-confirm-34-41-20261104). */
    uint64_t sqrt_nm = ca_isqrt(n / c.m) + 1;
    int lg = glv_ilog2(n) + 1;
    uint64_t rbudget = sqrt_nm / (12u * (uint64_t)lg);
    uint32_t rcap = lg >= 40 ? 128 : 32;
    uint32_t rr = 8;
    while ((uint64_t)rr * 2 <= rbudget && rr * 2 <= rcap) rr *= 2;
    c.r = rr;
    uint64_t wcap = sqrt_nm / (24u * (uint64_t)lg);
    uint32_t W = wcap < 1 ? 1 : (wcap > GLV_MAX_WALKS ? GLV_MAX_WALKS : (uint32_t)wcap);

    int dp = 0;
    double per_walk = 1.25 * (double)sqrt_nm / (32.0 * (double)W);
    if (per_walk >= 2.0) dp = glv_ilog2((uint64_t)per_walk);
    int min_dp = glv_ilog2(sqrt_nm) - 24;
    if (dp < min_dp) dp = min_dp;
    if (dp < 0) dp = 0;
    if (dp > 48) dp = 48;
    c.dp_bits = dp;
    c.dp_mask = dp ? ((1ULL << dp) - 1) : 0;
    c.abandon = (uint64_t)24 << dp;

    glv_checkpoint_header identity, saved;
    glv_checkpoint_identity(&identity, &c, W);
    int existing = glv_checkpoint_probe(checkpoint_path, &identity, seed, &saved);
    if (existing < 0) return CA_ERR_INTERNAL;
    uint64_t effective_seed = existing ? saved.seed : ca_seed_or_random(seed);
    ca_rng rng;
    ca_rng_seed(&rng, effective_seed);
    uint64_t ops = 0;
    uint64_t steps = 0;
    double elapsed_prior = 0;
    int checkpoint_ready = 0;
#ifdef CA_GLV_TRACE
    glv_trace tr;
    memset(&tr, 0, sizeof(tr));
    uint64_t ops_mark = 0;
    uint64_t trace_prior_ops = 0;
#endif
    c.M = calloc(c.r, sizeof(ca_elem));
    c.alpha = calloc(c.r, sizeof(uint64_t));
    c.beta = calloc(c.r, sizeof(uint64_t));
    uint64_t *scratch = calloc(2 * (size_t)W, sizeof(uint64_t));
    glv_walk *walks = calloc(W, sizeof(glv_walk));
    ca_elem *Yn = calloc(W, sizeof(ca_elem));
    ca_elem *B = calloc(W, sizeof(ca_elem));
    ca_htab tab;
    int have_tab = 0;
    ca_status failure = CA_ERR_NOMEM;
    if (!c.M || !c.alpha || !c.beta || !scratch || !walks || !Yn || !B) goto nomem;
    for (uint32_t i = 0; i < c.r; i++) {
        c.alpha[i] = ca_rng_below(&rng, n);
        c.beta[i] = ca_rng_below(&rng, n);
        if (!batch_table && !glv_startup_combination(&c, &c.M[i],
                                                      c.alpha[i], c.beta[i], 0, &ops)) {
            failure = CA_ERR_INTERNAL;
            goto nomem;
        }
    }
    if (batch_table) {
        ca_tau4_joint_counts batch = {0};
        double batch_start = startup ? ca_now() : 0.0;
        int ok = plane_format
            ? ca_ec_tau4_paired_two_plane_batch_profile(g, c.joint_plane, c.M,
                                                         c.alpha, c.beta, c.r, &batch)
            : tau_pair_steered
            ? ca_ec_tau4_paired_two_free_gauge_tau_pair_steered_batch_profile(
                g, c.joint_pre, c.M, c.alpha, c.beta, c.r, &batch)
            : free_gauge
            ? ca_ec_tau4_paired_two_free_gauge_batch_profile(g, c.joint_pre, c.M,
                                                              c.alpha, c.beta, c.r, &batch)
            : ca_ec_tau4_paired_two_batch_profile(g, c.joint_pre, c.M,
                                                   c.alpha, c.beta, c.r, &batch);
        if (!ok) {
            failure = CA_ERR_INTERNAL;
            goto nomem;
        }
        for (uint32_t i = 0; i < c.r; i++)
            glv_record_startup_point(startup, &c.M[i]);
        for (uint32_t i = 0; i < c.r; i++)
            ops += glv_generic_mul_budget(c.alpha[i]) +
                   glv_generic_mul_budget(c.beta[i]) + 1;
        if (startup) {
            glv_account_tau_startup(startup, &batch);
            startup->table_output_inversions += batch.inversions;
            startup->table_evaluations += c.r;
            startup->table_batch_size = c.r;
            startup->budget_equivalent_group_ops += ops;
            startup->evaluation_seconds += ca_now() - batch_start;
        }
    }
#ifdef CA_GLV_TRACE
    tr.table_ops = ops - ops_mark;
    ops_mark = ops;
#endif
    double exp_dps = 1.25 * (double)sqrt_nm / (double)(1ULL << dp) + 1024;
    if (ca_htab_init(&tab, (size_t)(exp_dps < 1e8 ? exp_dps : 1e8)) != CA_OK) goto nomem;
    have_tab = 1;
    ca_status rc = CA_ERR_NOT_FOUND;
    if (existing) {
        uint64_t prior_ops, result;
        int solved;
        if (!glv_checkpoint_load(checkpoint_path, &saved, walks, &tab, &rng,
                                 &prior_ops, &steps, &elapsed_prior, &result,
                                 &solved, &c)) {
            rc = CA_ERR_INTERNAL;
            goto done;
        }
        ops += prior_ops;
#ifdef CA_GLV_TRACE
        trace_prior_ops = prior_ops;
        ops_mark += prior_ops;
#endif
        checkpoint_ready = 1;
        if (solved) { *x = result; rc = CA_OK; goto done; }
    } else {
        for (uint32_t w = 0; w < W; w++) {
            if (!glv_restart(&c, &walks[w], &rng, &ops)) {
                rc = CA_ERR_INTERNAL;
                goto done;
            }
        }
        checkpoint_ready = 1;
    }
#ifdef CA_GLV_TRACE
    tr.start_ops = ops - ops_mark;
#endif
    uint64_t cap = 64 * sqrt_nm * c.m + (1ULL << 20); /* runaway guard */
    if (max_ops && max_ops < cap) cap = max_ops;
    double next_progress = ca_now() + (progress_interval ? progress_interval : 5);
    double next_checkpoint = ca_now() + (checkpoint_interval ? checkpoint_interval : 60);
    int monitor = checkpoint_path || verbose;
    if (monitor && !dlog_ckpt_progress(checkpoint_path, "glv", "walk", "running",
                           elapsed_prior + ca_now() - t0, ops, steps, tab.count, verbose)) {
        ca_set_error("glv: cannot persist progress"); rc = CA_ERR_INTERNAL; goto done;
    }
    while (ops < cap) {
        for (uint32_t w = 0; w < W; w++) {
            glv_walk *wk = &walks[w];
#ifdef CA_GLV_BATCH_ESCAPE
            if (wk->esc) { /* escaping: the batch doubles the cycle member */
                B[w] = wk->Y;
                Yn[w] = wk->Y;
                continue;
            }
#endif
            if (!wk->retry) {
                wk->idx = (uint32_t)(ca_mix64(ca_group_hash(g, &wk->Y)) % c.r);
                wk->first = wk->idx;
                wk->tries = 0;
            }
            B[w] = c.M[wk->idx];
            Yn[w] = wk->Y;
        }
#ifdef CA_GLV_FIELD_COUNT
        ca_fc_phase = CA_FC_BATCH;
        ca_fc_ev[CA_FC_EV_BATCHES]++;
        ca_fc_ev[CA_FC_EV_BATCH_WALKS] += W;
#endif
        ca_group_batch_op(g, Yn, Yn, B, W, scratch);
#ifdef CA_GLV_FIELD_COUNT
        ca_fc_phase = CA_FC_POST;
#endif
        ops += W;
        steps += W;
#ifdef CA_GLV_TRACE
        tr.step_ops += W;
        tr.iterations++;
#endif
        for (uint32_t w = 0; w < W; w++) {
            glv_walk *wk = &walks[w];
            uint32_t k;
            uint64_t h;
#ifdef CA_GLV_BATCH_ESCAPE
            if (wk->esc) {
                /* Finish the escape the previous iteration decided on: Yn[w]
                 * is twice the cycle member, in this walk's own batch slot.
                 * The state from here is exactly what the inline doubling
                 * left. */
                wk->esc = 0;
                wk->Y = Yn[w];
                wk->a = ca_addmod(wk->a, wk->a, n);
                wk->b = ca_addmod(wk->b, wk->b, n);
                uint32_t kk = glv_class_reduce(g, &wk->Y, c.m);
                if (kk) {
                    wk->a = ca_mulmod(wk->a, c.lam_pow[kk], n);
                    wk->b = ca_mulmod(wk->b, c.lam_pow[kk], n);
                }
                h = ca_group_hash(g, &wk->Y);
                goto glv_dp_check;
            }
#endif
            k = glv_class_reduce(g, &Yn[w], c.m);
            h = ca_group_hash(g, &Yn[w]);
            /* Fruitless-cycle look-ahead: if the reduced point would pick the
             * same multiplier we just used, advance to the next one and redo
             * the step -- a deterministic function of the class, so walks
             * still merge (generalises the negation map's 2-cycle rule).
             *
             * Also reject a candidate whose reduced point would pick the
             * multiplier Y itself selects (wk->first).  Without that, an
             * advance from Y onto j + 1 can land on the point the walk came
             * from, when that point had itself been left by an advance onto
             * j + 1: with -1 in the class, Y + M_{j+1} reduces back to it,
             * and the two points alternate until the walk is abandoned.
             * A traced run (experiments/glv-walk-trace-20261018) found every
             * 2-cycle to be of this form.  Both tests depend on Y alone, so
             * the step stays a function of the class.  Build with
             * -DCA_GLV_LOOKAHEAD_LEGACY for the original single test. */
            uint32_t nat = (uint32_t)(ca_mix64(h) % c.r);
#ifdef CA_GLV_LOOKAHEAD_LEGACY
            if (nat == wk->idx) {
#else
            if ((nat == wk->idx || nat == wk->first) && wk->tries + 1 < c.r) {
                wk->tries++;
#endif
                wk->idx = (wk->idx + 1) % c.r;
                wk->retry = 1;
#ifdef CA_GLV_FIELD_COUNT
                ca_fc_ev[CA_FC_EV_RETRIES]++;
#endif
#ifdef CA_GLV_TRACE
                tr.retry_steps++;
                wk->retried = 1;
#endif
                continue;
            }
            wk->retry = 0;
#ifdef CA_GLV_TRACE
            tr.useful_steps++;
            wk->ring_idx[wk->ring_pos % GLV_RING] = wk->idx;
            wk->ring_retry[wk->ring_pos % GLV_RING] = wk->retried;
            wk->retried = 0;
            wk->ring[wk->ring_pos++ % GLV_RING] = h;
#endif
            wk->a = ca_addmod(wk->a, c.alpha[wk->idx], n);
            wk->b = ca_addmod(wk->b, c.beta[wk->idx], n);
            if (k) {
                wk->a = ca_mulmod(wk->a, c.lam_pow[k], n);
                wk->b = ca_mulmod(wk->b, c.lam_pow[k], n);
            }
            wk->Y = Yn[w];
            wk->since_dp++;
#ifdef CA_GLV_CYCLE_ESCAPE
            {
                /* Deterministic escape from fruitless 2- and 4-cycles: when the
                 * new point equals the one two (or four) committed steps back,
                 * the walk is cycling.  Leave from the cycle member with the
                 * smallest hash by doubling it, so every walk that enters the
                 * same cycle leaves it the same way and walks still merge. */
                uint32_t L = 0;
                if (wk->hn >= 2 && wk->hh[1] == h)
                    L = 2;
                else if (wk->hn >= 4 && wk->hh[3] == h)
                    L = 4;
                if (L) {
                    uint32_t best = UINT32_MAX; /* UINT32_MAX: the new point itself */
                    uint64_t best_h = h;
                    for (uint32_t i = 0; i + 1 < L; i++)
                        if (wk->hh[i] < best_h) {
                            best_h = wk->hh[i];
                            best = i;
                        }
#    ifdef CA_GLV_FIELD_COUNT
                    ca_fc_ev[L == 2 ? CA_FC_EV_ESC2 : CA_FC_EV_ESC4]++;
#    endif
                    ca_elem P = best == UINT32_MAX ? wk->Y : wk->hY[best];
                    uint64_t pa = best == UINT32_MAX ? wk->a : wk->ha[best];
                    uint64_t pb = best == UINT32_MAX ? wk->b : wk->hb[best];
#    ifdef CA_GLV_BATCH_ESCAPE
                    /* Leave the doubling to this walk's slot in the next
                     * batch (a == b there is a doubling, sharing the batch's
                     * one inversion).  The slot is one of the W operations
                     * the iteration already counts, so the doubling is
                     * booked as before, one group operation; the walk's
                     * state after it is finished at the top of the next
                     * iteration and equals the inline result. */
                    wk->Y = P;
                    wk->a = pa;
                    wk->b = pb;
                    wk->esc = 1;
#    else
#        ifdef CA_GLV_FIELD_COUNT
                    ca_fc_phase = CA_FC_ESCAPE;
#        endif
                    ca_group_op(g, &wk->Y, &P, &P);
                    ops++;
                    wk->a = ca_addmod(pa, pa, n);
                    wk->b = ca_addmod(pb, pb, n);
                    uint32_t kk = glv_class_reduce(g, &wk->Y, c.m);
                    if (kk) {
                        wk->a = ca_mulmod(wk->a, c.lam_pow[kk], n);
                        wk->b = ca_mulmod(wk->b, c.lam_pow[kk], n);
                    }
                    h = ca_group_hash(g, &wk->Y);
#        ifdef CA_GLV_FIELD_COUNT
                    ca_fc_phase = CA_FC_POST;
#        endif
#    endif
                    wk->hn = 0;
#    ifdef CA_GLV_TRACE
                    if (L == 2)
                        tr.escape2++;
                    else
                        tr.escape4++;
#        ifndef CA_GLV_BATCH_ESCAPE
                    tr.restart_ops += 1; /* the doubling is booked with restarts */
#        endif
                    tr.abandon_wasted +=
                        L; /* the L committed steps around the cycle were not productive */
                    wk->trace_wasted_since_dp +=
                        ca_glv_trace_cycle_steps_since_dp(L, wk->since_dp);
                    assert(wk->trace_wasted_since_dp <= wk->since_dp);
                    wk->ring_pos = 0;
#    endif
#    ifdef CA_GLV_BATCH_ESCAPE
                    continue; /* no data point or abandon test until the doubling is done */
#    endif
                } else {
                    for (uint32_t i = 3; i > 0; i--) {
                        wk->hY[i] = wk->hY[i - 1];
                        wk->ha[i] = wk->ha[i - 1];
                        wk->hb[i] = wk->hb[i - 1];
                        wk->hh[i] = wk->hh[i - 1];
                    }
                    wk->hY[0] = wk->Y;
                    wk->ha[0] = wk->a;
                    wk->hb[0] = wk->b;
                    wk->hh[0] = h;
                    if (wk->hn < 4) wk->hn++;
                }
            }
#endif
#ifdef CA_GLV_BATCH_ESCAPE
        glv_dp_check:
#endif
            if ((h & c.dp_mask) == 0) {
                uint64_t oa, ob;
                int ins = ca_htab_insert(&tab, h, wk->a, wk->b, &oa, &ob);
                if (ins < 0) goto nomem;
                wk->since_dp = 0;
#ifdef CA_GLV_TRACE
                ca_glv_trace_reset_since_dp(&wk->trace_wasted_since_dp);
                tr.dps++;
#endif
                if (ins == 1) {
#ifdef CA_GLV_FIELD_COUNT
                    ca_fc_phase = CA_FC_OUTSIDE;
#endif
#ifdef CA_GLV_TRACE
                    tr.coll_total++;
                    if (oa == wk->a && ob == wk->b) tr.coll_same_ab++;
#endif
                    if (!(oa == wk->a && ob == wk->b) &&
                        glv_recover(g, base, target, n, oa, ob, wk->a, wk->b, x)) {
                        rc = CA_OK;
                        goto done;
                    }
#ifdef CA_GLV_TRACE
                    if (!(oa == wk->a && ob == wk->b)) tr.coll_recover_fail++;
                    uint64_t before = ops;
#endif
#ifdef CA_GLV_FIELD_COUNT
                    ca_fc_phase = CA_FC_POST;
#endif
                    if (!glv_restart(&c, wk, &rng, &ops)) {
                        rc = CA_ERR_INTERNAL;
                        goto done;
                    }
#ifdef CA_GLV_TRACE
                    tr.restart_ops += ops - before;
                    wk->ring_pos = 0;
                    wk->retried = 0;
#endif
                }
            } else if (wk->since_dp > c.abandon) {
#ifdef CA_GLV_TRACE
                tr.abandons++;
                assert(wk->trace_wasted_since_dp <= wk->since_dp);
                tr.abandon_wasted += ca_glv_trace_unaccounted_abandon_steps(
                    wk->since_dp, wk->trace_wasted_since_dp);
                { /* is the walk in a short cycle?  find the current hash among the previous ones */
                    uint32_t L = 0, have = wk->ring_pos < GLV_RING ? wk->ring_pos : GLV_RING;
                    for (uint32_t d = 1; d < have && !L; d++)
                        if (wk->ring[(wk->ring_pos - 1 - d) % GLV_RING] == h) L = d;
                    if (L) {
                        tr.abandon_cycle++;
                        tr.cycle_len[L]++;
                    } else
                        tr.abandon_nocycle++;
                    if (L == 2) {
                        uint32_t i1 = wk->ring_idx[(wk->ring_pos - 1) % GLV_RING],
                                 i2 = wk->ring_idx[(wk->ring_pos - 2) % GLV_RING];
                        if (i1 == i2) {
                            tr.cycle2_same_idx++;
                            if (wk->ring_retry[(wk->ring_pos - 1) % GLV_RING] ||
                                wk->ring_retry[(wk->ring_pos - 2) % GLV_RING])
                                tr.cycle2_after_retry++;
                        }
                    }
                }
                uint64_t before = ops;
#endif
                if (!glv_restart(&c, wk, &rng, &ops)) {
                    rc = CA_ERR_INTERNAL;
                    goto done;
                }
#ifdef CA_GLV_TRACE
                tr.restart_ops += ops - before;
                wk->ring_pos = 0;
                wk->retried = 0;
#endif
            }
        }
        double now = monitor ? ca_now() : 0;
        if (monitor && now >= next_progress) {
            if (!dlog_ckpt_progress(checkpoint_path, "glv", "walk", "running",
                                   elapsed_prior + now - t0, ops, steps, tab.count,
                                   verbose)) {
                ca_set_error("glv: cannot persist progress");
                rc = CA_ERR_INTERNAL; goto done;
            }
            next_progress = now + (progress_interval ? progress_interval : 5);
        }
        if (checkpoint_path && now >= next_checkpoint) {
            if (!glv_checkpoint_save(checkpoint_path, &identity, walks, &tab, &rng,
                                     effective_seed, ops, steps,
                                     elapsed_prior + now - t0, 0, 0)) {
                rc = CA_ERR_INTERNAL; goto done;
            }
            next_checkpoint = now + (checkpoint_interval ? checkpoint_interval : 60);
        }
    }
    if (max_ops && ops >= max_ops) rc = CA_ERR_LIMIT;
done:
#ifdef CA_GLV_FIELD_COUNT
    ca_fc_phase = CA_FC_OUTSIDE;
#endif
    if (have_tab && checkpoint_ready) {
        double elapsed = elapsed_prior + ca_now() - t0;
        if (checkpoint_path && !glv_checkpoint_save(checkpoint_path, &identity,
                walks, &tab, &rng, effective_seed, ops, steps, elapsed,
                rc == CA_OK ? *x : 0, rc == CA_OK)) rc = CA_ERR_INTERNAL;
        if ((checkpoint_path || verbose) && !dlog_ckpt_progress(checkpoint_path, "glv", "walk",
                                rc == CA_OK ? "ok" : "stopped", elapsed,
                                ops, steps, tab.count, verbose)) {
            ca_set_error("glv: cannot persist progress"); rc = CA_ERR_INTERNAL;
        }
    }
#ifdef CA_GLV_TRACE
{
    assert(tr.abandon_wasted <= tr.useful_steps);
    assert(ca_glv_trace_ops_total(tr.table_ops, tr.start_ops, tr.restart_ops, tr.step_ops)
           + trace_prior_ops == ops);
    const char *path = getenv("CA_GLV_TRACE_FILE");
    FILE *fp = path ? fopen(path, "a") : NULL;
    if (fp) {
        fprintf(fp,
                "{\"m\":%u,\"n\":%llu,\"W\":%u,\"r\":%u,\"dp_bits\":%d,\"abandon_after\":%llu,"
                "\"solved\":%d,\"total_ops\":%llu,"
                "\"table_ops\":%llu,\"start_ops\":%llu,\"restart_ops\":%llu,\"step_ops\":%llu,"
                "\"useful_steps\":%llu,\"retry_steps\":%llu,"
                "\"iterations\":%llu,\"dps\":%llu,\"coll_total\":%llu,\"coll_same_ab\":%llu,\"coll_"
                "recover_fail\":%llu,"
                "\"abandons\":%llu,\"abandon_wasted\":%llu,\"abandon_cycle\":%llu,\"abandon_"
                "nocycle\":%llu,"
                "\"cycle2_same_idx\":%llu,\"cycle2_after_retry\":%llu,\"escape2\":%llu,\"escape4\":"
                "%llu,\"cycle_len\":{",
                c.m, (unsigned long long)n, W, c.r, c.dp_bits, (unsigned long long)c.abandon,
                rc == CA_OK, (unsigned long long)ops, (unsigned long long)tr.table_ops,
                (unsigned long long)tr.start_ops, (unsigned long long)tr.restart_ops,
                (unsigned long long)tr.step_ops, (unsigned long long)tr.useful_steps,
                (unsigned long long)tr.retry_steps, (unsigned long long)tr.iterations,
                (unsigned long long)tr.dps, (unsigned long long)tr.coll_total,
                (unsigned long long)tr.coll_same_ab, (unsigned long long)tr.coll_recover_fail,
                (unsigned long long)tr.abandons, (unsigned long long)tr.abandon_wasted,
                (unsigned long long)tr.abandon_cycle, (unsigned long long)tr.abandon_nocycle,
                (unsigned long long)tr.cycle2_same_idx, (unsigned long long)tr.cycle2_after_retry,
                (unsigned long long)tr.escape2, (unsigned long long)tr.escape4);
        int first = 1;
        for (int L = 1; L <= GLV_RING; L++)
            if (tr.cycle_len[L]) {
                fprintf(fp, "%s\"%d\":%llu", first ? "" : ",", L,
                        (unsigned long long)tr.cycle_len[L]);
                first = 0;
            }
        fprintf(fp, "}}\n");
        fclose(fp);
    }
}
#endif
    if (st) {
        st->group_ops += ops;
        st->iterations += steps;
        st->table_entries = ca_max_u64(st->table_entries, tab.count);
        st->bytes_peak = ca_max_u64(st->bytes_peak, ca_htab_bytes(&tab) +
                         (uint64_t)c.r * 32 + (paired2
                         ? (plane_format ? sizeof(plane_pre) : sizeof(plane_pre.base)) : 0));
        st->seconds += elapsed_prior + ca_now() - t0;
        st->threads = 1;
    }
    ca_htab_free(&tab);
    free(c.M);
    free(c.alpha);
    free(c.beta);
    free(scratch);
    free(walks);
    free(Yn);
    free(B);
    return rc;
nomem:
    if (have_tab) ca_htab_free(&tab);
    free(c.M);
    free(c.alpha);
    free(c.beta);
    free(scratch);
    free(walks);
    free(Yn);
    free(B);
    return failure;
}

static ca_status curve_solve_mode(const ca_group *g, const ca_elem *base,
                                  const ca_elem *target, uint64_t seed, uint64_t *x,
                                  ca_curve_startup_mode mode, ca_curve_startup_stats *startup,
                                  ca_curve_info *info, ca_stats *st)
{
    if (startup) memset(startup, 0, sizeof(*startup));
    if (mode != CA_CURVE_STARTUP_GENERIC && mode != CA_CURVE_STARTUP_TAU_PAIRED2 &&
        mode != CA_CURVE_STARTUP_TAU_PAIRED2_BATCH &&
        mode != CA_CURVE_STARTUP_TAU_PAIRED2_PLANE_BATCH &&
        mode != CA_CURVE_STARTUP_TAU_PAIRED2_FREE_GAUGE_BATCH &&
        mode != CA_CURVE_STARTUP_TAU_PAIRED2_TAUPAIR_STEER_BATCH)
        return CA_ERR_INVALID;
    if (mode != CA_CURVE_STARTUP_GENERIC &&
        (g->kind != CA_GROUP_EC || g->endo_kind != CA_CURVE_ENDO_J0))
        return CA_ERR_UNSUPPORTED;
    if (info) {
        memset(info, 0, sizeof(*info));
        info->endo = (ca_curve_endo)g->endo_kind;
        info->aut_order = g->endo_kind ? g->aut_order : 2;
        info->lambda = g->endo_lambda;
        info->rho_speedup = sqrt((double)info->aut_order);
    }
    if (g->order && !ca_check_members(g, base, target, g->order, "glv rho"))
        return CA_ERR_NOT_FOUND;
    if (g->kind == CA_GROUP_EC && g->endo_kind != 0)
        return glv_rho_solve(g, base, target, seed, x, st,
                             mode != CA_CURVE_STARTUP_GENERIC,
                             mode == CA_CURVE_STARTUP_TAU_PAIRED2_BATCH ||
                             mode == CA_CURVE_STARTUP_TAU_PAIRED2_PLANE_BATCH ||
                             mode == CA_CURVE_STARTUP_TAU_PAIRED2_FREE_GAUGE_BATCH ||
                             mode == CA_CURVE_STARTUP_TAU_PAIRED2_TAUPAIR_STEER_BATCH,
                             mode == CA_CURVE_STARTUP_TAU_PAIRED2_PLANE_BATCH,
                             mode == CA_CURVE_STARTUP_TAU_PAIRED2_FREE_GAUGE_BATCH ||
                             mode == CA_CURVE_STARTUP_TAU_PAIRED2_TAUPAIR_STEER_BATCH,
                             mode == CA_CURVE_STARTUP_TAU_PAIRED2_TAUPAIR_STEER_BATCH,
                             startup, NULL, 0, 0, 0, 0);
    ca_rho_params rp;
    ca_rho_params_default(&rp);
    rp.seed = seed;
    return ca_rho_solve(g, base, target, &rp, x, st);
}

ca_status ca_curve_solve(const ca_group *g, const ca_elem *base, const ca_elem *target,
                         uint64_t seed, uint64_t *x, ca_curve_info *info, ca_stats *st)
{
    return curve_solve_mode(g, base, target, seed, x, CA_CURVE_STARTUP_GENERIC,
                            NULL, info, st);
}

ca_status ca_curve_solve_checkpointed(const ca_group *g, const ca_elem *base,
                                      const ca_elem *target, uint64_t seed,
                                      const char *checkpoint_path, uint32_t progress_interval,
                                      uint32_t checkpoint_interval, int verbose,
                                      uint64_t max_ops, uint64_t *x,
                                      ca_curve_info *info, ca_stats *st)
{
    if (info) {
        memset(info, 0, sizeof(*info));
        info->endo = (ca_curve_endo)g->endo_kind;
        info->aut_order = g->endo_kind ? g->aut_order : 2;
        info->lambda = g->endo_lambda;
        info->rho_speedup = sqrt((double)info->aut_order);
    }
    if (g->order && !ca_check_members(g, base, target, g->order, "glv rho"))
        return CA_ERR_NOT_FOUND;
    if (g->kind == CA_GROUP_EC && g->endo_kind)
        return glv_rho_solve(g, base, target, seed, x, st, 0, 0, 0, 0, 0, NULL,
                             checkpoint_path, progress_interval, checkpoint_interval,
                             verbose, max_ops);
    ca_rho_params rp;
    ca_rho_params_default(&rp);
    rp.seed = seed;
    rp.max_ops = max_ops;
    return ca_rho_solve_checkpointed(g, base, target, &rp, checkpoint_path,
                                     progress_interval, checkpoint_interval,
                                     verbose, x, st);
}

ca_status ca_curve_solve_startup(const ca_group *g, const ca_elem *base,
                                 const ca_elem *target, uint64_t seed, uint64_t *x,
                                 ca_curve_startup_mode mode, ca_curve_startup_stats *startup,
                                 ca_curve_info *info, ca_stats *st)
{
    return curve_solve_mode(g, base, target, seed, x, mode, startup, info, st);
}
