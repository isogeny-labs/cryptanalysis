/* GPU rho: device arithmetic checked against the host library, and the
 * full pipeline run through the emulator (and the CUDA backend when a
 * device is present). */
#include "test_fixtures.h"
#include "gpu_internal.h"
#include "dlog_checkpoint_internal.h"
#include <math.h>

static int write_checkpoint_header(const char *path, gpu_rho_checkpoint_header h)
{
    h.checksum = 0;
    h.checksum = dlog_ckpt_hash(&h, sizeof(h), UINT64_C(14695981039346656037));
    FILE *f = fopen(path, "wb");
    if (!f) return 0;
    int ok = fwrite(&h, sizeof(h), 1, f) == 1;
    return fclose(f) == 0 && ok;
}

static void test_checkpoint_metadata(void)
{
    char directory[] = "/tmp/ca-gpu-metadata-XXXXXX";
    CHECK(mkdtemp(directory) != NULL);
    char path[160], progress[180];
    snprintf(path, sizeof(path), "%s/state", directory);
    snprintf(progress, sizeof(progress), "%s.progress.json", path);
    ca_group g;
    ca_elem base, target;
    fx_zp_safe(&g, &base, 2000000579ULL);
    fx_instance(&g, &base, 42, &target);
    ca_gpu_rho_params p;
    ca_gpu_rho_params_default(&p);
    p.backend = CA_GPU_BACKEND_EMULATE;
    p.seed = 4;
    p.r = 4;
    p.blocks = 1;
    p.threads_per_block = 1;
    p.steps_per_launch = 1;
    p.dp_bits = 4;
    p.max_ops = 1;
    uint64_t answer = 0;
    ca_status rc =
        ca_gpu_rho_solve_checkpointed(&g, &base, &target, &p, path, 1, 1, 0, &answer, NULL);
    CHECK(rc == CA_ERR_LIMIT);
    FILE *f = fopen(path, "rb");
    CHECK(f != NULL);
    if (!f) return;
    gpu_rho_checkpoint_header original;
    int ok = fread(&original, sizeof(original), 1, f) == 1 && fgetc(f) == EOF;
    fclose(f);
    CHECK(ok && original.entries == 0);
    if (!ok || original.entries) return;
    const double invalid_elapsed[] = {INFINITY, NAN, -1.0};
    for (size_t i = 0; i < sizeof(invalid_elapsed) / sizeof(invalid_elapsed[0]); i++) {
        gpu_rho_checkpoint_header h = original;
        h.elapsed_seconds = invalid_elapsed[i];
        CHECK(write_checkpoint_header(path, h));
        CHECK(ca_gpu_rho_solve_checkpointed(&g, &base, &target, &p, path, 1, 1, 0, &answer, NULL) ==
              CA_ERR_INTERNAL);
    }
    for (unsigned field = 0; field < 3; field++) {
        gpu_rho_checkpoint_header h = original;
        if (field == 0) h.launches = UINT64_MAX;
        if (field == 1) h.dps = UINT64_MAX;
        if (field == 2) h.restarts = 1;
        CHECK(write_checkpoint_header(path, h));
        CHECK(ca_gpu_rho_solve_checkpointed(&g, &base, &target, &p, path, 1, 1, 0, &answer, NULL) ==
              CA_ERR_INTERNAL);
    }
    gpu_rho_checkpoint_header h = original;
    h.ops = UINT64_MAX;
    CHECK(write_checkpoint_header(path, h));
    CHECK(ca_gpu_rho_solve_checkpointed(&g, &base, &target, &p, path, 1, 1, 0, &answer, NULL) ==
          CA_ERR_INTERNAL);
    h = original;
    h.ops = UINT64_MAX - original.ops;
    CHECK(write_checkpoint_header(path, h));
    p.max_ops = UINT64_MAX;
    ca_stats stats = {0};
    CHECK(ca_gpu_rho_solve_checkpointed(&g, &base, &target, &p, path, 1, 1, 0, &answer, &stats) ==
          CA_ERR_LIMIT);
    CHECK_EQ_U64(stats.group_ops, UINT64_MAX);
    CHECK_EQ_U64(stats.reserved, 0);
    p.max_ops = 1;
    h = original;
    h.solved = 2;
    h.result = 42;
    CHECK(write_checkpoint_header(path, h));
    CHECK(ca_gpu_rho_solve_checkpointed(&g, &base, &target, &p, path, 1, 1, 0, &answer, NULL) ==
          CA_ERR_INTERNAL);
    h = original;
    h.solved = 1;
    h.result = 42;
    CHECK(write_checkpoint_header(path, h));
    CHECK(ca_gpu_rho_solve_checkpointed(&g, &base, &target, &p, path, 1, 1, 0, &answer, NULL) ==
          CA_OK);
    CHECK_EQ_U64(answer, 42);
    unlink(path);
    unlink(progress);
    rmdir(directory);
}

static void test_dp_capacity(void)
{
    const uint32_t values[] = {0, 1, 522239, 522240, UINT32_MAX - 7u, UINT32_MAX};
    for (unsigned d = 0; d < 64; d++) {
        for (size_t i = 0; i < sizeof(values) / sizeof(values[0]); i++) {
            for (size_t j = 0; j < sizeof(values) / sizeof(values[0]); j++) {
                __uint128_t exact = ((__uint128_t)values[i] * values[j] * 2) >> d;
                exact += 4096;
                if (exact > (1u << 20)) exact = 1u << 20;
                CHECK_EQ_U64(ca_gpu_dp_capacity(values[i], values[j], d), (uint64_t)exact);
            }
        }
    }
    /* Largest accepted walk herd and launch length: the previous double-to-
     * uint64_t conversion overflowed before the intended saturation. */
    CHECK_EQ_U64(ca_gpu_dp_capacity(UINT32_MAX - 7u, UINT32_MAX, 0), 1u << 20);
    CHECK_EQ_U64(ca_gpu_dp_capacity(522239, 1, 0), (1u << 20) - 2);
    CHECK_EQ_U64(ca_gpu_dp_capacity(522240, 1, 0), 1u << 20);
}

static void test_device_arith(void)
{
    ca_rng rng;
    ca_rng_seed(&rng, 4);
    uint64_t mods[] = {1000003, 4294967311ULL, 1099511627791ULL, 9223372036854775837ULL,
                       18446744073709551557ULL};
    for (size_t i = 0; i < sizeof(mods) / sizeof(mods[0]); i++) {
        ca_mont m;
        CHECK(ca_mont_init(&m, mods[i]));
        for (int k = 0; k < 5000; k++) {
            uint64_t a = ca_rng_below(&rng, mods[i]), b = ca_rng_below(&rng, mods[i]);
            CHECK_EQ_U64(ca_dev_mont_mul(a, b, m.p, m.pinv), ca_mont_mul(&m, a, b));
            CHECK_EQ_U64(ca_dev_addmod(a, b, m.p), ca_addmod(a, b, m.p));
            CHECK_EQ_U64(ca_dev_submod(a, b, m.p), ca_submod(a, b, m.p));
        }
        if (ca_is_prime(mods[i])) {
            for (int k = 0; k < 200; k++) {
                uint64_t a = 1 + ca_rng_below(&rng, mods[i] - 1);
                CHECK_EQ_U64(ca_dev_mont_inv(a, m.p, m.pinv, m.r1), ca_mont_inv(&m, a));
            }
        }
    }
    /* group op and scalar multiplication on a curve vs the host group */
    ca_group g;
    ca_elem gen;
    fx_ec(&g, &gen, 1000000007ULL, 3, 11);
    ca_gpu_rho_args a;
    memset(&a, 0, sizeof(a));
    a.p = g.p;
    a.pinv = g.mont.pinv;
    a.one = g.mont.r1;
    a.a_mont = g.a_mont;
    a.n = g.order;
    a.kind = CA_GPU_KIND_EC;
    for (int k = 0; k < 200; k++) {
        ca_elem P, Q, R;
        ca_ec_random_point(&g, &P, 50 + k);
        ca_ec_random_point(&g, &Q, 900 + k);
        if (k % 7 == 0) Q = P;                     /* doubling */
        if (k % 11 == 0) ca_group_inv(&g, &Q, &P); /* inverse pair -> infinity */
        ca_group_op(&g, &R, &P, &Q);
        uint64_t x = P.w[0], y = P.w[1];
        ca_dev_op(&a, &x, &y, Q.w[0], Q.w[1]);
        if (R.w[2])
            CHECK_EQ_U64(x, g.p);
        else {
            CHECK_EQ_U64(x, R.w[0]);
            CHECK_EQ_U64(y, R.w[1]);
        }
        uint64_t kk = ca_rng_below(&rng, g.order);
        ca_group_mul(&g, &R, &P, kk, NULL);
        ca_dev_mul(&a, &x, &y, P.w[0], P.w[1], kk);
        if (R.w[2])
            CHECK_EQ_U64(x, g.p);
        else {
            CHECK_EQ_U64(x, R.w[0]);
            CHECK_EQ_U64(y, R.w[1]);
        }
        CHECK_EQ_U64(ca_dev_hash(CA_GPU_KIND_EC, P.w[0], P.w[1], g.p), ca_group_hash(&g, &P));
    }
    /* Z_p^* hash and op */
    ca_group z;
    ca_elem zg;
    fx_zp_safe(&z, &zg, 2000000579ULL);
    a.p = z.p;
    a.pinv = z.mont.pinv;
    a.one = z.mont.r1;
    a.kind = CA_GPU_KIND_ZP;
    a.n = z.order;
    ca_elem h;
    ca_group_mul(&z, &h, &zg, 777, NULL);
    uint64_t x = zg.w[0], y = 0;
    ca_dev_mul(&a, &x, &y, zg.w[0], 0, 777);
    CHECK_EQ_U64(x, h.w[0]);
    CHECK_EQ_U64(ca_dev_hash(CA_GPU_KIND_ZP, h.w[0], 0, z.p), ca_group_hash(&z, &h));
}

/*
 * Run the kernel body directly over host buffers and check the invariant
 * that defines a correct walk: every walk state must satisfy
 * Y = a*base + b*target, with a and b the exponents the kernel maintains.
 * This is what catches a sign error in the negation-map exponent update or
 * in a cycle escape, independently of whether a solve happens to succeed.
 */
static void test_walk_invariant(const ca_group *g, const ca_elem *base, const ca_elem *target,
                                int negmap, uint32_t nthreads, uint32_t steps, const char *label)
{
    ca_gpu_rho_args a;
    memset(&a, 0, sizeof(a));
    a.p = g->p;
    a.pinv = g->mont.pinv;
    a.one = g->mont.r1;
    a.a_mont = g->a_mont;
    a.n = g->order;
    a.kind = g->kind == CA_GROUP_EC ? CA_GPU_KIND_EC : CA_GPU_KIND_ZP;
    a.negmap = negmap && g->kind == CA_GROUP_EC;
    a.seed = 0xC0FFEE;
    a.r = 32;
    a.steps = steps;
    a.nthreads = nthreads;
    a.dp_mask = 0xff; /* plenty of distinguished points */
    a.abandon_shift = 8;
    a.base_x = base->w[0];
    a.base_y = base->w[1];
    if (a.kind == CA_GPU_KIND_EC && base->w[2]) a.base_x = g->p;
    a.target_x = target->w[0];
    a.target_y = target->w[1];
    if (a.kind == CA_GPU_KIND_EC && target->w[2]) a.target_x = g->p;

    size_t nwalks = (size_t)nthreads * CA_GPU_W;
    uint64_t *mult = calloc((size_t)a.r * 4, sizeof(uint64_t));
    uint64_t *state = calloc(nwalks * 4, sizeof(uint64_t));
    uint64_t *aux = calloc(nwalks * CA_GPU_AUX, sizeof(uint64_t));
    uint64_t *dp = calloc((size_t)4096 * 4, sizeof(uint64_t));
    uint8_t *restart = malloc(nwalks);
    uint32_t dp_count = 0;
    CHECK(mult && state && aux && dp && restart);
    if (!mult || !state || !aux || !dp || !restart) {
        free(mult);
        free(state);
        free(aux);
        free(dp);
        free(restart);
        return;
    }
    memset(restart, 1, nwalks);
    ca_rng rng;
    ca_rng_seed(&rng, 4242);
    for (uint32_t i = 0; i < a.r; i++) {
        uint64_t al = ca_rng_below(&rng, g->order), be = ca_rng_below(&rng, g->order);
        ca_elem t1 = {{0}}, t2 = {{0}}, m = {{0}};
        ca_group_mul(g, &t1, base, al, NULL);
        ca_group_mul(g, &t2, target, be, NULL);
        ca_group_op(g, &m, &t1, &t2);
        mult[4 * (size_t)i] = (a.kind == CA_GPU_KIND_EC && m.w[2]) ? g->p : m.w[0];
        mult[4 * (size_t)i + 1] = m.w[1];
        mult[4 * (size_t)i + 2] = al;
        mult[4 * (size_t)i + 3] = be;
    }
    a.mult = mult;
    a.state = state;
    a.aux = aux;
    a.dp_out = dp;
    a.dp_count = &dp_count;
    a.dp_cap = 4096;
    a.restart = restart;

    int bad = 0;
    uint32_t dps_total = 0;
    for (int launch = 0; launch < 3; launch++) {
        dp_count = 0;
        for (uint32_t tid = 0; tid < nthreads; tid++) ca_dev_rho_thread(&a, tid);
        dps_total += dp_count;
        for (size_t w = 0; w < nwalks; w++) {
            uint64_t wx = state[4 * w];
            uint64_t wa = state[4 * w + 2], wb = state[4 * w + 3];
            ca_elem lhs, t1, t2;
            if (a.kind == CA_GPU_KIND_EC && wx == g->p) {
                ca_group_identity(g, &lhs);
            } else {
                lhs.w[0] = wx;
                lhs.w[1] = a.kind == CA_GPU_KIND_EC ? state[4 * w + 1] : 0;
                lhs.w[2] = 0;
                lhs.w[3] = 0;
                CHECK(ca_group_is_valid(g, &lhs));
            }
            ca_group_mul(g, &t1, base, wa, NULL);
            ca_group_mul(g, &t2, target, wb, NULL);
            ca_group_op(g, &t2, &t1, &t2);
            if (!ca_group_equal(g, &lhs, &t2)) bad++;
        }
    }
    printf("%-34s walks=%zu steps=%u dps=%u invariant violations=%d\n", label, nwalks, steps,
           dps_total, bad);
    CHECK_EQ_U64((uint64_t)bad, 0);
    /* Liveness: the kernel must report distinguished points.  An individual
     * launch can legitimately report none in a very small group, where a
     * fruitless cycle may contain no distinguished point at this density and
     * the walk spins until the abandon rule re-seeds it, so this is checked
     * over all launches rather than per launch. */
    CHECK(dps_total > 0);
    free(mult);
    free(state);
    free(aux);
    free(dp);
    free(restart);
}

static void run_solver(const ca_group *g, const ca_elem *gen, ca_gpu_backend be, int reps,
                       int negmap, const char *label)
{
    ca_rng rng;
    ca_rng_seed(&rng, 31);
    double tot = 0;
    for (int k = 0; k < reps; k++) {
        uint64_t xx = ca_rng_below(&rng, g->order);
        ca_elem h;
        fx_instance(g, gen, xx, &h);
        ca_gpu_rho_params p;
        ca_gpu_rho_params_default(&p);
        p.backend = be;
        p.seed = 500 + k;
        p.negation_map = negmap;
        uint64_t got = 0;
        ca_stats st = {0};
        ca_status rc = ca_gpu_rho_solve(g, gen, &h, &p, &got, &st);
        CHECK(rc == CA_OK);
        CHECK_EQ_U64(got, xx);
        tot += (double)st.group_ops;
        if (rc != CA_OK)
            fprintf(stderr, "  %s failed: %s %s\n", label, ca_status_string(rc), ca_last_error());
    }
    printf("%-28s ops/sqrt(n) = %.2f\n", label, tot / reps / sqrt((double)g->order));
}

static void test_launch_dimension_overflow(void)
{
    ca_group g;
    ca_elem gen, target;
    fx_zp_safe(&g, &gen, 2000000579ULL);
    fx_instance(&g, &gen, 7, &target);
    const uint32_t dimensions[][2] = {
        {1u << 25, 128},       /* thread count would truncate to zero */
        {(1u << 25) + 1, 128}, /* thread count would truncate to 128 */
        {1u << 22, 128},       /* thread count fits, walk IDs do not */
        {UINT32_MAX, UINT32_MAX},
    };
    for (size_t i = 0; i < sizeof(dimensions) / sizeof(dimensions[0]); i++) {
        ca_gpu_rho_params p;
        ca_gpu_rho_params_default(&p);
        p.backend = CA_GPU_BACKEND_EMULATE;
        p.blocks = dimensions[i][0];
        p.threads_per_block = dimensions[i][1];
        p.dp_bits = 0;
        p.steps_per_launch = 1;
        p.max_ops = 1;
        uint64_t got = UINT64_MAX;
        ca_status rc = ca_gpu_rho_solve(&g, &gen, &target, &p, &got, NULL);
        CHECK(rc == CA_ERR_INVALID);
        CHECK_EQ_U64(got, UINT64_MAX);
        if (rc != CA_ERR_INVALID) return; /* a broken guard must not attempt larger allocations */
    }
}

int main(void)
{
    test_checkpoint_metadata();
    test_launch_dimension_overflow();
    test_dp_capacity();
    test_device_arith();
    ca_group g;
    ca_elem gen;
    /* walk invariant: curves with and without the negation map, and Z_p^* */
    {
        ca_elem h;
        fx_ec(&g, &gen, 1000000007ULL, 3, 11);
        ca_group_mul(&g, &h, &gen, 987654, NULL);
        test_walk_invariant(&g, &gen, &h, 1, 8, 400, "ec negmap walk invariant");
        test_walk_invariant(&g, &gen, &h, 0, 8, 400, "ec no-neg walk invariant");
        fx_ec(&g, &gen, 100003, 1, 1);
        ca_group_mul(&g, &h, &gen, 777, NULL);
        test_walk_invariant(&g, &gen, &h, 1, 4, 2000, "ec small negmap walk invariant");
        fx_zp_safe(&g, &gen, 2000000579ULL);
        ca_group_mul(&g, &h, &gen, 123456789, NULL);
        test_walk_invariant(&g, &gen, &h, 1, 8, 400, "zp walk invariant");
    }
    fx_zp_safe(&g, &gen, 2000000579ULL);
    run_solver(&g, &gen, CA_GPU_BACKEND_EMULATE, 4, 1, "zp 31-bit emulate");
    fx_ec(&g, &gen, 1000000007ULL, 3, 11);
    run_solver(&g, &gen, CA_GPU_BACKEND_EMULATE, 4, 1, "ec 28-bit emulate negmap");
    run_solver(&g, &gen, CA_GPU_BACKEND_EMULATE, 3, 0, "ec 28-bit emulate no-neg");
    fx_ec(&g, &gen, 100003, 1, 1);
    run_solver(&g, &gen, CA_GPU_BACKEND_EMULATE, 4, 1, "ec 17-bit emulate");
    /* explicit small configuration: 1 block of 4 threads, 2 dp bits */
    {
        ca_gpu_rho_params p;
        ca_gpu_rho_params_default(&p);
        p.backend = CA_GPU_BACKEND_EMULATE;
        p.blocks = 1;
        p.threads_per_block = 4;
        p.dp_bits = 2;
        p.steps_per_launch = 16;
        p.seed = 9;
        fx_zp_safe(&g, &gen, 2000000579ULL);
        ca_elem h;
        fx_instance(&g, &gen, 123456789, &h);
        uint64_t got;
        CHECK(ca_gpu_rho_solve(&g, &gen, &h, &p, &got, NULL) == CA_OK);
        CHECK_EQ_U64(got, 123456789);
        p.max_ops = 1000;
        CHECK(ca_gpu_rho_solve(&g, &gen, &h, &p, &got, NULL) == CA_ERR_LIMIT);
    }
    /* composite order */
    CHECK(ca_group_zp_init(&g, 1000003, 0) == CA_OK);
    const uint64_t w[4] = {2, 0, 0, 0};
    CHECK(ca_group_encode(&g, &gen, w));
    run_solver(&g, &gen, CA_GPU_BACKEND_EMULATE, 3, 1, "zp composite emulate");
    /* An out-of-range dp_bits must be clamped, not shifted by 64 or more
     * (undefined).  Distinguished points then essentially never occur, so the
     * run is bounded by max_ops; the point of the test is that it terminates
     * cleanly, and that UBSan sees no bad shift. */
    {
        fx_zp_safe(&g, &gen, 2000000579ULL);
        ca_elem h;
        fx_instance(&g, &gen, 4242, &h);
        for (int32_t bits = 63; bits <= 200; bits += 37) {
            ca_gpu_rho_params p;
            ca_gpu_rho_params_default(&p);
            p.backend = CA_GPU_BACKEND_EMULATE;
            p.dp_bits = bits;
            p.max_ops = 20000;
            p.seed = 2;
            uint64_t got = 0;
            CHECK(ca_gpu_rho_solve(&g, &gen, &h, &p, &got, NULL) == CA_ERR_LIMIT);
        }
    }

    /* A tiny group is answered on the host, but an explicit CUDA request is
     * still refused when CUDA is unavailable rather than answered quietly. */
    {
        ca_group tiny;
        ca_elem tg, th;
        uint64_t got;
        CHECK(ca_group_zp_init(&tiny, 1019, 509) == CA_OK);
        CHECK(ca_group_find_generator(&tiny, &tg, 1) == CA_OK);
        ca_group_mul(&tiny, &th, &tg, 123, NULL);
        ca_gpu_rho_params p;
        ca_gpu_rho_params_default(&p);
        p.backend = CA_GPU_BACKEND_EMULATE;
        CHECK(ca_gpu_rho_solve(&tiny, &tg, &th, &p, &got, NULL) == CA_OK);
        CHECK_EQ_U64(got, 123);
        p.backend = CA_GPU_BACKEND_CUDA;
        ca_status want =
            (ca_gpu_cuda_compiled() && ca_gpu_device_count() > 0) ? CA_OK : CA_ERR_UNSUPPORTED;
        CHECK(ca_gpu_rho_solve(&tiny, &tg, &th, &p, &got, NULL) == want);
    }

    /* CUDA backend when available */
    printf("cuda compiled: %d, devices: %d\n", ca_gpu_cuda_compiled(), ca_gpu_device_count());
    if (ca_gpu_cuda_compiled() && ca_gpu_device_count() > 0) {
        char name[128];
        if (ca_gpu_device_name(0, name, sizeof(name)) == 0) printf("device 0: %s\n", name);
        fx_zp_safe(&g, &gen, 2000000579ULL);
        run_solver(&g, &gen, CA_GPU_BACKEND_CUDA, 3, 1, "zp 31-bit cuda");
        fx_ec(&g, &gen, 1000000007ULL, 3, 11);
        run_solver(&g, &gen, CA_GPU_BACKEND_CUDA, 3, 1, "ec 28-bit cuda negmap");
    } else {
        ca_gpu_rho_params p;
        ca_gpu_rho_params_default(&p);
        p.backend = CA_GPU_BACKEND_CUDA;
        ca_elem h;
        fx_zp_safe(&g, &gen, 2000000579ULL);
        fx_instance(&g, &gen, 5, &h);
        uint64_t got;
        CHECK(ca_gpu_rho_solve(&g, &gen, &h, &p, &got, NULL) == CA_ERR_UNSUPPORTED);
    }
    TEST_MAIN_END();
}
