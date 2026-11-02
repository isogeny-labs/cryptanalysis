# Xedni affine-coset Lean review

**Reviewed claim.** At producer commit `d243c3ce88e077a593c3be2c2ba502d976564534`, for any finite family of integer incidence rows, directions that annihilate every row and are coordinatewise divisible by positive `q` retain those properties under integer recombination. Every affine candidate formed from such directions preserves the starting vector's row dot products and coefficient residues. This is a conditional algebraic result about the candidate family.

**Review result.** The three named Lean declarations passed the pinned local checker and axiom audit, and the blind reviewer independently derived the invariant with its exact hypotheses. The source reviewer found that the merged workflow at `749d807be2c82175641c17c589e6883ba8b10abb` failed on first-use elan stderr. Repair PR [#1377](https://github.com/isogeny-labs/cryptanalysis/pull/1377) includes an explicit toolchain download and, at head `937b387b`, also binds `lattice.rs` in the checker and CI paths. The successful hosted Lean run [41505647909](https://github.com/isogeny-labs/cryptanalysis/actions/runs/41505647909) belongs to the earlier repair head `196aa0d`, so it does not certify the amended head or the merged workflow. Record a current-head hosted result before closing that gate.

## Per-claim findings

| Claim or gate | Machine status | Fidelity | Outcome and exact boundary |
| --- | --- | --- | --- |
| `XedniAffineCoset.direction_span_closed` | passed locally at producer bytes | faithful_scoped | validated_scoped for finite integer combinations of directions satisfying every row-kernel and zero-remainder premise. |
| `XedniAffineCoset.candidate_preserves_divisibility` | passed locally at producer bytes | faithful_scoped | validated_scoped for coefficient-difference divisibility under the same premises. |
| `XedniAffineCoset.candidate_preserves` | passed locally at producer bytes; hosted pass at `196aa0d` | faithful_scoped | validated_scoped for exact row values and residues of affine candidates, conditional on validated directions. |
| Rust LLL output-span bridge | source inspected | partial | `lattice.rs` uses integer row subtraction and swaps; the checked theorem is not a formal proof of Rust control flow or arbitrary runtime inputs. The returned candidate is separately certified by Rust. |
| Merged hosted gate at `749d807` | failed | mismatch | needs_revision: first-use elan messages made `check.py` reject stdout/stderr despite Lean exit 0. PR #1377 repairs the workflow; current-head checks remain to be recorded. |

The reviewed Lean source is `research/xedni_lift_optimizer_20261101/lean/XedniAffineCoset.lean` (SHA-256 `c39148eaf547acb4f8ea7c752413a83946b43557181ef55da86ac3f5f466e757`) under `leanprover/lean4:v4.34.1`. The Rust candidate source is `suite/src/cryptanalysis/xedni_lift.rs` (SHA-256 `b08c94845e9b4ed9660bd01aff01b2e59d274d0f7806a4ddf48ef3d35541ac96`); the LLL source is `suite/src/cryptanalysis/lattice.rs` (SHA-256 `0687b6c0c20a61300023d96ac83de271adc0fc1e1a372114acd5ed7a83dd6c0b`). All three named declarations reported only `propext` and `Quot.sound`. The check used installed Lean 4.34.1; no independent kernel binary recheck was performed.

## Controls, independence, and open work

- Blind controls at `n=1`, `u=0`, `q=2` rejected missing row-kernel and residue premises independently. For all integer coefficients, each direction must meet both premises; a single fixed candidate may have cancellation.
- Source-gate controls rejected a stale Rust source hash and an altered axiom receipt. The coordinator's amended checker also rejects a stale `lattice.rs` hash. These validate fail-closed behavior for those mutations, not implementation equivalence.
- The [precommitted review plan](review-plan.yaml) assigns algebra to `TASK-20261102-1a2b3c` and source/gate fidelity to `TASK-20261102-4d5e6f`. The [blind report](TASK-20261102-1a2b3c/report.md) and [source report](TASK-20261102-4d5e6f/report.md) were filed separately. Both attest no sibling report access. The cross-repository [independence adapter](check_independence.py) maps only field names and returns zero problems with the shared checker; it cannot authenticate private reviewer behavior. Exact commands and output are in [checks.txt](checks.txt).
- The frozen p=67 diagnostic has no run rows because checkpoint upload was denied. Its parent protocol and problem record retain that state. No performance graph is regenerated from an unrun comparison. The cross-field degree graph was checked against its CSV and left unchanged because this proof does not change its data.
- A formal refinement of the Rust validator, LLL output span, Babai choice, ranking, and certifier remains separate. The next gate for this packet is exact-head hosted CI on PR #1377 followed by a main-commit check after merge. The path-scoped proof job cannot be a universal required check for unrelated PRs; repository-wide status policy should use an always-emitted context if the owner wants required proof gating.

[Diagram source](proof-boundary.svg) · [Inspected PDF](report.pdf). This technical review changes no experiment result or official ledger decision.
