# Direct shared-root quartic gate for the N41 public point

## Contribution

The exact last-two-pair target condition is now encoded as two direct quartic
evaluations `f(w)=g(w)=0` on one free field witness. The circuit preserved the
archived five-pair relation, rejected all 32 frozen reachable controls, and
reduced the Boolean formula to **129,751 variables and 358,169 constraints**.
Against the prior structured Bezout root formula, a frozen one-worker
fixed-conflict comparison used **26.9% as many decisions** and **47.9–66.2% of
the paired wall time**. It passed the predeclared promotion gate, which
authorized the separately frozen 600-second ordinary N41 query.

## Method and proof

The field is `GF(2)[u]/(u^41+u^3+1)` and the curve is `y²+xy=x³+1`, curve ID
`EC1N41Ckb1h7d5e80d3c4d0`, subgroup order `549756390943`. The public point
is `Q=(1936680952394,910597499030)`. The five aligned W9 pair rotations are
`(0,0,12,12,24)`, with 71 allowed source codes and four signed states per
code. All five eight-bit codes, the preceding 41-bit reciprocal `z`, and the
shared 41-bit reciprocal `w` are free inputs. No archived code, `z` or `w`
bits are pinned. A complete IC pipeline is still `candidate_id: null`.

The first-three-pair F4 norm, source-code restrictions and column-collision
clauses are retained from the preceding circuit. The last two source quartics
are evaluated by four Horner multiply-add steps each. Their conjunction is
exactly the shared-root condition by definition, with no Bezout matrix or
determinant. The [Lean module](DirectRoot.lean) proves the Horner identity and
the two-zero common-root equivalence for arbitrary commutative rings. The
[proof map](PROOF_MAP.md) separates those checked identities from the
finite-audited curve/source bridge.

## Frozen build and paired probe

The [build protocol](build_protocol.json) pins the source, fixture, 33-row
panel, prior root circuit and checked [Sage runtime](sage_runtime_info.json).
The [builder](build.py) checked one satisfying archived assignment and 32
rejecting controls. Its complete measured interval was **32.624 s**,
including panel replay, with **154,435,584 B** self peak RSS under the
300-second/4-GiB envelope. The [read-only verifier](verify.py) checks exact
formula counts, all 33 decisions, source hashes and 122 unpinned input bits.

| Circuit | AND gates | Variables | CNF clauses | Native XOR rows | Total constraints | Bytes |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Structured Bezout root | 122,217 | 140,627 | 368,551 | 18,288 | 386,839 | 12,708,182 |
| Direct two-quartic root | **113,361** | **129,751** | **341,901** | **16,268** | **358,169** | **11,119,913** |

The direct circuit used **7.73% fewer variables**, **7.41% fewer total
constraints**, and **12.50% fewer serialized bytes**. The
[probe protocol](probe_protocol.json) froze serial root/direct/direct/root
order, one CryptoMiniSat worker, 20,000 requested conflicts, 170-second
solver and 180-second parent caps, and 4-GiB sampled combined RSS. All four
arms returned `INDETERMINATE_CONFLICT_CAP` with monitors passing. The
[aggregate receipt](probe_result.json) links every raw solver stream and
per-arm result.

| Arm | Gate | Wall seconds | Conflicts | Decisions | Propagations | Peak sampled combined RSS |
| ---: | --- | ---: | ---: | ---: | ---: | ---: |
| 0 | Structured root | 38.061 | 20,002 | 168,673 | 49M | 116,965,376 B |
| 1 | Direct root | 25.184 | 20,002 | 45,386 | 58M | 70,811,648 B |
| 2 | Direct root | 24.287 | 20,002 | 45,386 | 58M | 71,958,528 B |
| 3 | Structured root | 50.658 | 20,002 | 168,673 | 49M | 95,469,568 B |

The predeclared gate required each direct arm to use at most 80% of adjacent
baseline decisions and no more than 125% of paired baseline wall time.
Decision ratios were **0.269/0.269**; wall ratios were **0.662/0.479**. This
supports the decision to run the ordinary N41 query; fixed-conflict work is a
stage diagnostic and does not measure relation yield.

## Ordinary query

The [query protocol](query_protocol.json) freezes the same public point and
unpinned formula, the exact CryptoMiniSat binary, one worker, a 590-second
solver limit, a 600-second parent wall cap and 4-GiB sampled combined RSS.
A SAT model is independently replayed as five signed source-pair points on
the exact curve using the checked Sage launcher before counting a relation.

The [query receipt](query_result.json) records **`BOUNDED_UNKNOWN`,
`WALL_CAP`** at **600.058 s** parent wall. The last flushed restart line is
restart 727 at approximately 292,000 conflicts. The solver produced no SAT,
UNSAT or INDETERMINATE terminal line; that restart count is search progress,
not a relation-yield observation. The monitor sampled combined RSS 5,806
times, peaking at **173,178,880 B**, with no monitor error. Stderr is empty;
the raw stdout/stderr hashes are in the receipt. The target-dependent build
and bounded query sum to **632.682 s** of charged stage wall. Launcher checks
and process startup are outside these intervals. Independent curve replay is
conditioned on a SAT model and was not invoked for this capped run.

## Next discriminator

The final source-pair quartic has four independently audited field roots for
each of its 71 codes. Freeze an exact branch formulation over those 284
code-root cases, with `w` and the final code fixed per branch, and retain the
same first-three-pair norm and source-column exclusions. A source-preserving
branch census can then measure per-branch formula size and bounded search
under one shared 600-second/4-GiB work envelope. Its comparison must include
all branches examined and the setup cost of constructing the root table.
The direct circuit's fixed-conflict gain does not by itself select a faster
ordinary relation collector. N131 promotion still requires an independently
replayed unpinned N41 relation and a source-bound N131 feasibility gate.
