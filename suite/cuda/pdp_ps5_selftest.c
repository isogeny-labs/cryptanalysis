/*
 * pdp_ps5_selftest.c - checks of the PS-5 emulation that do not depend on the
 * PS-0 corpus, which has few positive pairs (a handful of roots per rung).
 *
 *   pdp_ps5_selftest --corpus corpus_lL.txt --program PROGRAM.slp [--reps R] [--seed S]
 *
 * 1. Truth tables.  Each of the five immediates (PS5_LUT_*) is checked against
 *    the C operator it stands for on all 8 input combinations (which determine
 *    a ternary function), and the host model of lop3 against the operators on
 *    random words.
 * 2. Every wire.  Jobs with random row values and random block tables are run
 *    through the emulated kernel (the job path of pdp_ps5_device.cuh) and the
 *    program file is interpreted independently (pdp_ps5_slp.h) on input planes
 *    built here from the same tables; all PS5_OPS wires must agree.  This checks
 *    the emitter, the chunking and the gate model against the program, on data
 *    where every wire is exercised.
 * 3. The function.  Rows and partner points are built so that about a third of
 *    the lanes make one of the four candidates fall in V (and some lanes have a
 *    zero denominator or a candidate just outside V); the kernel's hit and
 *    exceptional masks must equal a scalar GF(2^n) evaluation of the formulas
 *    of examples/pdp_speedup/kernel.rs, lane by lane, through the whole job path
 *    (input planes, valid masks, record list).
 */
#include "pdp_ps5_host.h"
#include "pdp_ps5_slp.h"

#define PS5_NO_JOB
#include "pdp_ps5_device.cuh"

int pdp_ps5_emulate(const ps5_u32 *jobs, ps5_u32 first, ps5_u32 count, const ps5_u32 *xb,
                    const ps5_u32 *yb, const ps5_u64 *rows, ps5_u32 m, ps5_u32 nblk,
                    ps5_u32 *nhits, Ps5Hit *hits, ps5_u32 cap);
void pdp_ps5_last_wires(ps5_u32 *dst);

static uint64_t rnd_n(Ps5Rng *r, int n) { return ps5_rng_next(r) & ((1ull << n) - 1u); }

#define NROWS 4u
#define NBLK 64u

int main(int argc, char **argv)
{
    const char *corpus_path = NULL, *prog_path = NULL;
    long reps = 100;
    uint64_t seed = 20261018;
    for (int i = 1; i + 1 < argc; i += 2) {
        if (!strcmp(argv[i], "--corpus")) corpus_path = argv[i + 1];
        else if (!strcmp(argv[i], "--program")) prog_path = argv[i + 1];
        else if (!strcmp(argv[i], "--reps")) reps = atol(argv[i + 1]);
        else if (!strcmp(argv[i], "--seed")) seed = strtoull(argv[i + 1], NULL, 10);
        else return 2;
    }
    if (!corpus_path || !prog_path) return 2;
    size_t len;
    uint8_t *ct = ps5_read_file(corpus_path, &len);
    Ps5Corpus corp;
    if (!ct || ps5_read_corpus((const char *)ct, &corp) != 0 || corp.n != PS5_N || corp.l != PS5_L) {
        fprintf(stderr, "bad corpus\n");
        return 2;
    }
    Ps5Gf gf = {corp.n, corp.modulus};
    uint8_t *pb = ps5_read_file(prog_path, &len);
    Ps5Prog prog;
    char err[256];
    if (!pb || ps5_slp_parse(pb, len, &prog, err, sizeof err) != 0 || prog.n_ops != PS5_OPS) {
        fprintf(stderr, "bad program\n");
        return 2;
    }
    unsigned long long bad = 0;

    /* 1. truth tables */
    int lut_ok = 1;
    {
        const unsigned A = 0xF0, B = 0xCC, C = 0xAA;
        lut_ok &= PS5_LUT_XOR == ((A ^ B) & 0xFF);
        lut_ok &= PS5_LUT_AND == ((A & B) & 0xFF);
        lut_ok &= PS5_LUT_OR == ((A | B) & 0xFF);
        lut_ok &= PS5_LUT_NOT == ((~A) & 0xFF);
        lut_ok &= PS5_LUT_XAND == ((A ^ (B & C)) & 0xFF);
        Ps5Rng r = {seed};
        for (int it = 0; it < 4096; ++it) {
            ps5_u32 a = (ps5_u32)ps5_rng_next(&r), b = (ps5_u32)ps5_rng_next(&r), c = (ps5_u32)ps5_rng_next(&r);
            lut_ok &= ps5_lop3(a, b, b, PS5_LUT_XOR) == (a ^ b);
            lut_ok &= ps5_lop3(a, b, b, PS5_LUT_AND) == (a & b);
            lut_ok &= ps5_lop3(a, b, b, PS5_LUT_OR) == (a | b);
            lut_ok &= ps5_lop3(a, a, a, PS5_LUT_NOT) == ~a;
            lut_ok &= ps5_lop3(a, b, c, PS5_LUT_XAND) == (a ^ (b & c));
        }
        /* all 256 immediates against the definition: bit (4a+2b+c) of lut */
        for (unsigned lut = 0; lut < 256; ++lut)
            for (unsigned idx = 0; idx < 8; ++idx) {
                ps5_u32 a = (idx & 4u) ? ~0u : 0u, b = (idx & 2u) ? ~0u : 0u, c = (idx & 1u) ? ~0u : 0u;
                lut_ok &= ((ps5_lop3(a, b, c, lut) & 1u) == ((lut >> idx) & 1u));
            }
    }
    if (!lut_ok) ++bad;

    /* Tables for the job path: NROWS rows, NBLK blocks, 8-block jobs. */
    const ps5_u32 m = NBLK * PS5_LANES;
    uint64_t wire_checked = 0, wire_bad = 0, lanes = 0, ref_hits = 0, ref_exc = 0, lane_bad = 0,
             forced_by_mode[8] = {0};
    ps5_u32 *xb = (ps5_u32 *)malloc((size_t)NBLK * PS5_N * 4), *yb = (ps5_u32 *)malloc((size_t)NBLK * PS5_N * 4);
    uint64_t *x2 = (uint64_t *)malloc(m * 8), *y2 = (uint64_t *)malloc(m * 8);
    ps5_u64 rows[NROWS * 4];
    ps5_u32 jobs[2 * NROWS * (NBLK / PS5_TASKS)];
    ps5_u32 *wires = (ps5_u32 *)malloc((size_t)PS5_OPS * 4), *iw = (ps5_u32 *)malloc((size_t)PS5_OPS * 4);
    ps5_u32 *inputs = (ps5_u32 *)malloc((size_t)PS5_INPUTS * 4);
    Ps5Rng rng = {seed};
    Ps5Hit *hits = (Ps5Hit *)malloc(sizeof(Ps5Hit) * (1u << 15));
    const uint64_t span = 1ull << PS5_L;

    for (long rep = 0; rep < reps; ++rep) {
        for (ps5_u32 r = 0; r < NROWS; ++r)
            for (int f = 0; f < 4; ++f) rows[4 * r + f] = rnd_n(&rng, PS5_N);
        for (ps5_u32 q = 0; q < m; ++q) {
            const ps5_u32 r = q % NROWS;
            const int mode = (int)(ps5_rng_next(&rng) % 8u);
            const uint64_t xu = rows[4 * r], yu = rows[4 * r + 1], xv = rows[4 * r + 2], yv = rows[4 * r + 3];
            uint64_t xr = rnd_n(&rng, PS5_N), yr = rnd_n(&rng, PS5_N);
            int forced = 0;
            if ((mode >= 1 && mode <= 4) || mode == 7) {
                const int vchain = (mode == 3 || mode == 4);
                const uint64_t cx = vchain ? xv : xu, cy = vchain ? yv : yu;
                uint64_t s = rnd_n(&rng, PS5_L), lam = rnd_n(&rng, PS5_N);
                if (mode == 7) s |= span; /* just outside V */
                uint64_t d = s ^ 1u ^ ps5_gf_sqr(&gf, lam) ^ lam;
                if (d != 0) {
                    const uint64_t cxr = cx ^ d;
                    uint64_t l1 = lam;
                    if (mode == 2 || mode == 4) l1 = lam ^ ps5_gf_mul(&gf, cxr, ps5_gf_inv(&gf, d));
                    xr = cxr;
                    yr = cy ^ ps5_gf_mul(&gf, l1, d);
                    forced = 1;
                }
            } else if (mode == 5) {
                xr = xu;
                forced = 1;
            } else if (mode == 6) {
                xr = xv;
                forced = 1;
            }
            forced_by_mode[forced ? mode : 0]++;
            x2[q] = xr;
            y2[q] = yr;
        }
        memset(xb, 0, (size_t)NBLK * PS5_N * 4);
        memset(yb, 0, (size_t)NBLK * PS5_N * 4);
        for (ps5_u32 q = 0; q < m; ++q)
            for (int i = 0; i < PS5_N; ++i) {
                xb[(size_t)(q / PS5_LANES) * PS5_N + i] |= (ps5_u32)((x2[q] >> i) & 1u) << (q % PS5_LANES);
                yb[(size_t)(q / PS5_LANES) * PS5_N + i] |= (ps5_u32)((y2[q] >> i) & 1u) << (q % PS5_LANES);
            }
        ps5_u32 nj = 0;
        for (ps5_u32 r = 0; r < NROWS; ++r)
            for (ps5_u32 b0 = 0; b0 < NBLK; b0 += PS5_TASKS) {
                jobs[2 * nj] = r;
                jobs[2 * nj + 1] = b0;
                ++nj;
            }
        ps5_u32 nh = 0;
        pdp_ps5_emulate(jobs, 0, nj, xb, yb, rows, m, NBLK, &nh, hits, 1u << 15);
        if (nh > (1u << 15)) { ++bad; continue; }

        /* 2. every wire, on a few jobs, against the interpreter */
        if (rep < 8) {
            for (ps5_u32 jb = 0; jb < nj; jb += nj / 4u) {
                ps5_u32 nh2 = 0;
                pdp_ps5_emulate(jobs, jb, 1, xb, yb, rows, m, NBLK, &nh2, hits + nh, 64);
                pdp_ps5_last_wires(wires);
                const ps5_u32 i1 = jobs[2 * jb], blk0 = jobs[2 * jb + 1];
                for (ps5_u32 k = 0; k < PS5_INPUTS; ++k) {
                    const ps5_u32 t = k / (6u * PS5_N), f = (k % (6u * PS5_N)) / PS5_N, i = k % PS5_N;
                    const ps5_u32 blk = blk0 + t < NBLK ? blk0 + t : NBLK - 1u;
                    ps5_u32 w;
                    if (f < 4) w = ((rows[4 * i1 + f] >> i) & 1u) ? ~0u : 0u;
                    else if (f == 4) w = xb[(size_t)blk * PS5_N + i];
                    else w = yb[(size_t)blk * PS5_N + i];
                    inputs[k] = w;
                }
                ps5_slp_eval(&prog, inputs, iw);
                for (ps5_u32 k = 0; k < PS5_OPS; ++k) {
                    ++wire_checked;
                    if (wires[k] != iw[k]) ++wire_bad;
                }
            }
        }

        /* 3. the function, lane by lane */
        static ps5_u32 khit[NROWS][NBLK * PS5_LANES / 32], kexc[NROWS][NBLK * PS5_LANES / 32];
        memset(khit, 0, sizeof khit);
        memset(kexc, 0, sizeof kexc);
        for (ps5_u32 h = 0; h < nh; ++h) {
            khit[hits[h].i1][hits[h].blk] |= hits[h].hit;
            kexc[hits[h].i1][hits[h].blk] |= hits[h].exc;
        }
        for (ps5_u32 r = 0; r < NROWS; ++r) {
            const uint64_t xu = rows[4 * r], yu = rows[4 * r + 1], xv = rows[4 * r + 2], yv = rows[4 * r + 3];
            for (ps5_u32 q = r; q < m; ++q) { /* partners q >= r are the row's pairs */
                const uint64_t dU = xu ^ x2[q], dV = xv ^ x2[q];
                const int exc = dU == 0 || dV == 0;
                int hit = 0;
                if (!exc) {
                    const uint64_t jU = ps5_gf_inv(&gf, dU), jV = ps5_gf_inv(&gf, dV);
                    const uint64_t lam = ps5_gf_mul(&gf, yu ^ y2[q], jU);
                    const uint64_t t1 = ps5_gf_sqr(&gf, lam) ^ lam ^ dU ^ 1u;
                    const uint64_t lam2 = lam ^ ps5_gf_mul(&gf, x2[q], jU);
                    const uint64_t t2 = ps5_gf_sqr(&gf, lam2) ^ lam2 ^ dU ^ 1u;
                    const uint64_t mu = ps5_gf_mul(&gf, yv ^ y2[q], jV);
                    const uint64_t t3 = ps5_gf_sqr(&gf, mu) ^ mu ^ dV ^ 1u;
                    const uint64_t mu2 = mu ^ ps5_gf_mul(&gf, x2[q], jV);
                    const uint64_t t4 = ps5_gf_sqr(&gf, mu2) ^ mu2 ^ dV ^ 1u;
                    hit = t1 < span || t2 < span || t3 < span || t4 < span;
                }
                const int kh = (khit[r][q / PS5_LANES] >> (q % PS5_LANES)) & 1u;
                const int ke = (kexc[r][q / PS5_LANES] >> (q % PS5_LANES)) & 1u;
                ++lanes;
                ref_hits += (uint64_t)hit;
                ref_exc += (uint64_t)exc;
                if (kh != hit || ke != exc) ++lane_bad;
            }
        }
    }
    if (wire_bad || lane_bad) ++bad;
    printf("{\"tool\":\"pdp_ps5_selftest\",\"what\":\"CPU emulation of the PS-5 kernel; not a device result\","
           "\"l\":%d,\"n\":%d,\"program_sha256\":\"%s\",\"seed\":%llu,\"reps\":%ld,"
           "\"lut_tables_ok\":%s,\"wires_compared\":%llu,\"wire_mismatches\":%llu,"
           "\"lanes_compared\":%llu,\"reference_hit_lanes\":%llu,\"reference_exceptional_lanes\":%llu,"
           "\"lane_mismatches\":%llu,\"lane_modes\":{\"random\":%llu,\"t1\":%llu,\"t2\":%llu,\"t3\":%llu,"
           "\"t4\":%llu,\"zero_den_u\":%llu,\"zero_den_v\":%llu,\"near_miss\":%llu},\"failed\":%llu}\n",
           PS5_L, PS5_N, PS5_PROGRAM_SHA256, (unsigned long long)seed, reps, lut_ok ? "true" : "false",
           (unsigned long long)wire_checked, (unsigned long long)wire_bad, (unsigned long long)lanes,
           (unsigned long long)ref_hits, (unsigned long long)ref_exc, (unsigned long long)lane_bad,
           (unsigned long long)forced_by_mode[0], (unsigned long long)forced_by_mode[1],
           (unsigned long long)forced_by_mode[2], (unsigned long long)forced_by_mode[3],
           (unsigned long long)forced_by_mode[4], (unsigned long long)forced_by_mode[5],
           (unsigned long long)forced_by_mode[6], (unsigned long long)forced_by_mode[7], bad);
    return bad ? 1 : 0;
}
