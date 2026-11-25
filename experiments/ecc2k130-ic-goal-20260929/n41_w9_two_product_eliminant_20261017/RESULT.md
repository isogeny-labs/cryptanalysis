# Target-conditioned two-product eliminant and subspace root search

A public N41 residual, with three of five aligned pair slots fixed, admits a **13-term bidegree-(4,4) eliminant** in the two remaining source products. A linearized polynomial for the 8-dimensional right-product subspace turns each specialized quartic into a constant-degree GCD. On all 71 left codes, this found the same unique relation as exhaustive signed-state group addition. Four frozen in-process N41 stage runs gave 0.800–0.868 s for GCD plus root extraction and 4.624–4.637 s for direct evaluation of all 256 subspace elements, a descriptive 5.3–5.8-fold stage reduction. This is the first compact target-conditioned constraint in this branch that jointly rejects families of two unresolved pair outputs while preserving the archived ordinary relation.

## Exact instance and method

The field is `GF(2)[u]/(u^41+u^3+1)`, the curve is `y²+xy=x³+1`, and the curve ID is `EC1N41Ckb1h7d5e80d3c4d0`. The source is the frozen aligned W9 family with 71 canonical valid codes per slot, rotations `(0,0,12,12,24)`, and public orientation 6. Slots 0, 3, and 4 are fixed **retrospectively** to state IDs `(105,47,111)` from the archived ordinary relation. The two unresolved slots are 1 and 2; each code has four signed states. Their fixed-seed products are `p=a(a+s)` and `q=Frob^12(a(a+s))`. The target-dependent residual is `T=Q-P₀-P₃-P₄`, with reciprocal `t=1/x(T)`.

For reciprocal pair outputs `a,b`, the fixed-seed quadratics are `C₁a²+pa+H₁=0` and `C₂b²+qb+H₂=0`. In the nonexceptional chart for the elliptic point sum, `S3(a,b,t)=0` becomes `Ab²+Bb+D=0`, with `A=1+(at)²`, `B=at`, and `D=a²+t²`. Its quadratic resultant with the second pair equation is

`G(a,q)=M²+LN`, where `M=AH₂+C₂D`, `L=Aq+C₂B`, and `N=BH₂+qD`.

Reduce `G` modulo the first pair equation to `r₀(p,q)+r₁(p,q)a`. Its norm is the eliminant

`H(p,q)=C₁r₀²+pr₀r₁+H₁r₁²`.

The producer found 13 nonzero monomials at exponent pairs `(0,0),(0,2),(0,4),(1,1),(1,3),(2,0),(2,2),(2,4),(3,1),(3,3),(4,0),(4,2),(4,4)`. Thus `H=E(p²,q²)+pq·O(p²,q²)`. Independent nested polynomial resultants reproduced every coefficient after the recorded normalization by `C₁³`; the exact coefficient list is in [result.json](result.json).

The source-product map `a↦a(a+s)=a²+sa` is binary-linear. The right products lie in an 8-dimensional subspace `V` with 256 elements. A 9-coefficient linearized annihilator `L_V(X)=Σ_{i=0}^8 cᵢX^(2^i)` was constructed recursively by `L_{V+⟨v⟩}(X)=L_V(X)²+L_V(v)L_V(X)`. For each left product `p`, the root method computes `gcd(H(p,X),L_V(X))` with `L_V` reduced modulo the quartic during evaluation. A deterministic trace splitter extracts roots only from that GCD. The roots are then mapped to valid right codes; exact point addition verifies surviving signed-state assignments.

## Frozen measurements and independent replay

| Work | Exact boundary | Result |
| --- | --- | --- |
| Eliminant producer | Target setup, symbolic build, 5,041 product pairs, exact witness replay | 0.2501 s, 0.0091 s, 4.8523 s, 0.00015 s; 5.1116 s sum; 264 MB peak RSS |
| Independent group audit | All 5,041 product pairs and 80,656 signed assignments | One zero code pair `(61,16)`, one witness state pair `(244,66)`; 4,550 column-eligible product pairs |
| Independent algebra audit | Literal nested resultants, exact finite-field coefficient comparison | All 13 terms equal; first resultant degree 4; 0.329 s |
| Direct subspace scan, ABBA runs 1/4 | 71 left quartics × 256 subspace values | 4.624/4.637 s; one field root |
| GCD plus trace extraction, ABBA runs 2/3 | 71 quartics; 9 linearized coefficients; constant-degree GCDs | 0.868/0.801 s; total GCD degree 1; one field root; 227 MB peak RSS |
| Independent integer-field replay | Python GF(2^41), all 18,176 left/subspace evaluations | Same sole root and valid code hit; 4.454 s |

The in-process timings exclude Sage startup and runtime validation, and use an ordinary shared host. The GCD-vs-scan ratio is a stage diagnostic within this fixed three-slot workload. All Sage processes used the checked repository launcher with saved runtime receipts. The root experiment was a single process with a 180 s wall timeout; its observed 227 MB RSS stayed below the 4 GiB research envelope, but that envelope was not enforced by the OS. The result retains `candidate_id: null` because these fixed slots are retrospective and this stage does not define a complete IC pipeline or a fresh single-target comparison.

The first generic Sage root routine aborted in NTL (`exit_code=134`); [failure receipt](root_probe_failure_v1.json), stdout, stderr, protocol, and source are retained. Version 2 used modular GCD plus deterministic trace splitting and passed. The first nested-resultant audit stopped while serializing a Sage integer after coefficient comparison; its recorded `PRODUCER_FAILURE_SERIALIZATION` was corrected in version 2 without replacing the failure evidence.

## Formal proof map

[TwoProductEliminant.lean](TwoProductEliminant.lean) builds under pinned Lean 4.34.1. `quadratic_common_root` proves `M²+LN=0` for two characteristic-two quadratic equations with a common root. `linear_remainder_norm` proves `H(p,q)=0` when the source quadratic and its linear remainder have a common root. `two_product_sound` composes them under the explicit polynomial-remainder identity. The [Lean output](lean.stdout) reports only `propext`, `Classical.choice`, and `Quot.sound` for each theorem; stderr is empty. The [independent resultant audit](resultant_audit_result_v2.json) establishes the concrete polynomial-remainder coefficients for this N41 field. A Lean polynomial-division bridge to the concrete S3 and curve-point objects, and a Lean proof of the linearized annihilator recurrence, remain open; the written formulas and exact computational checks above preserve those obligations. `lean4checker --fresh` is unavailable on this host.

## N131 cost gate and next experiment

The aligned N131 W29 source has 28 free canonical code bits and rank-28 pair-product subspaces, so the same compact GCD idea would use a 29-coefficient linearized polynomial rather than enumerate `2^28` right products. The audited 65,536-mask N131 source sample has 16,677 valid pairs. Applying that **sample rate as a projection**, not as a proven population count, gives about 68.3 million valid left codes. A 600 s run would require about **113,848 specialized quartics per second**, before the outer search over the three currently fixed slots. The measured N41 GCD stage handled roughly 82–89 quartics per second with 9 coefficients. This gap and the still-fixed three slots prevent promotion to an N131 public-query run on the present implementation.

The next discriminator is a three-product constraint with only two fixed slots, together with a native GF(2^131) modular-GCD microbenchmark on a frozen sample of ordinary W29 codes. Its gate is whether the target constraint rejects whole three-product families early enough that outer-slot work and the full one-worker 600 s/4 GiB budget can be charged. The final comparison requires an unseen public target, complete relation generation through target recovery, independent scalar replay, and a same-point rho online interval under the repository isolation contract.
