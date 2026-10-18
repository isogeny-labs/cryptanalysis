#include "cryptanalysis/cryptanalysis.h"
#include "ca_internal.h"
#include <stdio.h>
#include <math.h>
int main(int argc, char **argv)
{
    setvbuf(stdout, NULL, _IONBF, 0);
    uint64_t p = 65537, a, b, N;
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
    for (int neg = 0; neg < 2; neg++)
        for (unsigned r = 4; r <= 6; r++) {
            int fail = 0, tot = 30;
            double ops = 0, dps = 0, rest = 0, tab = 0;
            for (int s = 0; s < tot; s++) {
                uint64_t k = (s * 7919 + 13) % N;
                ca_elem t;
                ca_group_mul(&g, &t, &base, k, NULL);
                ca_rho_params rp;
                ca_rho_params_default(&rp);
                rp.seed = 100 + s;
                rp.r = r;
                rp.dp_bits = 0;
                rp.negation_map = neg;
                rp.max_ops = 1000000;
                uint64_t x;
                ca_stats st = {0};
                ca_status rc = ca_rho_solve(&g, &base, &t, &rp, &x, &st);
                ops += st.group_ops;
                dps += st.iterations;
                rest += st.collisions;
                tab += st.table_entries;
                if (rc != CA_OK) fail++;
            }
            printf("neg=%d r=%u fails %d/%d ops %.0f dps %.0f restarts %.0f table %.0f\n", neg, r,
                   fail, tot, ops / tot, dps / tot, rest / tot, tab / tot);
        }
    return 0;
}
