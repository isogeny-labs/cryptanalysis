# Proof map

The source-set counts are executable certificates tied to the frozen
`support_w20.tsv`, not Lean proofs of the elliptic-curve source construction.
The independent Python/NumPy audits reconstruct the source set from the
support table and replay the selected occupancy counts. `audit.py` replays all
171 coordinate two-bit partitions; `affine_audit.py` replays all 524,287
one-direction autocorrelations and all 2,016 searched two-planes.

| Mathematical statement | Lean declaration | Exact assumptions | Status |
| --- | --- | --- | --- |
| The sum of pair assignments over rectangular occupancy bins equals the product of the two total occupancies | `RectangleWork.ordered_pair_work` | Two arbitrary lists of natural-number occupancies | Checked |
| For equal source sets of size `S`, partitioning into rectangular bins preserves `S*S` ordered assignments | `RectangleWork.same_slot_pair_work` | Occupancy list sums to `S` | Checked |

These Lean statements prove the structural counting implication used in the
report. The bridge from actual W20 source masks to the enumerated occupancy
lists is audited by `audit.py` and `affine_audit.py`, and remains computational
rather than formalized in Lean. The theorem does not assert any number of
field multiplications for an arbitrary algebraic algorithm.

Pinned toolchain: `leanprover/lean4:v4.34.1` in `lean-toolchain`. Build from
this directory with `lean RectangleWork.lean > lean_check.txt 2>&1`.
`#print axioms` for all three declarations reports only `propext`.
`lean4checker --fresh` was unavailable in the local environment.
