/*
 * pohlig.c - Pohlig-Hellman and solver dispatch.
 */
#include "cryptanalysis/ca_pohlig.h"
#include "dlog_internal.h"
#include "dlog_checkpoint_internal.h"

void ca_dlog_params_default(ca_dlog_params *p)
{
    memset(p, 0, sizeof(*p));
    p->solver = CA_SOLVER_AUTO;
    p->bsgs_max_prime = 1ULL << 36;
    ca_bsgs_params_default(&p->bsgs);
    ca_rho_params_default(&p->rho);
    ca_kangaroo_params_default(&p->kangaroo);
    ca_grumpy_params_default(&p->grumpy);
}

const char *ca_solver_name(ca_solver s)
{
    switch (s) {
    case CA_SOLVER_AUTO: return "auto";
    case CA_SOLVER_BSGS: return "bsgs";
    case CA_SOLVER_RHO: return "rho";
    case CA_SOLVER_KANGAROO: return "kangaroo";
    case CA_SOLVER_GRUMPY: return "grumpy";
    case CA_SOLVER_BRUTE: return "brute";
    }
    return "?";
}

/* Scan consecutive EC multiples in 64-point blocks.  Building the offsets
 * by doubling prefixes and translating a block both use one field inversion
 * per batch, while candidate comparisons retain their original order. */
static ca_status brute_force_ec_batch(const ca_group *g, const ca_elem *base,
                                      const ca_elem *target, uint64_t lo, uint64_t hi,
                                      const ca_elem *start, uint64_t *x, ca_stats *st)
{
    enum { LANES = 64 };
    ca_elem offsets[LANES], addends[LANES] = {0}, left[LANES] = {0}, candidates[LANES];
    uint64_t scratch[2 * LANES];
    ca_group_identity(g, &offsets[0]);
    offsets[1] = *base;
    for (size_t span = 2; span < LANES; span *= 2) {
        ca_elem offset;
        ca_group_dbl(g, &offset, &offsets[span / 2]);
        for (size_t i = 0; i < span; i++) addends[i] = offset;
        ca_group_batch_op(g, offsets + span, offsets, addends, span, scratch);
        if (st) st->group_ops += span + 1; /* additions and one doubling */
    }
    ca_elem stride, cur = *start;
    ca_group_dbl(g, &stride, &offsets[LANES / 2]);
    if (st) st->group_ops++;

    for (uint64_t k = lo;;) {
        uint64_t remaining = hi - k;
        size_t count = remaining < LANES ? (size_t)remaining + 1 : LANES;
        for (size_t i = 0; i < count; i++) left[i] = cur;
        ca_group_batch_op(g, candidates, left, offsets, count, scratch);
        if (st) st->group_ops += count; /* charge all computed candidates */
        for (size_t i = 0; i < count; i++) {
            if (ca_group_equal(g, &candidates[i], target)) {
                *x = k + i;
                return CA_OK;
            }
        }
        if (remaining < LANES) break;
        k += LANES;
        ca_group_op(g, &cur, &cur, &stride);
        if (st) st->group_ops++;
    }
    return CA_ERR_NOT_FOUND;
}

static ca_status brute_force(const ca_group *g, const ca_elem *base, const ca_elem *target,
                             uint64_t lo, uint64_t hi, uint64_t *x, ca_stats *st)
{
    ca_elem cur;
    ca_group_mul(g, &cur, base, lo, st ? &st->group_ops : NULL);
    if (g->kind == CA_GROUP_EC && hi - lo >= 63) {
        if (ca_group_equal(g, &cur, target)) { *x = lo; return CA_OK; }
        return brute_force_ec_batch(g, base, target, lo, hi, &cur, x, st);
    }
    for (uint64_t k = lo;; k++) {
        if (ca_group_equal(g, &cur, target)) { *x = k; return CA_OK; }
        if (k == hi) break;
        ca_group_op(g, &cur, &cur, base);
        if (st) st->group_ops++;
    }
    return CA_ERR_NOT_FOUND;
}

static ca_solver resolve_prime_solver(const ca_group *g, uint64_t lo, uint64_t hi,
                                       const ca_dlog_params *params)
{
    ca_solver s = params->solver;
    if (s == CA_SOLVER_AUTO) {
        uint64_t width = hi - lo;
        uint64_t limit = params->bsgs_max_prime ? params->bsgs_max_prime : (1ULL << 36);
        /* Keep the old brute behavior below 4096 when a caller caps BSGS
         * below this EC interval; the cap must not select kangaroo here. */
        if (width < 4096 &&
            (g->kind != CA_GROUP_EC || width < 256 || width > limit)) s = CA_SOLVER_BRUTE;
        else if (width <= limit) s = CA_SOLVER_BSGS;
        else if (lo == 0 && g->order && hi == g->order - 1) s = CA_SOLVER_RHO;
        else s = CA_SOLVER_KANGAROO;
    }
    return s;
}

ca_status ca_dlog_prime_order(const ca_group *g, const ca_elem *base, const ca_elem *target,
                              uint64_t lo, uint64_t hi, const ca_dlog_params *params,
                              uint64_t *x, ca_stats *st)
{
    ca_dlog_params def;
    if (!params) { ca_dlog_params_default(&def); params = &def; }
    ca_status rc = ca_resolve_interval(g, &lo, &hi);
    if (rc != CA_OK) return rc;
    ca_solver s = resolve_prime_solver(g, lo, hi, params);
    switch (s) {
    case CA_SOLVER_BRUTE:
        return brute_force(g, base, target, lo, hi, x, st);
    case CA_SOLVER_BSGS:
        return ca_bsgs_solve(g, base, target, lo, hi, &params->bsgs, x, st);
    case CA_SOLVER_KANGAROO:
        return ca_kangaroo_solve(g, base, target, lo, hi, &params->kangaroo, x, st);
    case CA_SOLVER_GRUMPY:
        return ca_grumpy_solve(g, base, target, lo, hi, &params->grumpy, x, st);
    case CA_SOLVER_RHO: {
        if (lo == 0 && g->order && hi == g->order - 1)
            return ca_rho_solve(g, base, target, &params->rho, x, st);
        /* rho on a sub-interval: solve in the full group and reduce */
        if (g->order == 0) return CA_ERR_INVALID;
        rc = ca_rho_solve(g, base, target, &params->rho, x, st);
        if (rc != CA_OK) return rc;
        /* modulo ord(base), not just modulo the group order: see the comment
         * on ca_fit_interval_base */
        if (!ca_fit_interval_base(g, base, x, lo, hi)) return CA_ERR_NOT_FOUND;
        return CA_OK;
    }
    default:
        return CA_ERR_INVALID;
    }
}

typedef struct ph_checkpoint {
    char magic[8];
    uint64_t version, identity, n, fi, k, result, modulus, xk, qk;
    ca_stats stats;
    uint64_t checksum;
} ph_checkpoint;

/* Feed semantic words in a fixed byte order. This matches the old raw-word
 * FNV input on the little-endian checkpoint platforms and avoids hashing any
 * object-representation padding. */
static uint64_t ph_hash_words(const uint64_t *words, size_t count, uint64_t h)
{
    for (size_t i = 0; i < count; i++) {
        uint64_t word = words[i];
        for (unsigned byte = 0; byte < 8; byte++) {
            h ^= (word >> (8 * byte)) & UINT64_C(0xff);
            h *= UINT64_C(1099511628211);
        }
    }
    return h;
}

static uint64_t ph_identity(const ca_group *g, const ca_elem *base,
                            const ca_elem *target, uint64_t n,
                            const ca_dlog_params *p)
{
    uint64_t bw[4] = {0}, tw[4] = {0}, alpha_bits;
    ca_group_decode(g, bw, base); ca_group_decode(g, tw, target);
    memcpy(&alpha_bits, &p->grumpy.alpha, sizeof(alpha_bits));
    uint64_t v[] = {
        g->kind, g->p, g->a, g->b, g->order, g->cofactor,
        g->endo_kind, g->aut_order, g->endo_lambda, g->endo_c_mont, n,
        bw[0], bw[1], bw[2], bw[3], tw[0], tw[1], tw[2], tw[3],
        (uint64_t)p->solver, p->bsgs_max_prime, p->bsgs.table_size,
        p->rho.threads, p->rho.r, (uint64_t)p->rho.dp_bits,
        p->rho.walks_per_thread, (uint64_t)p->rho.negation_map,
        p->rho.seed, p->rho.max_table_entries,
        p->kangaroo.herd_size, (uint64_t)p->kangaroo.dp_bits,
        p->kangaroo.jumps, p->kangaroo.seed,
        p->grumpy.m, alpha_bits
    };
    return ph_hash_words(v, sizeof(v) / sizeof(v[0]), UINT64_C(14695981039346656037));
}

static int ph_save(const char *path, ph_checkpoint *c)
{
    if (!path) return 1;
    c->checksum = 0;
    c->checksum = dlog_ckpt_hash(c, sizeof(*c), UINT64_C(14695981039346656037));
    dlog_ckpt_file f;
    int ok = dlog_ckpt_begin(&f, path);
    if (ok) ok = fwrite(c, sizeof(*c), 1, f.f) == 1;
    return dlog_ckpt_finish(&f, ok);
}

static ca_status ph_load(const char *path, ph_checkpoint *c, uint64_t identity,
                          uint64_t n, const ca_factorization *f)
{
    FILE *in = fopen(path, "rb");
    if (!in) {
        if (errno == ENOENT) return CA_OK;
        ca_set_error("cannot open dlog checkpoint");
        return CA_ERR_INTERNAL;
    }
    int ok = fread(c, sizeof(*c), 1, in) == 1 && fgetc(in) == EOF;
    fclose(in);
    uint64_t sum = c->checksum;
    c->checksum = 0;
    ok = ok && memcmp(c->magic, "CADLOGC1", 8) == 0 && c->version == 1 &&
         c->identity == identity && c->n == n && c->fi <= f->count &&
         c->modulus > 0 && n % c->modulus == 0 && c->result < c->modulus &&
         c->qk > 0 && c->xk < c->qk &&
         (c->fi == f->count ? c->k == 0 : c->k <= f->f[c->fi].e) &&
         sum == dlog_ckpt_hash(c, sizeof(*c), UINT64_C(14695981039346656037));
    if (!ok) {
        ca_set_error("dlog checkpoint is damaged or belongs to another run");
        return CA_ERR_INVALID;
    }
    return CA_OK;
}

static ca_status ph_solve_digit(const ca_group *g, const ca_elem *base,
                                const ca_elem *target, const ca_dlog_params *p,
                                const char *path, uint32_t progress_interval,
                                uint32_t checkpoint_interval, int verbose,
                                uint64_t *digit, ca_stats *st)
{
    ca_solver solver = resolve_prime_solver(g, 0, g->order - 1, p);
    switch (solver) {
    case CA_SOLVER_BRUTE:
        return brute_force(g, base, target, 0, g->order - 1, digit, st);
    case CA_SOLVER_BSGS:
        return ca_bsgs_solve_checkpointed(g, base, target, 0, g->order - 1,
                    &p->bsgs, path, progress_interval, checkpoint_interval,
                    verbose, digit, st);
    case CA_SOLVER_RHO:
        return ca_rho_solve_checkpointed(g, base, target, &p->rho, path,
                    progress_interval, checkpoint_interval, verbose, digit, st);
    case CA_SOLVER_KANGAROO:
        return ca_kangaroo_solve_checkpointed(g, base, target, 0, g->order - 1,
                    &p->kangaroo, path, progress_interval, checkpoint_interval,
                    verbose, digit, st);
    case CA_SOLVER_GRUMPY:
        return ca_grumpy_solve_checkpointed(g, base, target, 0, g->order - 1,
                    &p->grumpy, path, progress_interval, checkpoint_interval,
                    verbose, digit, st);
    default:
        ca_set_error("invalid Pohlig-Hellman digit solver");
        return CA_ERR_INVALID;
    }
}

static uint64_t ph_completed_digits(const ca_factorization *f, const ph_checkpoint *c)
{
    uint64_t total = c->k;
    for (uint64_t i = 0; i < c->fi; i++) total += f->f[i].e;
    return total;
}

ca_status ca_pohlig_hellman_checkpointed(const ca_group *g, const ca_elem *base,
                            const ca_elem *target, const ca_dlog_params *params,
                            const char *checkpoint_prefix, uint32_t progress_interval,
                            uint32_t checkpoint_interval, int verbose,
                            uint64_t *x, ca_stats *st)
{
    if (!progress_interval || !checkpoint_interval) {
        ca_set_error("dlog progress and checkpoint intervals must be positive");
        return CA_ERR_INVALID;
    }
    ca_dlog_params def;
    if (!params) { ca_dlog_params_default(&def); params = &def; }
    if (!g->order) {
        ca_set_error("Pohlig-Hellman requires the group order");
        return CA_ERR_INVALID;
    }
    double t0 = ca_now();
    uint64_t n = ca_group_elem_order(g, base);
    if (!n) n = g->order;
    if (!ca_check_members(g, base, target, n, "Pohlig-Hellman")) return CA_ERR_NOT_FOUND;
    ca_factorization f;
    ca_factorize(n, &f);
    ca_stats local_stats = {0};
    ca_stats *acc = st ? st : &local_stats;
    char *parent = checkpoint_prefix ? dlog_ckpt_path(checkpoint_prefix, ".ckpt") : NULL;
    if (checkpoint_prefix && !parent) return CA_ERR_NOMEM;
    ph_checkpoint c = {0};
    uint64_t identity = ph_identity(g, base, target, n, params);
    ca_status rc = parent ? ph_load(parent, &c, identity, n, &f) : CA_OK;
    if (rc != CA_OK) { free(parent); return rc; }
    if (!c.version) {
        memcpy(c.magic, "CADLOGC1", 8);
        c.version = 1; c.identity = identity; c.n = n;
        c.modulus = 1; c.qk = 1;
        c.stats = *acc;
        if (!ph_save(parent, &c)) {
            free(parent); ca_set_error("cannot persist dlog checkpoint");
            return CA_ERR_INTERNAL;
        }
    } else *acc = c.stats;
    double prior_seconds = acc->seconds;
    for (; c.fi < f.count;) {
        uint64_t q = f.f[c.fi].p;
        unsigned e = f.f[c.fi].e;
        uint64_t qe = 1;
        for (unsigned i = 0; i < e; i++) qe *= q;
        ca_elem base_e, target_e, gq;
        ca_group_mul(g, &base_e, base, n / qe, &acc->group_ops);
        ca_group_mul(g, &target_e, target, n / qe, &acc->group_ops);
        ca_group_mul(g, &gq, &base_e, qe / q, &acc->group_ops);
        ca_group sub = *g;
        sub.order = q;
        for (; c.k < e;) {
            ca_elem t, hk;
            ca_group_mul(g, &t, &base_e, c.xk, &acc->group_ops);
            ca_group_inv(g, &t, &t);
            ca_group_op(g, &hk, &target_e, &t);
            ca_group_mul(g, &hk, &hk, qe / (c.qk * q), &acc->group_ops);
            ca_solver solver = resolve_prime_solver(&sub, 0, q - 1, params);
            char phase[80];
            snprintf(phase, sizeof(phase), "factor-%" PRIu64 "-digit-%" PRIu64 "-%s",
                     c.fi + 1, c.k + 1, ca_solver_name(solver));
            if (verbose) fprintf(stderr, "[dlog] factor %" PRIu64 "/%u q=%" PRIu64
                                 " digit %" PRIu64 "/%u solver=%s\n", c.fi + 1,
                                 f.count, q, c.k + 1, e, ca_solver_name(solver));
            if (!dlog_ckpt_progress(parent, "dlog", phase, "running",
                                    prior_seconds + ca_now() - t0, acc->group_ops,
                                    ph_completed_digits(&f, &c), acc->table_entries, 0)) {
                rc = CA_ERR_INTERNAL; ca_set_error("cannot persist dlog progress");
                goto ph_done;
            }
            acc->seconds = prior_seconds + ca_now() - t0;
            c.stats = *acc;
            if (!ph_save(parent, &c)) {
                rc = CA_ERR_INTERNAL; ca_set_error("cannot persist dlog stage state");
                goto ph_done;
            }
            char *digit_path = NULL;
            if (checkpoint_prefix) {
                size_t len = strlen(checkpoint_prefix) + 80;
                digit_path = malloc(len);
                if (!digit_path) { rc = CA_ERR_NOMEM; goto ph_done; }
                snprintf(digit_path, len, "%s.factor%" PRIu64 ".digit%" PRIu64 ".ckpt",
                         checkpoint_prefix, c.fi, c.k);
            }
            uint64_t d = 0;
            rc = ph_solve_digit(&sub, &gq, &hk, params, digit_path,
                                progress_interval, checkpoint_interval, verbose, &d, acc);
            free(digit_path);
            if (rc != CA_OK) goto ph_done;
            c.xk += d * c.qk;
            c.qk *= q;
            c.k++;
            acc->seconds = prior_seconds + ca_now() - t0;
            c.stats = *acc;
            if (!ph_save(parent, &c)) {
                rc = CA_ERR_INTERNAL; ca_set_error("cannot persist completed dlog digit");
                goto ph_done;
            }
        }
        c.result = ca_crt2(c.result, c.modulus, c.xk, qe);
        c.modulus *= qe;
        c.fi++; c.k = 0; c.xk = 0; c.qk = 1;
        acc->seconds = prior_seconds + ca_now() - t0;
        c.stats = *acc;
        if (!ph_save(parent, &c)) {
            rc = CA_ERR_INTERNAL; ca_set_error("cannot persist completed dlog factor");
            goto ph_done;
        }
    }
    if (!ca_verify_log(g, base, target, c.result)) {
        ca_set_error("Pohlig-Hellman result failed verification (target not in <base>?)");
        rc = CA_ERR_NOT_FOUND;
        goto ph_done;
    }
    *x = c.result;
    rc = CA_OK;
    acc->seconds = prior_seconds + ca_now() - t0;
    c.stats = *acc;
    if (!ph_save(parent, &c)) {
        rc = CA_ERR_INTERNAL; ca_set_error("cannot persist final dlog checkpoint");
        goto ph_done;
    }
    if (!dlog_ckpt_progress(parent, "dlog", "complete", "complete",
                            prior_seconds + ca_now() - t0, acc->group_ops,
                            ph_completed_digits(&f, &c), acc->table_entries, verbose)) {
        rc = CA_ERR_INTERNAL; ca_set_error("cannot persist dlog final progress");
    }
ph_done:
    acc->seconds = prior_seconds + ca_now() - t0;
    /* Persist the aggregate even when a digit solver stops at its operation
     * cap.  The child checkpoint may omit the final unsaved tail; the parent
     * owns elapsed time across whole invocations and must retain it. */
    c.stats = *acc;
    if (!ph_save(parent, &c)) {
        rc = CA_ERR_INTERNAL;
        ca_set_error("cannot persist final dlog checkpoint");
    }
    if (rc != CA_OK)
        (void)dlog_ckpt_progress(parent, "dlog", "stopped", "stopped",
                                 acc->seconds, acc->group_ops,
                                 ph_completed_digits(&f, &c), acc->table_entries, verbose);
    free(parent);
    return rc;
}

ca_status ca_pohlig_hellman(const ca_group *g, const ca_elem *base, const ca_elem *target,
                            const ca_dlog_params *params, uint64_t *x, ca_stats *st)
{
    ca_dlog_params def;
    if (!params) { ca_dlog_params_default(&def); params = &def; }
    if (g->order == 0) {
        ca_set_error("Pohlig-Hellman requires the group order");
        return CA_ERR_INVALID;
    }
    double t0 = ca_now();
    /* Decompose by ord(base), not by the group order: when base generates a
     * proper subgroup (a non-cyclic curve group, or a base of smaller order)
     * some q^(e-1) * base_e is the identity and the digit solve below has no
     * answer.  The logarithm is only defined modulo ord(base) anyway. */
    uint64_t n = ca_group_elem_order(g, base);
    if (n == 0) n = g->order;
    /* ord(target) must divide ord(base); otherwise a rho digit solve in some
     * large prime subgroup would walk forever. */
    if (!ca_check_members(g, base, target, n, "Pohlig-Hellman")) return CA_ERR_NOT_FOUND;
    ca_factorization f;
    ca_factorize(n, &f);
    uint64_t result = 0, modulus = 1;
    for (unsigned fi = 0; fi < f.count; fi++) {
        uint64_t q = f.f[fi].p;
        unsigned e = f.f[fi].e;
        uint64_t qe = 1;
        for (unsigned k = 0; k < e; k++) qe *= q;
        /* work in the order-q^e subgroup: base_e = (n/q^e) base */
        ca_elem base_e, target_e, gq;
        ca_group_mul(g, &base_e, base, n / qe, st ? &st->group_ops : NULL);
        ca_group_mul(g, &target_e, target, n / qe, st ? &st->group_ops : NULL);
        /* gq = q^(e-1) * base_e has order q */
        ca_group_mul(g, &gq, &base_e, qe / q, st ? &st->group_ops : NULL);
        ca_group sub = *g;
        sub.order = q;
        uint64_t xk = 0, qk = 1;
        for (unsigned k = 0; k < e; k++) {
            /* h_k = (target_e - xk * base_e) * q^(e-1-k) */
            ca_elem t, hk;
            ca_group_mul(g, &t, &base_e, xk, st ? &st->group_ops : NULL);
            ca_group_inv(g, &t, &t);
            ca_group_op(g, &hk, &target_e, &t);
            ca_group_mul(g, &hk, &hk, qe / (qk * q), st ? &st->group_ops : NULL);
            uint64_t d;
            ca_status rc = ca_dlog_prime_order(&sub, &gq, &hk, 0, q - 1, params, &d, st);
            if (rc != CA_OK) return rc;
            xk += d * qk;
            qk *= q;
        }
        result = ca_crt2(result, modulus, xk, qe);
        modulus *= qe;
    }
    if (!ca_verify_log(g, base, target, result)) {
        ca_set_error("Pohlig-Hellman result failed verification (target not in <base>?)");
        return CA_ERR_NOT_FOUND;
    }
    *x = result;
    if (st) st->seconds = ca_now() - t0;
    return CA_OK;
}

ca_status ca_dlog(const ca_group *g, const ca_elem *base, const ca_elem *target, uint64_t *x,
                  ca_stats *st)
{
    return ca_pohlig_hellman(g, base, target, NULL, x, st);
}
