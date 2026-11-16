# Joint projective row validation

Source `d95d582ca01739e138b605db6279a906d0dd230b`; claim
`PCC-20261116-c1df99`, unsigned/unverified. This follows the separate
[phase/scalar-arithmetic increment](../phase-projective-20261116/README.md),
claim `PCC-20261116-992167`. Earlier evidence is preserved. [pcc:unverified]

Each new row and each certificate row now checks `aG+bQ = ±Fi±Fj` using one
interleaved projective scalar loop and a homogeneous coordinate comparison.
Neither side is normalized, so this equation check calls no field inversion.
Index/scalar bounds, distinct-row requirements, complete column cancellation
and the final recovered-scalar check remain. This common optimization applies
equally to auxiliary, same-special-base direct and ordinary random-base IC;
it cannot itself demonstrate an auxiliary advantage. [pcc:unverified]

The small-group control enumerates public equations against every finite
point-pair sum on `y²=x³+x` over F_7, with both true and false equations,
torsion, infinity and equal/opposite points. Separate affine references cover
both requested large fields and full-width scalar boundaries. Existing full
recoveries and modified-scalar/weight/row refusals remain. [pcc:unverified]

| Check on this source | Unsigned producer observation |
| --- | --- |
| Stable core | 32 checks pass, including one doctest |
| Rust 1.78 core | 32 checks pass, including one doctest |
| Targeted CLI | Eight checks pass |
| Actual p=127 three-arm hand-off | Aligned with profiled phases |
| Strict core/CLI lint, format and fatal-warning docs on both core toolchains | Pass |

The [validator](validator.json) pins exact commands, exits, native logs and
the public correctness-fixture reports. Passing it is not a signed independent
verdict or proof of native execution. The earlier 13-method checker and two
C-backend controls remain scoped to `59524758`; they are not relabeled as
new runs on this source. No research performance, fresh-target or natural-yield
measurement occurred, and qualified speedup remains null. [pcc:unverified]

Next discriminating step: under the existing admission gates, freeze the
actual bases/candidates, then a fresh public 31-bit target panel; compare all
three IC arms, include matched rho separately, and retain all failures and
complete costs. Pair instrumented and uninstrumented controls to expose
profiling overhead without subtracting an estimate. Include upstream auxiliary
discovery/construction and independent replay outside the core phase sum.
An eligible 61-bit special subgroup panel remains a separate open requirement.
The earlier [failed preflight](../benchmark-request-20261116/README.md) is
preserved; access has not changed and it was not retried. This increment
establishes no measured improvement. [pcc:unverified]
