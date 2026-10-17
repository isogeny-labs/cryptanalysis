# All-valid W20 affine flats form a denser source cover

**A frozen one-worker search constructed 4,096 all-valid four-dimensional affine flats of the N131 W20 product-code space and covered 52,243 of its 132,045 valid codes.** Every 16-code block, anchor, addition count, and final union was independently replayed from the 19-bit validity bitmap. The bounded cover took **65.304 seconds** of target-independent work with **62,423,040 B** peak self RSS. This is a concrete source grouping for a future joint target predicate, with `candidate_id: null`.

## Source and exact flat recurrence

The source is the frozen W20 seed `898618` on `EC1N131Ckb1heb5f1998f20b`, over `GF(2)[t]/(t¹³¹+t¹³+t²+t+1)`. Its exact 132,045 valid pair-product codes are indexed by 19-bit vectors in the independently audited [validity bitmap](../n131_w20_code_trace_bitset_20261014/valid_bitmap.bin). If an affine flat is `x⊕S`, define its admissible translations

`C_S={v : x⊕s⊕v is valid for every s∈S}`.

Extending `S` by a direction `u` gives `S′=S∪(S⊕u)` and the exact recurrence `C_S′=C_S∩(C_S⊕u)`. The search uses this recurrence to test a complete doubling of a flat with one bitmap intersection. [FlatCandidate.lean](FlatCandidate.lean) checks the abstract finite-set identity under the stated additive laws; the [proof map](PROOF_MAP.md) identifies the concrete XOR/bitmap bridge. Each saved flat's direction vectors are independent and every one of its `2^d` codes has its validity bit set.

## Pairwise structure and bounded flat searches

A Walsh–Hadamard transform computed every XOR overlap `|V∩(V⊕u)|` for the full 19-bit code space. Among nonzero directions the observed overlap ranged from **32,318 to 34,162**, around a mean of **33,256.12**. The maximum 34,162 lies within the range of maxima **34,102–34,230** from twelve equal-size random-control sets under frozen seeds. The controls give no measured pairwise additive preference for choosing directions. The [autocorrelation receipt](autocorr_result.json) retains all top directions, a full-vector digest, transform timing and controls; the independent verifier directly recounts the top twenty overlaps from the bitmap.

| Frozen flat search | Attempts | 16-code flats found | 32-code flats found | Source work |
| --- | ---: | ---: | ---: | ---: |
| Random first three directions, then best fourth | 256 | 159 | 0 | 3.962 s |
| Sample 32 candidate third directions, then best fourth | 512 | **512** | 0 | 29.790 s |

The first policy's 16-code success count is close to its two random-set controls (169 and 168 of 256). The second policy always found a 16-code flat within its 512 attempts, at greater work per attempt. Its zero 32-code outcomes are a **bounded search result**, not an absence theorem: the protocol fixes the attempts, selection policy, seed, and 120-second alarm. The raw outcomes are in [flat_result.json](flat_result.json) and [flat_result_v2.json](flat_result_v2.json).

## Cover construction and matched selection

The [cover protocol](cover_protocol.json) repeatedly chooses the lowest uncovered valid code as an anchor. Up to eight random-extension attempts seek an all-valid flat through it; the first 16-code flat is kept. Every 512 blocks are flushed to a durable [block ledger](cover_blocks.jsonl). All 4,096 blocks succeeded at dimension four, with 6,284 flat-search attempts and no singleton fallback. Their union covers **39.56%** of the valid source. Coverage fell from 7,965 codes in the first 512 blocks to 5,319 new codes in blocks 3,585–4,096 as blocks began to overlap. The [cover result](cover_result.json) retains all checkpoint times, additions, hashes and resource use.

The [matched continuation](compare_result.json) starts both policies from the same frozen 52,243-code union, uses 512 more blocks, and retains separate [first-valid](compare_first.jsonl) and [best-of-eight](compare_best.jsonl) ledgers:

| Selection from same checkpoint | New valid codes | Covered after 512 blocks | Flat-search attempts | Source wall |
| --- | ---: | ---: | ---: | ---: |
| First valid flat | 4,934 | 57,177 | 777 | 9.857 s |
| Best of eight trials | **6,036** | **58,279** | 4,096 | 55.951 s |

Choosing the best of eight adds **1,102** more codes (22.33%) for **5.68×** the target-independent setup wall time in this matched continuation. The independent [verification receipt](verification.json) replays all 4,096 initial blocks and 1,024 continuation blocks with a separate pure-Python bitmap reader, checks exact affine spans and covered-set unions, and binds the autocorrelation and flat-search source hashes. These are source-construction costs; they are not substituted for online target-query time.

## Boundary for a target-conditioned relation solver

Any cover using only 16-code flats needs at least `ceil(132045/16)=8,253` blocks per slot. Even at that unattained ideal, two free slots have at least **68,112,009** block pairs and three have at least **562,128,410,277** block triples before cross-slot column exclusions. A 600-second traversal of those ideal block pairs needs at least **113,521 decisions/s** if each pair is visited separately; the three-slot figure needs about **936.9 million decisions/s**. The measured cover is partial, so its full block count is not inferred from these bounds. Larger 32-code flats could change the bound, and the bounded searches above do not decide whether such flats exist.

This source cover is materially denser than the fixed low-bit prefixes in the [prior rectangle survey](../n41_trace_rectangle_certificate_20261017/RESULT.md), but a target-dependent block test is still needed. The next experiment is to put arbitrary-oriented all-valid N41 flats into the frozen public eliminant and measure exact full-block rejection on an unpinned public relation. Only a source-bound joint predicate with charged construction and early rejection should be promoted to the N131 one-worker, 600-second, 4-GiB ordinary-relation gate; factor-log recovery and matched same-point rho remain subsequent gates of the active objective.
