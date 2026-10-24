# Fermat zero testing preserves the witness but does not lower two-box quotient time

Replacing 24 trace-bit equality factors with the exact finite-field
indicator `1+Q^(2^41-1)` preserved the frozen N41 decisions: the complete
negative four-code box was rejected and the complete witness box survived.
Checked Sage verified the indicator at all **256 exact roots** and found
the same single zero in code quadruple `(24,37,10,0)`. The new one-worker
producer took **75.200 s**, compared with **73.094 s** for the earlier
trace-bit producer on the identical two boxes. This is an ordinary-host
component comparison; the 2.9% total difference does not establish a
controlled performance change.

| Frozen box | Trace-bit zero phase | Fermat zero phase | Exact decision |
| --- | ---: | ---: | --- |
| First complete control `(0,7,16,33)` | 14.783 s, stopped after seven bits | 36.739 s, 82 squarings and seven multiplications | Reject |
| Witness `(38,53,16,0)` | 56.274 s, continued through 24 bits | 35.730 s, 82 squarings and seven multiplications | Retain |

Both protocols use curve `EC1N41Ckb1h7d5e80d3c4d0`, the same raw public
target, four free pair-code axes, final-three-state suffix `(14,109,51)`,
the same 32 code quadruples, one worker, a 300-second cap, and 4 GiB.
The new producer's observed `ru_maxrss` was **27,852,800 B**; the Sage
audit's was **252,854,272 B**.
Its independent checked-Sage audit took **10.529 s** after launcher startup.
`candidate_id` remains `null` for this decomposition component.

The comparison isolates why this replacement has limited value: fixed
exponentiation helps the surviving witness box, while the trace method
stops negative boxes early. The complete N41 four-axis group join in the
prior experiment covered all **1,386,816** admissible code quads in
**22.708 s**. Even covering only its **5,040 complete boxes** within a
600-second cap would require an average at most **0.119 s per box**; the
measured quotient phases are tens of seconds per box. This is a required
throughput threshold for a literal box sweep, not a prediction for a new
implicit family method.

The next method must generate or reject much larger code families from
the public target before any explicit four-axis quotient arithmetic. A
promising exact primitive is residual pair inversion: one pair-output
coordinate determines its product code through the fixed-seed quadratic,
after which linearized-product membership and source-point replay decide
the branch. The required experiment is a joint completion oracle that
uses that primitive across several still-free pair slots, with a frozen
ordinary N41 query and complete work accounting before a public N131 run.

`python3 verify.py` checks frozen source hashes, matched boxes, all result
receipts, witness retention, resource caps, and the pinned Lean output.
