# Higher genus does not produce a constant-bond quotient tensor

The homogeneous Hilbert controls show that fixed genus 3--7 does not collapse
the explicit norm quotient. This control tests whether the additional norm
coefficients nevertheless compress its canonical quotient map as a linear
tensor network.

For each valid squarefree curve and measured graded layer, tensorize

\[
 q_d:S_d\longrightarrow A_d
\]

by the source exponent string and keep the quotient output index on one side
of the cut. The balanced flattening rank is invariant under changes of basis
in $A_d$ and does not choose a section back into the monomial space. Every
balanced variable subset is tested, so the minimum applies to every variable
ordering with a global output at one end.

Two independent curves over $\mathbb F_{101}$ give identical summaries in
each panel:

| genus | section dimension | peak degree | quotient dimension | minimum rank | median rank | maximum rank |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 3 | 8 | 3 | 32 | 24 | 30 | 35 |
| 4 | 8 | 2 | 24 | 13 | 14 | 15 |
| 5 | 8 | 2 | 23 | 13 | 14 | 15 |
| 6 | 8 | 2 | 22 | 13 | 14 | 15 |
| 7 | 8 | 2 | 21 | 13 | 14 | 15 |
| 3 | 9 | 3 | 57 | 38 | 50 | 56 |
| 4 | 9 | 3 | 48 | 37 | 49 | 56 |
| 5 | 9 | 3 | 40 | 34 | 46 | 56 |
| 6 | 9 | 3 | 35 | 34 | 45 | 56 |
| 7 | 9 | 3 | 30 | 33 | 45 | 51 |

The fixed-genus equations reduce the finite quotient dimension, especially
at section dimension eight, but do not create a constant middle bond. At
dimension nine even genus seven needs rank at least 33 for every ordering and
has median rank 45.

## Exact limit

These are exact finite-field ranks for two curves per genus and two section
dimensions. They are basis- and complement-independent for the canonical
linear quotient map with one global output. They do not cover a distributed
output encoding, nonlinear or approximate circuit, or an algorithm that
never constructs quotient maps. No asymptotic tensor-rank theorem or DLP
exponent improvement is claimed.
