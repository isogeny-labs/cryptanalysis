# Fixed-bit elimination in the two-product cubic solver

**Substituting the fixed first-code bit before ANF construction removes one
Boolean variable, one equation, and 99 ANF monomials, while preserving every
field-coordinate polynomial exactly on the branch.** An alternating
same-input N131 comparison does **not** show a solver-time gain: the
archived implementation with an explicit `x₀=1` equation was faster in both
positive pairs, and the ordinary pairs crossed. This changes the next
algorithmic choice: the cubic form remains an exact component, but fixed-bit
elimination is not a measured acceleration of its Gröbner search.

The [2026-10-19 nonzero-branch result](../resultant_nonzero_branch_20261019/RESULT.md)
already proved and tested the odd-code cubic method on these N131 blocks.
The [2026-10-23 fixed-bit result](../nonzero_branch_cubic_20261023/RESULT.md)
implements **pre-elimination of the fixed bit** and compares that solver to
the original quartic; it should be read as an implementation experiment,
not as the first discovery of the nonzero branch. The current ABBA panel
compares the two cubic implementations directly.

## Exact input and algebraic comparison

Both arms use `EC1N131Ckb1heb5f1998f20b` over
`GF(2)[u]/(u^131+u^13+u²+u+1)` on `y²+xy=x³+1`, the W33 seed mask
`898618`, first product rotation zero and second rotation 18. The first
code is one of `1,3,5,7,9,11,13,15`; all 32 bits of the second code
remain free. The positive target is the archived constructed two-pair sum
with independently replayed codes `(3,16722)`. The ordinary target is the
frozen N131 raw public point
`(877610862732227974378969808549299291499,
2063336771837286479337213121437715536874)`.

The archived arm creates four first-code variables and adds `x₀+1` to its
131 cubic field equations. The pre-eliminated arm substitutes `x₀=1`
before building the field-valued ANF, leaving three first-code variables.
The independent [ANF audit](anf_audit_result.json) rebuilt both systems
with a separate carryless multiplier and compared every coefficient after
substitution on **both** target rows. All coefficients matched: the old
2,314-monomial ANF reduces to the new 2,215-monomial ANF. The structural
zero-set equivalence on this nonzero-product branch is covered by the
checked [Lean proof](../nonzero_branch_cubic_20261023/PROOF_MAP.md); this
experiment's coefficient equality is a finite computational check, not a
new abstract theorem.

## Alternating solver measurements

The [frozen protocol](protocol.json) prescribed `old, new, new, old`
separately for each target before any arm ran. Each arm copied the
hash-pinned source and its original protocol into a fresh directory, used
the checked repository Sage launcher, one process, `degrevlex` PolyBoRi,
a 600 s parent wall cap, and a 4-GiB sampled combined-RSS cap. The parent
interval includes Sage launch, ANF construction, reduction, and wrapper
completion. All eight arms completed below both caps and agreed on their
result: the positive pair `(3,16722)` or a reported unit ideal on the
ordinary block.

| Target | Old 1 | New 1 | New 2 | Old 2 | Old/New ratios in paired order |
| --- | ---: | ---: | ---: | ---: | ---: |
| Constructed positive | 47.07 s | 56.80 s | 66.62 s | 51.40 s | 0.829, 0.772 |
| Frozen public-point block | 63.56 s | 49.22 s | 68.34 s | 50.78 s | 1.291, 0.743 |

Old means are 49.23 s positive and 57.17 s ordinary; new means are
61.71 s and 58.78 s. These are **ordinary shared-host component
measurements**, so the paired ratios describe these executions rather than
a Tier 0 or Tier 1 CPU speedup. The sampled peak combined RSS was 1.19–1.20
GB for all arms. The two unit-ideal results are solver reports; the prior
[W33 GCD audit](../resultant_nonzero_branch_20261019/RESULT.md) independently
rejected every first code in this finite ordinary block.

The [terminal verifier](verification_result.json) checks every copied
source and protocol hash, result, raw stream, cap receipt, target point,
fixed code set, ANF count, and status. Run `python3 verify.py` to replay it.
The first ANF auditor reached the final degree check before encountering an
older plain-Python `int.bit_count` incompatibility; its
[failure record](audit_attempt1_failure.txt) and corrected script are
retained. The checked [Sage runtime receipt](sage_runtime_info.json) was
captured before the measured runs. `candidate_id: null` is retained for
this two-pair component.

## Next experiment

The existing [native N131 quartic/subspace filter](../n131_native_quartic_filter_20261019/RESULT.md)
already processes fixed two-pair residuals far faster than either cubic
Gröbner arm. A useful next test must **share work across target-derived
three-pair residual families** or reject those families before invoking
separate two-pair queries. The first gate is whole-family rejection on the
unpinned N41 public relation with exact group replay, followed by a
source-bound N131 public-point run under one worker, 600 s, and 4 GiB.
Useful rank, target descent, scalar verification, and matched online rho
time remain later gates of the active goal.
