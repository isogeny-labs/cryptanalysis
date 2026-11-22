# Table-free pair-output membership and target-conditioned terminal join

An exact fixed-seed output inverse replaces a stored pair-output index with one field inversion and a linear source-product membership check. On the N41 ordinary public-derived residual, the native terminal join scanned all **562** left pair outputs, derived **1,124** S3 right-output roots, and found the archived `(253,63)` pair-code hit. Independent checked Sage replayed every root and the unique hit. On the N131 constructed five-pair residual, the same kernel scanned **2,128** left outputs from a frozen 4,096-code prefix, derived **4,256** right-output roots, and found the constructed `(22,29)` pair-code hit; every root and membership decision passed independent Sage replay.

## Exact method

For a fixed source seed and Frobenius rotation, the pair-output reciprocal `c` satisfies `C c² + p c + H = 0`, where `C,H` are fixed field elements and the source product `p=w(w+s)` is binary linear in the free source-code bits. For `c≠0`, the candidate product is uniquely

`p = (C c² + H)/c`.

The native code batch-inverts proposed outputs, computes `p`, and reduces it against the frozen product basis over GF(2). A decoded code is a **necessary pair-family membership** decision; any emitted hit is then checked against endpoint source validity, actual point sums, and folded columns before use as a relation. The target-conditioned terminal routine derives at most two right outputs `d` per left output `c` by solving `(1+c²t²)d²+ctd+(c+t)²=0` for the supplied residual reciprocal `t`; it sends each right root to the table-free membership test. The native worker verifies the S3 equation for every emitted root. The [proof map](PROOF_MAP.md) links the additive source-product map, unique inversion formula, exact field audits, and archived group fixtures.

## Frozen controls and costs

| Boundary | N41 | N131 |
| --- | ---: | ---: |
| Field / curve | GF(2^41), `EC1N41Ckb1h7d5e80d3c4d0` | GF(2^131), `EC1N131Ckb1heb5f1998f20b` |
| Source seed mask; free product bits | 56; 10 | 898618; 28 |
| Source-output controls recovered | 64/64 | 64/64 |
| Uniform proposed outputs scanned | 100,000 | 200,000 |
| Native product-membership query time | 0.067990 s | 0.008927 s |
| Sampled random decisions replayed in Sage | 64/64 | 64/64 |
| Terminal left outputs | 562, all 281 valid N41 codes | 2,128 from 1,064 valid codes in prefix `0..4095` |
| Derived S3 right roots, all Sage-replayed | 1,124 | 4,256 |
| Product-image hits | one, codes `(253,63)` | one, codes `(22,29)` |
| Native terminal query time | 0.004749 s | 0.007807 s |
| Terminal parent wall / sampled combined peak RSS | 0.246 s / 24,182,784 B | 0.027 s / 25,051,136 B |

Each native stage had one worker, a frozen 120-second parent wall cap, and a 4-GiB combined-RSS cap. The checked Sage launcher produced and audited all finite-field inputs; its runtime receipt is archived. The N41 terminal residual is the archived ordinary public relation after its first three pair states are fixed. The N131 terminal residual is the constructed five-pair fixture's right two-pair sum. The terminal operator is tested on complete N41 left-code coverage and an N131 prefix; it has not yet generated an ordinary N131 relation. Both stages remain `candidate_id: null` until a complete relation collector, matrix, descent, and target recovery are specified.

The N131 random-output membership interval corresponds to about 22.4 million proposed outputs per second on this unisolated host. Applying that *stage rate alone* to the earlier sample-based 68,308,992 W29 valid-code projection gives about 3.05 seconds **after** pair outputs exist. It does not include source-validity census, pair-output generation, target-conditioned S3 roots, code/column checks, or the outer three-pair search. The 4,256-root constructed terminal measurement includes S3 root generation and membership, but its prefix is far smaller than the full W29 source. These figures are diagnostics and projections, not a complete public-query speedup.

The first Sage preparation failed before writing inputs because the N41 seed and N131 fixture reciprocal fields were misidentified. The corrected preparation used the exact source quadratic and passed; `prepare_failure_v1.json` and `prepare_sage_v1.py` preserve the failed attempt. The first independent auditor parsed native field limbs as decimal scalars and stopped before a result; `audit_failure_n41_v1.json` and `audit_sage_v1.py` preserve that attempt. The version-two audit parsed the three-limb encoding and passed. The frozen protocols, compiler and runtime receipts, input tables, native stdout/stderr, monitor receipts, Lean output, and independent audit records are in this directory.

## Next experiment

Stream a bounded W29 source-code prefix through native endpoint-validity and pair-output generation, then through this terminal operator. Measure generation and terminal costs separately, retain a constructed hit and a public-derived residual miss as controls, and project the complete source domain under one worker, 600 seconds, and 4 GiB. In parallel, design a target-conditioned constraint for the remaining three free pair families; a fast two-pair terminal alone still faces their Cartesian search.
