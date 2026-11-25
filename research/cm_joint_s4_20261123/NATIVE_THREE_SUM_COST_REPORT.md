# Same-target native S4 cost screen

The [cost protocol](NATIVE_THREE_SUM_COST_PROTOCOL.md) and runner were
committed at `be44ddf27` before the initial 64-target stream. The
[repeat addendum](NATIVE_THREE_SUM_COST_REPEATS.md) was committed at
`ab119597e` before four sequential measured runs. Each run uses the
same source and native endpoint eight-point bases on the existing
degree-five horizontal pair, 64 identical targets per arm, and seven
interleaved Gröbner solves per target and arm. The full [initial run](native_three_sum_cost_results.json)
and all four repeat JSON files retain every query, rational truth,
algebraic verdict, build time, and individual solve time. Separate
`.time.txt` files retain process real/user/sys. [pcc:unverified]

The original single-stream sum of per-query median solve times was
`0.104899 s` on the source and `0.101455 s` on the endpoint. That
small raw difference motivated the frozen repeats. Their results are:

| Seed | Source solve medians, sum (s) | Endpoint solve medians, sum (s) | Endpoint/source expected solve work per hit | Rational positives, source / endpoint | Process real / user / sys (s) |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 20261125 | 0.088175 | 0.086181 | 1.0199 | 4 / 2 | 4.61 / 3.02 / 0.49 |
| 20261126 | 0.085262 | 0.084599 | 1.0354 | 13 / 10 | 3.50 / 2.75 / 0.30 |
| 20261127 | 0.080792 | 0.083943 | 1.0842 | 6 / 5 | 3.28 / 2.65 / 0.28 |
| 20261128 | 0.086724 | 0.084940 | 1.0220 | 6 / 3 | 4.02 / 2.83 / 0.33 |

The ratio divides each solve-time sum by the **exact** full-group
support fraction from the earlier [yield census](NATIVE_THREE_SUM_REPORT.md):
`96/1068` for source and `92/1068` for native endpoint. It therefore
compares expected component work per useful uniform target without
mistaking the 64-row positive counts for stable yield estimates.
All four ratios exceed one, so the prespecified 10% endpoint-gain
gate fails. The small raw solve-time differences do not support a
robust endpoint cost advantage. [pcc:unverified]

Every one of the 256 queries has a matching exact signed group truth
and S4 algebraic satisfiability verdict in **both** arms; the retained
`truth_mismatch_rows` arrays are empty. The runs required 64 draws
per seed, with no rejected identity query. Map construction took
`0.059–0.228 s`, native-base construction `0.072–0.097 s`, and the
sum of 64 per-query builds `0.016–0.021 s` per arm. Those setup and
build times are excluded from the solve-median ratio; including them
cannot turn the observed endpoint ratio into an established full
cost gain. The process real/user/sys receipts include Sage startup
and both arms, so they are not separable end-to-end arm times.
[pcc:unverified]

Reproduce one frozen repeat from the repository root, varying the
listed seed and output basename for the other three:

```sh
/usr/bin/time -p /Volumes/SSD990/cryptanalysis/sage -python -c \
  "import sys; sys.path.insert(0, 'research/cm_joint_s4_20261123'); import native_three_sum_cost as n; n.SEED=20261125; n.main()" \
  > /tmp/native_three_sum_cost_replay.json \
  2> /tmp/native_three_sum_cost_replay.time.txt
```

Timing will vary, but target coefficients, exact truths, and verdicts
are reproducible. SHA-256 of the frozen cost protocol, repeat
addendum, and runner respectively:
`ae149a3a512a89b8454f64fd50b771bb1ba28d49dcd0e29bb01b99242ad84658`,
`22ddb4df11f977b024b2d7c761fa5484efefaf79936a0c91e9044e4b32be53e0`,
and `ce1f859f44ec76fe57cff5372a2264ad004b9d0f48c15e2f809e42e094bb4cb6`.
[pcc:unverified]

This is a small-field equation-system component test. It excludes
relation collection, witness extraction, rank, descent, peak memory,
host isolation, and matched rho. It does not extrapolate to P-192 or
other native base rules. The earlier yield-only stopping rule is
corrected by this explicit cost screen: a lower-yield base could in
principle win on solve cost, but this fixed pair does not pass that
component gate. [pcc:unverified]
