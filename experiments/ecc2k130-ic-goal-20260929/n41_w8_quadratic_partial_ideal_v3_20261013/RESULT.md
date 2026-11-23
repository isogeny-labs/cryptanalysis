# Exact quadratic ideals for small W8 partial-sum families

On the frozen unpinned N41 W8 four-pair relation, the reciprocal coordinates of both witness-centered two-pair families are linearly independent at widths four and eight. Their membership therefore has an exact squarefree quadratic description: write a candidate reciprocal as `Σ α_i c_i` in the family's basis, require `Σ α_i = 1` over `GF(2)`, and require `α_i α_j = 0` for every `i ≠ j`. These equations select precisely one enumerated reciprocal. The width-eight description held for 63 of 64 sampled region quadruples and failed in one measured rank-deficient right family. At width 16, every sampled nonempty family exceeded the 40-dimensional reciprocal trace-zero space, so this particular one-hot construction ceased to apply. Independent checked Sage reproduced the selected positive, negative, and rank-exception cases.

## Instance and method

The source is the independently audited diagonal four-pair table for curve `EC1N41Ckb1h7d5e80d3c4d0` over `GF(2)[X]/(X^41+X^3+1)`. There are 30,952 signed source states per slot. The public target is raw preimage index 1, with reciprocal x-coordinate `344545435656`; the verified witness has slot IDs `(17678,155,6169,16990)`. All four slots use aligned regions of `2^f` signed states, for `f=2,3,4,5`. A valid two-pair partial has disjoint folded columns and excludes identity or zero x-coordinate. The worker computes its reciprocal x-coordinate, its binary span rank, exact S3 coordinate compatibility with the fixed target, and exact full-point group compatibility with all eight columns distinct.

For each `f=2,3,4`, the worker also examines 64 deterministic random region quadruples from `mt19937_64(202610140300+f)`. The witness-centered region is a separate positive control. `exact_quadratic_one_hot_ideal` means that **each** side's number of distinct reciprocals equals its binary span rank and both sets are nonempty. The test concerns reciprocal-coordinate membership; full point signs and source labels remain in the exact group check.

| Width per slot | Witness unique reciprocals, left/right | Witness rank, left/right | Witness S3 / exact group hits | Sample nonempty / 64 | Sample exact one-hot / 64 | Sample S3 / exact group hits |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 4 | 8 / 8 | 8 / 8 | 1 / 1 | 61 | 61 | 0 / 0 |
| 8 | 32 / 32 | 32 / 32 | 1 / 1 | 64 | 63 | 0 / 0 |
| 16 | 120 / 128 | 40 / 40 | 1 / 1 | 62 | 0 | 0 / 0 |
| 32 | 504 / 512 | 40 / 40 | 1 / 1 | — | — | — |

The width-eight exception is case 70: its right family has 32 distinct reciprocals but rank 31. All nonempty sampled regions passed the earlier linear target-span screen. The new quadratic description is exact for the independent families even though that span screen has saturated. The quadratic equations also encode the enumerated reciprocal list; a faster relation search would need a way to combine these local ideals across many regions without explicitly visiting their source states.

## Verification and cost boundary

The version-three native census completed 196 cases in **6.990302041 s** under one worker, a 120 s wall cap, and a 4 GiB RSS cap. Its sampled combined RSS was 33,193,984 bytes. Checked Sage independently rebuilt cases 0, 1, 2, 4, 68, and 70 from the frozen table, compared ranks and group hits, and directly checked S3 coordinate matches at widths four and eight. The audit completed in **40.106055958 s**. Its RSS monitor reported degraded sampling, so its 256,000,000-byte sample is descriptive rather than a peak bound. The checked launcher runtime is in `sage_runtime_info.json`; native and audit source/binary hashes are in their frozen protocols. `python3 -B verify.py` checks both receipts, source hashes, counts, cases, and Sage comparisons.

The first checked-Sage implementation reached its 120 s wall cap before writing a result. The second replaced its inner S3 loop with exact GF(2^41) quadratic-root lookup and reached the same cap after printing progress through 80 cases. Both retained `WALL_CAP` receipts and outputs; their mathematical yield is censored. Version three moved the finite census to a compiled worker while retaining the independent Sage replay. These are stage costs for this N41 panel, with `candidate_id: null`; no complete IC candidate or single-target online comparison is represented by the panel.

## Proof and next experiment

The structural one-hot theorem is in `OneHot.lean`. Its checked Lean 4.34.1 proof establishes that an odd GF(2) sum plus every pairwise squarefree zero equation is equivalent to a unit Boolean coordinate vector. The proof uses only Lean's `propext` foundation; `lean_check.log` contains `#print axioms`. The finite N41 ranks, field arithmetic, curve additions, and exact witness checks are the versioned native computation and independent Sage audit. Their formalization bridge is recorded in `PROOF_MAP.md`.

A one-hot basis in this trace-zero space can contain at most 40 distinct reciprocal values. On the corresponding N131 curve, the same construction would allow at most 130 independent values per family. The next N41 test should use the width-16 families to search for **additional low-degree equations** that reject nonmembers without converting back to the explicit 120- or 128-value lookup. It must test unpinned nonempty regions, preserve the public witness, and count all candidate generation and verification work. Only an exact region-skipping procedure with a cost bound below explicit traversal should advance to the frozen N131 point.
