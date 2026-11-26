# Paired evaluation arrangements retain generic cohomology size

The weighted Frobenius witness count reduces inversion to high coefficients
of rational products with linear evaluation denominators. A standard way to
organize recurrences for such coefficients is through the matroid, or
equivalently the Orlik--Solomon state space, of the denominator hyperplane
arrangement. The binary hyperelliptic construction supplies \(2m\)
hyperplanes in a homogeneous section space of rank

\[
 h=m-g+1.
\]

If the conjugate pairing forced many row dependencies, the arrangement
state space could be much smaller than for generic hyperplanes.

The exact control reconstructs both evaluation rows above every split
abscissa in the seven genus-two norm panels. It enumerates every subset of
the \(2m\) rows, computes its rank over \(\mathbb F_{101}\), and forms the
matroid characteristic polynomial

\[
 \chi(T)=\sum_{A\subseteq E}(-1)^{|A|}T^{h-r(A)}.
\]

The absolute constant coefficient is the top Orlik--Solomon dimension. For
the uniform matroid it equals

\[
 \binom{2m-1}{h-1}=\binom{2m-1}{m-g}.
\]

## Results

| Slots \(m\) | Rank \(h\) | Actual bases | Uniform bases | Actual top dimension | Uniform top dimension |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 3 | 2 | 12 | 15 | 3 | 5 |
| 4 | 3 | 52 | 56 | 18 | 21 |
| 5 | 4 | 202 | 210 | 77 | 84 |
| 6 | 5 | 782 | 792 | 321 | 330 |
| 7 | 6 | 2,967 | 3,003 | 1,252 | 1,287 |
| 8 | 7 | 11,326 | 11,440 | 4,892 | 5,005 |
| 9 | 8 | 43,401 | 43,758 | 19,098 | 19,448 |

The small panels show dependencies caused by the paired geometry, but their
relative effect shrinks quickly. At nine slots, 99.18% of maximal subsets
are bases and the top dimension is 98.20% of the uniform value. For fixed
genus the uniform value grows as \(4^m/\sqrt m\) up to a genus-dependent
polynomial factor.

Thus the ordinary hyperplane-arrangement/creative-telescoping state space
does not give a subexponential coefficient engine for these controls. It is
already larger than the \(2^m\) branch space one wanted to avoid.

This is a finite state-space diagnostic, not an arithmetic-circuit lower
bound. It leaves recurrences that preserve the slot pairing in a way not
captured by the full denominator arrangement, direct Frobenius identities,
and algorithms using only the colorful coefficient rather than the whole
arrangement cohomology open.

~~~sh
python3 paired_arrangement_mobius.py | cmp - paired_arrangement_mobius.json
python3 -m py_compile paired_arrangement_mobius.py
~~~

