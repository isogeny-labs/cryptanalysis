/*
 * ca_grumpy.h - "Two grumpy giants and a baby" (Bernstein-Lange 2012).
 *
 * Interval discrete logarithm x in [lo, hi] with x * base == target.  Three
 * walks are interleaved: a baby walk j*base, a giant walk target + i*m*base
 * and a second giant walk 2*target - i*(m+1)*base.  Every point goes into
 * one hash table; a collision between any two walks reveals x.
 *
 * Measured average cost (see docs/ALGORITHMS.md, exact simulation and the
 * ca_bench tool), with the default step m = 0.7 sqrt(width):
 *   whole group of order n : 1.21 sqrt(n)  (interleaved BSGS: 1.33 sqrt(n))
 *   sub-interval, no wrap  : 1.72 sqrt(width)  (kangaroo: ~2 sqrt(width))
 * Memory is O(sqrt(width)) table entries (24 bytes each).
 */
#ifndef CA_GRUMPY_H
#define CA_GRUMPY_H

#include "ca_group.h"

#ifdef __cplusplus
extern "C" {
#endif

typedef struct ca_grumpy_params {
    uint64_t m;           /* giant step; 0 => round(alpha * sqrt(width)) */
    double alpha;         /* finite step factor used when m == 0; <= 0 => 0.7 */
    uint64_t max_ops;     /* 0 => none */
} ca_grumpy_params;

CA_API void ca_grumpy_params_default(ca_grumpy_params *p);

/* Automatic step selection rejects non-finite alpha and rounded steps >= 2^64.
 * An explicit m bypasses alpha.  A target outside the order-n subgroup
 * returns CA_ERR_NOT_FOUND at once; any other target with no logarithm in
 * [lo, hi] returns CA_ERR_NOT_FOUND after max(m, 2 width / (m + 1)) + 3
 * iterations at most (about 2.9 sqrt(width) with the default m). */
CA_API ca_status ca_grumpy_solve(const ca_group *g, const ca_elem *base, const ca_elem *target,
                                 uint64_t lo, uint64_t hi, const ca_grumpy_params *params,
                                 uint64_t *x, ca_stats *st);

/* Save the three walks and collision table for an exact interval resume.
 * NULL checkpoint_path enables live progress without persistence. */
CA_API ca_status ca_grumpy_solve_checkpointed(
    const ca_group *g, const ca_elem *base, const ca_elem *target,
    uint64_t lo, uint64_t hi, const ca_grumpy_params *params,
    const char *checkpoint_path, uint32_t progress_interval,
    uint32_t checkpoint_interval, int verbose, uint64_t *x, ca_stats *st);

#ifdef __cplusplus
}
#endif
#endif /* CA_GRUMPY_H */
