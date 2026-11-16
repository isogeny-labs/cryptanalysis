# Proof map

The pinned Lean toolchain and dependency revisions are in `formal/lean-toolchain` and `formal/lake-manifest.json`. `formal/build-output.txt` records `lake build FullHitBound` and seven `#print axioms` audits. Each declaration uses only standard Lean foundations: `propext`, `Classical.choice`, and `Quot.sound` as applicable.

| Mathematical result | Lean declaration | Exact assumptions | Status |
| --- | --- | --- | --- |
| No informative equality at seed position 0 | `XedniFullHitBound.execution_hit_zero_false` | Typed program from two points; actual group trace | Checked |
| Seed position 1 equality iff scalar 1 | `XedniFullHitBound.execution_hit_seed_iff` | Field and additive module; injective scalar map; actual trace and distinct seed forms | Checked |
| First hit at position 1 iff scalar 1 | `XedniFullHitBound.execution_first_hit_seed_iff` | Same, with first-hit time defined by the earliest informative equality | Checked |
| No first hit at position 0 | `XedniFullHitBound.execution_first_hit_zero_false` | Typed program and actual group trace | Checked |
| Seed first-hit mass equals encoding count | `XedniFullHitBound.execution_seed_hit_card` | Finite field, group and labels; finite bijective encoding type; injective scalar map | Checked |
| Full first-hit count decomposes into seed and late stages | `XedniFullHitBound.execution_total_hit_decomposition` | Same finite model; stages `0≤k<m` | Checked |
| Complete finite first-hit inequality | `XedniFullHitBound.execution_all_hit_bound` | Same model; arbitrary label-adaptive add/subtract program; one fallback label for the prior late-stage theorem | Checked |

The program's group-operation semantics, `groupRawHit` event, and full execution space `F × (A ≃ L)` are inherited from the pinned predecessor modules. The theorem counts each execution at its earliest informative hit. The probability expression in `RESULT.md` follows by division when `q>m²` and the encoding set is nonempty; the Lean declaration states the stronger exact integer inequality.
