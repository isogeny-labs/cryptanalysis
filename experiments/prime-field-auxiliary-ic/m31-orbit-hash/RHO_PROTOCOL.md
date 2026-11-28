# Cold same-target orbit/rho distance

Freeze before running `rho_replay.py`. Compare the signed-pair orbit Rust IC
collector against the archived C++ `comparison/compare_rho.cpp` on the exact
public p=2^31-1 curve, generator and target shared by the frozen auxiliary
and plain bases. Check identity fields against the rho fixture before timing.
Use seeds 0,1,2, eight balanced arm-order repeats per basis, block shuffle
seed 2026112717: 48 matched pairs, 96 fresh-process arms. Charge wall and
parent-plus-child CPU from before basis regeneration (IC) or input copy (rho)
through process exit and answer parsing. Charge IC table/bitmap setup,
relation collection, elimination and generator answer check. Exclude program
compilation and frozen fixture JSON loading. Preserve every arm, including
failure and timeout status. Verify both answers against the public point.

Report medians of paired orbit/rho wall and CPU ratios separately for each
basis, with successes and censored arms. This C++ rho is an archived
same-target distance indicator, not an optimized universal rho baseline.
