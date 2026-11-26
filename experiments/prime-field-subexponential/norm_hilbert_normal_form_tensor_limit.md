# Standard norm normal forms lose the input tensor compression

The norm quadrics have block-Hankel Hessians of displacement rank at most
four. A possible implicit solver would preserve that short representation
through homogeneous reduction. This control tests the standard monomial
normal-form map at the largest graded layer of each deterministic quotient.

Fix the row-echelon standard monomials $\mathcal B_d$. The exact map

\[
 \operatorname{NF}_d:S_d\longrightarrow
 \operatorname{span}(\mathcal B_d)\subseteq S_d
\]

sends every degree-$d$ monomial to its quotient coordinates. Across a split
$L\sqcup R$ of the variables, regard its coefficient tensor as a matrix with

\[
 (\text{target exponents on }L,\text{source exponents on }L)
\]

on the rows and the corresponding $R$-data on the columns. Its rank is the
operator-Schmidt rank, hence the minimum bond dimension across that cut for
an exact matrix-product-operator representation of this fixed map.

Every balanced variable subset gives:

| variables | peak degree | quotient dimension | cuts | minimum rank | median rank | maximum rank |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 3 | 1 | 3 | 3 | 2 | 2 | 2 |
| 4 | 1 | 4 | 6 | 2 | 2 | 2 |
| 5 | 2 | 8 | 10 | 9 | 12 | 13 |
| 6 | 2 | 13 | 20 | 13 | 17 | 19 |
| 7 | 3 | 21 | 35 | 36 | 69 | 83 |
| 8 | 3 | 40 | 70 | 59 | 107 | 125 |
| 9 | 3 | 66 | 126 | 82 | 136 | 158 |
| 10 | 4 | 121 | 252 | 243 | 583 | 652 |

Testing every balanced subset makes the statement insensitive to variable
ordering: every tensor-train ordering has one of these subsets as its middle
cut. In dimension ten even the best middle cut needs bond dimension 243, and
the median needs 583. The rank-four input displacement representation has
therefore been lost by the standard peak-degree normal form.

There is also a complement-independent version. Keep the output index of the
canonical quotient map

\[
 q_d:S_d\longrightarrow A_d
\]

on one side of each cut and flatten only its source exponent string. A change
of basis in $A_d$ performs invertible row operations, so these ranks are
intrinsic to $q_d$ and do not depend on a section back into $S_d$:

| variables | minimum intrinsic rank | median intrinsic rank | maximum intrinsic rank |
| ---: | ---: | ---: | ---: |
| 3 | 3 | 3 | 3 |
| 4 | 3 | 3 | 3 |
| 5 | 8 | 9 | 10 |
| 6 | 8 | 9 | 10 |
| 7 | 24 | 30 | 35 |
| 8 | 24 | 30 | 35 |
| 9 | 38 | 50 | 56 |
| 10 | 64 | 105 | 126 |

Thus changing the monomial complement cannot make the canonical quotient map
itself a constant-bond linear tensor train with one global quotient output.
At dimension ten every ordering needs a middle bond of at least 64, and a
median balanced cut needs 105.

## Exact limit

These are exact finite-field ranks for one deterministic coefficient triple.
The larger operator-Schmidt ranks apply only to the fixed row-echelon normal
form. The intrinsic ranks are independent of quotient basis and complement,
but apply to linear tensor networks with a global quotient output. A circuit
that distributes or nonlinearly encodes that output, approximate reduction,
or a solver that never constructs quotient maps may behave differently. The
data do not prove an asymptotic lower bound and do not improve the DLP
exponent.
