# Target-code XOR projection on the W23 six-pair public circuit

**The frozen public W23 six-pair XOR subsystem imposes no equation on
its 132 source-code wires after all other XOR variables are eliminated.**
The same statement holds for the 42 code wires of the matched N41
six-pair public formula. An independent ordered peel supplies one
non-code pivot for every original XOR row: **38,657/38,657 at N131** and
**3,689/3,689 at N41**. This excludes a *linear-only* target-derived
code-family filter from these exact encodings. The nonlinear CNF/AND
constraints still couple codes, pair outputs, and the public target;
the result does not classify their solutions.

The [first screen](result.json) rebuilds each public XCNF from its
frozen circuit and target and matches the archived SHA-256 byte for
byte. Projecting only CNF-private XOR variables reduces N41 from 3,689
to 1,319 XOR rows and N131 from 38,657 to 11,370. Neither projected
basis contains a code-only row. The stronger [code-boundary screen](code_result.json)
then treats *every* non-code variable as eliminable in the XOR system;
both projected systems have zero rows and zero contradictions. Its
certificate is independent of CNF satisfiability.

| Frozen public XCNF | XOR rows | Code wires | CNF-private residual rows | Code-only residual rank | Ordered non-code pivots | Peak self RSS in first screen |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| N41 six-pair, unpinned relation control | 3,689 | 42 | 1,319 | **0** | 3,689 | 64,110,592 B |
| N131 W23 six-pair, frozen public point | 38,657 | 132 | 11,370 | **0** | 38,657 | 366,739,456 B |

The [independent peel](peel_result.json) scans the raw XCNF without
calling the projection routine. At each step it chooses a non-code
variable appearing in only one *remaining* XOR row, removes that row,
and updates incidence. Initially 26,534 N41 and 56,312 N131 non-code
variables have degree one. The process removes every row with distinct
pivots. Given arbitrary code values and arbitrary free-variable values,
assigning these pivots in reverse peel order satisfies every XOR row.
The [Lean theorem](PeelExtension.lean) proves this upper-triangular
extension for arbitrary Boolean right-hand sides and later-pivot
coefficients; its [`#print axioms` output](lean.stdout) lists only
`propext`. The concrete row-to-triangular bridge is the independently
recomputed finite peel certificate.

Both successful screens used the checked repository Sage launcher and
[runtime receipt](sage_runtime_info.json), one process, a 180-second
alarm for the first and code-boundary screens, and a 4-GiB
observational self-RSS limit. The first screen spent 0.197 s on N41 and
3.994 s on N131 inside its process; the code-boundary screen spent
0.285 s and 5.299 s respectively. These are ordinary-host structural
diagnostics, not solver or single-target online times. The [terminal
verifier](verify.py) checks source and rebuilt formula hashes, counts,
peel receipts, error streams, and the Lean transcript.

The first launch through system Python stopped on a missing `psutil`
import before arithmetic; its raw [stderr](run.stderr) is retained.
An initial independent auditor incorrectly required every row to have
a pivot unique in the *original* matrix. It stopped at that assertion;
the frozen source, [failure receipt](leaf_attempt1.json), and raw
[stderr](leaf_run.stderr) remain. The successful audit uses the
mathematically sufficient ordered peel. Neither failure is a relation
search outcome.

## Algorithmic decision

The exact N41 [unpinned group join](../n41_sixpair_shared_target_20261017/RESULT.md)
still supplies the relation control, and the frozen N131
[public SAT attempt](../n131_w23_sixpair_public_sat_20261017/RESULT.md)
remains `BOUNDED_UNKNOWN`. A useful next family predicate must combine
source-code information with at least one nonlinear field-multiplication
or elliptic-addition constraint. A cheap next falsifier is to isolate a
small target-to-code AND-gate cut in the W23 circuit, derive its exact
Boolean consequence, and test whole-code-family rejection on the
unpinned N41 public point before another N131 query. This screen is a
solver-representation component with `candidate_id: null`.
