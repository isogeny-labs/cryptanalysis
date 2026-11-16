# Opt-in bounded-word arithmetic experiment

This is a separate, unmeasured arithmetic candidate. It does not modify the
frozen run-002 panel or promote any rejected timing pair.

Rational reconstruction bounds numerator and denominator by UINT32_MAX for
64-bit prime moduli. CA_IC_TRIAL32=portable selects four-way fixed-divisor
scans; CA_IC_TRIAL32=auto selects eight-lane AVX2 on supported x86-64 CPUs,
four-lane NEON on AArch64, or the portable implementation. Unset or 0 retains
the existing 64-bit path. Configuration is read at context construction.
Buffers are immutable for the lifetime of a context and freed with it.

Correctness requires matching status, output count, every column/exponent and
capacity failure against the existing factorizer. The native test exercises
144,000 comparisons across both selectors, including values 0..4095,
UINT32_MAX, 2^31, random words and empty/almost-full/full output buffers.
Existing reconstruction and projected-solution tests remain required.
AddressSanitizer and UndefinedBehaviorSanitizer must pass both modes.
These are producer tests; Linux AVX2 execution remains pending. [pcc:unverified]

Before timing, publish the exact candidate revision, complete the placement
and cgroup preflight, and allocate a fresh benchmark record. Compare 0,
portable and auto on identical inputs and compiler settings. Use fresh
fixture indices 15..19 and the five cases in PROTOCOL.md, alternating all
backend orders. Preserve setup separately, first-call primary timing and
99 repeated calls as secondary only. Keep the same scalar replay, same-point
rho/precomputation controls, A/A threshold and placement/noise gates. Keep
all failed pairs and null qualified fields. The candidate stays opt-in until
a controlled experiment justifies changing the default.
