# Blind mathematical review: known-label edge equations and affine cycles

Date: 2026-11-01
Scope: the abstract algebraic statements in the task only.
Verdict (math statement only): **holds**, subject to the stated existence and invertibility conditions. No verdict is given on a proposed elliptic-curve application.

## Oriented edge equations in an abelian group

Let (V) be an abelian group and suppose the three equations, with the *same* vertex variables and verified right-hand sides, are

\[
R_0+R_1=T_{01},\qquad R_1+R_2=T_{12},\qquad R_2+R_0=T_{20}.
\]

Subtracting the middle equation from the sum of the other two gives

\[
\boxed{,2R_0=T_{01}-T_{12}+T_{20}.,}
\]

Cyclically, (2R_1=T_{01}+T_{12}-T_{20}) and (2R_2=-T_{01}+T_{12}+T_{20}). These are identities in (V), with no assumption that division by two is available. If one solution (R_0) exists, every possible (R_0) differs from it by an element of (V[2]=\{x\in V:2x=0\}), and the corresponding (R_1,R_2) adjust consistently. Thus (R_0) is unique exactly when the doubling map has trivial kernel on the admissible domain; existence must also be checked. In an odd-order subgroup, doubling is bijective, so the displayed expression determines (R_0).

For a path of edge-sum equations (R_i+R_{i+1}=T_i), substitution gives (R_{i+1}=-R_i+T_i). Along a closed path of length (m), the return map has coefficient ((-1)^m). An even cycle has return coefficient (+1): its alternating sum of edge labels must be zero, but it supplies no coefficient on the starting vertex. An odd cycle has return coefficient (-1): its alternating sum gives twice the starting vertex. Chords or other independent equations can add information, so this statement concerns the cycle alone.

## Affine path composition

Let (M) be a module over a field (F), hence an (F)-vector space, and let every step use a specified scalar and offset:

\[
z_{i+1}=a_i z_i+c_i,\quad a_i\in F,\ c_i\in M,\quad i=0,\ldots,m-1.
\]

Successive substitution gives

\[
z_m=A z_0+C,\qquad
A=\prod_{i=0}^{m-1}a_i,\qquad
C=\sum_{j=0}^{m-1}\left(\prod_{k=j+1}^{m-1}a_k\right)c_j,
\]

where an empty product is (1). The closed-path condition (z_m=z_0) is exactly

\[
\boxed{\,(1-A)z_0=C.\,}
\]

More generally, for any coefficient endomorphism (B=1-A), a start exists precisely when (C\in\operatorname{im}B), and is unique precisely when it exists and (\ker B=\{0\}). For scalar coefficients on a **nonzero** (F)-vector space, (1-A\ne0) makes multiplication invertible and yields the unique start (z_0=(1-A)^{-1}C). If (1-A=0), then (C=0) leaves every start possible, while (C\ne0) leaves none. The zero module is the trivial exception: it has one start regardless of the coefficient.

An explicit zero-coefficient counterexample uses (F=M=\mathbb F_5) and two steps

\[
z_1=2z_0+1,\qquad z_2=3z_1+2.
\]

Then (A=3\cdot2=1\pmod5) and (C=3\cdot1+2=0\pmod5), so (z_2=z_0) for **all five** starts. A closed path has been verified, but it does not recover its starting state. Changing the second offset from (2) to (3) gives (C=1), so no start closes the path.

In characteristic two, minus and plus coincide for vector-space coordinates. For edge-sum equations *in a characteristic-two vector space*, the triangle's right-hand side must sum to zero and (2R_0=0) is tautological; the triangle does not identify (R_0). For a general affine cycle over a characteristic-two field, recovery still depends on (1-A\ne0) (equivalently (A\ne1)); characteristic two by itself does not settle it. An elliptic-curve point group over a characteristic-two field is not itself a characteristic-two vector space: its point-doubling map must be assessed as a group homomorphism, not replaced by the field identity (2=0).

## What an elliptic-subgroup application still requires

The edge right-hand sides must be independently computable points in one specified abelian subgroup, and the asserted orientation, vertex identity, and pair equation (R_i+R_j=T_{ij}) must be verified in that subgroup. If a label is written (uP+vQ), its evaluation needs actual known points (P,Q), correct scalar and sign conventions, and a check that it equals the claimed edge point. A closed walk must refer back to the same state and use the same update rule at each occurrence; merely finding a graph cycle does not establish those equalities. To recover (R_0) from (2R_0), establish existence and injectivity of doubling on the admissible subgroup (for example, an odd-order subgroup). To infer any unknown scalar from a recovered point, supply a separate, verified relation between that scalar and the point; point recovery alone does not provide that relation. Affine recovery additionally requires a demonstrated vector-space or module coordinate model and the actual coefficient (1-A) for the claimed updates.

## Controls and blind compliance

- Substitution control: replacing (R_1) by (T_{01}-R_0) and (R_2) by (T_{12}-R_1) in (R_2+R_0=T_{20}) reproduces (2R_0=T_{01}-T_{12}+T_{20}).
- Composition control: the two-step formula gives (z_2=a_1a_0z_0+a_1c_0+c_1), matching the general expression.
- Degenerate control: the (\mathbb F_5) example explicitly tests both (A=1,C=0) and (A=1,C\ne0).
- Parity and characteristic controls: the cycle coefficient ((-1)^m) and the distinction between field characteristic and elliptic point-group doubling are stated explicitly.

sources_read: none; derivation is from the task's equations and first principles.
sibling_report_access: no
blind_compliance: I did not read producer Lean source, README, PR, receipt, review plan, another reviewer's report, or prior agent context. I did not inspect or edit the repository and did not run a build.
