#ifndef CA_GLV_TRACE_ACCOUNTING_H
#define CA_GLV_TRACE_ACCOUNTING_H

#include <stdint.h>

/* Number of the last cycle_steps committed walk steps that are still within
 * the current since-DP interval. A detected cycle can straddle a DP, while
 * since_dp remains the solver's abandonment timer. */
static inline uint64_t ca_glv_trace_cycle_steps_since_dp(uint64_t cycle_steps,
                                                         uint64_t since_dp)
{
    return cycle_steps < since_dp ? cycle_steps : since_dp;
}

/* Escape accounting has already charged these steps. Count only the rest of
 * the abandoned segment so the trace does not charge a cycle step twice. */
static inline uint64_t ca_glv_trace_unaccounted_abandon_steps(uint64_t since_dp,
                                                              uint64_t charged_since_dp)
{
    return since_dp - charged_since_dp;
}

static inline void ca_glv_trace_reset_since_dp(uint64_t *charged_since_dp)
{
    *charged_since_dp = 0;
}

static inline uint64_t ca_glv_trace_ops_total(uint64_t table_ops, uint64_t start_ops,
                                              uint64_t restart_ops, uint64_t step_ops)
{
    return table_ops + start_ops + restart_ops + step_ops;
}

#endif
