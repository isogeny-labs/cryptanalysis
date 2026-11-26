# Best proved end-to-end baseline in genus 2--7

This note separates the best currently accounted exponent from the
experimental inversion directions in this archive. The setting is a
generic fixed-genus curve over a growing prime field. Exponents are in
field operations, suppressing factors \(p^{o(1)}\). The same generic
smoothness ledger applies to hyperelliptic and nonhyperelliptic curves;
their relation generators and constants differ.

The balanced factor-base line is conditional on the usual generic smoothness
and full-rank relation hypotheses, which must be proved for a claimed concrete
family.  The double-large-prime line below is stronger: it records a published
expected-time theorem, with its representation and group-structure hypotheses.
This is an end-to-end exponent ledger, not a subexponential result.

## A complete baseline ledger

Take a degree-one factor base of size \(B=p^\beta\). A generic reduced
degree-\(g\) divisor is factor-base smooth with probability

\[
  p^{-g(1-\beta)+o(1)}.
\]

Collecting \(B\) independent sparse relations therefore costs

\[
  p^{\beta+g(1-\beta)+o(1)}
  =p^{g-(g-1)\beta+o(1)}.
\]

A black-box sparse linear solve on a \(B\)-column matrix costs
\(p^{2\beta+o(1)}\) field operations and \(p^{\beta+o(1)}\) storage. Setup,
individual relation verification, and final DLP verification have no larger
exponent. Balancing relation collection and linear algebra gives

\[
 \beta=\frac{g}{g+1},\qquad
 E_{\rm FB}=\frac{2g}{g+1}.
\]

Pollard rho has exponent \(E_\rho=g/2\), since a generic Jacobian has order
\(p^{g+o(1)}\).

## The proved double-large-prime improvement

Gaudry, Thome, Theriault, and Diem proved an expected-time bound

\[
 E_{\rm DLP}=2-\frac{2}{g}
\]

for fixed-genus imaginary hyperelliptic curves with cyclic Jacobian.  Diem's
general-curve analysis proves the same exponent for nonsingular curves given
by bounded-degree plane models when the degree-zero class group is cyclic, or
when its structure is known.  Both results apply in particular to growing
prime fields.  The general-curve construction uses a factor base of exponent

\[
 \beta_{\rm DLP}=1-\frac1g,
\]

a sparse matrix with \(\widetilde O(p^{\beta_{\rm DLP}})\) columns, and a
large-prime tree with storage bounded by
\(\widetilde O(p^{1-1/g+1/g^2})\).  Relation-tree construction, final relation
collection, and sparse linear algebra are each bounded by
\(\widetilde O(p^{2-2/g})\); verification is lower order.

Primary sources: [hyperelliptic theorem and analysis](https://eprint.iacr.org/2004/153.pdf)
and [general bounded-degree plane-model theorem](https://arxiv.org/abs/math/0606607).

The resulting decision table is:

| Genus | Pollard rho | Balanced factor base | Double large prime | Best proved exponent | Asymptotic choice |
| ---: | ---: | ---: | ---: | ---: | --- |
| 2 | \(1\) | \(4/3\) | \(1\) | \(1\) | rho by constants; exponent tie |
| 3 | \(3/2\) | \(3/2\) | \(4/3\) | \(4/3\) | double large prime |
| 4 | \(2\) | \(8/5\) | \(3/2\) | \(3/2\) | double large prime |
| 5 | \(5/2\) | \(5/3\) | \(8/5\) | \(8/5\) | double large prime |
| 6 | \(3\) | \(12/7\) | \(5/3\) | \(5/3\) | double large prime |
| 7 | \(7/2\) | \(7/4\) | \(12/7\) | \(12/7\) | double large prime |

Thus the proved exponent improves from \(2g/(g+1)\) to \(2-2/g\) in every
genus at least three.  In genus two it ties rho at exponent one, so rho remains
the conservative practical default.  The unrestricted practical
double-large-prime algorithm is often faster than the deliberately simplified
variant used in the proof, but only the latter is entered in this theorem
ledger.

For hyperelliptic curves, Mumford arithmetic provides the direct relation
machinery.  For nonhyperelliptic curves, Diem's proof uses bounded-degree
plane models, maximally reduced divisors, and an explicit large-prime tree;
the proof controls special divisors rather than assuming generic smoothness.
The cyclic/known-group-structure condition remains material and must not be
silently dropped.

## Why the new inversion routes do not replace the baseline yet

The output-sensitive coefficient-lattice route in this archive has prefix
exponent

\[
 E_{\rm coeff}=g-\frac{2(g-1)}{g+2}=\frac{g^2+2}{g+2}.
\]

For genus \(2,\ldots,7\), this is respectively
\(3/2,11/5,3,27/7,19/4,17/3\), so it is not an end-to-end improvement over
the table. Its value is structural: it preserves the full
\(p^{g-1}\) residual codimension and identifies nonlinear root structure as
the missing ingredient.

Multiplicative-coset slots solve a different missing piece. Random cosets
have rigorously bounded second moment and constant target-averaged coverage
at occupancy. But the phase equations \(x_i^S=d_i\) define a reduced finite
cover of degree

\[
  S^m=p^{g+o(1)}.
\]

Replacing each powering equation by an addition chain makes every equation
quadratic but preserves that projection degree. A resultant, homotopy, lex
Gröbner basis, or enumeration that materializes those sheets therefore
does not give subexponential inversion. The section constraints must be
used before the phase cover is expanded.

For the \(g+1\)-point residual pencil, that joint operation is possible:
compute \(X^S\bmod U_t\) symbolically and take the gcd of the characteristic
coefficient equations in \(t\). Their degrees are \(O_g(S)\), so one
relation costs \(S^{1+o(1)}\) without enumerating \(S^{g+1}\) phases.
Collecting \(B\asymp S\) relations and solving the matrix both cost
\(S^{2+o(1)}=p^{2g/(g+1)+o(1)}\). This constructively realizes the table on
primes with a suitable divisor of \(p-1\), but does not change its exponent.
[Pencil/coset solver](pencil_coset_gcd.md)

## Exact remaining breakthrough condition

Let \(S=p^{o(1)}\), \(m=o(\log p)\), and \(S^m\asymp p^g\). The coverage
theorem supplies constant-probability bases on primes with \(S\mid p-1\).
A subexponential algorithm would follow from a solver that, on these bases,
does all of the following in \(p^{o(1)}\) expected work and storage:

1. intersects the section-norm family with the equations \(x_i^S=d_i\)
   without enumerating \(S^m\) root phases;
2. returns an actual signed divisor decomposition or certifies absence;
3. supplies enough independently distributed verified relations for a
   \(p^{o(1)}\)-column matrix, or bypasses that matrix with an equally
   complete logarithm-recovery step;
4. handles arbitrary growing primes, either by replacing the divisor
   condition \(S\mid p-1\) or by proving a suitable dense prime subsequence
   theorem and a separate generic-prime reduction.

No solver in the archive currently meets item 1. Consequently there is no
proved classical \(p^{o(1)}\) algorithm here. The best next target is not
another generic quadratic-system solver; it is a phase-sensitive algorithm
for the companion-power/decimated-trace structure that prunes the section
family before lifting root phases.

The sharpest current specialization chooses \(m=g\log_2p+O(1)\) split
hyperelliptic fibers and lets each slot choose one of its two conjugate
points. The factor base and relation elimination become polylogarithmic, and
a sharp Fourier calculation proves constant coverage over every odd prime
field. Inversion is the quadratic norm system \(U_{\boldsymbol z}=U_0\).
Its planted fibers are degree one through the seven tested dimensions, but
the first static certificate degree grows with the section dimension. A
direct norm inverse would change the exponent; ordinary Macaulay elimination
and prime-divisor allocation do not.
[Binary signed-fiber status](binary_signed_fiber_inversion.md)

On the disjoint-support chart, the norm inverse is equivalently a signed
Hankel-MinRank problem. The matrix has size
\((b+g)\times(b+1)=O_g(\log p)\), fixed row excess \(g-1\), and one known
rank-one Vandermonde update per sign. All exact split controls have a unique
rank-deficient signing. A polynomial-time signed Hankel solver would supply
the missing inversion primitive; enumerating its \(2^m\) signings does not.
[Compressed Hankel formulation](signed_hankel_minrank.md)

## Reproduction

The table is generated with exact rational arithmetic.

~~~sh
python3 strategy_exponents.py | cmp - strategy_exponents.json
~~~
