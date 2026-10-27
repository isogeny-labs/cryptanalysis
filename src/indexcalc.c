/*
 * indexcalc.c - index calculus in (Z/pZ)^*, p < 2^64.
 */
#include "cryptanalysis/ca_indexcalc.h"
#include "cryptanalysis/ca_group.h"
#include "cryptanalysis/ca_pohlig.h"
#include "linalg.h"
#include "ca_internal.h"

#include <math.h>
#include <pthread.h>
#include <stdatomic.h>
#include <stdarg.h>
#include <stdio.h>
#include <errno.h>
#include <fcntl.h>
#include <inttypes.h>
#include <stddef.h>
#include <sys/stat.h>
#include <time.h>
#include <unistd.h>

#define IC_SMALL_Q (1ULL << 24)   /* prime factors of p-1 up to this: Pohlig-Hellman */
#define IC_MAX_REL_COLS 96

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
    ic_fbdiv *fb_div;             /* their exact-division constants */
    uint64_t *fb_log;             /* logs mod p-1 */
    uint8_t *fb_known;
    ca_ic_params params;
    uint32_t progress_interval;
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

/* A journal record is committed only after fflush and fsync.  The native
 * layout is intentionally versioned and checked: a different build/ABI must
 * reject the file rather than reinterpret relations. */
typedef struct ic_journal_header {
    char magic[8];
    uint64_t p, g, zeta;
    uint32_t B, C, nfb, ncols, target, relation_size;
} ic_journal_header;

typedef struct ic_journal_record {
    uint32_t marker, index, count;
    uint64_t candidates, checksum;
} ic_journal_record;

static uint64_t ic_hash(const void *data, size_t n, uint64_t h)
{
    const unsigned char *p = data;
    for (size_t i = 0; i < n; i++) { h ^= p[i]; h *= UINT64_C(1099511628211); }
    return h;
}

static uint64_t ic_record_hash(const ic_journal_record *r, const relation *rels)
{
    uint64_t h = UINT64_C(14695981039346656037);
    h = ic_hash(&r->index, sizeof(r->index), h);
    h = ic_hash(&r->count, sizeof(r->count), h);
    h = ic_hash(&r->candidates, sizeof(r->candidates), h);
    return ic_hash(rels, (size_t)r->count * sizeof(*rels), h);
}

static int ic_sync(FILE *f)
{
    return fflush(f) == 0 && fsync(fileno(f)) == 0;
}

static int ic_sync_parent(const char *path)
{
    if (!path || !*path) return 0;
    char *dir = strdup(path);
    if (!dir) return 0;
    const char *parent = dir;
    char *slash = strrchr(dir, '/');
    if (slash) {
        if (slash == dir) slash[1] = '\0';
        else *slash = '\0';
    } else {
        parent = ".";
    }
    int fd = open(parent, O_RDONLY);
    int ok = fd >= 0 && fsync(fd) == 0;
    if (fd >= 0) close(fd);
    free(dir);
    return ok;
}

static FILE *ic_journal_open(const char *path, const ic_journal_header *want, rel_list *rels,
                             uint8_t **complete_out, size_t complete_count, uint64_t *candidates)
{
    uint8_t *complete = calloc(complete_count, 1);
    *complete_out = complete;
    if (!complete) return NULL;
    FILE *f = fopen(path, "rb+");
    if (!f && errno == ENOENT) {
        int fd = open(path, O_RDWR | O_CREAT | O_EXCL, 0600);
        if (fd < 0) return NULL;
        f = fdopen(fd, "wb+");
        if (!f) { close(fd); return NULL; }
        if (fwrite(want, sizeof(*want), 1, f) != 1 || !ic_sync(f) || !ic_sync_parent(path)) {
            fclose(f); unlink(path); return NULL;
        }
        return f;
    }
    if (!f) { ca_set_error("cannot open index-calculus checkpoint"); return NULL; }
    ic_journal_header got;
    if (fread(&got, sizeof(got), 1, f) != 1 || memcmp(&got, want, sizeof(got)) != 0) {
        ca_set_error("checkpoint identity or format does not match this run");
        fclose(f);
        return NULL;
    }
    for (;;) {
        off_t start = ftello(f);
        ic_journal_record r;
        size_t nr = fread(&r, 1, sizeof(r), f);
        if (ferror(f)) goto io_error;
        if (nr == 0 && feof(f)) break;
        if (nr != sizeof(r)) {
            if (ftruncate(fileno(f), start) != 0) goto io_error;
            break;
        }
        if (r.marker != UINT32_C(0x43493152) || r.index >= complete_count ||
            r.count > complete_count) {
            ca_set_error("checkpoint contains an out-of-range sieve unit");
            fclose(f);
            return NULL;
        }
        if (complete[r.index]) {
            ca_set_error("checkpoint contains an invalid or duplicate sieve unit");
            fclose(f);
            return NULL;
        }
        relation *batch = calloc(r.count ? r.count : 1, sizeof(*batch));
        if (!batch) goto io_error;
        nr = fread(batch, sizeof(*batch), r.count, f);
        if (ferror(f)) { free(batch); goto io_error; }
        if (nr != r.count) {
            free(batch);
            if (ftruncate(fileno(f), start) != 0) goto io_error;
            break;
        }
        if (ic_record_hash(&r, batch) != r.checksum) {
            free(batch);
            ca_set_error("checkpoint relation checksum mismatch");
            fclose(f);
            return NULL;
        }
        for (uint32_t i = 0; i < r.count; i++) {
            if (batch[i].n > IC_MAX_REL_COLS || batch[i].rhs >= want->p - 1) {
                free(batch); ca_set_error("checkpoint relation is invalid"); fclose(f); return NULL;
            }
            for (uint32_t j = 0; j < batch[i].n; j++) {
                if (batch[i].col[j] >= want->ncols) {
                    free(batch); ca_set_error("checkpoint column is invalid"); fclose(f); return NULL;
                }
            }
            if (rel_push(rels, &batch[i]) < 0) { free(batch); goto io_error; }
        }
        free(batch);
        complete[r.index] = 1;
        *candidates += r.candidates;
    }
    clearerr(f);
    if (fseeko(f, 0, SEEK_END) != 0) goto io_error;
    return f;
io_error:
    ca_set_error("cannot read or repair index-calculus checkpoint");
    fclose(f);
    return NULL;
}

static int ic_journal_append(FILE *f, uint32_t index, const rel_list *batch, uint64_t candidates)
{
    ic_journal_record r = {0};
    r.marker = UINT32_C(0x43493152);
    r.index = index;
    r.count = batch->n;
    r.candidates = candidates;
    r.checksum = ic_record_hash(&r, batch->r);
    return fwrite(&r, sizeof(r), 1, f) == 1 &&
           (!batch->n || fwrite(batch->r, sizeof(*batch->r), batch->n, f) == batch->n) &&
           ic_sync(f);
}

typedef struct ic_precomp_header {
    char magic[8];
    uint64_t p, g, zeta;
    uint32_t B, C, method, nfb;
    ca_ic_stats stats;
    uint64_t checksum;
} ic_precomp_header;

static char *ic_precomp_path(const char *journal, const char *suffix)
{
    size_t n = strlen(journal) + strlen(suffix) + 1;
    char *path = malloc(n);
    if (path) snprintf(path, n, "%s%s", journal, suffix);
    return path;
}

static char *ic_sibling_path(const char *journal, const char *name)
{
    const char *slash = strrchr(journal, '/');
    size_t prefix = slash ? (size_t)(slash - journal + 1) : 0;
    size_t name_len = strlen(name) + 1;
    char *path = malloc(prefix + name_len);
    if (!path) return NULL;
    memcpy(path, journal, prefix);
    memcpy(path + prefix, name, name_len);
    return path;
}

static uint64_t ic_precomp_hash(const ic_precomp_header *h, const ca_ic_ctx *ctx)
{
    uint64_t v = ic_hash(h, offsetof(ic_precomp_header, checksum), UINT64_C(14695981039346656037));
    v = ic_hash(ctx->fb_log, (size_t)ctx->nfb * sizeof(uint64_t), v);
    return ic_hash(ctx->fb_known, ctx->nfb, v);
}

static int ic_precomp_load(const char *journal, ca_ic_ctx *ctx, uint32_t B, uint32_t C,
                            ca_ic_stats *st)
{
    char *path = ic_precomp_path(journal, ".precomp");
    if (!path) return -1;
    FILE *f = fopen(path, "rb");
    free(path);
    if (!f) {
        if (errno == ENOENT) return 0;
        ca_set_error("cannot open index-calculus precomputation");
        return -1;
    }
    ic_precomp_header h;
    int ok = fread(&h, sizeof(h), 1, f) == 1 &&
             memcmp(h.magic, "CAICP1", 6) == 0 &&
             h.p == ctx->p && h.g == ctx->g && h.zeta == ctx->zeta &&
             h.B == B && h.C == C && h.method == (uint32_t)ctx->params.method &&
             h.nfb == ctx->nfb;
    if (ok) ok = fread(ctx->fb_log, sizeof(uint64_t), ctx->nfb, f) == ctx->nfb &&
                 fread(ctx->fb_known, 1, ctx->nfb, f) == ctx->nfb && fgetc(f) == EOF;
    fclose(f);
    if (ok) ok = ic_precomp_hash(&h, ctx) == h.checksum;
    if (ok) {
        uint32_t verified = 0;
        for (uint32_t i = 0; i < ctx->nfb; i++) {
            if (ctx->fb_known[i] > 1 ||
                (ctx->fb_known[i] && ca_powmod(ctx->zeta, ctx->fb_log[i], ctx->p) != ctx->fb[i])) {
                ok = 0; break;
            }
            verified += ctx->fb_known[i];
        }
        if (verified != h.stats.verified_logs || h.stats.factor_base_size != ctx->nfb)
            ok = 0;
    }
    if (!ok) {
        ca_set_error("index-calculus precomputation is corrupt or belongs to another run");
        return -1;
    }
    *st = h.stats;
    return 1;
}

static int ic_precomp_save(const char *journal, const ca_ic_ctx *ctx,
                            uint32_t B, uint32_t C, const ca_ic_stats *st)
{
    char *path = ic_precomp_path(journal, ".precomp");
    char *tmp = ic_precomp_path(journal, ".precomp.tmp.XXXXXX");
    if (!path || !tmp) { free(path); free(tmp); return 0; }
    ic_precomp_header h = {0};
    memcpy(h.magic, "CAICP1", 6);
    h.p = ctx->p; h.g = ctx->g; h.zeta = ctx->zeta;
    h.B = B; h.C = C; h.method = (uint32_t)ctx->params.method; h.nfb = ctx->nfb;
    h.stats = *st;
    h.checksum = ic_precomp_hash(&h, ctx);
    int fd = mkstemp(tmp);
    FILE *f = fd >= 0 ? fdopen(fd, "wb") : NULL;
    if (!f) { if (fd >= 0) close(fd); free(path); free(tmp); return 0; }
    int ok = fwrite(&h, sizeof(h), 1, f) == 1 &&
             fwrite(ctx->fb_log, sizeof(uint64_t), ctx->nfb, f) == ctx->nfb &&
             fwrite(ctx->fb_known, 1, ctx->nfb, f) == ctx->nfb && ic_sync(f);
    if (fclose(f) != 0) ok = 0;
    if (ok && rename(tmp, path) != 0) ok = 0;
    if (ok && !ic_sync_parent(path)) ok = 0;
    if (!ok) unlink(tmp);
    free(path); free(tmp);
    return ok;
}

/* ---- smoothness test by trial division ---------------------------------- */

/* Factor v over the primes fb[0..nfb) ; writes exponents to (col,val) with
 * column offset col0.  Returns 1 if fully smooth.  div[] holds each
 * prime's exact-division constants (ic_fbdiv). */
static int trial_factor(uint64_t v, const uint32_t *fb, const ic_fbdiv *div, uint32_t nfb,
                        uint32_t col0, relation *rel, uint32_t *cnt)
{
    uint32_t n = *cnt;
    for (uint32_t i = 0; i < nfb && v > 1; i++) {
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
        int32_t e = 0;
        if (q == 2) {
            e = __builtin_ctzll(v);
            v >>= e;
        } else {
            const uint64_t inv = div[i].inv, lim = div[i].lim;
            while (v * inv <= lim) {
                v *= inv;
                e++;
            }
        }
        if (e) {
            if (n >= IC_MAX_REL_COLS) return 0;
            rel->col[n] = col0 + i;
            rel->val[n] = e;
            n++;
        }
    }
    *cnt = n;
    return v == 1;
}

/* ---- linear sieve ------------------------------------------------------- */

typedef struct sieve_shared {
    uint64_t p, H, J;             /* H = ceil(sqrt p), J = H^2 - p */
    uint32_t B, C;
    const uint32_t *fb;
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
    FILE *journal;
    const char *journal_path;
    uint8_t *complete;
    uint32_t completed;
    double started, last_report, last_saved;
    uint32_t progress_interval;
    int verbose;
} sieve_shared;

static int ic_progress_save(const sieve_shared *s, const char *phase)
{
    if (!s->journal_path) return 1;
    char *path = ic_sibling_path(s->journal_path, "progress.json");
    char *tmp = ic_sibling_path(s->journal_path, ".progress.tmp.XXXXXX");
    if (!path || !tmp) { free(path); free(tmp); return 0; }
    int fd = mkstemp(tmp);
    FILE *f = fd >= 0 ? fdopen(fd, "wb") : NULL;
    if (!f) { if (fd >= 0) close(fd); free(path); free(tmp); return 0; }
    int ok = fprintf(f,
                     "{\"schema\":1,\"phase\":\"%s\",\"completed_units\":%u,\"total_units\":%u,"
                     "\"relations\":%u,\"target_relations\":%u,\"candidates\":%" PRIu64
                     ",\"elapsed_seconds\":%.3f}\n",
                     phase, s->completed, 2 * s->C + 1, s->rels->n, s->target_rels,
                     atomic_load(&s->candidates), ca_now() - s->started) > 0 && ic_sync(f);
    if (fclose(f) != 0) ok = 0;
    if (ok && rename(tmp, path) != 0) ok = 0;
    if (ok && !ic_sync_parent(path)) ok = 0;
    if (!ok) unlink(tmp);
    free(path); free(tmp);
    return ok;
}

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
    while (!atomic_load(&s->done)) {
        int idx = atomic_fetch_add(&s->next_c1, 1);
        if (idx > 2 * C) break;
        if (s->complete && s->complete[idx]) continue;
        uint64_t cand_count = 0;
        local.n = 0;
        int oom = 0;
        int64_t c1 = idx - C;
        /* sieve c2 in [c1, C] */
        int64_t c2lo = c1, c2hi = C;
        size_t n = (size_t)(c2hi - c2lo + 1);
        memset(arr, 0, n);
        for (uint32_t i = 0; i < nfb; i++) {
            uint64_t q = s->fb[i];
            /* a = (H + c1) mod q, b = (J + c1 H) mod q ; root: c2 = -b / a */
            uint64_t c1m = (uint64_t)(((c1 % (int64_t)q) + (int64_t)q) % (int64_t)q);
            uint64_t a = (hmod[i] + c1m) % q;
            if (a == 0) continue;
            uint64_t b = (jmod[i] + c1m * hmod[i]) % q;
            uint64_t inv = ca_invmod(a, q);
            uint64_t root = (q - ca_mulmod(b, inv, q)) % q; /* c2 == root (mod q) */
            /* first c2 >= c2lo with c2 == root mod q */
            int64_t c2lo_m = ((c2lo % (int64_t)q) + (int64_t)q) % (int64_t)q;
            int64_t start = c2lo + (int64_t)((root + q - (uint64_t)c2lo_m) % q);
            uint8_t lg = s->fb_log2[i];
            for (int64_t c2 = start; c2 <= c2hi; c2 += (int64_t)q) arr[c2 - c2lo] += lg;
        }
        /* scan candidates */
        for (size_t k = 0; k < n; k++) {
            int64_t c2 = c2lo + (int64_t)k;
            ca_i128 v = sieve_value(s, c1, c2);
            uint64_t av = v < 0 ? (uint64_t)(-v) : (uint64_t)v;
            if (av == 0) continue;
            unsigned bl = bitlen(av);
            /* allow ~ the largest prime unaccounted (prime powers) */
            if ((unsigned)arr[k] + 6 < bl) continue;
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
            if (rel_push(&local, &rel) < 0) { oom = 1; break; }
        }
        pthread_mutex_lock(&s->lock);
        if (oom || (s->journal && !ic_journal_append(s->journal, (uint32_t)idx, &local, cand_count))) {
            s->status = oom ? CA_ERR_NOMEM : CA_ERR_INTERNAL;
            if (!oom) ca_set_error("cannot persist index-calculus sieve unit");
            atomic_store(&s->done, 1);
        } else {
            for (uint32_t i = 0; i < local.n; i++) {
                if (rel_push(s->rels, &local.r[i]) < 0) { s->status = CA_ERR_NOMEM; atomic_store(&s->done, 1); break; }
            }
            if (s->complete) s->complete[idx] = 1;
            s->completed++;
            atomic_fetch_add(&s->candidates, cand_count);
            if (s->rels->n >= s->target_rels) atomic_store(&s->done, 1);
            double now = ca_now();
            if (s->verbose && now - s->last_report >= s->progress_interval) {
                fprintf(stderr, "[ic] sieve %u/%u units, %u/%u relations, %" PRIu64
                        " candidates, %.1fs elapsed\n", s->completed, 2 * s->C + 1,
                        s->rels->n, s->target_rels, atomic_load(&s->candidates), now - s->started);
                fflush(stderr);
                s->last_report = now;
            }
            if (s->journal_path && now - s->last_saved >= s->progress_interval) {
                if (!ic_progress_save(s, "sieving")) {
                    s->status = CA_ERR_INTERNAL;
                    atomic_store(&s->done, 1);
                } else {
                    s->last_saved = now;
                }
            }
        }
        pthread_mutex_unlock(&s->lock);
    }
    free(local.r);
    free(arr); free(hmod); free(jmod);
    return NULL;
}

/* ---- random exponent collector ----------------------------------------- */

typedef struct ic_rexp_header {
    char magic[8];
    uint64_t p, g, zeta, seed, tests, generation, fb_hash;
    double elapsed_seconds;
    uint32_t B, C, nfb, ncols, target, threads, relation_size, count;
    uint64_t checksum;
} ic_rexp_header;

static int rexp_snapshot_load(const char *path, const ic_rexp_header *want,
                              uint64_t requested_seed, rel_list *rels,
                              uint64_t *seed, uint64_t *tests, uint64_t *generation,
                              double *elapsed_seconds)
{
    FILE *f = fopen(path, "rb");
    if (!f) {
        if (errno == ENOENT) return 0;
        ca_set_error("cannot open random-exponent checkpoint");
        return -1;
    }
    ic_rexp_header h;
    struct stat sb;
    int ok = fread(&h, sizeof(h), 1, f) == 1 &&
             memcmp(h.magic, "CAICRX1", 8) == 0 &&
             h.p == want->p && h.g == want->g && h.zeta == want->zeta &&
             h.B == want->B && h.C == want->C && h.nfb == want->nfb &&
             h.ncols == want->ncols && h.target == want->target &&
             h.threads == want->threads && h.relation_size == sizeof(relation) &&
             h.fb_hash == want->fb_hash && (!requested_seed || h.seed == want->seed) &&
             h.seed != 0 && h.count >= 1 && h.elapsed_seconds >= 0 &&
             isfinite(h.elapsed_seconds) &&
             fstat(fileno(f), &sb) == 0 && sb.st_size >= 0 &&
             (uint64_t)sb.st_size == sizeof(h) + (uint64_t)h.count * sizeof(relation);
    if (!ok || (uint64_t)h.count > (uint64_t)want->target + 64 * (uint64_t)want->threads + 1) {
        fclose(f);
        ca_set_error("random-exponent checkpoint identity or header mismatch");
        return -1;
    }
    /* The checked file length, not a deserialized allocation size, owns the buffer. */
    size_t saved_bytes = (size_t)((uint64_t)sb.st_size - sizeof(h));
    if (saved_bytes / sizeof(relation) != h.count) {
        fclose(f);
        ca_set_error("random-exponent checkpoint payload is too large");
        return -1;
    }
    relation *saved = malloc(saved_bytes);
    if (!saved) { fclose(f); return -2; }
    ok = fread(saved, sizeof(*saved), h.count, f) == h.count && fgetc(f) == EOF;
    fclose(f);
    uint64_t hash = ic_hash(&h, offsetof(ic_rexp_header, checksum),
                            UINT64_C(14695981039346656037));
    hash = ic_hash(saved, (size_t)h.count * sizeof(*saved), hash);
    ok = ok && hash == h.checksum;
    for (uint32_t i = 0; ok && i < h.count; i++) {
        if (saved[i].n > IC_MAX_REL_COLS || saved[i].rhs >= h.p - 1) { ok = 0; break; }
        for (uint32_t j = 0; j < saved[i].n; j++) {
            if (saved[i].col[j] >= h.ncols || saved[i].val[j] < 0) { ok = 0; break; }
        }
    }
    if (!ok) {
        free(saved);
        ca_set_error("random-exponent checkpoint checksum or relation mismatch");
        return -1;
    }
    free(rels->r);
    rels->r = saved; rels->n = h.count; rels->cap = h.count;
    *seed = h.seed; *tests = h.tests; *generation = h.generation + 1;
    *elapsed_seconds = h.elapsed_seconds;
    return 1;
}

typedef struct rexp_shared {
    uint64_t p, zeta;
    const uint32_t *fb;
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
    atomic_int active;
    ca_status status;
    const char *checkpoint_path;
    ic_rexp_header header;
    uint64_t generation;
    double elapsed_prior;
    double started, last_report;
    uint32_t progress_interval;
    int verbose;
} rexp_shared;

static int rexp_snapshot_save(rexp_shared *s)
{
    if (!s->checkpoint_path) return 1;
    char *tmp = ic_precomp_path(s->checkpoint_path, ".tmp.XXXXXX");
    if (!tmp) return 0;
    int fd = mkstemp(tmp);
    FILE *f = fd >= 0 ? fdopen(fd, "wb+") : NULL;
    if (!f) { if (fd >= 0) close(fd); free(tmp); return 0; }
    pthread_mutex_lock(&s->lock);
    ic_rexp_header h = s->header;
    h.seed = s->seed; h.tests = atomic_load(&s->tests);
    h.generation = s->generation; h.count = s->rels->n;
    h.elapsed_seconds = s->elapsed_prior + ca_now() - s->started;
    h.checksum = 0;
    uint64_t hash = ic_hash(&h, offsetof(ic_rexp_header, checksum),
                            UINT64_C(14695981039346656037));
    hash = ic_hash(s->rels->r, (size_t)h.count * sizeof(relation), hash);
    h.checksum = hash;
    int ok = fwrite(&h, sizeof(h), 1, f) == 1 &&
             fwrite(s->rels->r, sizeof(relation), h.count, f) == h.count;
    pthread_mutex_unlock(&s->lock);
    if (ok) ok = ic_sync(f);
    if (fclose(f) != 0) ok = 0;
    if (ok && rename(tmp, s->checkpoint_path) != 0) ok = 0;
    if (ok && !ic_sync_parent(s->checkpoint_path)) ok = 0;
    if (!ok) unlink(tmp);
    free(tmp);
    return ok;
}

static int rexp_progress_save(rexp_shared *s, const char *phase)
{
    if (!s->checkpoint_path) return 1;
    char *path = ic_sibling_path(s->checkpoint_path, "progress.json");
    char *tmp = ic_sibling_path(s->checkpoint_path, ".progress.tmp.XXXXXX");
    if (!path || !tmp) { free(path); free(tmp); return 0; }
    int fd = mkstemp(tmp);
    FILE *f = fd >= 0 ? fdopen(fd, "wb") : NULL;
    if (!f) { if (fd >= 0) close(fd); free(path); free(tmp); return 0; }
    pthread_mutex_lock(&s->lock);
    uint32_t count = s->rels->n;
    pthread_mutex_unlock(&s->lock);
    int ok = fprintf(f,
        "{\"schema\":1,\"method\":\"rexp\",\"phase\":\"%s\","
        "\"relations\":%u,\"target_relations\":%u,\"smooth_tests\":%" PRIu64
        ",\"elapsed_seconds\":%.3f}\n",
        phase, count, s->target_rels, atomic_load(&s->tests),
        s->elapsed_prior + ca_now() - s->started) > 0 &&
        ic_sync(f);
    if (fclose(f) != 0) ok = 0;
    if (ok && rename(tmp, path) != 0) ok = 0;
    if (ok && !ic_sync_parent(path)) ok = 0;
    if (!ok) unlink(tmp);
    free(path); free(tmp);
    return ok;
}

static void *rexp_thread(void *arg)
{
    rexp_shared *s = arg;
    ca_rng rng;
    ca_rng_seed(&rng, s->seed ^ (0x9E3779B97F4A7C15ULL *
                      (uint64_t)(atomic_fetch_add(&s->tid, 1) + 1)) ^
                      (s->generation ? ca_mix64(s->generation) : 0));
    ca_mont m;
    ca_mont_init(&m, s->p);
    uint64_t zm = ca_mont_to(&m, s->zeta);
    uint64_t e = 1 + ca_rng_below(&rng, s->p - 2);
    uint64_t cur = ca_mont_pow(&m, zm, e);
    uint64_t tests = 0;
    uint64_t pending_tests = 0;
    rel_list local = {0};
    while (!atomic_load(&s->done)) {
        /* step e by a random small amount to keep exponentiation cheap */
        uint64_t step = 1 + ca_rng_below(&rng, 255);
        cur = ca_mont_mul(&m, cur, ca_mont_pow(&m, zm, step));
        e = (e + step) % (s->p - 1);
        uint64_t v = ca_mont_from(&m, cur);
        tests++;
        pending_tests++;
        relation rel;
        memset(&rel, 0, sizeof(rel));
        uint32_t cnt = 0;
        if (trial_factor(v, s->fb, s->fb_div, s->nfb, s->col_prime0, &rel, &cnt)) {
            rel.n = cnt;
            rel.rhs = e; /* sum e_q log q == e */
            if (rel_push(&local, &rel) < 0) {
                pthread_mutex_lock(&s->lock);
                s->status = CA_ERR_NOMEM;
                atomic_store(&s->done, 1);
                pthread_mutex_unlock(&s->lock);
                break;
            }
            if (local.n >= 64) {
                pthread_mutex_lock(&s->lock);
                for (uint32_t i = 0; i < local.n; i++) {
                    if (rel_push(s->rels, &local.r[i]) < 0) {
                        s->status = CA_ERR_NOMEM;
                        atomic_store(&s->done, 1);
                        break;
                    }
                }
                if (s->rels->n >= s->target_rels) atomic_store(&s->done, 1);
                pthread_mutex_unlock(&s->lock);
                local.n = 0;
                if (atomic_load(&s->done)) break;
            }
        }
        if (pending_tests >= 4096) {
            atomic_fetch_add(&s->tests, pending_tests);
            pending_tests = 0;
            double now = ca_now();
            if (s->verbose) {
                pthread_mutex_lock(&s->lock);
                if (now - s->last_report >= s->progress_interval) {
                    fprintf(stderr, "[ic] random exponents: %" PRIu64 " tests, %u/%u relations, %.1fs elapsed\n",
                            atomic_load(&s->tests), s->rels->n, s->target_rels,
                            s->elapsed_prior + now - s->started);
                    fflush(stderr);
                    s->last_report = now;
                }
                pthread_mutex_unlock(&s->lock);
            }
        }
        if (s->max_tries && tests > s->max_tries) break;
    }
    pthread_mutex_lock(&s->lock);
    if (s->status == CA_OK) {
        for (uint32_t i = 0; i < local.n; i++) {
            if (rel_push(s->rels, &local.r[i]) < 0) {
                s->status = CA_ERR_NOMEM;
                atomic_store(&s->done, 1);
                break;
            }
        }
    }
    if (s->rels->n >= s->target_rels) atomic_store(&s->done, 1);
    pthread_mutex_unlock(&s->lock);
    atomic_fetch_add(&s->tests, pending_tests);
    free(local.r);
    atomic_fetch_sub(&s->active, 1);
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

static ca_status ic_precompute_impl(uint64_t p, uint64_t g, const ca_ic_params *params,
                                    const char *checkpoint_path, uint32_t progress_interval,
                                    ca_ic_ctx **out, ca_ic_stats *st)
{
    ca_ic_params def;
    if (!params) { ca_ic_params_default(&def); params = &def; }
    if (checkpoint_path && !*checkpoint_path) {
        ca_set_error("checkpoint path must not be empty");
        return CA_ERR_INVALID;
    }
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
    ctx->progress_interval = progress_interval ? progress_interval : 5;
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
    if (C > 1000000) {
        ca_set_error("index-calculus sieve radius exceeds supported limit");
        ca_ic_free(ctx);
        return CA_ERR_INVALID;
    }
    /* A factor-base prime q >= p reduces to 0 or to a smaller residue mod p,
     * so its logarithm is undefined or duplicates another's and the solve
     * fails for a tiny modulus (p < B).  p >= 7 keeps B >= 6 here. */
    if ((uint64_t)B >= p) B = (uint32_t)(p - 1);
    uint32_t threads = params->threads ? params->threads : 1;
    st->threads = threads;

    /* factor base */
    size_t nfb = ca_sieve_primes(B, NULL, 0);
    ctx->fb = malloc(nfb * sizeof(uint32_t));
    ctx->fb_log = calloc(nfb, sizeof(uint64_t));
    ctx->fb_known = calloc(nfb, 1);
    ctx->fb_div = malloc(nfb * sizeof(ic_fbdiv));
    uint8_t *fb_log2 = malloc(nfb);
    if (!ctx->fb || !ctx->fb_log || !ctx->fb_known || !ctx->fb_div || !fb_log2) {
        free(fb_log2);
        ca_ic_free(ctx);
        return CA_ERR_NOMEM;
    }
    ca_sieve_primes(B, ctx->fb, nfb);
    ctx->nfb = (uint32_t)nfb;
    for (size_t i = 0; i < nfb; i++) {
        uint64_t q = ctx->fb[i], inv = q; /* Newton: q odd, correct to 3 bits */
        for (int k = 0; k < 5; k++) inv *= 2 - q * inv;
        ctx->fb_div[i].inv = inv;
        ctx->fb_div[i].lim = UINT64_MAX / q;
    }
    for (size_t i = 0; i < nfb; i++) fb_log2[i] = (uint8_t)(log2((double)ctx->fb[i]) + 0.5);
    st->factor_base_size = ctx->nfb;
    if (checkpoint_path) {
        int loaded = ic_precomp_load(checkpoint_path, ctx, B, C, st);
        if (loaded < 0) { free(fb_log2); ca_ic_free(ctx); return CA_ERR_INVALID; }
        if (loaded) {
            ctx->ord_g = ca_mult_order(g, p);
            if (g == ctx->zeta) { ctx->log_g = 1; ctx->g_known = 1; }
            st->sieve_seconds = 0;
            st->linalg_seconds = 0;
            st->total_seconds = ca_now() - t_start;
            st->threads = threads;
            vlog(params, "[ic] loaded verified factor-base logs from checkpoint\n");
            free(fb_log2);
            *out = ctx;
            return CA_OK;
        }
    }

    /* column layout: [primes][H+c ...] ; -1 handled on the rhs */
    uint32_t col_prime0 = 0;
    uint32_t col_h0 = ctx->nfb;
    uint32_t ncols = params->method == CA_IC_LINEAR_SIEVE ? ctx->nfb + 2 * C + 1 : ctx->nfb;
    st->unknowns = ncols;
    uint32_t extra = params->extra_relations ? params->extra_relations : 64 + ncols / 20;
    if (extra > UINT32_MAX - ncols) {
        ca_set_error("index-calculus relation target overflows");
        free(fb_log2); ca_ic_free(ctx);
        return CA_ERR_INVALID;
    }
    uint32_t target = ncols + extra;

    /* ---- relation collection ---- */
    rel_list rels = {0};
    double t0 = ca_now();
    double prior_sieve_seconds = 0;
    /* an explicit relation for zeta (usually itself a factor-base prime):
     * sum e_q log q == 1 */
    {
        relation rel;
        memset(&rel, 0, sizeof(rel));
        uint32_t cnt = 0;
        if (trial_factor(ctx->zeta, ctx->fb, ctx->fb_div, ctx->nfb, col_prime0, &rel, &cnt)) {
            rel.n = cnt;
            rel.rhs = 1;
            if (rel_push(&rels, &rel) < 0) {
                free(fb_log2);
                ca_ic_free(ctx);
                return CA_ERR_NOMEM;
            }
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
        s.verbose = params->verbose;
        s.progress_interval = progress_interval ? progress_interval : 5;
        s.started = s.last_report = s.last_saved = ca_now();
        s.journal_path = checkpoint_path;
        atomic_store(&s.next_c1, 0);
        atomic_store(&s.done, 0);
        atomic_store(&s.candidates, 0);
        pthread_mutex_init(&s.lock, NULL);
        if (checkpoint_path) {
            ic_journal_header header = {0};
            memcpy(header.magic, "CAICJ1", 6);
            header.p = p; header.g = g; header.zeta = ctx->zeta;
            header.B = B; header.C = C; header.nfb = ctx->nfb;
            header.ncols = ncols; header.target = target;
            header.relation_size = sizeof(relation);
            uint64_t replay_candidates = 0;
            s.journal = ic_journal_open(checkpoint_path, &header, &rels, &s.complete,
                                        (size_t)2 * C + 1, &replay_candidates);
            if (!s.journal) {
                ca_status failure = s.complete ? CA_ERR_INVALID : CA_ERR_NOMEM;
                free(s.complete); pthread_mutex_destroy(&s.lock);
                free(tids); free(fb_log2); free(rels.r); ca_ic_free(ctx);
                return failure;
            }
            atomic_store(&s.candidates, replay_candidates);
            for (uint32_t i = 0; i <= 2 * C; i++) s.completed += s.complete[i];
            if (rels.n >= target) atomic_store(&s.done, 1);
            if (s.completed)
                vlog(params, "[ic] resumed %u sieve units, %u relations, %" PRIu64 " candidates\n",
                     s.completed, rels.n, replay_candidates);
        }
        if (!ic_progress_save(&s, "sieving")) {
            ca_set_error("cannot persist index-calculus progress");
            if (s.journal) fclose(s.journal);
            free(s.complete); pthread_mutex_destroy(&s.lock);
            free(tids); free(fb_log2); free(rels.r); ca_ic_free(ctx);
            return CA_ERR_INTERNAL;
        }
        vlog(params, "[ic] p=%llu (%u bits) linear sieve B=%u (%u primes) C=%u unknowns=%u target=%u threads=%u\n",
             (unsigned long long)p, bitlen(p), B, ctx->nfb, C, ncols, target, threads);
        uint32_t started = 0;
        for (uint32_t t = 0; t < threads; t++) {
            if (threads == 1) sieve_thread(&s);
            else if (pthread_create(&tids[started], NULL, sieve_thread, &s) == 0) started++;
        }
        if (threads > 1 && started == 0) sieve_thread(&s);
        for (uint32_t t = 0; t < started; t++) pthread_join(tids[t], NULL);
        if (s.status == CA_OK &&
            !ic_progress_save(&s, rels.n >= target ? "relations_collected" : "sieve_exhausted"))
            s.status = CA_ERR_INTERNAL;
        if (params->verbose) {
            vlog(params, "[ic] sieve complete: %u/%u units, %u/%u relations\n",
                 s.completed, 2 * C + 1, rels.n, target);
        }
        if (s.journal) fclose(s.journal);
        free(s.complete);
        pthread_mutex_destroy(&s.lock);
        st->sieve_candidates = atomic_load(&s.candidates);
        if (s.status != CA_OK) {
            if (s.status == CA_ERR_INTERNAL) ca_set_error("cannot persist index-calculus checkpoint or progress");
            free(tids); free(fb_log2); free(rels.r); ca_ic_free(ctx); return s.status;
        }
    } else {
        rexp_shared s;
        memset(&s, 0, sizeof(s));
        s.p = p;
        s.zeta = ctx->zeta;
        s.fb = ctx->fb;
        s.fb_div = ctx->fb_div;
        s.nfb = ctx->nfb;
        s.col_prime0 = col_prime0;
        s.target_rels = target;
        s.max_tries = params->max_relation_tries;
        s.rels = &rels;
        s.seed = seed;
        s.verbose = params->verbose && !checkpoint_path;
        s.status = CA_OK;
        s.checkpoint_path = checkpoint_path;
        s.progress_interval = progress_interval ? progress_interval : 5;
        s.started = s.last_report = ca_now();
        atomic_store(&s.done, 0);
        atomic_store(&s.tid, 0);
        atomic_store(&s.active, 0);
        atomic_store(&s.tests, 0);
        pthread_mutex_init(&s.lock, NULL);
        if (checkpoint_path) {
            memcpy(s.header.magic, "CAICRX1", 7);
            s.header.p = p; s.header.g = g; s.header.zeta = ctx->zeta;
            s.header.seed = seed;
            s.header.B = B; s.header.C = C; s.header.nfb = ctx->nfb;
            s.header.ncols = ncols; s.header.target = target;
            s.header.threads = threads; s.header.relation_size = sizeof(relation);
            s.header.fb_hash = ic_hash(ctx->fb, (size_t)ctx->nfb * sizeof(uint32_t),
                                       UINT64_C(14695981039346656037));
            uint64_t saved_tests = 0;
            int loaded = rexp_snapshot_load(checkpoint_path, &s.header, params->seed,
                                             &rels, &s.seed, &saved_tests,
                                             &s.generation, &s.elapsed_prior);
            if (loaded < 0) {
                pthread_mutex_destroy(&s.lock);
                free(tids); free(fb_log2); free(rels.r); ca_ic_free(ctx);
                return loaded == -2 ? CA_ERR_NOMEM : CA_ERR_INVALID;
            }
            atomic_store(&s.tests, saved_tests);
            seed = s.seed;
            prior_sieve_seconds = s.elapsed_prior;
            if (rels.n >= target) atomic_store(&s.done, 1);
            if (loaded) vlog(params, "[ic] resumed %u relations and %" PRIu64
                             " smoothness tests\n", rels.n, saved_tests);
            if (!rexp_snapshot_save(&s) || !rexp_progress_save(&s, "collecting")) {
                pthread_mutex_destroy(&s.lock);
                free(tids); free(fb_log2); free(rels.r); ca_ic_free(ctx);
                ca_set_error("cannot persist random-exponent checkpoint or progress");
                return CA_ERR_INTERNAL;
            }
        }
        vlog(params, "[ic] p=%llu (%u bits) random exponents B=%u (%u primes) target=%u threads=%u\n",
             (unsigned long long)p, bitlen(p), B, ctx->nfb, target, threads);
        uint32_t started = 0;
        for (uint32_t t = 0; !atomic_load(&s.done) && t < threads; t++) {
            atomic_fetch_add(&s.active, 1);
            if (threads == 1 && !checkpoint_path) rexp_thread(&s);
            else if (pthread_create(&tids[started], NULL, rexp_thread, &s) == 0) started++;
            else atomic_fetch_sub(&s.active, 1);
        }
        if (!atomic_load(&s.done) && threads > 1 && started == 0 && !checkpoint_path) {
            atomic_fetch_add(&s.active, 1);
            rexp_thread(&s);
        }
        if (!atomic_load(&s.done) && checkpoint_path && started == 0) {
            s.status = CA_ERR_INTERNAL;
            ca_set_error("cannot start random-exponent checkpoint worker");
        }
        if (checkpoint_path && started) {
            double last_saved = ca_now();
            while (atomic_load(&s.active) > 0) {
                double now = ca_now();
                if (now - last_saved >= s.progress_interval) {
                    if (!rexp_snapshot_save(&s) || !rexp_progress_save(&s, "collecting")) {
                        pthread_mutex_lock(&s.lock);
                        s.status = CA_ERR_INTERNAL;
                        atomic_store(&s.done, 1);
                        pthread_mutex_unlock(&s.lock);
                        ca_set_error("cannot persist random-exponent checkpoint or progress");
                        break;
                    }
                    pthread_mutex_lock(&s.lock);
                    uint32_t relations_now = rels.n;
                    pthread_mutex_unlock(&s.lock);
                    if (params->verbose) fprintf(stderr, "[ic] random exponents: %" PRIu64
                        " tests, %u/%u relations, %.1fs elapsed\n",
                        atomic_load(&s.tests), relations_now, target,
                        s.elapsed_prior + now - s.started);
                    last_saved = now;
                }
                struct timespec wait = {.tv_sec = 0, .tv_nsec = 100000000};
                nanosleep(&wait, NULL);
            }
        }
        for (uint32_t t = 0; t < started; t++) pthread_join(tids[t], NULL);
        if (s.status == CA_OK && checkpoint_path &&
            (!rexp_snapshot_save(&s) || !rexp_progress_save(&s,
                rels.n >= target ? "relations_collected" : "exhausted"))) {
            s.status = CA_ERR_INTERNAL;
            ca_set_error("cannot persist final random-exponent checkpoint");
        }
        pthread_mutex_destroy(&s.lock);
        st->smooth_tests = atomic_load(&s.tests);
        if (s.status != CA_OK) {
            free(tids); free(fb_log2); free(rels.r); ca_ic_free(ctx);
            return s.status;
        }
    }
    free(tids);
    free(fb_log2);
    st->relations = rels.n;
    st->sieve_seconds = prior_sieve_seconds + ca_now() - t0;
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
    vlog(params, "[ic] solving small subgroup logs modulo %" PRIu64 "\n", m_small);
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
                rc = build_matrix(&rels, ncols, pm1, &A, &b);
                if (rc != CA_OK) goto done;
                have_matrix = 1;
            }
            uint64_t qe = 1;
            for (unsigned e = 0; e < f.f[i].e; e++) qe *= q;
            uint64_t *xq = calloc(ncols, sizeof(uint64_t));
            uint8_t *kq = calloc(ncols, 1);
            ca_linsolve_report rep;
            if (!xq || !kq) { free(xq); free(kq); rc = CA_ERR_NOMEM; break; }
            vlog(params, "[ic] solving relation matrix modulo %" PRIu64 "^%u\n", q, f.f[i].e);
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
    st->total_seconds = prior_sieve_seconds + ca_now() - t_start;
    if (checkpoint_path && !ic_precomp_save(checkpoint_path, ctx, B, C, st)) {
        ca_set_error("cannot persist index-calculus precomputation");
        ca_ic_free(ctx);
        return CA_ERR_INTERNAL;
    }
    *out = ctx;
    return CA_OK;
}

ca_status ca_ic_precompute(uint64_t p, uint64_t g, const ca_ic_params *params, ca_ic_ctx **out,
                           ca_ic_stats *st)
{
    return ic_precompute_impl(p, g, params, NULL, 5, out, st);
}

void ca_ic_free(ca_ic_ctx *ctx)
{
    if (!ctx) return;
    free(ctx->fb);
    free(ctx->fb_log);
    free(ctx->fb_known);
    free(ctx->fb_div);
    pthread_mutex_destroy(&ctx->rng_lock);
    free(ctx);
}

/* log_zeta(h) via smoothness of h * zeta^e */
static ca_status individual_log_zeta(ca_ic_ctx *ctx, uint64_t h, uint64_t *out, uint64_t *tries)
{
    uint64_t p = ctx->p, pm1 = p - 1;
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
    double started = ca_now(), last_report = started;
    for (uint64_t t = 0; t < limit; t++) {
        uint64_t v = ca_mont_from(&m, cur);
        relation rel;
        uint32_t cnt = 0;
        (*tries)++;
        if (ctx->params.verbose && (t & 4095) == 0) {
            double now = ca_now();
            if (now - last_report >= ctx->progress_interval) {
                vlog(&ctx->params, "[ic] individual log: %" PRIu64 " attempts, %.1fs elapsed\n",
                     t + 1, now - started);
                last_report = now;
            }
        }
        if (trial_factor(v, ctx->fb, ctx->fb_div, ctx->nfb, 0, &rel, &cnt)) {
            /* h zeta^e = prod q^a  =>  log h = sum a log q - e */
            int ok = 1;
            uint64_t acc = 0;
            for (uint32_t i = 0; i < cnt; i++) {
                if (!ctx->fb_known[rel.col[i]]) { ok = 0; break; }
                acc = ca_addmod(acc, ca_mulmod((uint64_t)rel.val[i], ctx->fb_log[rel.col[i]], pm1), pm1);
            }
            if (ok) {
                acc = ca_submod(acc, e % pm1, pm1);
                /* verify */
                if (ca_mont_from(&m, ca_mont_pow(&m, zm, acc)) == h % p) { *out = acc; return CA_OK; }
            }
        }
        uint64_t step = 1 + ca_rng_below(&rng, 4095);
        cur = ca_mont_mul(&m, cur, ca_mont_pow(&m, zm, step));
        e = (e + step) % pm1;
    }
    return CA_ERR_LIMIT;
}

ca_status ca_ic_log(ca_ic_ctx *ctx, uint64_t h, uint64_t *x, ca_stats *st)
{
    if (!ctx || !x || ctx->p < 2) return CA_ERR_INVALID;
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

ca_status ca_ic_solve_checkpointed(uint64_t p, uint64_t g, uint64_t h,
                                   const ca_ic_params *params, const char *checkpoint_path,
                                   uint32_t progress_interval, uint64_t *x, ca_ic_stats *st)
{
    ca_ic_ctx *ctx;
    ca_ic_stats local;
    if (!st) st = &local;
    ca_status rc = ic_precompute_impl(p, g, params, checkpoint_path, progress_interval, &ctx, st);
    if (rc != CA_OK) return rc;
    double t0 = ca_now();
    if (ctx->params.verbose) fprintf(stderr, "[ic] solving individual logarithm for h=%" PRIu64 "\n", h);
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
