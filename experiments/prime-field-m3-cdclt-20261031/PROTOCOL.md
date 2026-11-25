# Draft protocol: prime-field arity-three CDCL(T) exponent screen

**Freeze status:** draft. No affected data collection is authorized. This
version incorporates the prospective 2026-11-01 hardening amendment before
any held-out instance or scientific row exists.

## Question and cost gates

At fixed arity `m=3`, does a source-bound CaDiCaL/`F_p` CDCL(T) bundle solve
the complete natural point-decomposition panel with online work
`Q(s)=2^(e s)` and reusable setup `S(s)=2^(a s)`, where the fitted scale is
the recorded `log2(p)/3`?

For `Theta(2^s)` relation queries, complete collection work is

```text
S(s) + 2^s Q(s) = 2^(a s) + 2^((e+1)s)
```

up to polynomial factors. The arity-three PDP route advances only when both
corrected upper 95% intervals satisfy

```text
e < 0.5  and  a < 1.5.
```

The response is never divided by candidate-space size. The cold one-target
count `S(s)+Q(s)` remains primary and is measured in a fresh process. Setup
and online counts are stage counters within that same interval; calling setup
reusable does not establish reuse. A later multi-target experiment must prove
which state is target-independent and charge `S(s)` once for its frozen target
count.

## Fixed semantic predicate

Each instance uses a nonsingular elliptic curve over `F_p` with known odd
prime whole-group order, a finite rational non-2-torsion target, and three
disjoint windows of **abscissa candidates**. A projected summand is
`(window index, x, rational-lift sign)`, not an already-signed point and not an
unqualified `x` word.

The canonical IR and every exporter must bind:

- exactly one abscissa selector per window;
- disjoint abscissa domains;
- recovered rational-lift signs and the exact target sign;
- unsigned field/index range predicates;
- two chained `S3` relations through an intermediate point;
- the nonzero-displacement lambda chart and an explicit `t=0` branch;
- final curve membership and exact signed group replay.

The chained `S3` equations are sign-blind by themselves. A backend that finds
compatible abscissae but cannot bind the recovered signs to the projected
relation has not implemented the semantic predicate. Independent replay is a
checker, not a repair for an underconstrained encoding.

The nonexceptional lift equation is

```text
(2 t lambda - s0)^2 = f(x),
```

and its discriminant as a quadratic in `lambda` is

```text
(-4 t s0)^2 - 4(4 t^2)(s0^2-f(x)) = 16 t^2 f(x).
```

For `t != 0`, rational `lambda` exists exactly when `x` has a rational curve
lift. The generator represents `t=0` as an explicit exceptional branch and
never divides it away.

Under the odd-prime-order, rational non-2-torsion target and disjoint-abscissa
guards, Frobenius negates every quadratic-twist lift. One nonrational summand
cannot make the total rational; two would sum to rational 2-torsion and hence
zero, repeating an abscissa; three would make the target 2-torsion. Therefore
every accepted arity-three model has rational lifts without a separate
per-summand rationality circuit. At arity four or higher, retain and charge
explicit rationality circuits.

## Frozen Boolean and range encodings

For the initial `s=6..14` CDCL(T) screen, exactly-one is the Sinz sequential
at-most-one encoding plus one at-least-one clause. A window of size `n>=2`
has `n-1` auxiliary variables and `3n-3` clauses. The native development
oracle exhaustively checks this construction through `n=8`.

Field and index membership is one semantic predicate `0 <= word < domain`.
Exporters use an unsigned comparator or native theory-domain check. They may
emit one clause per forbidden word only when a frozen preflight cap explicitly
admits the complete list; no result may hide an exponential `2^k-domain`
enumeration.

Pure CNF is an encoding-cost control. Its frozen multiplier implementation,
gate basis and modular-reduction circuit must be named before freeze. A
schoolbook multiplier may have `Theta((log p)^2)` gates by construction, but
that is not a lower bound for general Boolean multiplication. Report actual
gate, variable, clause and byte counts.

## Solver routes and certificate eligibility

### `cdcl-t-fp` — decision candidate

CaDiCaL owns the Boolean skeleton. An external `F_p` theory propagator owns
field arithmetic, inversion guards, the chained group-law constraints,
sign binding and exceptional-chart consistency. Every theory propagation or
conflict returns a Boolean explanation clause that an independent checker
replays. An UNSAT row additionally requires a proof log whose Boolean steps
and admitted theory lemmas both replay.

The API shell may be ported from source-bound binary-field Q1421, but the
prime-field implementation receives its own source identity and compile
receipt. Every theory call, field operation, explanation literal, proof step
and replay failure is counted.

### `qf-ff` — diagnostic until a checked proof route exists

Export the identical canonical predicate to a pinned cvc5 `QF_FF` build and
verify every SAT model by independent signed group replay. Inspected cvc5
source head `02f77af402b4be82f27e5cc00b86b265a90dea3d` returns no finite-field
proof checker. Consequently this route is not advance-eligible for an UNSAT-
containing complete panel. Before freeze it must either:

1. bind a newer source and independently replayed finite-field UNSAT proof;
2. bind an external certificate checked independently; or
3. remain a SAT/model diagnostic outside the slope decision family.

An unproved `unsat` response is recorded as `unknown` and makes the complete
panel inconclusive; it is never silently dropped.

### `cnf-cost`, `f4-base`, and `enum-ref`

- `cnf-cost` records the complete selected bit-blast size and proof log; it is
  not a theorem-bearing solver candidate.
- `f4-base` receives the identical polynomial IR and is an algebraic reference.
- `enum-ref` is the exact two-window scan, projected-model oracle where it
  completes, and the `e=2` cost reference.

## Ladder, representation admission, and controls

The initial ladder contains every integer rung `s=6..14`; the regression
coordinate is the actual recorded `log2(p)/3`. At each rung generate eight
independent instances in each class: natural, planted and exact UNSAT, for 216
semantic instances before solver arms. Generation finishes before arm labels
are assigned, with seeds derived from the frozen protocol hash.

The selected one-hot encoding has these exact structural sizes at `s=27`:

```text
402,653,184 selector variables
402,653,181 Sinz auxiliary variables
805,306,365 total Boolean variables before theory auxiliaries
1,207,959,543 exactly-one clauses
```

Therefore `s=15..27` is not an automatic continuation of the initial one-hot
bundle. A prospective amendment must freeze either a measured resource budget
that admits the exact representation or a new compact/lazy multi-valued
selector with fresh model-set equivalence, A/A, setup-exponent and memory
preflights. The current bundle cannot be described as a path to `s=27` until
that admission gate passes.

Controls on the same canonical IR are:

| Arm | Role |
| --- | --- |
| `enum-ref` | exact two-window projected-model oracle and `e=2` reference |
| `f4-base` | algebraic baseline |
| `cdcl-t-fp` | primary hybrid candidate |
| `qf-ff` | SAT/model diagnostic unless proof capability is established before freeze |
| `cnf-cost` | selected pure-CNF encoding-cost control |
| `cdcl-t-aa` | byte-identical fresh-process A/A arm |
| `planted-positive` | witness, sign-binding and explanation positive control |
| `matched-null` | curve-free sparse system matched on field, variables, degrees, support incidence, encoding and exact small-cell model count |

Mutation controls alter one field coefficient, admit one out-of-range word,
make two windows share an abscissa, corrupt one sign/root, corrupt one theory
explanation and corrupt one UNSAT proof step. The canonical evaluator and
certificate checkers must reject all six.

## Complete accounting

Each fresh process records these non-overlapping stages:

1. **cold setup:** process start through target-independent IR construction,
   parsing, solver initialization and preprocessing;
2. **online query:** first target-dependent instruction through backend exit;
3. **certificate and replay:** model/proof extraction, explanation checking,
   proof replay and independent signed group-law verification.

Primary counted metrics are complete cold instructions, setup instructions,
online-plus-verification instructions and peak RSS over the whole cold
interval. Also retain theory field-operation vectors, CDCL decisions/conflicts/
propagations/restarts/learned bytes and per-stage bytes. No stage may overlap or
fall outside the cold total.

The online exponent `e` is fit only from natural instances. The setup exponent
`a` is fit from the target-independent stage once per generated predicate. The
planted and exact-UNSAT classes are correctness/control strata with separately
reported descriptive slopes; they are never pooled into `e`.

## Inference and decision rules

The primary Theil--Sen regressions use actual `log2(p)/3`. Bootstrap resampling
units, one-sided interval construction and any multiplicity family are fixed in
the analysis source before freeze. If only `cdcl-t-fp` is eligible, there is
one slope candidate and no artificial two-arm Holm correction. A future
proof-capable QF_FF candidate adds a prospective Holm family before data.

**Advance:** every preregistered natural row at every rung completes with a
verified exact status; every planted and exact-UNSAT control completes and
verifies; the frozen power condition holds; the corrected upper intervals
satisfy `e<0.5` and `a<1.5`; both conclusions lie outside A/A spread; and cold,
setup, online, theory and verification ledgers reconcile.

**Do not advance:** the complete verified panel and power condition are valid
and either corrected lower interval has `e>=0.5` or `a>=1.5`.

**Inconclusive:** anything else, including any natural timeout, OOM, `unknown`,
unproved UNSAT, incomplete rung, favorable-subset completion, failed positive
control, explanation/proof rejection, insufficient power, or a conclusion
that appears only after omitting setup, theory or verification work.

No imputation or completed-row subset can satisfy the advance gate. Censored
rows remain in the export as outcomes and may support a separate conservative
lower-bound analysis fixed before data, but not this decision statistic.

## Freeze blockers

- source-bound canonical generator and typed IR beyond the landed development fixture;
- prime-field external propagator and independent explanation/proof checker;
- pinned CaDiCaL, F4 and CNF-control builds; QF_FF certificate eligibility decision;
- exact setup/online/cold instrumentation and stage reconciliation;
- analysis source, bootstrap/multiplicity implementation and power calculation;
- runtime and memory preflight fixing the exactly enumerable prefix and continuation ceiling;
- immutable held-out manifest and protocol hash.

Until every item is present and this protocol is frozen in a reviewed commit,
only implementation and disclosed development-fixture validation are allowed.
