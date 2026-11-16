# Five optional relation-collection paths

`optimized::solve` and `solve-hashed-optimized` compose five optional paths on
top of the reusable exact point tables. Defaults call the original joint
prepared solver; existing commands retain their behavior. This is a prime-field,
two-slot implementation. Binary-field support is a separate task.

From this crate directory:

```sh
cargo run --locked --release --bin hashed-ecdl -- \
  solve-hashed-optimized PROBLEM.json OPTIONS.json NEW_RECEIPT.json
cargo run --locked --release --bin hashed-ecdl -- verify NEW_RECEIPT.json
```

The problem and v1 receipt formats are unchanged. The options file must be a
JSON object; unknown/duplicate fields, arrays and null primitive options are
rejected. Inputs keep the existing bounded reader and exclusive output rule.
An empty object selects the joint prepared control. Example combining all five:

```json
{
  "subgroup_provenance": true,
  "batch_chunk": 8,
  "relation_graph": true,
  "extra_scans": 4,
  "walk": {"table_size": 16, "block_length": 16},
  "joint_targets": true
}
```

| Option | Default / supported values | Behavior and retained checks |
|---|---|---|
| `subgroup_provenance` | false / boolean | Sealed internal point construction skips repeated query order multiplication. External points still undergo subgroup validation. Full curve parameters bind a token to a prepared table. |
| `batch_chunk` | 1 / 1, 8, 32, 128 | Share one ordinary-denominator inversion per nonempty chunk; identity/equal-x exceptions use checked affine addition. Order and exact point equality stay unchanged. |
| `relation_graph` | false / boolean | A weighted bipartite forest supplies sparse cycle dependencies, screening zero-v cycles and considering further cycles. Collection still emits exactly N+1 rows for v1. |
| `extra_scans` | 0 / 0, 4, 16 | Requires the graph; after a first hit, examines at most this many additional candidates, including misses, for a closing edge. The callback sees points/connectivity, never u/v. |
| `walk` | null / object | Table size 16 or 32, block length 16, 64 or 256. Fresh two-coefficient anchors delimit correlated adding-walk blocks. Tables require two-dimensional label span; identity increments are retained. |
| `joint_targets` | true / boolean | Use the existing shared public-coefficient chain for independent targets. Walks use their own joint table regardless of this independent-target option. |

Batching computes full chunks before searching their results. Unused tails are
charged and reported. A resource error during precomputation is an error even
if an earlier point could have been a hit. Extra scans count lookup candidates;
previously precomputed tails may exceed the remaining scan cap, and remain
visible in `unused_precomputed_complements`. Error timing and resource use can
therefore differ from the scalar first-hit control.

Every accepted witness is replayed by factor-base membership and point addition;
recovery replays the scalar and original v1 certificate verifier. Hash matches
never constitute proof. Graph mode changes dependency choice, not the row-count
contract. Walk mode changes RNG consumption and target correlation; no iid
coverage or relation-yield theorem is asserted. [pcc:unverified]

Diagnostics record effective options, setup/query/lookup/replay events, batch
products/inversions/fallbacks, unused complements, bounded witness scans, graph
cycles and walk table/anchor/step events. These are unpriced development counters,
not calibrated GAE, runtime, execution attestations or performance evidence.
Mirror builds retain their existing optional phase and group-call observer.

See the paired study `research/point_hash_five_leads_20261116` for source
manifests, development logs, individual option files and pending measurement work.

The optimized solve command prints only the receipt path on stdout. Its scalar
remains in the explicitly requested receipt, available through normal replay;
it is not echoed into routine command logs. The walk partition seed is public
randomization, not a password salt or secret. Deterministic public seeds in
correctness tests are intentional.
