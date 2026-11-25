#include "cryptanalysis/cryptanalysis.h"
#include "ca_internal.h"
#include <stdio.h>
#include <math.h>
int main(int argc, char **argv)
{
    setvbuf(stdout, NULL, _IONBF, 0);
    uint64_t p = 65537, a = 3, b = 7, N;
    /* find a curve with prime-ish order */
    ca_rng R;
    ca_rng_seed(&R, 1);
    for (;;) {
        a = ca_rng_next(&R) % p;
        b = 1 + ca_rng_next(&R) % (p - 1);
        if (ca_ec_count_points(p, a, b, &N, NULL) == CA_OK && ca_is_prime(N)) break;
    }
    ca_group g;
    ca_group_ec_init(&g, p, a, b, N);
    ca_elem base;
    ca_ec_random_point(&g, &base, 3);
    printf("N=%llu\n", (unsigned long long)N);
    int dps[] = {-1, 0, 1, 3};
    unsigned rs[] = {0, 4, 5, 6, 8, 9};
    for (int di = 0; di < 4; di++)
        for (int ri = 0; ri < 6; ri++) {
            int fail = 0, tot = 60;
            uint64_t ops = 0;
            for (int s = 0; s < tot; s++) {
                uint64_t k = (s * 7919 + 13) % N;
                ca_elem t;
                ca_group_mul(&g, &t, &base, k, NULL);
                ca_rho_params rp;
                ca_rho_params_default(&rp);
                rp.seed = 100 + s;
                rp.r = rs[ri];
                rp.dp_bits = dps[di];
                rp.max_ops = 3000000;
                uint64_t x;
                ca_stats st = {0};
                ca_status rc = ca_rho_solve(&g, &base, &t, &rp, &x, &st);
                ops += st.group_ops;
                if (rc != CA_OK) fail++;
            }
            printf("dp=%d r=%u: fails %d/%d mean ops %.0f (sqrtN=%.0f)\n", dps[di], rs[ri], fail,
                   tot, (double)ops / tot, sqrt((double)N));
        }
    return 0;
}
