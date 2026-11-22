# Cubic residual-output filter gate on N41

**The N41 two-pair output source spans the full 10,701-dimensional space of degree-at-most-three Boolean functions on the subgroup's trace-zero (x)-coordinate hyperplane.** An exact cubic polynomial in (x) that accepts every legitimate two-pair output must therefore accept every target-conditioned residual `Q′−P₁−P₂−P₃` in this five-pair layout. This extends the [degree-two gate](../n41_two_pair_degree2_filter_20261013/RESULT.md) and removes all cubic (x)-only annihilators as a route to family rejection for this source.

## Frozen source and run

The curve is `EC1N41Ckb1h7d5e80d3c4d0`, `y²+xy=x³+1` over `GF(2)[t]/(t^41+t³+1)`, with subgroup order `549756390943`. The public point is `(920359962848,755404565011)`, transformed by the common-Frobenius factor to `Q′=(1099765887764,1148205618145)`. The source contains 30,952 rotation-zero signed W8 diagonal pair states; each is multiplied by four before two states are joined with four distinct folded columns. The [retry protocol](protocol.json) froze the source and binary hashes, 15,000 attempt cap, one worker, 180-second parent cap, 4-GiB memory cap, and the [first-launch failure](../n41_two_pair_degree3_filter_20261013/RESULT.md) before execution. The retry moved the 14.4-MB elimination basis from stack to heap; the source law, RNG, and feature order stayed fixed.

The worker formed all squarefree monomials through degree three in the 40 free (x)-bits, retained only rank-increasing rows, and stopped when rank reached 10,701. Its [native result](native_result.json) records 11,102 attempts, 10,703 valid outputs, 399 column rejects, and full rank after 7.884 seconds of exploratory native wall. The [parent interval](query_receipt.json) was 8.155417 seconds; maximum RSS was 18,120,704 bytes. These timings are local algorithm diagnostics without an isolation receipt.

The [10,701 pivot rows](witnesses.tsv) are a finite rank certificate. Under its [frozen protocol](audit_protocol.json), independent checked Sage reconstructed every selected two-pair group output from 15,405 source states, verified its (x)-coordinate and distinct columns, and repeated elimination with a separately written feature encoder. It obtained [rank 10,701](audit_result.json). The [read-only verifier](verify.py) checks hashes, caps, counts, status, witness shape, and audit linkage.

## Exact implication for target-conditioned filtering

The trace of an (x)-coordinate in this polynomial basis is its constant coefficient bit (x₀). For this binary curve, `x(2P)=λ²+λ`, hence `Tr(x(2P))=0`. Doubling is invertible on the odd-order subgroup, so every subgroup point, including each candidate residual formed from the public target and three projected pair outputs, lies in the hyperplane `x₀=0`.

Squarefree ANF monomials through degree three on the remaining 40 bits form a vector space of dimension `1+40+binom(40,2)+binom(40,3)=10,701`. The selected legitimate two-pair outputs have an evaluation matrix of that full rank. If a cubic polynomial is zero on every legitimate output, it is zero on these pivots; full rank forces its restriction to be zero on the entire trace-zero hyperplane. It therefore rejects no subgroup residual. The [proof map](PROOF_MAP.md) identifies which algebraic implications are Lean-checked and which concrete field and finite-rank bridges remain computational.

## Next method gate

The next target-conditioned constraint must use additional information: source-mask or XOR-seed structure, signed (y)-coordinates, or a higher-degree joint invariant on multiple partial sums. A compact condition should be tested on an unpinned N41 public target for exact family rejection and genuine relation yield, then projected to N131 with full one-worker work and memory before another capped public query. This stage retains `candidate_id: null`; the ordinary N131 relation and the complete single-target/rho comparison remain open.
