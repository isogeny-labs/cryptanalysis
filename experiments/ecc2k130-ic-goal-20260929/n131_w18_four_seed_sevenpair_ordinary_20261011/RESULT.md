# Four-seed seven-pair query on the N131 public point

The exact seven-pair, four-seed W18 circuit searched the frozen public point
through **300.894 solver CPU seconds** and 2,681 restart rows under one
CryptoMiniSat worker. Its terminal status is **`BOUNDED_UNKNOWN`** at the
300-second soft CPU limit. The full target-dependent attempt cost was
**1,400.779 seconds wall** on the contended local host; the saved receipt
charges every construction and search phase to this point.

The input is curve `EC1N131Ckb1heb5f1998f20b` over
`GF(2)[t]/(t^131+t^13+t²+t+1)`, subgroup order
`680564733841876926932320129493409985129`, public point
`Q=(1052727368764798954359115163823647684025,
2071227447786120917960296877345506689833)`, and workload
`cc09e7eb202a`. Seven rotated W18 pair slots choose affine seeds
`212,213,214,215`; one of 32 signed terminal states and one of four raw
preimages completes the exact S3 chain. The source census gives a
2,138.64042535 labeled-tuple mean upper ceiling for this policy.

| Frozen stage measure | Result |
| --- | ---: |
| XCNF SHA-256 | `eca62860f7842396421cc522211c7efddc62db4a51c3bb38109ea972d50fcbf9` |
| Variables / AND gates | 194,458 / 122,080 |
| CNF clauses / native XOR rows | 392,967 / 68,705 |
| Solver CPU / solver wall | 300.893746 s / 1,380.671349 s |
| All target-dependent phases, wall | 1,400.779348 s |
| Peak sampled parent plus solver RSS | 461,537,280 bytes |
| Restarts / terminal solver lines | 2,681 / 0 |
| Exit / stop | `-24` (`SIGXCPU`) / `CPU_SOFT_LIMIT` |

The [query receipt](query_result.json) preserves the exclusive phases:
4.103615 seconds for the four raw preimages, 5.297544 for 128 residuals,
10.646314 for formula construction, 0.058778 for XCNF serialization,
1,380.671349 for solver search, and 0.001749 for terminal parsing. The
sum is the charged wall interval. `solver.stderr.txt` is empty; the complete
`solver.stdout.txt` has no SAT or UNSAT line. The
[compressed XCNF](ordinary.xcnf.gz) replays byte-for-byte against the formula
hash, and the [independent checked-Sage audit](sage_audit_result.json)
verified all 128 public residuals. The [receipt audit](audit_result.json)
passed. This is a censored ordinary-query stage result, with
`candidate_id: null` and no measured relation row or rank increment.

CryptoMiniSat's startup log declined the seven `3315 × 9132` XOR matrices
under its default matrix limits. The next frozen test keeps the same XCNF,
public point, one-worker CPU and memory limits and enables those matrices in
the [Gaussian replay](../n131_w18_four_seed_sevenpair_gauss_20261011/protocol.json).
Its result will test the exact solver setting on the same ordinary query.
