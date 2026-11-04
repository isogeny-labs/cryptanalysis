# Results (derived from frozen records; no new measurement)

Available per-group-operation factor from a coordinate change: realistic c = 1.05 (batch depth is the only lever left once arithmetic is batched affine), generous c = 1.3 (the ALU ratio read in the lab's favour). Sources in data.json.

| row | gap IC/rho | f_g | f_g measured? | c* needed for parity | row speedup at c=1.05 | at c=1.30 | parity at c=1.05? | at c=1.30? |
|---|---:|---:|:--|---:|---:|---:|:--|:--|
| a1 n29 Frobenius-orbit IC vs rho-frob | 1.566 | 0.587 | yes | 2.61 | 1.029 | 1.157 | no | no |
| n41 disjoint cold CPU panel (compact vs rho) | 1.314 | 1.000 | no (envelope 1) | 1.31 | 1.050 | 1.300 | no | no |
| rule v8 Koblitz descent n47 (cold) | 4.67 | 1.000 | no (envelope 1) | 4.67 | 1.050 | 1.300 | no | no |
| baseline n41 rule v3 (cold) | 7.657 | 1.000 | no (envelope 1) | 7.66 | 1.050 | 1.300 | no | no |
| baseline n53 rule v3 (cold) | 13.24 | 1.000 | no (envelope 1) | 13.2 | 1.050 | 1.300 | no | no |
| baseline n61 rule v3 (cold) | 20.97 | 1.000 | no (envelope 1) | 21 | 1.050 | 1.300 | no | no |
| baseline n83 rank-finder (cold, wall) | 3.924 | 1.000 | no (envelope 1) | 3.92 | 1.050 | 1.300 | no | no |
| p36 prime res2 vs rho.negation | 2.59 | 1.000 | no (envelope 1) | 2.59 | 1.050 | 1.300 | no | no |
| tournament round 0026 n19a0 batch16 (Ir) | 11.52 | 1.000 | no (envelope 1) | 11.5 | 1.050 | 1.300 | no | no |

Reading: with f_g = 1 the required factor equals the gap itself, so the smallest gap on record, 1.314 on the n41 cold panel, needs c = 1.314, above the generous 1.30 by 1%; every other row needs c >= 1.566. On the one row with a measured f_g (0.587) parity needs c = 2.61, while the available factor is at most 1.05 to 1.30.

## Sources

- **a1 n29 Frobenius-orbit IC vs rho-frob**: gap from crypto research/ecbench_frobenius_orbit_vs_rho_20261014/README.md:76 (1.566 [0.992, 2.347], S in GAE/sqrt r); f_g: crypto research/ecbench_frobenius_orbit_vs_rho_20261014/tables/derived-phase-means.jsonl:5: ic_group 315 of ic_total 537 GAE (means of 48 runs); README.md:163 gives additions+doublings only IC/rho-frob = 0.96 The only row with a measured group-operation share.
- **n41 disjoint cold CPU panel (compact vs rho)**: gap from crypto research/notes/ecc2k130/disjoint_cold_v2_outcome_20261001/RESULT.md:28 (paired 1.314 [1.288, 1.359], CPU seconds); f_g: not recorded; selector_phase_admission_20261001/DECISION.md:9 splits elapsed into index build 35.27% and rank+targets 63.23% only. Envelope f_g = 1. Closest row to parity: 23.9% reduction needed.
- **rule v8 Koblitz descent n47 (cold)**: gap from crypto research/ic_tool_program/rule/v8/README.md:49 (4.67 [4.34, 5.07]); f_g: not recorded; setup wall split build 4.33M / collect 7.81M / select 3.60M / verify 1.52M / la 0.26M ns (mean of 135 repetitions, runs/k1n47/T0*-R1.price.json) carries no group-op split. Envelope f_g = 1.
- **baseline n41 rule v3 (cold)**: gap from cryptanalysis docs/ic/baselines.json n41 (cold 7.66 [6.90, 8.61]); unit one batched affine addition; f_g: not recorded; setup is 98.9% of cold S (BASELINES.md next_improvement). Envelope f_g = 1.
- **baseline n53 rule v3 (cold)**: gap from cryptanalysis docs/ic/baselines.json n53 (13.2 [11.8, 15.0]); f_g: not recorded; setup 99.7% of cold S. Envelope f_g = 1.
- **baseline n61 rule v3 (cold)**: gap from cryptanalysis docs/ic/baselines.json n61 (21.0 [18.6, 23.8]); f_g: not recorded; setup 99.7% of cold S. Envelope f_g = 1.
- **baseline n83 rank-finder (cold, wall)**: gap from cryptanalysis docs/ic/baselines.json n83 gap_tuned_rho (end-to-end cold 3.924, point estimate); f_g: not recorded; wall split e2e cold 7273.5 ms = rank 2806.5 + setup 4308.5 (index build 3246.3) + online 158.6; the index build is hashing, not group operations, so the true f_g is well below 1. Envelope f_g = 1. Factor-base construction uncharged on this row.
- **p36 prime res2 vs rho.negation**: gap from crypto research/ic_planner_exhaustive_20261026/README.md:335 (2.5921 [2.234, 3.008] at w=0); f_g: not recorded; the per-run records.jsonl is in the artifact store. Envelope f_g = 1.
- **tournament round 0026 n19a0 batch16 (Ir)**: gap from crypto research/ic_candidate_tournament_20260915/runs/round-0026/REPORT.md:72 (11.524 [10.718, 13.016] Ir); f_g: phase table lines 105-118 (M Ir): factor base+tables 18.536 of 30.347 total; collection+decomposition 1.840; verify+filter+linalg 3.591. No group-op split. Envelope f_g = 1.

## Measured coordinate or curve-shape arms in the lab

| arm | numbers | source |
|---|---|---|
| genus-2 weighted-projective state vs affine wrapper (not an elliptic curve) | state/wrapper 1.1016 pooled over 1,260 targets (0.5468-1.3037 across 36 cells, 12/36 favour state); wrapper/rho 3.7938, state/rho 4.1793 | crypto research/projective_law_followup_20261022/REPORT.md:22-42 |
| P-256 rho seed ladder, Jacobian vs affine (setup only, L0) | 0.6615 vs 11.5295 ms per seed, 17.43x, about 750 inversions to 1; the report says the effect on whole-run throughput is small | crypto benchmarks/20261017-gpu-nist-jac-seed/REPORT.md:43-51 |
| ECC2K-130 affine batch vs lambda-projective (priced, nothing built) | 38.1 vs 60.5 clmad per update (1.59x in favour of affine); affine batch 16 measured 14.41 B/s | crypto ecc2k130/LAMBDA-PROJECTIVE.md:104-121 |
| rho batched inversion rewrite (engineering, same coordinates) | Callgrind Ir/step 1.040 at n41 and n53; native 1.117 not established, A/A 7.0%; rerun paired 0.989 | crypto research/rho_batchinv_20261022/README.md:10-24 |
| Curve25519 factor-base coordinate: Weierstrass x, Montgomery x, Edwards y (support counts, k=20) | signed classes at width 2^10: 458, 533, 499; Edwards/Weierstrass F4 mul-adds per target 0.997-1.000 at t=4 and 0.989-0.993 at t=6-7 | crypto research/curve25519_algebraic_ladder_20261102/README.md:16-24; research/curve25519_edwards_semaev_20261102/README.md:53-89 |
