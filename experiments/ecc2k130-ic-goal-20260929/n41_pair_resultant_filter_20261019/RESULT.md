# Exact target-conditioned two-pair filter for fixed-seed binary curves

A branch-free scalar equation now decides whether either root of each of two
fixed-seed pair quadratics satisfies the reciprocal three-point summation
equation for a specified residual x-coordinate. The equation is the product
of the four root-choice S3 checks, proved in Lean without exceptional
root-dependent division. On the complete 39,335-pair usable W11 code-pair
catalog for a frozen N41 public-relation residual, it accepted exactly
`(425,527)`, the same pair found by independent curve-group enumeration.
The same equation accepts an audited, Frobenius-rotated N131 constructed
control.

## Algorithm and proof

For characteristic-two field elements, write each pair-output reciprocal
root as `z` or `w`. The fixed-seed pair equation is

`C z² + p z + H = 0`, with `C = 1 + H`, `p = w_a w_b`.

When `C` is invertible, put `α=p/C`, `γ=q/C`, and `β=H/C` for two source
codes. Their root equations are `z²+αz+β=0` and `w²+γw+β=0`. For the
target residual reciprocal `t`, the binary-curve reciprocal S3 equation is

`F(z,w,t) = (zwt)² + zwt + (z+w+t)² = 0`.

Reduce `F` modulo both pair quadratics. The result is `Azw+Bz+Dw+E`, where

```
A = t²αγ+t              B = α(1+t²β)
D = γ(1+t²β)            E = t²(β²+1)
U = B²+γBA+βA²          V = γ(BD+EA)
W = E²+γED+βD²          L1 = Uα+V
L0 = Uβ+W               R = L0²+αL0L1+βL1².
```

For fixed `z`, put `M=Az+D` and `N=Bz+E`. Multiplying `Mw+N` over the two
roots `w,w+γ` gives `N²+γNM+βM² = Uz²+Vz+W = L0+L1z`.
Multiplying this over `z,z+α` gives `R`. Therefore

`R = F(z,w,t)F(z,w+γ,t)F(z+α,w,t)F(z+α,w+γ,t)`.

This identity handles `M=0` directly. It gives a necessary and sufficient
x-coordinate test for the four split-root choices; signed source points and
the full group sum are replayed separately.

[PairResultant.lean](PairResultant.lean), pinned to Lean 4.34.1, contains:

| Result | Lean declaration | Hypotheses and checked scope |
| --- | --- | --- |
| Reciprocal S3 reduction | `f3_eq_bilinear` | Characteristic-two field; two normalized quadratic roots |
| Exact four-root product | `resultant_eq_four_f3` | Same field and split roots; includes repeated-root cases |
| Exact zero criterion | `resultant_zero_iff_four_f3` | Same hypotheses; disjunction of the four S3 checks |
| Original pair form | `normalize_pair_root`, `fixed_seed_pair_resultant_zero` | Common nonzero `C` supplied by `C*Cinv=1`; original pair-root equations |

`lean PairResultant.lean` built the actual module. `#print axioms` reported
only `propext`, `Classical.choice`, and `Quot.sound` for the displayed
theorems. `lean4checker --fresh` was unavailable on this host. The Lean
result covers the algebraic filter; the derivation of the pair quadratic
and reciprocal S3 from the specific elliptic-curve group law is checked by
the independent Sage group replays and remains a separate formal bridge.

Resultants are already standard in summation-polynomial methods, and SAT
symmetry breaking for binary PDP also has prior work
([Semaev's algorithm](https://arxiv.org/abs/1504.01175),
[binary SAT study](https://pmc.ncbi.nlm.nih.gov/articles/PMC7334981/)).
This experiment evaluates the specialized fixed-seed, target-conditioned
two-pair elimination within the present ECC2K pipeline; it does not assign
literature-level novelty to the resultant operation itself.

## Exhaustive N41 control

The [frozen protocol](protocol.json) fixes
`EC1N41Ckb1h7d5e80d3c4d0` over `GF(2)[u]/(u^41+u³+1)`, curve
`y²+xy=x³+1`, public raw point `(1936680952394,910597499030)`, 281
source-valid W11 codes, and all 39,335 code pairs with four distinct
folded columns. The residual
`(58884997003,2017134506522)` is the public point minus the first three
pair outputs of the independently audited ordinary five-pair relation in
the [all-aligned experiment](../n41_n131_all_aligned_20261019/RESULT.md).
Thus `(425,527)` is a correctness control for this target-conditioned
two-pair query.

The checked Sage launcher and its [runtime receipt](sage_runtime_info.json)
preceded measurement. [run_sage.py](run_sage.py) prebuilt all four signed
pair states per code, evaluated `R` once per code pair, then independently
tested all 16 signed curve sums per pair. The [result](result.json) is:

| Exhaustive N41 stage | Result |
| --- | ---: |
| Distinct-column code pairs | 39,335 |
| Accepted by `R` / accepted by coordinate sums | `(425,527)` / `(425,527)` |
| Exact raw group-sum match | `(425,527)` |
| Filter wall / 16-sum enumeration wall | 0.202 s / 5.818 s |
| Setup and residual wall / total wall | 0.310 s / 6.339 s |
| Sampled self peak RSS | 266,600,448 B |

The 28.8× ratio compares this field filter with exhaustive signed group
enumeration on an ordinary host. A stronger field-only comparator is four
direct S3 evaluations using precomputed roots. In the frozen ABBA
[comparison](field_compare_result.json), both methods accepted the same one
pair in every run; median wall was **0.167 s for `R` and 0.159 s for the
four-root comparator**. These short, ordinary-host stage timings do not
select an end-to-end IC candidate.

The first field-comparison attempt stopped on a tuple-versus-JSON-list
assertion after calculation and before writing a result. Its
[failure receipt](field_compare_first_attempt_failure.json) and frozen
[v1 protocol](field_compare_protocol_v1.json) remain beside the corrected
[protocol](field_compare_protocol.json).

## Independent replay and N131 bridge

[audit_sage.py](audit_sage.py) multiplied the four S3 values independently
for every N41 code pair and compared the **full field value** with the
closed formula. All 39,335 values matched; the ordered value digest is
`56152d778d466050b78dfe2b6497a5921880c9c06d9452187f8e3113b5c01296`.
The [v2 audit](audit_result.json) also transported the two N131 right-pair
quadratics through Frobenius rotation 36 and checked that their resultant
vanishes for the constructed target residual
`(2403901758133154277611562267680540841657,
775431192514838725578231655052027417434)` on
`EC1N131Ckb1heb5f1998f20b`. The first passed audit is retained as a
versioned [receipt](audit_result_v1.json). The
[terminal audit](terminal_audit.json) binds source, proof, and output hashes.

The next decisive experiment is a Boolean circuit variant for the frozen
N131 public point: replace the right two pair-output root witnesses and
their S3 link with `R=0`, keeping exact source validity, distinct folded
columns, target coupling, and independent full group replay. Measure circuit
size, constructed assignment, ordinary-query status under the same
one-worker 600-second cap, and paired same-point controls before selecting
an IC candidate. `candidate_id` is `null` while relation collection,
factor-base logs, target descent, and the final rho comparison remain open.
