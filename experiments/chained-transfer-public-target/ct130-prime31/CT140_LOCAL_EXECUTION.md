# CT140: small-lane cold ECDLP control and a CT139 unit repair

2026-11-15. [pcc:unverified]. Preregistered at [protocol commit d0120ef8](https://github.com/isogeny-labs/cryptanalysis/commit/d0120ef8e2358203825d6c477a237590718ea7a8) **before** local execution. Inherits cryptanalysis #1550, crypto #3877; CT126/C137 native pricing is separate.

## Result: 5,120 checked toy-curve scalar recoveries

Fixed public seeds 20261340–20261343; exactly 32 distinct source public points per seed; four widths (2, 4, 8, 16); five cold source/target solver arms with two alternating repeats per target. Four-row rotating width schedule. Native C++17 `-O3 -DNDEBUG` under a 2 GiB virtual-memory and 120 s/process cap, no paid backend. Unchanged CT136 native source SHA256 `20b0305d0b291602dd141a278c00459c47e78608f17e33bea6395a3106438921` with one-occurrence guarded replacements for lane count, round bound, labels, and count. [pcc:unverified]

| Width | Best fixed source total (ns) | Best fixed mapped total (ns) | Source / mapped |
|---:|---:|---:|---:|
| 2 | 1,574,967,345 | 1,068,861,498 | 1.473500 |
| 4 | **1,023,458,260** | 848,125,089 | 1.206730 |
| 8 | 1,157,085,846 | 904,053,947 | 1.279886 |
| 16 | 1,242,474,565 | **847,199,361** | 1.466567 |

The **best fixed direct source solver is batch width 4**, and the **best fixed transferred solver is width 16**. On this same local host/cohort the corrected whole-cohort ratio is **1.20804890456×** (descriptive paired-bootstrap 95% interval **1.11101475–1.38616589×**). Using width 16 on both arms alone gives 1.466567× and therefore overstates the advantage against the better width-4 source reference. This is a concrete source-reference optimization; it is not evidence of a generalized prime-field attack. Compared with CT139's 1.31936789× from a different container/machine state, host equivalence is unproved, so do not attribute the difference to the algorithm. [pcc:unverified]

Same-host observed extra *unmeasured* overhead headroom is `(1,023,458,260 - 847,199,361)/(128 * 1e6) = 1.3770226484375 ms/target`. The mapped arm already times two map calls and final scalar verification, but **does not** include the full original-prime 695/701 Jacobian correction chain, all setup, strong rho/BSGS/IC and linear algebra. Not an accepted complete original-prime ECDLP advantage. [pcc:unverified]

## Fail-closed independent checks and custody

The separately written `ct136_verify.py` independently recomputed source public points, isogeny identities, known-answer logs, inversion and state counters, target count, repeated-arm order, aggregate totals and ratio footer; the CT140 wrapper also compared identical targets across widths, original native-source SHA, generated code SHA, memory/time receipts and exact run schedule. **All 5,120 answers** accepted in ordinary and `python -O`; four mutation/dimensional controls rejected. Max recorded RSS **7,268 KiB**. These are local producer-run checks, not a signed PCC or independently administered runner. [pcc:unverified]

Local conversation evidence archive `ct140_low_lane_evidence_20261115.zip`: **69 members**, SHA256 `117442544b0f91ff54d925cf62bc1f6e3260c0c86d872ca8b43e308b8f1518a1`. Contains source, generated variants, compiled binaries, every 16 original CSVs, stdout/stderr and resource receipts, both independent verifiers, negative controls and the manifest. Durable object-store custody and signed review pending. Do not silently replace a raw file with an edited aggregate. [pcc:unverified]

### Correct CT139 millisecond units (actual defect)

CT139's `by_width.extra_headroom_ms_per_target` was computed as `(source_ns-target_ns)/128`, which has **ns**, despite its `ms` label. At width 16 in CT139's new run the old value is `1192640.125`; the correct value is **1.192640125 ms**. The CT139 top-level millisecond field already correctly divides by `1e6`. This PR fixes exactly that one expression in `ct139_headroom.py` and preserves the frozen legacy outputs. Rerunning the corrected auditor with both unchanged original archives under Python normal/-O gives CT138 width16 **1.2333947109375 ms** and CT139 width16 **1.192640125 ms**. No input scalar, underlying solver result, measured nanosecond total or ratio changes. [pcc:unverified]

## Reproduction and next blocking gate

From the included archive:

```sh
python3 ct140_verify.py
python3 -O ct140_verify.py
python3 ct139_headroom.py ct138_old . > ct140_ct139_corrected_headroom.json
```

For fresh native replay, run `python3 ct140_generate.py generated_ct140`, build each `ct140_width{2,4,8,16}.cpp` with `g++ -std=c++17 -O3 -DNDEBUG -I.`, then execute the 16 source/seed pairs in the frozen protocol under 120s/2GiB limits. See raw archive for captured schedule.

**Priority:** execute admitted CT126/C137 native C169/C13a/C13b/doubling D paired original/reuse binaries on the fixed original-prime source; then price full 695/701 Jacobian chain and cold same-host optimized rho, BSGS, IC, setup, verification, LA and peak memory. Preserve the source-character FB30 obstruction in concurrent crypto #3877 and cryptanalysis #1523. No EKS/Spot spend, protected merge, scientific promotion or full-original-prime speedup claim. [pcc:unverified]

Prior art/practices checked: Bernstein–Lange negation-map rho and Montgomery inversion batching (https://cr.yp.to/elliptic/negation-20110102.pdf), and GLV endomorphism techniques (https://arxiv.org/abs/1106.5149). No algorithmic novelty claim; shared research KB and Conductor not exposed in this session.
