# L1: inverted CDCL(T) with the native lin21 leaf as theory, killed on paper (2026-11-18)

This is a desk analysis. Nothing was built or run. All of it is
`[pcc:unverified]`.

## The lead

L1 proposed handing the native lin21 leaf to CaDiCaL as an IPASIR-UP
external theory, with SAT carrying only the side constraints. Its stated
value was twofold:

1. near-scan speed on subspace bases;
2. opening non-subspace factor bases (Hamming-weight normal-basis bases),
   where no scan exists.

## Why it gains nothing

**Subspace bases.** On V = span(1, …, z^(d−1)), the lin21 leaf *is* the
native scan: one linear solve per third summand
(`crypto:examples/ic_algebraic_floor/linear21.rs`). A CDCL(T) wrapper calls
the same leaf at least as many times, plus overhead. The lead's own
prediction, "wall within 2x of the native scan", is therefore at best parity
with the baseline it would be measured against. Under the success
criterion that is not an improvement.

**Non-subspace bases.** The leaf is linear only because p = x1·x2 lies in
span(1, …, z^(2d−2)), whose dimension is 2d − 1. That holds because V is a
polynomial span, so V·V has no wrap
(`linear21.rs`: "p ∈ span(1, …, z^{2d−2})"). For a Hamming-weight base
F_w = {x : wt(x) ≤ w}:

- s = x1 + x2 ranges over a union of weight shells, not a subspace;
- p = x1·x2 is dense in F_{2^n}.

So no F2-linear leaf in (s, p) exists to serve as the theory. The theory
would have to be a pair or root lookup. That is what the compact-s3
root-lemma propagators already did
(`cryptanalysis:experiments/compact-s3-m4-20261003/*/theory_solver.cpp`,
Q1419–Q1592), and the relations there came from the native root index, not
from search. The second benefit therefore does not exist.

## Spin-off checked and discarded: a Frobenius-orbit union base

On a Koblitz curve, take B = ∪ᵢ φⁱ(V), the union of the n Frobenius images
of V. Here φ(V) = {x² : x ∈ V}.

- **Linear case.** The lin21 leaf stays linear only when both pair summands
  lie in the same φᵃ(V). Applying φ^−a turns R = P1 + P2 + P3 into
  φ^−a(R) = P1′ + P2′ + φ^(c−a)(P3′), with P1′, P2′ ∈ V.
- **Cost.** Per target, this is a plain V-scan for each of the n target
  twists a, and each of the n slot offsets c − a. That is n² · 2^d leaves.
- **Yield.** About n² · 2^(3d) / (2 · 2^n). Per leaf, that is
  2^(2d) / (2 · 2^n), against 2^(2d) / (6 · 2^n) for plain V.
- **Verdict.** The same rate up to the ordering constant 3. Plain V
  achieves this anyway by running on more targets, so there is no gain.

## Decision

Kill. The remaining open item in this lead set is round-4 lead D (Macaulay
rank of the bilinear (t; q) system), which L4's counting check showed
carries all the isolating information. It is a measurement with a 3% prior
in round 4. It is not a SAT lead and is not started here.
