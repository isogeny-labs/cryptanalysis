# Proof map: exact Fermat zero indicator in the N41 quotient

The previous four-code experiment represents 16 product-code tuples and
eight first-two-pair roots per tuple in a 128-dimensional quotient over
`GF(2^41)`. For its four-state norm product `Q`, every exact specialization
lands in `GF(2^41)`. Thus `Q^(2^41-1)` specializes to zero when `Q=0`
and to one when `Q≠0`. Characteristic two makes
`I=1+Q^(2^41-1)` the exact zero indicator. `I=0` as a quotient element
excludes every exact root and code tuple in the box.

The producer computes the power with the fixed chain
`1,2,4,5,10,20,40,41`: **82 quotient squarings and seven quotient
multiplications**. Its two boxes are byte-for-byte the code boxes of the
previous trace-bit protocol.

| Result | Lean declaration or finite check | Status |
| --- | --- | --- |
| A characteristic-two Fermat indicator is one exactly on zero inputs. | `FermatZero.indicator_eq_one_iff_zero` in `FermatSound.lean` | Checked under explicit zero-power, nonzero-power, addition, nontriviality, and decidable-equality hypotheses. `#print axioms` reports `propext`. |
| The seven chain steps reach exponent `2^41-1`. | `FermatZero.addition_chain_exponents` | Checked without axioms. |
| The quotient exponentiation equals the direct field zero test for every specialized N41 root. | `audit_sage.py` | Checked Sage evaluated both code boxes, 32 families, 256 roots, all four target charts per fourth code, and the single exact zero. |

The Lean module was built with pinned
`ELAN_TOOLCHAIN=leanprover/lean4:v4.34.1 lean FermatSound.lean` and bundled
`Std`; `lean_check.log` retains the command output. The toolchain commit is
`5045d0056413266e57c625dcd7c365b10e377c52`.
`lean4checker --fresh` was unavailable. The full finite-field Fermat law,
the polynomial-quotient evaluation map, and the power-chain implementation
are not yet joined into one Lean theorem on the concrete N41 curve; this
formalization is partial. The exact finite bridge is independently checked
by Sage on every tested root.
