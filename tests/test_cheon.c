#include "test_fixtures.h"
#include <unistd.h>

static void run_checkpoint(const ca_group *g, const ca_elem *gen)
{
    char path[] = "/tmp/ca-cheon-checkpoint-XXXXXX";
    int fd = mkstemp(path);
    CHECK(fd >= 0);
    CHECK(close(fd) == 0);
    CHECK(unlink(path) == 0);
    ca_elem ga, gad;
    CHECK(ca_cheon_make_instance(g, gen, 4242, 2, &ga, &gad) == CA_OK);
    ca_cheon_params cp;
    ca_cheon_params_default(&cp);
    cp.max_exps = 3;
    uint64_t got = 0;
    ca_stats st = {0};
    CHECK(ca_cheon_solve_checkpointed(g, gen, &ga, &gad, 2, &cp,
                                      path, 1, 1, 0, &got, &st) == CA_ERR_LIMIT);
    CHECK(st.iterations == 3);
    FILE *f = fopen(path, "rb");
    CHECK(f != NULL);
    CHECK(fclose(f) == 0);
    CHECK(ca_cheon_checkpoint_validate(g, gen, &ga, &gad, 2, path) == CA_OK);

    cp.max_exps = 295;
    st = (ca_stats){0};
    CHECK(ca_cheon_solve_checkpointed(g, gen, &ga, &gad, 2, &cp,
                                      path, 1, 1, 0, &got, &st) == CA_ERR_LIMIT);
    CHECK(st.iterations >= 295);
    cp.max_exps = 1000;
    st = (ca_stats){0};
    CHECK(ca_cheon_solve_checkpointed(g, gen, &ga, &gad, 2, &cp,
                                      path, 1, 1, 0, &got, &st) == CA_OK);
    CHECK_EQ_U64(got, 4242);
    CHECK(st.iterations > 3);
    got = 0;
    CHECK(ca_cheon_solve_checkpointed(g, gen, &ga, &gad, 2, &cp,
                                      path, 1, 1, 0, &got, NULL) == CA_OK);
    CHECK_EQ_U64(got, 4242);

    ca_elem other_ga, other_gad;
    CHECK(ca_cheon_make_instance(g, gen, 4243, 2, &other_ga, &other_gad) == CA_OK);
    CHECK(ca_cheon_solve_checkpointed(g, gen, &other_ga, &other_gad, 2, &cp,
                                      path, 1, 1, 0, &got, NULL) == CA_ERR_INVALID);
    CHECK(ca_cheon_checkpoint_validate(g, gen, &other_ga, &other_gad, 2, path) ==
          CA_ERR_INVALID);
    f = fopen(path, "rb+");
    CHECK(f != NULL);
    CHECK(fseek(f, -1, SEEK_END) == 0);
    int byte = fgetc(f);
    CHECK(byte != EOF);
    CHECK(fseek(f, -1, SEEK_END) == 0);
    CHECK(fputc(byte ^ 1, f) != EOF);
    CHECK(fclose(f) == 0);
    CHECK(ca_cheon_solve_checkpointed(g, gen, &ga, &gad, 2, &cp,
                                      path, 1, 1, 0, &got, NULL) == CA_ERR_INVALID);
    CHECK(ca_cheon_checkpoint_validate(g, gen, &ga, &gad, 2, path) == CA_ERR_INVALID);
    CHECK(unlink(path) == 0);
    char progress[sizeof(path) + 20];
    snprintf(progress, sizeof(progress), "%s.progress.json", path);
    CHECK(unlink(progress) == 0);

    /* With d = order - 1, the second orbit is the long phase. */
    uint64_t d2 = g->order - 1;
    CHECK(ca_cheon_make_instance(g, gen, 4242, d2, &ga, &gad) == CA_OK);
    cp.max_exps = 3;
    CHECK(ca_cheon_solve_checkpointed(g, gen, &ga, &gad, d2, &cp,
                                      path, 1, 1, 0, &got, NULL) == CA_ERR_LIMIT);
    f = fopen(progress, "rb");
    CHECK(f != NULL);
    char phase[256] = {0};
    CHECK(fread(phase, 1, sizeof(phase) - 1, f) > 0);
    CHECK(strstr(phase, "second-baby") != NULL);
    CHECK(fclose(f) == 0);
    cp.max_exps = 1000;
    got = 0;
    CHECK(ca_cheon_solve_checkpointed(g, gen, &ga, &gad, d2, &cp,
                                      path, 1, 1, 0, &got, NULL) == CA_OK);
    CHECK_EQ_U64(got, 4242);
    CHECK(unlink(path) == 0);
    CHECK(unlink(progress) == 0);
}

static void run(const ca_group *g, const ca_elem *gen, uint64_t d, int reps)
{
    uint64_t p = g->order;
    ca_rng rng;
    ca_rng_seed(&rng, 13 + d);
    for (int k = 0; k < reps; k++) {
        uint64_t alpha = 1 + ca_rng_below(&rng, p - 1);
        ca_elem ga, gad;
        CHECK(ca_cheon_make_instance(g, gen, alpha, d, &ga, &gad) == CA_OK);
        uint64_t got = 0;
        ca_stats st = {0};
        ca_status rc = ca_cheon_solve(g, gen, &ga, &gad, d, NULL, &got, &st);
        CHECK(rc == CA_OK);
        CHECK_EQ_U64(got, alpha);
        if (k == 0)
            printf("p=%" PRIu64 " d=%" PRIu64 ": %" PRIu64 " exps, %" PRIu64
                   " ops (sqrt p = %.0f)\n",
                   p, d, st.iterations, st.group_ops, sqrt((double)p));
    }
}

static void run_p_plus_1(const ca_group *g, const ca_elem *gen, uint64_t d, const uint64_t *alphas,
                         size_t nalpha)
{
    uint64_t p = g->order;
    size_t count = (size_t)(2 * d + 1);
    ca_elem *powers = calloc(count, sizeof(*powers));
    CHECK(powers != NULL);

    for (size_t i = 0; i < nalpha; i++) {
        uint64_t alpha = alphas[i] % p;
        CHECK(alpha != 0);
        CHECK(ca_cheon_make_instance_p_plus_1(g, gen, alpha, d, powers, count) == CA_OK);

        /* The helper must really produce P_i = [alpha^i]P. */
        ca_elem want;
        uint64_t scalar = 1;
        for (uint64_t j = 0; j <= 2 * d; j++) {
            ca_group_mul(g, &want, gen, scalar, NULL);
            CHECK(ca_group_equal(g, &want, &powers[j]));
            scalar = (uint64_t)(((ca_u128)scalar * alpha) % p);
        }

        uint64_t got = 0;
        ca_stats st = {0};
        ca_status rc = ca_cheon_solve_p_plus_1(g, powers, count, d, NULL, &got, &st);
        CHECK(rc == CA_OK);
        CHECK_EQ_U64(got, alpha);
        printf("p+1: p=%" PRIu64 " d=%" PRIu64 " alpha=%" PRIu64 ": %" PRIu64 " exps, %" PRIu64
               " ops\n",
               p, d, alpha, st.iterations, st.group_ops);
    }

    free(powers);
}

int main(void)
{
    ca_group g;
    ca_elem gen;
    /* Z_q^* subgroup of prime order p where p-1 has a balanced divisor.
     * p = 1000000009 - is it prime? p-1 = 2^3 * 3 * 41666667 */
    uint64_t p = 1000000009ULL;
    CHECK(ca_is_prime(p));
    /* find q = 2*k*p + 1 prime so the order-p subgroup of Z_q^* exists */
    uint64_t q = 0;
    for (uint64_t k = 1; k < 100000; k++) {
        if (ca_is_prime(2 * k * p + 1)) {
            q = 2 * k * p + 1;
            break;
        }
    }
    CHECK(q != 0);
    CHECK(ca_group_zp_init(&g, q, p) == CA_OK);
    CHECK(ca_group_find_generator(&g, &gen, 1) == CA_OK);
    double cost;
    uint64_t best = ca_cheon_best_divisor(p, &cost);
    printf("best d for p=%" PRIu64 " is %" PRIu64 " (%.0f exps)\n", p, best, cost);
    run(&g, &gen, best, 3);
    run(&g, &gen, 24, 2);
    run(&g, &gen, 1, 1);     /* degenerates to a sqrt(p) exponentiation BSGS */
    run(&g, &gen, p - 1, 1); /* other extreme */

    /* A prime p with p-1 = 2 * 3 * 5 * 7 * 11 * 13 * 17 * 19 * 23 * k form to get d ~ sqrt(p) */
    uint64_t base = 2ULL * 3 * 5 * 7 * 11 * 13 * 17 * 19 * 23 * 29;
    uint64_t p2 = 0;
    for (uint64_t k = 1; k < 100000; k++) {
        if (ca_is_prime(base * k + 1)) {
            p2 = base * k + 1;
            break;
        }
    }
    CHECK(p2 != 0);
    uint64_t q2 = 0;
    for (uint64_t k = 1; k < 100000; k++) {
        if (ca_is_prime(2 * k * p2 + 1)) {
            q2 = 2 * k * p2 + 1;
            break;
        }
    }
    CHECK(q2 != 0);
    CHECK(ca_group_zp_init(&g, q2, p2) == CA_OK);
    CHECK(ca_group_find_generator(&g, &gen, 2) == CA_OK);
    best = ca_cheon_best_divisor(p2, &cost);
    printf("best d for p=%" PRIu64 " is %" PRIu64 " (%.0f exps)\n", p2, best, cost);
    run(&g, &gen, best, 3);

    /* Elliptic curve group of prime order */
    fx_ec(&g, &gen, 1000000007ULL, 3, 11);
    if (ca_is_prime(g.order)) {
        best = ca_cheon_best_divisor(g.order, &cost);
        printf("ec: p=%" PRIu64 " best d=%" PRIu64 " (%.0f exps)\n", g.order, best, cost);
        run(&g, &gen, best, 2);
    }
    /* invalid d */
    ca_elem ga, gad;
    uint64_t got;
    ca_group small;
    ca_elem small_gen;
    CHECK(ca_group_zp_init(&small, 1000003, 166667) == CA_OK);
    CHECK(ca_group_find_generator(&small, &small_gen, 1) == CA_OK);
    run_checkpoint(&small, &small_gen);
    ca_group_zp_init(&g, q, p);
    ca_group_find_generator(&g, &gen, 1);
    ca_cheon_make_instance(&g, &gen, 5, 24, &ga, &gad);
    CHECK((p - 1) % 11 != 0);
    CHECK(ca_cheon_solve(&g, &gen, &ga, &gad, 11, NULL, &got, NULL) == CA_ERR_INVALID);

    /* Cheon's p+1 variant: p+1 = 2 * 5 * 17 * 5882353, so d=170
     * keeps the auxiliary sequence small while reducing the torus search
     * to order (p+1)/d = 5882353. */
    {
        const uint64_t pplus_d = 170;
        const uint64_t alphas[] = {2, 42424242, 987654321};
        CHECK((p + 1) % pplus_d == 0);
        run_p_plus_1(&g, &gen, pplus_d, alphas, sizeof(alphas) / sizeof(alphas[0]));

        size_t count = (size_t)(2 * pplus_d + 1);
        ca_elem *powers = calloc(count, sizeof(*powers));
        CHECK(powers != NULL);
        CHECK(ca_cheon_make_instance_p_plus_1(&g, &gen, 42424242, pplus_d, powers, count) == CA_OK);
        CHECK(ca_cheon_solve_p_plus_1(&g, powers, count - 1, pplus_d, NULL, &got, NULL) ==
              CA_ERR_INVALID);
        CHECK((p + 1) % 11 != 0);
        CHECK(ca_cheon_solve_p_plus_1(&g, powers, count, 11, NULL, &got, NULL) == CA_ERR_INVALID);
        free(powers);
    }
    TEST_MAIN_END();
}
