# Main integration and SHA-2 compatibility

Claim `PCC-20261116-62ae45`, unsigned/unverified. This is bounded engineering
validation, not a performance experiment or an independent execution verdict.
[pcc:unverified]

Merge `a175be78` retains parents `c895e5d0` and main `d9ee51f2`. The exact
canonical main ledger bytes are the prefix; all 26 unmerged branch claim/note
bodies are replayed with the PCC writer. The reviewed main attestation metadata
for `PCC-20261115-8d2645` is active; the branch JSON repair is archived as
`reports/courtois-getrandom-compat-20261115/branch-json-repair-8d2645-20261116.json`.
Both correction histories, all original raw logs/validators and the explicit
adoption note remain. No standing is promoted. The main artifact policy keeps
the ledger without duplicate entries. [pcc:unverified]

The incoming SHA-2 update exposed stale locks, the removed digest `LowerHex`
implementation and a compiler-floor mismatch: 0.11.1 requires Rust 1.88 while
the selected native packages declare 1.85. The repair regenerates affected
consumer locks, encodes the same lowercase 64-character digest, preserves the
rehashed-forgery rejection, and pins non-yanked 0.11.0 in both native consumers.
Cached registry metadata declares 1.85 for that version; actual all-target
checks exercise the selected graph. No compiler floor is raised and no check
is disabled. Retained package versions/checksums are unchanged except the
explicit SHA-2 selection and required dependency additions/orphan removals.
[pcc:unverified]

| Source | Development outcome |
| --- | --- |
| `a175be78` | Both original locked consumer commands refuse stale locks |
| `79249df6` | Both compilations expose the inherited `LowerHex` refusal |
| `192a50d6` | Eight auxiliary CLI checks pass; the native library run times out at 240 seconds; Rust 1.85 rejects SHA-2 0.11.1 |
| `5b9f7050` | Eight auxiliary CLI checks and wrapper 1.85 all-target checking pass; native all-target checking finds the old formatter in a forgery test |
| `f748c746` | Native selected-package 1.85 all-target checking, one digest-vector check, three structured CLI/forgery checks, two C arithmetic parity checks, one audit digest check, four locked graph resolutions, strict lint and targeted formatting pass |

These are unsigned producer observations, separately scoped. Full commands,
exits and outputs, including failures and timeout, are in this directory and
pinned by [the validator](validator.json). The local test builds labeled
`CARGO_PROFILE_TEST_DEBUG=0` omit debug symbols while retaining assertions and
the same test selection. Native Clippy exits zero with its existing
`clippy.toml`/manifest MSRV configuration warning retained. The full native
library suite is **not established passing** by this receipt; the focused
compatibility controls do not replace it or any hosted check. [pcc:unverified]

The core and auxiliary CLI source bytes remain those of algorithm source
`d95d582c`; its 32-check stable/1.78 suites retain their original scope.
The frozen snapshot has no changed paths. No research benchmark, fresh target
panel, timing advantage or independent signed replay is supplied. The failed
checkpoint/runner admission remains open. Current-head CI and reviews still
govern merge. [pcc:unverified]
