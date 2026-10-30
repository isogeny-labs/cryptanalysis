# One simple residue factor determines a V4 quartic's local splitting

For the two exact degree-144 quartic presentations with Galois group `V4` over the degree-36 base field, **one simple residue factor of degree one or two determines the full unramified relative splitting pattern**. A simple linear factor gives `[1,1,1,1]`; a simple irreducible quadratic factor gives `[2,2]`. This remains useful when the quartic reduction has repeated factors and does not itself satisfy the squarefree factorization criterion.

The frozen nine-prime control audit found **183/183** simple-linear sites consistent with complete splitting, including **48** repeated reductions where ordinary squarefree factorization was unavailable. The prospectively frozen five-prime holdout at `61,67,71,73,79` matched **62/62** right-quartic observations. At `p=71`, one repeated left reduction with two simple linear factors predicted `[1,1,1,1]`, and one with a simple irreducible quadratic predicted `[2,2]`; both were independently resolved from the right quartic by normalized Taylor tests. The remaining two repeated left reductions were retained and classified by separately frozen left Kummer checks.

| Prime | Base places | `[1,1,1,1]` | `[2,2]` | Right observation |
| ---: | ---: | ---: | ---: | --- |
| 61 | 2 | 0 | 2 | 2 squarefree reductions |
| 67 | 18 | 18 | 0 | 18 squarefree reductions |
| 71 | 20 | 17 | 3 | 16 squarefree reductions, 4 Taylor checks |
| 73 | 4 | 0 | 4 | 4 squarefree reductions |
| 79 | 18 | 18 | 0 | 18 squarefree reductions |

## Method and evidence boundary

For a monic quartic integral at a base prime `P`, a simple irreducible factor of degree `d` modulo `P` lifts by Hensel to a local irreducible factor of degree `d`. At the selected odd primes the exact relative discriminant support is contained above 2 and 3, so the quartic extension is unramified. Frobenius acts on the four roots through the regular `V4` action. A fixed root makes Frobenius the identity and fixes all four roots; a two-cycle makes it nonidentity and gives two two-cycles. The exact conjugacy `s -> -s` transfers the left pattern at `P` to the right pattern at `σ(P)`.

`protocol.json` froze both control-source hashes and the five holdout primes before the left Sage producer. `control_audit.py` checked the historical reduction factors against separately retained local resolutions at primes 7, 11, 23, 31, 41, 43, 47, 53, 59. `control_result.json` retains all 216 examined sites, including the 183 simple-root sites and 48 repeated simple-root controls.

`predict_sage.py` factored only the left quartic at the holdout places. Its frozen output had 58 squarefree predictions, one simple-linear shortcut, one simple-quadratic shortcut, and three initially unresolved reductions. `quadratic_extension_protocol.json` fixed the complementary degree-two rule **before** right observation and classified one of those three. `fallback_protocol.json` froze the other two and the exact left Kummer input; `fallback_sage.py` classified them. `combine.py` produced `combined_predictions.json` with all 62 right-side patterns. `observation_protocol.json` sealed that file's SHA-256 `919758e671b32990d5914c61873347c1fca34fad088340b351eb7e066a5c780d` before any right-side observation.

`observe_sage.py` reconstructed and factored only the right quartic: 58 squarefree reductions and four repeated reductions at `p=71`. `taylor_protocol.json` froze those four right sites without expected degrees. `taylor_sage.py` independently lifted every doubled linear residue root `a`, checked `v_P(g(a))≥2` and `v_P(g'(a))≥1`, and checked the full polynomial identity `g(a+pz)/p² ≡ Az²+Bz+C (mod P)`. Each nonzero normalized discriminant classified its double cluster. The resulting four patterns were `[2,2]`, `[2,2]`, `[1,1,1,1]`, and `[1,1,1,1]` at right place indices 0, 3, 16, 19. `compare.py` checks all exact identities and sealed hashes; `comparison.json` reports `PASS_PROSPECTIVE_V4_FACTOR_SHORTCUTS`, 62 matches.

The checked-Sage stage receipts record 65.014 seconds for the left producer, 11.268 seconds for left Kummer fallback, 91.056 seconds for right observation, and 37.404 seconds for Taylor replay on this shared local host. These are stage timings, not isolated performance or single-target ECDLP measurements. `sage-runtime-info.txt` records the loaded accepted arithmetic build.

## Proof map

`SimpleRootV4.lean` proves `one_fixed_root_forces_identity`, `one_fixed_root_forces_all_four_fixed`, and `one_two_cycle_forces_all_orbits_two` for the regular rank-two sign action on four root labels. It builds under pinned Lean `leanprover/lean4:v4.35.0-rc4` and mathlib4 `021c46bdd042f67b538b9f9871d556a93713a9a9`; `lean-output.txt` records `#print axioms` with only standard `propext`. The predecessor's `ConjugateFactors.lean` proves generic base-preserving quotient, prime-ideal, and residue transport, while the earlier local-factor `QuadraticSplit.lean` proves the quadratic discriminant criterion. The formalization is partial at the exact field/coefficient import, integral-closure prime bridge, and Hensel/Taylor connection from residue factors to root orbits. The readable argument and exact finite-field receipts above retain those obligations.

## Replay

From the repository root, preserving the frozen protocols and seals:

```sh
python3 experiments/hecke-432-j1728-simple-root-shortcut-20261026/control_audit.py
python3 experiments/hecke-432-j1728-simple-root-shortcut-20261026/run_bounded.py predict
python3 experiments/hecke-432-j1728-simple-root-shortcut-20261026/extend_quadratic.py
python3 experiments/hecke-432-j1728-simple-root-shortcut-20261026/run_bounded.py fallback
python3 experiments/hecke-432-j1728-simple-root-shortcut-20261026/combine.py
python3 experiments/hecke-432-j1728-simple-root-shortcut-20261026/run_bounded.py observe
python3 experiments/hecke-432-j1728-simple-root-shortcut-20261026/run_bounded.py taylor
python3 experiments/hecke-432-j1728-simple-root-shortcut-20261026/compare.py
```

Every bounded Sage stage invokes `/Volumes/SSD990/cryptanalysis/sage -python`.
