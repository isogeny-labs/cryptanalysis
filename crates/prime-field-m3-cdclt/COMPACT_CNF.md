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
predicate for these exact fixtures; the CNF gate compiler described
below has not yet been implemented or exhaustively checked.

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
bit blast may be substantially larger than the existing 4,101-clause
planted full-theory closure. Actual variable and clause counts must
be recorded from an emitted DIMACS before any solver comparison.

## Controls and unresolved validation

An emitter must hash the exact canonical IR bytes, preserve the 18
selector variables, record all auxiliary variables and construction
time, and parse its DIMACS back independently. It must check that
every gate-equivalence clause is emitted and that existential CNF
models project exactly to the group models on all 262,144 selectors
for the planted, natural, and exact-UNSAT fixtures. The null fixtures
must stay null under projection. The Rust algebraic test does not
substitute for that emitter check.

A later SP cohort needs matched SAT and UNSAT cases, identical
encoding and solver settings, declared preprocessing, and setup
versus solve cost. The checkpoint gate remains a prerequisite to
that screen. No screen or SP run is performed here.
