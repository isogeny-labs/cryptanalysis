#include "test_fixtures.h"
#include "cryptanalysis/ca_curve.h"
#include "cryptanalysis/ca_sixclass.h"

int main(void)
{
    uint64_t p, a, b, n;
    CHECK(ca_curve_by_name("glv-j0-26", &p, &a, &b, &n) == CA_OK);
    ca_group g;
    CHECK(ca_curve_group(&g, p, a, b, n, NULL) == CA_OK);
    ca_elem base, target;
    CHECK(ca_group_find_generator(&g, &base, 17) == CA_OK);
    ca_group_mul(&g, &target, &base, 12345, NULL);
    uint64_t answer = 0;
    ca_sixclass_stats stats;
    CHECK(ca_sixclass_solve(&g, &base, &target, 19, 32, 4,
                            10000, &answer, &stats) == CA_OK);
    CHECK_EQ_U64(answer, 12345);
    CHECK(stats.class_visits > 0 && stats.distinguished > 0);
    uint64_t accounted = 0;
    for (unsigned t = 0; t < 6; t++) {
        CHECK_EQ_U64(stats.twist_visits[t],
                     stats.route_parity_by_twist[t][0] +
                     stats.route_parity_by_twist[t][1]);
        accounted += stats.twist_visits[t];
    }
    CHECK_EQ_U64(accounted, stats.class_visits);
    CHECK(ca_sixclass_solve(&g, &base, &target, 19, 3, 4,
                            100, &answer, NULL) == CA_ERR_INVALID);
    ca_elem identity;
    ca_group_identity(&g, &identity);
    CHECK(ca_sixclass_solve(&g, &identity, &identity, 19, 32, 4, 1, &answer, NULL) ==
          CA_ERR_INVALID);
    return 0;
}
