# Frozen N41 public-point nine-pair join control

This run tests an exact group meet-in-the-middle source law on the public point
in raw target row `T 0` of `join_input.tsv`. The input was produced and checked
in `n41_w8_sixpair_mitm_20261011`; its 128 independent Sage group-add checks
are rechecked by the native program before table construction.

The left table uses all distinct-edge triples from slots 0, 1, and 2. Each
right probe uses a distinct-edge triple from slots 3, 4, and 5, one of four
signs of edge 0 from slot 0, and one of four ordered two-edge prefix panels:
`(132,136)`, `(124,128)`, `(116,120)`, `(108,112)` from slots 0 and 1.
The first accepted hit stops the run. All nine source edges must be distinct;
the program checks this and replays the raw group sum. The prefix panels and
terminal states are fixed in source before the public target is read.

Input SHA-256: `1f99b78210c3ec6c30945f3a9d261c1fd58cbb3a509e3a050fb5bdd4a75f06dd`

Source SHA-256: `b0a74e93f5daf4f66c22e866c6594b7e6e3e4df024cba2989e4df7e1ac5129db`

Native binary SHA-256: `b13c1d0cadbffe19a11131f1107af68260bcbb12247d4f542d5e31c61e494902`

Compile: `clang++ -O3 -std=c++17 -Wall -Wextra join9.cpp -o join9`.
One local worker, 180-second wall cap, 4 GiB sampled RSS cutoff at 0.2-second
sampling intervals, no shared precomputed table. The initial preflight attempt
to set a 4 GiB macOS `RLIMIT_AS` failed in `preexec_fn` before the solver
started (`ValueError: current limit exceeds maximum limit`); that failure is
preserved in `preflight.txt`. Runner preserves stdout, stderr, exit status,
elapsed wall, and child resource usage. The table-build cost is part of the target-specific
run here because the table is built after starting the program; it should be
separated if a reusable indexed candidate is later defined.

Outcomes are `HIT` with independent checked-Sage replay, `MISS_COMPLETE`,
`TIMEOUT`, or `ERROR`. This is a restricted N41 source-control experiment;
any transfer to N131 requires its own source and resource measurements.
