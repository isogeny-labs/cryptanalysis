/*
 * grumpy.c - two grumpy giants and a baby.
 *
 * After shifting the problem so that x' = x - lo lies in [0, N):
 *   baby   B_j = j*G                       (j = 0, 1, 2, ...)
 *   giant1 U_i = H' + i*m*G                (i = 0, 1, 2, ...)
 *   giant2 V_i = 2H' - i*(m+1)*G
 * Collisions:
 *   B_j = U_i   =>  x' = j - i m
 *   B_j = V_i   =>  2x' = j + i (m+1)
 *   U_i = V_k   =>  x' = i m + k (m+1)
 * All congruences are taken modulo the group order n when known, and
 * every candidate is verified before being returned.
 */
#include "cryptanalysis/ca_grumpy.h"
#include "dlog_internal.h"
#include "dlog_checkpoint_internal.h"

#include <math.h>
#include <stddef.h>

enum { W_BABY = 0, W_G1 = 1, W_G2 = 2 };

void ca_grumpy_params_default(ca_grumpy_params *p)
{
    memset(p, 0, sizeof(*p));
    p->alpha = 0.7;
}

typedef struct grumpy_ctx {
    const ca_group *g;
    const ca_elem *base, *target;
    uint64_t lo, hi, n, m;
    uint64_t inv2;
} grumpy_ctx;

static int grumpy_candidate(grumpy_ctx *c, ca_i128 xprime_times, int doubled, uint64_t *x)
{
    /* xprime_times is x' (doubled == 0) or 2x' (doubled == 1) as a possibly
     * negative integer; reduce and verify. */
    uint64_t n = c->n;
    ca_i128 v = xprime_times;
    uint64_t cands[2];
    int nc = 0;
    if (n) {
        ca_i128 nn = (ca_i128)n;
        v %= nn;
        if (v < 0) v += nn;
        uint64_t u = (uint64_t)v;
        if (!doubled) cands[nc++] = u;
        else if (n & 1) cands[nc++] = ca_mulmod(u, c->inv2, n);
        else {
            if ((u & 1) == 0) { cands[nc++] = u / 2; cands[nc++] = (u / 2 + n / 2) % n; }
        }
    } else {
        if (v < 0) return 0;
        if (doubled) {
            if (v & 1) return 0;
            v /= 2;
        }
        if (v > (ca_i128)UINT64_MAX) return 0;
        cands[nc++] = (uint64_t)v;
    }
    for (int i = 0; i < nc; i++) {
        ca_u128 full = (ca_u128)c->lo + cands[i];
        uint64_t xx;
        if (n) xx = (uint64_t)(full % n);
        else {
            if (full > UINT64_MAX) continue;
            xx = (uint64_t)full;
        }
        if (ca_verify_log(c->g, c->base, c->target, xx)) {
            /* The header promises x in [lo, hi].  A verified logarithm that
             * cannot be shifted into the interval is not the answer that was
             * asked for, so keep looking rather than return it. */
            if (!ca_fit_interval_base(c->g, c->base, &xx, c->lo, c->hi)) continue;
            *x = xx;
            return 1;
        }
    }
    return 0;
}

static int grumpy_collide(grumpy_ctx *c, int t1, uint64_t i1, int t2, uint64_t i2, uint64_t *x)
{
    if (t1 == t2) return 0;
    /* order so that t1 < t2 */
    if (t1 > t2) { int tt = t1; t1 = t2; t2 = tt; uint64_t ti = i1; i1 = i2; i2 = ti; }
    ca_i128 m = (ca_i128)c->m;
    if (t1 == W_BABY && t2 == W_G1) {
        /* j = i1, i = i2: x' = j - i m */
        return grumpy_candidate(c, (ca_i128)i1 - (ca_i128)i2 * m, 0, x);
    }
    if (t1 == W_BABY && t2 == W_G2) {
        /* 2x' = j + i (m+1) */
        return grumpy_candidate(c, (ca_i128)i1 + (ca_i128)i2 * (m + 1), 1, x);
    }
    /* G1 (i1) vs G2 (i2): x' = i1 m + i2 (m+1) */
    return grumpy_candidate(c, (ca_i128)i1 * m + (ca_i128)i2 * (m + 1), 0, x);
}

typedef struct grumpy_checkpoint_header {
    char magic[8];
    uint64_t p, a, b, order, cofactor;
    uint64_t base[4], target[4], lo, hi, m;
    uint32_t kind, endo_kind, aut_order, entry_size;
    uint64_t endo_lambda, endo_c_mont;
    uint64_t next_i, ops, entries, result;
    double elapsed_seconds;
    uint32_t solved;
    uint64_t checksum;
} grumpy_checkpoint_header;

static void grumpy_checkpoint_identity(grumpy_checkpoint_header *h, const grumpy_ctx *c)
{
    memset(h, 0, sizeof(*h));
    memcpy(h->magic, "CAGRMP01", 8);
    h->p = c->g->p; h->a = c->g->a; h->b = c->g->b;
    h->order = c->g->order; h->cofactor = c->g->cofactor;
    ca_group_decode(c->g, h->base, c->base);
    ca_group_decode(c->g, h->target, c->target);
    h->lo = c->lo; h->hi = c->hi; h->m = c->m;
    h->kind = c->g->kind; h->endo_kind = c->g->endo_kind;
    h->aut_order = c->g->aut_order; h->entry_size = sizeof(ca_htab_entry);
    h->endo_lambda = c->g->endo_lambda; h->endo_c_mont = c->g->endo_c_mont;
}

static int grumpy_checkpoint_probe(const char *path, const grumpy_checkpoint_header *identity,
                                    grumpy_checkpoint_header *saved)
{
    if (!path) return 0;
    FILE *f = fopen(path, "rb");
    if (!f) {
        if (errno == ENOENT) return 0;
        ca_set_error("grumpy: cannot open checkpoint");
        return -1;
    }
    int ok = fread(saved, 1, sizeof(*saved), f) == sizeof(*saved) &&
             memcmp(saved, identity, offsetof(grumpy_checkpoint_header, next_i)) == 0 &&
             saved->ops >= saved->next_i && saved->entries <= saved->ops &&
             saved->elapsed_seconds >= 0 && isfinite(saved->elapsed_seconds);
    fclose(f);
    if (!ok) { ca_set_error("grumpy: checkpoint identity or format does not match"); return -1; }
    return 1;
}

static int grumpy_checkpoint_save(const char *path, const grumpy_checkpoint_header *identity,
                                   const ca_group *g, const ca_elem walk[3], const ca_htab *tab,
                                   uint64_t next_i, uint64_t ops, double elapsed,
                                   int solved, uint64_t result)
{
    if (!path) return 1;
    dlog_ckpt_file w;
    int ok = dlog_ckpt_begin(&w, path);
    grumpy_checkpoint_header h = *identity;
    h.next_i = next_i; h.ops = ops; h.entries = tab->count;
    h.elapsed_seconds = elapsed; h.solved = solved; h.result = result;
    h.checksum = 0;
    uint64_t hash = dlog_ckpt_hash(&h, sizeof(h), UINT64_C(14695981039346656037));
    if (ok) ok = fwrite(&h, 1, sizeof(h), w.f) == sizeof(h);
    for (int i = 0; ok && i < 3; i++) {
        uint64_t words[4];
        ca_group_decode(g, words, &walk[i]);
        hash = dlog_ckpt_hash(words, sizeof(words), hash);
        ok = fwrite(words, 1, sizeof(words), w.f) == sizeof(words);
    }
    for (size_t i = 0; ok && i < tab->cap; i++) {
        const ca_htab_entry *e = &tab->e[i];
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
    if (!ok) ca_set_error("grumpy: cannot persist checkpoint");
    return ok;
}

static int grumpy_checkpoint_load(const char *path, const grumpy_checkpoint_header *saved,
                                   const ca_group *g, ca_elem walk[3], ca_htab *tab)
{
    FILE *f = fopen(path, "rb");
    if (!f) { ca_set_error("grumpy: cannot reopen checkpoint"); return 0; }
    grumpy_checkpoint_header h = {0};
    int ok = fread(&h, 1, sizeof(h), f) == sizeof(h) &&
             memcmp(&h, saved, sizeof(h)) == 0; /* NOLINT(bugprone-suspicious-memory-comparison,cert-exp42-c,cert-flp37-c): both headers are raw fread() bytes of the same file, padding included */
    struct stat fs;
    uint64_t prefix = sizeof(h) + (size_t)3 * 4 * sizeof(uint64_t);
    if (h.entries > (UINT64_MAX - prefix) / sizeof(ca_htab_entry)) ok = 0;
    uint64_t bytes = ok ? prefix + h.entries * sizeof(ca_htab_entry) : 0;
    if (!ok || fstat(fileno(f), &fs) != 0 || fs.st_size < 0 ||
        bytes != (uint64_t)fs.st_size) ok = 0;
    uint64_t checksum = h.checksum;
    h.checksum = 0;
    uint64_t hash = dlog_ckpt_hash(&h, sizeof(h), UINT64_C(14695981039346656037));
    for (int i = 0; ok && i < 3; i++) {
        uint64_t words[4];
        if (fread(words, 1, sizeof(words), f) != sizeof(words) ||
            !ca_group_encode(g, &walk[i], words)) { ok = 0; break; }
        hash = dlog_ckpt_hash(words, sizeof(words), hash);
    }
    for (uint64_t i = 0; ok && i < h.entries; i++) {
        ca_htab_entry e;
        if (fread(&e, 1, sizeof(e), f) != sizeof(e) || !e.key ||
            e.v0 > W_G2 || e.v1 > h.next_i) { ok = 0; break; }
        hash = dlog_ckpt_hash(&e, sizeof(e), hash);
        if (ca_htab_insert(tab, e.key, e.v0, e.v1, NULL, NULL) != 0) ok = 0;
    }
    if (ok && (hash != checksum || tab->count != h.entries || fgetc(f) != EOF)) ok = 0;
    if (ferror(f)) ok = 0;
    fclose(f);
    if (!ok) ca_set_error("grumpy: checkpoint is truncated or corrupt");
    return ok;
}

static ca_status grumpy_solve_impl(const ca_group *g, const ca_elem *base, const ca_elem *target,
                                   uint64_t lo, uint64_t hi, const ca_grumpy_params *params,
                                   const char *checkpoint_path, uint32_t progress_interval,
                                   uint32_t checkpoint_interval, int verbose,
                                   uint64_t *x, ca_stats *st)
{
    ca_grumpy_params def;
    if (!params) { ca_grumpy_params_default(&def); params = &def; }
    ca_status rc = ca_resolve_interval(g, &lo, &hi);
    if (rc != CA_OK) return rc;
    double t0 = ca_now();
    uint64_t width = hi - lo;
    uint64_t n = g->order;
    grumpy_ctx c = { g, base, target, lo, hi, n, 0, 0 };
    uint64_t sq = ca_isqrt(width) + 1;
    uint64_t m = params->m;
    if (m == 0) {
        double alpha = params->alpha > 0 ? params->alpha : 0.7;
        m = (uint64_t)(alpha * (double)sq + 0.5);
        if (m < 1) m = 1;
    }
    c.m = m;
    if (n & 1) c.inv2 = ca_invmod(2, n);
    grumpy_checkpoint_header identity, saved = {0};
    grumpy_checkpoint_identity(&identity, &c);
    int existing = grumpy_checkpoint_probe(checkpoint_path, &identity, &saved);
    if (existing < 0) return CA_ERR_INVALID;

    /* shifted target H' = target - lo*base, and 2H' */
    ca_elem Hp, H2, t;
    uint64_t ops = 0;
    ca_group_mul(g, &t, base, lo, &ops);
    ca_group_inv(g, &t, &t);
    ca_group_op(g, &Hp, target, &t);
    ca_group_dbl(g, &H2, &Hp);
    ops += 2;
    ca_elem mG, m1G_neg;
    ca_group_mul(g, &mG, base, m, &ops);
    ca_group_op(g, &m1G_neg, &mG, base);
    ca_group_inv(g, &m1G_neg, &m1G_neg);
    ops += 1;

    ca_htab tab;
    if (ca_htab_init(&tab, (size_t)(3 * sq / 2 + 64)) != CA_OK) return CA_ERR_NOMEM;
    /* The three walks B (baby), U and V (giants) advance together through
     * the batched op, which on a curve shares one field inversion among
     * the three; results and counts are the three single ops'. */
    ca_elem walk[3] = {{{0}}, Hp, H2}, step[3] = {*base, mG, m1G_neg};
    ca_group_identity(g, &walk[0]);
    uint64_t scratch[6];
    uint64_t i = 0;
    double elapsed_prior = 0;
    rc = CA_ERR_INTERNAL;
    if (existing) {
        if (!grumpy_checkpoint_load(checkpoint_path, &saved, g, walk, &tab)) {
            rc = CA_ERR_INVALID;
            goto out;
        }
        i = saved.next_i;
        ops += saved.ops;
        elapsed_prior = saved.elapsed_seconds;
        if (saved.solved) {
            uint64_t candidate = saved.result;
            if (!ca_verify_log(g, base, target, candidate) ||
                !ca_fit_interval_base(g, base, &candidate, lo, hi)) {
                ca_set_error("grumpy: saved solution fails verification");
                rc = CA_ERR_INVALID;
                goto out;
            }
            *x = candidate;
            rc = CA_OK;
        }
    }
    int monitored = checkpoint_path != NULL || verbose;
    if (!progress_interval) progress_interval = 5;
    if (!checkpoint_interval) checkpoint_interval = 60;
    double next_progress = ca_now() + progress_interval;
    double next_checkpoint = ca_now() + checkpoint_interval;
    if (monitored &&
        (!grumpy_checkpoint_save(checkpoint_path, &identity, g, walk, &tab,
                                 i, ops, elapsed_prior + ca_now() - t0,
                                 rc == CA_OK, rc == CA_OK ? *x : 0) ||
         !dlog_ckpt_progress(checkpoint_path, "grumpy", "walk",
                             rc == CA_OK ? "ok" : "running",
                             elapsed_prior + ca_now() - t0, ops, i, tab.count, verbose))) {
        ca_set_error("grumpy: cannot persist progress");
        rc = CA_ERR_INTERNAL;
        goto out;
    }
    if (rc == CA_OK) goto out;
    /* Upper bound on iterations: the baby walk alone finds x' in at most
     * width+1 steps (it meets U_0 = H'). */
    uint64_t max_iter = width > UINT64_MAX - 2 ? UINT64_MAX : width + 2;
    for (; i < max_iter; i++) {
        for (int tpe = 0; tpe < 3; tpe++) {
            uint64_t ot, oi;
            int ir = ca_htab_insert(&tab, ca_group_hash(g, &walk[tpe]), (uint64_t)tpe, i, &ot, &oi);
            if (ir < 0) { rc = CA_ERR_NOMEM; goto finalize; }
            if (ir == 1) {
                if (grumpy_collide(&c, (int)ot, oi, tpe, i, x)) { rc = CA_OK; goto finalize; }
                /* same walk type re-visiting a point: happens only when the
                 * walk period divides a small order; keep going */
            }
        }
        ca_group_batch_op(g, walk, walk, step, 3, scratch);
        ops += 3;
        if (params->max_ops && ops > params->max_ops) {
            rc = CA_ERR_LIMIT;
            i++;
            goto finalize;
        }
        if (monitored && (i & 255u) == 0) {
            double now = ca_now();
            if (now >= next_progress) {
                if (!dlog_ckpt_progress(checkpoint_path, "grumpy", "walk", "running",
                                        elapsed_prior + now - t0, ops, i + 1,
                                        tab.count, verbose)) {
                    ca_set_error("grumpy: cannot persist progress");
                    rc = CA_ERR_INTERNAL;
                    goto out;
                }
                next_progress = now + progress_interval;
            }
            if (now >= next_checkpoint) {
                if (!grumpy_checkpoint_save(checkpoint_path, &identity, g, walk, &tab,
                                            i + 1, ops, elapsed_prior + now - t0, 0, 0)) {
                    rc = CA_ERR_INTERNAL;
                    goto out;
                }
                if (verbose && checkpoint_path) fprintf(stderr, "[grumpy] checkpoint saved\n");
                next_checkpoint = now + checkpoint_interval;
            }
        }
    }
    rc = CA_ERR_NOT_FOUND;
finalize:
    if (monitored &&
        (!grumpy_checkpoint_save(checkpoint_path, &identity, g, walk, &tab,
                                 i, ops, elapsed_prior + ca_now() - t0,
                                 rc == CA_OK, rc == CA_OK ? *x : 0) ||
         !dlog_ckpt_progress(checkpoint_path, "grumpy", "walk",
                             rc == CA_OK ? "ok" : "stopped",
                             elapsed_prior + ca_now() - t0, ops, i, tab.count, verbose))) {
        ca_set_error("grumpy: cannot persist final progress");
        rc = CA_ERR_INTERNAL;
    }
out:
    if (st) {
        st->group_ops += ops;
        st->iterations += i;
        st->table_entries = ca_max_u64(st->table_entries, tab.count);
        st->bytes_peak = ca_max_u64(st->bytes_peak, ca_htab_bytes(&tab));
        st->threads = 1;
        st->seconds += elapsed_prior + ca_now() - t0;
    }
    ca_htab_free(&tab);
    return rc;
}

ca_status ca_grumpy_solve(const ca_group *g, const ca_elem *base, const ca_elem *target,
                          uint64_t lo, uint64_t hi, const ca_grumpy_params *params,
                          uint64_t *x, ca_stats *st)
{
    return grumpy_solve_impl(g, base, target, lo, hi, params, NULL, 0, 0, 0, x, st);
}

ca_status ca_grumpy_solve_checkpointed(
    const ca_group *g, const ca_elem *base, const ca_elem *target,
    uint64_t lo, uint64_t hi, const ca_grumpy_params *params,
    const char *checkpoint_path, uint32_t progress_interval,
    uint32_t checkpoint_interval, int verbose, uint64_t *x, ca_stats *st)
{
    return grumpy_solve_impl(g, base, target, lo, hi, params, checkpoint_path,
                             progress_interval, checkpoint_interval, verbose, x, st);
}
