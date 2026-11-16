# Random relations versus a special auxiliary curve

Status: implementation/comparison specification, not a frozen benchmark.
No fresh target panel, timing result or speedup is established here.
The implementation baseline is PR source `8abb2b14`; there is no qualified
Rust timing baseline to ratchet. Final curve/workload/candidate identifiers
and measured costs remain unset until the existing admission rules are met.
[pcc:unverified]

## Three required IC arms

| Arm | Factor base | Relation decomposition |
| --- | --- | --- |
| A: special auxiliary | Complete auxiliary-map fiber lifted onto the target curve | Low-degree resultant circuit and checked signed sums |
| B: same-base direct | Exactly A's signed columns | Optimized batched direct subtraction, no maps |
| C: ordinary random | Independently sampled random subgroup points, exactly A's usable signed-column count | The same optimized direct subtraction as B |

A versus C is the requested special-versus-random IC comparison. A versus B
isolates the maps' contribution. B is not a random-base control. Power and
torus encodings, if included, get separate named arms and the same controls;
they are not relabeled as auxiliary elliptic curves. Rho remains an optional
additional reference and does not replace the IC comparisons.

Support both requested fields, `p=2^31-1` and `p=2^61-1`, with the same target
curve, prime subgroup, generator and target for every arm in a paired row.
An admitted 31-bit panel can proceed independently; a missing eligible
61-bit panel is not a reason to omit an otherwise admissible 31-bit run.
The existing archived public parameters can define the curve choices, but
their known-answer targets are correctness fixtures rather than fresh
benchmark targets. For example, the archived 61-bit subgroup has cofactor
14,627,932; random preparation must clear it, not attempt millions of
subgroup-rejection trials per point.

All three bases must pass the solver's target-subgroup validation before a
paired row is admitted. A split auxiliary fiber alone does not establish
usable subgroup columns. Random-base preparation at 61 bits is tested here;
an eligible complete three-arm 61-bit benchmark panel is still unestablished.
Do not cofactor-clear the special base and assume its old membership maps
still describe the resulting coordinates. If a proposed special base fails,
retain that refusal and qualify a valid base/target combination before freeze.

## Base and target law

Match the actual `folded_columns` K and affine point count. Raw fiber size
is not the random-base size. Record raw membership roots, rejected lifts,
clearing to the identity, duplicate columns and every random draw separately.
The random constructor receives curve, subgroup and generator, never Q or a
target logarithm. It samples field coordinates with rejection before modular
reduction, lifts, clears the Hasse-certified cofactor and folds point negation.
It refuses uncertified/non-coprime cofactors and unattainable K. It does not
generate points by selecting known multiples of the generator.

Freeze all base seeds, actual point sets, auxiliary maps and search limits
before fresh targets are generated. Use multiple independently prescribed
base seeds, not the best seed after inspection. Archive the actual bases under
the repository factor-base rules before publishing measurements. Keep the
base seed separate from the public relation-search seed. Retain every
preparation failure, empty/invalid base, timeout and exhausted search.

## Two distinct comparisons

For relation yield, run `--relation-yield-only` in all three arms with the
same public `--seed`, `--walk-lanes`, positive `--max-queries` and limits. Their target
walks depend on the public curve/G/Q and those sampler parameters, not the
factor base. Recovery and graph elimination are disabled in this mode, so an
early solution does not shorten one arm's query prefix. Include failed and
infinity queries in the denominator. Record distinct valid nonzero signed
rows, duplicate rows and total processed/generated targets. Report both
distinct-row yield and hit count (`relations + duplicate_rows`). Do not
compare yield on unequal processed prefixes or silently discard capped rows;
only `complete`/`QueryBudget` rows completed the requested panel.

The CLI now includes `factor_base.columns_blake3`: a domain-separated hash
of the field, curve coefficients, subgroup order, usable-column count and
ordered canonical `(x,y)` representatives (u64 little-endian). It excludes
the target, encoding and sampler seed, so A and B can share an identity while
using different decomposition methods. This is a reported identity, not a
signed execution attestation or a substitute for archiving the actual base.

Align three existing scalar yield reports with:

```sh
python3 experiments/prime-field-auxiliary-ic/random-vs-special/compare_reports.py \
  --auxiliary auxiliary.json --same-base same-base.json --random random.json \
  --output comparison.json
```

The helper launches no searches. It checks public inputs, source labels,
binary identity, actual-column identity for A/B, usable sizes, sampler/limits,
scalar arithmetic, unused-lane accounting and random preparation counters.
It retains incomplete arms and input hashes while refusing derived comparisons
for unmatched/censored prefixes, replay/full-solve modes, malformed counters,
duplicate JSON keys and nonfinite constants. A random draw that legitimately
produces the same base is flagged and retained. Only aligned fixed prefixes
get exact row/hit fractions, with every processed query in the denominator.
All outputs remain unsigned producer data; matching labels/hashes do not prove
execution. No time ratio or qualified speedup is inferred. Native SIMD and
full-solve cost comparisons require their own scopes and remain outstanding.
[pcc:unverified]

For end-to-end cost, remove `--relation-yield-only` and run full collection,
graph recovery and public certificate replay on the same fresh Q. Record
queries and work until a checked recovery or explicit resource exhaustion.
Relation-yield-only timings exclude recovery and cannot establish an
end-to-end advantage. Match scalar field arithmetic first; report an additional
native SIMD comparison separately with its selected backend recorded.

Commands below are templates; K and other parameters must come from the
frozen panel. They are not an authorization to bypass measurement gates.

```sh
# Shared suffix: --backend scalar --seed QUERY_SEED --walk-lanes LANES
#                --max-queries QUERIES --max-relations ROW_CAP
#                --profile-phases
# A
ca-ic auxiliary --input frozen-special.json --relation-yield-only
# B
ca-ic auxiliary --input frozen-special.json --without-auxiliary --relation-yield-only
# C; only public curve/G/Q parameters are needed in this input
ca-ic auxiliary --input frozen-public.json --random-base-columns K \
  --factor-base-seed BASE_SEED --random-base-max-draws DRAW_CAP --relation-yield-only
```

## Accounting and outstanding admission

`--profile-phases` now instruments the core target-dependent interval in
all three arms, without changing their sampler or row order. Integer
nanosecond intervals partition initialization, target walking, decomposition,
new-row coefficient validation, graph recovery, local certificate replay and
bookkeeping. Initialization includes target validation and jump/lane setup.
Decomposition includes candidate evaluation/subtraction and signed-sum checks;
row validation checks the distinct retained row's `aG+bQ` equation. Graph
recovery includes row storage and dependency expansion. The remaining
bookkeeping interval charges deduplication, counters, limits and cleanup.
Clock overhead stays charged. A profiled report uses the exact core total
for `online_wall_seconds` and retains the enclosing call duration separately
as `online_call_wall_seconds`; an unprofiled report retains its old caller
interval and a null partition. Profiling must match across arms. The offline
alignment helper checks phase types, exact sums and scope, and rejects any
graph/replay time in yield-only mode. It still derives no time ratio.
These are producer instrumentation assertions, not signed timing evidence.
[pcc:unverified]

Profiled timings describe the instrumented implementation. Include matched
uninstrumented controls to expose instrumentation effects; never subtract an
estimated overhead or combine unprofiled totals with phases from another run.

Cold totals charge auxiliary-curve discovery, point counting/order evidence,
smooth-kernel search, isogeny-map construction, fiber enumeration/lifting,
random-base sampling/clearing/deduplication, circuit preparation, target walks,
decomposition, row checks, graph recovery and final replay. Existing CLI
preparation counters start at input loading; they do not account for earlier
auxiliary discovery. The core partition excludes all upstream preparation and
any independent verifier. The launcher must retain those additional phases and
prevent overlap or double charging. Warm totals report excluded preparation,
reuse count and amortization separately. All reported comparisons keep the
same denominator, workload and successful-recovery requirement.

Before a research timing run: successful checkpoint upload; admitted GPU/host
allocation under the standing protocol; immutable candidate/base/target panel;
isolation, A/A and positive controls; benchmark record/raw-data custody;
exclusive phase accounting; independent signed replay. These remain open in
[the qualification problem](../../../problems/prime-field-auxiliary-ic-validation.md).
No timing run is launched by adding these controls. Correctness tests are
development controls, not performance measurements or independent verdicts.
