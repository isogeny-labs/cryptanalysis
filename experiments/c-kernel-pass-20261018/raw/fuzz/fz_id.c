#include "cryptanalysis/cryptanalysis.h"
#include "ca_internal.h"
#include <stdio.h>
int main(void)
{
    setvbuf(stdout, NULL, _IONBF, 0);
    ca_group g;
    ca_group_zp_init(&g, 1000003, 0); /* order 1000002 */
    ca_elem id, t;
    ca_group_identity(&g, &id);
    uint64_t w[4] = {5, 0, 0, 0};
    ca_group_encode(&g, &t, w);
    uint64_t x = 0;
    ca_stats st = {0};
    ca_rho_params rp;
    ca_rho_params_default(&rp);
    rp.max_ops = 3000000;
    rp.seed = 3;
    ca_status rc = ca_rho_solve(&g, &id, &t, &rp, &x, &st);
    printf("rho id base: rc=%s ops=%llu\n", ca_status_string(rc), (unsigned long long)st.group_ops);
    memset(&st, 0, sizeof st);
    rc = ca_bsgs_solve(&g, &id, &t, 0, 0, NULL, &x, &st);
    printf("bsgs id base: rc=%s\n", ca_status_string(rc));
    {
        ca_kangaroo_params kp;
        ca_kangaroo_params_default(&kp);
        kp.max_ops = 2000000;
        rc = ca_kangaroo_solve(&g, &id, &t, 0, 5000, &kp, &x, &st);
    }
    printf("kang id base: rc=%s\n", ca_status_string(rc));
    rc = ca_grumpy_solve(&g, &id, &t, 0, 0, NULL, &x, &st);
    printf("grumpy id base: rc=%s\n", ca_status_string(rc));
    rc = ca_pohlig_hellman(&g, &id, &t, NULL, &x, &st);
    printf("PH id base: rc=%s\n", ca_status_string(rc));
    ca_precomp_params pp;
    ca_precomp_params_default(&pp);
    rc = ca_precomp_solve(&g, &id, &t, &pp, &x, &st);
    printf("precomp id base: rc=%s\n", ca_status_string(rc));
    return 0;
}
