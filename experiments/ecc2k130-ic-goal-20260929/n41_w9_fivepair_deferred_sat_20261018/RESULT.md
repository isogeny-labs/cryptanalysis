# N41 public-point five-pair source-eligibility control

Both N41 five-pair circuits accept the independently archived public
relation as a complete assignment. With the five source masks left free,
**neither the exact nor deferred-eligibility solver returned a model within
its paired 120-second parent cap**. Deferring the last two source checks
reduced this N41 circuit by 656 AND gates (4.4%) and 2,054 clauses (4.5%)
but did not pass the unpinned search gate. The N131 deferred-source public
query is therefore not promoted on this evidence.

| Same archived public-point orientation | Exact eligibility | Slots 3/4 deferred |
| --- | ---: | ---: |
| AND gates | 15,047 | 14,391 |
| Variables | 18,340 | 17,328 |
| Clauses | 45,733 | 43,679 |
| Native XOR rows | 2,720 | 2,446 |
| Constructed assignment | All rows pass | All rows pass |
| Unpinned solver status | `BOUNDED_UNKNOWN`, `WALL_CAP` | `BOUNDED_UNKNOWN`, `WALL_CAP` |
| Parent wall seconds | 120.034 | 120.127 |
| Sampled combined peak RSS | 242,614,272 B | 211,648,512 B |

The field is `GF(2)[t]/(t^41+t³+1)` and the curve is `y²+xy=x³+1`
(`EC1N41Ckb1h7d5e80d3c4d0`). Both searches use the archived raw public
point `(2026560328086,1928332930914)`, Frobenius orientation 3, and
oriented point `(2105655159232,891719206310)`. Orientation 3 was selected
because the prior native five-pair join had found and independently replayed
a relation there. The SAT formulas received the oriented point and source
rules, with all five masks and pair outputs unconstrained by the archived
witness. The known relation was used separately to check every CNF and XOR
row before either unpinned search.

Each solver used one CryptoMiniSat 5.14.7 worker, a 110-second solver option,
a 120-second parent wall cap, and a 4-GiB combined-RSS cap. The parent cap
terminated both processes; neither raw log contains a terminal SAT or UNSAT
line. Their status is censored. The exact and deferred formulas, checked-Sage
runtime receipt, source/binary hashes, raw logs, and cap records are frozen
here. `python3 verify.py` checks the hashes, formula row counts, assignment
check records, and capped search receipts. These are ordinary-host
algorithmic diagnostics; `candidate_id` is null.

The circuit modification preserves the archived relation because the two
deferred slots still satisfy the source law. No model reached the proposed
post-solve source audit or exclusion-cut stage, so those stages have not
been evaluated. These paired caps give no evidence that this circuit-size
reduction addresses the observed search barrier. The next experiment should constrain
target-compatible partial-sum families *before* a general SAT search or
use an exact indexed join, and should keep the N41 public-point relation
as an independently replayed control before N131 promotion.
