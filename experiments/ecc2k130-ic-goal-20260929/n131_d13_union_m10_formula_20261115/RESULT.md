# N131 ten-leaf adjacent-union formula and planted control

The exact adjacent-branch construction produces a ten-leaf, four-endpoint
XCNF for the frozen official ECC2K-130 public point. The
[formula](official_q_d13_union_m10_v1.xcnf) has **337,789 variables,
309,161 clauses, and 246,591 native XOR rows** (14,521,119 bytes). Its
output is bound to the [frozen protocol](protocol.json) and
[receipt](formula_receipt.json). The factor-base geometry is the earlier
exact d13 adjacent-union census: 2,166,216 subgroup-usable points before
folding and 4,134 folded log columns. The source selector and branch bit
remain free in the official-target formula.

For each of ten distinct Frobenius positions, the source phi chart is a
13-bit linear form. The Boolean equation
`(1+b*y)*phi_out=phi+b*phi²`, with `y=phi²+phi`, chooses the original or
adjacent-Frobenius image. Every output phi is a full-field variable. The
nine chained S3 links therefore use generic ONB multiplication for their
variable products. The last link selects one of the four verified cofactor
lifts of the same official point. The exact eligibility table excludes
the 4,058 invalid selector codes at every leaf.

A [planted ten-leaf assignment](planted_result.json) with both branch
values satisfies all **311,661 clauses after 2,500 primary pins** and all
246,591 native XOR rows. Its point signs sum to the synthetic target.
An [independent Sage replay](sage_result.json), launched through the checked
repository Sage runtime, verifies all ten selected curve points, eight
partial sums, and four target-fiber endpoints. The planted point is a
correctness control; its construction does not measure ordinary target
coverage or relation yield.

The preceding original-source d13/m12 formula used 232,244 variables,
228,629 clauses, and 171,278 native XOR rows. This ten-leaf union formula
is 1.45 times its variable count and 1.44 times its XOR-row count, while
using two fewer summands. These are formula-size comparisons, not solver
runtime or end-to-end IC measurements. The next falsifier is a frozen
one-worker ordinary query on the official target, retaining timeout,
memory, and output status, followed by independent decoding of any model.
Its use should be considered alongside the continuing d13/m12 collector's
prospective zero-yield gate and the bounded N41 free-branch SAT query.

The current record is a design and component gate, with `candidate_id: null`.
The complete candidate stage policy, natural yield, rank, factor logs,
fresh-target recovery, and matched one-target rho measurement remain the
next evidence sequence. Run `python3 verify.py` from this directory for the
read-only custody check.
