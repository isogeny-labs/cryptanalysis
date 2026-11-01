# Draft protocol: prime-field arity-three CDCL(T) exponent screen

**Freeze status:** draft. No affected data collection is authorized.

## Question and gate

At fixed arity `m=3`, does either hybrid CaDiCaL/`F_p` CDCL(T) or cvc5
`QF_FF` solve natural point-decomposition predicates with work
`2^(e s)`, where `s=log2(p)/3`, and a Holm-corrected upper 95% interval for
`e` is strictly below `0.5`?

The response is `log2(complete counted work)` fitted directly against `s`.
It is not divided by candidate-space size. A finite fitted slope is evidence
only for the frozen implementation, ladder and workload.

## Fixed predicate

Each instance uses a nonsingular elliptic curve over `F_p` with known odd
prime whole-group order, a rational non-2-torsion target, and three disjoint
one-hot factor-base windows. The Boolean layer owns:

- exactly-one clauses for each window;
- disjoint-window constraints;
- one clause forbidding every field/index word outside its declared domain;
- CDCL decisions, Boolean propagation and learned clauses.

Two chained `S3` relations connect the three selected summands through an
intermediate point. Do not expand an `S4` polynomial. The nonexceptional
lambda chart uses

```text
(2 t lambda - s0)^2 = f(x),
```

whose discriminant as a quadratic in `lambda` is

```text
(-4 t s0)^2 - 4(4 t^2)(s0^2-f(x)) = 16 t^2 f(x).
```

The generator represents `t=0` as an explicit exceptional branch; it never
divides that case away.

Under the stated odd-prime-order, rational-target and disjoint-window guards,
Frobenius negates every quadratic-twist lift. One nonrational summand cannot
make the total rational; two would have to sum to rational 2-torsion and hence
to zero, forcing repeated abscissae; three would make the target 2-torsion.
Thus accepted arity-three models are rational without an extra rationality
circuit. At arity four or higher this argument is not automatic: retain and
charge explicit rationality circuits.

## Solver routes

### `cdcl-t-fp`

CaDiCaL owns the Boolean skeleton. An external `F_p` theory propagator owns
field addition, multiplication, inversion side conditions, the two chained
group-law constraints and exceptional-chart consistency. Every theory
propagation or conflict must return a Boolean explanation clause that an
independent checker replays before accepting the row.

The API architecture may be ported from the source-bound `F_{2^n}` Q1421
loop named in `README.md`, but the prime-field implementation receives a new
source identity and compile receipt. Count every theory call, field operation,
explanation literal and replay failure.

### `qf-ff`

Export the identical canonical predicate to a pinned cvc5 build using
`QF_FF`. Record the binary hash, flags, parser/export cost, backend counters
that exist, model extraction and independent group-law replay.

### `cnf-cost`

Pure CNF is an encoding-cost control only. Boolean quotient relations
`z^2-z` avoid arithmetic carries in `F_p[z]/(z^2-z)`, but a general
prime-field multiplication still requires `Theta(log^2 p)` Boolean gates.
Record gate, variable, clause and byte counts; do not call this arm the
theorem-bearing solver.

## Ladder and controls

The initial ladder contains every integer `s=6..14`. For each `s`, generate
eight independent instances in each of three target classes: natural,
planted and exact UNSAT, for 216 semantic instances before solver arms.
Generation finishes before arm labels are assigned, with seeds derived from
the frozen protocol hash.

Attempt these arms on the same canonical IR:

| Arm | Role |
| --- | --- |
| `enum-ref` | Canonical exact two-window scan, correctness oracle where it completes and `e=2` exponent control |
| `f4-base` | Algebraic baseline on the identical chained predicate |
| `cdcl-t-fp` | Primary hybrid candidate |
| `qf-ff` | Independent finite-field solver candidate |
| `cnf-cost` | Pure-CNF encoding-cost control |
| `cdcl-t-aa` | Byte-identical fresh-process A/A arm |
| `planted-positive` | Witness and explanation-checker positive control |
| `matched-null` | Curve-free sparse system matched on field, variables, degrees, support incidence, one-hot shape and exact small-cell model count |

Mutation controls alter one field coefficient, admit one forbidden word,
make two windows share an abscissa, corrupt one explanation clause and corrupt
one extracted root. The canonical evaluator must reject all five.

## Complete work boundary

Start at the first target-dependent canonical-IR instruction. Stop only after
solver termination, model/proof extraction, theory-explanation replay and
independent elliptic group-law verification. Charge parsing, serialization,
every failed and timed-out attempt, every theory call and field operation,
and all verification. Report reusable target-independent setup separately.

The primary work metric is retired instructions over that complete interval.
Also retain exact theory field-operation vectors, CDCL decisions/conflicts/
propagations/restarts/learned bytes, peak RSS, wall time, and per-stage
instructions. Native CDCL work `W(w)=decisions+conflicts+w*propagations` for
`w in {0,0.1,1}` is a sensitivity diagnostic, never a substitute for theory
or verification cost.

## Decision rules

Use Holm correction across the two candidate solver bundles at family alpha
`0.05`.

- **Advance:** all correctness and control gates pass, the frozen power
  condition is met, and the corrected upper 95% interval for `e` is strictly
  below `0.5` with complete theory and verification work included.
- **Do not advance:** controls and power are valid and the corrected lower
  95% interval for `e` is at least `0.5`.
- **Inconclusive:** anything else, including censoring, insufficient power,
  wrong or unproved answers, explanation-checker failures, favorable-subset
  completion, or a conclusion that exists only after omitting theory work.

The continuation band `s=15..27` is a separate amendment after the initial
screen. It is not silently appended after seeing `s=6..14` results. At roughly
80-bit fields rho costs about `2^40` group operations; this protocol measures
the PDP exponent rather than expecting a wall-clock win.

## Freeze blockers

- canonical prime/curve/window/target generator and typed IR;
- exhaustive small-cell oracle including `t=0` and forbidden words;
- source-bound `F_p` external propagator and independent explanation checker;
- pinned CaDiCaL, cvc5 and F4 builds with hashes and flags;
- analysis code, bootstrap/Holm implementation and a power calculation;
- runtime and memory preflight fixing budgets and the exactly enumerable prefix;
- immutable instance manifest and protocol hash.

Until every item is present and the protocol is frozen in a reviewed commit,
the only authorized work is implementation and development-fixture validation.
