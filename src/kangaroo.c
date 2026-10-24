/*
 * kangaroo.c - van Oorschot-Wiener parallel kangaroos (run in one thread
 * with batched group operations).
 *
 * Positions are tracked as integers (exponents); tame kangaroos start at
 * lo + width/2 + small offsets, wild kangaroos start at target + small
 * offsets.  Jump j of size s_j = 2^j is chosen by the element hash.  When
 * a tame and a wild kangaroo land on the same distinguished point,
 * x = tame_position - wild_distance.
 */
#include "cryptanalysis/ca_kangaroo.h"
#include "dlog_internal.h"

#include <errno.h>
#include <fcntl.h>
#include <inttypes.h>
#include <math.h>
#include <stddef.h>
#include <stdio.h>
#include <sys/stat.h>
#include <unistd.h>

void ca_kangaroo_params_default(ca_kangaroo_params *p)
{
    memset(p, 0, sizeof(*p));
    p->dp_bits = -1;
}

typedef struct roo {
    ca_elem Y;
    uint64_t dist;    /* tame: absolute exponent; wild: offset from x */
    uint64_t since_dp;
} roo;

typedef struct k_lane_record {
    uint64_t words[4];
    uint64_t dist, since_dp;
} k_lane_record;

/* Native snapshot: the identity prefix is compared before any saved state is
 * used.  Canonical point words avoid persisting Montgomery internals. */
typedef struct k_checkpoint_header {
    char magic[8];
    uint64_t p, a, b, order, cofactor;
    uint64_t base[4], target[4], lo, hi;
    uint32_t kind, endo_kind, aut_order, herd, jumps, dp_bits;
    uint32_t lane_size, entry_size;
    uint64_t endo_lambda, endo_c_mont;
    uint64_t seed, rng[4], ops, dps, restarts, entries, result;
    double elapsed_seconds;
    uint32_t solved;
    uint64_t checksum;
} k_checkpoint_header;

static uint64_t k_hash_bytes(const void *data, size_t n, uint64_t hash)
{
    const unsigned char *p = data;
    for (size_t i = 0; i < n; i++) { hash ^= p[i]; hash *= UINT64_C(1099511628211); }
    return hash;
}

static char *k_path(const char *path, const char *suffix)
{
    size_t n = strlen(path) + strlen(suffix) + 1;
    char *out = malloc(n);
    if (out) snprintf(out, n, "%s%s", path, suffix);
    return out;
}

static int k_sync_parent(const char *path)
{
    char *dir = strdup(path);
    if (!dir) return 0;
    const char *parent = dir;
    char *slash = strrchr(dir, '/');
    if (slash) {
        if (slash == dir) slash[1] = '\0';
        else *slash = '\0';
    } else parent = ".";
    int fd = open(parent, O_RDONLY);
    int ok = fd >= 0 && fsync(fd) == 0;
    if (fd >= 0) close(fd);
    free(dir);
    return ok;
}

static void k_identity(k_checkpoint_header *h, const ca_group *g,
                       const ca_elem *base, const ca_elem *target,
                       uint64_t lo, uint64_t hi, uint32_t herd, uint32_t jumps, int dp)
{
    memset(h, 0, sizeof(*h));
    memcpy(h->magic, "CAKANG01", 8);
    h->p = g->p; h->a = g->a; h->b = g->b;
    h->order = g->order; h->cofactor = g->cofactor;
    ca_group_decode(g, h->base, base);
    ca_group_decode(g, h->target, target);
    h->lo = lo; h->hi = hi;
    h->kind = g->kind; h->endo_kind = g->endo_kind;
    h->aut_order = g->aut_order; h->endo_lambda = g->endo_lambda;
    h->endo_c_mont = g->endo_c_mont;
    h->herd = herd; h->jumps = jumps; h->dp_bits = (uint32_t)dp;
    h->lane_size = sizeof(k_lane_record); h->entry_size = sizeof(ca_htab_entry);
}

static int k_probe(const char *path, const k_checkpoint_header *want,
                   k_checkpoint_header *saved, uint64_t requested_seed)
{
    if (!path) return 0;
    FILE *f = fopen(path, "rb");
    if (!f) {
        if (errno == ENOENT) return 0;
        ca_set_error("kangaroo: cannot open checkpoint");
        return -1;
    }
    int ok = fread(saved, 1, sizeof(*saved), f) == sizeof(*saved) &&
             memcmp(saved, want, offsetof(k_checkpoint_header, seed)) == 0 &&
             saved->seed != 0 && saved->ops >= saved->dps &&
             saved->entries <= saved->dps && saved->elapsed_seconds >= 0 &&
             isfinite(saved->elapsed_seconds) &&
             (!requested_seed || requested_seed == saved->seed);
    fclose(f);
    if (!ok) {
        ca_set_error("kangaroo: checkpoint identity or format does not match");
        return -1;
    }
    return 1;
}

static int k_save(const char *path, const k_checkpoint_header *identity,
                  const ca_group *g, const roo *roos, uint32_t total,
                  const ca_htab *tab, const ca_rng *rng, uint64_t seed,
                  uint64_t ops, uint64_t dps, uint64_t restarts,
                  double elapsed, int solved, uint64_t result)
{
    if (!path) return 1;
    char *tmp = k_path(path, ".tmp.XXXXXX");
    if (!tmp) { ca_set_error("kangaroo: out of memory for checkpoint path"); return 0; }
    int fd = mkstemp(tmp);
    FILE *f = fd >= 0 ? fdopen(fd, "wb+") : NULL;
    if (!f && fd >= 0) close(fd);
    int ok = f != NULL;
    k_checkpoint_header h = *identity;
    h.seed = seed;
    memcpy(h.rng, rng->s, sizeof(h.rng));
    h.ops = ops; h.dps = dps; h.restarts = restarts; h.entries = tab->count;
    h.elapsed_seconds = elapsed; h.solved = solved; h.result = result;
    h.checksum = 0;
    uint64_t hash = k_hash_bytes(&h, sizeof(h), UINT64_C(14695981039346656037));
    if (ok) ok = fwrite(&h, 1, sizeof(h), f) == sizeof(h);
    for (uint32_t i = 0; ok && i < total; i++) {
        k_lane_record rec = {0};
        ca_group_decode(g, rec.words, &roos[i].Y);
        rec.dist = roos[i].dist; rec.since_dp = roos[i].since_dp;
        hash = k_hash_bytes(&rec, sizeof(rec), hash);
        ok = fwrite(&rec, 1, sizeof(rec), f) == sizeof(rec);
    }
    for (size_t i = 0; ok && i < tab->cap; i++) {
        const ca_htab_entry *e = &tab->e[i];
        if (!e->key) continue;
        hash = k_hash_bytes(e, sizeof(*e), hash);
        ok = fwrite(e, 1, sizeof(*e), f) == sizeof(*e);
    }
    if (ok) {
        h.checksum = hash;
        ok = fseek(f, 0, SEEK_SET) == 0 && fwrite(&h, 1, sizeof(h), f) == sizeof(h) &&
             fflush(f) == 0 && fsync(fileno(f)) == 0;
    }
    if (f && fclose(f) != 0) ok = 0;
    if (ok) ok = rename(tmp, path) == 0 && k_sync_parent(path);
    if (!ok) { unlink(tmp); ca_set_error("kangaroo: cannot persist checkpoint"); }
    free(tmp);
    return ok;
}

static int k_load(const char *path, const k_checkpoint_header *saved,
                  const ca_group *g, roo *roos, uint64_t *hs, uint32_t total,
                  ca_htab *tab, ca_rng *rng)
{
    FILE *f = fopen(path, "rb");
    if (!f) { ca_set_error("kangaroo: cannot reopen checkpoint"); return 0; }
    k_checkpoint_header h = {0};
    int ok = fread(&h, 1, sizeof(h), f) == sizeof(h) &&
             memcmp(&h, saved, sizeof(h)) == 0; /* NOLINT(bugprone-suspicious-memory-comparison,cert-exp42-c,cert-flp37-c): both headers are raw fread() bytes of the same file, padding included */
    struct stat fs;
    uint64_t prefix = sizeof(h) + (uint64_t)total * sizeof(k_lane_record);
    if (h.entries > (UINT64_MAX - prefix) / sizeof(ca_htab_entry)) ok = 0;
    uint64_t expected = ok ? prefix + h.entries * sizeof(ca_htab_entry) : 0;
    if (!ok || fstat(fileno(f), &fs) != 0 || fs.st_size < 0 ||
        expected != (uint64_t)fs.st_size) ok = 0;
    uint64_t checksum = h.checksum;
    h.checksum = 0;
    uint64_t hash = k_hash_bytes(&h, sizeof(h), UINT64_C(14695981039346656037));
    for (uint32_t i = 0; ok && i < total; i++) {
        k_lane_record rec;
        if (fread(&rec, 1, sizeof(rec), f) != sizeof(rec) ||
            !ca_group_encode(g, &roos[i].Y, rec.words)) { ok = 0; break; }
        hash = k_hash_bytes(&rec, sizeof(rec), hash);
        roos[i].dist = rec.dist; roos[i].since_dp = rec.since_dp;
        hs[i] = ca_group_hash(g, &roos[i].Y);
    }
    for (uint64_t i = 0; ok && i < h.entries; i++) {
        ca_htab_entry e;
        if (fread(&e, 1, sizeof(e), f) != sizeof(e) || !e.key || e.v1 > 1) {
            ok = 0; break;
        }
        hash = k_hash_bytes(&e, sizeof(e), hash);
        if (ca_htab_insert(tab, e.key, e.v0, e.v1, NULL, NULL) != 0) ok = 0;
    }
    if (ok && (hash != checksum || tab->count != h.entries || fgetc(f) != EOF)) ok = 0;
    if (ferror(f)) ok = 0;
    fclose(f);
    if (!ok) { ca_set_error("kangaroo: checkpoint is truncated or corrupt"); return 0; }
    memcpy(rng->s, h.rng, sizeof(rng->s));
    if (!(rng->s[0] | rng->s[1] | rng->s[2] | rng->s[3])) {
        ca_set_error("kangaroo: checkpoint has invalid RNG state");
        return 0;
    }
    return 1;
}

static int k_progress(const char *path, int verbose, double elapsed,
                      uint64_t ops, uint64_t dps, uint64_t restarts,
                      size_t entries, const char *status)
{
    if (verbose) fprintf(stderr, "[kangaroo] %.1fs ops=%" PRIu64 " dps=%" PRIu64
                         " entries=%zu restarts=%" PRIu64 "\n",
                         elapsed, ops, dps, entries, restarts);
    if (!path) return 1;
    char *out = k_path(path, ".progress.json");
    char *tmp = k_path(path, ".progress.tmp.XXXXXX");
    if (!out || !tmp) { free(out); free(tmp); return 0; }
    int fd = mkstemp(tmp);
    int ok = fd >= 0 && dprintf(fd,
        "{\"status\":\"%s\",\"elapsed_seconds\":%.3f,\"group_ops\":%" PRIu64
        ",\"distinguished_points\":%" PRIu64 ",\"table_entries\":%zu,"
        "\"restarts\":%" PRIu64 "}\n", status, elapsed, ops, dps, entries, restarts) > 0 &&
        fsync(fd) == 0;
    if (fd >= 0 && close(fd) != 0) ok = 0;
    if (ok) ok = rename(tmp, out) == 0 && k_sync_parent(out);
    if (!ok) { unlink(tmp); ca_set_error("kangaroo: cannot persist progress"); }
    free(out); free(tmp);
    return ok;
}

static ca_status k_solve_impl(const ca_group *g, const ca_elem *base, const ca_elem *target,
                              uint64_t lo, uint64_t hi, const ca_kangaroo_params *params,
                              const char *checkpoint_path, uint32_t progress_interval,
                              uint32_t checkpoint_interval, int verbose,
                              uint64_t *x, ca_stats *st)
{
    ca_kangaroo_params def;
    if (!params) { ca_kangaroo_params_default(&def); params = &def; }
    ca_status rc = ca_resolve_interval(g, &lo, &hi);
    if (rc != CA_OK) return rc;
    double t0 = ca_now();
    uint64_t width = hi - lo; /* inclusive count minus one */
    uint64_t n = g->order;

    /* tiny interval: linear scan */
    if (width < 256) {
        ca_elem cur;
        ca_group_mul(g, &cur, base, lo, st ? &st->group_ops : NULL);
        for (uint64_t k = 0; k <= width; k++) {
            if (ca_group_equal(g, &cur, target)) {
                *x = lo + k;
                if (st) { st->group_ops += k; st->seconds += ca_now() - t0; }
                return CA_OK;
            }
            ca_group_op(g, &cur, &cur, base);
        }
        return CA_ERR_NOT_FOUND;
    }

    /* Past the linear scan the walk needs a target that some x * base can
     * equal: with the identity as base (or a target outside the order-n
     * subgroup) no hop ever reaches a tame/wild collision that verifies, and
     * the loop below would run until max_ops, or forever without one. */
    if (ca_group_is_identity(g, base)) {
        if (ca_group_is_identity(g, target)) {
            *x = lo;
            if (st) st->seconds += ca_now() - t0;
            return CA_OK;
        }
        ca_set_error("kangaroo: the base is the identity and the target is not");
        return CA_ERR_NOT_FOUND;
    }
    if (n && !ca_check_members(g, base, target, n, "kangaroo")) return CA_ERR_NOT_FOUND;

    uint64_t sqrt_w = ca_isqrt(width) + 1;
    uint32_t herd = params->herd_size;
    /* 2 * herd must not wrap, and the herd arrays are allocated up front:
     * CA_KANGAROO_MAX_HERD kangaroos per herd is already 64 MB of state. */
    if (herd > CA_KANGAROO_MAX_HERD) herd = CA_KANGAROO_MAX_HERD;
    if (herd == 0) {
        /* each kangaroo start costs ~1.5 log2(n) operations; keep the total
         * start-up under sqrt(width)/8 */
        herd = (g->kind == CA_GROUP_EC) ? 64 : 8;
        unsigned lg = 1;
        for (uint64_t t = n ? n : width; t > 1; t >>= 1) lg++;
        uint64_t cap = sqrt_w / (24u * (uint64_t)lg);
        if (cap < 1) cap = 1;
        if (herd > cap) herd = (uint32_t)cap;
    }
    uint32_t total = 2 * herd;
    /* mean jump ~ total * sqrt(width) / 4 (vOW), realised with powers of two */
    double mean_target = (double)total * (double)sqrt_w / 4.0;
    if (mean_target < 2) mean_target = 2;
    uint32_t nj = params->jumps;
    if (nj == 0) {
        nj = 1;
        while (nj < 63 && ((double)((1ULL << nj) - 1) / (double)nj) < mean_target) nj++;
    }
    if (nj > 62) nj = 62;
    int dp = params->dp_bits;
    if (dp > 62) dp = 62; /* dp is a shift count for a 64-bit mask */
    if (dp < 0) {
        double expected = 2.0 * (double)sqrt_w; /* total jumps */
        double per_roo = expected / (32.0 * total);
        dp = 0;
        while (per_roo >= 2.0 && dp < 40) { per_roo /= 2; dp++; }
    }
    uint64_t dp_mask = dp ? ((1ULL << dp) - 1) : 0;
    k_checkpoint_header identity, saved = {0};
    k_identity(&identity, g, base, target, lo, hi, herd, nj, dp);
    int existing = k_probe(checkpoint_path, &identity, &saved, params->seed);
    if (existing < 0) return CA_ERR_INVALID;
    uint64_t seed = existing ? saved.seed : ca_seed_or_random(params->seed);

    /* jump table */
    ca_elem *J = calloc(nj, sizeof(ca_elem));
    uint64_t *jsz = calloc(nj, sizeof(uint64_t));
    roo *roos = calloc(total, sizeof(roo));
    ca_elem *Yn = calloc(total, sizeof(ca_elem));
    ca_elem *B = calloc(total, sizeof(ca_elem));
    uint64_t *scratch = calloc(2 * (size_t)total, sizeof(uint64_t));
    uint32_t *jidx = calloc(total, sizeof(uint32_t));
    /* hs[i] is the hash of roos[i].Y, recomputed only where Y changes: a
     * hop needs it for the distinguished-point test and again for the
     * next jump, and hashing twice was a third of a Z_p hop. */
    uint64_t *hs = calloc(total, sizeof(uint64_t));
    ca_htab tab;
    if (!J || !jsz || !roos || !Yn || !B || !scratch || !jidx || !hs ||
        ca_htab_init(&tab, 4096) != CA_OK) {
        free(J);
        free(jsz);
        free(roos);
        free(Yn);
        free(B);
        free(scratch);
        free(jidx);
        free(hs);
        return CA_ERR_NOMEM;
    }
    /* (h >> 32) mod nj without a divide (Lemire; exact for 32-bit values) */
    const uint64_t nj_magic = UINT64_MAX / nj + 1;
    uint64_t ops = 0;
    for (uint32_t j = 0; j < nj; j++) {
        jsz[j] = 1ULL << j;
        ca_group_mul(g, &J[j], base, jsz[j], &ops);
    }
    ca_rng rng;
    ca_rng_seed(&rng, seed);
    /* initial placement: tames around the middle, wilds at target + offset */
    uint64_t mid = lo + width / 2;
    uint64_t spacing = (uint64_t)(mean_target / (double)herd) + 1;
    uint64_t dps = 0, restarts = 0;
    double elapsed_prior = 0;
    if (existing) {
        if (!k_load(checkpoint_path, &saved, g, roos, hs, total, &tab, &rng)) {
            rc = CA_ERR_INVALID;
            goto cleanup;
        }
        ops += saved.ops;
        dps = saved.dps; restarts = saved.restarts;
        elapsed_prior = saved.elapsed_seconds;
    } else {
        for (uint32_t i = 0; i < total; i++) {
            roo *r = &roos[i];
            /* spacing >= 1 by construction, so ca_rng_below never sees 0 */
            uint64_t off = (uint64_t)(i / 2) * spacing + ca_rng_below(&rng, spacing);
            if ((i & 1) == 0) {
                r->dist = mid + off;
                ca_group_mul(g, &r->Y, base, r->dist, &ops);
            } else {
                r->dist = off;
                ca_elem t;
                ca_group_mul(g, &t, base, off, &ops);
                ca_group_op(g, &r->Y, target, &t);
                ops++;
            }
            r->since_dp = 0;
        }
        for (uint32_t i = 0; i < total; i++) hs[i] = ca_group_hash(g, &roos[i].Y);
    }
    rc = CA_ERR_INTERNAL;
    /* 32 << dp wraps to 0 for dp >= 59 (dp is clamped to 62, not to 58), which
     * would abandon every kangaroo at every hop; saturate instead. */
    uint64_t abandon = dp >= 59 ? UINT64_MAX : (uint64_t)32 << dp;
    int running = 1;
    if (existing && saved.solved) {
        uint64_t candidate = saved.result;
        if (!ca_verify_log(g, base, target, candidate) ||
            !ca_fit_interval_base(g, base, &candidate, lo, hi)) {
            ca_set_error("kangaroo: saved solution fails verification");
            rc = CA_ERR_INVALID;
            goto cleanup;
        }
        *x = candidate;
        rc = CA_OK;
        running = 0;
    }
    int monitored = checkpoint_path != NULL || verbose;
    if (!progress_interval) progress_interval = 5;
    if (!checkpoint_interval) checkpoint_interval = 60;
    double next_progress = ca_now() + progress_interval;
    double next_checkpoint = ca_now() + checkpoint_interval;
    if (monitored && (!k_save(checkpoint_path, &identity, g, roos, total, &tab, &rng,
                              seed, ops, dps, restarts, elapsed_prior + ca_now() - t0,
                              rc == CA_OK, rc == CA_OK ? *x : 0) ||
                      !k_progress(checkpoint_path, verbose, elapsed_prior + ca_now() - t0,
                                  ops, dps, restarts, tab.count,
                                  rc == CA_OK ? "ok" : "running"))) {
        rc = CA_ERR_INTERNAL;
        goto cleanup;
    }
    uint64_t batches = 0;
    while (running) {
        for (uint32_t i = 0; i < total; i++) {
            jidx[i] = (uint32_t)(((ca_u128)(nj_magic * (hs[i] >> 32)) * nj) >> 64);
            B[i] = J[jidx[i]];
            Yn[i] = roos[i].Y;
        }
        ca_group_batch_op(g, Yn, Yn, B, total, scratch);
        ops += total;
        for (uint32_t i = 0; i < total; i++) {
            roo *r = &roos[i];
            r->Y = Yn[i];
            r->dist += jsz[jidx[i]];
            r->since_dp++;
            uint64_t h = ca_group_hash(g, &r->Y);
            hs[i] = h;
            int tame = (i & 1) == 0;
            if ((h & dp_mask) == 0) {
                uint64_t od, otype;
                int ir = ca_htab_insert(&tab, h, r->dist, (uint64_t)tame, &od, &otype);
                dps++;
                r->since_dp = 0;
                if (ir < 0) { rc = CA_ERR_NOMEM; running = 0; break; }
                if (ir == 1) {
                    if (otype == (uint64_t)tame) {
                        /* same herd collided: re-seed this kangaroo */
                        uint64_t off = ca_rng_below(&rng, spacing * herd + 1);
                        if (tame) {
                            r->dist = mid + off;
                            ca_group_mul(g, &r->Y, base, r->dist, &ops);
                        } else {
                            r->dist = off;
                            ca_elem t;
                            ca_group_mul(g, &t, base, off, &ops);
                            ca_group_op(g, &r->Y, target, &t);
                            ops++;
                        }
                        hs[i] = ca_group_hash(g, &r->Y);
                        restarts++;
                    } else {
                        /* tame position T, wild distance D: x = T - D */
                        uint64_t T = tame ? r->dist : od;
                        uint64_t D = tame ? od : r->dist;
                        uint64_t cand = T - D;
                        if (n) cand = (uint64_t)(((ca_i128)T - (ca_i128)D) % (ca_i128)n);
                        if (n && (ca_i128)T - (ca_i128)D < 0) cand = (cand + n) % n;
                        if (ca_verify_log(g, base, target, cand) &&
                            ca_fit_interval_base(g, base, &cand, lo, hi)) {
                            /* The header promises x in [lo, hi].  A verified
                             * logarithm that cannot be shifted into the
                             * interval is not the answer that was asked for,
                             * so keep hopping rather than return it. */
                            *x = cand;
                            rc = CA_OK;
                            running = 0;
                            break;
                        }
                        /* 64-bit fingerprint collision or stale entry: ignore */
                    }
                }
            } else if (r->since_dp > abandon) {
                uint64_t off = ca_rng_below(&rng, spacing * herd + 1);
                if (tame) {
                    r->dist = mid + off;
                    ca_group_mul(g, &r->Y, base, r->dist, &ops);
                } else {
                    r->dist = off;
                    ca_elem t;
                    ca_group_mul(g, &t, base, off, &ops);
                    ca_group_op(g, &r->Y, target, &t);
                    ops++;
                }
                hs[i] = ca_group_hash(g, &r->Y);
                restarts++;
            }
        }
        if (running && params->max_ops && ops > params->max_ops) {
            rc = CA_ERR_LIMIT; running = 0;
        }
        if (monitored && running && ((++batches & 255u) == 0)) {
            double now = ca_now();
            if (now >= next_progress) {
                if (!k_progress(checkpoint_path, verbose, elapsed_prior + now - t0,
                                ops, dps, restarts, tab.count, "running")) {
                    rc = CA_ERR_INTERNAL; running = 0;
                }
                next_progress = now + progress_interval;
            }
            if (running && now >= next_checkpoint) {
                if (!k_save(checkpoint_path, &identity, g, roos, total, &tab, &rng,
                            seed, ops, dps, restarts, elapsed_prior + now - t0, 0, 0)) {
                    rc = CA_ERR_INTERNAL; running = 0;
                } else if (verbose && checkpoint_path) {
                    fprintf(stderr, "[kangaroo] checkpoint saved\n");
                }
                next_checkpoint = now + checkpoint_interval;
            }
        }
    }
    if (monitored && rc != CA_ERR_INTERNAL &&
        (!k_save(checkpoint_path, &identity, g, roos, total, &tab, &rng,
                 seed, ops, dps, restarts, elapsed_prior + ca_now() - t0,
                 rc == CA_OK, rc == CA_OK ? *x : 0) ||
         !k_progress(checkpoint_path, verbose, elapsed_prior + ca_now() - t0,
                     ops, dps, restarts, tab.count,
                     rc == CA_OK ? "ok" : "stopped"))) rc = CA_ERR_INTERNAL;
cleanup:
    if (st) {
        st->group_ops += ops;
        st->iterations += dps;
        st->collisions += restarts;
        st->table_entries = ca_max_u64(st->table_entries, tab.count);
        st->bytes_peak = ca_max_u64(st->bytes_peak, ca_htab_bytes(&tab));
        st->threads = 1;
        st->seconds += elapsed_prior + ca_now() - t0;
    }
    ca_htab_free(&tab);
    free(J);
    free(jsz);
    free(roos);
    free(Yn);
    free(B);
    free(scratch);
    free(jidx);
    free(hs);
    return rc;
}

ca_status ca_kangaroo_solve(const ca_group *g, const ca_elem *base, const ca_elem *target,
                            uint64_t lo, uint64_t hi, const ca_kangaroo_params *params,
                            uint64_t *x, ca_stats *st)
{
    return k_solve_impl(g, base, target, lo, hi, params, NULL, 0, 0, 0, x, st);
}

ca_status ca_kangaroo_solve_checkpointed(
    const ca_group *g, const ca_elem *base, const ca_elem *target,
    uint64_t lo, uint64_t hi, const ca_kangaroo_params *params,
    const char *checkpoint_path, uint32_t progress_interval,
    uint32_t checkpoint_interval, int verbose, uint64_t *x, ca_stats *st)
{
    return k_solve_impl(g, base, target, lo, hi, params, checkpoint_path,
                        progress_interval, checkpoint_interval, verbose, x, st);
}
