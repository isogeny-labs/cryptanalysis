#include "cryptanalysis/cryptanalysis.h"
#include "ca_internal.h"
#include <stdio.h>
int main(void)
{
    uint64_t tp[] = {7,  11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47,
                     53, 59, 61, 67, 71, 73, 79, 83, 89, 97, 101};
    for (size_t i = 0; i < sizeof tp / 8; i++) {
        uint64_t p = tp[i];
        for (int m = 0; m < 2; m++) {
            ca_ic_params ip;
            ca_ic_params_default(&ip);
            ip.seed = 5 + i;
            ip.method = m ? CA_IC_RANDOM_EXPONENT : CA_IC_LINEAR_SIEVE;
            ip.factor_base_bound = p - 1 < 5 ? 5 : (uint32_t)(p - 1);
            uint64_t g = ca_primitive_root(p), h = 2, x;
            ca_ic_stats st;
            ca_status rc = ca_ic_solve(p, g, h, &ip, &x, &st);
            printf("p=%llu m=%d B=%u rc=%s %s\n", (unsigned long long)p, m, ip.factor_base_bound,
                   ca_status_string(rc), rc ? ca_last_error() : "");
        }
    }
    return 0;
}
