# Folded list recovery passes the size test but not the known decoder theorem

The split-fiber norm inverse can be viewed as list recovery for a rational
evaluation code.  Folding gives a useful conditional target: both its explicit
input and its expected output can be \(p^{o(1)}\).  Existing folded
Reed--Solomon list-recovery theorems do not apply, because the Cartesian branch
list grows exponentially in the folding order.

## Rational and interleaved-code views

For each split abscissa \(x_i\), the section condition is

\[
 C(x_i)=t_i^{\pm}B(x_i),\qquad
 t_i^{\pm}=\frac{\pm y_i-v(x_i)}{u(x_i)}.
\]

Here \(\deg B\le b\), \(\deg C\le c\), and
\(b+c=m-g-1\).  Thus the unknown ratio \(C/B\) belongs to a projective
rational evaluation code with about \(m-g\) field symbols of information in
\(m\) positions.  Equivalently, the pair of evaluation vectors
\((B(x_i),C(x_i))\) belongs to a product of two Reed--Solomon codes, while its
local symbol is constrained to the union of the two known lines

\[
 \{(z,t_i^+z):z\in\mathbb F_p\}\ \cup\
 \{(z,t_i^-z):z\in\mathbb F_p\}.
\]

This interleaved formulation is linear before imposing the two-line local
lists.

## Ordinary multiplicity interpolation misses by a factor two

Let a bivariate interpolation polynomial have \(Y\)-degree \(L\), and require
multiplicity \(s\) at both branch points over every \(x_i\).  It imposes

\[
 2m\binom{s+1}{2}=m s(s+1)
\]

linear conditions.  After substituting \(Y=C/B\) and multiplying by \(B^L\),
the term \(q_j(X)Y^j\) has degree at most

\[
 \deg q_j+jc+(L-j)b.
\]

To force the substituted polynomial to vanish identically, this weighted
degree must be below \(ms\).  With \(b,c=m/2+O_g(1)\), the largest possible
monomial count is asymptotically

\[
 \max_L (L+1)(ms-Lm/2)
 =\left(\frac12+o(1)\right)ms^2.
\]

This is only half the condition count.  The low-degree polynomial
\((uY+v)^2-f\) vanishing on both branches is the universal curve equation;
after substitution it reaches the degree-\(ms\) boundary and gives the
original norm identity, not an identity below the forcing threshold.  The
ledger performs the exact finite monomial count through multiplicity 48.

## Folding has subexponential input and output

Take

\[
 m=g\log_2p+\lceil\sqrt{\log_2p}\rceil,
 \qquad f=\lceil\sqrt{\log_2p}\rceil.
\]

Group the evaluation points into multiplicative or additive orbit blocks of
length \(f\).  Finding all-split blocks takes expected \(2^f=p^{o(1)}\)
fiber trials per block.  Each block has the explicit Cartesian list of its
\(2^f\) sign tuples, and there are \(O_g(\sqrt{\log p})\) blocks.  Hence the
whole folded input has size \(p^{o(1)}\).  The expected number of valid global
sections is

\[
 \frac{2^m}{p^g}=2^{O(\sqrt{\log p})}=p^{o(1)}.
\]

Thus neither input nor output size rules out a subexponential folded decoder.

For multiplicative blocks this sourcing step also has a character-sum proof.
Choose a multiplier whose first \(f\) powers do not identify two geometric
branch roots.  Expanding the product of the \(f\) quadratic-residue
indicators gives a main term \(p/2^f\); every nonempty character product is
nonsquare and contributes \(O_g(f\sqrt p)\).  Hence there are
\(p/2^f+O_g(f\sqrt p)\) valid starts.  The chosen
\(f=\Theta(\sqrt{\log p})\) lies safely in the range where the main term
dominates.  The finite control over \(\mathbb F_{101}\) enumerates the
corresponding short blocks exactly.

## Why the standard folded-RS theorem does not apply

An \(f\)-folded symbol must list all branch tuples in its block, so its
ordinary list size is

\[
 \ell=2^f.
\]

For zero errors, the maximum decoding slack below the distance boundary is

\[
 \varepsilon=1-R=\frac{g}{m}=\Theta(1/\log p).
\]

Capacity-level folded Reed--Solomon list recovery requires folding parameter

\[
 f=\Omega(\ell/\varepsilon^2).
\]

In this instance that would require

\[
 f=\Omega(2^f\log^2p),
\]

which is impossible.  The 2018 algorithms also place candidates in an affine
space of dimension depending at least linearly on \(\ell\), and their pruning
enumerates powers of \(\ell\).  The 2026 near-linear algorithms retain the
same parameter regime: \(\ell\), \(1/\varepsilon\), and the folding or
multiplicity order are fixed for the standard near-linear statement.

The issue is not the total explicit list size, which is subexponential here.
It is that ordinary list recovery treats the \(2^f\) Cartesian tuples as
unrelated symbols and therefore asks the folding order to dominate its own
exponential.

## Exact remaining opportunity

A positive result would need a decoder for the product code
\(RS_b\times RS_c\) with coordinate lists that are unions of two lines, or a
folded rational-code decoder whose complexity depends on the succinct
Cartesian description rather than on \(\ell=2^f\) through the standard
folding requirement.  If such a decoder ran in time polynomial in the
explicit block lists, \(1/\varepsilon\), and \(\log p\), and output all
solutions, the parameters above would give the missing \(p^{o(1)}\) inverter.

No such theorem is established here.  Folding reorganizes the branch entropy
but does not by itself solve it.

- Kopparty, Ron-Zewi, Saraf, and Wootters,
  [Improved Decoding of Folded Reed--Solomon and Multiplicity Codes](https://ieee-focs.org/FOCS-2018-Papers/pdfs/59f212.pdf).
- Goyal, Harsha, Kumar, and Shankar,
  [Fast List Recovery of Univariate Multiplicity Codes](https://doi.org/10.4230/LIPIcs.APPROX/RANDOM.2026.67).

[Executable ledger](folded_list_recovery_ledger.py) ·
[Frozen ledger](folded_list_recovery_ledger.json) ·
[Split-block control](folded_split_blocks.py) ·
[Frozen split blocks](folded_split_blocks.json)

```sh
python3 folded_list_recovery_ledger.py | cmp - folded_list_recovery_ledger.json
python3 folded_split_blocks.py | cmp - folded_split_blocks.json
```
