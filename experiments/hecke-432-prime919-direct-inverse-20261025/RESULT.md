# Complete source-free level-432 inverse at p=919

The exact rational resolvent produces **1,224** `(C,E)` pairs at p=919. The degree-12 B polynomial and the degree-three B-to-E isogeny have a linear gcd at every pair, yielding exactly one rational B point. Direct cyclic 16/27 path recovery then returns **1,152 single-chain and 72 double-chain fibers**, accounting for all **1,296** independently enumerated noncuspidal source chains. The independent audit finds zero missing, extra, or incorrect chain-candidate sets.

| Stage | Complete p919 result |
| --- | ---: |
| Rational C points, including identity | 972 |
| Rational E points, including identity | 868 |
| Resolvent `(C,E)` pairs | 1,224 |
| Valid exact B lifts | 1,224 |
| Distinct C points in inverse image | 324 |
| Raw source-chain evaluations and matches | 1,296 / 1,296 |
| Chain-candidate multiplicity | 1,152 single; 72 double |

The double fibers project to exactly six B points: `(1,297)`, `(1,622)`, `(52,297)`, `(52,622)`, `(866,297)`, and `(866,622)`. These are precisely the points satisfying `x_B³=1` and `y_B²=−15` modulo 919. All six have order 434 in `B(F₉₁₉)`, as checked by Sage. This is an exact finite-field concentration, not yet a uniform characterization of exceptional fibers across primes.

## Construction and independent audit

[`protocol.json`](protocol.json) froze the prime, rational resolvents, B branch and polynomial, modular coordinate maps, path enumerator, and forward evaluator by SHA-256 before the source-free screen. The p919 source census and forward image are explicitly audit-only inputs: [`screen.py`](screen.py) and [`recover_sage.py`](recover_sage.py) never load them. The screen enumerates every rational point of `C:y²+y=x³−7` and `E:y²=x³+432`, tests the exact 12-degree `x_E` resolvent, and records every passing pair in shards. The checked-Sage producer computes the exact polynomial gcd with `T³−x_E T²−64`, lifts B points, derives source and intermediate j-invariants from C, enumerates the matching 16/27 paths, and verifies each forward B image.

The pure-Python [`audit.py`](audit.py) independently enumerates every rational resolvent pair; recomputes all **1,224** specialized gcds with explicit Bézout and divisibility checks; enumerates all rational B lifts; and rebuilds source-chain keys from the separately frozen p919 census and image. [`audit.json`](audit.json) records the exact candidate-set comparison and six exceptional B points. [`result.json`](result.json), [`gcd_rows.json`](gcd_rows.json), the candidate shards, and [`sage-runtime-info.txt`](sage-runtime-info.txt) preserve the producer evidence.

The checked Lean/Std theorem `generated_keys_perm_sources` proves exhaustive equality of duplicate-free generated and source-key lists from containment and the equal count 1,296. `fiber_count` checks `1152+72=1224` and `1152+2·72=1296`. The pinned build and `#print axioms` output are in [`formal/`](formal/). The theorem uses only standard Lean foundations (`propext`, `Classical.choice`, `Quot.sound`). The concrete finite-field arithmetic and modular-curve source map are verified by the producer and independent audit; their formalization in Lean remains open.

Replay from the repository root:

```sh
python3 experiments/hecke-432-prime919-direct-inverse-20261025/screen.py
./sage --runtime-info > experiments/hecke-432-prime919-direct-inverse-20261025/sage-runtime-info.txt
./sage -python experiments/hecke-432-prime919-direct-inverse-20261025/recover_sage.py
python3 experiments/hecke-432-prime919-direct-inverse-20261025/audit.py
cd experiments/hecke-432-prime919-direct-inverse-20261025/formal && lean ChainCoverage.lean
cd .. && shasum -a 256 -c SEAL.sha256
```

This is an out-of-sample confirmation of the source-free inverse pipeline tested at p883, p887, and p997. The next mathematical step is to derive an intrinsic condition on a level-432 point that predicts when distinct 16-chains share `(C,E,B)`, then test that condition at new primes before observing their fibers.
