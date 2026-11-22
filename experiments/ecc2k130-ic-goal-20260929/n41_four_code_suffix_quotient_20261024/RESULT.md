# Four free N41 pair-code axes preserve the witness; exact traversal wins the cost comparison

The four-axis quotient retained the archived ordinary witness while
rejecting a complete negative 16-family code box. Checked Sage verified
both decisions on **256 exact roots** and recomputed all **160 target
residual charts** after fixing only the final three pair states. An exact
one-worker group join then traversed **all 1,386,816 admissible code
quadruples** and found the same single witness in **22.708 seconds**, with
**368,656,384 B** observed peak RSS. The two-box symbolic quotient took
**73.094 seconds** and covered 32 quadruples. This implementation's
full-search path is the group join; the quotient filter needs a much
cheaper way to reject large code families before it can improve that path.

## Frozen N41 experiment

The curve is `EC1N41Ckb1h7d5e80d3c4d0` over
`GF(2)[t]/(t^41+t³+1)`. The input is the archived public raw target
`(1970584690684,115750356512)`. Pair slots 4–6 are fixed at state IDs
`(14,109,51)`; slots 0–3 are free. Each fourth-slot product code has four
exact raw pair states. Their target residual charts were built with the
checked repository Sage launcher before the symbolic freeze. The witness
state IDs are `(97,151,42,0,14,109,51)`; fourfold projection yields the
archived public subgroup point `(1458168294740,1672312028033)`.

The complete code census has **42,432** admissible first-three-code
triples, **1,386,816** admissible four-code quadruples, and **5,040**
complete 2×2×2×2 boxes at the selected prefix depth. The negative box is
the first complete prefix `(0,7,16,33)` and the positive box has prefix
`(38,53,16,0)`. They were frozen before the symbolic run. The 128-dimensional
quotient specializes the archived degree-eight H once per box, interpolates
four target charts across the fourth code variable, multiplies four exact
third-pair norms, and tests bits `0..23` of that product.

| Stage | Frozen scope and result | Wall interval | Peak RSS |
| --- | --- | ---: | ---: |
| Quotient producer | 2 boxes, 32 families; negative rejected by bit 7, witness retained through bit 24 | 73.094 s | 25,722,880 B |
| Independent checked Sage audit | 256 roots, 288 H coefficients, all 160 residual charts; one exact zero at `(24,37,10,0)` and fourth-state offset 0 | 98.005 s | 265,715,712 B |
| Complete checked Sage group join | 1,386,816 code quads represented by 2,715,648 first-three-state sums; one exact witness match | 22.708 s | 368,656,384 B |

The quotient producer spent 0.023 s on setup, 0.373 s on symbolic H,
1.641 s on the four norms, and 71.057 s on the zero fingerprint;
rounding and serialization account for the remainder. The complete join's
22.708 s interval comprises 0.583 s setup, 0.024 s target-map construction,
and 22.101 s traversal. Its 24,864 first-two-state sums and 2,715,648
first-three-state sums were charged within this run. These are ordinary-host
component timings, with no rho comparison or isolation tier. The quotient
run checked two of the 5,040 complete boxes; the complete group join is a
separate exact algorithm with a different cost structure.

An initial freeze asserted that every product-code prefix contained two
codes. The source geometry contains one-, two-, and three-code prefixes.
After that pre-execution assertion failure, the corrected freeze counted
only complete two-code axes. Two further pre-execution checks corrected
the expected first prefix and tuple type of the witness code. The frozen
`protocol.json` is the corrected version used by the successful run.

## N131 W23 transfer check

The N131 W23 source uses six pair slots and the standard `1/x` chart. A
versioned bridge derived the exact first-two-pair polynomial for that chart:
**138 terms, degree eight** in the first-two sum reciprocal. It vanishes on
the previously checked constructed six-pair control. Independent binary
field arithmetic verified the source pair equations, S3 equation, and all
138 terms. The first frozen bridge attempt stopped on a Sage `ETuple` versus
Python tuple type check; its protocol, source hash, stderr, and failure
receipt are preserved. The corrected v2 run took **0.097 s** of internal
arithmetic time after checked Sage startup.

This bridge supplies the first-two-pair algebra for N131. The current
four-axis code still requires an exact fourth-state residual table after
fixing the remaining pair slots, and a complete continuation through the
W23 six-pair public target. Those inputs are not supplied by the N41
seven-pair fixture or the W23 constructed control. The measured N41 cost
also gives no basis to promote this quotient implementation as a
single-target speed candidate. The next design step is target-dependent
family generation or pruning that avoids traversing explicit product-code
boxes; it must be measured on an unpinned ordinary N41 query before a
frozen public N131 run.

Run `python3 verify.py` to check the frozen hashes, result receipts, Lean
output, exact counts, failed bridge attempt, and corrected N131 bridge.
