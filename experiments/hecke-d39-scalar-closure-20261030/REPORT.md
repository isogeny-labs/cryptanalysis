# Hecke index calculus: small-scalar closure of the D=-39 matrix

2026-10-30. Status: **implementation unit-tested; research execution blocked**.
This follows the user request to pursue Hecke index calculus from the cited
low-conductor experiment. It does not claim a new rank or a faster IC solver.

## What the source establishes

The [original result](../ecdlp-hecke-d39-holdout-20261026/RESULT.md) studies
points of X_0(11)=11a1, not class-group vectorization as a standalone attack.
Its curve over F_367 is y^2+y=x^3-x^2-10x-20, with group order 385=5*7*11.
The saved class contains 64 distinct points. Its 48 Hecke rows have rank 40,
and adding 64 Atkin–Lehner rows gives rank 52 modulo 11. These values are
inherited evidence, not fresh measurements in this change.
The [repeated-root audit](../hecke-d39-f6-repeated-root-audit-20261026/RESULT.md)
found zero extra rows from repeated-root recovery on this exact fixture.

The starting chat's class-group explanation was too generic for this work:
the relevant unknowns are point logarithms on the modular elliptic curve.
Relations among CM ideal classes do not automatically provide those logs.
The lead atlas's [class-group bridge record](https://github.com/isogeny-labs/crypto-autoresearcher/blob/main/knowledge/leads/ecdlp/structure/LEAD-STR-class-group-ecdlp-bridge.yaml)
tracks the distinct missing bridge. Its representative-selection record
concerns transported factor-base yield, a different mechanism from the finite
modular-curve relation matrix considered here. Both were reviewed.

## Derived gap and proposed addition

Rank-nullity gives a 12-dimensional kernel on the 64 columns. Eleven more
independent homogeneous constraints would leave one dimension, which one
known-log anchor could normalize. This is necessary linear algebra, not a
claim that the additional constraints exist or can be cheaply generated.

Project P to [35]P so the relevant group is the order-11 component. If
[35]P_j=[35m]P_i, applying the discrete-log homomorphism gives
log([35]P_j)-m*log([35]P_i)=0 modulo 11. Equal projections and projected zero
give additional valid equalities. This uses ordinary scalar arithmetic and
point comparison; relation collection does not require known logs. It does
not establish a new structural theorem, and no Lean verification is claimed.

The [protocol](PROTOCOL.md) fixes multipliers 2,3 and six arms. The stdlib-only
[checker](audit.py) validates points and relations, independently counts the
small curve, compares dense elimination with the frozen sparse checker and,
if rank reaches 63, solves with one anchor and replays every scalar. It checks
Hecke rows in the full group and Atkin–Lehner rows after projection: the latter
have a torsion translation, so homogeneous full-group checks would be wrong.
New projected relations are only asserted modulo 11; unrelated moduli are
not valid comparison fields for these rows.

## Validation and execution limits

Three [synthetic unit tests](validation/unit-tests.txt) pass: rational
five-torsion arithmetic, dense elimination with a nonzero right-hand side,
and relation construction with duplicate/zero points and invalid-row rejection.
The first attempt had two incorrect test expectations: the doubling and
tripling torsion coordinates were swapped. Hand computation gives doubling
slope 5 and 2(5,5)=(16,-61); the expectations were corrected. Checker
arithmetic did not change. The initial failure is retained in
[first-attempt.txt](validation/first-attempt.txt).
Python compilation, shell syntax and git whitespace checks passed.
These checks do not execute the saved research fixture or establish its
new arm ranks.

The required checkpoint gate first failed because BSD stat output was mixed
with GNU stat output on Linux. `scripts/checkpoint.sh` now uses Python os.stat
for the two metadata queries; the gate then reached the upload check.
The [retained failure](validation/checkpoint-gate.txt) states that this workspace
has no checkpoint upload token, AWS profile or AWS CLI upload path. No
research run was launched. The original 64-point fixture remains untouched.

## Requirement status and next action

| Requirement | Status | Evidence or remaining work |
| --- | --- | --- |
| Identify exact starting experiment | verified complete | pinned input, original result and producer reviewed |
| Develop a concrete next discriminator | implemented | six-arm protocol and checker |
| Validate checker building blocks | verified complete | three synthetic tests; syntax checks |
| Run six arms and recover base logs if possible | blocked | successful S3 checkpoint required |
| Establish scalable IC improvement | unresolved | larger sparse bases, target descent and matched costs |

The [problem record](../../problems/hecke-d39-scalar-closure-execution.md)
gives checkable exit conditions. Configure checkpoint upload through the
supported environment setup, then from the repository root run:

```sh
bash scripts/checkpoint.sh gate
timeout 60 python3 experiments/hecke-d39-scalar-closure-20261030/audit.py \
  --out experiments/hecke-d39-scalar-closure-20261030/runs/ATTEMPT/receipt.json
```

Replace ATTEMPT with a new identifier; the checker refuses to overwrite its
receipt and rechecks the checkpoint gate itself. Capture stdout/stderr and
exit status, retain failures and record source/input hashes. A successful
finite rank result still needs larger-class tests with random-set controls:
64 columns in an order-11 group can exhibit a strong density artifact.
Arbitrary-target descent and matched rho timing are not implemented here.

## Visual and canonical graph review

The [editable diagram](evidence.dot), [SVG](evidence.svg) and
[PDF report](report.pdf) separate saved evidence from the unexecuted proposal.
The quantitative diagram uses two existing rank observations, with no
statistical uncertainty assigned to exact finite ranks; it contains no new
experimental observation. The original D39 evidence-map and canonical
`docs/ecdlp-surfaces/transfer.dot`, transfer SVG and counts SVG were checked.
No new isogeny edge or surface-transfer fact was established, so these
canonical graphs remain unchanged. Rebuild this PDF with `python3 build_report.py`.
