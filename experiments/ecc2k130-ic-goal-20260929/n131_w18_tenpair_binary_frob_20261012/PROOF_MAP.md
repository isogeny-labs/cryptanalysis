# Proof map: ten-pair N131 target circuit

| Result | Lean declaration or receipt | Status and hypotheses |
| --- | --- | --- |
| Additive inverse-Frobenius relation and cofactor transport for any finite source-point list | `NinePairOrbit.relation_pullback` in `../n131_w18_ninepair_orbit_20261012/OrbitTransport.lean` | Checked in pinned Lean 4.34.1 with only `propext` and `Quot.sound`; requires inverse endomorphisms, base closure, an actual group sum, and cofactor map. Its list-length-independent statement applies to ten summands conditionally. |
| Binary Frobenius selector composes controlled `2^k` iterates | `BinaryFrobenius.binary_target_correct` in `../n131_w18_ninepair_binary_frob_20261012/BinaryFrobenius.lean` | Checked in Lean 4.34.1 with only `propext`; the concrete circuit-to-field bridge remains partial. |
| Ten W18 source pairs, distinct folded columns, and constructed target sum | `control_result.json`, `sage_fixture_result.json` | All constructed CNF/XOR rows checked and the added source point independently replayed in checked Sage. The full N131 elliptic-curve group and SAT encoder semantics are not formalized in Lean. |
| Frozen ordinary N131 target query | `query_result.json`, `audit_result.json`, `archive_receipt.json` | Byte-exact formula replay and terminal classification checked. The ordinary solver status is `BOUNDED_UNKNOWN` with `s INDETERMINATE`; no mathematical UNSAT statement follows. |

The two referenced Lean modules pin toolchain 4.34.1 and retain the actual
build and `#print axioms` output. `lean4checker --fresh` was unavailable on
this host. The concrete field/curve/source-to-circuit implication remains
an explicit open formalization obligation; the exact missing definitions
are the binary-field elliptic-curve group, 20-column source encoder, and
native-XOR/CNF group-link semantics.
