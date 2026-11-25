# CT324 — batched-affine rho implementation and falsification gates

**Standing:** [pcc:unverified]. Existing draft PR #1920. Source/correctness study, not a speedup result.

## Construction
The unchanged CT323 rho control computes a field inverse for each nontrivial affine addition. CT324 adds ct324_batch_inverse.rs, a Montgomery prefix/suffix product trick, and ct324_prime31_batched_rho.rs, a 16-lane public-only rho candidate that reuses the same kernel.

For nonzero denominators d_0,...,d_{k-1}, compute prefixes P_i=product_{j<i}d_j, invert P=product_j d_j once, and recover inverses in reverse: inv(d_i)=P_i*(P^{-1} product_{j>i}d_j). The recurrence updates the inverse accumulator by multiplying by d_i. Identity and vertical cancellations bypass the product. This construction does not change the Weierstrass group law.

The native rho candidate retains CT323's 32-point public additive jump table, coefficient invariant aG+bQ, canonical distinguished-point collision test, bounded 8192-step per-lane resets, 64*ceil(sqrt(n)) aggregate step cap, 65536-entry memory cap and mandatory group-equation verification. It uses 16 independent walkers and one batch inversion per nonempty wave. The distinguished threshold changed from 1/16 to 1/64 to avoid saturating the table at the aggregate cap; therefore walk distributions are NOT claimed identical to CT323.

## Independent arithmetic check (not native execution)
Separately coded Python affine arithmetic for the original prime31 curve p=2147483647, a=847514846, b=2087444724, G=(625037715,2100627251) reproduced 16 distinct successive points and checked all 225 nontrivial denominators in the 16x16 pair grid using one batch inversion. This checks the algebra, not compiled Rust behavior or performance.

## Frozen source correctness gate
Four Rust arithmetic tests exercise all 25 toy pairs, the full prime31 256-pair grid, identity-only batches, and vertical/identity/doubling exceptions. A source-pinned GitHub Actions workflow compiles both opt0/opt3 Rust test binaries and executes toy/principal-curve known-answer logarithm-2 smoke controls on the standalone batched rho binary. Its outcome must be inspected before native correctness can be claimed.

## Follow-up and success criteria
1. Reject any failed source or known-answer test; preserve failure receipts.
2. Compare independently verified blinded public rho solves against CT323 and strongest applicable optimized rho, matched BSGS and frontier IC under same-host ABBA and complete cold wall/RSS/counters.
3. Count all setup/jump construction/recovery/verification; run A/A and repeat independent hosts with uncertainty.
4. Rejoin the actual native 695/701 model and physical C169/C13a/C13b/D/N2_actual only after owner-approved six-object S3 custody and tool/config reconciliation.

No qualified complete single-target speedup, paid compute, protected merge or signed PCC is claimed.
