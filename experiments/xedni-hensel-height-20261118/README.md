# Coordinate Hensel steps and rational height

## Result

For the first eligible public relation under the frozen query law, successive
coordinate shifts raised the exact rational relation residual's 313-adic
formal-parameter depth from 1 to 8. The maximum numerator/denominator bit
length of the rational model rose from 23 to 205. Every intermediate exact
group sum was nonidentity. This is a constructive finite-depth lift and a
measured height trajectory for one preselected relation.

| Depth | Model bits | Residual-coordinate bits | Formal-parameter numerator bits |
| ---: | ---: | ---: | ---: |
| 1 | 23 | 587 | 585 |
| 2 | 54 | 1408 | 1413 |
| 3 | 74 | 2030 | 2042 |
| 4 | 102 | 2865 | 2886 |
| 5 | 119 | 3353 | 3376 |
| 6 | 148 | 4222 | 4259 |
| 7 | 177 | 5124 | 5170 |
| 8 | 205 | 5964 | 6019 |

The public grid contains 512 queries, 6,656 vector tests, and nine public
hits. The selected relation is the first hit with distinct point x-coordinates:
`p=313`, `q=331`, `G=(0,130)`, target `w=300`, offsets `(0,13)`,
`U=(15,174)`, `V=(236,132)`, and vector `(5,4)`. It is query 5,
vector event 68. The selection is fixed by `protocol.json` before rational
lifting, and is an existence/control result rather than a relation-yield
estimate for the lifting rule.

## Construction and proof boundary

Let the centered lifts of `U,V` have coordinates `(x1,y1),(x2,y2)`.
At every step, the four integer shifts add multiples of `p` to those
coordinates. Interpolate

`A = ((y1²-x1³) - (y2²-x2³))/(x1-x2)` and
`B = y1²-x1³-A*x1`.

The run checks nonsingularity, good coefficient reduction, exact point
membership, and the exact rational group sum `R=5P1+4P2`.
For `R` in the reduction kernel, it uses `t(R)=-x(R)/y(R)`.
At precision `p^(k+1)`, it probes coordinate axes in order, takes the
first nonzero finite difference, and chooses the unique digit that
cancels the current `p^k` coefficient. All seven accepted steps used the
first coordinate axis. `run-result.json` retains the attempted probes,
shifts, coefficients, points, exact residuals, and formal parameters.

The proved arithmetic obstruction is conditional: if the absolute
numerator of an exact rational residual is divisible by `p^k` **and**
strictly below `p^k`, it is zero. The Lean declaration
`XedniHenselHeight.numerator_zero_of_depth_and_height` checks this step.
Its hypotheses require a bound on the numerator of the **same exact
residual**. The experiment does not supply a uniform bound as precision
increases; at depth 8 the formal-parameter numerator has 6,019 bits while
`313^8` has 67 bits. The full proposed xedni-calculus impossibility
statement therefore remains open. A next proof step is a uniform height
bound for the allowed lift family, or a lower bound on height required by
successive cancellations, stated for an exact rational group relation.

## Reproduction and proof map

The frozen protocol SHA-256 is
`5b880b5c02a42d52dbc3028ad10f9cc3b610d8354fa8950be3f3248b1e895ca5`.
The parent protocol SHA-256 is recorded in `protocol.json` and checked by
both scripts. `runtime-info.json` records the checked Sage installation.

```sh
/Volumes/SSD990/cryptanalysis/sage --runtime-info > experiments/xedni-hensel-height-20261118/runtime-info.json
/Volumes/SSD990/cryptanalysis/sage -python experiments/xedni-hensel-height-20261118/run.py
python3 experiments/xedni-hensel-height-20261118/audit.py
cd experiments/xedni-hensel-height-20261118/formal
lake build HeightDivisibility
```

The audit uses separate pure-Python finite-field affine arithmetic to
regenerate every public query and relation, and exact `Fraction` arithmetic
to replay every probe and accepted rational group sum. Its receipt is
`audit-result.json`.

| Mathematical statement | Lean declaration | Status / assumption |
| --- | --- | --- |
| A nonzero numerator divisible by `p^k` has magnitude at least `p^k` | `numerator_height_lower_bound` | Checked; natural absolute numerator and divisibility supplied |
| Divisibility by `p^k` plus strict numerator-height bound forces zero | `numerator_zero_of_depth_and_height` | Checked; natural absolute numerator, bound and divisibility supplied |
| A uniform numerator-height bound for this coordinate-lift family | none | Open; observed values grow along the selected path |
| Zero formal numerator implies exact relation identity for every allowed curve/point configuration | none | Open; requires formal group law and exceptional-case bridge |

The Lean module builds with the pinned Lean 4 `v4.35.0-rc4` and mathlib
`021c46bdd042f67b538b9f9871d556a93713a9a9` revisions. Its
`#print axioms` output lists only standard `propext` for both declarations.
The module contains no `sorry`, `admit`, or custom claim axioms. A separate
`lean4checker --fresh` executable was unavailable on this host. The checked
proof is the stated arithmetic implication; the uniform elliptic height
bridge remains the next theorem to establish.
