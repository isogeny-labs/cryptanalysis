# Prime-field subexponential index-calculus research

The [research note](prime_field_subexponential.md) gives written arguments for an embedding-degree-one family of absolutely simple genus-two Jacobians and an order-free complexity bound for growing imaginary hyperelliptic genus. It also proves a coverage threshold for sums over a small random factor base and reduces fixed-genus index calculus to finding those sums. The general inversion algorithm remains open. The genus-two pairing reduction is classical, and the family argument assumes that the curve and subgroup are supplied. [pcc:unverified]

| Fixture | Scope |
| --- | --- |
| [Frey–Rück script](frey_ruck_witness.py) and [output](frey_ruck_witness.txt) | Point counts, pairing, bilinearity and discrete logarithm in one subgroup of order seven over $\mathbb F_{29}$ |
| [Evaluation-code script](subexp_code_check.py) and [output](subexp_code_check.json) | Evaluation-code rank versus direct Jacobian addition on 3,906 subsets of a fixed point list over $\mathbb F_{29}$ |

## Reproduce the exact checks

Use the checked Sage launcher from the repository root. For a source checkout without the launcher, follow the [Sage release instructions](../../docs/SAGE_RELEASE.md).

```sh
fixture_dir=experiments/prime-field-subexponential
replay_dir="$(mktemp -d)"
./sage -python "$fixture_dir/frey_ruck_witness.py" > "$replay_dir/frey_ruck_witness.txt" &&
  diff -u "$fixture_dir/frey_ruck_witness.txt" "$replay_dir/frey_ruck_witness.txt"
./sage -python "$fixture_dir/subexp_code_check.py" > "$replay_dir/subexp_code_check.json" &&
  diff -u "$fixture_dir/subexp_code_check.json" "$replay_dir/subexp_code_check.json"
```

The two frozen outputs are retrospective producer fixtures from the research workspace, using Conda SageMath 10.10 and Python 3.14.10. The scripts pin their random seeds. Both scripts were replayed in that environment before the import, with byte-for-byte agreement against the frozen outputs. The repository’s patched Sage launcher was unavailable for that replay. The outputs cover exact finite-field arithmetic with no timings. The evaluation-code script uses exhaustive enumeration. [pcc:unverified]

## Proof status

The written proofs and their hypotheses are in the research note. A Lean formalization remains open. It would need the abelian-surface classification and pairing results for the genus-two family, the character estimates and Riemann–Roch evaluation for the coverage result, and the small-place generation and exact subgroup relation arguments for the growing-genus bound. The mathematical claims and finite fixtures have unverified PCC standing. [pcc:unverified]


## Fixed-genus strategy ledger

The [genus 2--7 strategy ledger](best_strategy_genus_2_7.md) separates three end-to-end exponents: Pollard rho, balanced smoothness-only index calculus, and the proved double-large-prime method. Under a bounded-degree plane model and a cyclic degree-zero class group (or known class-group structure), the last has expected time \(\widetilde O(p^{2-2/g})\). It improves the accounted exponent in genera 3--7 and ties rho in genus 2, but remains exponential in \(\log p\); it is not the requested fixed-genus subexponential breakthrough. [pcc:unverified]

```sh
fixture_dir=experiments/prime-field-subexponential
python3 "$fixture_dir/strategy_exponents.py" |
  diff -u "$fixture_dir/strategy_exponents.json" -
python3 -m py_compile "$fixture_dir/strategy_exponents.py"
```


## Fixed-genus oversampling controls

The [oversampling regularity note](oversampling_regular_limit.md) tests whether deliberately creating multiple transverse branch-product solutions lowers Macaulay stabilization degree. The large-field controls plant up to ten solutions over $\mathbb F_{101}$, exhaust every branch assignment, and record the cumulative quotient through degree six. They do not establish an asymptotic solving-degree bound or a subexponential algorithm. [pcc:unverified]

The [semi-regular branch analysis](semiregular_branch_barrier.md) compares those degrees with the Hilbert/Krawtchouk prediction and records genus 2–7 ledgers for branch degrees two through four. It identifies the low-degree-syzygy requirement for a successful direct algebraic attack; it is a model calculation, not a lower bound. [pcc:unverified]

```sh
fixture_dir=experiments/prime-field-subexponential
python3 "$fixture_dir/high_density_branch_regular.py" |
  diff -u "$fixture_dir/high_density_branch_regular.json" -
python3 "$fixture_dir/multiplanted_branch_regular.py" |
  diff -u "$fixture_dir/multiplanted_branch_regular.json" -
python3 "$fixture_dir/semiregular_krawtchouk_ledger.py" |
  diff -u "$fixture_dir/semiregular_krawtchouk_ledger.json" -
python3 "$fixture_dir/semiregular_branch_degree_ledger.py" |
  diff -u "$fixture_dir/semiregular_branch_degree_ledger.json" -
```

## Structured split-abscissa control

The [structured-abscissa note](structured_abscissa_limit.md) compares every split-fiber arithmetic-progression set on the genus-two control curve over $\mathbb F_{101}$ with matched random panels. All 112 systems certify at degree four. This is finite negative evidence, not an asymptotic lower bound or a subexponential algorithm. [pcc:unverified]

The run also fixes a sparse-row bug for zero planted parameters and includes a one-variable regression.

```sh
fixture_dir=experiments/prime-field-subexponential
python3 "$fixture_dir/certificate_zero_regression.py"
python3 "$fixture_dir/structured_abscissa_search.py" |
  diff -u "$fixture_dir/structured_abscissa_search.json" -
python3 -m py_compile \
  "$fixture_dir/binary_graeffe_macaulay.py" \
  "$fixture_dir/binary_split_norm_control.py" \
  "$fixture_dir/toy_jacobian.py" \
  "$fixture_dir/multisection_span_control.py" \
  "$fixture_dir/structured_abscissa_search.py" \
  "$fixture_dir/certificate_zero_regression.py"
```

## Growing-genus cover transfer

The [cover-lift note](cover_lift_limit.md) records why pulling a fixed-genus DLP into a growing-genus cover does not compose with the existing all-small-place algorithm to give $p^{o(1)}$ work. The transfer is injective away from the cover degree, but degree-one base setup costs $p^{1-o(1)}$; partial lifts pay the Prym dimension, and complete fibers collapse to the source relation problem. [pcc:unverified]

```sh
fixture_dir=experiments/prime-field-subexponential
python3 "$fixture_dir/cover_lift_tradeoff.py" |
  diff -u "$fixture_dir/cover_lift_tradeoff.json" -
```

## Folded split-fiber list recovery

The [folded list-recovery note](folded_list_recovery_limit.md) rewrites norm inversion as recovery in $RS_b\times RS_c$ from coordinate lists that are unions of two lines. Folding $\Theta(\sqrt{\log p})$ coordinates gives subexponential explicit input and expected output, but ordinary folded-RS recovery sees lists of size $2^f$ and requires the impossible condition $f=\Omega(2^f\log^2p)$. This is a conditional target, not an algorithm. [pcc:unverified]

```sh
fixture_dir=experiments/prime-field-subexponential
python3 "$fixture_dir/folded_list_recovery_ledger.py" |
  diff -u "$fixture_dir/folded_list_recovery_ledger.json" -
python3 "$fixture_dir/folded_split_blocks.py" |
  diff -u "$fixture_dir/folded_split_blocks.json" -
python3 "$fixture_dir/cartesian_folded_linear.py" |
  diff -u "$fixture_dir/cartesian_folded_linear.json" -
```

## Composed split-root controls

The [composed-root note](composed_root_limit.md) tests complete multiplicative cosets, giving root polynomials $P(X^2)$, $XP(X^2)$, $P(X^4)$, and $XP(X^4)$. All 70 composed panels have the same certificate degrees as 70 matched random controls. Sparse right-hand sides alone do not create an early rank surplus. [pcc:unverified]

```sh
fixture_dir=experiments/prime-field-subexponential
python3 "$fixture_dir/composed_abscissa_search.py" |
  diff -u "$fixture_dir/composed_abscissa_search.json" -
```

## Projective two-line decoder target

The [projective subspace-list note](projective_subspace_list_limit.md) shows why treating each two-line symbol as one subspace erases the constraint, while ordinary affine list recovery incurs a mandatory factor of $p-1$ from scalar copies. All seven exact split panels have a one-dimensional homogeneous kernel: 101 affine vectors, 100 nonzero representatives, and one projective orbit. A positive decoder must preserve the union and quotient scalar orbits. This is a scope result, not a new decoder or subexponential algorithm. [pcc:unverified]

```sh
fixture_dir=experiments/prime-field-subexponential
python3 "$fixture_dir/projective_scaling_control.py" |
  diff -u "$fixture_dir/projective_scaling_control.json" -
```

## Paired hyperplane-transversal scope

The [paired-transversal note](paired_hyperplane_transversal.md) identifies the projective inverse with a non-spanning transversal of $m=d+g-1$ Vandermonde/RS row pairs. Every exact genus-two panel has one deficient signing and one projective kernel. Fixed excess alone cannot supply a generic decoder: a determinant reduction embeds Subset Sum in arbitrary prime-field row pairs with $m=d+1$. The reduction uses projectively repeated forcing pairs and does not establish hardness for the structured curve rows. [pcc:unverified]

```sh
fixture_dir=experiments/prime-field-subexponential
python3 "$fixture_dir/paired_hyperplane_control.py" |
  diff -u "$fixture_dir/paired_hyperplane_control.json" -
python3 "$fixture_dir/paired_subset_sum_control.py" |
  diff -u "$fixture_dir/paired_subset_sum_control.json" -
```

## Scalar RS two-list limit

The [scalar two-list note](rs_two_list_subset_sum.md) proves that exact Reed--Solomon list recovery from two values per coordinate is modular Subset Sum at redundancy one. Two exhaustive panels over $\mathbb F_{101}$ verify that the subset equation, dual syndrome, and augmented-Vandermonde rank test agree on all 128 choices. This does not establish hardness for the coupled hyperelliptic product code; it shows that RS structure and list size two alone are not enough. [pcc:unverified]

```sh
fixture_dir=experiments/prime-field-subexponential
python3 "$fixture_dir/rs_two_list_subset_sum.py" |
  diff -u "$fixture_dir/rs_two_list_subset_sum.json" -
```

## Conjugate-center Hankel quotient

The [conjugate-center note](conjugate_hankel_quotient.md) splits each branch slope as $-v/u\pm y/u$. The sign-independent Hankel term satisfies the order-$g$ recurrence defined by $u$, so it has rank at most $g$. In the growing genus-two panels, quotienting that center leaves a maximal-rank $(q-1)\times q$ signed matrix for every signing and reduces the final test to two residual equations. Their multilinear supports are nevertheless almost maximal: 63/62 of 63, 91/92 of 92, and 253/252 of 255 available monomials. The residual truth-table cut ranks reach 8 at seven slots and 16 at nine slots, attaining the full central-cut width and matching the meet-in-the-middle state scale. Exhausting all balanced bipartitions shows that both nine-slot residuals have rank 16 on all 126 cuts; the width is therefore unchanged by variable reordering. This is a compressed determinant formulation, not an exponent improvement. [pcc:unverified]

```sh
fixture_dir=experiments/prime-field-subexponential
python3 "$fixture_dir/conjugate_hankel_quotient.py" |
  diff -u "$fixture_dir/conjugate_hankel_quotient.json" -
```

## Polynomial Cornacchia limit

The [Cornacchia note](polynomial_cornacchia_limit.md) rewrites signed-fiber norm inversion as rational reconstruction from a chosen CRT square root of \(f\bmod U_0\). The reconstruction is efficient after the signs are known, but the critical degree budget gives \(m\) homogeneous equations in \(m+1\) coefficients for every allocation. Across all 1,016 sign assignments in the seven exact genus-two panels, every reconstruction kernel has projective dimension one; only the final target congruence isolates the planted regular candidate. This is a scope control, not a subexponential norm solver. [pcc:unverified]

~~~sh
fixture_dir=experiments/prime-field-subexponential
python3 "$fixture_dir/polynomial_cornacchia_control.py" |
  diff -u "$fixture_dir/polynomial_cornacchia_control.json" -
python3 -m py_compile "$fixture_dir/polynomial_cornacchia_control.py"
~~~

## Structured residual tensor-width census

The [structured tensor-width note](structured_tensor_width_limit.md) exhausts every distinct split-fiber arithmetic or geometric progression of lengths seven through nine on the genus-two control curve over $\mathbb F_{101}$, together with matched random panels. Across 41 structured and 41 random panels, progression structure does not lower the minimum balanced flattening rank. This is finite negative evidence, not an asymptotic lower bound or a subexponential algorithm. [pcc:unverified]

```sh
fixture_dir=experiments/prime-field-subexponential
python3 "$fixture_dir/structured_tensor_width_search.py" |
  diff -u "$fixture_dir/structured_tensor_width_search.json" -
python3 -m py_compile "$fixture_dir/structured_tensor_width_search.py"
```


## Structured residual displacement-rank census

The [displacement-rank note](structured_displacement_rank_limit.md) tests four standard Stein/Sylvester operators, cyclic and nilpotent shifts, and every binary/Gray/bit-reversed row-column order pair on the 41 structured residual panels and 41 matched random controls. Seven- and nine-slot tables have full row displacement rank; eight-slot minima are 14 or 15 out of 16 in both arms. Standard one-dimensional displacement generators do not compress these finite tables. This is finite negative evidence, not an asymptotic lower bound or a subexponential algorithm. [pcc:unverified]

```sh
fixture_dir=experiments/prime-field-subexponential
python3 "$fixture_dir/structured_displacement_rank.py" |
  diff -u "$fixture_dir/structured_displacement_rank.json" -
python3 -m py_compile "$fixture_dir/structured_displacement_rank.py"
```


## Elliptic-DLP reduction to every fixed hyperelliptic genus

The [elliptic-quotient note](elliptic_quotient_reduction.md) gives an explicit degree-$d$ map from a genus-$g$ hyperelliptic curve to any supplied elliptic curve, with $d=\lceil(g+1)/2\rceil$. A bounded shift search produces exactly $2g+2$ branch points, and norm after pullback is multiplication by $d$. Consequently, a universal $p^{o(1)}$ algorithm for fixed-genus hyperelliptic Jacobians would imply a classical subexponential elliptic-curve DLP algorithm. For $g\ge3$, the constructed curve has a rational branch point, so the implication already applies to universal odd-degree hyperelliptic algorithms. This is a scope reduction, not a DLP algorithm. [pcc:unverified]

```sh
fixture_dir=experiments/prime-field-subexponential
python3 "$fixture_dir/elliptic_hyperelliptic_cover_control.py" |
  diff -u "$fixture_dir/elliptic_hyperelliptic_cover_control.json" -
python3 -m py_compile "$fixture_dir/elliptic_hyperelliptic_cover_control.py"
```


## Paired evaluation-arrangement state count

The [paired-arrangement note](paired_arrangement_cohomology_limit.md) enumerates the complete evaluation-row matroid in all seven binary genus-two panels. At nine slots, 43,401 of 43,758 maximal subsets are bases, and the top Orlik--Solomon dimension is 19,098 versus the uniform maximum 19,448. Every balanced slot cut also has full matroid connectivity. Thus both the standard hyperplane-arrangement recurrence and pair-preserving matroid DP retain exponential state width rather than $p^{o(1)}$. This is a finite state-space diagnostic, not an arithmetic-circuit lower bound. [pcc:unverified]

```sh
fixture_dir=experiments/prime-field-subexponential
python3 "$fixture_dir/paired_arrangement_mobius.py" |
  diff -u "$fixture_dir/paired_arrangement_mobius.json" -
python3 -m py_compile "$fixture_dir/paired_arrangement_mobius.py"
The [dimension ledger](elliptic_locus_dimension.md) bounds this cover locus inside hyperelliptic moduli. Its codimension is at least 1, 2, 2, 4, 4, and 6 in genera 2–7, respectively, so the reduction does not obstruct a carefully quantified density-one theorem. Such a theorem must state its curve distribution and bound the exceptional set. [pcc:unverified]

```sh
python3 "$fixture_dir/elliptic_locus_dimension.py" |
  diff -u "$fixture_dir/elliptic_locus_dimension.json" -
```
