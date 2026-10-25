/*
 * bsgs.c - baby-step giant-step.
 *
 * Baby steps j*base for 0 <= j < m go into a hash table keyed by the
 * element fingerprint.  Giant steps walk target - (lo + i m) base for
 * i = 0, 1, ... and look up the table.  Matches are verified by a scalar
 * multiplication so 64-bit fingerprint collisions cannot produce a wrong
 * answer.
 */
#include "cryptanalysis/ca_bsgs.h"
#include "dlog_internal.h"
#include "dlog_checkpoint_internal.h"

#include <math.h>
#include <stddef.h>

/* Baby and giant steps advance BSGS_LANES elements at once through the
 * group's batched op, which on a curve shares one field inversion among
 * them (a single affine add pays one each).  Which elements are hashed,
 * inserted, looked up and verified, in which order, and every count are
 * those of the one-at-a-time loops; a block may compute up to
 * BSGS_LANES - 1 elements past the last one used, which are not counted. */
#define BSGS_LANES 64

/* Fill 0, base, ..., (count - 1) * base.  Doubling the filled prefix
 * lets each level share one inversion on elliptic curves. */
static void bsgs_multiples(const ca_group *g, ca_elem *out, const ca_elem *base,
                           size_t count, uint64_t *scratch)
{
    ca_group_identity(g, &out[0]);
    if (count == 1) return;
    if (g->kind != CA_GROUP_EC) {
        for (size_t i = 1; i < count; i++)
            ca_group_op(g, &out[i], &out[i - 1], base);
        return;
    }
    out[1] = *base;
    ca_elem addends[BSGS_LANES];
    for (size_t span = 2; span < count; span *= 2) {
        ca_elem offset;
        ca_group_dbl(g, &offset, &out[span / 2]);
        size_t n = count - span < span ? count - span : span;
        for (size_t i = 0; i < n; i++) addends[i] = offset;
        ca_group_batch_op(g, out + span, out, addends, n, scratch);
    }
}

struct ca_bsgs_table {
    const ca_group *g;
    ca_elem base;
    ca_elem neg_m_base; /* -m * base */
    ca_elem giant[BSGS_LANES]; /* k * (-m * base) for k < BSGS_LANES */
    ca_elem giant_block;       /* BSGS_LANES * (-m * base) */
    uint64_t m;
    ca_htab1 tab;
};

enum { BSGS_PHASE_BABY = 0, BSGS_PHASE_GIANT = 1,
       BSGS_PHASE_SOLVED = 2, BSGS_PHASE_EXHAUSTED = 3 };

typedef struct bsgs_checkpoint_header {
    char magic[8];
    uint64_t p, a, b, order, cofactor;
    uint64_t base[4], target[4], lo, hi, requested_m;
    uint32_t kind, endo_kind, aut_order, entry_size;
    uint64_t endo_lambda, endo_c_mont;
    uint32_t phase, status;
    uint64_t effective_m, baby_next, giant_next, ops, entries, result;
    double elapsed_seconds;
    uint64_t checksum;
} bsgs_checkpoint_header;

static void bsgs_checkpoint_identity(bsgs_checkpoint_header *h, const ca_group *g,
                                      const ca_elem *base, const ca_elem *target,
                                      uint64_t lo, uint64_t hi, uint64_t m)
{
    memset(h, 0, sizeof(*h));
    memcpy(h->magic, "CABSGS01", 8);
    h->p = g->p; h->a = g->a; h->b = g->b;
    h->order = g->order; h->cofactor = g->cofactor;
    ca_group_decode(g, h->base, base);
    ca_group_decode(g, h->target, target);
    h->lo = lo; h->hi = hi; h->requested_m = m;
    h->kind = g->kind; h->endo_kind = g->endo_kind;
    h->aut_order = g->aut_order; h->entry_size = sizeof(ca_htab1_entry);
    h->endo_lambda = g->endo_lambda; h->endo_c_mont = g->endo_c_mont;
}

static int bsgs_checkpoint_probe(const char *path, const bsgs_checkpoint_header *identity,
                                  bsgs_checkpoint_header *saved)
{
    if (!path) return 0;
    FILE *f = fopen(path, "rb");
    if (!f) {
        if (errno == ENOENT) return 0;
        ca_set_error("bsgs: cannot open checkpoint");
        return -1;
    }
    int ok = fread(saved, 1, sizeof(*saved), f) == sizeof(*saved) &&
             memcmp(saved, identity, offsetof(bsgs_checkpoint_header, phase)) == 0 &&
             saved->phase <= BSGS_PHASE_EXHAUSTED &&
             saved->effective_m >= 1 && saved->effective_m <= identity->requested_m &&
             saved->baby_next <= identity->requested_m &&
             saved->entries <= saved->baby_next && saved->ops >= saved->entries &&
             (saved->phase != BSGS_PHASE_BABY ||
              (saved->baby_next < identity->requested_m &&
               saved->baby_next % BSGS_LANES == 0)) &&
             (saved->phase == BSGS_PHASE_BABY ||
              saved->baby_next == saved->effective_m) &&
             (saved->phase != BSGS_PHASE_SOLVED || saved->status == CA_OK) &&
             (saved->phase != BSGS_PHASE_EXHAUSTED ||
              saved->status == CA_ERR_NOT_FOUND) &&
             saved->elapsed_seconds >= 0 && isfinite(saved->elapsed_seconds);
    fclose(f);
    if (!ok) { ca_set_error("bsgs: checkpoint identity or format does not match"); return -1; }
    return 1;
}

static int bsgs_checkpoint_save(const char *path, const bsgs_checkpoint_header *identity,
                                 const ca_htab1 *tab, uint32_t phase, ca_status status,
                                 uint64_t effective_m, uint64_t baby_next,
                                 uint64_t giant_next, uint64_t ops, double elapsed,
                                 uint64_t result)
{
    if (!path) return 1;
    dlog_ckpt_file w;
    int ok = dlog_ckpt_begin(&w, path);
    bsgs_checkpoint_header h = *identity;
    h.phase = phase; h.status = (uint32_t)status;
    h.effective_m = effective_m; h.baby_next = baby_next;
    h.giant_next = giant_next; h.ops = ops; h.entries = tab->count;
    h.elapsed_seconds = elapsed; h.result = result; h.checksum = 0;
    uint64_t hash = dlog_ckpt_hash(&h, sizeof(h), UINT64_C(14695981039346656037));
    if (ok) ok = fwrite(&h, 1, sizeof(h), w.f) == sizeof(h);
    for (size_t i = 0; ok && i < tab->cap; i++) {
        const ca_htab1_entry *e = &tab->e[i];
        if (!e->key) continue;
        hash = dlog_ckpt_hash(e, sizeof(*e), hash);
        ok = fwrite(e, 1, sizeof(*e), w.f) == sizeof(*e);
    }
    if (ok) {
        h.checksum = hash;
        ok = fseek(w.f, 0, SEEK_SET) == 0 &&
             fwrite(&h, 1, sizeof(h), w.f) == sizeof(h);
    }
    ok = dlog_ckpt_finish(&w, ok);
    if (!ok) ca_set_error("bsgs: cannot persist checkpoint");
    return ok;
}

static int bsgs_checkpoint_load(const char *path, const bsgs_checkpoint_header *saved,
                                 ca_htab1 *tab)
{
    FILE *f = fopen(path, "rb");
    if (!f) { ca_set_error("bsgs: cannot reopen checkpoint"); return 0; }
    bsgs_checkpoint_header h = {0};
    int ok = fread(&h, 1, sizeof(h), f) == sizeof(h) &&
             /* Both headers are raw fread() bytes of the same file, including padding. */
             // NOLINTNEXTLINE(bugprone-suspicious-memory-comparison,cert-exp42-c,cert-flp37-c)
             memcmp(&h, saved, sizeof(h)) == 0;
    struct stat fs;
    if (h.entries > (UINT64_MAX - sizeof(h)) / sizeof(ca_htab1_entry)) ok = 0;
    uint64_t bytes = ok ? sizeof(h) + h.entries * sizeof(ca_htab1_entry) : 0;
    if (!ok || fstat(fileno(f), &fs) != 0 || fs.st_size < 0 ||
        bytes != (uint64_t)fs.st_size) ok = 0;
    uint64_t checksum = h.checksum;
    h.checksum = 0;
    uint64_t hash = dlog_ckpt_hash(&h, sizeof(h), UINT64_C(14695981039346656037));
    for (uint64_t i = 0; ok && i < h.entries; i++) {
        ca_htab1_entry e;
        if (fread(&e, 1, sizeof(e), f) != sizeof(e) || !e.key ||
            e.v0 >= h.baby_next) { ok = 0; break; }
        hash = dlog_ckpt_hash(&e, sizeof(e), hash);
        if (ca_htab1_insert(tab, e.key, e.v0, NULL) != 0) ok = 0;
    }
    if (ok && (hash != checksum || tab->count != h.entries || fgetc(f) != EOF)) ok = 0;
    if (ferror(f)) ok = 0;
    fclose(f);
    if (!ok) ca_set_error("bsgs: checkpoint is truncated or corrupt");
    return ok;
}

void ca_bsgs_params_default(ca_bsgs_params *p)
{
    p->table_size = 0;
    p->max_ops = 0;
}

ca_status ca_bsgs_table_new(const ca_group *g, const ca_elem *base, uint64_t m, ca_bsgs_table **out)
{
    if (m == 0) return CA_ERR_INVALID;
    ca_bsgs_table *t = calloc(1, sizeof(*t));
    if (!t) return CA_ERR_NOMEM;
    t->g = g;
    t->base = *base;
    t->m = m;
    if (ca_htab1_init(&t->tab, (size_t)m) != CA_OK) {
        free(t);
        return CA_ERR_NOMEM;
    }
    /* lane c holds (j0 + c) * base for the block starting at j0 */
    ca_elem lane[BSGS_LANES], stride[BSGS_LANES];
    uint64_t scratch[2 * BSGS_LANES];
    const uint64_t first = m < BSGS_LANES ? m : BSGS_LANES;
    bsgs_multiples(g, lane, base, (size_t)first, scratch);
    if (m > BSGS_LANES) {
        ca_group_dbl(g, &stride[0], &lane[BSGS_LANES / 2]);
        for (int c = 1; c < BSGS_LANES; c++) stride[c] = stride[0];
    }
    for (uint64_t j0 = 0; j0 < m; j0 += BSGS_LANES) {
        const uint64_t n = m - j0 < BSGS_LANES ? m - j0 : BSGS_LANES;
        /* hash the block first and request its slots together, so the
         * table's cache misses overlap instead of queueing one by one */
        uint64_t hs[BSGS_LANES];
        for (uint64_t c = 0; c < n; c++) {
            hs[c] = ca_group_hash(g, &lane[c]);
            ca_htab1_prefetch(&t->tab, hs[c]);
        }
        for (uint64_t c = 0; c < n; c++) {
            int rc = ca_htab1_insert(&t->tab, hs[c], j0 + c, NULL);
            if (rc < 0) {
                ca_bsgs_table_free(t);
                return CA_ERR_NOMEM;
            }
            if (rc == 1) {
                /* base has order <= j: the table already spans the whole group */
                t->m = j0 + c;
                goto baby_done;
            }
        }
        if (j0 + BSGS_LANES < m) {
            const uint64_t next = m - j0 - BSGS_LANES;
            ca_group_batch_op(g, lane, lane, stride, next < BSGS_LANES ? next : BSGS_LANES,
                              scratch);
        }
    }
baby_done:
    if (t->m == 0) { ca_bsgs_table_free(t); return CA_ERR_INVALID; }
    ca_elem mb;
    ca_group_mul(g, &mb, base, t->m, NULL);
    ca_group_inv(g, &t->neg_m_base, &mb);
    bsgs_multiples(g, t->giant, &t->neg_m_base, BSGS_LANES, scratch);
    ca_group_dbl(g, &t->giant_block, &t->giant[BSGS_LANES / 2]);
    *out = t;
    return CA_OK;
}

void ca_bsgs_table_free(ca_bsgs_table *t)
{
    if (!t) return;
    ca_htab1_free(&t->tab);
    free(t);
}

static ca_status bsgs_table_solve_impl(const ca_bsgs_table *t, const ca_elem *target, uint64_t lo,
                                       uint64_t hi, uint64_t *x, ca_stats *st, int add_time)
{
    const ca_group *g = t->g;
    ca_status rc = ca_resolve_interval(g, &lo, &hi);
    if (rc != CA_OK) return rc;
    double t0 = ca_now();
    uint64_t width_m1 = hi - lo; /* number of candidates minus one */
    uint64_t m = t->m;
    /* R = target - lo*base */
    ca_elem R, tmp;
    ca_group_mul(g, &tmp, &t->base, lo, st ? &st->group_ops : NULL);
    ca_group_inv(g, &tmp, &tmp);
    ca_group_op(g, &R, target, &tmp);
    uint64_t steps = width_m1 / m + 1;
    /* Step i + k of a block is R_i + k * (-m base), BSGS_LANES of them per
     * batched op; they are looked up in order and each one that does not
     * return is charged one op, as the one-step loop charges it. */
    ca_elem Rs[BSGS_LANES], Rrep[BSGS_LANES];
    uint64_t scratch[2 * BSGS_LANES];
    for (uint64_t i0 = 0; i0 < steps; i0 += BSGS_LANES) {
        const uint64_t n = steps - i0 < BSGS_LANES ? steps - i0 : BSGS_LANES;
        for (uint64_t k = 0; k < n; k++) Rrep[k] = R;
        ca_group_batch_op(g, Rs, Rrep, t->giant, n, scratch);
        uint64_t hs[BSGS_LANES];
        for (uint64_t k = 0; k < n; k++) {
            hs[k] = ca_group_hash(g, &Rs[k]);
            ca_htab1_prefetch(&t->tab, hs[k]);
        }
        for (uint64_t k = 0; k < n; k++) {
            const uint64_t i = i0 + k;
            uint64_t j;
            if (ca_htab1_find(&t->tab, hs[k], &j)) {
                ca_u128 cand = (ca_u128)lo + (ca_u128)i * m + j;
                if (cand <= hi) {
                    uint64_t cx = (uint64_t)cand;
                    if (ca_verify_log(g, &t->base, target, cx)) {
                        *x = cx;
                        if (st) {
                            st->iterations += i + 1;
                            st->table_entries = ca_max_u64(st->table_entries, t->tab.count);
                            st->bytes_peak = ca_max_u64(st->bytes_peak, ca_htab1_bytes(&t->tab));
                            if (add_time) st->seconds += ca_now() - t0;
                        }
                        return CA_OK;
                    }
                }
            }
            if (st) st->group_ops++;
        }
        if (n == BSGS_LANES) ca_group_op(g, &R, &R, &t->giant_block);
    }
    if (st) {
        st->iterations += steps;
        st->table_entries = ca_max_u64(st->table_entries, t->tab.count);
        st->bytes_peak = ca_max_u64(st->bytes_peak, ca_htab1_bytes(&t->tab));
        if (add_time) st->seconds += ca_now() - t0;
    }
    return CA_ERR_NOT_FOUND;
}

ca_status ca_bsgs_table_solve(const ca_bsgs_table *t, const ca_elem *target, uint64_t lo,
                              uint64_t hi, uint64_t *x, ca_stats *st)
{
    return bsgs_table_solve_impl(t, target, lo, hi, x, st, 1);
}

ca_status ca_bsgs_solve(const ca_group *g, const ca_elem *base, const ca_elem *target, uint64_t lo,
                        uint64_t hi, const ca_bsgs_params *params, uint64_t *x, ca_stats *st)
{
    ca_bsgs_params def;
    if (!params) { ca_bsgs_params_default(&def); params = &def; }
    ca_status rc = ca_resolve_interval(g, &lo, &hi);
    if (rc != CA_OK) return rc;
    double t0 = ca_now();
    uint64_t width_m1 = hi - lo;
    uint64_t m = params->table_size;
    if (m == 0) { m = ca_isqrt(width_m1) + 1; /* >= 1 for every width, including 0 */ }
    if (params->max_ops && m + width_m1 / m > params->max_ops) return CA_ERR_LIMIT;
    ca_bsgs_table *t;
    rc = ca_bsgs_table_new(g, base, m, &t);
    if (rc != CA_OK) return rc;
    if (st) st->group_ops += t->m;
    rc = bsgs_table_solve_impl(t, target, lo, hi, x, st, 0);
    ca_bsgs_table_free(t);
    if (st) st->seconds += ca_now() - t0;
    return rc;
}

ca_status ca_bsgs_solve_checkpointed(
    const ca_group *g, const ca_elem *base, const ca_elem *target,
    uint64_t lo, uint64_t hi, const ca_bsgs_params *params,
    const char *checkpoint_path, uint32_t progress_interval,
    uint32_t checkpoint_interval, int verbose, uint64_t *x, ca_stats *st)
{
    ca_bsgs_params def;
    if (!params) { ca_bsgs_params_default(&def); params = &def; }
    ca_status rc = ca_resolve_interval(g, &lo, &hi);
    if (rc != CA_OK) return rc;
    double t0 = ca_now();
    uint64_t width_m1 = hi - lo;
    uint64_t requested_m = params->table_size;
    if (!requested_m) requested_m = ca_isqrt(width_m1) + 1;
    if (requested_m == 0 || requested_m > SIZE_MAX / 2) {
        ca_set_error("bsgs: table size is not representable");
        return CA_ERR_INVALID;
    }
    bsgs_checkpoint_header identity, saved = {0};
    bsgs_checkpoint_identity(&identity, g, base, target, lo, hi, requested_m);
    int existing = bsgs_checkpoint_probe(checkpoint_path, &identity, &saved);
    if (existing < 0) return CA_ERR_INVALID;

    ca_bsgs_table t = {0};
    t.g = g; t.base = *base; t.m = requested_m;
    size_t initial = (size_t)(requested_m < 4096 ? requested_m : 4096);
    if (ca_htab1_init(&t.tab, initial) != CA_OK) return CA_ERR_NOMEM;
    uint32_t phase = BSGS_PHASE_BABY;
    uint64_t effective_m = requested_m, baby_next = 0, giant_next = 0;
    uint64_t ops = 0;
    double elapsed_prior = 0;
    if (existing) {
        if (!bsgs_checkpoint_load(checkpoint_path, &saved, &t.tab)) {
            rc = CA_ERR_INVALID;
            goto done;
        }
        phase = saved.phase; effective_m = saved.effective_m;
        baby_next = saved.baby_next; giant_next = saved.giant_next;
        ops = saved.ops; elapsed_prior = saved.elapsed_seconds;
        if (phase == BSGS_PHASE_SOLVED) {
            if (saved.status != CA_OK || saved.result < lo || saved.result > hi ||
                !ca_verify_log(g, base, target, saved.result)) {
                ca_set_error("bsgs: saved solution fails verification");
                rc = CA_ERR_INVALID;
            } else { *x = saved.result; rc = CA_OK; }
            goto done;
        }
        if (phase == BSGS_PHASE_EXHAUSTED) {
            rc = CA_ERR_NOT_FOUND;
            goto done;
        }
    }
    int monitored = checkpoint_path != NULL || verbose;
    if (!progress_interval) progress_interval = 5;
    if (!checkpoint_interval) checkpoint_interval = 60;
    double next_progress = ca_now() + progress_interval;
    double next_checkpoint = ca_now() + checkpoint_interval;
    if (monitored &&
        (!bsgs_checkpoint_save(checkpoint_path, &identity, &t.tab, phase,
                               CA_ERR_INTERNAL, effective_m, baby_next, giant_next,
                               ops, elapsed_prior + ca_now() - t0, 0) ||
         !dlog_ckpt_progress(checkpoint_path, "bsgs",
                             phase == BSGS_PHASE_BABY ? "baby" : "giant", "running",
                             elapsed_prior + ca_now() - t0, ops,
                             phase == BSGS_PHASE_BABY ? baby_next : giant_next,
                             t.tab.count, verbose))) {
        ca_set_error("bsgs: cannot persist initial progress");
        rc = CA_ERR_INTERNAL;
        goto done;
    }

    if (phase == BSGS_PHASE_BABY) {
        ca_elem offsets[BSGS_LANES], lane[BSGS_LANES], stride[BSGS_LANES], start;
        uint64_t scratch[2 * BSGS_LANES];
        bsgs_multiples(g, offsets, base, BSGS_LANES, scratch);
        ops += BSGS_LANES - 1;
        ca_group_mul(g, &stride[0], base, BSGS_LANES, &ops);
        for (size_t c = 1; c < BSGS_LANES; c++) stride[c] = stride[0];
        if (baby_next) {
            ca_group_mul(g, &start, base, baby_next, &ops);
            for (size_t c = 0; c < BSGS_LANES; c++) lane[c] = start;
            ca_group_batch_op(g, lane, lane, offsets, BSGS_LANES, scratch);
            ops += BSGS_LANES;
        } else memcpy(lane, offsets, sizeof(lane));
        while (baby_next < requested_m) {
            uint64_t nblock = requested_m - baby_next < BSGS_LANES ?
                              requested_m - baby_next : BSGS_LANES;
            uint64_t hs[BSGS_LANES];
            for (uint64_t c = 0; c < nblock; c++) {
                hs[c] = ca_group_hash(g, &lane[c]);
                ca_htab1_prefetch(&t.tab, hs[c]);
            }
            int duplicate = 0;
            for (uint64_t c = 0; c < nblock; c++) {
                int ir = ca_htab1_insert(&t.tab, hs[c], baby_next + c, NULL);
                if (ir < 0) { rc = CA_ERR_NOMEM; goto done; }
                if (ir == 1) {
                    effective_m = baby_next + c;
                    baby_next = effective_m;
                    duplicate = 1;
                    break;
                }
                ops++;
            }
            if (!duplicate) baby_next += nblock;
            if (duplicate || baby_next == requested_m) {
                if (!effective_m) { rc = CA_ERR_INVALID; goto finish; }
                phase = BSGS_PHASE_GIANT;
                if (!bsgs_checkpoint_save(checkpoint_path, &identity, &t.tab, phase,
                                          CA_ERR_INTERNAL, effective_m, baby_next,
                                          giant_next, ops, elapsed_prior + ca_now() - t0, 0)) {
                    rc = CA_ERR_INTERNAL; goto done;
                }
                if (params->max_ops && ops > params->max_ops) {
                    rc = CA_ERR_LIMIT; goto finish;
                }
                break;
            }
            if (params->max_ops && ops > params->max_ops) {
                rc = CA_ERR_LIMIT; goto finish;
            }
            double now = monitored ? ca_now() : 0;
            if (monitored && now >= next_progress) {
                if (!dlog_ckpt_progress(checkpoint_path, "bsgs", "baby", "running",
                                        elapsed_prior + now - t0, ops, baby_next,
                                        t.tab.count, verbose)) {
                    ca_set_error("bsgs: cannot persist progress");
                    rc = CA_ERR_INTERNAL; goto done;
                }
                next_progress = now + progress_interval;
            }
            if (checkpoint_path && now >= next_checkpoint) {
                if (!bsgs_checkpoint_save(checkpoint_path, &identity, &t.tab, phase,
                                          CA_ERR_INTERNAL, effective_m, baby_next,
                                          giant_next, ops, elapsed_prior + now - t0, 0)) {
                    rc = CA_ERR_INTERNAL; goto done;
                }
                if (verbose) fprintf(stderr, "[bsgs] baby checkpoint saved\n");
                next_checkpoint = now + checkpoint_interval;
            }
            if (baby_next < requested_m) {
                ca_group_batch_op(g, lane, lane, stride, BSGS_LANES, scratch);
                ops += BSGS_LANES;
            }
        }
    }

    if (phase == BSGS_PHASE_GIANT) {
        t.m = effective_m;
        ca_elem mb;
        ca_group_mul(g, &mb, base, t.m, &ops);
        ca_group_inv(g, &t.neg_m_base, &mb);
        uint64_t scratch[2 * BSGS_LANES];
        bsgs_multiples(g, t.giant, &t.neg_m_base, BSGS_LANES, scratch);
        ops += BSGS_LANES - 1;
        ca_group_dbl(g, &t.giant_block, &t.giant[BSGS_LANES / 2]);
        ops++;
        ca_elem R, tmp;
        ca_group_mul(g, &tmp, base, lo, &ops);
        ca_group_inv(g, &tmp, &tmp);
        ca_group_op(g, &R, target, &tmp);
        ops++;
        uint64_t steps = width_m1 / t.m;
        if (steps == UINT64_MAX) {
            ca_set_error("bsgs: interval has too many giant steps");
            rc = CA_ERR_INVALID; goto done;
        }
        steps++;
        if (giant_next > steps) {
            ca_set_error("bsgs: saved giant position is outside interval");
            rc = CA_ERR_INVALID; goto done;
        }
        if (giant_next) {
            ca_group_mul(g, &tmp, &t.neg_m_base, giant_next, &ops);
            ca_group_op(g, &R, &R, &tmp);
            ops++;
        }
        while (giant_next < steps) {
            uint64_t nblock = steps - giant_next < BSGS_LANES ?
                              steps - giant_next : BSGS_LANES;
            ca_elem Rs[BSGS_LANES], Rrep[BSGS_LANES];
            for (uint64_t k = 0; k < nblock; k++) Rrep[k] = R;
            ca_group_batch_op(g, Rs, Rrep, t.giant, nblock, scratch);
            uint64_t hs[BSGS_LANES];
            for (uint64_t k = 0; k < nblock; k++) {
                hs[k] = ca_group_hash(g, &Rs[k]);
                ca_htab1_prefetch(&t.tab, hs[k]);
            }
            for (uint64_t k = 0; k < nblock; k++) {
                uint64_t i = giant_next + k, j;
                if (ca_htab1_find(&t.tab, hs[k], &j)) {
                    ca_u128 cand = (ca_u128)lo + (ca_u128)i * t.m + j;
                    if (cand <= hi) {
                        uint64_t cx = (uint64_t)cand;
                        if (ca_verify_log(g, base, target, cx)) {
                            *x = cx; ops += k + 1; giant_next = i + 1;
                            phase = BSGS_PHASE_SOLVED; rc = CA_OK; goto finish;
                        }
                    }
                }
            }
            ops += nblock;
            giant_next += nblock;
            if (nblock == BSGS_LANES) {
                ca_group_op(g, &R, &R, &t.giant_block);
                ops++;
            }
            if (params->max_ops && ops > params->max_ops) {
                rc = CA_ERR_LIMIT; goto finish;
            }
            double now = monitored ? ca_now() : 0;
            if (monitored && now >= next_progress) {
                if (!dlog_ckpt_progress(checkpoint_path, "bsgs", "giant", "running",
                                        elapsed_prior + now - t0, ops, giant_next,
                                        t.tab.count, verbose)) {
                    ca_set_error("bsgs: cannot persist progress");
                    rc = CA_ERR_INTERNAL; goto done;
                }
                next_progress = now + progress_interval;
            }
            if (checkpoint_path && now >= next_checkpoint) {
                if (!bsgs_checkpoint_save(checkpoint_path, &identity, &t.tab, phase,
                                          CA_ERR_INTERNAL, effective_m, baby_next,
                                          giant_next, ops, elapsed_prior + now - t0, 0)) {
                    rc = CA_ERR_INTERNAL; goto done;
                }
                if (verbose) fprintf(stderr, "[bsgs] giant checkpoint saved\n");
                next_checkpoint = now + checkpoint_interval;
            }
        }
        phase = BSGS_PHASE_EXHAUSTED;
        rc = CA_ERR_NOT_FOUND;
    }
finish:
    if (monitored &&
        (!bsgs_checkpoint_save(checkpoint_path, &identity, &t.tab, phase, rc,
                               effective_m, baby_next, giant_next, ops,
                               elapsed_prior + ca_now() - t0,
                               rc == CA_OK ? *x : 0) ||
         !dlog_ckpt_progress(checkpoint_path, "bsgs",
                             phase == BSGS_PHASE_BABY ? "baby" : "giant",
                             rc == CA_OK ? "ok" : "stopped",
                             elapsed_prior + ca_now() - t0, ops,
                             phase == BSGS_PHASE_BABY ? baby_next : giant_next,
                             t.tab.count, verbose))) {
        ca_set_error("bsgs: cannot persist final progress");
        rc = CA_ERR_INTERNAL;
    }
done:
    if (st) {
        st->group_ops += ops;
        st->iterations += giant_next;
        st->table_entries = ca_max_u64(st->table_entries, t.tab.count);
        st->bytes_peak = ca_max_u64(st->bytes_peak, ca_htab1_bytes(&t.tab));
        st->threads = 1;
        st->seconds += elapsed_prior + ca_now() - t0;
    }
    ca_htab1_free(&t.tab);
    return rc;
}
