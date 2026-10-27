# Frozen one-step Hecke commutator test

`inputs.json` pins six D=-7 matrices, the archived Hecke functions, the
multiplicity-aware collector, and both recovered-row receipts. The
degree-2 target source columns are fixed there before this test. The
conductor-60/90 certificates motivated the identity; conductors 42,
70, 150, and 210 are held out from rule selection.

For `R_l(P)=T_l(P)-a_l P` viewed as an integer row vector, commute the
degree-2 and degree-`l` correspondence operators at a source `S`:

`sum_{Q in T_l(S)} R_2(Q) - a_l R_2(S)
 = sum_{Q in T_2(S)} R_l(Q) - a_2 R_l(S)`.

The sums count repeated neighbors with multiplicity. For each fixed
missing degree-2 target, enumerate odd degrees from the saved degree
set in ascending order, then source columns in ascending order. An
anchor qualifies only when both first-step fibers and every needed
row are complete and inside the frozen class; the archived matrix
contains every row in the displayed identity except the target; its
coefficient is nonzero; and the full integer commutator vector is
zero in every column. Retain the first qualifying anchor, derive its
rational archived-row certificate, and independently replay the
integer identity. If no anchor qualifies, record `NO_ONE_STEP` with
the searched degree/source counts. Do not change the selection rule
after seeing held-out results.

Formalize the abstract commuting-operator identity in Lean with
explicit commutation and linearity hypotheses. The finite point-set
bridge, exact Hecke fibers, and archived-row availability remain
separate executable checks.
