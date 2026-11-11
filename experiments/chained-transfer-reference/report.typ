#set page(paper: "a4", margin: 18mm)
#set text(font: "DejaVu Sans", size: 10pt)
#set par(justify: true)
= Chained transfer differential reference
2026-11-11 · fixed F₁₀₁ fixture · producer-run development checks

*Standing: unverified.* The reference arithmetic predates this work and is
imported unchanged, but both implementations are run by this producer and
use Cantor reduction. Agreement is not signed independent verification.

== Pinned source and models
Native source: isogeny-labs/crypto commit
b280efc5c22b77718063514c09083af27d6b78c0, package
research/chained_jacobian_transfers_20261110/native. The reference is
suite/src/prime_hyperelliptic from cryptanalysis commit
68594c8874c75a0a6c04a3874adb1374088ca4f5. source-pin.json and SHA-256
manifests bind all imported files; check.sh refuses drift before compiling.

The source is C:y²=x⁶+1 over F₁₀₁, based at (10,0). The target is
C₂:w²=41z⁶+9z⁴+9z²+41. The order-17 elliptic subgroup has
P=(4,41) on E:y²=x³+1. A faithful coordinate change makes each odd
quintic monic: t=a·z, Y=a²·Z with a=inverse(leading(F)). The reference
therefore computes on the same curves, not an unrecorded twist.
[pcc:unverified]

== Exact development coverage
#table(columns: (1fr, 2fr), inset: 5pt,
  [Check], [Retained scope],
  [Source arithmetic], [10,404 canonical additions and inverses],
  [Richelot subgroup], [All 289 additions in the order-17 target subgroup],
  [Full forward image], [10,404 source images and fixed-translation additions; 2,601 distinct target classes],
  [Point-count order], [Both Jacobian orders recomputed as 10,404 from Fp/Fp² counts],
  [Successor], [Both9,216-class sets: paired additions, dual norms, independent point-count order9,216 and self-inverse counts4/16],
  [Local suite], [27 tests pass; 1 pre-existing benchmark remains ignored],
)
Raw outputs retain the original baseline and successor development/pinned
receipts. The latest full replay includes source guards, formatting and strict
Clippy against the published b280efc pin. Initial18db046 metadata is archived
in source-pins/. PCC-20261111-820d6f remains unsigned/unverified. First Clippy failure and the subsequent pass are
retained; its compatibility annotation affects only the unchanged reference’s
from_fp(&self) API. No correctness test was suppressed. [pcc:unverified]

== Reproduce and limits
Check out the two repositories as siblings, with the pinned native files in
crypto, then run experiments/chained-transfer-reference/check.sh from
cryptanalysis. Cargo.lock and numeric dependency versions are fixed.

There is no DLP timing or speed claim, new curve-family coverage, or full
formal Picard construction in this record. The initial target is isomorphic to its source. The successor rational
2-torsion counts4/16 obstruct an F101-isomorphism of the Jacobians; its
source elliptic quotient has96 points and preserved prime subgroup3. The
upstream report retains vanishing projections and direct elliptic shortcuts
for both complete endpoint functions. These checks do not establish a new
computational reduction.
[pcc:unverified]

Primary sources: Galbraith, corrected book ch.8 §8.3 and ch.10 §§10.3–10.4;
Kunzweiler, DCC92 (2024), DOI10.1007/s10623-024-01366-1, §§3.1–3.2.
The complete source receipt is pinned upstream. KB and vault gaps remain
explicit; no novelty claim is made.

#pagebreak()
= Route of the pinned upstream fixture
#image("route.svg", width: 100%)
This diagram is copied from the pinned upstream commit. Solid arrows show the
explicit maps; dashed arrows are zero controls; dotted arrows are complete
finite elliptic shortcuts. Both fixed-field fixtures are shown, with their
different subgroup sizes visible. All evidence remains unsigned.
