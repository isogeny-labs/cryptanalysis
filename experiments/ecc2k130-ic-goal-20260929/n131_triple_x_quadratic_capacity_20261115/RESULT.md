# Quadratic x-feature hull has a 270-family N131 rejection window

On the frozen W23 three-pair source panel, the quadratic bit-feature hull rejects both archived ordinary target residuals through **270** ascending source-valid first-slot families. The independent checked-Sage audit finds that the 271st family brings the hull to full rank **8,646** and admits both ordinary residuals, although neither is an exact x member of the 10,240 values seen through 320 families. The constructed six-pair control passes from the first family. This locates the exact capacity boundary for this fixed-two-slot screen and prevents promoting an unrestricted quadratic hull as a whole-family N131 relation filter.

## Exact panel and method

The curve is `EC1N131Ckb1heb5f1998f20b` over `GF(2)[t]/(t^131+t^13+t²+t+1)` with model `y²+xy=x³+1`. The W23 seed mask is 898618. Slots 1 and 2 are the frozen W23 pair edges from the six-pair panel; the first-slot families are its first four archived source-valid edges followed by ascending source-valid canonical masks starting at 47. The producer requires two distinct folded columns disjoint from fixed slots 1–5. Each first-slot family has four signed pair states; summing with the four states in each of slots 1 and 2 gives 32 distinct x coordinates. The residuals are the constructed control and two previously frozen ordinary raw points after subtracting slots 3–5. Their exact source and target hashes are in the [pre-execution protocol](protocol.json).

For each 131-bit x coordinate, the feature vector contains its 131 bits and all 8,515 products of distinct bit pairs. The gate tests whether a residual's feature vector belongs to the GF(2) affine hull of observed source features. Exact x membership implies hull membership; [the Lean proof](PROOF_MAP.md) records that lossless implication. The producer updates the binary rank and target decisions as source families enter in ascending order; the independent auditor reconstructs all source points and uses a different pivot direction.

| Families admitted | Distinct x values | Linear rank / 131 | Quadratic rank / 8,646 | Ordinary residuals in quadratic hull |
| ---: | ---: | ---: | ---: | --- |
| 1 | 32 | 31 | 31 | neither |
| 5 | 160 | 131 | 159 | neither |
| 64 | 2,048 | 131 | 2,047 | neither |
| 128 | 4,096 | 131 | 4,095 | neither |
| 256 | 8,192 | 131 | 8,191 | neither |
| 270 | 8,640 | 131 | below 8,646 | neither; independently audited first-entry boundary |
| 271 | 8,672 | 131 | **8,646** | both; first entry |
| 320 | 10,240 | 131 | 8,646 | both; exact x membership still false |

The 270 and 271 rows come from [the independent audit](audit_result.json), which checked every family; the other rows are archived producer checkpoints independently matched by that audit. The producer completed in **59.689 s**, with **227,246,080 B** sampled peak self RSS, under the frozen one-worker, 600 s, 4 GiB envelope. The independent full reconstruction took **91.333 s** and reported **250,642,432 B** `ru_maxrss` on this macOS host. These are correctness and capacity measurements on an ordinary shared host, not isolated IC/rho timing. The exact source-family masks, rank checkpoints, target decisions, timestamps, and hashes are in [the result](result.json). `candidate_id` remains null because this is a fixed-slot point-decomposition screen, not a complete candidate pipeline.

## Search decision

The quadratic hull expands the rejection window from four first-slot families for the linear hull to 270 on this exact panel. Its feature rank then saturates, so adding more families to this same hull cannot reject any 131-bit target. The 320-family production cost and the need to keep at least five W23 pair slots jointly unresolved prevent this fixed-slot screen from being a complete ordinary N131 relation algorithm. The next method must retain more algebraic structure across multiple free pair slots or use a nonlinear summary that survives beyond this finite feature rank. A candidate should first demonstrate an unpinned ordinary relation with all source generation and failed-block work charged, then run on the frozen degree-131 public point under the declared cap.

Reproduce with the checked repository launcher after reviewing `protocol.json`: `./sage -python experiments/ecc2k130-ic-goal-20260929/n131_triple_x_quadratic_capacity_20261115/run_sage.py` and `./sage -python experiments/ecc2k130-ic-goal-20260929/n131_triple_x_quadratic_capacity_20261115/audit_sage.py`. Both producers refuse to overwrite their frozen results. The saved `sage_runtime_info.json` was captured before measurement. Run `lean QuadraticHull.lean` from this directory for the proof and axiom audit.
