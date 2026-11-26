# Polynomial Cornacchia does not choose the square-root allocation

The split norm equation admits a tempting modular-square-root formulation.
It makes rational reconstruction efficient **after** the signs are chosen,
but it does not select the right CRT square root.  At the critical degree
budget, every sign assignment generically produces a reconstruction
candidate.

## From the norm equation to a modular square root

For the imaginary hyperelliptic model \(y^2=f\), write the target in Mumford
form \((u,v)\), with

\[
 f=v^2+uw.
\]

The binary signed-fiber section is

\[
 F=B(y+v)+uC,
\]

and its norm condition is

\[
 B^2w-2BvC-uC^2=U_0,
 \qquad U_0=\prod_{i=1}^m(X-x_i),
\]

up to the fixed projective scalar.  Put

\[
 R=uC+vB.
\]

Then

\[
 R^2-fB^2=-uU_0.
\]

At every root \(x_i\), the fraction \(R/B\) is therefore one of the two
square roots \(\pm y_i\) of \(f(x_i)\).  A sign assignment chooses one of the
\(2^m\) CRT square roots of \(f\bmod U_0\).  Given that choice, extended
Euclid or Padé reconstruction recovers the bounded pair \((R,B)\) quickly.

## Why rational reconstruction does not prune the signs

Let the degree bounds be \(\deg R\le d_R\) and \(\deg B\le d_B\).  In the
binary norm construction they satisfy

\[
 d_R+d_B=m-1.
\]

For prescribed signed values \(s_i\in\{y_i,-y_i\}\), reconstruction is the
homogeneous linear system

\[
 R(x_i)-s_iB(x_i)=0,
 \qquad 1\le i\le m.
\]

It has \((d_R+1)+(d_B+1)=m+1\) coefficients and only \(m\) equations.
Generically its projective kernel is one-dimensional for **every** sign
assignment.  Every proper prefix has even larger nullity.  Consequently a
Cornacchia tree based only on modular square-root compatibility cannot reject
a branch before the final target test.

The actual witness condition is the missing Mumford congruence

\[
 R\equiv vB\pmod u.
\]

It imposes \(g\) field conditions.  At occupancy, the \(2^m\) reconstructed
candidates are distributed across about \(p^g\) target classes, leaving the
expected constant witness count but no exponent saving.

This explains the circularity of a generic polynomial-Cornacchia proposal:
the fast step reconstructs a section from one selected prime above every
factor of \(U_0\); choosing those primes so that their divisor class is the
target is the original Jacobian subset-sum problem.

## Exact controls

The genus-two split panels exhaust all sign assignments for section
dimensions one through seven.  Every one of their 8 through 512 assignments
has a one-dimensional projective reconstruction kernel, and every
reconstructed norm is divisible by \(U_0\).  Some candidates at dimensions
four and above have \(B(x_i)=R(x_i)=0\) at a selected fiber; these are the
expected common-factor degeneracies rather than rational interpolants of one
chosen branch there.  Among the regular candidates, exactly the planted
assignment satisfies the target congruence in every panel.

This is a finite structural control, not a generic asymptotic lower bound.
It leaves algorithms that process all CRT roots implicitly, or exploit the
target congruence before selecting a root, open.  Ordinary Cornacchia/Padé
reconstruction applied independently to roots does neither.

## Reproduction

~~~sh
python3 polynomial_cornacchia_control.py |
  cmp - polynomial_cornacchia_control.json
~~~
