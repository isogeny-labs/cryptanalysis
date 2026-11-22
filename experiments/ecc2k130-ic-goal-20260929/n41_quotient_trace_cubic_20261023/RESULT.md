# Root-free cubic feature certificates for N41 code families

The quotient-algebra calculation recovered **exactly the same 10,661-bit
cubic constancy masks** as eight archived N41 two-code root sets, without
extracting roots in the producer. The eight-family panel includes the known
ordinary witness code pair `(24,37)`. Checked Sage independently verified
all 64 source roots, every mask bit, and all 520 target decisions. The
witness family retains its frozen residual; each of the other seven selected
families rejects all 65 residuals. This supplies a correct implicit leaf
predicate for the earlier code-region screen.

## Exact construction

The source is curve `EC1N41Ckb1h7d5e80d3c4d0`, over
`GF(2)[t]/(t^41+t^3+1)`, with W8 seed 56 and the frozen first two pair
slots. Each selected admissible product-code pair has a degree-eight,
split, squarefree root polynomial `H(U)` in `u=1/(x+1)`. The archived
feature coordinate is `z=1/x=u/(1+u)`. The first attempt used `u` directly
as `z`; the independent audit rejected its first root. The failure receipt,
first protocol, producer result, and original scripts remain in this folder.

The corrected worker evaluates `H(1)`, divides `H(U)+H(1)` by `U+1`, and
uses that quotient to invert `U+1` modulo `H`. It then represents each bit
`z_i` as `Tr(α_i z)` in the quotient algebra, using the trace-dual basis of
the declared polynomial field representation. Products of those residues
give one bit `z₀`, 780 squarefree quadratic bits, and 9,880 squarefree
cubic bits. A residue equal to constant zero or one certifies the bit value
for every root, under the audited split-root chart. The target can reject a
whole code pair when one certified bit disagrees.

| Frozen case index | Product codes | Constant feature bits | Residuals rejected / 65 | Root audit |
| ---: | --- | ---: | ---: | --- |
| 0 | recorded in `result.json` | 2,511 | 65 | pass |
| 1 | recorded in `result.json` | 2,849 | 65 | pass |
| 7 | recorded in `result.json` | 2,627 | 65 | pass |
| 31 | recorded in `result.json` | 3,645 | 65 | pass |
| 255 | recorded in `result.json` | 3,349 | 65 | pass |
| 766 | recorded in `result.json` | 3,396 | 65 | pass |
| 966 | `(24,37)` | 3,228 | 64; witness retained | pass |
| 1553 | recorded in `result.json` | 3,739 | 65 | pass |

The panel indices and all source hashes were frozen in `protocol_v2.json`
before the corrected run. The producer reads code IDs from the archived
case file but does not read its root coordinates. `audit_v2.py` uses the
checked repository Sage launcher and those archived roots only after the
producer result exists. It verifies `H(u)=0` for all eight roots per family,
the exact zero/one masks, and target decisions. The archived full 1,554-family
Sage census separately established eight distinct roots per admissible
two-code specialization; this experiment recomputes the finite bridge for
its eight selected families.

## Cost and next gate

The one-process Python producer took **43.198 s** for eight families,
including 0.265 s of trace-dual setup. Its measured family phases totaled
0.014 s polynomial specialization, 0.644 s trace residues, and **42.176 s
feature products**. Observed self peak was 26,394,624 bytes. The independent
Sage replay took 0.158 s inside its audit interval after startup and after
loading archived roots, with observed self peak 257,523,712 bytes. These
intervals are exploratory component timings on an ordinary host; the
producer's root-free method currently incurs per-family feature-product
work and does not compress the code-pair count. `candidate_id` is `null`.

The next experiment is a **two-code-prefix quotient**: retain at least two
choices on each product-code axis, derive any cubic bit common to every
root across that rectangle without specializing `H` once per code pair,
and compare its exact rejections with the archived 810 reciprocal-coordinate
families rejected in two-axis-free rectangles. Freeze positive and negative
N41 inputs, count polynomial operations, target-dependent queries, witness
retention, memory, and total wall. A native quotient kernel alone can reduce
the 42.176-second feature-product stage, but region-level sharing is needed
before attempting the N131 W23 public-point relation within the declared
600-second/4-GiB envelope.
