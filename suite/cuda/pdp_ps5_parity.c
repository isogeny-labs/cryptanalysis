/*
 * pdp_ps5_parity.c - replay a PS-0 verdict corpus through the PS-5 kernel's
 * CPU emulation and compare with the corpus.
 *
 *   pdp_ps5_parity --corpus corpus_l11.txt [--threads T] [--max-targets K]
 *                  [--expect-verdicts HEX] [--expect-roots HEX]
 *                  [--expect-program-sha HEX]
 *
 * One binary per rung: it is compiled against the generated header of that
 * rung's program (-DPS5_PARAMS_H) and linked with pdp_ps5_emulate.c built from
 * the same header.  For every target R of the corpus the driver does what the
 * `crypto` bit-sliced driver (examples/pdp_speedup/bskernel.rs) does around
 * the kernel:
 *   - lists the rational base points (abscissa below 2^l, ascending) and
 *     transposes them into blocks of 32 lanes;
 *   - computes the row points U+- = P_i1 +- R exactly, for every row;
 *   - tiles every pair (i1, i2 >= i1) into jobs of PS5_TASKS blocks, and checks
 *     that the tiling covers m(m+1)/2 pairs exactly;
 *   - runs the emulated kernel over all jobs (no early exit);
 *   - confirms every reported hit lane and recomputes every exceptional lane
 *     exactly (group-law reference), collecting the roots (x_i1, x_i2, t) with
 *     t < 2^l, sorted and de-duplicated;
 * and then compares, per target, the full root set and the verdict with the
 * corpus, and the verdict and root digests with the corpus' and with the
 * digests recorded by PS-0.  A hit lane the exact reference does not confirm
 * is a kernel defect and is counted as a mismatch.  A target the group-law
 * formulation may decide differently from the baseline (x_R = 0, in V, or
 * 1/x_R in V) is counted as unsupported and fails the run; PS-0's corpora have none.
 *
 * Wall times printed are of the CPU emulation on this host.  They are not a
 * device measurement and say nothing about one.
 */
#define _POSIX_C_SOURCE 200809L
#include <pthread.h>
#include <time.h>

#include "pdp_ps5_host.h"
#include "pdp_ps5_slp.h"

#define PS5_NO_JOB
#include "pdp_ps5_device.cuh"

int pdp_ps5_emulate(const ps5_u32 *jobs, ps5_u32 first, ps5_u32 count, const ps5_u32 *xb,
                    const ps5_u32 *yb, const ps5_u64 *rows, ps5_u32 m, ps5_u32 nblk,
                    ps5_u32 *nhits, Ps5Hit *hits, ps5_u32 cap);
void pdp_ps5_info(ps5_u32 out[8], const char **sha256);

#define HIT_CAP (1u << 15)
#define CHUNK_JOBS 16u

static double now_s(void)
{
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return (double)ts.tv_sec + 1e-9 * (double)ts.tv_nsec;
}

/* ── the emulated launch ─────────────────────────────────────────────── */

typedef struct {
    const ps5_u32 *jobs, *xb, *yb;
    const ps5_u64 *rows;
    ps5_u32 n_jobs, m, nblk;
    pthread_mutex_t mu;
    ps5_u32 next;
    Ps5Hit *out;     /* concatenated records */
    size_t n_out, cap_out;
    unsigned overflow;
} Launch;

static void *worker(void *arg)
{
    Launch *L = (Launch *)arg;
    Ps5Hit *buf = (Ps5Hit *)malloc(HIT_CAP * sizeof(Ps5Hit));
    for (;;) {
        pthread_mutex_lock(&L->mu);
        ps5_u32 first = L->next;
        L->next = first + CHUNK_JOBS < L->n_jobs ? first + CHUNK_JOBS : L->n_jobs;
        ps5_u32 count = L->next - first;
        pthread_mutex_unlock(&L->mu);
        if (count == 0) break;
        ps5_u32 nh = 0;
        pdp_ps5_emulate(L->jobs, first, count, L->xb, L->yb, L->rows, L->m, L->nblk, &nh, buf,
                        HIT_CAP);
        pthread_mutex_lock(&L->mu);
        if (nh > HIT_CAP) L->overflow++;
        else {
            if (L->n_out + nh > L->cap_out) {
                L->cap_out = (L->n_out + nh) * 2 + 64;
                L->out = (Ps5Hit *)realloc(L->out, L->cap_out * sizeof(Ps5Hit));
            }
            memcpy(L->out + L->n_out, buf, nh * sizeof(Ps5Hit));
            L->n_out += nh;
        }
        pthread_mutex_unlock(&L->mu);
    }
    free(buf);
    return NULL;
}

static int cmp_u32_rec(const void *a, const void *b)
{
    const Ps5Hit *x = (const Ps5Hit *)a, *y = (const Ps5Hit *)b;
    if (x->i1 != y->i1) return x->i1 < y->i1 ? -1 : 1;
    if (x->blk != y->blk) return x->blk < y->blk ? -1 : 1;
    return 0;
}

static void put_u64(Ps5Sha *s, uint64_t v)
{
    uint8_t b[8];
    for (int i = 0; i < 8; ++i) b[i] = (uint8_t)(v >> (8 * i));
    ps5_sha_update(s, b, 8);
}

static void put_u32(Ps5Sha *s, uint32_t v)
{
    uint8_t b[4];
    for (int i = 0; i < 4; ++i) b[i] = (uint8_t)(v >> (8 * i));
    ps5_sha_update(s, b, 4);
}

int main(int argc, char **argv)
{
    const char *corpus_path = NULL, *exp_v = NULL, *exp_r = NULL, *exp_p = NULL;
    int threads = 1;
    long max_targets = -1;
    for (int i = 1; i + 1 < argc; i += 2) {
        if (!strcmp(argv[i], "--corpus")) corpus_path = argv[i + 1];
        else if (!strcmp(argv[i], "--threads")) threads = atoi(argv[i + 1]);
        else if (!strcmp(argv[i], "--max-targets")) max_targets = atol(argv[i + 1]);
        else if (!strcmp(argv[i], "--expect-verdicts")) exp_v = argv[i + 1];
        else if (!strcmp(argv[i], "--expect-roots")) exp_r = argv[i + 1];
        else if (!strcmp(argv[i], "--expect-program-sha")) exp_p = argv[i + 1];
        else {
            fprintf(stderr, "unknown option %s\n", argv[i]);
            return 2;
        }
    }
    if (!corpus_path || threads < 1) {
        fprintf(stderr, "usage: %s --corpus FILE [--threads T] [--max-targets K] "
                        "[--expect-verdicts HEX] [--expect-roots HEX] [--expect-program-sha HEX]\n",
                argv[0]);
        return 2;
    }

    ps5_u32 info[8];
    const char *prog_sha;
    pdp_ps5_info(info, &prog_sha);
    unsigned mismatches = 0;
    if (info[0] != PS5_N || info[1] != PS5_L || info[2] != PS5_TASKS) {
        fprintf(stderr, "emulation object was built for another program\n");
        return 2;
    }
    if (exp_p && strcmp(exp_p, prog_sha) != 0) {
        fprintf(stderr, "program hash %s is not the expected %s\n", prog_sha, exp_p);
        return 2;
    }

    size_t clen;
    uint8_t *ctext = ps5_read_file(corpus_path, &clen);
    if (!ctext) {
        fprintf(stderr, "cannot read %s\n", corpus_path);
        return 2;
    }
    char corpus_sha[65];
    ps5_sha256_hex(ctext, clen, corpus_sha);
    Ps5Corpus corp;
    if (ps5_read_corpus((const char *)ctext, &corp) != 0) {
        fprintf(stderr, "cannot parse the corpus %s\n", corpus_path);
        return 2;
    }
    if (corp.l != PS5_L || corp.n != PS5_N) {
        fprintf(stderr, "corpus is l=%d n=%d, program is l=%d n=%d\n", corp.l, corp.n, PS5_L, PS5_N);
        return 2;
    }
    Ps5Gf gf = {corp.n, corp.modulus};
    if (!((corp.modulus >> corp.n) & 1u) || (corp.modulus >> (corp.n + 1)) != 0) {
        fprintf(stderr, "modulus 0x%llx is not of degree %d\n", (unsigned long long)corp.modulus, corp.n);
        return 2;
    }

    /* Base points: rational lifts of the abscissae of V, ascending. */
    const uint64_t span = 1ull << PS5_L;
    Ps5As as;
    ps5_as_init(&as, &gf);
    uint64_t *bx = (uint64_t *)malloc(span * sizeof(uint64_t));
    uint64_t *by = (uint64_t *)malloc(span * sizeof(uint64_t));
    ps5_u32 m = 0;
    for (uint64_t x = 0; x < span; ++x) {
        uint64_t y;
        if (ps5_lift(&gf, &as, x, &y)) {
            bx[m] = x;
            by[m] = y;
            ++m;
        }
    }
    const ps5_u32 nblk = (m + PS5_LANES - 1u) / PS5_LANES;
    ps5_u32 *xb = (ps5_u32 *)calloc((size_t)nblk * PS5_N, sizeof(ps5_u32));
    ps5_u32 *yb = (ps5_u32 *)calloc((size_t)nblk * PS5_N, sizeof(ps5_u32));
    for (ps5_u32 q = 0; q < m; ++q)
        for (int i = 0; i < PS5_N; ++i) {
            xb[(size_t)(q / PS5_LANES) * PS5_N + i] |= (ps5_u32)((bx[q] >> i) & 1u) << (q % PS5_LANES);
            yb[(size_t)(q / PS5_LANES) * PS5_N + i] |= (ps5_u32)((by[q] >> i) & 1u) << (q % PS5_LANES);
        }

    /* Jobs: row i1 against blocks i1/32 ... nblk-1, PS5_TASKS blocks at a time. */
    size_t cap_jobs = 1024, n_jobs = 0;
    ps5_u32 *jobs = (ps5_u32 *)malloc(cap_jobs * 2 * sizeof(ps5_u32));
    for (ps5_u32 i1 = 0; i1 < m; ++i1)
        for (ps5_u32 b0 = i1 / PS5_LANES; b0 < nblk; b0 += PS5_TASKS) {
            if (n_jobs == cap_jobs) {
                cap_jobs *= 2;
                jobs = (ps5_u32 *)realloc(jobs, cap_jobs * 2 * sizeof(ps5_u32));
            }
            jobs[2 * n_jobs] = i1;
            jobs[2 * n_jobs + 1] = b0;
            ++n_jobs;
        }
    uint64_t valid_pairs = 0;
    for (size_t j = 0; j < n_jobs; ++j)
        for (ps5_u32 k = 0; k < PS5_TASKS; ++k)
            valid_pairs += (uint64_t)__builtin_popcount(ps5_valid(jobs[2 * j], jobs[2 * j + 1] + k, m));
    const uint64_t want_pairs = (uint64_t)m * (m + 1u) / 2u;
    int tiling_ok = valid_pairs == want_pairs;
    if (!tiling_ok) ++mismatches;
    const uint64_t lane_slots = (uint64_t)n_jobs * PS5_TASKS * PS5_LANES;

    ps5_u64 *rows = (ps5_u64 *)malloc((size_t)m * 4 * sizeof(ps5_u64));
    Launch L;
    memset(&L, 0, sizeof L);
    pthread_mutex_init(&L.mu, NULL);
    L.jobs = jobs;
    L.xb = xb;
    L.yb = yb;
    L.rows = rows;
    L.n_jobs = (ps5_u32)n_jobs;
    L.m = m;
    L.nblk = nblk;

    Ps5Sha sv, sr;
    ps5_sha_init(&sv);
    ps5_sha_init(&sr);
    size_t n_targets = corp.n_targets;
    if (max_targets >= 0 && (size_t)max_targets < n_targets) n_targets = (size_t)max_targets;
    uint64_t hit_lanes = 0, hit_confirmed = 0, hit_unconfirmed = 0, exc_lanes = 0, exc_with_root = 0,
             records = 0, roots_total = 0, root_set_mismatch = 0, verdict_mismatch = 0,
             unsupported = 0, found_targets = 0, pairs_run = 0;
    double emu_secs = 0;
    uint64_t overflow = 0;

    for (size_t ti = 0; ti < n_targets; ++ti) {
        Ps5Target *t = &corp.t[ti];
        Ps5Pt R = {0, t->xr, t->yr};
        int bad_target = 0;
        if (ps5_degenerate(&gf, PS5_L, t->xr)) {
            ++unsupported;
            bad_target = 1;
        }
        if (!ps5_on_curve(&gf, t->xr, t->yr)) {
            fprintf(stderr, "target %u is not on the curve\n", t->idx);
            bad_target = 1;
        }
        uint64_t (*roots)[3] = NULL;
        size_t n_roots = 0, cap_roots = 16;
        roots = (uint64_t(*)[3])malloc(cap_roots * sizeof(uint64_t[3]));
        if (!bad_target) {
            for (ps5_u32 i1 = 0; i1 < m; ++i1) {
                Ps5Pt p1 = {0, bx[i1], by[i1]};
                Ps5Pt u = ps5_add(&gf, p1, R), v = ps5_add(&gf, p1, ps5_neg(R));
                if (u.inf || v.inf) {
                    fprintf(stderr, "row %u: P +- R is the point at infinity\n", i1);
                    bad_target = 1;
                    break;
                }
                rows[4 * i1] = u.x;
                rows[4 * i1 + 1] = u.y;
                rows[4 * i1 + 2] = v.x;
                rows[4 * i1 + 3] = v.y;
            }
        }
        if (!bad_target) {
            L.next = 0;
            L.n_out = 0;
            L.overflow = 0;
            double t0 = now_s();
            pthread_t th[64];
            if (threads > 64) threads = 64;
            for (int k = 0; k < threads; ++k) pthread_create(&th[k], NULL, worker, &L);
            for (int k = 0; k < threads; ++k) pthread_join(th[k], NULL);
            emu_secs += now_s() - t0;
            pairs_run += valid_pairs;
            overflow += L.overflow;
            records += L.n_out;
            qsort(L.out, L.n_out, sizeof(Ps5Hit), cmp_u32_rec);
            for (size_t r = 0; r < L.n_out; ++r) {
                const Ps5Hit *h = &L.out[r];
                for (int pass = 0; pass < 2; ++pass) {
                    ps5_u32 bits = pass == 0 ? h->hit : h->exc;
                    while (bits) {
                        const int j = __builtin_ctz(bits);
                        bits &= bits - 1u;
                        const ps5_u32 i2 = h->blk * PS5_LANES + (ps5_u32)j;
                        if (i2 >= m || i2 < h->i1) {
                            ++mismatches;
                            continue;
                        }
                        Ps5Pt p1 = {0, bx[h->i1], by[h->i1]}, p2 = {0, bx[i2], by[i2]};
                        uint64_t th3[4];
                        int ok[4], any = 0;
                        ps5_thirds(&gf, p1, p2, R, th3, ok);
                        for (int q = 0; q < 4; ++q) {
                            if (!ok[q] || th3[q] >= span) continue;
                            any = 1;
                            if (n_roots == cap_roots) {
                                cap_roots *= 2;
                                roots = (uint64_t(*)[3])realloc(roots, cap_roots * sizeof(uint64_t[3]));
                            }
                            uint64_t a = bx[h->i1], b = bx[i2], c = th3[q], tmp;
                            if (a > b) { tmp = a; a = b; b = tmp; }
                            if (b > c) { tmp = b; b = c; c = tmp; }
                            if (a > b) { tmp = a; a = b; b = tmp; }
                            roots[n_roots][0] = a;
                            roots[n_roots][1] = b;
                            roots[n_roots][2] = c;
                            ++n_roots;
                        }
                        if (pass == 0) {
                            ++hit_lanes;
                            if (any) ++hit_confirmed;
                            else ++hit_unconfirmed;
                        } else {
                            ++exc_lanes;
                            if (any) ++exc_with_root;
                        }
                    }
                }
            }
            qsort(roots, n_roots, sizeof(uint64_t[3]), ps5_cmp3);
            size_t w = 0;
            for (size_t r = 0; r < n_roots; ++r)
                if (w == 0 || ps5_cmp3(roots[w - 1], roots[r]) != 0) memcpy(roots[w++], roots[r], sizeof(uint64_t[3]));
            n_roots = w;
        }
        /* Compare with the corpus. */
        int same = !bad_target && n_roots == t->n_roots;
        for (size_t r = 0; same && r < n_roots; ++r)
            if (ps5_cmp3(roots[r], t->roots[r]) != 0) same = 0;
        if (!same) ++root_set_mismatch;
        const int found = n_roots > 0;
        if (found != t->found) ++verdict_mismatch;
        if (found) ++found_targets;
        roots_total += n_roots;
        /* The digests are built from what the kernel path produced. */
        {
            uint8_t head[1] = {(uint8_t)t->planted};
            ps5_sha_update(&sv, head, 1);
            ps5_sha_update(&sr, head, 1);
            put_u64(&sv, t->xr);
            put_u64(&sr, t->xr);
            uint8_t f1[1] = {(uint8_t)found};
            ps5_sha_update(&sv, f1, 1);
            ps5_sha_update(&sr, f1, 1);
            put_u32(&sr, (uint32_t)n_roots);
            for (size_t r = 0; r < n_roots; ++r)
                for (int k = 0; k < 3; ++k) put_u64(&sr, roots[r][k]);
        }
        free(roots);
    }

    char dv[65], dr[65];
    ps5_sha_final_hex(&sv, dv);
    ps5_sha_final_hex(&sr, dr);
    const int full = n_targets == corp.n_targets;
    const int dv_corpus = full && strcmp(dv, corp.digest_verdicts) == 0;
    const int dr_corpus = full && strcmp(dr, corp.digest_roots) == 0;
    const int dv_expect = exp_v ? strcmp(dv, exp_v) == 0 : -1;
    const int dr_expect = exp_r ? strcmp(dr, exp_r) == 0 : -1;
    mismatches += (unsigned)(root_set_mismatch + verdict_mismatch + unsupported + hit_unconfirmed + overflow);
    if (full && (!dv_corpus || !dr_corpus)) ++mismatches;
    if (dv_expect == 0 || dr_expect == 0) ++mismatches;

    printf("{\"tool\":\"pdp_ps5_parity\",\"what\":\"CPU emulation of the PS-5 kernel; not a device result\","
           "\"l\":%d,\"n\":%d,\"program_sha256\":\"%s\",\"corpus\":\"%s\",\"corpus_sha256\":\"%s\","
           "\"targets\":%zu,\"targets_in_corpus\":%zu,\"base_points\":%u,\"blocks\":%u,\"jobs\":%zu,"
           "\"lane_slots\":%llu,\"valid_pairs_per_target\":%llu,\"pairs_replayed\":%llu,"
           "\"tiling_covers_each_pair_once\":%s,\"records\":%llu,\"hit_lanes\":%llu,"
           "\"hit_lanes_confirmed\":%llu,\"hit_lanes_unconfirmed\":%llu,\"exceptional_lanes\":%llu,"
           "\"exceptional_lanes_with_root\":%llu,\"roots_found\":%llu,\"targets_with_roots\":%llu,"
           "\"root_set_mismatches\":%llu,\"verdict_mismatches\":%llu,\"unsupported_targets\":%llu,"
           "\"hit_list_overflows\":%llu,\"digest_verdicts\":\"%s\",\"digest_verdicts_corpus_file\":\"%s\","
           "\"digest_roots\":\"%s\",\"digest_roots_corpus_file\":\"%s\",\"digest_verdicts_equal_corpus\":%s,"
           "\"digest_roots_equal_corpus\":%s,\"digest_verdicts_equal_expected\":%d,"
           "\"digest_roots_equal_expected\":%d,\"gates_fused_per_run\":%u,\"gates_unfused_per_run\":%u,"
           "\"threads\":%d,\"emulation_secs\":%.3f,\"mismatches\":%u}\n",
           PS5_L, PS5_N, prog_sha, corpus_path, corpus_sha, n_targets, corp.n_targets, m, nblk, n_jobs,
           (unsigned long long)lane_slots, (unsigned long long)want_pairs, (unsigned long long)pairs_run,
           tiling_ok ? "true" : "false", (unsigned long long)records, (unsigned long long)hit_lanes,
           (unsigned long long)hit_confirmed, (unsigned long long)hit_unconfirmed,
           (unsigned long long)exc_lanes, (unsigned long long)exc_with_root, (unsigned long long)roots_total,
           (unsigned long long)found_targets, (unsigned long long)root_set_mismatch,
           (unsigned long long)verdict_mismatch, (unsigned long long)unsupported,
           (unsigned long long)overflow, dv, corp.digest_verdicts, dr, corp.digest_roots,
           dv_corpus ? "true" : "false", dr_corpus ? "true" : "false", dv_expect, dr_expect,
           info[4], info[5], threads, emu_secs, mismatches);
    return mismatches ? 1 : 0;
}
