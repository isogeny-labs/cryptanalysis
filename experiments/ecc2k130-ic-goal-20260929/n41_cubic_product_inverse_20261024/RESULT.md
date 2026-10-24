# N41 quadratic third-product inverse: 410,256 exact queries

A target-conditioned quadratic in the third pair product processed every one of the 33 frozen N41 residual panels. All 410,256 queries specialized to degree two; their 820,512 field roots produced one usable source product and one exact seven-block point match. The 33-panel target-dependent traversal took **94.806972250 seconds** with one worker. The method replaces a cubic-looking norm test by a quadratic in the product, after removing the exceptional `1+r` factor.

## Method

For each of the 12,432 frozen first-two pair chart roots `u` and each frozen target residual chart `t`, form

`A=t²+u(u+1)t(t+1)+(t+1)²`, `B=u(u+1)t(t+1)`, `D=(u+1)²t²+u²(t+1)²`, `S=s²`.

The third pair product `r` must satisfy the polynomial

`R=(D+SA)²+SB²+rB(D+S(A+B))+r²D(A+B+D)=0`.

It is the resultant in `d` of `(1+r)d²+rd+S` and `Ad²+Bd+D`. The original inverse norm equals `(1+r)R`, so removing `1+r` is exact for this enumerated N41 third source set, which contains no `r=1`. Resolve the quadratic with the field halftrace routine, look up roots among 40 actual source products, enforce distinct source columns, and check the entire point sum against the fixed public point. The Lean factor identity and common-root implication are described in `PROOF_MAP.md`.

## Frozen measured result

| Field/curve | Panels | Queries | Root outcomes | Source hits | Admissible hits | Point matches | Target-dependent wall | Setup | Peak sampled RSS |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `EC1N41Ckb1h7d5e80d3c4d0` | 33 | 410,256 degree two | 820,512 | 1 | 1 | 1 | 94.806972250 s | 2.386504250 s | 86,917,120 B |

The point match is archived as panel 0, prefix state IDs 97 and 151, third state 42, suffix state IDs `[0,14,109,51]`; the coordinate hit is `[0,24,37,10,801447660706,216004441708]`. `verify.py` independently expands the Sylvester determinant, rechecks the polynomial factor identity, the source digests and the complete frozen archived witness census. `verification.json` records `PASS_INDEPENDENT_N41_QUADRATIC_INVERSE_AUDIT`. `./sage --runtime-info` was captured before the producer as `sage_runtime_info.json`. Execute the producer only on a fresh artifact directory because it refuses to overwrite `result.json`; recheck an existing result with `python3 verify.py` and `lean QuadraticInverse.lean`.

This is a **component traversal of 33 fixed residual panels** on an ordinary local macOS host, with `candidate_id: null`. The prior N41 four-code full join (22.708 s on one suffix triple) has a different search space and is not a paired timing comparison. No single-target end-to-end IC/rho ratio can be derived from these rows.

## Next frozen gate

Transfer the symbolic identity and `r=1` exclusion test to the exact N131 W23 pair-product chart, then measure a fixed constructed witness and the previously frozen ordinary public input separately under a declared cap. Preserve each eligible product, multiplicity, root count, source hit, distinct-column check, and full point replay. A one-target online IC timing comparison requires all target-dependent relation acquisition, rank completion, target descent, recovery check, and a same-point rho reference inside the same measured resource envelope.
