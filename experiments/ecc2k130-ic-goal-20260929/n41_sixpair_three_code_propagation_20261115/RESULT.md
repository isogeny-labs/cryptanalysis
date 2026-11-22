# Three-code propagation on the N41 six-pair public query

Fixing three source product codes and running CNF plus native-XOR unit
propagation rejected **5,404 of 64,000** complete first-three-code families
on the frozen N41 public-point formula. The independent source-column
census classified **all 5,404** rejected triples as already invalid because
their six folded columns overlap. The **58,596 source-valid triples all
remained open**, including the independently replayed ordinary relation's
code triple `(6,100,97)`. This finite result closes plain three-code unit
propagation as a target-dependent whole-family filter for this formula and
input law.

The [protocol](protocol.json) froze the archived 31,533-variable,
82,957-clause, 3,689-XOR public XCNF, all six source-state tables, the
independent relation certificate, source hashes, a 600-second wall cap,
and a 4-GiB observation threshold. The [producer](run.py) reused the
previously audited incidence-based propagator, pinned exactly 21 code
wires, and retained each outcome in [rows.jsonl](rows.jsonl). The full
one-worker pass completed in **206.032 s** on the ordinary macOS host;
its process-reported peak RSS was **62,586,880** in the recorded raw
macOS units. Every attempted case, including the 5,404 conflicts, is
charged to that interval.

The [independent audit](audit_result.json) rebuilt the source-column map
from the frozen signed-state table and checked the source-validity label
of **all 64,000 rows**. A separate whole-formula scan implementation
replayed **166 deterministically selected** propagation cases, including
the relation witness, and matched their statuses and open fixed-point
assignment counts. The [read-only verifier](verify.py) checks both
protocols, every source and row hash, counts, witness, and replay receipt.

| First-code prefix depth | Families | Conflicts | Source-valid conflicts |
| ---: | ---: | ---: | ---: |
| One code, prior complete census | 40 | 0 | 0 |
| Two codes, prior complete census | 1,600 | 46 | 0 |
| Three codes, this complete census | 64,000 | 5,404 | **0** |

The first two rows are from the frozen [one-code](../n41_sixpair_code_propagation_20261115/RESULT.md)
and [two-code](../n41_sixpair_two_code_propagation_20261115/RESULT.md)
censuses on the same XCNF. They and this result are finite algorithmic
diagnostics, with `candidate_id: null`; their ordinary-host wall times do
not establish a complete IC/rho ratio. Four-code direct propagation would
visit 2.56 million code quadruples before any full point decomposition,
and the N131 W23 source has over a trillion two-edge families. The next
search change therefore needs a nonlinear target consequence that rejects
many still-free code families in one operation, with a complete-source
cost case before the N131 public-point gate.
