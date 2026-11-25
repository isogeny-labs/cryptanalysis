# CT158 — Independently counted q223 nu=12 twist of the original source

2026-11-16. **[pcc:unverified]**. Developer-local full census. No complete transferred ECDLP or signed verification.

## Precise model distinction

CT152 reconstructed the original E0 over K=F223[z]/(z^3-3):

    y² = x³ + a2*x² + a4*x + a6
    a2=(127,56,199); a4=(152,35,36); a6=(212,109,150)

Shift x_old = X - a2/3 to the short model E0s:

    Y² = X³ + A*X + B
    A=(214,144,205); B=(137,218,9)

The quadratic non-square v=12 has v^((223³-1)/2)=-1 in K. The corresponding
explicit twist E0s^(12), Y²=X³+v²*A*X+v³*B, has coefficients

    v²*A=(42,220,84); v³*B=(133,57,165).

**This explicit twist is not literally the fixed nu12 model!** Inspect the
actual Rust in
twisted-pair-preflight/src/twist_append.rs: TwistedPair::construct() twists
old.source() of its ThirdHop, not original E0. To transfer our count to
that different K-model requires a certified K-defined isogeny
E0 -> old.source() and its twisted isogeny. Neither certificate was newly
executed here. Distinguish independent point count from map/source binding.

## Exhaustive independent integer evidence

Stand-alone C++17 code uses a generic degree-4 convolution with z³=3,
independently builds the entire square-residue roster over K and evaluates
all 11,089,567 x-values for each curve. Neither Rust nor CT152's point
count engine is imported.

| Curve | RHS zero | Nonzero square | Nonsquare | Full order |
| --- | ---: | ---: | ---: | ---: |
| Original short E0s | 3 | 5,546,144 | 5,543,420 | **11,092,292** |
| Explicit E0s^(12) | 3 | 5,543,420 | 5,546,144 | **11,086,844** |

Both have 11,089,567 RHS classifications, and the two orders sum to
22,179,136 = 2*(223³+1). Every nonzero RHS is a square for exactly one
member of the quadratic twist pair; zeros contribute one point to each,
and both curves have their points at infinity. This explains the exact
trace sign reversal without supposing the targeted root's maps exist.

An independent Python derivation checks polynomial translation and twist
coefficients, v's quadratic character, 128 coordinate and Legendre-character
controls, all 59 prime-field admissible Frobenius traces, and three negative
model mutations under both regular and -O Python. Actual full C++ mutant
recount changes only twist B[0] from 133 to 134: its order becomes
**11,088,974**, so the twist-pair identity is deliberately rejected.

Local source/output digests:
- C++ SHA256: 0103c938576d7d4129be21376c3556a7ff0a64a4cb1fff856e148289e95429a0
- Nominal JSON SHA256: 75e11eecaaabf5050a3213eb36626d76fd86e888df4151306f75b18c32d73648
- Mutant JSON SHA256: 313ed6ceedf339a32adac439a3a76ccaa84cdb0191de4eca891a4e6f70780771
- Python SHA256: 6b39e180bf4e4cb968ab8a98cd1feddd0bce719606dfcc467efec6a78b909d70
- Python normal and -O JSON SHA256: 4f860ab811478c1208112f8ff3e3221656041ff98ff87de3343e9425ff08f430

These are developer-local execution and digest observations, not a trusted
PCC signature, independent runner custody or a calibrated ECDLP timing.

## Conditional Frobenius consequence, not a speedup

Explicit original and explicit twist traces over K are -2724 and +2724.
If the actual fixed nu12 source is K-isogenous to E0s^(12) through the
twisting of genuine K-isogenies, then its full order is 11,086,844 and
its cubic trace +2724. For every integer t in the Hasse interval
[-29,29] over F223, neither cubic base-change trace t³-669t equals
±2724 (minimum absolute gap: 112). CT151's corresponding zero-Hom
obstruction then applies to prime-field elliptic maps into the *specific*
Weil restrictions, under the indicated field/source binding.

It does not exclude unrelated prime-field curves, a new Jacobian,
non-homomorphic black-box operations, or cross-characteristic candidate
algorithms. It also does not establish the proposed degree-eight quotient
is defined over F223.

## Reproduce without paid compute

    D=experiments/chained-transfer-public-target/norm-point-reuse-01
    python3 -B "$D/ct158_twist_coefficient_audit.py" >/tmp/ct158-a.json
    python3 -O -B "$D/ct158_twist_coefficient_audit.py" >/tmp/ct158-b.json
    cmp /tmp/ct158-a.json /tmp/ct158-b.json
    c++ -std=c++17 -O3 -Wall -Wextra -Werror "$D/ct158_twist_pair_census.cpp" -o /tmp/ct158-census
    /tmp/ct158-census >/tmp/ct158-normal.json
    /tmp/ct158-census --mutate-twist-b >/tmp/ct158-mutated.json
    cmp /tmp/ct158-normal.json "$D/CT158_NOMINAL_COUNT.json"
    cmp /tmp/ct158-mutated.json "$D/CT158_MUTATED_COUNT.json"

## References and remaining gates

Read root [crypto #3877](https://github.com/isogeny-labs/crypto/pull/3877);
[cryptanalysis #1533](https://github.com/isogeny-labs/cryptanalysis/pull/1533),
[#1589](https://github.com/isogeny-labs/cryptanalysis/pull/1589),
[#1523](https://github.com/isogeny-labs/cryptanalysis/pull/1523),
[#1562](https://github.com/isogeny-labs/cryptanalysis/pull/1562);
crypto #4215/#4178; actual twisted-pair Rust and CT152/CT151 reports.
Standard quadratic twists are covered in Sage's elliptic-curve finite-field
reference: https://doc.sagemath.org/html/en/reference/arithmetic_curves/sage/schemes/elliptic_curves/ell_field.html.
Research-KB MCP/Conductor unavailable in this connector runtime; primary
source files were used instead, and no absence/novelty inference is made.

Next bind old.source via real K-rational isogenies, then independently replay
all 695/701 original/reuse actual Jacobian records, and obtain *only admitted*
same-host C169/C13a/C13b/D pricing. The decisive ECDLP experiment must still
solve the full cold prime-field public-Q problem against strongest matched
rho/BSGS/IC, counting setup, transfer, correction, LA, verification, memory,
uncertainty and independently signed PCC. No paid job, protected merge,
original fixture or PCC ledger was touched. [pcc:unverified]
