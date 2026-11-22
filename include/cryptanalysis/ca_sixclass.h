/* Experimental Curve Smash six-class GLV distinguished-point walk.
 * This 64-bit implementation is for paired toy-curve research. It is
 * deliberately separate from the default ca_curve_solve walk. */
#ifndef CA_SIXCLASS_H
#define CA_SIXCLASS_H
#include "ca_group.h"
#ifdef __cplusplus
extern "C" {
#endif

typedef struct ca_sixclass_stats {
    uint64_t class_visits, distinguished, short_cycle_escapes;
    uint64_t walkers, exceptional, collisions;
    /* Every class visit, including a DP, contributes to these H1 counts. */
    uint64_t twist_visits[6], route_parity_by_twist[6][2];
} ca_sixclass_stats;

/* r must be a power of two, dp_bits <= 24. Returns CA_OK only after
 * independently verifying x*base == target. CA_ERR_LIMIT means the bounded
 * experiment ended without a solving collision. */
CA_API ca_status ca_sixclass_solve(const ca_group *g, const ca_elem *base,
                                   const ca_elem *target, uint64_t seed,
                                   uint32_t r, uint32_t dp_bits,
                                   uint64_t max_walkers, uint64_t *x,
                                   ca_sixclass_stats *stats);
#ifdef __cplusplus
}
#endif
#endif
