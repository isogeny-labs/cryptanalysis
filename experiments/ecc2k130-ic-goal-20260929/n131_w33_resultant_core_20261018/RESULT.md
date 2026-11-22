# Fixed-first-code N131 resultant solved by Boolean Gröbner reduction

Fixing one 32-bit source code turns the N131 13-term two-pair resultant
into 131 quadratic Boolean equations in the other 32 code bits. A direct
PolyBoRi Gröbner reduction recovered the known second code `16722` from
first code `3` in 12.626 seconds of Gröbner time, 33.976 seconds including
the checked Sage launch and equation construction. Independent Sage
replay verified the two source pairs and their sum against the frozen
constructed point. On the frozen ordinary public point with first code
`3`, the same solver reported the unit ideal in 4.395 seconds of Gröbner
time, 16.986 seconds including launch and construction. This gives an
exact solver for a conditioned pair subproblem and a concrete search
target for eliminating many first-code families together.

## Method and instance

The field is `GF(2)[u]/(u^131+u^13+u^2+u+1)` and the curve is
`y²+xy=x³+1`, `EC1N131Ckb1heb5f1998f20b`. The W33 source has 32 free
code bits after the seed-high-bit convention, product-basis rank 32,
and pair rotations `(0,18)`. The source codes refer to the exact frozen
construction in the [N131 preflight](../n131_w33_freecode_resultant_20261018/RESULT.md).
The method holds the first product `p` fixed. If `q=Σ b_i q_i` is the
second product in its 32-dimensional binary source span, `q²` and `q⁴`
are linear in the bits, while `q³` is quadratic. Expanding the resultant
thus yields 131 field-bit equations of Boolean degree at most two. The
[Lean proof map](PROOF_MAP.md) gives the checked square and cube identities.

The algebraic solve deliberately delays source-point validity checks.
For its recovered positive code, independent Sage replay checks the
source traces, reciprocal traces, lifted curve points, Frobenius
rotations, branch choices, and exact group sum. The recovered source
masks are `(3,898617)` and `(16722,915304)`; the matching branches are
`(0,0)` and `(1,0)`.

## Frozen measurements

| Probe | Result | Wall interval | Sampled peak combined RSS |
| --- | --- | ---: | ---: |
| Free-code resultant-only XCNF, constructed positive | `BOUNDED_UNKNOWN`, wall cap | 300.048 s | 61,620,224 B |
| Same XCNF, first code 3 pinned | `BOUNDED_UNKNOWN`, wall cap | 120.091 s | 38,240,256 B |
| Quadratic Gröbner, first code 3, constructed positive | code `16722`; 32 linear basis polynomials | 33.976 s total; 12.626 s Gröbner | 360,759,296 B |
| Independent Sage curve replay | exact positive group sum | separate correctness run | recorded by checked launcher |
| Quadratic Gröbner, first code 3, frozen ordinary point | unit ideal reported | 16.986 s total; 4.395 s Gröbner | 343,293,952 B |

The relaxed positive XCNF has 6,841 AND gates, 11,868 variables,
20,655 CNF clauses, and 4,963 native XOR rows. Its known assignment
passes every clause and XOR row. Both SAT runs used one CryptoMiniSat
worker and a 4 GiB RSS cap. The algebraic runs used one checked Sage
process and a 4 GiB RSS cap. The wall intervals in this table include
process startup for the algebraic probes and are stage diagnostics on an
ordinary host. The public unit-ideal result applies only to first code
`3`; the returned basis itself was not saved as a separately checkable
certificate. The result record therefore retains `candidate_id: null`.

## Next gate

The fixed-first-code solver changes a 120-second capped SAT search into
an independently replayed 34-second solve, but applying it separately
to `2^32` first codes cannot meet the 600-second ordinary-point gate.
The next algorithmic step is to eliminate *blocks* of first codes at
once: derive a target-conditioned necessary constraint from the
quadratic second-code system, prove that it preserves all genuine
solutions, and measure how many first-code families it rejects before
any per-code Gröbner call. Use an unpinned N41 control to audit the
rejection and witness-preservation logic before an N131 promotion.

`python3 verify.py` checks source and protocol hashes, formula and solver
receipts, the independent replay, and the final Lean proof log. The
initial system-`python3` wrapper invocation failed before launching a
solver because that interpreter lacked `psutil`; its producer-failure
record is retained in `wrapper_attempt0.json`. The checked Sage runner
then completed the measured algebraic probes. The
following commands generate the algebraic and replay results under the
checked launcher in a fresh copy of this directory with protocols
rehashed for that copy:

```sh
/Volumes/SSD990/cryptanalysis/sage -python quadratic_solver.py
/Volumes/SSD990/cryptanalysis/sage -python quadratic_public.py
/Volumes/SSD990/cryptanalysis/sage -python replay_sage.py
lean QuadraticSourceExpansion.lean
```
