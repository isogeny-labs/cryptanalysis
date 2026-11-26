#set page(paper: "us-letter", margin: 0.7in)
#set text(font: "Helvetica", size: 9.5pt)
= Four-summand support on the fixed horizontal mixed base
2026-11-25 · Retrospective exact point census · PCC unverified

The five signed eight-point bases from the earlier S4 study all have
three-summand support 96. At four summands, each has 330 indexed
multisets. Exact nonidentity support is 216, 216, 218, 220, and 224
for source A, source B, mixed, random 1, and random 2 respectively.

#figure(image("four_sum_mixed_support.svg", width: 70%), caption: [The fixed bases and exact support computation.])

#figure(image("four_sum_mixed_support_chart.png", width: 96%), caption: [Four-summand support on the 1068 nonidentity targets. Each bar is an exhaustive finite point-group census.])

The mixed base covers two more targets than source A, but both random
controls cover more than the mixed base. This is a support observation
for the existing fixed bases, not a solver or full ECDLP cost result.
It does not identify a horizontal-specific yield gain. A future
four-summand solver claim needs equal-support arms, paired models, and
full setup and target accounting.

Sources and reproduction: `FOUR_SUM_MIXED_SUPPORT.md`,
`four_sum_mixed_support.py`, `four_sum_mixed_support_results.json`,
and `MIXED_EQUAL_YIELD_COST_PROTOCOL.md` in this study directory.
