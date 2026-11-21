# Registered PKM tower phase 1: preparation and hold

Status: prepared, measurement not launched. [pcc:unverified]

The lead spec is `lead.json`, validated against the trunk registry (`sha256 e840213ad5cf...`). The frozen phase-1 plan has matched raw F4 baseline and tower-engine arms for m=2..6 at p=786433, seed=1347112276, with 3 planted and 3 random targets, all registered tower kinds and controls. It sets t_min=3 for m=5,6; m=7..9 are unsupported by the current engine. The earlier m=5,t=2 result did not measure F4 because four base abscissae could not supply five distinct target points. This is a correction to setup scope, not a new solver result. [pcc:unverified]

The clean isolated checkout `/Volumes/SSD990-2/.codex/worktrees/cryptanalysis-pkm-high-arity-20261121` built `ca-ic` and `pkm_tower_pilot` with Rust 1.97.0 via `cargo build --release --locked --bin ca-ic --example pkm_tower_pilot` on 2026-11-21. Build log: `/private/tmp/pkm-registered-build-20261121.log` (local, ephemeral). No protocol cell has started. [pcc:unverified]

The repository requires `scripts/checkpoint.sh gate` before an experiment. The saved token at `~/.config/checkpoint/upload-token` was last modified 2026-11-16 and its presigned upload returned HTTP 403. Fallback profile `ecc-challenges-new` returned InvalidAccessKeyId; the default profile returned AllAccessDisabled on the checkpoint S3 prefix. These are access failures, not scientific outcomes. The local `.resume/RESUME.md` has the full resume record. [pcc:unverified]

After checkpoint access is restored, from the cryptanalysis worktree run `scripts/checkpoint.sh gate`. Then from `/Volumes/SSD990-2/workspace` run:

```sh
python3 tools/lead_sweep.py run /Volumes/SSD990-2/.codex/worktrees/cryptanalysis-pkm-high-arity-20261121/research/pkm_tower_registered_m5m6_20261121/lead.json --phase 1 --cryptanalysis /Volumes/SSD990-2/.codex/worktrees/cryptanalysis-pkm-high-arity-20261121
```

Review every cell status and raw JSONL, retain resource-limit states, and report the frozen gate verdict with any independent verification required for a scientific claim. Update the checkpoint after launch and completion. [pcc:unverified]
