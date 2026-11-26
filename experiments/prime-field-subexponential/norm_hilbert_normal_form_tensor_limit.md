# Standard norm normal forms lose the input tensor compression

The norm quadrics have block-Hankel Hessians of displacement rank at most
four. A possible implicit solver would preserve that short representation
through homogeneous reduction. This control tests the standard monomial
normal-form map at the largest graded layer of each deterministic quotient.

Fix the row-echelon standard monomials (\mathcal B_d). The exact map

\[
 \operatorname{NF}_d:S_d\longrightarrow
 \operatorname{span}(\mathcal B_d)\subseteq S_d
\]

sends every degree-(d) monomial to its quotient coordinates. Across a split
(L\sqcup R) of the variables, regard its coefficient tensor as a matrix with

\[
 (\text{target exponents on }L,\text{source exponents on }L)
\]

on the rows and the corresponding (R)-data on the columns. Its rank is the
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

## Exact limit

These are exact finite-field ranks for one deterministic coefficient triple.
Operator-Schmidt rank is a lower bound only for tensor-network
representations of this fixed row-echelon normal-form map. A different
quotient complement, a nonlinear arithmetic circuit, approximate reduction,
or a solver that never constructs normal forms may behave differently. The
data do not prove an asymptotic lower bound and do not improve the DLP
exponent.
