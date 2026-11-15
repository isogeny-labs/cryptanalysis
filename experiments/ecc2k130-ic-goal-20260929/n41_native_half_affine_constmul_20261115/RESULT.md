# Fixed-basis multiplication for the N41 target-conditioned affine gate

Precomputing multiplication by the fourteen fixed product-basis elements made
the exact N41 two-half affine filter faster on its complete public-point family
census. In a frozen alternating six-arm run, the new target-dependent loop took
**1.086 and 1.095 s**, versus **2.663 and 2.353 s** for the prior affine
implementation and **1.979 and 2.033 s** for direct per-root rank. The new
filter retained the same 495 of 248,640 chart/family combinations, both half
rank histograms, the 3,960 final source checks, and the independently audited
ordinary relation `(chart 0, left 24, right 37, root 2, third 10)`.

The [native source](native_constmul.cpp) changes only the fixed-basis products
inside the span construction. For each of seven basis elements and its square,
it precomputes six 256-entry byte tables. Multiplication by that element then
XORs six table entries instead of performing a bit-serial field multiply.
This uses 172,032 bytes of table entries. Table construction is reusable setup
and occurs before `query_s`; the target-dependent interval includes all
248,640 families, both half-rank gates, rejected cases, and final source
checks. The same independent checked-Sage archive supplies the full census
and group-replayed witness for all three native arms.

| Frozen arm order | Target-dependent loop, s | Families | Retained | Hit |
| --- | ---: | ---: | ---: | --- |
| Prior affine | 2.663 | 248,640 | 495 | same |
| Fixed-basis table | 1.086 | 248,640 | 495 | same |
| Direct rank | 1.979 | 248,640 | all 1,989,120 roots checked | same |
| Direct rank | 2.033 | 248,640 | all 1,989,120 roots checked | same |
| Fixed-basis table | 1.095 | 248,640 | 495 | same |
| Prior affine | 2.353 | 248,640 | 495 | same |

The median query-loop ratio is **2.30** for prior affine over the table arm
and **1.84** for direct rank over the table arm in this panel. The table arm's
setup intervals were 10.2 and 6.3 ms. Its macOS `getrusage` peak-RSS
values were 2,359,296 and 2,342,912 in the recorded raw units, versus
2,129,920–2,146,304 in the reference arms. The run
used one native process at a time on the ordinary macOS arm64 host, while
other work was live. These are exploratory component timings with no CPU
isolation tier and no complete IC or matched-rho timing.

The [protocol](protocol.json) pins the source, input, independent Sage
archive, runner, compiler flags, order, and expected census before the run.
The [receipt](abba_result.json) retains every build, binary hash, row and
timing. `python3 verify.py` rechecks its hashes, the complete rank histograms,
source-check counts, and witness. No new mathematical result is asserted:
the substitution uses distributivity of field multiplication over XOR and
the same exact affine gate already proved and independently checked in the
prior archive.

The next degree-131 gate needs a target-conditioned multi-family filter with
complete source traversal inside a frozen 600-second, 4-GiB budget. This
fixed-factor multiplication is a reusable kernel for such a filter; it does
not remove the outer family enumeration. `candidate_id` remains `null` at this
point-decomposition component stage.
