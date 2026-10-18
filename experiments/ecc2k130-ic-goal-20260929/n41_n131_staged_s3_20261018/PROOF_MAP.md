# Staged reciprocal S3 proof map

For reciprocal (x)-coordinates (a,b,t), the staged gate is

`S3(a,b,t) = (abt)^2 + abt + a^2 + b^2 + t^2`.

The first-three-pair circuit exposes the reciprocal `m` of the sum of
the first two signed source-pair points. It imposes `S3(a,b,m)=0` and
`S3(m,c,z)=0`, where `z` is the reciprocal of the three-pair sum. The
source-pair quadratics constrain `a,b,c` to their exact code roots.

The two S3 equations are quadratics in `m` with coefficients
`(A,B,C)=(1+(ab)^2,ab,a^2+b^2)` and
`(D,E,G)=(1+(cz)^2,cz,c^2+z^2)`. A common root gives
`M=(A*G+C*D)=(A*E+B*D)*m=L*m` and
`B*G+C*E=L*m^2`. Consequently
`M^2+L*(B*G+C*E)=0`, exactly the F4 polynomial used by the
preceding first-three-pair norm. This implication holds even if a
quadratic leading coefficient vanishes.

| Result | Lean declaration | Hypotheses and status |
| --- | --- | --- |
| Shared quadratic root implies F4 eliminant | `StagedS3.two_quadratics_imply_resultant` | Arbitrary commutative ring of characteristic two; kernel checked. |
| Two reciprocal S3 links imply the exact F4 polynomial | `StagedS3.staged_s3_implies_f4` | Arbitrary commutative ring of characteristic two; kernel checked. |
| Group-coordinate and full-solution bridge | Open Lean bridge | Requires exact Koblitz group law, source-code/root correspondence, and nonexceptional intermediate chart. The checked-Sage [audit](audit_result.json) exhausts all 79,424 disjoint N41 first-two-pair state combinations and finds zero identity and zero-`x` sums. The N131 512-code audit is sampled only; a full N131 encoding must include exceptional branches or prove their absence for its entire source domain. |

Every genuine N41 five-pair relation has a first-two-pair sum in this
chart on the frozen source domain, so its signed points supply `a,b,c,m,z`
that satisfy the staged equations. The equations may admit extra
coordinate witnesses; a terminal SAT model is accepted as a relation
only after independent signed-point group replay.

The actual module is [StagedS3.lean](StagedS3.lean), built with pinned
[Lean 4.34.1](lean-toolchain). `lean StagedS3.lean` returned exit code
zero. [lean_check.log](lean_check.log) records `#print axioms`: the two
declarations depend only on `propext`, `Classical.choice`, and
`Quot.sound`. No `sorry`, `admit`, custom research axiom or unverified
native evaluation is used. `lean4checker --fresh` was unavailable on
this host.
