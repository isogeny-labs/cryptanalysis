# Branch flips are principal minors of a self-adjoint interpolation projection

The paired hyperplane formulation can be narrowed further at the first
saturating depth. Choose \(h=r+1\) slots, equal to the homogeneous section
dimension, and fix one branch \(y_i\) above each abscissa \(x_i\). Let \(E\)
be the square matrix of those base evaluation rows. On the open set where
\(E\) is invertible, every branch assignment is a principal-minor query on
a structured projection.

## Interpolation projection

Split the section coefficients into the \(B\)-block and \(C\)-block in

\[
 F=B(y-v)-uC.
\]

Let \(J\) be the coefficient projection onto the \(B\)-block and put

\[
 P=EJE^{-1}.
\]

Then \(P^2=P\), with rank
\(q=\lfloor(r-1)/2\rfloor+1=\lfloor h/2\rfloor\). Flipping the ordinate in row
\(i\) changes only the \(B\)-block. If \(D\) is the matrix of all row
differences, then

\[
 D=\operatorname{diag}(c_i)EJ,
 \qquad
 c_i=\frac{-2y_i}{y_i-v(x_i)}.
\]

Consequently

\[
 K=DE^{-1}=\operatorname{diag}(c_i)P.
\]

For a flip set \(S\), with indicator vector \(s\), the selected square
matrix is

\[
 M_S=(I+\operatorname{diag}(s)K)E.
\]

Rows outside \(S\) form an identity block in the first factor, so

\[
 \det M_S
 =\det(E)\det(I+K_{S,S})
 =\det(E)\det((I+K)_{S,S}).
\]

The branch-selection problem at saturation is therefore exactly the search
for a singular principal submatrix of \(I+K\).

## Residue self-adjointness

This is not an arbitrary projection. Put

\[
 U(X)=\prod_{i=1}^h(X-x_i),
 \qquad
 W_i=\frac1{u(x_i)(y_i-v(x_i))U'(x_i)}.
\]

The \(B\)- and \(C\)-evaluation blocks are orthogonal for the diagonal
pairing \(W\). Indeed every cross term is a scalar multiple of

\[
 \sum_i\frac{x_i^d}{U'(x_i)}=0,
 \qquad 0\le d\le h-2,
\]

the standard Lagrange residue identity. Hence

\[
 WP=P^TW.
\]

Since \(K=\operatorname{diag}(c)P\), it is self-adjoint for the diagonal
weights

\[
 H_i=W_i/c_i
 \sim\frac1{y_i u(x_i)U'(x_i)}:
 \qquad HK=K^TH.
\]

Thus \(I+K\) is diagonally symmetrizable (and becomes symmetric after a
diagonal similarity over a small extension). Its nonsingular principal
subsets form the representable delta-matroid associated with a symmetric
principal-minor assignment.

## Exact controls and remaining target

The seven original genus-two panels and three extended planted divisors use
square sections of sizes two through eleven. They verify:

- the idempotence and expected rank of \(P\);
- both explicit diagonal self-adjointness identities;
- \(K=\operatorname{diag}(c)P\); and
- the direct determinant, determinant-lemma, and principal-minor values for
  all 4,092 branch assignments.

The square subproblems contain 1, 1, 1, 1, 1, 3, 3, 7, 14, and 22 deficient
assignments, respectively.

This is a genuine curve-specific compression beyond arbitrary paired
transversals, but it is not yet a search algorithm. A positive continuation
must find a vanishing principal minor of this diagonal-scaled interpolation
projection without querying its \(2^h\) subsets. Generic delta-matroid
feasibility finds nonsingular subsets rather than the rare singular subset,
so it does not immediately solve the inverse.

~~~sh
python3 interpolation_projection_control.py |
  cmp - interpolation_projection_control.json
python3 -m py_compile interpolation_projection_control.py
~~~

