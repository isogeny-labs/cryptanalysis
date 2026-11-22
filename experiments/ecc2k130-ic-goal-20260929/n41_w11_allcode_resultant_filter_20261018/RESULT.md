# W11 unrestricted-code resultant filter on the frozen N41 panel

**The target-conditioned 13-term resultant isolated the archived positive
code pair across 26,214,400 unrestricted code-pair evaluations.** Each of
25 frozen residuals was tested against all `1024²` W11 free-code pairs.
The only zero was `(253,63)` on the positive residual; the 24 ordinary
target-derived residuals had zero roots. The enlarged domain introduced
zero roots with an invalid source code on this panel. The positive pair's
exact curve-sum replay is in the [archived valid-code census](../n41_w11_freecode_resultant_20261018/RESULT.md).

| Field and source | Exact value |
| --- | --- |
| Curve | `EC1N41Ckb1h7d5e80d3c4d0`; `GF(2)[u]/(u^41+u³+1)`, `y²+xy=x³+1` |
| W11 source | Seed `s=112`, ten free bits at positions `0,1,2,3,4,6,7,8,9,10`; `a` uses these bit positions shifted left once |
| Source product | `p=a(a+s)`, then Frobenius rotations 12 and 24 for the two pair slots |
| Target equation | Frozen 13-term bivariate resultant, bidegree `(4,4)` |
| Source-code domain | All 1,024 codes per slot, including the 281 archived valid codes |
| Workload | One archived positive plus 24 frozen ordinary target-derived residuals |
| Candidate identity | `candidate_id: null`; complete IC pipeline unresolved |

The native [census](census_all.cpp) rebuilt products for all codes from
the field arithmetic and checked every archived valid-code product
against the frozen [coefficient input](../n41_w11_freecode_resultant_20261018/resultant_input.tsv).
It then evaluated the full resultant for each code pair and saved all
zeros in [result.json](result.json). The independent
[receipt replay](verification_result.json) binds the source, compiler
binary, input, result, and prior valid-code census hashes, and compares
every target's valid-code root set to that prior census.

| Measured item | Result |
| --- | ---: |
| Unrestricted pair tests | 26,214,400 |
| Resultant zeros | 1, the positive `(253,63)` |
| Zeros with at least one invalid code | 0 |
| Native census wall | 13.9753 s |
| Native `ru_maxrss` raw value | 1,622,016 |

These are complete finite-domain measurements for the frozen N41
coefficient panel. The symbolic resultant's shared-root implication and
its hypotheses are covered by the [existing checked Lean proof map](../n41_w11_freecode_resultant_20261018/PROOF_MAP.md);
this experiment adds no new algebraic theorem. The observed root count
does not establish the false-positive rate on N131 or on other target
distributions.

To replay the frozen artifact from this directory, run
`python3 verify.py`. To regenerate the census in a fresh directory,
compile with `clang++ -O3 -std=c++20 census_all.cpp -o census_all` and
run the exact command in [protocol.json](protocol.json). The binary and
all executed inputs are hash-pinned there. The next gate is to test a
validity-free N131 circuit on the constructed positive before querying
the public point.
