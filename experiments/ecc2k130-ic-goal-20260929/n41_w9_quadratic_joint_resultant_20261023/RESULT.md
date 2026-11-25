# Direct target-conditioned quadratic resultant: exact circuit and capped probe

The N41 circuit eliminates the right two-pair sum coordinate from two S3
equations and retains a target-dependent resultant gate. The frozen
positive row satisfies the resulting 116,305-AND Boolean circuit, and
the 32 reachable controls fail its preceding partial-sum link. In a
matched 20,000-conflict ABBA probe, the direct resultant used about half
the propagations and wall time of the explicit right-sum witness encoding,
but 29% more decisions. Both encodings remained indeterminate at the cap.

## Exact algebra and controls

For pair reciprocals `u,v`, preceding reciprocal `z`, public target
reciprocal `t`, and an eliminated right-sum reciprocal `y`, the two
quadratic S3 equations have coefficients

```
f(y) = A y² + B y + C,  A=1+(uv)², B=uv, C=(u+v)²
g(y) = D y² + E y + G,  D=1+(zt)², E=zt, G=(z+t)².
```

The circuit enforces the characteristic-two resultant
`R=(AG+CD)²+(AE+BD)(BG+CE)=0`. A common finite `y` implies this
condition. The Boolean circuit also contains the existing left norm,
source-pair quadratics, and the links `S3(z,u,w)=0` and `S3(w,v,t)=0`.
The latter equations already imply `R=0`: see the subsequent checked
Lean theorem in `../n41_w9_source_reduced_resultant_20261023/`.
Thus the new gate is exact as a necessary equation but adds no algebraic
filter after those links.

The field is the archived `EC1N41Ckb1h7d5e80d3c4d0` representation.
The input is the single frozen public point in the immutable fixture.
The 33 archived rows are one planted correctness row and 32 reachable
controls; they measure circuit correctness, not natural relation yield.
`preflight_result.json` records zero leading-coefficient exceptions in
this panel. The circuit's complete positive assignment satisfies every
clause and XOR. The target resultant vanishes on 1 of 33 rows, while
the pre-existing preceding link already vanishes on the same 1 of 33.

## Circuit and bounded solver results

| Encoding | AND gates | Variables | Clauses | Native XOR rows |
| --- | ---: | ---: | ---: | ---: |
| Direct resultant | 116,305 | 133,375 | 350,856 | 16,866 |

The direct formula has 11,291,455 bytes and SHA-256
`afaafb7a7f9684b46bb0597b92763b37369cede296e7f8b1625da5c3c7a1b4b2`.
The checked Sage builder took 4.478 s; its supervised parent took 4.725 s
and sampled 181 MB combined peak RSS. The first build attempt through
system Python failed because that interpreter lacked `psutil`; its
failure receipt is `build_attempt1.json`. The successful build used the
required checked repository Sage launcher and recorded its runtime.

| ABBA arm | Reported conflicts | Decisions | Propagations | Wall seconds | Status |
| --- | ---: | ---: | ---: | ---: | --- |
| Explicit `y`, first | 20,002 | 35,089 | 79M | 2.526 | Indeterminate at cap |
| Resultant, first | 20,002 | 45,271 | 38M | 1.280 | Indeterminate at cap |
| Resultant, second | 20,002 | 45,271 | 38M | 1.271 | Indeterminate at cap |
| Explicit `y`, second | 20,002 | 35,089 | 79M | 2.509 | Indeterminate at cap |

The frozen promotion rule required the direct resultant to use no more
than 90% of adjacent explicit-witness decisions and no more than 125%
of its wall time. The decision condition failed. No full N41 or N131
public query was promoted from this gate. These are ordinary-host stage
measurements, not single-target online IC/rho timing.

## Source-quadratic reduction and next step

Reducing the exact resultant modulo the two source-pair quadratics
produced a 54-term polynomial linear in each pair reciprocal `u,v`.
It matched the unreduced resultant on all 33 frozen rows. That
representation was not promoted to a Boolean circuit after the direct
resultant failed the decision gate and the universal redundancy theorem
showed the algebraic filter was implied.

The next target-conditioned constraint must use additional information,
such as which root of each source-pair quadratic corresponds to its
actual signed source-point sum. The first experiment should verify the
branch selector on all 71 admissible codes, then measure its incremental
rejection and circuit cost on frozen public controls.

## Evidence

`protocol.json`, `build_protocol.json`, `build_run_protocol.json`,
`probe_protocol.json`, and `reduction_protocol.json` freeze source hashes
and caps. `verify_archive.py` checks these receipts, result statuses,
formula digest, the 33 exact controls, and all four capped arms. The
complete stdout/stderr for each solver arm is retained here.
`candidate_id` remains `null` until the specified full IC pipeline exists.
