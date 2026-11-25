# TASK-20261102-4d5e6f: source and proof-gate fidelity

## Bound inputs and result

I reviewed the producer source at `d243c3ce88e077a593c3be2c2ba502d976564534` and the named merge commit `749d807be2c82175641c17c589e6883ba8b10abb`, against precommitted plan `3b5ba368fc1718c62f6f8e376a36275736ff50d90f8a2e78f15483dab017bf72`. The receipt names source commit `545de2e1c91a301b342b45317f402be4497647ba`; the reviewed Lean and Rust bytes at `d243c3c` match the receipt hashes: Lean `c39148eaf547acb4f8ea7c752413a83946b43557181ef55da86ac3f5f466e757`, Rust `b08c94845e9b4ed9660bd01aff01b2e59d274d0f7806a4ddf48ef3d35541ac96`, toolchain `d5edba4e4b8faad9c1baeadb265716d20d03be4d1a2647dc5e35b0c0325bea7b`. The Rust LLL module hash at the reviewed revision is `0687b6c0c20a61300023d96ac83de271adc0fc1e1a372114acd5ed7a83dd6c0b`, but is outside the receipt.

**Joint verdict: breaks for the merged hosted gate; holds for the stated conditional algebra and the inspected Rust integer-span path.** The named merge tree retains the first-use elan failure mode. The successful hosted run checks a different, unmerged workflow head. This does not refute the Lean theorem.

## Theorem-to-source trace

* `XedniAffineCoset.lean:20-29` defines a finite integer dot product and `u + Σ cᵢDᵢ`. `:99-114` proves closure of kernel rows and zero remainders under integer combinations. `:118-153` proves row equality and coefficient-difference divisibility/remainder for every finite list of directions satisfying the premises. The `q > 0` parameter is passed but not used in the proof; this is a redundant hypothesis, consistent with Rust's stricter positive-modulus validation. The theorem has no assertion about finding directions, rank, scoring, or optimizing.
* `xedni_lift.rs:303-340` checks dimension, nonzero directions, row lengths, every row/direction dot product, and positive `q` plus every direction's zero remainder when a modulus exists. `:410-422` forms the same coordinatewise affine sum, pairing basis rows with search coefficients by `zip`; `:517-527` validates before cloning directions and calling `lll_reduce_hp`. Babai returns integer coefficients, and the bounded search adds integer deltas (`:356-407, 463-489`). Dimension checks make the `zip` truncation in `affine_candidate` harmless on this path.
* `lattice.rs:135-269` mutates the basis only by `basis[k][i] -= q_bi * basis[j][i]` with `q_bi : BigInt` (`:183-199`) and by row swap (`:225-229`). Gram–Schmidt and its incremental updates affect choices, not basis entries. The iteration-cap and malformed-input paths return `Err`; `optimize_affine_lift` propagates it at `xedni_lift.rs:524`. Thus each successfully returned post-LLL row is an integer combination of validated input rows by source-level induction over these mutations. This bridge is **source inspected**, not a Lean theorem about Rust or a tested full implementation refinement.
* `xedni_lift.rs:424-436, 550-565` certifies the selected result against the original exact rows and optional modulus and returns `Err` if either check fails. It does not separately certify the reported Babai vector at `:527-528`; the same source-level span argument applies to it. The theorem's residue conclusion applies when `Some(q)`; with `None`, Rust's congruence flag is vacuously true and no Lean modulus conclusion is needed.
* The proof map's `README.md:42-52` explicitly leaves parser, Rust control flow, LLL output-span invariant, Babai, discriminant, ranking, and certifier as separate implementation obligations. The Lean theorem covers arbitrary dimension, including the seven- and ten-coordinate modes; the Rust entry points fix those dimensions at `xedni_lift.rs:568-592, 801-834`.

## Machine checks and controls

I materialized only the five pinned inputs (`lean-toolchain`, Rust source, Lean source, `check.py`, `receipt.json`) from `d243c3c` in a disposable tree and used installed Lean 4.34.1. The exact checker passed, printing only three axiom audit lines and its success line. All three named declarations reported exactly `[propext, Quot.sound]`; no `sorryAx` or custom axiom appeared. This is a fresh local check of the declarations and receipt, not an independent kernel binary recheck.

Two checker controls in the disposable tree behaved as expected:

| Control | Result |
| --- | --- |
| Append a comment to pinned Rust source, leaving receipt unchanged | Exit 1; Rust SHA-256 mismatch |
| Add `sorryAx` to the receipt axiom list, leaving Lean unchanged | Exit 1; Lean axiom audit mismatch |

The checker (`check.py:27-51`) hashes the Lean module, `xedni_lift.rs`, and `lean-toolchain`; checks the declared toolchain string; executes Lean; rejects nonzero exit, any stderr, unexpected stdout, and an axiom map differing from the receipt. Its `source_commit` field is metadata only: the checker does not verify Git ancestry or revision, and the receipt/checker/workflow/LLL source are not themselves hash-bound by this script. A modified receipt and source together could change the accepted axiom policy; the read-only CI checkout and review of committed bytes are the relevant external trust boundary. The axiom parser matches the three printed names and their exact lists, but it does not audit declarations without `#print axioms` calls.

## Hosted workflow discrepancy

Run [41505293019](https://github.com/isogeny-labs/cryptanalysis/actions/runs/41505293019) at producer head `d243c3c` failed with Lean exit 0 because first-use elan download messages were on stderr, which `check.py:41-42` treats as failure. Run [41505647909](https://github.com/isogeny-labs/cryptanalysis/actions/runs/41505647909) succeeded at `196aa0de1cbca4c975c736e83f6f27ceef941777` after an explicit `elan toolchain install` step. The named merge commit `749d807` has parents `545de2e` and `d243c3c`, and its workflow tree still has no download step (`.github/workflows/xedni-affine-coset-lean.yml:35-46`). `196aa0d` is not an ancestor of `749d807`. Therefore the successful hosted job does not verify the exact merged workflow; a clean runner executing the merged workflow can reproduce the earlier infrastructure failure. The merge's PR/push path filter also omits `suite/src/cryptanalysis/lattice.rs`, although that file supplies the load-bearing integer-span bridge.

## Scoped conclusion and next action

The conditional finite integer affine-coset theorem is machine checked on pinned source and matches the inspected candidate construction and validation premises. The post-LLL span property follows from the reviewed Rust row mutations, but has no formal implementation proof or CI source binding. Repair the merged workflow by adding the pre-download step, include `lattice.rs` in the workflow trigger and checkout/hash policy, then obtain an exact-merge-or-descendant hosted check before describing the merged gate as passing. Preserve the existing successful run as evidence for its actual head.
