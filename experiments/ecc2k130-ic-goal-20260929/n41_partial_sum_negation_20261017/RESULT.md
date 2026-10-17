# Negation-quotiented N41 public-target join

The exact negation quotient keeps one left triple from each global sign pair
and reconstructs the other only when the public-target lookup requires it.
It recovered the same independently checked six-pair relation on the frozen
N41 public point with **1,875,072 left rows** and **86,016,000 bytes sampled
combined peak**. The earlier exact hash join used 3,750,144 left rows and
247,955,456 bytes sampled combined peak. This run finished in **6.546 s**
parent wall on the ordinary local host; the earlier hash join took 6.927 s.

## Exact method

All 160 signed states in each of six slots have a unique partner obtained by
flipping both source-point signs. The partner has the same folded columns and
the negative raw pair sum. For a triple `(a,b,c)`, the partner triple
`(neg(a),neg(b),neg(c))` has the negative partial sum. Keeping only rows with
`a < neg(a)` therefore retains one witness from each global sign pair.

The left index stores exact raw point coordinates, three source-state IDs,
and a 16-bit x-prefix directory. For a right partial sum `R`, the public
target gives exact need point `Q-R`. The lookup examines stored rows with
that x-coordinate, tests both stored point signs, reconstructs sign-flipped
state IDs when needed, checks twelve distinct folded columns, and replays
the point sum. [PROOF_MAP.md](PROOF_MAP.md) links the group implication and
the complete source-state involution audit.

## Frozen results

| Same N41 public target and archived source states | Prior hash join | Full sorted index | Negation quotient |
| --- | ---: | ---: | ---: |
| Left rows | 3,750,144 | 3,750,144 | **1,875,072** |
| Parent wall to accepted hit | 6.927 s | 11.356 s | **6.546 s** |
| Sampled combined peak RSS | 247,955,456 B | 146,079,744 B | **86,016,000 B** |
| Accepted six state IDs | `12,122,116,47,128,34` | same | same |

The quotient's left enumeration ended at 2.203 s, sorting and census at
2.546 s, and the accepted hit at 6.280 s process elapsed. It used one worker,
a 60 s parent cap, and a 4 GiB combined RSS cap; monitoring was healthy.
The first accepted hit occurred after 1,100,323 right probes and used the
stored sign. Its six state IDs exactly match the archived independent
checked-Sage certificate for raw public point
`(2026560328086,1928332930914)` on curve
`EC1N41Ckb1h7d5e80d3c4d0`.

A separate **constructed correctness control** made the sign-flipped branch
necessary at the first right probe. The same native binary returned
`HIT 15 121 119 0 4 8 ... flipped=1`; checked Sage constructed its target
from the negated left partial sum and the right partial sum. This control
tests branch wiring, while the ordinary public-point run supplies the
relation measurement. [verification.json](verification.json) checks source,
binary, input, raw logs, both hits, old receipts, and the archived replay;
run `python3 verify.py` to reproduce those checks.

The wall figures are single exploratory ordinary-host observations. The
memory reduction follows from halving the stored left rows and is visible
in the monitored peaks; the small wall difference needs a controlled paired
benchmark before it can support a performance claim. Source and inputs are
hash-bound in `protocol.json`, with `candidate_id: null` because the full IC
pipeline is still unresolved.

## Next gate

The quotient saves a factor of two in left-state count. On the frozen N131
W23 source, that still leaves roughly `3.7e19` labeled left triples before
column filtering, so the next method must prune families before enumerating
three signed slots. Test a compact, exact representation of the map from
source-code prefixes to partial-sum coordinates on the N41 public instance:
measure representation size, source-witness preservation, and the fraction
of code families rejected by the public target before triple expansion.
Promote only a construction with a measured scaling law and an ordinary
verified relation under the N41 gate.
