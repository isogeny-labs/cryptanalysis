# CT324 — Batched-affine rho primitive (prospective)

Standing: [pcc:unverified]. Continuation of CT323 on existing draft cryptanalysis #1920. No claim of a faster complete ECDLP solver.

## Hypothesis
The CT323 rho walker uses one Fermat field inversion for nearly every nontrivial affine addition. For W independent walkers at identical prime p, the same affine additions can be evaluated by Montgomery batch inversion with one field inverse and O(W) extra field products. Preserve the CT323 jump-partition formula, raw coefficient invariants aG+bQ, canonical distinguished-point test and verified discrete-log recovery. Do not substitute a changed partition rule without an independently paired protocol.

## Frozen first gate
1. Add a standalone Rust group-addition primitive with a batch of arbitrary pairs, returning precisely the same results as the unchanged affine baseline on every tested group input. Include identity, inverse/vertical, doubling, and mixed ordinary cases. Use a separate control implementation for comparison.
2. Test the toy F97 order-5 group exhaustively, plus the unchanged CT322 ordinary F(2^31-1) source at a fixed 16-pair sample. Execute native rustc --test on the actual PR head; report compile/test errors as failures.
3. Count inversions per batch only when at least one denominator is nonzero. Compare with summed per-pair inversions. The count is a component statistic, *not* wall time, and setup/verification costs are excluded only from this controlled equality experiment.
4. Integrate this primitive into 16-lane public-only rho while preserving the exact CT323 source curve, public challenge generation and scalar verification. Later run a separately frozen same-host ABBA full cold solve vs CT323 and strongest optimized rho/BSGS/IC; retain failures and RSS.
5. No native benchmark execution until source gate passes. No original 695/701 model, approved S3 admission, paid cloud, key material, protected merge, or PCC standing is implied.

## Kill gates
A wrong group sum, division-by-zero, noncanonical field element, counter mismatch, or native build failure stops this candidate. A component inversion reduction without a **fully charged** cold cost improvement cannot be promoted as a solver speedup.
