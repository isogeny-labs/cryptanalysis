# Joint Boolean Gröbner solving of target-resultant first-code blocks

**One Gröbner solve recovered the archived N41 source pair while leaving
up to five first-code bits free, and the same construction recovered
the N131 pair with up to three first-code bits free.** All ten frozen
N41 positive/ordinary controls completed: positive blocks recovered
`(253,63)`, while the paired ordinary residual returned the unit ideal.
On N131, widths one through three recovered `(3,16722)` on the
constructed positive and returned the unit ideal on the frozen public
raw point for the corresponding source-code block. The N131 width-three
positive and public blocks completed within one worker, 600 seconds,
and 4 GiB sampled combined RSS. A width-four constructed-positive query
ended `BOUNDED_UNKNOWN` at its 600-second wall cap, so its public query
remains gated.

The method keeps `k` first-source code bits and **all** second-source
code bits free in one Boolean system. It specializes the frozen 13-term
target-conditioned resultant to a first-code block. In characteristic
two, source products are binary linear in code bits; their squares and
fourth powers are linear and their cubes have degree two. Consequently
the exact joint ANF has degree at most two in each source-code family
and total degree at most four. The [Lean proof map](PROOF_MAP.md)
records the checked expansion identity and the remaining code-level
formalization obligation. [joint_gb.py](joint_gb.py) builds the ANF,
checks its family degrees, and solves its 41- or 131-equation Boolean
system with PolyBoRi. It delays source-point validity checks until a
model is decoded.

| Frozen setting | N41 W11 | N131 W33 |
| --- | --- | --- |
| Curve | `EC1N41Ckb1h7d5e80d3c4d0`; `GF(2)[u]/(u^41+u³+1)` | `EC1N131Ckb1heb5f1998f20b`; `GF(2)[u]/(u^131+u^13+u²+u+1)` |
| Curve equation | `y²+xy=x³+1` | `y²+xy=x³+1` |
| Source seed and rotations | `s=112`, rotations `(12,24)` | seed mask `898618`, rotations `(0,18)` |
| Source-code variables | Ten second-code bits plus `k=1..5` first-code bits | 32 second-code bits plus `k=1..3` completed first-code bits; `k=4` capped |
| Positive and ordinary points | Frozen positive plus frozen ordinary residual index 1 | Frozen constructed positive plus frozen public raw point |
| Candidate identity | `candidate_id: null` | `candidate_id: null` |

The N41 cases exhaustively compared ANF and direct finite-field
resultant values for **every assignment in each tested block** before
Gröbner reduction. The complete prior all-code census has exactly the
archived positive root and no root on ordinary residual index 1.
The [N41 gate](n41_gate.json) binds all ten case receipts, input
hashes, those expected root sets, and resource checks. N131 runs were
launched only after that gate passed. Their positive code pair matches
the earlier [independent source-point and curve-sum replay](../n131_w33_resultant_core_20261018/replay_result.json).

| First free bits `k` | N41 positive / ordinary monitored wall | N41 result |
| ---: | ---: | --- |
| 1 | 9.77 / 8.91 s | `(253,63)` / unit ideal |
| 2 | 11.72 / 12.92 s | `(253,63)` / unit ideal |
| 3 | 13.61 / 15.15 s | `(253,63)` / unit ideal |
| 4 | 19.10 / 15.60 s | `(253,63)` / unit ideal |
| 5 | 22.41 / 21.19 s | `(253,63)` / unit ideal |

| First free bits `k` | N131 ANF monomials | Positive monitored wall / peak RSS | Public-block monitored wall / peak RSS |
| ---: | ---: | ---: | ---: |
| 1 | 1,058 | 14.43 s / 413,810,688 B | 15.95 s / 412,123,136 B |
| 2 | 1,619 | 16.19 s / 439,107,584 B | 15.24 s / 440,549,376 B |
| 3 | 3,204 | 405.23 s / 1,687,273,472 B | 296.27 s / 1,738,309,632 B |

The width-four positive built 5,317 ANF monomials in 36 Boolean
variables and entered Gröbner reduction. The monitored first attempt
ended `BOUNDED_UNKNOWN` at 600.149 s, with 1,912,569,856 B sampled
peak combined RSS and no solver result file. The
[cap replay](width4_verification.json) checks its terminal receipt,
frozen input hashes, known-positive block membership, and absence of
a completed basis. This cap is not an UNSAT result or a zero-yield
measurement.

Every row above is one monitored ordinary-host stage run, including
checked-Sage child startup, ANF construction, Gröbner reduction and
wrapper completion. Each N131 run had one Sage child, a 600-second
parent wall cap and a 4-GiB sampled combined RSS cap. The unit-ideal
rows are PolyBoRi reports; separate independently checkable Gröbner
certificates were not saved. The recovered positive codes were checked
against the joint ANF, and the N131 pair has prior independent
direct-resultant and curve replay. These runs do not constitute a full IC
candidate or an online IC/rho comparison.

The first N131 positive width-three child produced a result but its
wrapper failed when sandbox policy denied process-group termination;
[the failure record](n131_p_k3_wrapper_failure.txt) keeps its resource
status unresolved. A second attempt recovered the pair in 318.76 s,
but [its receipt](n131_p_k3_v2_receipt.json) records `MONITOR_FAILURE`
from a child-exit sampling race. The third, repaired-monitor attempt is
the 405.23-second complete row in the table. The first two outputs
remain preserved. A verifier path correction after the panel was
frozen is retained in [verification_attempt2.txt](verification_attempt2.txt).
[verify_n41_gate.py](verify_n41_gate.py) and
[verify_n131_panel.py](verify_n131_panel.py) replay the frozen hashes,
status, cap and positive-code checks; the final N131
[verification result](n131_panel_verification.json) passes six cases.

## Scaling decision

The nonlinear solver rejects N41 five-bit blocks even where the
earlier affine-span filter filled the field and rejected none. At N131,
the width-three block represents eight first codes but costs
296–405 seconds per target residual. Covering all `2^32` first codes
with disjoint width-three blocks requires `2^29` block queries; this
count alone rules out a serial per-block search within 600 seconds at
the measured cost. These times are stage diagnostics, and the
all-block projection is explicitly an extrapolation from the frozen
blocks. The width-four constructed-positive cap bounds this particular
PolyBoRi ordering; it does not classify other elimination orders or
the public width-four block. The next method must eliminate much larger
first-code regions
in one target-conditioned operation, or share most of the elimination
across regions and residuals. Another local validity-clause reduction
or a serial small-block scan does not meet the ordinary-relation gate.
