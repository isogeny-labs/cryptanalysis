# Target-orbit transport proof map

The readable argument is: if `[4]U_i=Q` and nine source pairs sum to
`τ^j U_i`, apply inverse Frobenius `τ^-j` to each summand. Additivity gives
sum `U_i`, so its cofactor-four projection is `Q`. If the factor base is
closed under inverse Frobenius, every transported summand remains in the
declared base. All four raw preimages and all 131 conjugates are choices of
**one** public target; they are not multiple target workloads.

| Result | Lean declaration | Exact hypotheses | Status |
| --- | --- | --- | --- |
| Additive inverse-orbit relation and base transport | `NinePairOrbit.relation_pullback` in `OrbitTransport.lean` | `g ∘ f = id`; `g` preserves zero and addition; base closed under `g`; `cofactor u=q`; source-point sum is `f^j u`; each source point is in base | Checked under pinned Lean 4.34.1; `#print axioms` reports only `propext` and `Quot.sound` |
| Concrete curve/Frobenius bridge | open | `G=E(GF(2^131))`, `f=τ`, `g=τ^-1=τ^130`, `[4]U_i=Q`, source support and signed-Frobenius closure | Partial formalization; independent Sage checks all 524 choices on the exact field and curve |
| SAT circuit to point relation | open | Native-XOR/CNF encoding of each pair and S3 link; valid folded-column set; decoded signed point sum | Constructed assignment checked; an ordinary solver model still requires independent group replay |

The full concrete bridge is open because this module does not define the
elliptic-curve group over the specified binary field or prove the SAT
encoder's semantics in Lean. The computational checks are
`sage_audit_result.json` and `audit_result.json`; they do not replace those
formal obligations. The exact Lean command and output are in
`lean_check.txt`. The module contains no `sorry`, `admit`, custom research
axioms, or native-evaluation proof shortcut.
