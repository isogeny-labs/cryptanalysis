# GHS cover-candidate sweeper (Rust)

Native Rust CLI and library in `aburan28/cryptanalysis`. This is an engineering
port of the earlier prototype, with fixed census fixtures and no runtime Python,
Sage, CUDA or native cryptanalysis-bindings dependency. SQLite is bundled.

```sh
# From the repository root:
cargo build --release --locked --manifest-path experiments/ghs-sweeper/Cargo.toml
experiments/ghs-sweeper/target/release/ghs-sweeper --help
```

The binary implements `plan`, `init`, `run`, `status`, `verify`, `sources`,
`export`, `review`, `subfields`, and `import-python`. Progress goes to stderr;
machine-readable results go to stdout. Example:

```sh
experiments/ghs-sweeper/target/release/ghs-sweeper init \
  --config experiments/ghs-sweeper/configs/smoke.json \
  --db experiments/ghs-sweeper/runs/smoke.sqlite
experiments/ghs-sweeper/target/release/ghs-sweeper run \
  --db experiments/ghs-sweeper/runs/smoke.sqlite --workers 2
experiments/ghs-sweeper/target/release/ghs-sweeper verify \
  --db experiments/ghs-sweeper/runs/smoke.sqlite
experiments/ghs-sweeper/target/release/ghs-sweeper sources \
  --db experiments/ghs-sweeper/runs/smoke.sqlite
experiments/ghs-sweeper/target/release/ghs-sweeper export \
  --db experiments/ghs-sweeper/runs/smoke.sqlite --format jsonl \
  --output experiments/ghs-sweeper/runs/candidates.jsonl
```

## Mathematical boundary

The engine enumerates ordinary binary hyperelliptic curves

```text
w^2+w = A*x+c+R(x)/H(x) over F_q, q=2^d
H monic irreducible, deg(H)=N odd >=3
A!=0; R!=0, deg(R)<N; both absolute-trace choices for c
genus=N; candidate elliptic source field F_(q^N)
```

Denominators are normalized under affine changes of x. All nonzero A and R
and both twists are retained. Residual stabilizers can repeat isomorphic
models; a normalized-model count is not a count of distinct curves.

A Walsh transform first requires `#C(F_(q^e))=q^e+1` for `e<N`, then tests the
ordinary elliptic trace bound at e=N. Positives receive direct point counts
through degree N. Those counts determine the sparse candidate polynomial
`T^(2N)-t*T^N+q^N`. The separate verifier uses carryless products, polynomial
division and extended Euclid, without log tables or Walsh transforms.

The [retained branch-orbit argument](reference/prototype-branch-orbit.md)
relates this family to genus-N hyperelliptic covers **assuming** an ordinary
source and a simple Weil restriction. The tool does not prove simplicity,
construct quotient maps, check DLP subgroup preservation, or solve a planted
log. It does not classify higher-genus, nonhyperelliptic, even-relative-degree,
or odd-characteristic targets. Prime source fields have no applicable proper
subfield. A completed negative search is limited to its model family and
hypotheses; a partial run excludes only completed denominator jobs.

`sources` finds explicit models `y^2+x*y=x^3+a*x^2+b` with the candidate
elliptic trace. It prefers full absolute degree for b when available and
checks each chosen source order independently. Its canonical GHS comparison
retains the formal genus **and** the trace-based Frobenius-lift condition.
It neither constructs that cover nor excludes the full gGHS framework.

## Configuration and resumption

| File | Fixed parameter choices (q,N) |
| --- | --- |
| `configs/smoke.json` | (2,5), (4,3), (8,3) |
| `configs/regression.json` | (2,5), (2,11), (2,13), (4,5) |
| `configs/exploration.json` | (2,7), (2,9), (4,7), (8,5), (16,3) |

Configs have `schema_version: 1` and a nonempty `searches` list. Each search
has `base_degree` d and `relative_degree` N; genus is N. Unknown fields,
duplicate searches, d outside 1..4, even N, N<3, and Walsh width above 20
bits are rejected. Width is N for d=1 and d(N+1) otherwise. `plan` enumerates
the exact jobs before a run; large plans and runs can still be expensive.

```sh
experiments/ghs-sweeper/target/release/ghs-sweeper subfields \
  --absolute-degree 15 --output experiments/ghs-sweeper/runs/degree15.json
experiments/ghs-sweeper/target/release/ghs-sweeper plan \
  --config experiments/ghs-sweeper/configs/exploration.json
experiments/ghs-sweeper/target/release/ghs-sweeper run \
  --db experiments/ghs-sweeper/runs/smoke.sqlite --workers 2 --max-jobs 20
```

`subfields` reports every divisor, including excluded choices and their
reasons. It writes only supported choices. It does not imply that all
subfields are supported by this engine.

One denominator is one deterministic checkpoint. SQLite commits its candidates
and completed state together. Native Rayon workers compute independently;
only the parent writes the journal. A cross-process exclusive file lock
prevents simultaneous writers. `status` and export read consistent snapshots
of committed work. Init and export refuse to overwrite existing files.

Repeat `run` to resume. Abandoned running jobs are replayed; completed jobs
are skipped; failed jobs remain visible until `--retry-failed`. `--max-jobs`
bounds dispatched jobs. `--max-seconds` is a soft dispatch limit: current
jobs finish and can exceed it. The first interrupt or SIGTERM drains current
jobs; a second interrupt aborts. Checkpoints are per denominator, not per
field point. `verify --limit 10` bounds new independent model checks and
`sources --limit 4` bounds new source trace classes. Both skip saved results.

Journals bind the compiled Rust sources and Cargo lockfile by hash. A changed
implementation refuses to extend an old journal; retain the original binary
or create a new journal. Old journals remain readable and exportable.

## Carry over the earlier journal

```sh
experiments/ghs-sweeper/target/release/ghs-sweeper import-python \
  --input /path/to/earlier/sweep.sqlite \
  --db experiments/ghs-sweeper/runs/imported.sqlite
```

The Rust importer reads the historical SQLite schema directly, without
launching Python. It retains completed spectral coverage and model identities
under the new plan, validates historical counts, and records the input hash
and original source hashes. Historical worker times are reported separately
from Rust worker times. Pending, running and failed historical work becomes
pending. Raw-verification flags, source matches and reviews are reset for
fresh checks with this implementation. The original journal is unchanged;
the import needs a new output path. An interrupted import leaves only its
committed completed jobs; remaining work can be run in Rust.

## Evidence and novelty triage

The [Hess scope note](HESS_SCOPE.md) derives a published-construction inclusion
baseline for full-relative-degree coefficients, with a
[PDF proof and diagram](HESS_SCOPE.pdf) and a separate Rust witness example.
It is an existence bound, not a minimum-genus or cost result. It changes no
search checkpoint, prior snapshot, catalogue, or novelty verdict.

```sh
cargo test --release --locked \
  --manifest-path experiments/ghs-sweeper/Cargo.toml --example hess_scope
```

`spectral_model_id` is a stable hash of the normalized model parameters in the
declared deterministic binary power-basis convention. Field moduli and base
embeddings are retained with every result. This is not an EC1 curve identity
or an IC1 pipeline identity: `curve_id` and `candidate_id` remain null until
the required subgroup and full pipeline are specified.

The [reference provenance](reference/PROVENANCE.json) binds the saved F2/F4
censuses and historical local catalogue. A journal freezes this local prior
index. It flags previous spectral records and matching elliptic isogeny or
quadratic-twist classes. Historical catalogue witness paths are identified as
prototype paths; those map proofs are not redistributed in this fixture
snapshot. This index is for deduplication, not publication review.

```sh
experiments/ghs-sweeper/target/release/ghs-sweeper export \
  --db experiments/ghs-sweeper/runs/smoke.sqlite --needs-review
experiments/ghs-sweeper/target/release/ghs-sweeper export \
  --db experiments/ghs-sweeper/runs/smoke.sqlite --unseen-source-classes
experiments/ghs-sweeper/target/release/ghs-sweeper review \
  --db experiments/ghs-sweeper/runs/smoke.sqlite --model MODEL_ID --record review.json
```

The first filter selects models awaiting source-family review; the second
excludes local source classes and their twists. Absence from the local index
does not establish novelty. See [review.example.json](configs/review.example.json)
for the required shape; replace the example with a model-specific assessment.
Reference paths are relative to the `init --reference-root` directory (default:
the init working directory). References must stay within that root. Source
sections, assessments and content hashes are retained. Changed or missing
references reopen the review gate. An active known-overlap review is not
erased by a later narrower assessment.

Reviews distinguish `source_family`, `map` and `criterion`. Allowed verdicts
are `known_overlap`, `unresolved` and `outside_reviewed_criteria`. None sets
publication novelty or verifies a map. No command promotes a spectral hit to
the affected-curve catalogue. Pollard rho is not an acceptance gate.

Search invocation, worker, raw verification and source-identification timings
are labelled separately. Worker times overlap in parallel runs. Imported
times remain historical. No value is a complete DLP attack time or a speedup.

## Validation

```sh
cargo fmt --manifest-path experiments/ghs-sweeper/Cargo.toml -- --check
cargo clippy --locked --manifest-path experiments/ghs-sweeper/Cargo.toml --all-targets -- -D warnings
cargo test --release --locked --manifest-path experiments/ghs-sweeper/Cargo.toml -- --test-threads=2
```

The native tests replay all saved F2 genus-5/11/13 and F4 genus-5 models,
comparing complete positive sets and coverage; F2 stage-survival counts also
match. They check arithmetic separately, affine stabilizers, source orders,
the trace-one canonical-lift obstruction, Koblitz control, transaction rollback,
abandoned-job recovery, explicit failed-job retry, bounded parallel resume,
cancellation, engine fingerprints, local overlap, stale references, CLI
overwrite protection and historical SQLite import. Neither the CLI nor tests
spawn Python or Sage. The [CI workflow](../../.github/workflows/ghs-sweeper.yml)
runs formatting, Clippy and the release tests.

The [engineering notes](NOTES.md) record the literature and software sources
reviewed before this port and why existing curve/transfer graphs remain current.
No new affected family or end-to-end cryptanalytic result is claimed.
