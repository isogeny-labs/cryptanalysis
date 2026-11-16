#include "test_fixtures.h"
#include "grumpy_checkpoint_internal.h"
#include <unistd.h>
#include <float.h>

static void run(const ca_group *g, const ca_elem *gen, uint64_t width, int reps, double alpha,
                double *ratio)
{
    uint64_t n = g->order;
    ca_rng rng;
    ca_rng_seed(&rng, 11);
    double tot = 0;
    for (int k = 0; k < reps; k++) {
        uint64_t lo = ca_rng_below(&rng, n - width);
        uint64_t x = lo + ca_rng_below(&rng, width);
        ca_elem h;
        fx_instance(g, gen, x, &h);
        ca_grumpy_params p;
        ca_grumpy_params_default(&p);
        p.alpha = alpha;
        uint64_t got = 0;
        ca_stats st = {0};
        ca_status rc = ca_grumpy_solve(g, gen, &h, lo, lo + width - 1, &p, &got, &st);
        CHECK(rc == CA_OK);
        CHECK_EQ_U64(got, x);
        tot += (double)st.group_ops;
    }
    if (ratio) *ratio = tot / reps / sqrt((double)width);
}

static int write_checkpoint_case(const char *path, const unsigned char *original, size_t n,
                                 grumpy_checkpoint_header h, unsigned char *expected)
{
    memcpy(expected, original, n);
    h.checksum = 0;
    memcpy(expected, &h, sizeof(h));
    uint64_t hash = UINT64_C(14695981039346656037);
    for (size_t i = 0; i < n; i++) {
        hash ^= expected[i];
        hash *= UINT64_C(1099511628211);
    }
    h.checksum = hash;
    memcpy(expected, &h, sizeof(h));
    FILE *f = fopen(path, "wb");
    if (!f) return 0;
    int ok = fwrite(expected, 1, n, f) == n;
    if (fclose(f) != 0) ok = 0;
    return ok;
}

static int checkpoint_file_matches(const char *path, const unsigned char *expected, size_t n)
{
    FILE *f = fopen(path, "rb");
    if (!f) return 0;
    int ok = 1;
    for (size_t i = 0; ok && i < n; i++) ok = fgetc(f) == expected[i];
    if (ok && (fgetc(f) != EOF || ferror(f))) ok = 0;
    if (fclose(f) != 0) ok = 0;
    return ok;
}

static void test_checkpoint_counter_bounds(const char *original_path, const char *dir,
                                           const ca_group *g, const ca_elem *gen,
                                           const ca_elem *target, ca_grumpy_params p)
{
    FILE *f = fopen(original_path, "rb");
    CHECK(f != NULL);
    if (!f) return;
    CHECK(fseek(f, 0, SEEK_END) == 0);
    long size = ftell(f);
    CHECK(size >= (long)sizeof(grumpy_checkpoint_header));
    if (size < (long)sizeof(grumpy_checkpoint_header)) {
        fclose(f);
        return;
    }
    rewind(f);
    size_t n = (size_t)size;
    unsigned char *original = malloc(n), *expected = malloc(n);
    CHECK(original != NULL && expected != NULL);
    if (!original || !expected) {
        free(original);
        free(expected);
        fclose(f);
        return;
    }
    CHECK(fread(original, 1, n, f) == n);
    CHECK(fclose(f) == 0);
    grumpy_checkpoint_header saved;
    memcpy(&saved, original, sizeof(saved));
    char path[160], progress[192];
    snprintf(path, sizeof(path), "%s/counter.ckpt", dir);
    snprintf(progress, sizeof(progress), "%s.progress.json", path);
    p.max_ops = 100000;
    /* A cached solution with a fresh checksum proves that these fixtures reach semantic checks. */
    grumpy_checkpoint_header h = saved;
    h.solved = 1;
    h.result = 424242;
    CHECK(write_checkpoint_case(path, original, n, h, expected));
    uint64_t answer = 99;
    ca_stats stats = {0};
    CHECK(ca_grumpy_solve_checkpointed(g, gen, target, saved.lo, saved.hi, &p, path, 1, 1, 0,
                                       &answer, &stats) == CA_OK);
    CHECK_EQ_U64(answer, 424242);
    CHECK(stats.group_ops >= saved.ops);
    uint64_t setup_ops = stats.group_ops - saved.ops;
    CHECK(setup_ops > 0 && setup_ops < UINT64_MAX - 2);
    for (int which = 0; which < 3; which++) {
        h = saved;
        if (which == 0) h.ops = UINT64_MAX;
        if (which == 1) {
            h.solved = 2;
            h.result = 424242;
        }
        if (which == 2) {
            h.next_i = saved.hi - saved.lo + 3;
            h.ops = h.next_i + 10;
        }
        CHECK(write_checkpoint_case(path, original, n, h, expected));
        answer = 99;
        memset(&stats, 0, sizeof(stats));
        CHECK(ca_grumpy_solve_checkpointed(g, gen, target, saved.lo, saved.hi, &p, path, 1, 1, 0,
                                           &answer, &stats) == CA_ERR_INVALID);
        CHECK_EQ_U64(answer, 99);
        CHECK(checkpoint_file_matches(path, expected, n));
    }
    h = saved;
    h.ops = UINT64_MAX - setup_ops - 2;
    CHECK(write_checkpoint_case(path, original, n, h, expected));
    answer = 99;
    memset(&stats, 0, sizeof(stats));
    CHECK(ca_grumpy_solve_checkpointed(g, gen, target, saved.lo, saved.hi, &p, path, 1, 1, 0,
                                       &answer, &stats) == CA_ERR_LIMIT);
    CHECK_EQ_U64(answer, 99);
    CHECK_EQ_U64(stats.group_ops, UINT64_MAX - 2);
    f = fopen(path, "rb");
    CHECK(f != NULL);
    if (f) {
        CHECK(fread(&h, 1, sizeof(h), f) == sizeof(h));
        CHECK(fclose(f) == 0);
        CHECK_EQ_U64(h.next_i, saved.next_i);
        CHECK_EQ_U64(h.ops, UINT64_MAX - 2);
    }
    unlink(path);
    unlink(progress);
    free(original);
    free(expected);
}

static void test_step_factor_bounds(void)
{
    ca_group g;
    ca_elem gen, target;
    fx_zp_safe(&g, &gen, 1019);
    fx_instance(&g, &gen, 5, &target);
    const double invalid[] = {INFINITY, -INFINITY, NAN, DBL_MAX, 0x1p64};
    for (size_t i = 0; i < sizeof(invalid) / sizeof(invalid[0]); i++) {
        ca_grumpy_params p;
        ca_grumpy_params_default(&p);
        p.alpha = invalid[i];
        p.max_ops = 1000;
        uint64_t answer = 99;
        ca_stats stats = {0};
        CHECK(ca_grumpy_solve(&g, &gen, &target, 0, 31, &p, &answer, &stats) == CA_ERR_INVALID);
        CHECK_EQ_U64(answer, 99);
        CHECK_EQ_U64(stats.group_ops, 0);
        CHECK(ca_grumpy_solve_checkpointed(&g, &gen, &target, 0, 31, &p, NULL, 0, 0, 0, &answer,
                                           &stats) == CA_ERR_INVALID);
        CHECK_EQ_U64(answer, 99);
        CHECK_EQ_U64(stats.group_ops, 0);
    }
    const double valid[] = {0, -1, 0.7, DBL_MIN};
    for (size_t i = 0; i < sizeof(valid) / sizeof(valid[0]); i++) {
        ca_grumpy_params p;
        ca_grumpy_params_default(&p);
        p.alpha = valid[i];
        p.max_ops = 1000;
        uint64_t answer = 99;
        CHECK(ca_grumpy_solve(&g, &gen, &target, 0, 31, &p, &answer, NULL) == CA_OK);
        CHECK_EQ_U64(answer, 5);
    }
    ca_grumpy_params p;
    ca_grumpy_params_default(&p);
    p.m = 17;
    p.alpha = INFINITY; /* unused when an explicit step is supplied */
    p.max_ops = 1000;
    uint64_t answer = 99;
    CHECK(ca_grumpy_solve(&g, &gen, &target, 0, 31, &p, &answer, NULL) == CA_OK);
    CHECK_EQ_U64(answer, 5);
}

int main(void)
{
    test_step_factor_bounds();
    ca_group g;
    ca_elem gen;
    double ratio;
    fx_zp_safe(&g, &gen, 2000000579ULL);
    {
        char dir[] = "/tmp/ca-grumpy-resume-XXXXXX";
        CHECK(mkdtemp(dir) != NULL);
        char path[128], progress[160];
        snprintf(path, sizeof(path), "%s/walk.ckpt", dir);
        snprintf(progress, sizeof(progress), "%s.progress.json", path);
        ca_elem target;
        fx_instance(&g, &gen, 424242, &target);
        ca_grumpy_params cp;
        ca_grumpy_params_default(&cp);
        cp.max_ops = 100;
        uint64_t answer = 0;
        ca_stats first = {0}, second = {0};
        CHECK(ca_grumpy_solve_checkpointed(&g, &gen, &target, 0, 1u << 20,
            &cp, path, 1, 1, 0, &answer, &first) == CA_ERR_LIMIT);
        CHECK(first.table_entries > 0);
        CHECK(access(path, F_OK) == 0 && access(progress, F_OK) == 0);
        test_checkpoint_counter_bounds(path, dir, &g, &gen, &target, cp);
        cp.m = 17;
        CHECK(ca_grumpy_solve_checkpointed(&g, &gen, &target, 0, 1u << 20,
            &cp, path, 1, 1, 0, &answer, NULL) == CA_ERR_INVALID);
        cp.m = 0;
        cp.max_ops = 100000;
        CHECK(ca_grumpy_solve_checkpointed(&g, &gen, &target, 0, 1u << 20,
            &cp, path, 1, 1, 0, &answer, &second) == CA_OK);
        CHECK_EQ_U64(answer, 424242);
        CHECK(second.group_ops > first.group_ops);
        FILE *f = fopen(path, "rb+");
        CHECK(f != NULL);
        if (f) {
            CHECK(fseek(f, -1, SEEK_END) == 0);
            int last = fgetc(f);
            CHECK(last != EOF);
            CHECK(fseek(f, -1, SEEK_END) == 0);
            CHECK(fputc(last ^ 1, f) != EOF);
            CHECK(fclose(f) == 0);
        }
        CHECK(ca_grumpy_solve_checkpointed(&g, &gen, &target, 0, 1u << 20,
            &cp, path, 1, 1, 0, &answer, NULL) == CA_ERR_INVALID);
        unlink(progress); unlink(path); rmdir(dir);
    }
    run(&g, &gen, 1ULL << 24, 40, 0.5, &ratio);
    printf("zp  width 2^24 ops/sqrt(w) = %.3f\n", ratio);
    CHECK(ratio < 2.5);
    fx_ec(&g, &gen, 1000000007ULL, 3, 11);
    {
        char dir[] = "/tmp/ca-grumpy-ec-resume-XXXXXX";
        CHECK(mkdtemp(dir) != NULL);
        char path[128], progress[160];
        snprintf(path, sizeof(path), "%s/walk.ckpt", dir);
        snprintf(progress, sizeof(progress), "%s.progress.json", path);
        ca_elem target;
        fx_instance(&g, &gen, 424242, &target);
        ca_grumpy_params cp;
        ca_grumpy_params_default(&cp);
        cp.max_ops = 100;
        uint64_t answer = 0;
        CHECK(ca_grumpy_solve_checkpointed(&g, &gen, &target, 0, 1u << 20,
            &cp, path, 1, 1, 0, &answer, NULL) == CA_ERR_LIMIT);
        cp.max_ops = 100000;
        CHECK(ca_grumpy_solve_checkpointed(&g, &gen, &target, 0, 1u << 20,
            &cp, path, 1, 1, 0, &answer, NULL) == CA_OK);
        CHECK_EQ_U64(answer, 424242);
        unlink(progress); unlink(path); rmdir(dir);
    }
    run(&g, &gen, 1ULL << 22, 40, 0.5, &ratio);
    printf("ec  width 2^22 ops/sqrt(w) = %.3f\n", ratio);
    CHECK(ratio < 2.5);
    run(&g, &gen, 10, 10, 0.5, NULL);
    run(&g, &gen, 1000, 10, 0.5, NULL);
    /* whole group and edge cases */
    uint64_t n = g.order;
    ca_elem h;
    uint64_t got;
    fx_instance(&g, &gen, n - 1, &h);
    CHECK(ca_grumpy_solve(&g, &gen, &h, 0, 0, NULL, &got, NULL) == CA_OK);
    CHECK_EQ_U64(got, n - 1);
    fx_instance(&g, &gen, 0, &h);
    CHECK(ca_grumpy_solve(&g, &gen, &h, 0, 0, NULL, &got, NULL) == CA_OK);
    CHECK_EQ_U64(got, 0);
    /* even group order (full Z_p^*) exercises the 2x' = v branch */
    CHECK(ca_group_zp_init(&g, 1000003, 0) == CA_OK);
    const uint64_t w[4] = {2, 0, 0, 0};
    CHECK(ca_group_encode(&g, &gen, w));
    run(&g, &gen, 1ULL << 18, 20, 0.5, NULL);
    /* unknown group order: interval-only mode */
    g.order = 0;
    run(&g, &gen, 1ULL << 16, 5, 0.5, NULL);

    /* Regression, fuzz/crashes/grumpy_kangaroo_out_of_interval: a base that
     * generates a proper subgroup.  The solutions are a class modulo
     * ord(base), not modulo the group order, so shifting the found value by
     * multiples of the group order is not enough to land it in [lo, hi].
     * The answer 2 is in [0, 2]; the solver used to return 5. */
    CHECK(ca_group_zp_init(&g, 7, 0) == CA_OK); /* Z_7^*, order 6 */
    const uint64_t w2[4] = {2, 0, 0, 0};        /* 2 has order 3 */
    CHECK(ca_group_encode(&g, &gen, w2));
    ca_elem h2;
    ca_group_mul(&g, &h2, &gen, 2, NULL);
    ca_grumpy_params gp;
    ca_grumpy_params_default(&gp);
    gp.max_ops = 100000;
    uint64_t sub;
    CHECK(ca_grumpy_solve(&g, &gen, &h2, 0, 2, &gp, &sub, NULL) == CA_OK);
    CHECK_EQ_U64(sub, 2);
    /* and the contract itself: whatever comes back is inside the interval */
    CHECK(sub <= 2);
    TEST_MAIN_END();
}
