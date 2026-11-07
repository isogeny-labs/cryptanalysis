# Two formal-scope corrections: CubicGluing determinant, Hecke-432 torsion wording

These are additive corrections. The archived files stay byte for byte
unchanged: their hashes are bound by `SEAL.sha256` files and
`tools/ci/quartic_certificates.json`. They were found by the read-only
CFSG exposure audit,
isogeny-labs/crypto-autoresearcher#2690,
`docs/reports/2026-10-29-cfsg-lessons-ecdlp-exposure/report.md`, items 8 and
13 of the crypto/cryptanalysis table. Both are mode A: a sentence that says
more than the Lean theorem it cites.

## 1. `ghs-sweeper/formal/CubicGluing.lean`: `determinant_binding`

The comment above the theorem reads "These constants bind the certificate to
q=3, M=diag(3,4), det(M)=q^3". The theorem is

```lean
theorem determinant_binding : (3:K)*4 = 3^3 := by decide
```

with `K` the field of five elements (`Fin 5` coordinates). It proves the
**congruence** 3·4 ≡ 3³ (mod 5). Both sides are 2 mod 5. It does not prove
det M = q³. Over ℤ, det diag(3,4) = 12 and q³ = 27, so that equation is
false. [`check.py`](check.py) recomputes both facts
([`check.json`](check.json)).

**Corrected reading.** `determinant_binding` states det M ≡ q³ (mod 5) for
the fixed q = 3, M = diag(3,4), and nothing more. Any sentence citing it for
an integral determinant identity should be read with this scope. The README
table row in `ghs-sweeper/formal/README.md` lists the declaration only as
part of the "verified exact Fin 5 coordinates" certificate, which is
consistent with this reading. The defect is confined to the Lean comment.

## 2. `hecke-432-cusp-image-20261025/RESULT.md`: "trivial torsion over K"

The result states in bold that B: y² = x³ − 16 has **trivial torsion over
K = ℚ(ζ₆)**. The cited Lean theorem,
`CuspArithmetic.no_torsion_prime_from_reduction_orders`, proves only the
arithmetic implication. Its hypotheses `atSeven`/`atThirteen` assume that a
torsion prime ℓ divides the residue-group orders at the good primes above 7
and 13. Those hypotheses encode the standard fact that prime-to-p torsion
injects into the reduction at a prime of good reduction p. RESULT.md line 37
already lists this bridge as not formalized, together with the cusp-field
bridge and Manin–Drinfeld.

**Corrected reading.** "Trivial torsion over K" is a written argument from
two standard facts:
- injectivity of torsion into good reduction away from ℓ;
- the residue orders 7 and 9.

Lean checks only the final arithmetic step, conditional on the reduction
divisibility hypotheses. The downstream conditional statement ("**if** the
evaluator extends to a ℚ-defined morphism ... every cusp image equals O")
inherits this condition, and so does
`experiments/hecke-432-map-identity-20261025/RESULT.md` line 50, which uses the
same "trivial torsion" premise.

## Graphs

No graph plots either quantity. A repository-wide search for
`determinant_binding` and "trivial torsion" finds only the files named above
plus three name lists: `docs/reports/2026-10-28-formal-coverage/inventory.json`,
`tools/lean/current-corpus-gate.py` and a reviewer's reconstructed gate. These
list the declaration name only; none is a graph source. No figure changes.
