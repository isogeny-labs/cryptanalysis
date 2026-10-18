# W33 exact five-pair source and capped positive search

The W33 five-pair encoding accepts a complete constructed relation assignment
on the N131 curve: **243,979 clauses and 43,415 native XOR rows all pass**.
It uses 32 free canonical source bits, the balanced three-plus-two addition
tree, and the previously audited ten-leaf control. The complete SAT search
on this satisfiable constructed instance reached its 600-second parent cap
without returning a model. The frozen public-point search remained behind
the independent-model gate and was not launched.

| Stage | Recorded outcome | Wall seconds | Other evidence |
| --- | --- | ---: | --- |
| Positive formula build and assignment check | `PASS_W33_FIVEPAIR_CIRCUIT` | 7.685 | 7,923,553 bytes; 80,709 AND gates; 125,987 variables |
| Frozen public formula build | `PASS_W33_FIVEPAIR_CIRCUIT` | 4.453 | 7,923,756 bytes; same structural counts |
| Constructed positive SAT search | `BOUNDED_UNKNOWN`, `WALL_CAP` | 600.065 | One worker; sampled combined peak RSS 257,982,464 bytes; last restart index 1,485; no terminal SAT/UNSAT line |
| Public SAT search | `GATED_UNRUN` | — | Positive search supplied no independently auditable model |

The field is `GF(2)[t]/(t^131+t^13+t²+t+1)` and the curve is
`y²+xy=x³+1` (`EC1N131Ckb1heb5f1998f20b`). The constructed raw target
is `(146863897895816109986651225918031237479,
1492132185809627015012067357695613418716)`; the frozen public raw point
is `(877610862732227974378969808549299291499,
2063336771837286479337213121437715536874)`. The five source rotations
are `(0,18,36,54,72)`. Exact source eligibility and the pair quadratic
are enforced in every slot. The positive assignment checks the Boolean
formula directly; the older independent Sage replay of the embedded W29
control establishes the group relation. A new SAT-returned model would
require a separate independent group audit before public promotion.

The formula files, source hashes, checked Sage runtime receipt, solver
binary hash, 600-second/4-GiB protocol, raw solver output, and status record
are frozen here. `python3 verify.py` checks source and result hashes, counts
every formula row, and confirms the cap classification and public gate.
The search outcome is censored and gives no ordinary relation-yield estimate.
`candidate_id` remains null because factor-base enumeration, relation rank,
target descent, and single-target rho comparison are still unresolved.

The next source-to-target experiment should change the search constraint:
enforce inverse-trace eligibility in three pair slots, audit the other two
after each returned model, and exclude failed model masks exactly. An
unpinned N41 public-point control must validate this policy before a frozen
N131 public-point query. In particular, a smaller formula alone cannot pass
the ordinary-relation gate.
