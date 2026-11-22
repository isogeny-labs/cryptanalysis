# One-sided GCD decides complete N41 source-product fibers

**A one-sided polynomial GCD decides all four frozen N41 source-product fiber sizes, including the complete 32-by-32 bins.** It enumerates products from one seed bin while keeping the other bin in a single reusable membership polynomial; it does not expand their Cartesian product during the query. On the complete size-32 positive and negative fibers, the exact target test took **0.278 s** and **0.244 s** internally, respectively. Independent checked-Sage group arithmetic evaluated **43,520 signed assignments** across the panel, found two witnesses for every positive fiber and none for every negative fiber, and agreed with all eight GCD decisions.

The fully symbolic nested resultant agreed through size 16 but both size-32 cases reached their 45-second wall caps. The GCD refinement avoids its degree-`8k` intermediate polynomial while preserving the exact source-fiber predicate. It is a stage improvement on this N41 input, with the N131 family-generation and one-target work still to be bounded.

## Method and frozen input

The curve is `EC1N41Ckb1h7d5e80d3c4d0` over `GF(2)[t]/(t^41+t^3+1)` with `y²+xy=x³+1`. The source is the frozen four-pair diagonal-point public relation, restricted to its last two rotated pair slots, rotations 14 and 21. Their positive seed XORs are fixed from the witness and each complete bin has 32 distinct source mask pairs. The [panel](panel.json) orders the positive mask pair first in each bin, then the remaining pairs lexicographically; sizes 4, 8, 16, and 32 are nested. It fixes the known right-block reciprocal x coordinate and a separate SHA-256-derived coordinate before any resultant run. This is a partial-sum stage (`candidate_id: null`).

For rotated seed values `a,b`, allowed rotated pair products `P={p_i}` and `Q={q_j}`, and proposed right-block reciprocal coordinate `z`, form

`G_P(p)=∏_(p_i∈P)(p+p_i)`, `G_Q(q)=∏_(q_j∈Q)(q+q_j)`.

Let `H(a,b,p,q,z)` be the [previously checked 266-term four-atom resultant](../n131_w15_rotated_fouratom_inverse_20261010/resultant.json). The family predicate is

`R(z)=Res_q(G_Q(q), Res_p(G_P(p), H(a,b,p,q,z)))`.

Because the two source polynomials split into distinct linear factors over the field, `R(z)=0` exactly when some allowed product pair `(p_i,q_j)` satisfies `H(a,b,p_i,q_j,z)=0`. The first elimination is a polynomial in `q`; its observed degree is `8k` for bin prefix size `k=4,8,16`. The product polynomials are target-independent source data, while specialization of `H` at `z` and both eliminations are target dependent in the measured script. Source-product roots are constructed in the script's build phase, so that phase was charged rather than silently treated as precomputation.

The refinement keeps `G_Q(q)` and evaluates the degree-at-most-eight polynomial `H(a,b,p_i,q,z)` once for each `p_i∈P`. It accepts exactly when `gcd(G_Q(q),H(a,b,p_i,q,z))` has positive degree for some `p_i`. Since `G_Q` splits into the allowed `q_j` roots, this is the same existential condition as the nested resultant. The known positive product was moved to the **last** tested position, so its measured row does not benefit from witness-first ordering. The [hybrid protocol](hybrid_protocol.json) freezes its source, the independent audit, case order, one worker, and a 180-second/4-GiB run cap before execution.

The [protocol](protocol.json) froze source hashes, exact panel, runtime, case order, one worker, a 45-second wall cap per case, and 4-GiB monitored process-tree RSS. All local Sage jobs used the checked repository launcher; its [runtime receipt](sage_runtime_info.json) precedes the cases.

## Results

| Fiber size per seed | Coordinate | Group-law matches | Symbolic status | First resultant | Total internal time | Parent wall | Peak RSS |
| ---: | --- | ---: | --- | ---: | ---: | ---: | ---: |
| 4 | positive | 2 | `EXIT_0`, zero | 0.605 s | 0.717 s | 12.587 s | 270.2 MB |
| 4 | negative | 0 | `EXIT_0`, nonzero | 0.603 s | 0.725 s | 8.186 s | 269.2 MB |
| 8 | positive | 2 | `EXIT_0`, zero | 4.273 s | 4.348 s | 7.590 s | 284.8 MB |
| 8 | negative | 0 | `EXIT_0`, nonzero | 4.016 s | 4.119 s | 8.269 s | 282.3 MB |
| 16 | positive | 2 | `EXIT_0`, zero | 33.906 s | 34.029 s | 37.870 s | 345.2 MB |
| 16 | negative | 0 | `EXIT_0`, nonzero | 32.654 s | 32.794 s | 37.595 s | 345.6 MB |
| 32 | positive | 2 | `TIMEOUT_45S`, bounded unknown | unknown | unknown | 45.034 s | 303.0 MB |
| 32 | negative | 0 | `TIMEOUT_45S`, bounded unknown | unknown | unknown | 45.076 s | 336.1 MB |

The internal totals include source-product polynomial construction and both eliminations; they exclude checked-Sage launch and import. The parent wall includes those costs. Per-case JSON results, stdout/stderr, and `case_*_run_status.json` retain every completed or capped attempt. The [independent audit](audit.json) rebuilt diagonal source points from the archived geometry and used only curve addition, signs, rotations, and the proposed reciprocal coordinate to count group matches. Its [run receipt](audit_run_status.json) records 4.044 s parent wall and 269,615,104 B sampled peak RSS. CPU times are exploratory without a host-isolation receipt; the terminal statuses and exact decisions are the primary evidence.

| One-sided GCD size | Positive decision / GCDs | Negative decision / GCDs | Positive internal | Negative internal |
| ---: | --- | --- | ---: | ---: |
| 4 | hit / 4 | miss / 4 | 0.106 s | 0.047 s |
| 8 | hit / 8 | miss / 8 | 0.051 s | 0.051 s |
| 16 | hit / 16 | miss / 16 | 0.101 s | 0.114 s |
| 32 | hit / 32 | miss / 32 | 0.278 s | 0.244 s |

The frozen [GCD result](hybrid_result.json) records construction and GCD time separately for all eight cases. Its [parent receipt](hybrid_run_status.json) records `EXIT_0`, 7.299 s wall including Sage startup, and 252,510,208 B sampled peak RSS. At size 16, the paired symbolic/GCD internal ratios are about 335 for the positive coordinate and 288 for the negative coordinate on this unisolated host. No ratio is assigned at size 32 because both symbolic runs are censored.

## Proof and transfer boundary

The readable proof of the family predicate is the product formula for resultants over a splitting field, applied first to `G_P` and then to `G_Q`: each resultant is a nonzero leading-coefficient power times the product of evaluations at its source roots, and a product in a field is zero exactly when one factor is zero. The existing checked Lean theorem [`JointNorm.joint_zero_iff`](../n41_joint_fourpair_resultant_20261012/JointNorm.lean) proves the finite-root zero equivalence under explicit integral-domain hypotheses, with only standard `propext` and `Quot.sound` axioms. The [proof map](PROOF_MAP.md) records the still-open formal bridge from Sage polynomial resultants to this product identity and from `H` to the concrete curve-law source. The 43,520 group checks are independent concrete validation, not a general formal curve proof.

For the GCD refinement, the proof is direct: over a field, a nonconstant GCD of `G_Q` and `H(p_i,q,z)` exists exactly when they share a root in an algebraic closure; every root of the split polynomial `G_Q` is an allowed `q_j` in the original field. Therefore the GCD loop returns true exactly when an allowed product pair makes `H` vanish. The finite-list existential step is the same checked Lean theorem; formalizing the polynomial-GCD root bridge remains open.

The N131 W18 fixed-seed source has **33,191** admissible pair codes per slot in the existing frozen circuit. A literal first eliminant at the observed degree pattern would have degree up to `8×33,191=265,528` in the second product variable, before the second elimination. The GCD variant replaces this polynomial with **33,191** exact small-degree GCD queries for one offered output, but the target-dependent algorithm must still generate useful offered outputs and seed families. The N41 size-32 GCD timings cannot be transferred to N131 field arithmetic or multiplied into a complete search estimate. The next falsifiable step is to generate target-derived block outputs while at least two source-pair slots remain unresolved, then measure how many whole N131 seed families the GCD rejects per charged query and whether the complete source-bound work fits one worker, 600 seconds, and 4 GiB. The existing unpinned N41 relation and independent replay remain the promotion control.
