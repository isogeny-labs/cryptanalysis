/*
 * gpu_rho.c - generic driver for the GPU / emulated Pollard rho.
 *
 * The host builds the multiplier table, chooses the walk count and the
 * distinguished-point density, then repeatedly launches the kernel and
 * drains the DP buffer into a hash table.  A second arrival at a
 * distinguished point with different (a, b) solves the logarithm; the
 * same (a, b) means the walk cycled onto its own trail and it is re-seeded.
 */
#include "gpu_internal.h"
#include "dlog_internal.h"
#include "dlog_checkpoint_internal.h"

#include <stdio.h>

typedef struct gpu_rho_checkpoint_header {
    char magic[8];
    uint64_t p, a, b, order, cofactor, base[4], target[4];
    uint32_t kind, negmap, r, nthreads, dp_bits, tpb, requested_steps;
    uint32_t walks_per_thread, aux_words, entry_size, resolved_steps;
    uint64_t seed, resumes, ops, launches, dps, restarts, entries, result;
    double elapsed_seconds;
    uint32_t solved;
    uint64_t checksum;
} gpu_rho_checkpoint_header;

static void gpu_rho_checkpoint_identity(gpu_rho_checkpoint_header *h,
                                         const ca_group *g, const ca_elem *base,
                                         const ca_elem *target, const ca_gpu_rho_args *a,
                                         uint32_t tpb, uint32_t requested_steps,
                                         int dp_bits)
{
    memset(h, 0, sizeof(*h));
    memcpy(h->magic, "CAGPUDP1", 8);
    h->p = g->p; h->a = g->a; h->b = g->b; h->order = g->order;
    h->cofactor = g->cofactor;
    ca_group_decode(g, h->base, base);
    ca_group_decode(g, h->target, target);
    h->kind = a->kind; h->negmap = a->negmap; h->r = a->r;
    h->nthreads = a->nthreads; h->dp_bits = (uint32_t)dp_bits;
    h->tpb = tpb; h->requested_steps = requested_steps;
    h->walks_per_thread = CA_GPU_W; h->aux_words = CA_GPU_AUX;
    h->entry_size = sizeof(ca_htab_entry);
}

static int gpu_rho_checkpoint_same_run(const gpu_rho_checkpoint_header *a,
                                        const gpu_rho_checkpoint_header *b)
{
    return memcmp(a->magic, b->magic, 8) == 0 && a->p == b->p &&
           a->a == b->a && a->b == b->b && a->order == b->order &&
           a->cofactor == b->cofactor &&
           memcmp(a->base, b->base, sizeof(a->base)) == 0 &&
           memcmp(a->target, b->target, sizeof(a->target)) == 0 &&
           a->kind == b->kind && a->negmap == b->negmap && a->r == b->r &&
           a->nthreads == b->nthreads && a->dp_bits == b->dp_bits &&
           a->tpb == b->tpb && a->requested_steps == b->requested_steps &&
           a->walks_per_thread == b->walks_per_thread &&
           a->aux_words == b->aux_words && a->entry_size == b->entry_size;
}

static int gpu_rho_checkpoint_probe(const char *path,
                                     const gpu_rho_checkpoint_header *identity,
                                     uint64_t requested_seed,
                                     gpu_rho_checkpoint_header *saved)
{
    if (!path) return 0;
    FILE *f = fopen(path, "rb");
    if (!f) {
        if (errno == ENOENT) return 0;
        ca_set_error("gpu rho: cannot open checkpoint");
        return -1;
    }
    int ok = fread(saved, 1, sizeof(*saved), f) == sizeof(*saved) &&
             gpu_rho_checkpoint_same_run(saved, identity) && saved->seed &&
             (!requested_seed || saved->seed == requested_seed) &&
             saved->resolved_steps && saved->entries <= SIZE_MAX / sizeof(ca_htab_entry) &&
             saved->elapsed_seconds >= 0 && saved->resumes < UINT64_MAX;
    fclose(f);
    if (!ok) ca_set_error("gpu rho: checkpoint identity, format or seed does not match");
    return ok ? 1 : -1;
}

static int gpu_rho_checkpoint_load(const char *path,
                                    const gpu_rho_checkpoint_header *expected,
                                    ca_htab *tab, const ca_group *g,
                                    const ca_elem *base, const ca_elem *target)
{
    FILE *f = fopen(path, "rb");
    if (!f) { ca_set_error("gpu rho: cannot reopen checkpoint"); return 0; }
    gpu_rho_checkpoint_header h = {0};
    int ok = fread(&h, 1, sizeof(h), f) == sizeof(h) &&
             memcmp(&h, expected, sizeof(h)) == 0; /* NOLINT(bugprone-suspicious-memory-comparison,cert-exp42-c,cert-flp37-c): both headers are raw fread() bytes of the same file, padding included */
    uint64_t checksum = h.checksum;
    h.checksum = 0;
    uint64_t hash = dlog_ckpt_hash(&h, sizeof(h), UINT64_C(14695981039346656037));
    for (uint64_t i = 0; ok && i < h.entries; i++) {
        ca_htab_entry e;
        ok = fread(&e, 1, sizeof(e), f) == sizeof(e);
        if (ok) {
            hash = dlog_ckpt_hash(&e, sizeof(e), hash);
            ok = e.key && e.v0 < g->order && e.v1 < g->order &&
                 ca_htab_insert(tab, e.key, e.v0, e.v1, NULL, NULL) == 0;
        }
    }
    if (ok) ok = fgetc(f) == EOF && hash == checksum && tab->count == h.entries;
    fclose(f);
    if (ok && h.solved) ok = ca_verify_log(g, base, target, h.result);
    if (!ok) ca_set_error("gpu rho: checkpoint is damaged or incompatible");
    return ok;
}

static int gpu_rho_checkpoint_save(const char *path,
                                    const gpu_rho_checkpoint_header *identity,
                                    const ca_htab *tab, uint64_t seed, uint64_t resumes,
                                    uint64_t ops, uint64_t launches, uint64_t dps,
                                    uint64_t restarts, double elapsed, uint64_t result,
                                    int solved)
{
    if (!path) return 1;
    dlog_ckpt_file w;
    if (!dlog_ckpt_begin(&w, path)) {
        dlog_ckpt_finish(&w, 0);
        ca_set_error("gpu rho: cannot create checkpoint"); return 0;
    }
    gpu_rho_checkpoint_header h = *identity;
    h.seed = seed; h.resumes = resumes; h.ops = ops;
    h.launches = launches; h.dps = dps; h.restarts = restarts;
    h.entries = tab->count; h.elapsed_seconds = elapsed;
    h.result = result; h.solved = solved;
    uint64_t hash = dlog_ckpt_hash(&h, sizeof(h), UINT64_C(14695981039346656037));
    int ok = fwrite(&h, 1, sizeof(h), w.f) == sizeof(h);
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
    if (!ok) ca_set_error("gpu rho: cannot persist checkpoint");
    return ok;
}

static int gpu_rho_progress(const char *path, const char *backend, const char *status,
                             double elapsed, uint64_t ops, uint64_t launches,
                             uint64_t dps, uint64_t restarts, size_t entries, int verbose)
{
    if (verbose) fprintf(stderr, "[gpu-rho/%s] %.1fs launches=%" PRIu64
                         " ops=%" PRIu64 " dps=%" PRIu64 " entries=%zu restarts=%" PRIu64 "\n",
                         backend, elapsed, launches, ops, dps, entries, restarts);
    if (!path) return 1;
    char *progress_path = dlog_ckpt_path(path, ".progress.json");
    if (!progress_path) { ca_set_error("gpu rho: cannot allocate progress path"); return 0; }
    dlog_ckpt_file w;
    int ok = dlog_ckpt_begin(&w, progress_path);
    if (ok) ok = fprintf(w.f,
        "{\"status\":\"%s\",\"backend\":\"%s\",\"elapsed_seconds\":%.3f,"
        "\"group_ops\":%" PRIu64 ",\"launches\":%" PRIu64
        ",\"distinguished_points\":%" PRIu64 ",\"restarts\":%" PRIu64
        ",\"table_entries\":%zu}\n",
        status, backend, elapsed, ops, launches, dps, restarts, entries) > 0;
    ok = dlog_ckpt_finish(&w, ok);
    free(progress_path);
    if (!ok) ca_set_error("gpu rho: cannot persist progress");
    return ok;
}

void ca_gpu_rho_params_default(ca_gpu_rho_params *p)
{
    memset(p, 0, sizeof(*p));
    p->backend = CA_GPU_BACKEND_AUTO;
    p->dp_bits = -1;
    p->negation_map = 1;
}

const char *ca_gpu_backend_name(ca_gpu_backend b)
{
    switch (b) {
    case CA_GPU_BACKEND_AUTO: return "auto";
    case CA_GPU_BACKEND_CUDA: return "cuda";
    case CA_GPU_BACKEND_EMULATE: return "emulate";
    }
    return "?";
}

int ca_gpu_device_count(void) { return ca_gpu_cuda_device_count_impl(); }
int ca_gpu_device_name(int device, char *buf, size_t len)
{
    return ca_gpu_cuda_device_name_impl(device, buf, len);
}

static int ilog2u(uint64_t v)
{
    int l = -1;
    while (v) {
        v >>= 1;
        l++;
    }
    return l;
}

/* Solve from a collision between (a1,b1) and (a2,b2) at one canonical point. */
static int gpu_try_solve(const ca_group *g, const ca_elem *base, const ca_elem *target,
                         uint32_t negmap, uint64_t a1, uint64_t b1, uint64_t a2, uint64_t b2,
                         uint64_t *x)
{
    uint64_t n = g->order;
    for (unsigned sign = 0; sign < (negmap ? 2u : 1u); sign++) {
        uint64_t c, d;
        if (sign == 0) {
            c = ca_submod(b1, b2, n);
            d = ca_submod(a2, a1, n);
        } else {
            c = ca_addmod(b1, b2, n);
            d = n - ca_addmod(a1, a2, n);
            if (d == n) d = 0;
        }
        if (c == 0) continue;
        uint64_t gg = ca_gcd(c, n);
        if (d % gg) continue;
        uint64_t nn = n / gg;
        uint64_t x0 = ca_mulmod((d / gg) % nn, ca_invmod((c / gg) % nn, nn), nn);
        if (gg > 65536) gg = 65536;
        for (uint64_t k = 0; k < gg; k++) {
            uint64_t cand = x0 + k * nn;
            if (cand >= n) break;
            if (ca_verify_log(g, base, target, cand)) {
                *x = cand;
                return 1;
            }
        }
    }
    return 0;
}

static ca_status gpu_rho_solve(const ca_group *g, const ca_elem *base,
                               const ca_elem *target, const ca_gpu_rho_params *params,
                               const char *checkpoint_path, uint32_t progress_interval,
                               uint32_t checkpoint_interval, int verbose,
                               uint64_t *x, ca_stats *st)
{
    ca_gpu_rho_params def;
    if (!params) {
        ca_gpu_rho_params_default(&def);
        params = &def;
    }
    if (g->order == 0) {
        ca_set_error("GPU rho requires a known group order");
        return CA_ERR_INVALID;
    }
    double t0 = ca_now();
    uint64_t n = g->order;
    if (!ca_check_members(g, base, target, n, "gpu rho")) return CA_ERR_NOT_FOUND;

    /* Backend selection happens before the shortcuts below, so that asking
     * explicitly for CUDA fails predictably when CUDA is unavailable instead
     * of quietly answering from the CPU. */
    const ca_gpu_backend_ops *ops;
    switch (params->backend) {
    case CA_GPU_BACKEND_CUDA:
        if (!ca_gpu_cuda_compiled()) {
            ca_set_error("CUDA backend not compiled in (CA_CUDA=OFF)");
            return CA_ERR_UNSUPPORTED;
        }
        if (ca_gpu_device_count() <= params->device) {
            ca_set_error("no CUDA device %d", params->device);
            return CA_ERR_UNSUPPORTED;
        }
        ops = &ca_gpu_cuda_ops;
        break;
    case CA_GPU_BACKEND_EMULATE: ops = &ca_gpu_emulate_ops; break;
    default:
        ops = (ca_gpu_cuda_compiled() && ca_gpu_device_count() > params->device)
                  ? &ca_gpu_cuda_ops
                  : &ca_gpu_emulate_ops;
        break;
    }
    int on_gpu = ops == &ca_gpu_cuda_ops;

    if (ca_group_is_identity(g, target)) {
        *x = 0;
        return CA_OK;
    }
    if (n < 4096) {
        /* smaller than one launch is worth: brute force on the host */
        ca_elem cur;
        ca_group_identity(g, &cur);
        for (uint64_t k = 0; k < n; k++) {
            if (ca_group_equal(g, &cur, target)) {
                *x = k;
                if (st) {
                    st->group_ops += k;
                    st->seconds += ca_now() - t0;
                }
                return CA_OK;
            }
            ca_group_op(g, &cur, &cur, base);
        }
        return CA_ERR_NOT_FOUND;
    }

    ca_gpu_rho_args a;
    memset(&a, 0, sizeof(a));
    a.p = g->p;
    a.pinv = g->mont.pinv;
    a.one = g->mont.r1;
    a.a_mont = g->a_mont;
    a.n = n;
    a.kind = g->kind == CA_GROUP_EC ? CA_GPU_KIND_EC : CA_GPU_KIND_ZP;
    a.negmap = params->negation_map && g->kind == CA_GROUP_EC;
    a.seed = params->seed;
    /* internal (Montgomery) words of base and target */
    a.base_x = base->w[0];
    a.base_y = base->w[1];
    if (a.kind == CA_GPU_KIND_EC && base->w[2]) a.base_x = g->p;
    a.target_x = target->w[0];
    a.target_y = target->w[1];
    if (a.kind == CA_GPU_KIND_EC && target->w[2]) a.target_x = g->p;

    uint64_t sqrt_n = ca_isqrt(n) + 1;
    int lg = ilog2u(n) + 1;
    /* multiplier count: the table is built on the host (cheap), so use the
     * large tables that keep fruitless cycles rare whenever the group is
     * big enough for them to matter (r <= sqrt(n)/64). */
    if (params->r)
        a.r = params->r;
    else {
        uint64_t budget = sqrt_n / 64;
        uint32_t r = 8, cap = a.negmap ? 1024u : 64u;
        while ((uint64_t)r * 2 <= budget && r * 2 <= cap) r *= 2;
        a.r = r;
    }
    if (a.r < 4) a.r = 4;
    /* thread count: every walk start costs ~3 log2(n) operations; keep the
     * total under sqrt(n)/8.  Threads beyond nthreads in the last block
     * exit immediately, so small groups do not pay for a full block. */
    /* Only the thread count is chosen here; each backend derives its own
     * block count from it and from threads_per_block. */
    uint32_t tpb = params->threads_per_block ? params->threads_per_block : 128;
    uint64_t nthreads;
    if (params->blocks == 0) {
        uint64_t walks_cap = sqrt_n / (24u * (uint64_t)lg);
        uint64_t threads_cap = walks_cap / CA_GPU_W;
        if (threads_cap < 1) threads_cap = 1;
        uint64_t want = on_gpu ? (uint64_t)tpb * 1024 : (uint64_t)tpb * 4;
        nthreads = want > threads_cap ? threads_cap : want;
    } else {
        nthreads = (uint64_t)params->blocks * tpb;
    }
    a.nthreads = (uint32_t)nthreads;
    uint64_t nwalks = (uint64_t)a.nthreads * CA_GPU_W;
    /* distinguished points: ~32 per walk over the expected run, at most 2^24 total */
    double expected = 1.25 * (double)sqrt_n / (a.negmap ? 1.4142 : 1.0);
    int dp = params->dp_bits;
    if (dp < 0) {
        double per_walk = expected / (32.0 * (double)nwalks);
        dp = per_walk >= 2.0 ? ilog2u((uint64_t)per_walk) : 0;
        int min_dp = ilog2u((uint64_t)expected) - 24;
        if (dp < min_dp) dp = min_dp;
        if (dp < 0) dp = 0;
        if (dp > 48) dp = 48;
    }
    /* An explicitly requested dp_bits is honoured, but a shift of 64 or more
     * is undefined, so clamp it.  (Anything near this makes distinguished
     * points so rare that a work limit is essential; see ca_gpu.h.) */
    if (dp > 63) dp = 63;
    a.dp_mask = dp ? ((1ULL << dp) - 1) : 0;
    a.abandon_shift = (uint32_t)dp;
    gpu_rho_checkpoint_header identity, saved;
    gpu_rho_checkpoint_identity(&identity, g, base, target, &a, tpb,
                                 params->steps_per_launch, dp);
    int existing = gpu_rho_checkpoint_probe(checkpoint_path, &identity,
                                             params->seed, &saved);
    if (existing < 0) return CA_ERR_INTERNAL;
    a.seed = existing ? saved.seed : ca_seed_or_random(params->seed);
    uint32_t steps = params->steps_per_launch;
    if (existing) steps = saved.resolved_steps;
    else if (steps == 0) {
        /* Aim at about 1/16 of the expected work per launch, but run at least
         * long enough that the herd is likely to report a distinguished point
         * (one per 2^dp steps, spread over nwalks walks). */
        double per = expected / (16.0 * (double)nwalks);
        double dp_floor = (double)(1ULL << (dp > 40 ? 40 : dp)) / (double)nwalks;
        if (per < dp_floor) per = dp_floor;
        if (per < 64) per = 64;
        /* A launch is not interruptible and max_ops is only checked between
         * launches, so never put more than the whole expected run - or the
         * whole work limit - into one of them.  Without this an unusual
         * dp_bits makes a single launch dwarf the entire search. */
        double whole_run = expected / (double)nwalks + 64;
        if (per > whole_run) per = whole_run;
        if (params->max_ops) {
            double limit = (double)params->max_ops / (double)nwalks + 1;
            if (per > limit) per = limit;
        }
        if (per > 1e7) per = 1e7;
        steps = per < 1 ? 1 : (uint32_t)per;
    }
    a.steps = steps;
    identity.resolved_steps = steps;
    /* DP buffer for one launch: twice the expected count plus slack, and
     * hard-capped so that a large group cannot ask for a huge allocation.
     * Overflowing the buffer is safe by construction: the kernel drops the
     * excess (it only writes slots below dp_cap) and the host clamps the
     * count, so an overflow costs work, never correctness. */
    double exp_dps = (double)nwalks * steps / (double)(1ULL << dp);
    uint64_t cap = (uint64_t)(exp_dps * 2) + 4096;
    if (cap > (1u << 20)) cap = 1u << 20;
    a.dp_cap = (uint32_t)cap;

    /* multipliers (host) */
    uint64_t *mult = malloc((size_t)a.r * 4 * sizeof(uint64_t));
    if (!mult) return CA_ERR_NOMEM;
    ca_rng rng;
    ca_rng_seed(&rng, a.seed);
    uint64_t setup_ops = 0;
    for (uint32_t i = 0; i < a.r; i++) {
        uint64_t al = ca_rng_below(&rng, n), be = ca_rng_below(&rng, n);
        ca_elem t1, t2, m;
        ca_group_mul(g, &t1, base, al, &setup_ops);
        ca_group_mul(g, &t2, target, be, &setup_ops);
        ca_group_op(g, &m, &t1, &t2);
        uint64_t *slot = mult + 4 * (size_t)i;
        slot[0] = (a.kind == CA_GPU_KIND_EC && m.w[2]) ? g->p : m.w[0];
        slot[1] = m.w[1];
        slot[2] = al;
        slot[3] = be;
    }
    a.mult = mult;
    uint64_t resumes = existing ? saved.resumes + 1 : 0;
    /* Keep multiplier coefficients fixed, but give every resumed run fresh
     * walk starts. Earlier distinguished points remain valid for this table. */
    if (existing) a.seed = ca_mix64(a.seed ^ ca_mix64(resumes));

    void *ctx = NULL;
    ca_status rc = ops->create(&a, tpb, params->device, &ctx);
    if (rc != CA_OK) {
        free(mult);
        return rc;
    }
    ca_htab tab;
    if (ca_htab_init(&tab, (size_t)(expected / (double)(1ULL << dp)) + 4096) != CA_OK) {
        ops->destroy(ctx);
        free(mult);
        return CA_ERR_NOMEM;
    }
    uint64_t total_ops = setup_ops, launches = 0, dps_total = 0, restarts = 0;
    double elapsed_prior = 0;
    int checkpoint_ready = !existing;
    int monitor = checkpoint_path || verbose;
    rc = CA_ERR_INTERNAL;
    if (existing) {
        if (!gpu_rho_checkpoint_load(checkpoint_path, &saved, &tab, g, base, target))
            goto finish;
        total_ops += saved.ops;
        launches = saved.launches;
        dps_total = saved.dps;
        restarts = saved.restarts;
        elapsed_prior = saved.elapsed_seconds;
        checkpoint_ready = 1;
        if (saved.solved) { *x = saved.result; rc = CA_OK; goto finish; }
    }
    double next_progress = ca_now() + (progress_interval ? progress_interval : 5);
    double next_checkpoint = ca_now() + (checkpoint_interval ? checkpoint_interval : 60);
    if (monitor && !gpu_rho_progress(checkpoint_path, ops->name, "running",
                                      elapsed_prior + ca_now() - t0, total_ops,
                                      launches, dps_total, restarts, tab.count, verbose))
        goto finish;
    if (params->max_ops && total_ops > params->max_ops) {
        rc = CA_ERR_LIMIT;
        goto finish;
    }
    for (;;) {
        const uint64_t *dps;
        uint32_t count;
        ca_status lrc = ops->launch(ctx, &dps, &count);
        if (lrc != CA_OK) {
            rc = lrc;
            break;
        }
        launches++;
        /* One walk step is one group operation.  Retried steps (negation-map
         * look-ahead) really do perform an operation, so they belong here;
         * the rare cycle-escape walk is device-side and is not counted, so
         * this is a very slight undercount when escapes happen. */
        total_ops += nwalks * steps;
        dps_total += count;
        int done = 0;
        for (uint32_t i = 0; i < count && !done; i++) {
            const uint64_t *rec = dps + 4 * (size_t)i;
            uint64_t h = rec[0], da = rec[1], db = rec[2];
            uint32_t wid = (uint32_t)rec[3];
            uint64_t oa, ob;
            int ir = ca_htab_insert(&tab, h, da, db, &oa, &ob);
            if (ir < 0) {
                rc = CA_ERR_NOMEM;
                done = 1;
                break;
            }
            if (ir == 1) {
                /* Identical (a, b) means the walk rediscovered its own trail;
                 * a different pair that yields no logarithm is an unusable
                 * relation.  Either way the walk is re-seeded. */
                int same_trail = oa == da && ob == db;
                if (!same_trail && gpu_try_solve(g, base, target, a.negmap, oa, ob, da, db, x)) {
                    rc = CA_OK;
                    done = 1;
                } else {
                    ops->restart(ctx, wid);
                    restarts++;
                }
            }
        }
        if (done) break;
        double now = monitor ? ca_now() : 0;
        if (monitor && now >= next_progress) {
            if (!gpu_rho_progress(checkpoint_path, ops->name, "running",
                                  elapsed_prior + now - t0, total_ops, launches,
                                  dps_total, restarts, tab.count, verbose)) {
                rc = CA_ERR_INTERNAL;
                break;
            }
            next_progress = now + (progress_interval ? progress_interval : 5);
        }
        if (checkpoint_path && now >= next_checkpoint) {
            if (!gpu_rho_checkpoint_save(checkpoint_path, &identity, &tab,
                                         existing ? saved.seed : a.seed, resumes,
                                         total_ops, launches, dps_total, restarts,
                                         elapsed_prior + now - t0, 0, 0)) {
                rc = CA_ERR_INTERNAL;
                break;
            }
            next_checkpoint = now + (checkpoint_interval ? checkpoint_interval : 60);
        }
        if (params->max_ops && total_ops > params->max_ops) {
            rc = CA_ERR_LIMIT;
            break;
        }
    }
finish:
    if (checkpoint_ready) {
        double elapsed = elapsed_prior + ca_now() - t0;
        if (checkpoint_path && !gpu_rho_checkpoint_save(checkpoint_path, &identity,
                &tab, existing ? saved.seed : a.seed, resumes, total_ops,
                launches, dps_total, restarts, elapsed, rc == CA_OK ? *x : 0,
                rc == CA_OK)) rc = CA_ERR_INTERNAL;
        if (monitor && !gpu_rho_progress(checkpoint_path, ops->name,
                rc == CA_OK ? "ok" : "stopped", elapsed, total_ops,
                launches, dps_total, restarts, tab.count, verbose))
            rc = CA_ERR_INTERNAL;
    }
    if (st) {
        st->group_ops += total_ops;
        st->iterations += dps_total;
        st->collisions += restarts;
        st->table_entries = ca_max_u64(st->table_entries, tab.count);
        st->bytes_peak =
            ca_max_u64(st->bytes_peak, ca_htab_bytes(&tab) + nwalks * 96 + (uint64_t)a.dp_cap * 32);
        st->threads = a.nthreads;
        st->reserved = (uint32_t)launches;
        st->seconds += elapsed_prior + ca_now() - t0;
    }
    ca_htab_free(&tab);
    ops->destroy(ctx);
    free(mult);
    return rc;
}

ca_status ca_gpu_rho_solve(const ca_group *g, const ca_elem *base, const ca_elem *target,
                            const ca_gpu_rho_params *params, uint64_t *x, ca_stats *st)
{
    return gpu_rho_solve(g, base, target, params, NULL, 0, 0, 0, x, st);
}

ca_status ca_gpu_rho_solve_checkpointed(const ca_group *g, const ca_elem *base,
                                         const ca_elem *target, const ca_gpu_rho_params *params,
                                         const char *checkpoint_path,
                                         uint32_t progress_interval,
                                         uint32_t checkpoint_interval, int verbose,
                                         uint64_t *x, ca_stats *st)
{
    return gpu_rho_solve(g, base, target, params, checkpoint_path,
                          progress_interval, checkpoint_interval, verbose, x, st);
}
