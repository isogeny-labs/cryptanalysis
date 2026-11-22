# Rust sweeper engineering port

Classification: engineering. This change ports the existing binary spectral
sweeper into this repository. It introduces no mathematical criterion, new
affected curve, IC result, performance comparison, or publication-priority claim.
The validation workload consists of correctness controls and saved censuses.

## Sources reviewed before implementation

- Repository cover boundary:
  [hyperelliptic-cover infrastructure](../hyperelliptic-cover-infrastructure/README.md).
  Construction, arithmetic, transfer, subgroup preservation, and measured
  advantage are separate obligations. A matching polynomial does not verify
  a transfer. This port does not modify the mirrored arithmetic or its parity
  manifest.
- Repository GHS audit:
  [literature check](../ecc2k130-isogeny-class/gaps/G2-verify-weil-descent-ghs/literature_check.json)
  and [results](../ecc2k130-isogeny-class/gaps/G2-verify-weil-descent-ghs/results.json).
  These distinguish coefficient-module ranks, canonical genus, generalized
  split-pole constructions, and constant-field assumptions. Their large-degree
  conclusions are not inferred from the toy census here.
- Hess, *Generalising the GHS Attack on the Elliptic Curve Discrete Logarithm
  Problem* (2004), [Theorems 11 and 12](https://doi.org/10.1112/S146115700000108X),
  read in the retained primary text of the prototype. The canonical comparison
  retains the absolute/relative-trace Frobenius-lift condition; a formal genus
  is not a descent certificate. The primary PDF is not redistributed here.
- The prototype's branch-orbit argument and saved F2/F4 censuses were read.
  The model family is necessary for a hyperelliptic genus-N realization only
  under ordinary-source and simple-Weil-restriction hypotheses. Its construction
  and the Frobenius/two-torsion method are prior work; the tool checks neither
  publication novelty nor simplicity. Reference fixtures preserve the original
  bytes and their SHA-256 provenance.
- Official [Rust package/crate documentation](https://doc.rust-lang.org/book/ch07-01-packages-and-crates.html),
  [rusqlite transaction contract](https://docs.rs/rusqlite/latest/rusqlite/struct.Transaction.html),
  and [SQLite atomic commit](https://www.sqlite.org/atomiccommit.html).
  The standalone crate avoids the native/GPU bindings workspace; completed jobs
  and their candidates commit together, and dropping a failed transaction rolls
  it back.

## Evidence boundary

Spectral models have `spectral_model_id`, not an `IC1` pipeline identity.
`candidate_id` and `curve_id` stay null: subgroup, generator, maps and complete
solver wiring are unresolved. Source-order matching does not finalize a DLP
curve in the canonical registry. No factor base is generated or cited.

The local prior index is a deduplication aid. Its historical catalogue records
do not establish publication novelty or carry their original map proofs into
this crate. The README identifies the outstanding map, subgroup and literature
obligations. Pollard rho is not a search acceptance gate.

This is a port and fixed-fixture replay, not a substantive search for a new
curve or mechanism. The cover infrastructure source-parity table and the GHS
audit's graphable claims were checked; there is no new curve, transport edge,
or corrected mathematical claim to add to their canonical graphs. No Sage job
or IC benchmark is launched by this change.
