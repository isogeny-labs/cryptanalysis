# CT27 — complete base-field quotient norm certificate

**Status:** [pcc:unverified]. Independent development implementation over fixed public toy fields, not a signed verifier, measured speedup, or complete chained solver. This feature branch starts from [CT21 #1488](https://github.com/isogeny-labs/cryptanalysis/pull/1488) exact head `7c1f32ecb24daffce449703075573c824dd1f241` without modifying its native maps, PCC records or frozen source pins.

## Result and formulas

Let `C: y²=x⁶+a*x⁴+b*x²+c` be a smooth even genus-two sextic, in odd characteristic with `c ≠ 0`. Its two elliptic quotients are:

- `q_even(x,y)=(x²,y)`, on `Y²=U³+a*U²+b*U+c`
- `q_recip(x,y)=(c/x²,c*y/x³)`, on `Z²=V³+b*V²+(a*c)*V+c²`, extended over zeros and infinities.

For a degree-two finite support `u(x)=x²+s*x+t`, `v(x)=v0+v1*x`, with `u | (f-v²)`, the **even norm** for `s≠0` uses

```
m = -v1/s
n = v0+m*t
S = s²-2*t
U = m²-a-S
Y = -(m*U+n)
```

All arithmetic is in the base field. Indeed, `x²=-s*x-t` on the support, so `y=m*(x²)+n`, and the third intersection of that line with the quotient cubic has abscissa `U`; reflection gives `Y`. If `s=0`, double the point `(-t,v0)` for `v1=0`; otherwise `v0=0` and the opposite images cancel.

For the **reciprocal norm**, when `t≠0`, set `sp=s/t`, `tp=1/t`, `z0=c*tp*(v0*sp-v1)`, and `z1=c*(v0*(sp²-tp)-v1*sp)`. For `sp≠0` use:

```
m = -z1/(sp*c)
n = z0+m*c*tp
S = c*(sp²-2*tp)
V = m²-b-S
Z = -(m*V+n)
```

This follows by reducing `z=c*y/x³` modulo `w²+sp*w+tp`, with `w=1/x`. If `sp=0`, use doubling (`z1=0`) or cancellation; if `t=0`, the `x=0` point maps to the elliptic identity and the remaining finite point is evaluated directly (or identity if both finite roots vanish).

**Balanced infinities are not optional:** a degree-`d` class with `plus=k` is represented by `D_fin+k∞₊+(2-d-k)∞₋-(∞₊+∞₋)`. Both infinities map to identity on the even quotient. On the reciprocal quotient, their images are `(0,c)` and `(0,-c)`; therefore add `[2*k+d-2](0,c)` to the reciprocal finite-support norm. This also preserves nontrivial degree-zero and degree-one balanced classes.

## Complete independent development replay

Reproduce with assertions enabled, no third-party imports:

```sh
python3 -S -B experiments/chained-transfer-reference/ct27/even_quotient_norm_oracle.py
python3 -O -S experiments/chained-transfer-reference/ct27/even_quotient_norm_oracle.py
# The second command MUST fail nonzero: it refuses disabled assertions
```

For **each** of the fixed curves `C0: (a,b,c)=(6,13,56)` and `C1:(26,42,68)`, the development run constructed 12,317 distinct canonical balanced representatives and checked both direct norms against independently computed elliptic group laws. Counts per model: three infinity-only representatives; 236 degree-one/infinity representatives; 6,844 split quadratic; 5,116 irreducible quadratic; 118 repeated/tangent quadratic. Non-split checks used fresh `F101²` arithmetic and Frobenius-conjugate points, including 100 nonsplit cases with `s=0`. Split cases included 116 with `s=0`, 59 cancelling opposite-support pairs and two finite `x=0` points. The oracle examined all 5,050 irreducible monic quadratic polynomials in F101[x], and rejected optimized Python. These are producer-run arithmetic checks, not a signed independent PCC verdict or a native Rust differential replay.

**Retained failed assumptions:** an earlier development version used the wrong sign `n=v0-m*t`, detected by a split-support mismatch and corrected to `v0+m*t`. A second attempt incorrectly assumed `p≡3 (mod4)` for a square-root shortcut; `p=101≡1 (mod4)`, so the final code uses a complete base-field square-root table. These are corrected implementation errors.

## Provenance, novelty and bounded scope

- [crypto #3877 / SEVEN_JACOBIAN_PROOF](https://github.com/isogeny-labs/crypto/blob/research/chained-jacobian-transfer-20261110/research/chained_jacobian_transfers_20261110/SEVEN_JACOBIAN_PROOF.md) — established quotient maps and global pull/norm obligations.
- [cryptanalysis #1484](https://github.com/isogeny-labs/cryptanalysis/pull/1484), [#1488](https://github.com/isogeny-labs/cryptanalysis/pull/1488), and existing `experiments/chained-transfer-reference/src/balanced.rs` — accepted native class semantics, complete genus-two maps and subsequent Richelot transfer. No duplicate native implementation was attempted.
- Howe–Leprévost–Poonen, [Large torsion subgroups of split Jacobians](https://arxiv.org/abs/math/9809210), §3.2, and [Milne's Abelian Varieties notes](https://www.jmilne.org/math/CourseNotes/AV.pdf). The formulas are elementary elliptic chord-and-tangent identities, **not claimed new**.
- Shared research-KB and encrypted ECDLP atlas are not accessible in this runtime; prior published checked sources were consulted instead. This is an evidence gap, not a negative literature search.

The immediate acceptance step is a guarded **Rust** implementation checked against unchanged `QuadraticCover::norm` and reciprocal norm on all 12,317 divisor classes of each curve, including zero, repeated and ramified cases, followed by exact native field-operation counts. Existing full-cost DLP comparisons against optimized rho/index calculus require authorized benchmark admission: S3 checkpoint/profile and live budget token remain unavailable. No paid experiment was started. Parent ledger, archive, CI/review and independent scientific-signature gates remain in force.

The associated source-link diagram is `route.dot`. An inspected two-page local PDF report was produced for this checkpoint; it is not part of this text-only GitHub commit.
