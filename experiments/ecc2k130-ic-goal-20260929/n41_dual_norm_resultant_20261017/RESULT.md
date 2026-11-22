# Eliminating one partial coordinate in the public N41 dual norm

The quadratic resultant eliminates the right 41-bit partial-sum coordinate
while preserving the archived six-pair public-point witness. On the same
unrestricted six-code N41 source geometry, it produces 541,388 AND gates,
2.898 times the preceding two-norm circuit. An ordinary one-worker
CryptoMiniSat run searched for 130.059 s and ended at its parent wall cap with
status `BOUNDED_UNKNOWN`.

## Construction

Let `t` and `u` be reciprocal coordinates of the left and right three-pair
sums, and `q` that of the public point. In characteristic two,

`S3(t,u,q) = (1+(tq)^2)u^2 + (tq)u + (t+q)^2`.

On the branch `1+tq != 0`, set `A=(1+tq)^2`, `alpha=tq/A`, and
`beta=(t+q)^2/A`. Reduce the second three-source norm in the quadratic
algebra `u^2=alpha*u+beta`, giving `r0+r1*u`; require its norm
`r0^2+alpha*r0*r1+beta*r1^2` to vanish. The first three-source norm remains
at the free coordinate `t`. The same 40 allowed pair codes per slot and 690
cross-slot folded-column collision clauses are present. The exceptional
branch `1+tq=0` needs separate treatment in any complete solver.

The public raw target is `(2026560328086, 1928332930914)` on
`EC1N41Ckb1h7d5e80d3c4d0`, frozen from the earlier independently audited
six-pair join. The archived witness satisfies every generated clause and
native XOR row. The independent exact-field audit computes both roots of the
public `S3` quadratic and obtains right-half norm values
`(0, 539479613123)`, so their product vanishes. The witness has
`1+tq=86709635634`, within the branch tested. It is a control input, not a
solver assumption. This is a stage experiment with `candidate_id: null`.

## Frozen measurements

| Stage | Direct dual norm | Eliminated-coordinate resultant | Boundary |
| --- | ---: | ---: | --- |
| AND gates | 186,824 | 541,388 | Same six source slots and public target |
| Variables | 214,101 | 606,936 | Resultant removes 41 primary bits but expands auxiliary logic |
| Clauses / XOR rows | 561,815 / 27,153 | 1,625,466 / 65,465 | All rows checked on the archived witness |
| Formula bytes | 17,505,806 | 44,808,390 | Resultant is 2.560 times larger |
| Build | 6.795 s parent wall | 9.848 s parent wall; 5.605 s circuit phase | Resultant build monitor degraded, so its sampled combined-RSS field is unavailable; child self peak was 477,200,384 B |
| Ordinary query | `BOUNDED_UNKNOWN` at 190.056 s, 601 restart lines | `BOUNDED_UNKNOWN` at 130.059 s, 17 restart lines | Different caps; neither row supports a solve-time ratio |

The resultant query used CryptoMiniSat 5.14.7, one thread,
`--maxnummatrices=0`, a 120 s solver setting, 130 s parent wall cap, and a
4 GiB combined RSS cap. It parsed the full XCNF and entered search. The
parent sent SIGTERM at the cap; sampled combined peak was 522,354,688 B
with a healthy query monitor. No terminal SAT status appears in the raw log.
All wall measurements are ordinary-host stage diagnostics.

[verification.json](verification.json) records the integrity checks; run
`python3 verify.py` to recheck hashes, parse/search status, field witness,
Lean output, and the comparison. [PROOF_MAP.md](PROOF_MAP.md) gives the exact
scope of the checked algebra and remaining bridges.

## Decision

Direct quadratic elimination increases circuit cost enough to move the next
test to compact partial-sum representations. A useful next falsifier is a
frozen N41 measurement of whether target-conditioned partial sums admit an
exact index or decision diagram materially smaller than the explicit
three-pair table, while retaining every source-code and root witness. Measure
construction, memory, exact lookup yield, and the same public-point replay;
then test its scaling law before any N131 allocation.
