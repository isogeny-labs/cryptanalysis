# Proof and verification map

| Result | Formal or executable check | Status and scope |
| --- | --- | --- |
| One product inverse implies the two endpoint inverse identities; endpoint trace and chunk-splitting identities | `../n41_n131_shared_pair_inverse_20261017/SharedInverse.lean`; `lean_source.stdout` | Lean 4.34.1 build passed; `#print axioms` reports no axioms for the three listed declarations. These are algebraic circuit dependencies. |
| A relation on a Frobenius-rotated target pulls back to the raw target | `../n41_s3_direct_orbit_20261017/OrbitTransport.lean`; `lean_orbit.stdout` | Lean 4.34.1 build passed; `#print axioms` reports only Lean's `propext` and `Quot.sound`. This is a structural implication under that module's declared group-action hypotheses. |
| Selector semantics and exclusion of unused codes | `audit_selector.py`, `selector_result.json` | Exact finite gate evaluation of all 64 codes passed; this is an executable finite certificate, not a general Lean theorem. |
| Existence of the 32 public N41 decompositions | `census/join4_census.cpp`, `census/census.stdout`, `census/audit_sage.py`, `census/audit_result.json`, `census/archive_verify.py` | Complete finite census under the frozen source and four-slot policy. Each output was independently recomputed with the checked Sage launcher, including distinct folded columns and raw-target transport. No separate Lean encoding of the N41 curve or each witness was attempted. |
| Satisfiability of the W11 circuit with the archived public witness | `build_control_orbit.py`, `orbit_build_result.json`, `orbit41.xcnf` | The complete assignment passed every emitted clause and XOR row. This checks one witness; it does not establish completeness of the circuit for every possible decomposition. |

Commands from the repository root:

```sh
elan run leanprover/lean4:v4.34.1 lean experiments/ecc2k130-ic-goal-20260929/n41_n131_shared_pair_inverse_20261017/SharedInverse.lean
elan run leanprover/lean4:v4.34.1 lean experiments/ecc2k130-ic-goal-20260929/n41_s3_direct_orbit_20261017/OrbitTransport.lean
python3 experiments/ecc2k130-ic-goal-20260929/n41_w11_fourpair_orbit_sat_20261019/archive_verify.py
python3 experiments/ecc2k130-ic-goal-20260929/n41_w11_fourpair_orbit_sat_20261019/census/archive_verify.py
```

Both Lean files contain the `#print axioms` checks whose output is archived. The toolchain is pinned by the commands above; the repo source files and frozen runtime/protocol hashes identify the dependencies. The finite-census claim is computational and its bridge to curve arithmetic is the independently executed checked-Sage audit. A general formal proof of circuit completeness is open.
