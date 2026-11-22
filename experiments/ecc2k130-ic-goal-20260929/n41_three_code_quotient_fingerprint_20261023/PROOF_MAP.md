# Proof map: three-code quotient fingerprint

The coefficient algebra is

`R = GF(2^41)[p,q,r]/((p+p₀)(p+p₁),(q+q₀)(q+q₁),(r+r₀)(r+r₁))`.

The three quadratic code relations make `R` eight-dimensional over the
field. The archived 170-term `H(a,b,p,q,U)` is monicized in `R[U]`, giving
a 64-dimensional quotient `K=R[U]/H`. For the public residual chart `t`
and third-pair seed `s`, the producer constructs the eliminated norm

```
A = t² + U(U+1)t(t+1) + (t+1)²
B = U(U+1)t(t+1)
D = (U+1)²t² + U²(t+1)²
L = 1+r
M = LB+rA
N = LD+s²A
Q = LN²+rNM+s²M².
```

At an exact specialized root, `Q=0` is the third-pair S3 incidence
condition. The producer computes the dual trace coordinates of `Q` and
multiplies `1+bit_i(Q)` for the first 24 bits, stopping when the quotient
residue is zero. A zero residue evaluates to zero at every admissible code
triple and every root of `H`, so that complete box contains no exact zero
of `Q`.

| Mathematical result | Declaration or check | Status and hypotheses |
| --- | --- | --- |
| Zero quotient fingerprint excludes exact norm zeros in all roots of a three-axis code box. | `ThreeCodeBox.zero_quotient_excludes_box` in `BoxSound.lean` | Lean 4.34.1 checked. Assumes zero-preserving specialization, exact indicator evaluation, `0≠1`, and a decidable field equality. `#print axioms` reports only `propext`. |
| Three-axis coefficient quotient, H specialization, Q specialization, and the bit-product fingerprint agree at each N41 root. | `audit_sage.py` and `holdout/audit_sage.py` | Checked Sage evaluated 576 and 1,152 specialized H coefficients, 512 and 1,024 roots, and all four fingerprint checkpoints for both frozen runs. |
| Eliminated Q and direct third-pair S3 have the same zero set on the first run's roots. | `audit_geometry_sage.py` | Checked Sage compared both conditions on 512 roots, with one zero in the witness family. |
| The seven-state ordinary witness sums to the archived raw target and its fourfold is the public target. | Both checked Sage audits | Exact point equality checked on the N41 curve. |

The Lean module includes the readable proof. Its exact command and output are
retained in `lean_check.log`; the command was
`ELAN_TOOLCHAIN=leanprover/lean4:v4.34.1 lean BoxSound.lean` from this folder.
The dependency is the bundled `Std` for Lean 4.34.1 at commit
`5045d0056413266e57c625dcd7c365b10e377c52`.
`lean4checker --fresh` was unavailable on this host. The finite-field
quotient construction and trace-dual equality are checked by the independent
Sage evaluations above; a direct Lean polynomial-quotient formalization
remains open.
