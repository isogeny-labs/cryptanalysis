# The actual q223 source cannot have a prime-field elliptic isogeny model

2026-11-13. This concerns elliptic curves over F223 and isogenies after base
extension to K=F223³. The positive transfer to Jac(C)(F223) remains in scope.
The written mathematical argument is complete under the standard counting
theorems below; the formalization covers its integer obstruction only.

The actual source has #E(K)=11092292, certified by the original independent
prime/nonzero-generator/Hasse-uniqueness checks in P1 e08eac. Suppose B/F223
became K-isogenous to E. Isogenous elliptic curves over the same finite field
have the same point count, so #B(K)=11092292. The inclusion of F223-rational
points is a subgroup inclusion B(F223) into B(K). Hence m=#B(F223) divides
11092292 by Lagrange. Hasse gives 224−2sqrt223 ≤ m ≤ 224+2sqrt223; integer
bounds29²≤4*223<30² therefore force195≤m≤253. None of these59 integers
divides11092292. This is a contradiction. [pcc:unverified]

This rules out a K-isogeny to any elliptic curve defined over F223 for this
actual source, including an F223 model of the source. It is stronger than
checking j outside F223, which by itself only obstructs a model change. It
does not rule out higher-genus Jacobian descent, a different prime field or
a different source, and it supplies no new ECDLP complexity bound or timing
advantage. No novelty is claimed. [pcc:unverified]

| Exact local declaration | Claim and original gate scope |
| --- | --- |
| `hasse_radius_integer_bounds` | d8f845; closed integer radius bounds |
| `all_hasse_candidates_fail_divisibility` | 180a3c; universal Fin59 kernel computation |
| `no_hasse_count_divides_extension_count` | 7c5dfe; any Nat m with195≤m≤253 |

Both unchanged original gates, producerLean4.35 and consumerLean4.34.1,
pass3 declarations/zero trusted. All three exact original PCC bindings
locally pass in `evidence/prime-field-bindings-02`, unsigned. The only audited
foundations are propext and Quot.sound; the closed radius statement uses
none. There is no custom axiom, sorry, native_decide or kernel bypass.
The actual elliptic groups, Hasse theorem, rational-point inclusion and
isogeny point-count invariance are written standard bridges; they are not
definitions or theorems in this Lean module. [pcc:unverified]

The first exact binding returned2/not_covered because the caller PATH did
not contain lake/lean. That verdict is preserved in bindings01 and953579.
The same unchanged d8f845 claim passes after restoring the actual HOME elan
path; the other two bindings then pass. Both whole proof captures are
standard tar/XZ archives of24 files,30544/30564bytes, with complete member
indices, commands, original outputs and guards (3809b4/f5d8b9). [pcc:unverified]

Sources: frozen P1 source/order certificate, `NoBaseFieldCurve.lean`,
`evidence/prime-field-plan-01`, both `prime-field-lean` captures and
`prime-field-bindings-02`. KB/ecdb tools remain unavailable in this runtime;
the locked atlas was not read or modified. The primary N4 source and actual
native identity supply the input; absence from a search is not evidence.
