# G33-005: local two-chord bit circuit for an s=5 IR

This specifies a CNF construction from the three archived Lead 2B s=5
canonical IR fixtures. It avoids a case split over the 4,096 choices of
the first two signed points. It is a different encoding from both the
dynamic CDCL(Fp) solver and the previously exported static full-theory
closure. No survey-propagation interpretation follows from this note.

## Algebraic predicate

Each window has 32 rational abscissae and two lift signs, selected by
five index bits and one sign bit. For an affine point pair
\(U=(x,y), V=(v,w)\) with \(d=v-x\ne0\), set, in \(\mathbb F_p\),
\[
d=v-x,\quad n=w-y,\quad D=d^2,\quad T=dD,\quad
A=n^2-(x+v)D,\quad B=n(xD-A)-yT.
\]
The chord law gives \(U+V=(A/D,B/T)\); inverses are used only in this
mathematical explanation, not in the proposed circuit.

For selected \(P_0,P_1,P_2\) and public target \(Q\), calculate
\((A,B,d)\) for \((P_0,P_1)\) and \((C,E,f)\) for
\((Q,-P_2)\). The exact target predicate is
\[
A f^2=C d^2,\qquad B f^3=E d^3\pmod p. \tag{1}
\]
It is equivalent to \(P_0+P_1+P_2=Q\) whenever \(d,f\ne0\).
Those preconditions hold for **every** assignment in each archived
fixture: windows 0 and 1 have disjoint abscissae, and all three
target abscissae (112778, 125160, 505590) lie outside window 2.
The finite replay in `tests/compact_chord_equivalence.rs` independently
compares (1) with the repository's affine group law for all
\(64^3=2^{18}=262144\) signed selections per fixture. Model counts
are planted 1, natural 0, exact-UNSAT 0. This validates the algebraic
predicate for these exact fixtures.

## Deterministic Tseitin expansion

Use a 20-bit unsigned word for each canonical residue, since
\(p=884981<2^{20}\). Build two 64-entry multiplexer trees per window,
one for each coordinate. The six selector bits address the 64
precomputed signed rational points. A binary 2:1 mux uses four
three-literal clauses for `z = (not s and a) or (s and b)`;
constant propagation may simplify them. The unsimplified selection
network has \(3\cdot2\cdot20\cdot63=7560\) bit muxes. It reads
only the three 64-point windows and does not inspect any pair table.

Construct the field circuit for (1) with canonical-residue wires:

* For \(R=U+V\bmod p\), assert \(U+V=R+c p\) as a 21-bit
  binary equality, where \(c\) is one carry bit, and assert \(R<p\).
* For \(R=U-V\bmod p\), assert \(U+c p=V+R\) similarly.
* For \(R=UV\bmod p\), assert \(UV=pK+R\) as a **41-bit**
  binary equality, with a 20-bit quotient \(K\), and assert \(R<p\).
  The 41st bit rules out wraparound. Since \(0\le U,V<p\), the
  unique true quotient is less than \(p\) and fits 20 bits.

Use ordinary schoolbook shifted partial products and ripple full
adders to form the exact binary sums; constant multiplication by
\(p\) is a shifted-add network (\(p\) has ten set bits). For every
Boolean gate add its equivalence clauses: AND has three clauses,
XOR four, NOT two, and the mux four; a full adder is built from
two XORs, two ANDs and one OR. Compare \(R<p\) by a 20-bit
unsigned comparator. Gate equivalences give each auxiliary wire a
unique value for fixed selectors and quotient bits. The range and
41-bit equality force each quotient and remainder uniquely, so
existential projection onto the 18 selectors equals (1). Assert
both equalities in (1) bitwise.

The two chords and cross-products require 18 modular multiplications,
plus 13 modular additions or subtractions (counting negation of the
selected third ordinate as a subtraction). A direct, unshared
schoolbook implementation therefore uses
\(O(18\cdot20^2+3\cdot64\cdot20)\) Boolean gates and clauses,
independent of the 4,096 first-pair combinations. This is a locality
and construction-cost claim, **not** a lower clause count: a naive
bit blast is substantially larger than the existing 4,101-clause
planted full-theory closure. The emitted counts from
`tools/m3_compact_cnf.py` are:

| Archived IR | Variables | Clauses | DIMACS bytes | SHA-256 |
| --- | ---: | ---: | ---: | --- |
| planted | 61,735 | 207,958 | 3,834,601 | `5702fccfd7cc029d6b773087bd67a467b95a6e80064417edf18773ce87e4de65` |
| natural | 61,732 | 207,923 | 3,833,531 | `ab2f0a3e4641f87f68dc8e7f997ea583708a54aedb300d39fef3ab4709a3140a` |
| exact-UNSAT | 62,308 | 209,888 | 3,871,585 | `dd3e5ccf5e026f1fc98967cbb72b808e7149aab75aebab33116cf134e75a3253` |

The differing counts arise from public target constants and Boolean
constant propagation. Construction uses the fixed three 64-point
tables and the circuit, not a first-pair lookup. DIMACS generation
time and downstream solve time are separate costs; the counts alone
establish no solver advantage.

To reproduce one emitted file without overwriting an existing path:

```sh
python3 crates/prime-field-m3-cdclt/tools/m3_compact_cnf.py \
  crates/prime-field-m3-cdclt/fixtures/s5/lead2b-s5-planted.ir \
  /tmp/lead2b-s5-planted-compact.cnf
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover \
  -s crates/prime-field-m3-cdclt/tests -p test_m3_compact_cnf.py
CARGO_TARGET_DIR=/tmp/g33-compact-cargo-target cargo test \
  --manifest-path crates/prime-field-m3-cdclt/Cargo.toml \
  --test compact_chord_equivalence
```

## Controls and unresolved validation

The emitter hashes the exact canonical IR bytes and preserves the 18
selector variables, followed by its auxiliary variables. The
independent DIMACS parser in `tests/test_m3_compact_cnf.py` checks a
complete satisfying auxiliary assignment for the planted fixture,
checks that a changed selector fails at least one clause, and checks
rejected sample assignments for both null fixtures. It also checks
header counts, input digest, literal bounds, clause terminators and
collision refusal. Focused tests cover all primitive-gate input truth
tables and all 25 ordered input pairs for modular addition,
subtraction and multiplication over \(\mathbb F_5\), including
checks that flipping a result bit invalidates the generated witness.
The gate equivalences and exact integer-width
constraints give the semantic argument for existential projection;
the Rust test exhaustively checks the underlying group predicate.
There has **not** been an independent SAT-level enumeration of every
selector's auxiliary completions, so the parser test alone must not
be described as such a check. The natural and exact-UNSAT cases stay
null under the algebraic predicate; their emitted CNFs have not been
separately solved to completion.

A later SP cohort needs matched SAT and UNSAT cases, identical
encoding and solver settings, declared preprocessing, and setup
versus solve cost. The checkpoint gate remains a prerequisite to
that screen. No screen or SP run is performed here.
