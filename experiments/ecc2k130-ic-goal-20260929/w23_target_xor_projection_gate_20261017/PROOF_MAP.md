# XOR projection and ordered peeling proof map

For each frozen public XCNF, let `c` be its source-code wires and `u`
all other variables that occur in XOR rows. The XOR subsystem has the
form `A_c c + A_u u = b` over `GF(2)`. If elimination leaves zero
equations on `c` and no contradiction, every code assignment extends
to an XOR assignment. This implication concerns the XOR subsystem;
CNF/AND clauses remain essential and are not eliminated here.

The independent peel gives a stronger constructive certificate. Number
the XOR rows in peel order. Its chosen pivot for row `i` occurs in no
row numbered after `i`. Set all non-pivot variables freely and absorb
their contributions, including the chosen code bits, into each row's
right-hand side. The rows are upper triangular in the pivots: row `i`
contains pivot `i` and may contain only later pivots. Solve from the
last row backward. Because an earlier pivot is absent from every later
row, each choice preserves all equations already satisfied.

| Result | Lean declaration or finite evidence | Scope |
| --- | --- | --- |
| Any upper-triangular XOR system with one pivot per row is satisfiable for arbitrary right-hand sides | `PeelExtension.target_xor_any_rhs_satisfiable` | Checked in Lean 4.34.1, `#print axioms` only `propext` |
| Every N41 public XOR row has an ordered exclusive non-code pivot | `peel_result.json` and `peel_cert.py` | Exact 3,689-row finite scan, raw XCNF rebound by SHA-256 |
| Every N131 public XOR row has an ordered exclusive non-code pivot | `peel_result.json` and `peel_cert.py` | Exact 38,657-row finite scan, raw XCNF rebound by SHA-256 |
| CNF-private and code-boundary XOR projections | `result.json` and `code_result.json` | Separate elimination boundary choices on byte-matched frozen public XCNFs |

The Lean theorem models the triangular rows as Boolean right-hand
sides and lists of coefficients on later pivots. The finite peel checks
that the actual public XOR systems have exactly that structure. A
fully formal Lean parser and bit-matrix bridge for the XCNF bytes has
not been built; the read-only terminal verifier binds the source and
independent computational checks.
