# Scalar two-list Reed--Solomon recovery is already Subset Sum

The paired inverse cannot be solved merely by invoking generic exact
list recovery for a Reed--Solomon code.  At redundancy one, that recovery
problem is exactly modular Subset Sum.

Let \(x_1,\ldots,x_m\) be distinct, let \(k=m-1\), and define

\[
 \lambda_i=\left(\prod_{j\ne i}(x_i-x_j)\right)^{-1}.
\]

A word \(y\in\mathbb F_p^m\) is the evaluation of a polynomial of degree
less than \(k\) if and only if its unique dual syndrome vanishes:

\[
 \sum_i\lambda_i y_i=0.
\]

Now supply the two-value list

\[
 y_i\in\{\beta_i,\ \beta_i+\delta_i\}.
\]

Writing the choice as \(s_i\in\{0,1\}\), exact list recovery asks for

\[
 \sum_i s_i(\lambda_i\delta_i)
   =-\sum_i\lambda_i\beta_i.
\]

The differences \(\delta_i\) and one baseline value can encode arbitrary
weights and target in \(\mathbb F_p\).  Thus an output-sensitive decoder at
this rate would solve modular Subset Sum with the same number of solutions.
The frozen controls construct the lists from two arbitrary weight panels and
exhaust all 128 choices over \(\mathbb F_{101}\); the subset-sum, dual
syndrome, and augmented-Vandermonde rank tests agree on every choice.

For redundancy \(h\), the dual code similarly gives an \(h\)-dimensional
vector subset sum, although the column directions are constrained by the
dual Vandermonde curve.  This does not prove hardness for the hyperelliptic
inverse: its local symbols are unions of lines in the coupled product code
\(RS_b\times RS_c\), not arbitrary scalar lists.  It does show that
Reed--Solomon structure and list size two alone are insufficient.  A positive
decoder must exploit the conjugate-line geometry and the coupling between
\(B\) and \(C\), or another property not present in scalar exact list
recovery.

[Exact control](rs_two_list_subset_sum.py)

~~~sh
python3 rs_two_list_subset_sum.py |
  cmp - rs_two_list_subset_sum.json
~~~
