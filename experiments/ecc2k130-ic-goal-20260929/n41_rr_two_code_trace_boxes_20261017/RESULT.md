# Odd-trace certificates reach the direct-screen cost boundary on an N41 two-code box

## Result

The first shared odd-power trace certificate for a frozen **1,024-state N41
two-code box** needs 25 terms, from \(D\) through \(D^{49}\). The first 24
terms give feature rank 984 and augmented rank 985. With 25 terms, both ranks
are 1,024; `certificate.json` contains an explicit coefficient vector whose
trace is one on every signed determinant in the box. A separate Sage program
recomputed all 1,024 seven-point determinants and checked the 1,024 trace
values. Direct determinant screening found no zero in this box. The
known-relation control retained exactly one zero among its 256 signed states
and had no certificate through eight odd powers.

The certificate construction tested here is substantially more expensive than
the direct screen on the same target-dependent determinant coefficients.
Directly evaluating all 1,024 sign states took **1.570 ms**. Constructing the
25 odd-power feature blocks took **102.921 ms**, followed by **341.268 ms**
to calculate all 25 successive ranks. The full measured direct pipeline,
including common coefficient construction, took **47.255 ms**; the measured
certificate pipeline took **491.443 ms**. These are ordinary-host, sequential
stage timings within one producer run, not isolated online IC or rho timings.
Even ignoring rank solving, this feature construction costs about 65.6 times
the direct sign evaluation it uses as input.

## Frozen input and method

The field is \(\mathbb F_2[t]/(t^{41}+t^3+1)\), the curve is
\(y^2+xy=x^3+1\), and the public raw point is the frozen N41 six-pair target
\((2026560328086,1928332930914)\). Slots 2–5 use the x-root classes of
the archived relation, with the lower encoded y point chosen as sign origin.
Slots 0 and 1 are free within the predeclared code pairs
\((2,5),(2,6),(3,5),(3,6)\); each pair has four x-root charts and each chart
has 64 sign choices. This is a two-free-slot conditional control. A separate
predeclared control uses code pair \((6,196)\) and the same fixed suffix.
`protocol.json` pins the exact source geometry, target, runner, checked Sage
runtime and one-worker resource envelope.

For each seven-point chart, the producer first computes the 64 Boolean ANF
coefficients of its determinant through the 35-term Riemann–Roch Laplace
expansion. The direct screen evaluates those coefficients for all sign masks
and tests zero. The trace route takes those same values, forms ANFs of
\(D,D^3,\ldots,D^{49}\), and solves the shared GF(2) coefficient equations
after each added odd power. A coordinate functional satisfying all 1,024
rows is converted to 25 field trace coefficients. Because each term vanishes
at \(D=0\), a trace value of one excludes zero. The saved certificate passes
an independent Sage determinant and trace replay on all states.

| Box | Charts | Signed states | Zero determinants | Smallest checked shared certificate |
| --- | ---: | ---: | ---: | --- |
| Lexical 2×2 code box | 16 | 1,024 | 0 | 25 odd powers; rank 1,024 |
| Archived-relation code pair | 4 | 256 | 1 | None through eight powers; zero witness rules out this form at every degree |

| Matched stage on the lexical box | Time | Field multiplications |
| --- | ---: | ---: |
| Common determinant ANF construction | 45.685 ms | 11,920 |
| Direct 1,024-sign evaluation | 1.570 ms | 0; 10,496 coefficient XORs |
| 25 odd-power feature construction after sign evaluation | 102.921 ms | 25,600 |
| Successive ranks for one through 25 powers | 341.268 ms | 0 |
| Symbolic \(D^3\) alone, without sign evaluation | 122.096 ms | 29,248 |

The symbolic-cube control checks its 64 values per chart against \(D^3\).
Its 122.096 ms is about 77.8 times the 1.570 ms direct sign screen, while
the two-power certificate is inconsistent for the box. The count of direct
coefficient XORs is recorded in `result.json`; the value in the table is
computed from that record. These costs describe the executed Python/Sage
implementations and this box; they do not establish a lower bound for every
possible trace construction.

## Independent replay and proof status

The producer completed with a 0.727 s monitored parent interval and
50,085,888 bytes sampled combined RSS, below its frozen 600 s / 4 GiB
envelope. `audit_sage.py` independently formed the seven-row determinant
over Sage's binary field for all 1,280 signed states, matched the producer's
ANF hashes and zero locations, and reproduced the decisive ranks at 1, 2,
24 and 25 powers. Rank inconsistency at 24 powers also excludes a certificate
using any prefix of those powers, because a shorter coefficient vector can
be extended by zeros. `audit_certificate_sage.py` then replayed the explicit
25-power certificate on all 1,024 lexical-box states. `terminal.json`
checks source/result hashes, raw outputs, protocols, and audit statuses.

The zero-exclusion implication is the checked Lean theorem
`QuadraticTrace.separator_excludes_zero` in the preceding
`n41_n131_rr_quadratic_trace_20261017` experiment. No new general theorem is
asserted here; the 24/25 boundary is an exact finite-rank observation.
The Boolean ANF, trace-pairing, and curve-determinant bridge remain the
formalization obligations listed in that experiment's proof map. The source
panels and independent Sage replays provide the concrete checks for this
finite instance.

## Decision and next experiment

The present odd-trace construction already evaluates every signed determinant
to form its higher-power features. The symbolic-cube variant avoids that
enumeration but costs more on the same box and does not yield a two-power
certificate. This removes the local odd-trace certificate as the next
solver-integrated pruning route under the measured implementation.

The next gate is a target-dependent predicate on **still-free source-code
bits**, formed directly from the 35-term left/right minor split, before x-root
or sign states are enumerated. Its first acceptance test is an unpinned N41
public query under the frozen one-worker, 600 s, 4 GiB envelope, with exact
relation replay and complete target-dependent cost. The N131 promotion gate
remains the ordinary frozen public point; this conditional two-slot control
is `candidate_id: null`.
