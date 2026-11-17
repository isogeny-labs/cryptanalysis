# CT185 — counterbalanced cold transfer does not identify arbitrary sequence-conditioned latency

2026-11-17, [pcc:unverified]. Independent frozen source/pinned-reader synthetic null, **not a native benchmark, cryptographic correctness result, or complete ECDLP speedup**.

## Falsification result

The original CT182 v2 statistics function from exact immutable reader commit `92d0c646a757046f8f10a015ae17ce0ed9d0fd2c` accepted the 48-packet/8-block synthetic matrix and reported a spurious 1.5x direct-over-retained transfer ratio for **both routes having identical intrinsic physical cost 1**. Each packet has exactly four ABBA and four BAAB blocks; the trailing A/A drift diagnostic returns 0, and the order-separated log ratios each equal ln(3/2). For strata with >1 independent packets, the packet-cluster bootstrap CI collapses to [1.5,1.5] because every input packet shares the same artificial nuisance. In single-packet identity strata the original reader intentionally provides no cross-packet interval. [pcc:unverified]

Construction: for an ABBA block give the four treatment slots time factors (3,2,2,3); for BAAB give (2,3,3,2). No route-specific multiplier is applied (A=B=1). The physical-time schedule is a deterministic function of the known order and slot. Therefore every block has two A-labelled samples totalling 6 and two B-labelled samples totalling 4. The terminal A/A pair costs (3,3), making its log-ratio 0. This is an **identifiability counterexample under a permitted nuisance model**, not a report that the actual Rust routes are equal or that an actual host exhibits that nuisance.

| Controlled scenario | 16-stratum reported A/B ratio | ABBA order diagnostic | BAAB order diagnostic | Terminal A/A |
| --- | ---: | ---: | ---: | ---: |
| Identical physical costs; stationary slot factors (3,2,2,3) | 1.000 | ln(1.5) | ln(2/3) | 0 |
| Identical physical costs; factors tied to sequence | **1.500 false advantage** | ln(1.5) | ln(1.5) | 0 |
| True physical 5:4 ratio, stationary slots | 1.250 | not the sole claim | not the sole claim | 0 |

The difference from CT181 is important: counterbalancing does cancel a **stationary** slot effect. CT185 shows it does **not** establish robustness against period/sequence interactions or carryover that changes the slot profile together with the assignment. The null is consciously adversarial and synthetic; no empirical prevalence of this failure mode is inferred.

## Reproduction and actual hosted checks

- Prospectively frozen protocol: `CT185_ORDER_LOCKED_NULL_PROTOCOL.md` at `cda9364024b1cb1ce30a231fec97d3a1cbf46b9f` prior to test.
- Test: `test_ct185_order_locked_null.py` imports and directly executes the original immutable CT182 `paired_statistics_v2`, with the original fixture blob `9ac741668dd1ffa9632ff0d58e6f4dd9f2dd18c3` and roster digest `1dddb4839321ad6560fd429330778aa083ff3a13625393250e964c05f9fc5ee4`. Original reader and original producer branches are not edited.
- First scoped workflow [#44108600235](https://github.com/isogeny-labs/cryptanalysis/actions/runs/44108600235) failed on a test-harness typo (`PINN` instead of `PINNED`), before any substantive assertion. Kept the failure.
- Corrected [source-only scoped workflow #44108952629](https://github.com/isogeny-labs/cryptanalysis/actions/runs/44108952629), exact tested code SHA `0d4ce551d166358aad6c33a6452ea784dfc4d2dd`, job `134128960481`, **completed successfully: 4/4 normal Python and 4/4 optimized Python**. The immutable CT182 reader Git hash and 48-row fixture hash were checked by the job. The decoded logs independently show the four relevant tests passing; this is not a signed PCC verdict.
- Local reconstruction of the four-slot arithmetic yields stationary null 1.0, order-locked null 1.5, stationary true effect 1.25. The exact reader check is the scope of the hosted CI, not the local algebra alone.

A future checkout with the pinned reader staged in `ct182-pinned` can reproduce with:

```bash
export CT182_SOURCE_ROOT="$PWD/ct182-pinned/experiments/chained-transfer-public-target/primitive-pricing-01"
root=experiments/chained-transfer-public-target/primitive-pricing-01
python3 -S -m unittest discover -s "$root" -p 'test_ct185_order_locked_null.py' -v
python3 -O -S -m unittest discover -s "$root" -p 'test_ct185_order_locked_null.py' -v
```

## Meaning for the cold single-target ECDLP decision

Do not promote a CT182 transfer-only ratio or its narrow bootstrap interval into a causal route-speed claim solely because 8 blocks balanced ABBA/BAAB and the final-slot A/A control was stable. The next discriminating test is an independently source-checked **sham first-four-slot same-route assignment** on the same host/packet grid, ideally with randomized timing/order and a prospectively frozen acceptance rule for period interactions. It must not silently mutate the existing v2 producer/reader or waive any EKS Spot cap.

Even a clean sham cannot replace original whole 695/701-artifact custody, native 48 arithmetic parity, primitive prices `C169/C13a/C13b/N2_actual/D`, the complete cold **single-target** transfer/solve cost against strongest rho/BSGS/IC (including setup, transfer, recovery, LA, memory and uncertainty), or signed independent PCC.

## Sources checked

Exact cryptanalysis #1700, #1706, #1711, #1713, #1714; crypto #3877, #3904, #4215 and GPU IC #4178; frozen original CT125/CT172/CT175 source. Measurement design background: NIST/SEMATECH confounding glossary (https://itl.nist.gov/div898/handbook/pri/section7/pri7.htm); Penn State STAT 509 §12.5–12.6 (https://online.stat.psu.edu/stat509/Lesson12); Reed, *Four Period Crossover Designs* (2012), DOI 10.22237/jmasm/1335846240. Shared research-KB service is unavailable and the autoresearcher source checkout is vault-encrypted in this runtime; absence claims are not drawn from that gap.

## Gates

Draft stacked [PR #1715](https://github.com/isogeny-labs/cryptanalysis/pull/1715) on CT184 draft #1714. Authenticated source and scientific PCC, original corpus replay, native execution, downstream proof completeness, CI/review/ledger gates, and full-ECDLP advantage remain unresolved. No paid machine allocation, merge override, native Rust invocation or protected branch update occurred.
