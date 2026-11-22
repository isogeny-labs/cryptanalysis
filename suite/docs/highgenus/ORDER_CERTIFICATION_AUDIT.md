# Exact-order certification gap in high-genus relation lattices

Status: **audit finding, [pcc:unverified]**. This document records a mathematical qualification; it is not an independently verified order certificate.

## Exact statements

Let (G=\operatorname{Jac}(C)(\mathbf F_p)), let (P_1,\dots,P_m\in G) be the chosen factor-base classes, and define the surjective map (\varphi:\mathbf Z^m\to H=\langle P_1,\ldots,P_m\rangle) by sending standard basis vectors to (P_i). Its full relation lattice is (K=\ker\varphi), so ([\mathbf Z^m:K]=|H|).

Every **correctly verified** collected relation lies in (K). If the collected lattice (L\subseteq K) has full rank, then

\[
[\mathbf Z^m:L]=[\mathbf Z^m:K][K:L]=|H|[K:L].
\]

Consequently, the index of the *collected* relation lattice is an **upper multiple**, not in general the exact subgroup order. If fewer than all relations have been found, the multiplier ([K:L]) can exceed one.

The gcd of a **subset** of maximal minors is likewise a multiple of the determinantal divisor (the gcd over **all** maximal minors). Exact CRT reconstruction of the sampled minors does not remove this incomplete-sampling ambiguity.

If (H\subsetneq G), even proving (|H|) would not by itself prove (|G|).

## What the existing checks establish

- Verifying each relation by recomputing the group equality establishes (L\subseteq K), assuming the group law is correct.
- If a positive candidate (h) annihilates **every** element of (G), then the group exponent divides (h); this is not equivalent to (|G|=h).
- A finite number of random annihilation tests is a probabilistic diagnostic, not a universal annihilation proof.
- Membership of (h) in the Hasse–Weil interval does not force the correct value unless there is an additional uniqueness argument.
- Verifying a planted logarithm by scalar multiplication certifies that particular equality, **not** the claimed Jacobian order or group-law implementation.

## Requirements before promoting an exact-order claim

1. Validate every relation independently and certify its computation against a second arithmetic implementation, where feasible.
2. Establish that the collected lattice equals the entire kernel (for example, by a certified subgroup cardinality and matching Smith normal form invariant factors), rather than assuming enough sampled minors suffice.
3. Establish that the factor base generates the entire Jacobian, or explicitly report only the generated subgroup.
4. Obtain an independently certified (|G|) (for example by exact point counts and a proven zeta-function reconstruction, or another mathematically rigorous order computation). Cross-check against the relation-lattice index.
5. Record certificate artifacts and PCC standing. Until then use **candidate lattice index** or **estimated order**, with `[pcc:unverified]`, instead of **exact Jacobian order**.

## Adversarial regression tests to implement

- A generated group (G=\mathbf Z/6\mathbf Z) with one generator and only relation (12P=0): the collected lattice index is 12, although (|G|=6).
- (G=\mathbf Z/2\mathbf Z\times\mathbf Z/2\mathbf Z) with one nonzero factor-base element: (|H|=2\ne|G|=4).
- A full-rank relation matrix with sampled maximal minors having a gcd strictly larger than the gcd of all maximal minors.
- Random annihilation checks on groups with rare torsion components; do not promote a passing sample to a universal certificate.
- Inject one invalid relation and require an independent group-equality verification to reject it.

## Scope

This audit does not invalidate any individually verified planted-log scalar multiplication, and does not claim that the reported numerical orders are wrong. It identifies a proof gap in how **exact order** is justified. No speedup claim follows from this audit.
