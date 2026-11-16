/* Same-public-point prime-power rho and reusable-precomputation controls. */
#include "cryptanalysis/cryptanalysis.h"
#include "ca_internal.h"
#include <inttypes.h>
#include <stdio.h>

typedef struct subgroup {
    ca_group group;
    ca_elem base;
    uint64_t q, qe;
    unsigned exponent;
    ca_bsgs_table *small;
    ca_precomp_table *precomp;
} subgroup;

static ca_status solve(subgroup *groups, unsigned count, uint64_t p, uint64_t generator,
                       uint64_t inverse, uint64_t target, int precomputed, uint64_t *answer,
                       ca_stats *stats)
{
    uint64_t n = p - 1, result = 0, modulus = 1;
    for (unsigned i = 0; i < count; ++i) {
        subgroup *s = &groups[i];
        uint64_t x = 0, qk = 1;
        for (unsigned k = 0; k < s->exponent; ++k) {
            uint64_t residual = ca_mulmod(target, ca_powmod(inverse, x, p), p);
            uint64_t words[4] = {ca_powmod(residual, n / (qk * s->q), p), 0, 0, 0};
            ca_elem digit_target;
            if (!ca_group_encode(&s->group, &digit_target, words)) return CA_ERR_INVALID;
            uint64_t digit;
            ca_status rc;
            if (s->small)
                rc = ca_bsgs_table_solve(s->small, &digit_target, 0, s->q - 1, &digit, stats);
            else if (precomputed) {
                if (!s->precomp) return CA_ERR_LIMIT;
                rc = ca_precomp_table_solve(s->precomp, &digit_target, &digit, stats);
            } else {
                ca_rho_params params;
                ca_rho_params_default(&params);
                params.threads = 1;
                params.seed = 12345 + i * 64 + k;
                params.max_ops = 50000000;
                params.max_table_entries = 1000000;
                rc = ca_rho_solve(&s->group, &s->base, &digit_target, &params, &digit, stats);
            }
            if (rc != CA_OK) return rc;
            x += qk * digit;
            qk *= s->q;
        }
        result = ca_crt2(result, modulus, x, s->qe);
        modulus *= s->qe;
    }
    *answer = result;
    return ca_powmod(generator, result, p) == target ? CA_OK : CA_ERR_INTERNAL;
}

int main(int argc, char **argv)
{
    if (argc != 3) return 2;
    uint64_t p = strtoull(argv[1], NULL, 10), fixture = strtoull(argv[2], NULL, 10);
    uint64_t generator = ca_primitive_root(p), n = p - 1;
    uint64_t expected = (UINT64_C(0x23456789abcd) + fixture * UINT64_C(0x9e3779b97f4a7c15)) % n;
    uint64_t target = ca_powmod(generator, expected, p);
    uint64_t inverse = ca_invmod(generator, p);
    ca_factorization factors;
    ca_factorize(n, &factors);
    subgroup groups[64] = {0};
    double setup = ca_now();
    for (unsigned i = 0; i < factors.count; ++i) {
        subgroup *s = &groups[i];
        s->q = factors.f[i].p;
        s->qe = 1;
        s->exponent = factors.f[i].e;
        for (unsigned k = 0; k < s->exponent; ++k) s->qe *= s->q;
        if (ca_group_zp_init(&s->group, p, s->q) != CA_OK) return 3;
        uint64_t words[4] = {ca_powmod(generator, n / s->q, p), 0, 0, 0};
        if (!ca_group_encode(&s->group, &s->base, words)) return 3;
        if (s->q <= 4096 &&
            ca_bsgs_table_new(&s->group, &s->base, ca_isqrt(s->q) + 1, &s->small) != CA_OK)
            return 3;
    }
    setup = ca_now() - setup;
    uint64_t answer = 0;
    ca_stats stats = {0};
    double start = ca_now();
    ca_status rc = solve(groups, factors.count, p, generator, inverse, target, 0, &answer, &stats);
    double rho = ca_now() - start;
    printf("{\"p\":%" PRIu64 ",\"h\":%" PRIu64 ",\"expected\":%" PRIu64 ",\"rho_x\":%" PRIu64
           ",\"rho_status\":%d,\"rho_wall\":%.9g,\"rho_setup_wall\":%.9g,\"rho_solver_group_ops\":"
           "%" PRIu64,
           p, target, expected, answer, rc, rho, setup, stats.group_ops);
    start = ca_now();
    int precomp_status = CA_OK;
    for (unsigned i = 0; i < factors.count; ++i) {
        subgroup *s = &groups[i];
        if (s->small) continue;
        ca_precomp_params params;
        ca_precomp_params_default(&params);
        params.threads = 1;
        params.seed = 12345;
        params.max_precomp_ops = 5000000;
        params.max_online_ops = 5000000;
        ca_status prc = ca_precomp_table_new(&s->group, &s->base, &params, &s->precomp, NULL);
        if (prc != CA_OK) precomp_status = prc;
    }
    double precomp_setup = ca_now() - start;
    start = ca_now();
    answer = 0;
    memset(&stats, 0, sizeof(stats));
    ca_status prc = precomp_status == CA_OK ? solve(groups, factors.count, p, generator, inverse,
                                                    target, 1, &answer, &stats)
                                            : precomp_status;
    double precomp_online = ca_now() - start;
    printf(",\"precomp_status\":%d,\"precomp_x\":%" PRIu64
           ",\"precomp_setup_wall\":%.9g,\"precomp_online_wall\":%.9g}\n",
           prc, answer, precomp_setup, precomp_online);
    for (unsigned i = 0; i < factors.count; ++i) {
        ca_bsgs_table_free(groups[i].small);
        ca_precomp_table_free(groups[i].precomp);
    }
    return rc == CA_OK ? 0 : 4;
}
