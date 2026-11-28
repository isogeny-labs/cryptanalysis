# Higher-degree known-log atoms trade sourcing for a larger norm system

The Abel-curve intersection bound prevents sourcing enough degree-one fibers
with known discrete logarithms. A natural relaxation uses effective divisors
of degree $q$, with $1\le q\le g$, and the binary pair $\{D,\iota D\}$.

The Abel image $W_q$ has $O_g(p^q)$ rational effective divisors inside a
Jacobian subgroup of order $p^{g+o(1)}$. Uniform known-scalar sampling
therefore hits it with probability at most

\[
 p^{q-g+o(1)}
\]

for $q<g$. At $q=g$, Riemann--Roch makes every degree-$g$ divisor class
effective, so known-log atom setup becomes efficient.

This gain enlarges the inversion system. Binary coverage still needs

\[
 m=g\log_2p+O_g(1)
\]

slots. The product of the degree-$q$ Mumford factors has degree $qm$, and the
associated projective section space has

\[
 r=qm-g=qg\log_2p+O_g(1)
\]

variables. The fixed-genus semi-regular norm model has quotient length
$2^{r+o(r)}$, hence $p^{qg+o(1)}$. Increasing the atom degree therefore makes
the explicit algebraic inverse worse even as it makes known-log sourcing
easier.

The exponent ledger is:

| quantity | exponent in $p$ |
| --- | ---: |
| known-log degree-$q$ sourcing | $g-q$ |
| explicit semi-regular quotient | $qg$ |
| all binary orientations | $g$ |
| generic meet in the middle | $g/2$ |

No $1\le q\le g$ makes all of these exponents vanish. At the only setup-free
endpoint, $q=g$, choosing atoms $D_i=[2^i]G$ makes the orientation equation

\[
 Q=\sum_i\epsilon_iD_i
\]

exactly signed-binary discrete logarithm. The Mumford coordinates give a
succinct doubling circuit for the instance, but not a bit predicate: doubling
is a bijection on the odd prime-order component, so both sign branches always
have group predecessors.

## Exact limit

The sourcing estimate is a dimension/counting bound and the quotient exponent
is the semi-regular model measured in the companion controls, not a lower
bound on every structured solver. The ledger does not exclude an implicit
algorithm specialized to degree-$q$ factor blocks. It shows that merely
raising the atom degree and applying standard enumeration, meet-in-the-middle,
or Macaulay methods cannot produce $p^{o(1)}$ work.
