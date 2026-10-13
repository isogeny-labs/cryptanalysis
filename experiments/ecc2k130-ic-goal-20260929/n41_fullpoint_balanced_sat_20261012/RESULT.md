# Full-point N41 addition circuit compresses the balanced public formula

**The full-point balanced-tree circuit reduced the frozen N41 ten-pair public formula from 289,065 to 33,868 variables and from 160,407 to 16,956 AND gates.** It carries both affine coordinates through nine addition links, using the source pair's signed point rather than a reciprocal x-coordinate and a later sign lift. The known ten-pair public relation satisfies every emitted row, and an independent audit reconstructed all nine curve additions. The one-worker pinned control and unpinned public query remained active until their respective 30- and 180-second parent caps, preserving an exact solver boundary for this smaller encoding.

## Frozen method

The field is `GF(2)[t]/(t^41+t³+1)`, the curve is `y²+xy=x³+1`, the subgroup order is `549756390943`, and the cofactor is four. The public point is `(920359962848,755404565011)` on `EC1N41Ckb1h7d5e80d3c4d0`. The source and public input are exactly those of the prior [functional reciprocal-only formula](../n41_w8_tenpair_functional_20261012/RESULT.md): ten signed W8 pair slots, 140 states per slot at rotations `(0,7,14,21,28,35,0,7,14,21)`, ten distinct source edges, and all four raw preimages of the public point. The control pins the ten known state choices and one raw-preimage flag; every slope and internal point remains free to the solver. The public formula pins none of these choices. This remains a component design with `candidate_id: null`.

At each tree link with points `P=(x₁,y₁)`, `R=(x₂,y₂)`, and output `S=(x₃,y₃)`, the circuit requires `x₁+x₂ ≠ 0` and introduces a slope `λ` satisfying

`λ(x₁+x₂)=y₁+y₂`, `x₃=λ²+λ+x₁+x₂`, and `y₃=λ(x₁+x₃)+x₃+y₁`.

Over the declared field, the first equation uniquely sets `λ=(y₁+y₂)/(x₁+x₂)` on this chart. The latter two are the affine addition formulas for this curve. The nine-link tree ends with equality to one selected full raw-preimage point, including its y-coordinate. This chart excludes branches with equal input x-coordinates; the positive relation has no such branch. The [Lean proof map](PROOF_MAP.md) separates the checked nine-link structural implication from the remaining formal field/curve and CNF-emission bridges.

The [protocol](protocol.json) froze the runner, input, known relation, prior builder, solver, target, one-worker policy, 4-GiB combined RSS ceiling, and both parent caps before the run. Formula construction, known-assignment checking, and serialization were measured separately from solver search. CPU timings are exploratory on an unisolated host.

| Frozen N41 formula | Prior reciprocal-only public | Full-point public |
| --- | ---: | ---: |
| Variables | 289,065 | **33,868** |
| AND gates | 160,407 | **16,956** |
| CNF clauses | 604,526 | **174,583** |
| Native-XOR rows | 127,245 | **14,401** |
| Serialized XCNF | 14,922,651 B | **3,108,600 B** |
| Unpinned solver status | `BOUNDED_UNKNOWN` at 180.025 s | `PARENT_TIME_CAP` at 180.036 s |

| New frozen arm | Known assignment checked | Parent solver wall | Sampled combined RSS | Restart rows | Terminal status |
| --- | --- | ---: | ---: | ---: | --- |
| Pinned source and target control | 174,594 CNF and 14,401 XOR rows | 30.016 s | 121,143,296 B | 593 | `PARENT_TIME_CAP`, no SAT/UNSAT line |
| Unpinned public point | 174,583 CNF and 14,401 XOR rows | 180.036 s | 166,789,120 B | 1,417 | `PARENT_TIME_CAP`, no SAT/UNSAT line |

The [independent archive audit](audit.json) rechecks input and formula hashes, both XCNF headers and all row counts, the exact eleven control-only unit clauses, raw solver logs and terminal statuses, ten distinct source edges, and all nine positive group additions with separate integer-field arithmetic. `verify.py` can now replay those checks read-only against the immutable first audit receipt. The [control](control.json) and [public](public.json) receipts retain commands, phase boundary, resource peaks, exits, and log hashes. `FullPointTree.lean` was checked with Lean 4.34.1; [the output](lean_check.txt) reports only `propext` under `#print axioms`.

## Next gate

The current free-slope formulation is compact but its pinned positive control did not close under 30 seconds. The next refinement is a **functional slope**: derive each slope from the nonzero x-difference with an exact inverse circuit, then compare the pinned and unpinned N41 searches on the same public point and source. A successful unpinned relation must be independently replayed for raw group sum and folded columns. Only a source-bound compact W18 construction with projected complete work below 600 seconds and 4 GiB warrants an N131 public-point run. The single-target IC comparison remains governed by the repository measurement contract.
