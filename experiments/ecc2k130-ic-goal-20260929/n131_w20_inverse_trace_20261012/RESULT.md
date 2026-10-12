# Compact exact W20 source gates for the N131 seven-pair circuit

Replacing the W20 source BDDs and generic IR backend with inverse-trace
witnesses and a sparse Karatsuba circuit reduces the frozen ordinary-target
formula from 1,354,163 to **167,935 variables** and from 46,355,807 to
**10,390,466 XCNF bytes**. The constructed seven-pair assignment satisfies
every one of 352,337 clauses and 48,141 native XOR rows. On the same public
point and 615-second parent cap, the compact formula processed 3.251 million
logged conflicts, compared with 71,000 for the earlier W20 BDD/IR formula.
This is a formula and search-progress result on an exploratory host; the
public search ended `BOUNDED_UNKNOWN` at its cap.

The exact curve is `EC1N131Ckb1heb5f1998f20b` over
`GF(2)[t]/(t^131+t^13+t²+t+1)`, with `y²+xy=x³+1` and prime subgroup order
`680564733841876926932320129493409985129`. The source is the span of
`t` through `t²⁰`, with fixed pair seed 898618 and seven Frobenius rotations
`0,18,36,54,72,90,108`. The source census fixes 132,045 valid unordered
pairs per slot, 3,697,260 actual usable base points across the seven
windows before folding, and 263,959 folded columns. The labeled
uniform-target support ceiling is 16.8501676 before cross-slot exclusions;
it is a combinatorial ceiling, not measured relation yield. The one-point
workload is `cc09e7eb202a`, raw preimage index zero, frozen in
[protocol.json](protocol.json) and [solver_protocol.json](solver_protocol.json).

For each nonzero source endpoint `x`, the gate introduces `v` with `xv=1`
and `Tr(v)=0`. Dividing the curve equation by `x²` shows that a rational
point above `x` exists exactly when `Tr(x+x⁻²)=0`; the absolute trace is
invariant under squaring. The [freeze audit](protocol.json) checks zero trace
on all 20 source-basis vectors, so the gate is equivalent to source
rationality on this span. It recomputes the 132,045 canonical accepted pairs
from the frozen [support table](../n131_w20_sevenpair_gate_20261010/support_w20.tsv),
whose earlier native census checked every nonzero W20 mask and whose BDD
audit checked all 524,288 canonical selectors. The prior checked-Sage
[group audit](../n131_w20_sevenpair_gate_20261010/sage_audit_result.json)
verifies the selected seven-pair relation. This experiment additionally
checks inverse and trace identities on its 14 selected endpoints and all
clauses/XOR rows of their [constructed assignment](control_result.json).
The [proof map](PROOF_MAP.md) ties the gate replacement to a checked Lean
seven-slot theorem and records the remaining concrete-field bridge.

| Frozen ordinary formula | W20 BDD/IR | W20 inverse-trace/Karatsuba | Ratio |
| --- | ---: | ---: | ---: |
| Variables | 1,354,163 | 167,935 | 8.06× smaller |
| CNF clauses | 1,250,440 | 352,337 | 3.55× smaller |
| Native XOR rows | 936,218 | 48,134 | 19.45× smaller |
| XCNF bytes | 46,355,807 | 10,390,466 | 4.46× smaller |

The comparison changes the source gate, field-circuit backend, and reciprocal
coordinate representation together. These counts measure the resulting
complete formula, so they do not isolate the contribution of each change.
The earlier [ordinary build receipt](../n131_w20_sevenpair_gate_20261010/sevenpair_ordinary_build.json)
and the new [ordinary build receipt](ordinary_build_result.json) retain exact
formula hashes. The source and solver binaries are hash-bound by the two
protocols. The generated XCNFs, stdout, and stderr are retained in this
directory.

| Frozen public-target stage | W20 BDD/IR | W20 inverse-trace/Karatsuba |
| --- | ---: | ---: |
| Solver flags | `--threads=1 --maxtime=600` | Same |
| Parent/RSS cap | 615 s / 4 GiB | Same |
| Parent stop | `PARENT_TIMEOUT` | `PARENT_TIMEOUT` |
| Search wall | 615.117 s | 615.097 s |
| Last logged conflicts | 71,000 | 3,251,000 |
| Sampled peak child RSS | 527,745,024 B | 665,632,768 B |
| Sampled child CPU | Unrecorded | 341.274 s |
| Terminal status | `BOUNDED_UNKNOWN` | `BOUNDED_UNKNOWN` |

The new [solver receipt](solver_result.json) and [raw log](solver.stdout.txt)
retain the failed bounded attempt. The 18.724-second formula construction
and 0.010-second serialization were measured in a separate process before
the solver run, so the table reports stage costs rather than a combined
single-target online interval. Host-level CPU isolation was unavailable;
the conflict count is a diagnostic and does not establish an isolated
wall-time speedup. Candidate ID remains `null` while natural verified
relation yield, rank novelty, factor-log recovery, target descent, and
same-point rho accounting are unresolved.

The next focused experiment is to linearize each pair-output equation using
an inverse output witness. For standard reciprocal output `a`, the current
equation is `a P(s)+(1+h²)a²+h²=0`; introducing `b` with `ab=1` makes the
source-product condition `P(s)=(1+h²)a+h²b` linear in the 19 selector bits,
`a`, and `b`. A constructed-assignment audit followed by a frozen, paired
public-target cap can test whether the added inverse multiplication is paid
back by stronger XOR propagation. The N41 complete IC pipeline remains the
end-to-end control while this N131 point-decomposition gate is developed.
