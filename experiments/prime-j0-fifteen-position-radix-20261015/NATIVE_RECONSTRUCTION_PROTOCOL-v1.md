# Native radix-15 reconstruction protocol v1

**Status:** planned protocol; no native run or timing was performed for this version. This protocol does not restore or validate the historical Tier 1 build.

## Recoverable source pin

Build a new, versioned candidate from repository commit `37a57501a3297727abe32764cd86d2ab98af30b3` (the base of PR #907), using the source and crate files below. These are the recoverable inputs present in that commit:

| Input | SHA-256 |
| --- | --- |
| `experiments/prime-j0-secp256k1-native/Cargo.toml` | `438235eda97f13312fbb34ad9728be1292a0765b34aae8cdaa082db0dfc3b85b` |
| `experiments/prime-j0-secp256k1-native/Cargo.lock` | `c31dcbed43a3410e0ee3a440ee7165b221a304804ab9cbb9d7532f2a6ffa482f` |
| `experiments/prime-j0-secp256k1-native/src/bin/eisenstein_fixed.rs` | `a65d7e20552626235a75d5895e67b0240d6f6e3de65c3806703a6168117a5f65` |
| `experiments/prime-j0-secp256k1-native/src/bin/eisenstein_fixed/unit_orbit_windows.rs` | `7a6492af38b021df02ee822abdc44de7672d4fbdd74da4d98ebfa2e0f6caca30` |
| Frozen scalar input `experiments/prime-j0-mixed640-materialized-tree-20261013/selective-holdout.json` | `7f4672b7b676969fe40056d0f14c6ecf45ad36109870cdf3466ebafd9e7b22d8` |

The recoverable Rust module is not the historical `e195374c4e6fde368bdba106c769c6335cd319f9f5547e8e2291089fe055335e` parent expected by [`native268_overlay.py`](native268_overlay.py), and it does not contain that overlay's `SPLIT_PRIME_NORM=19183` section. Do not run the historical overlay against it or report a matching historical binary. First implement a separately reviewed `radix15-rebuild-v1` port from the mathematical selector and frozen correctness artifacts in this directory. Commit that port and its patch/source digest before building. This is a new candidate snapshot.

## Correctness gate and fingerprints

Use a disposable checkout of the pinned commit and an isolated `CARGO_TARGET_DIR`; preserve the original tree and all raw artifacts. Verify the source hashes above before applying the new port. Use the locked offline release build (`cargo test --offline --locked --release --bin eisenstein_fixed`) after confirming all locked crates are available. The port must test every residue modulo 71,023 and independently compare the frozen scalar set with binary multiplication. The test log must retain the exact command, toolchain, exit status, and all generated artifacts.

The fixture is the exact `selective-holdout.json` byte stream above; copy those bytes to the benchmark's expected `src/bin/mixed640_bench_fixture.json` location and require the copied hash to remain `7f4672b7…`. Record its parsed scalar count and order as well as the file hash. Before any timing is eligible, require these independent output checks:

| Output check | Required fingerprint |
| --- | --- |
| Frozen representative scalar printed by the native preflight | scalar SHA-256 `5ae1bd49667d0bfc07435aade1e39386bbb3ea1f46cc7f30403b750c0c1cd0e0`; point `(x,y)` `bfd7964d7b68d0201a03f639140824d5d19a1bdbee299aed5d7559852857c112:e6114044e49c8f817316f03309a104b330e0dcc0e7620db93fa00eb6517152ca` |
| Existing independent affine replay of 128 frozen and 260 fresh scalars | [`group-replay268.json`](group-replay268.json): output-point SHA-256 `aa1dc3e8adf194bb549e13fc99328e8b08435e362ef4c2a9621a84a997bcd641`, `388` independently checked scalars |
| Existing integer recoding replay of the 128 frozen cases | [`screen268.json`](screen268.json): representative replay SHA-256 `e77fa8202cb188b15e66b84efdb722c65a59de39e772f2c2fc1b5c3413ddc92b` |
| Historical stdout-only single preflight result (reference fingerprint, not a new test) | `linux-preflight.stdout`: `verified=1`, `count=12288`, `batch_id=all128x96`, fixture hash `7f4672b7…`, representative scalar and point as above |

The historical output fingerprints are independent acceptance targets for a new implementation; matching them does not prove that the missing historical executable or source was recovered. If the port fails any check, retain the failure and stop before performance measurement.

## Performance rerun gate

Correctness alone establishes no throughput claim. Before a new paired panel, recover or implement a separately pinned radix-16 reference from available source and freeze both candidate source trees, executable hashes, fixture hash, compiler/toolchain, and commands in a new manifest. If the exact reference cannot be reproduced, do not report a 15-versus-16 timing ratio. The historical comparison has 96 arms, 48 pairs, 16 alternating repeats, and 128 frozen scalars; a new panel must preserve those workload and pairing criteria or document a separately reviewed, stricter protocol before running.

Each run must capture a **per-child process** peak RSS field with PID, process start identity, raw units, and conversion rule (for Linux, a per-run `/usr/bin/time -v` record or `wait4(2)` `ru_maxrss` for the one measured child). Archive the raw record alongside stdout/stderr and bind it to the exact arm, binary, source, fixture, and run ID. Also retain wall/online time, user/system CPU time, cgroup memory/throttle deltas, steal time, faults, context switches, exit status, correctness output, and host/allocation receipt. Cgroup `memory.peak` is supplementary container-wide context and never substitutes for per-process RSS. The preflight, build, and test process RSS must not be substituted for the measured child.

A future panel can support only the newly pinned implementation and reference. It cannot retroactively fill the missing source snapshot or per-process RSS of panel `2481bd3c0f7e491698694ccb039f1048`; preserve that panel, its existing graph, and the original claim limits unchanged. The current panel's 1.024327× median and `[1.020012,1.031215]` repeat-bootstrap interval remain historical measurements with the documented provenance/evidence gaps.

## Reproduction commands (future execution only)

These commands describe the protocol and are not evidence that it has run:

```bash
git worktree add --detach /tmp/radix15-rebuild-v1 37a57501a3297727abe32764cd86d2ab98af30b3
cd /tmp/radix15-rebuild-v1/experiments/prime-j0-secp256k1-native
sha256sum Cargo.toml Cargo.lock src/bin/eisenstein_fixed.rs src/bin/eisenstein_fixed/unit_orbit_windows.rs
# Apply the committed radix15-rebuild-v1 port and verify its recorded diff/source hash.
cp ../prime-j0-mixed640-materialized-tree-20261013/selective-holdout.json src/bin/mixed640_bench_fixture.json
sha256sum src/bin/mixed640_bench_fixture.json
CARGO_TARGET_DIR=/tmp/radix15-rebuild-v1-target cargo test --offline --locked --release --bin eisenstein_fixed
```

The `cp` command is run from the crate directory; its relative fixture path points to the sibling experiment directory. The run must not proceed to paired timing unless the source, fixture, test, reference, and per-process-RSS gates above all pass.
