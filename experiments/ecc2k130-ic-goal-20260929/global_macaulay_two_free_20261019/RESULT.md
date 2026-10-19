# Two-free-code Macaulay degree-seven boundary

The exact N41 two-pair resultant has Boolean degree four when both ten-bit source-product codes remain free. On a frozen ordinary residual with **no unrestricted-code resultant root**, its complete degree-seven Macaulay matrix does **not** contain the constant polynomial. A saved dual functional annihilates every one of the 55,391 generated rows and evaluates the constant row to one; an independent replay checked those 55,392 parity statements. This is an exact, target-conditioned whole-domain certificate *boundary*: the specified low-degree Macaulay linearization cannot by itself reject this ordinary two-code family. The result directs the next solver toward source-validity constraints, a different joint eliminant, or higher-degree reasoning before N131 promotion. This component has `candidate_id: null`.

## Exact instance and method

The field is `GF(2)[u]/(u^41+u³+1)`, the curve is `y²+xy=x³+1`, and the curve ID is `EC1N41Ckb1h7d5e80d3c4d0`. The fixed seed is `112`. The first and second pair products use Frobenius rotations 12 and 24 and ten free code bits each. The frozen 13-term bidegree-(4,4) resultant `F_R(p,q)` is in the hashed [input table](../n41_w11_freecode_resultant_20261018/resultant_input.tsv). Residual index 0 is the constructed control containing the independently replayed code pair `(253,63)`; residual index 1 is the ordinary target-derived point `(1537610160516,1106209404072)`. The prior exhaustive unrestricted-code census found one zero pair on index 0 and zero on index 1 across all `1024²` code pairs per residual.

Each source product is binary linear in its ten code bits. Binary squaring preserves linearity; a cube has Boolean degree at most two. Substituting both products into the resultant therefore gives 41 Boolean coordinate equations of degree at most four in 20 free bits. For a Macaulay multiplier degree `s`, the experiment multiplies each equation by **every** squarefree monomial of degree at most `s`, reduces with `xᵢ²=xᵢ`, and asks whether the constant polynomial belongs to their GF(2) row span. For `s=3`, the matrix has `41·(1+20+190+1140)=55,391` rows and `Σ_{j=0}^7 C(20,j)=137,980` columns.

| Residual and multiplier degree | Rows visited | Rank | Constant in span | Worker wall | Raw peak RSS |
| --- | ---: | ---: | --- | ---: | ---: |
| Constructed, `s≤2` | 8,651 | 8,651 | no | 8.709 s | 297,762,816 B |
| Ordinary, `s≤2` | 8,651 | 8,651 | no | 11.153 s | 296,550,400 B |
| Ordinary, `s=3` complete matrix | 55,391 | 55,227 | no | 112.693 s | 931,938,304 B |
| Independent ordinary `s=3` rebuild | 55,391 | 55,227; augmented rank 55,228 | no | 111.381 s | 960,069,632 B |
| Dual witness extraction | 55,391 | 55,227 | no | 120.842 s | 961,085,440 B |
| Independent dual parity replay | 55,391 | — | all rows zero; constant one | 18.073 s | — |

The degree-zero, one and two stages have ranks 41, 861 and 8,651 on both residuals. The ordinary degree-three multiplier stage has 164 row dependencies, yet the constant row increases rank by one. The dual witness has weight 27,832 in the declared 137,980-column order. Its parity replay is the direct certificate for the stated absence of a constant-one row-span proof. The producer and independent auditor built the same 3,046-nonzero-term Boolean polynomial with SHA-256 `0035bf76a8d8a8de4fdd774ee35f67c9237f213a8bc6eace7334ecc922c18e9c`, using separate field multipliers and monomial constructions.

All completed workers used one process, a frozen 180-second wall cap and 4-GiB RSS limit, and ran on an ordinary shared host. The first independent audit used a slower monomial order and reached its **180-second wall cap** before rank completion; its raw `audit.stderr` is retained and its outcome is `WALL_CAP_PARTIAL_AUDIT`. The later independent audit and dual replay passed. These are component and proof diagnostics, not a single-target IC timing. The original frozen runs occurred under `/private/tmp/ecc2k130-global-macaulay-20261019`; every source, protocol, result and raw log was copied byte for byte here. [The terminal verifier](terminal_result.json) maps the original paths to the committed copies and checks their hashes and statuses, without representing the copies as fresh runs.

## Scaling consequence and next test

The analogous unfiltered degree-seven monomial domain has **268,602,259 columns** for two 28-bit W29 codes and **704,494,193 columns** for two 32-bit W33 codes. Those are representation counts, before sparse storage, source restrictions or any solver optimization; they are not measured N131 runtimes. The N41 absence certificate and these dimensions make a literal global Macaulay matrix an unpromising N131 transfer under one worker, 600 seconds and 4 GiB.

The next experiment should bring exact source-validity equations or a quotient-algebra constraint into a *joint* first-code-family gate, then measure whether it rejects code regions before visiting individual codes on an unpinned N41 ordinary relation. Only a source-bound gate with a credible N131 work and memory projection advances to the frozen N131 public-point relation run. The remaining full-goal gates are useful rank, factor-base logs, unseen single-target scalar recovery, and a matched isolated rho comparison.
