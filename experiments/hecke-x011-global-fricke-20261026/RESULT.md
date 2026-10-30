# The Fricke involution on the 11a1 model is `P ↦ T − P`

On the genus-one curve `X_0(11)`, using the model

`E: y² + y = x³ − x² − 10x − 20`, with cusp infinity as the group origin,
the moduli-theoretic Fricke involution is the global algebraic map

`W_11(P) = T − P`, where `T=(16:-61:1)` is cusp zero.

This identifies the candidate coordinate map used by the [D=-2631
pointwise audit](https://github.com/isogeny-labs/cryptanalysis/pull/1194) with
the modular involution throughout the curve, and hence after good reduction
in every characteristic other than 11. It turns that audit's finite-class
commutation check into evidence about the actual Fricke action on the saved
Hecke fibers.

## Proof

The [explicit modular-curve model and cusp table](https://web.mat.upc.edu/joan.carles.lario/types.pdf),
Section 5.1, give `E`, cusp infinity `O`, and cusp zero `T=(16,-61)` in these
coordinates. The [moduli definition of the Atkin–Lehner
involution](https://public.websites.umich.edu/~asnowden/teaching/2013/679/L16.html)
dualizes a cyclic 11-isogeny, so `W_11(O)=T` and `W_11(T)=O`.

Any automorphism `w` of an elliptic curve is `P ↦ w(O)+u(P)` for an
origin-preserving automorphism `u`. The `j`-invariant of this curve is
`−122023936/161051`, different from `0` and `1728`; in characteristic zero
its origin-preserving automorphisms are `+1` and `−1`. Sage verifies `T` has
order five. If `u=+1`, then `w(T)=2T`, contradicting the cusp exchange
`w(T)=O`. Therefore `u=−1`, and `W_11(P)=T−P` for every geometric point.

The unique normalized weight-two newform at level 11 has Fricke eigenvalue
`−1`, independently agreeing with the action on invariant differentials;
the [LMFDB newform table](https://www.lmfdb.org/ModularForm/GL2/Q/holomorphic/11/2/a/)
records this sign. Sage also checks the modular degree of the 11a1
parametrization is one, so these exact coordinates give the curve itself.

## Reproducibility

The [frozen protocol](PROTOCOL.md) fixes the model and theorem before the
checks. Run `./sage --runtime-info` and
`./sage -python experiments/hecke-x011-global-fricke-20261026/verify.py`
from the repository root. The saved [runtime](runtime-info.json) and
[verification](verification.json) show conductor 11, modular degree one,
`T` of order five, Fricke sign `−1`, and `a_11=1`. The map is an involution
on every checked point over `F_7`, `F_13`, and `F_23`; the `F_23743` check
uses three distinguished points. The Q-level proof above supplies the
global identity; these finite-field calculations check the implementation.

The [Lean module](formal/FrickeAffine.lean) proves the decisive conditional
algebraic step: an affine map with linear part `±1` that exchanges zero and
an element of order greater than two has linear part `−1`. It also proves
the resulting map is an involution and exchanges the cusps. `lake env lean
FrickeAffine.lean` passed under Lean `v4.35.0-rc4`, pinned Mathlib revision
`021c46bdd042f67b538b9f9871d556a93713a9a9`;
[`#print axioms`](formal/build-output.txt) reports only `propext` for all
four declarations. `lean4checker --fresh` was unavailable. The full modular
theorem's Lean bridge is still open: formal definitions of `X_0(11)`, its
Fricke moduli automorphism, this Weierstrass coordinate isomorphism, and
the classification of origin-preserving automorphisms for the curve are not
in this module. The written proof uses those mathematical inputs explicitly.

## Visual report and graph review (2026-10-30)

The [PDF report](report.pdf) contains this report, the
[global-identity evidence diagram](evidence.svg) (editable [Graphviz source](evidence.dot)),
and the [saved finite-field coverage plot](coverage.svg). Rebuild it with
`python3 experiments/hecke-x011-global-fricke-20261026/build_report.py`;
the renderer requires Graphviz, ReportLab and PyMuPDF. The
[rendering receipt](visuals-validation.json) records versions, exact source
hashes and the saved coverage counts. This documentation build does not rerun
Sage or Lean and supplies no new experimental or proof evidence.

The diagram distinguishes the written modular-curve inputs, the conditional
Lean step and the remaining formalization bridge. The plot reports exact
saved point counts, with no statistical uncertainty: 10, 10 and 25 enumerated
points over F7, F13 and F23, and only three distinguished points over F23743.
Those checks corroborate the implementation; they do not prove the global
identity or establish an ECDLP speedup.

Affected-graph check: inspected the sources for
`experiments/volcano-ic/figures/census.svg` and `ecdlp.svg` (Koblitz descendant
counts, yield and solve-work comparisons), and
`experiments/hecke-d39-scalar-closure-20261030/evidence.dot` and `result.dot`
(the fixed F367 rank/control fixture). Their source data and finite claims do
not change under this documentation correction, so their figures are retained.
The associated `experiments/ic-candidate-catalog/curves.yaml` was checked;
this addition creates no curve record, isogeny route, subgroup-transport claim
or ISO1 admission. The new diagram records the global Fricke interpretation
without relabeling a conditional Lean lemma as the complete modular theorem.
