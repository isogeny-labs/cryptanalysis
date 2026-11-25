# Read-only tooling backlog integration

Integrates the exact author heads of #1211
(`a28fb82ccec6fed0f2049d41e5677ae77eccbdeb`) and #1180
(`5e83c651453734b7c00091a23017b1e005ebb05f`) with normal merge commits on
main `fc363d74762fcc5d7142788f1c5cd560bf2039eb`. Both author heads are ancestors.

The literature watcher can follow explicitly configured default-branch commits,
including repositories that do not publish releases. Explicitly watched release
and commit items remain at least in the watch tier; unrelated low-scoring search
items remain noise. The README now documents this behavior. A watch item is a
reading prompt, never evidence of a mathematical result.

The local LMFDB CLI exposes completed local Parquet indexes with extraction
provenance and bounded results. It distinguishes elliptic curves over Q, curves
over number fields, genus-two curves, and finite-field abelian-variety isogeny
classes. The original NAS paths and identity caveats are retained. No NAS data
was accessed and no live scientific query or experiment was run here.

Adds a reproducible DuckDB 1.4.4 dependency pin (Python >=3.9), meaningful query
refusal/unknown-data controls, and a scoped CI job that runs both fixture suites
without live services. The first local query-test attempt lacked DuckDB; after
installing the explicit pinned environment, all 18 literature controls and all
four query integration tests pass. They cover incomplete manifests, provenance,
parameterized labels, SQL result bounds, preserved null rank, rejected mutation
or multiple statements, and invalid limits. Actionlint and scoped whitespace
checks pass. No C or Rust source, evidence receipt, scientific baseline or
threshold changes.

Sources reviewed: the complete submitted patches and existing watcher source,
configuration, fixture tests and README; the submitted LMFDB CLI, README and
identity guidance; the DuckDB 1.4.4 package metadata and Python compatibility;
and GitHub's default-branch commit-list API contract used by the watcher.
Local raw test logs are retained in `ci-repair-tooling-20261027/`.

All current-head required and applicable checks and reviews must finish before
merge. Earlier heads' results do not validate this integration.

## Hosted parity finding

On head 6ee60ba8, all 29 emitted checks completed; the only failed job was
`parity`. The original LMFDB PR supplied its skill body only on `.agents`,
while the repository requires a relative adapter on `.claude` as well. Added
the same directory-symlink convention used by the existing skills, preserving
the original skill body's bytes. The complete existing skills-parity check
now passes for all 13 skills, and the shared-code lock passes all four listed
files. No lock hash or validator was relaxed. Fresh hosted checks remain
necessary for this corrected head.
