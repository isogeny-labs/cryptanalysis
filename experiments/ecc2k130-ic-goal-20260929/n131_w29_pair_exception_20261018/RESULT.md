# Constant-coefficient obstruction for aligned N131 W29 pair intermediates

The aligned W29 source on `EC1N131Ckb1heb5f1998f20b` has an exact linear
obstruction to a two-torsion sum of its two equal-rotation pair outputs.
For every pair of W29 product codes `p,q`, the corresponding fixed-seed
quadratics cannot have roots `u,v` with `uv=1`. A 131-bit certificate is
particularly compact: **the coefficient of `1` in the polynomial-basis
representation is zero on every term of the necessary equation and one on
its right-hand side**. This rules out that exceptional intermediate for the
first aligned pair (rotation zero) and, by Frobenius, for the second
equal-rotation pair (rotation 36).

## Exact instance and proof

The field is `GF(2)[u]/(u^131+u^13+u²+u+1)` and the curve is
`y²+xy=x³+1`. The W29 source uses seed polynomial encoded by
`s=898618 << 1 = 1797236`, 28 free canonical
mask bits, and 28 product-basis elements `b_i=a_i²+s a_i`. Its source
products form `V=span_GF(2){b_0,...,b_27}`. Let
`H=halftrace(s)²`, `C=1+H`, and `CH=C·H=s²`; their exact integer field
representations are in [linear_certificate.json](linear_certificate.json).
The two pair-output reciprocal roots satisfy
`C u²+p u+H=0` and `C v²+q v+H=0`.

If `uv=1`, these equations force `u=Cp+Hq` and `v=Hp+Cq`.
Writing `q=p+d` gives the necessary equation

`p²+p·d+CH·d²=1` with `p,d∈V`.

Let `λ` return the coefficient of `1` in the canonical polynomial-basis
representation of a field element. The [certificate](linear_certificate.json)
and an independent [Sage field replay](linear_certificate_sage_replay.json)
verify `λ(b_i²)=0` for 28 elements, `λ(b_i b_j)=0` for all 406 unordered
pairs, and `λ(CH b_i²)=0` for 28 elements. Squaring and multiplication are
binary bilinear, so `λ` of the left side is zero for every `p,d∈V`, whereas
`λ(1)=1`. The 462 generators span a 114-dimensional subspace of the
131-dimensional field, and adjoining `1` raises its rank to 115. The
explicit separating parity mask is the integer `1`.

For `E: y²+xy=x³+1`, adding its unique rational two-torsion point
`T=(0,1)` sends nonzero `x` to `1/x`; hence a sum of two nonzero-x points
equal to `T` forces the product of their reciprocal x-coordinates to be
one. The checked [Lean module](PairException.lean) proves the affine
translation identity, the forced-root equation, and the sparse
reparameterization. The [proof map](PROOF_MAP.md) identifies the group-law
and finite-field circuit bridges that remain outside Lean.

## Measured circuit gate and independent checks

Both SAT encodings quantify over all `2^28` W29 product codes in each slot,
including source-invalid codes. They are necessary-condition gates for the
equal-rotation pair exception, with `candidate_id: null`. The query resource
envelope was one CryptoMiniSat 5.14.7 worker, a 600-second parent wall cap,
and a 4 GiB combined RSS cap. The [checked Sage runtime](sage_runtime_info.json)
was recorded before the builds.

| Encoding / check | Size or scope | Recorded result |
| --- | ---: | --- |
| Direct `(Cp+Hq)(Hp+Cq)=1` XCNF | 4,751 AND gates; 8,214 variables | `BOUNDED_UNKNOWN` at 600.142 s parent query wall; 134,643,712 B sampled peak combined RSS |
| Sparse `p²+pd+CHd²=1` XCNF | 784 AND gates; 1,424 variables | `UNSAT_UNCERTIFIED` at 0.113 s parent query wall; 24,461,312 B sampled peak combined RSS |
| Exact reduced-space enumeration | 17-dimensional kernel; 131,071 nonzero difference codes | Zero solvable systems; all system ranks 27; independently reproduced by pure Python |
| GF(2) linear certificate | 462 generators; span rank 114 | Constant-coefficient separator checked by pure Python and independent Sage finite-field arithmetic |

The direct and sparse XCNF build and query receipts are
[build_result.json](build_result.json), [query_result.json](query_result.json),
[sparse_build_result.json](sparse_build_result.json), and
[sparse_query_result.json](sparse_query_result.json). The exact enumeration
and independent replay are [enumeration_result.json](enumeration_result.json)
and [verification_result.json](verification_result.json). The SAT return
alone has no proof certificate; the separate linear certificate supplies
the mathematical exclusion.

This removes one exceptional intermediate chart from the aligned N131
five-pair point-decomposition design. The next implementation step is to
reuse this explicit obstruction in a full target-conditioned N131 circuit,
handle the remaining identity and unequal-rotation charts, and run the
frozen public-point relation gate with complete source-validity and
distinct-column conditions.

## Reproduction

From the repository root, use the checked launcher for the Sage jobs:

```sh
./sage -python experiments/ecc2k130-ic-goal-20260929/n131_w29_pair_exception_20261018/rank_certificate.py
./sage -python experiments/ecc2k130-ic-goal-20260929/n131_w29_pair_exception_20261018/enumerate_exception.py
python3 experiments/ecc2k130-ic-goal-20260929/n131_w29_pair_exception_20261018/verify_enumeration.py
python3 experiments/ecc2k130-ic-goal-20260929/n131_w29_pair_exception_20261018/linear_certificate.py
./sage -python experiments/ecc2k130-ic-goal-20260929/n131_w29_pair_exception_20261018/verify_linear_certificate_sage.py
```

The existing result-producing scripts intentionally write receipts to fixed
paths; rerun in an isolated copy to preserve this frozen evidence.
