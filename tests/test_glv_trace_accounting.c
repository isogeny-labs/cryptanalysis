#include "glv_trace_accounting.h"
#include "test_util.h"

int main(void)
{
    /* A four-step cycle is detected after a DP, but two of its steps were
     * before that DP. Then three non-cycle steps accrue before abandonment. */
    const uint64_t cycle_len = 4;
    const uint64_t steps_before_dp = 2;
    const uint64_t steps_after_dp_in_cycle = 2;
    const uint64_t steps_after_escape = 3;
    uint64_t since_dp = steps_after_dp_in_cycle;
    uint64_t trace_wasted = 0;
    uint64_t trace_wasted_since_dp = 0;
    uint64_t committed_steps = steps_before_dp + steps_after_dp_in_cycle;

    trace_wasted += cycle_len;
    trace_wasted_since_dp += ca_glv_trace_cycle_steps_since_dp(cycle_len, since_dp);
    CHECK_EQ_U64(trace_wasted_since_dp, steps_after_dp_in_cycle);

    /* Three further steps accrue before abandonment without another DP.
     * The later two cycle steps overlap since_dp; the two from before the DP
     * remain in aggregate waste but outside the abandonment timer. */
    since_dp += steps_after_escape;
    committed_steps += steps_after_escape;
    trace_wasted += ca_glv_trace_unaccounted_abandon_steps(since_dp, trace_wasted_since_dp);

    CHECK(trace_wasted <= committed_steps);
    CHECK_EQ_U64(trace_wasted, cycle_len + steps_after_escape);

    /* A later DP starts a new timer interval: old cycle waste stays in the
     * aggregate but cannot reduce a subsequent abandoned segment. */
    uint64_t after_dp_since = 0;
    uint64_t after_dp_charged = 2;
    uint64_t after_dp_wasted = 2;
    ca_glv_trace_reset_since_dp(&after_dp_charged);
    const uint64_t after_dp_steps = 4;
    after_dp_since += after_dp_steps;
    after_dp_wasted += ca_glv_trace_unaccounted_abandon_steps(after_dp_since, after_dp_charged);
    CHECK_EQ_U64(after_dp_wasted, 6);
    CHECK(after_dp_wasted <= 2 + after_dp_steps);

    /* The escape doubling is booked with restart work; diagnostic waste does
     * not alter the solver's operation total. */
    const uint64_t table_ops = 5;
    const uint64_t start_ops = 3;
    const uint64_t restart_ops = 1;
    const uint64_t step_ops = committed_steps;
    const uint64_t total_ops = 16;
    CHECK_EQ_U64(ca_glv_trace_ops_total(table_ops, start_ops, restart_ops, step_ops), total_ops);

    TEST_MAIN_END();
}
